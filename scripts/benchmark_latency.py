"""Measure end-to-end per-frame latency and FPS of the real-time pipeline over a fixed video.

End-to-end frame time = decode frame + YOLO predict (pre/infer/post, incl. GPU->CPU copy)
                        + rule engine + overlay drawing + alert handling (SQLite + snapshots).
Display (cv2.imshow) is excluded, as it depends on the screen. The first --warmup frames are not counted.

Usage: python scripts/benchmark_latency.py --weights weights/X.pt --video path.mp4 --device 0 --frames 300
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.alerts import AlertManager, EmailConfig, ViolationLog  # noqa: E402
from src.detect import Pipeline  # noqa: E402


def cpu_name() -> str:
    try:
        return subprocess.run(["powershell", "-NoProfile", "-c", "(Get-CimInstance Win32_Processor).Name"],
                              capture_output=True, text=True, timeout=20).stdout.strip() or platform.processor()
    except Exception:
        return platform.processor()


def stats(xs):
    a = np.array(xs)
    return {"mean": round(float(a.mean()), 2), "median": round(float(np.median(a)), 2),
            "p95": round(float(np.percentile(a, 95)), 2), "max": round(float(a.max()), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--device", default="0", help="0 for first CUDA GPU, or cpu")
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--warmup", type=int, default=20)
    ap.add_argument("--conf", type=float, default=0.5)
    ap.add_argument("--out")
    args = ap.parse_args()

    import torch

    dev = "cpu" if args.device == "cpu" else int(args.device)
    hw = {"device": torch.cuda.get_device_name(dev) if dev != "cpu" else cpu_name(), "cpu": cpu_name(),
          "torch": torch.__version__, "python": platform.python_version()}
    cap = cv2.VideoCapture(args.video)
    vid = {"file": Path(args.video).name, "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
           "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), "fps": cap.get(cv2.CAP_PROP_FPS),
           "frames_in_file": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}
    print("hardware:", json.dumps(hw))
    print("video:", json.dumps(vid))

    pipe = Pipeline(args.weights, conf=args.conf, device=dev)
    tmp = Path(tempfile.mkdtemp())
    alerts = AlertManager(vid["file"], db=ViolationLog(tmp / "bench.db"), snapshot_dir=tmp / "snaps",
                          email_cfg=EmailConfig("", 0, "", "", "", False))
    rec = {k: [] for k in ("read", "model_total", "yolo_pre", "yolo_infer", "yolo_post", "rules", "draw", "alerts",
                           "end_to_end")}
    n = counted = 0
    viol_frames = 0
    t_start = None
    while counted < args.frames:
        t0 = time.perf_counter()
        ok, frame = cap.read()
        if not ok:
            break
        t1 = time.perf_counter()
        out = pipe.process(frame)
        t2 = time.perf_counter()
        alerts.handle(frame, out.result)
        t3 = time.perf_counter()
        n += 1
        if n <= args.warmup:
            continue
        if t_start is None:
            t_start = t0
        counted += 1
        viol_frames += bool(out.result.violations)
        rec["read"].append((t1 - t0) * 1e3)
        for k in ("model_total", "yolo_pre", "yolo_infer", "yolo_post", "rules", "draw"):
            rec[k].append(out.timings_ms[k])
        rec["alerts"].append((t3 - t2) * 1e3)
        rec["end_to_end"].append((t3 - t0) * 1e3)
    wall = time.perf_counter() - t_start
    res = {"hardware": hw, "video": vid, "weights": Path(args.weights).name, "conf": args.conf,
           "warmup_frames": args.warmup, "measured_frames": counted, "wall_time_s": round(wall, 2),
           "throughput_fps": round(counted / wall, 2),
           "latency_ms": {k: stats(v) for k, v in rec.items()},
           "frames_with_violation": viol_frames, "alerts_logged_after_cooldown": alerts.n_alerts}
    print(json.dumps(res, indent=2))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(res, indent=2))
    if counted < args.frames:
        print(f"NOTE: video ended after {counted} measured frames (requested {args.frames})")


if __name__ == "__main__":
    main()
