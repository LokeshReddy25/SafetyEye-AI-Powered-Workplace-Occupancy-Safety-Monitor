"""Evaluate a trained model on one split (val for model selection, test for the final report).

Usage:
    python -m src.evaluate --weights weights/A_v8n_default_aug.pt --split val  --name A_val
    python -m src.evaluate --weights weights/<winner>.pt         --split test --name final_test --samples

Writes results/eval/<name>/: metrics.json, per_class.csv, per_class.md, confusion matrix + PR curve,
and (with --samples) GT-vs-prediction images: the worst images (most errors) and a few successes.
Metric definitions are Ultralytics' (mAP@0.5, mAP@0.5:0.95, precision/recall at the max-F1 confidence).
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from src import config

PLOTS = ["confusion_matrix.png", "confusion_matrix_normalized.png", "BoxPR_curve.png", "BoxF1_curve.png",
         "BoxP_curve.png", "BoxR_curve.png", "PR_curve.png", "F1_curve.png"]


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0


def load_gt(img_path: Path, w: int, h: int):
    lbl = img_path.parent.parent / "labels" / (img_path.stem + ".txt")
    out = []
    for line in lbl.read_text().splitlines():
        if line.strip():
            c, x, y, bw, bh = map(float, line.split())
            out.append((int(c), ((x - bw / 2) * w, (y - bh / 2) * h, (x + bw / 2) * w, (y + bh / 2) * h)))
    return out


def match_errors(gt, preds, thr=0.5):
    """Greedy same-class matching at IoU>=thr. Returns (#FP, #FN)."""
    used = set()
    fp = 0
    for c, box, _ in sorted(preds, key=lambda p: -p[2]):
        best, bi = 0, None
        for j, (gc, gb) in enumerate(gt):
            if j not in used and gc == c:
                v = iou(box, gb)
                if v > best:
                    best, bi = v, j
        if best >= thr:
            used.add(bi)
        else:
            fp += 1
    return fp, len(gt) - len(used)


def render(img, boxes, names, title, color_fn):
    im = img.copy()
    for c, b, *s in boxes:
        x1, y1, x2, y2 = map(int, b)
        col = color_fn(names[c])
        cv2.rectangle(im, (x1, y1), (x2, y2), col, 2)
        txt = names[c] + (f" {s[0]:.2f}" if s else "")
        cv2.putText(im, txt, (x1, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1)
    cv2.rectangle(im, (0, 0), (im.shape[1], 24), (30, 30, 30), -1)
    cv2.putText(im, title, (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    return im


def save_samples(model, split_list: Path, out_dir: Path, names, conf=0.5, n_fail=6, n_ok=4):
    out_dir.mkdir(parents=True, exist_ok=True)
    color = lambda n: (0, 0, 255) if n.startswith("NO-") else (0, 180, 0)
    scored = []
    for p in map(Path, split_list.read_text().split()):
        r = model.predict(str(p), conf=conf, verbose=False)[0]
        img = r.orig_img
        h, w = img.shape[:2]
        gt = load_gt(p, w, h)
        preds = [(int(c), tuple(b), float(s)) for b, c, s in
                 zip(r.boxes.xyxy.cpu().numpy(), r.boxes.cls.cpu().numpy(), r.boxes.conf.cpu().numpy())]
        fp, fn = match_errors(gt, preds)
        scored.append((fp + fn, fp, fn, p, img, gt, preds))
    scored.sort(key=lambda s: -s[0])
    rows = ["kind,file,false_positives,false_negatives,gt_boxes"]
    picks = [("failure", s) for s in scored[:n_fail]] + \
            [("success", s) for s in [s for s in scored if s[0] == 0 and s[5]][:n_ok]]
    for i, (kind, (_, fp, fn, p, img, gt, preds)) in enumerate(picks):
        side = np.hstack([render(img, gt, names, "ground truth", color),
                          render(img, preds, names, f"prediction conf>={conf}  FP={fp} FN={fn}", color)])
        cv2.imwrite(str(out_dir / f"{kind}_{i:02d}.jpg"), side)
        rows.append(f"{kind},{p.name},{fp},{fn},{len(gt)}")
    (out_dir / "samples_index.csv").write_text("\n".join(rows) + "\n")
    tot_fp, tot_fn = sum(s[1] for s in scored), sum(s[2] for s in scored)
    tot_gt = sum(len(s[5]) for s in scored)
    zero_err = sum(1 for s in scored if s[0] == 0)
    return {"conf": conf, "iou_match": 0.5, "images": len(scored), "gt_boxes": tot_gt, "false_positives": tot_fp,
            "false_negatives": tot_fn, "images_with_zero_errors": zero_err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--split", choices=["val", "test"], required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--samples", action="store_true")
    args = ap.parse_args()

    model = YOLO(args.weights)
    names = model.names
    m = model.val(data=str(config.DATA_YAML), split=args.split, imgsz=640, batch=16, device=0, plots=True,
                  project=str(config.RUNS / "eval"), name=args.name, exist_ok=True)
    out = config.RESULTS / "eval" / args.name
    out.mkdir(parents=True, exist_ok=True)

    overall = {"precision": float(m.box.mp), "recall": float(m.box.mr), "mAP50": float(m.box.map50),
               "mAP50_95": float(m.box.map)}
    counts = getattr(m, "nt_per_class", None)
    per_class = []
    for k, ci in enumerate(m.box.ap_class_index):
        p, r, ap50, ap = m.box.class_result(k)
        per_class.append({"class": names[int(ci)], "instances": int(counts[int(ci)]) if counts is not None else None,
                          "precision": float(p), "recall": float(r), "mAP50": float(ap50), "mAP50_95": float(ap)})

    meta = {"weights": args.weights, "split": args.split, "imgsz": 640, "val_conf": m.args.conf, "val_iou": m.args.iou,
            "speed_ms_per_image": m.speed}
    res = {"meta": meta, "overall": overall, "per_class": per_class}
    if args.samples:
        res["sample_error_counts"] = save_samples(model, config.SPLITS_DIR / f"{args.split}.txt", out / "samples",
                                                  names)
    (out / "metrics.json").write_text(json.dumps(res, indent=2))

    hdr = "class,instances,precision,recall,mAP50,mAP50_95"
    lines = [hdr, f"all,{sum(c['instances'] or 0 for c in per_class)},{overall['precision']:.4f},"
                  f"{overall['recall']:.4f},{overall['mAP50']:.4f},{overall['mAP50_95']:.4f}"]
    md = ["| Class | Instances | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |", "|---|---:|---:|---:|---:|---:|",
          f"| **all** | {sum(c['instances'] or 0 for c in per_class)} | {overall['precision']:.3f} | "
          f"{overall['recall']:.3f} | {overall['mAP50']:.3f} | {overall['mAP50_95']:.3f} |"]
    for c in per_class:
        lines.append(f"{c['class']},{c['instances']},{c['precision']:.4f},{c['recall']:.4f},{c['mAP50']:.4f},"
                     f"{c['mAP50_95']:.4f}")
        md.append(f"| {c['class']} | {c['instances']} | {c['precision']:.3f} | {c['recall']:.3f} | "
                  f"{c['mAP50']:.3f} | {c['mAP50_95']:.3f} |")
    (out / "per_class.csv").write_text("\n".join(lines) + "\n")
    (out / "per_class.md").write_text("\n".join(md) + "\n")
    run_dir = config.RUNS / "eval" / args.name
    for f in PLOTS:
        if (run_dir / f).exists():
            shutil.copy2(run_dir / f, out / f)
    print("\n".join(md))
    print(json.dumps(res.get("sample_error_counts", {}), indent=2))


if __name__ == "__main__":
    main()
