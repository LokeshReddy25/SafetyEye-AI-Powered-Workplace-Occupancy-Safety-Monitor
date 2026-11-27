"""Module 3 – Real-time PPE violation detection on a webcam or video file.

Usage:
    python -m src.detect --weights weights/best.pt --source 0                  # webcam 0
    python -m src.detect --weights weights/best.pt --source path/to/video.mp4  # file
Options: --conf 0.5  --rules NO-Hardhat "NO-Safety Vest" [NO-Mask]  --no-show  --save out.mp4
         --max-frames N  --cooldown 10
Press q to quit the window. Email alerts are sent only if EMAIL_ENABLED=1 in .env.
"""
from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from src.rules import DEFAULT_ACTIVE, Detection, FrameResult, RuleEngine, from_ultralytics

RED, GREEN, GREY, WHITE = (0, 0, 255), (0, 180, 0), (160, 160, 160), (255, 255, 255)
PPE_OK = {"Hardhat", "Safety Vest", "Mask"}


@dataclass
class FrameOutput:
    annotated: np.ndarray
    detections: list[Detection]
    result: FrameResult
    timings_ms: dict = field(default_factory=dict)


def draw(frame: np.ndarray, dets: list[Detection], result: FrameResult, fps: Optional[float] = None) -> np.ndarray:
    img = frame.copy()
    for d in dets:
        color = RED if d.cls_name.startswith("NO-") else GREEN if d.cls_name in PPE_OK else GREY
        x1, y1, x2, y2 = map(int, d.box)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label = f"{d.cls_name} {d.conf:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, max(0, y1 - th - 6)), (x1 + tw + 4, y1), color, -1)
        cv2.putText(img, label, (x1 + 2, max(th, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)
    comp = "n/a" if result.compliance is None else f"{result.compliance * 100:.0f}%"
    hud = f"workers {result.n_workers}  compliant {comp}" + (f"  {fps:.1f} FPS" if fps else "")
    cv2.rectangle(img, (0, 0), (img.shape[1], 28), (40, 40, 40), -1)
    cv2.putText(img, hud, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
    if result.violations:  # GUI warning banner
        rules = sorted({v.rule for v in result.violations})
        h = img.shape[0]
        cv2.rectangle(img, (0, h - 36), (img.shape[1], h), RED, -1)
        cv2.putText(img, "VIOLATION: " + ", ".join(rules), (8, h - 11), cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 2)
    return img


class Pipeline:
    def __init__(self, weights: str, conf: float = 0.5, rules=DEFAULT_ACTIVE, imgsz: int = 640,
                 device: Optional[str] = None):
        from ultralytics import YOLO

        self.model = YOLO(weights)
        self.names = self.model.names
        self.conf, self.imgsz, self.device = conf, imgsz, device
        # detection threshold for drawing; the rule engine applies the same min_conf
        self.engine = RuleEngine(active=rules, min_conf=conf, person_min_conf=conf)

    def process(self, frame: np.ndarray, fps: Optional[float] = None) -> FrameOutput:
        t0 = time.perf_counter()
        res = self.model.predict(frame, conf=self.conf, imgsz=self.imgsz, device=self.device, verbose=False)[0]
        dets = from_ultralytics(res, self.names)       # .cpu() inside => GPU work finished here
        t1 = time.perf_counter()
        result = self.engine.evaluate(dets)
        t2 = time.perf_counter()
        annotated = draw(frame, dets, result, fps)
        t3 = time.perf_counter()
        sp = res.speed  # ultralytics internal ms: preprocess / inference / postprocess
        return FrameOutput(annotated, dets, result, {
            "model_total": (t1 - t0) * 1e3, "yolo_pre": sp["preprocess"], "yolo_infer": sp["inference"],
            "yolo_post": sp["postprocess"], "rules": (t2 - t1) * 1e3, "draw": (t3 - t2) * 1e3})


def open_source(src: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(int(src)) if src.isdigit() else cv2.VideoCapture(src)
    if not cap.isOpened():
        raise SystemExit(f"Cannot open source {src!r}")
    return cap


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--source", default="0")
    ap.add_argument("--conf", type=float, default=0.5)
    ap.add_argument("--rules", nargs="+", default=list(DEFAULT_ACTIVE))
    ap.add_argument("--cooldown", type=float, default=10.0)
    ap.add_argument("--no-show", action="store_true")
    ap.add_argument("--save")
    ap.add_argument("--max-frames", type=int)
    args = ap.parse_args()

    from src.alerts import AlertManager

    pipe = Pipeline(args.weights, args.conf, args.rules)
    alerts = AlertManager(source=Path(args.source).name if not args.source.isdigit() else f"webcam{args.source}",
                          cooldown_s=args.cooldown)
    cap = open_source(args.source)
    writer = None
    n, fps, t_prev = 0, None, time.perf_counter()
    while True:
        ok, frame = cap.read()
        if not ok or (args.max_frames and n >= args.max_frames):
            break
        out = pipe.process(frame, fps)
        alerts.handle(frame, out.result)
        now = time.perf_counter()
        inst = 1.0 / max(now - t_prev, 1e-6)
        fps = inst if fps is None else 0.9 * fps + 0.1 * inst
        t_prev = now
        if args.save:
            if writer is None:
                h, w = out.annotated.shape[:2]
                writer = cv2.VideoWriter(args.save, cv2.VideoWriter_fourcc(*"mp4v"),
                                         cap.get(cv2.CAP_PROP_FPS) or 25, (w, h))
            writer.write(out.annotated)
        if not args.no_show:
            cv2.imshow("SafetyEye", out.annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        n += 1
    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    print(f"Processed {n} frames, {alerts.n_alerts} violation alerts logged to {alerts.db.db_path}")


if __name__ == "__main__":
    main()
