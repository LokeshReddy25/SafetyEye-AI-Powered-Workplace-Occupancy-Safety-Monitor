"""Module 1 – Data preparation.

Reads the dataset IN PLACE (never copies it), then:
  1. checks that every image has a label file and vice versa,
  2. checks every image decodes, and every label line is valid YOLO format
     (5 fields, integer class in [0, nc), normalized coords in [0, 1], w/h > 0),
  3. counts empty label files (background images: valid in YOLO, kept),
  4. checks for train/val/test leakage (identical image bytes, and the same Roboflow
     source image appearing in more than one split),
  5. writes cleaned image lists (data/splits/*.txt) excluding any corrupt file,
     plus configs/data.yaml pointing at them,
  6. writes a class-distribution report (CSV + PNG) and sample images with labels drawn.

Usage:  python -m src.data_prep.validate
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import yaml

from src import config

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
RF_SUFFIX = re.compile(r"\.rf\.[0-9a-f]{32}$")


@dataclass
class LabelCheck:
    ok: bool
    n_boxes: int = 0
    classes: list[int] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def check_label_text(text: str, nc: int) -> LabelCheck:
    """Validate the contents of one YOLO label file. Empty file = valid background image."""
    res = LabelCheck(ok=True)
    seen = set()
    for i, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            res.errors.append(f"line {i}: expected 5 fields, got {len(parts)}")
            continue
        try:
            cls = int(parts[0])
            x, y, w, h = map(float, parts[1:])
        except ValueError:
            res.errors.append(f"line {i}: non-numeric value")
            continue
        if not 0 <= cls < nc:
            res.errors.append(f"line {i}: class {cls} out of range")
        if not all(0.0 <= v <= 1.0 for v in (x, y, w, h)):
            res.errors.append(f"line {i}: coordinate outside [0,1]")
        if w <= 0 or h <= 0:
            res.errors.append(f"line {i}: zero/negative size")
        key = (cls, round(x, 6), round(y, 6), round(w, 6), round(h, 6))
        if key in seen:
            res.errors.append(f"line {i}: duplicate box")
        seen.add(key)
        res.classes.append(cls)
        res.n_boxes += 1
    res.ok = not res.errors
    return res


def source_stem(filename: str) -> str:
    """Roboflow names files '<original>_<ext>.rf.<hash>.jpg'; return '<original>_<ext>'."""
    return RF_SUFFIX.sub("", Path(filename).stem)


def validate_split(split_dir: Path, nc: int) -> dict:
    img_dir, lbl_dir = split_dir / "images", split_dir / "labels"
    images = {p.stem: p for p in img_dir.iterdir() if p.suffix.lower() in IMG_EXTS}
    labels = {p.stem: p for p in lbl_dir.glob("*.txt")}

    out = {
        "n_images": len(images), "n_labels": len(labels),
        "images_without_label": sorted(set(images) - set(labels)),
        "labels_without_image": sorted(set(labels) - set(images)),
        "corrupt_images": [], "bad_labels": {}, "empty_labels": 0,
        "instances": Counter(), "images_per_class": Counter(),
        "image_sizes": Counter(), "md5": {}, "sources": set(), "kept": [],
    }
    for stem, img_path in sorted(images.items()):
        data = img_path.read_bytes()
        im = cv2.imdecode(__import__("numpy").frombuffer(data, "uint8"), cv2.IMREAD_COLOR)
        if im is None:
            out["corrupt_images"].append(img_path.name)
            continue
        out["image_sizes"][f"{im.shape[1]}x{im.shape[0]}"] += 1
        out["md5"][hashlib.md5(data).hexdigest()] = img_path.name
        out["sources"].add(source_stem(img_path.name))
        if stem not in labels:
            continue
        chk = check_label_text(labels[stem].read_text(), nc)
        if not chk.ok:
            out["bad_labels"][labels[stem].name] = chk.errors
            continue
        if chk.n_boxes == 0:
            out["empty_labels"] += 1
        out["instances"].update(chk.classes)
        out["images_per_class"].update(set(chk.classes))
        out["kept"].append(img_path)
    return out


def draw_samples(paths: list[Path], dst: Path, names: list[str], n: int = 6) -> list[Path]:
    import random

    dst.mkdir(parents=True, exist_ok=True)
    rng = random.Random(0)
    written = []
    for p in rng.sample(paths, min(n, len(paths))):
        im = cv2.imread(str(p))
        h, w = im.shape[:2]
        lbl = p.parent.parent / "labels" / (p.stem + ".txt")
        for line in lbl.read_text().splitlines():
            c, x, y, bw, bh = line.split()
            c = int(c)
            x1, y1 = int((float(x) - float(bw) / 2) * w), int((float(y) - float(bh) / 2) * h)
            x2, y2 = int((float(x) + float(bw) / 2) * w), int((float(y) + float(bh) / 2) * h)
            color = (0, 0, 255) if names[c].startswith("NO-") else (0, 200, 0)
            cv2.rectangle(im, (x1, y1), (x2, y2), color, 2)
            cv2.putText(im, names[c], (x1, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        out = dst / f"sample_{len(written)}.jpg"
        cv2.imwrite(str(out), im)
        written.append(out)
    return written


def main() -> None:
    names = config.CLASS_NAMES
    nc = len(names)
    report_dir = config.RESULTS / "data_report"
    report_dir.mkdir(parents=True, exist_ok=True)
    config.SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    config.CONFIGS.mkdir(parents=True, exist_ok=True)

    print(f"Dataset root (read in place): {config.DATASET_ROOT}")
    results = {}
    for split, folder in config.SPLITS.items():
        r = validate_split(config.DATASET_ROOT / folder, nc)
        results[split] = r
        list_file = config.SPLITS_DIR / f"{split}.txt"
        list_file.write_text("\n".join(str(p.resolve()).replace("\\", "/") for p in r["kept"]) + "\n")
        print(f"\n[{split}] images={r['n_images']} labels={r['n_labels']} kept={len(r['kept'])} "
              f"empty_labels(background)={r['empty_labels']}")
        print(f"  images_without_label={len(r['images_without_label'])} "
              f"labels_without_image={len(r['labels_without_image'])} "
              f"corrupt_images={len(r['corrupt_images'])} bad_label_files={len(r['bad_labels'])}")
        print(f"  image sizes: {dict(r['image_sizes'])}")
        for fname, errs in list(r["bad_labels"].items())[:10]:
            print(f"  BAD {fname}: {errs[:3]}")

    # Leakage checks
    print("\nLeakage checks:")
    leak = {}
    for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
        same_bytes = set(results[a]["md5"]) & set(results[b]["md5"])
        same_src = results[a]["sources"] & results[b]["sources"]
        leak[f"{a}-{b}"] = {"identical_images": len(same_bytes), "shared_source_stems": len(same_src),
                            "examples": sorted(same_src)[:5]}
        print(f"  {a} vs {b}: identical image bytes={len(same_bytes)}, "
              f"shared Roboflow source stems={len(same_src)} {sorted(same_src)[:5]}")
    print(f"  unique source stems: train={len(results['train']['sources'])} "
          f"val={len(results['val']['sources'])} test={len(results['test']['sources'])}")

    # data.yaml
    data_yaml = {
        "path": str(config.SPLITS_DIR.resolve()).replace("\\", "/"),
        "train": "train.txt", "val": "val.txt", "test": "test.txt",
        "nc": nc, "names": {i: n for i, n in enumerate(names)},
    }
    config.DATA_YAML.write_text(yaml.safe_dump(data_yaml, sort_keys=False))
    print(f"\nWrote {config.DATA_YAML}")

    # Class distribution
    rows = ["class_id,class_name," + ",".join(f"{s}_instances,{s}_images" for s in config.SPLITS)]
    for i, n in enumerate(names):
        rows.append(f"{i},{n}," + ",".join(
            f"{results[s]['instances'][i]},{results[s]['images_per_class'][i]}" for s in config.SPLITS))
    (report_dir / "class_distribution.csv").write_text("\n".join(rows) + "\n")
    print("\nClass distribution (instances / images containing class):")
    print("\n".join(rows))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(11, 4.5))
    xs = np.arange(nc)
    for k, s in enumerate(config.SPLITS):
        tot = sum(results[s]["instances"].values()) or 1
        ax.bar(xs + (k - 1) * 0.27, [results[s]["instances"][i] / tot * 100 for i in range(nc)],
               width=0.27, label=f"{s} (n={tot})")
    ax.set_xticks(xs, names, rotation=30, ha="right")
    ax.set_ylabel("% of instances in split")
    ax.set_title("Class distribution per split (share of box instances)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(report_dir / "class_distribution.png", dpi=120)

    samples = draw_samples(results["train"]["kept"], report_dir / "samples", names)
    print(f"Wrote {len(samples)} labelled sample images to {report_dir / 'samples'}")

    summary = {
        s: {k: (len(v) if isinstance(v, (list, dict, set)) and k not in ("instances", "images_per_class",
                                                                           "image_sizes") else v)
            for k, v in r.items() if k not in ("md5", "sources", "kept")}
        for s, r in results.items()
    }
    for s in summary:
        for k in ("instances", "images_per_class", "image_sizes"):
            summary[s][k] = {(names[i] if isinstance(i, int) else i): c for i, c in results[s][k].items()}
        summary[s]["kept"] = len(results[s]["kept"])
    summary["leakage"] = leak
    (report_dir / "validation_summary.json").write_text(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
