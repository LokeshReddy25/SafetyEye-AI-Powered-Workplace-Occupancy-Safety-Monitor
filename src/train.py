"""Module 2 – Train YOLOv8 on the Construction Site Safety dataset.

Usage:
    python -m src.train --config configs/train_baseline.yaml [--epochs N] [--name NAME]

Every run is saved to runs/train/<name>/ by Ultralytics. Afterwards the small artifacts
(results.csv, curves, confusion matrix, PR curve, args.yaml) are copied into
results/train/<name>/ (committed), and best.pt is copied to weights/<name>.pt (gitignored).
Model selection between runs uses the VALIDATION split only; the test split is touched
only by src/evaluate.py on the chosen model.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import time

import torch
import yaml
from ultralytics import YOLO

from src import config

ARTIFACTS = [
    "results.csv", "results.png", "args.yaml", "confusion_matrix.png", "confusion_matrix_normalized.png",
    "BoxPR_curve.png", "BoxP_curve.png", "BoxR_curve.png", "BoxF1_curve.png",
    "PR_curve.png", "P_curve.png", "R_curve.png", "F1_curve.png", "labels.jpg",
    "train_batch0.jpg", "val_batch0_labels.jpg", "val_batch0_pred.jpg",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--epochs", type=int)
    ap.add_argument("--name")
    args = ap.parse_args()

    if not config.DATA_YAML.exists():
        raise SystemExit("configs/data.yaml missing – run `python -m src.data_prep.validate` first")

    cfg = yaml.safe_load(open(args.config))
    model_name = cfg.pop("model")
    name = args.name or cfg.pop("name")
    cfg.pop("name", None)
    if args.epochs:
        cfg["epochs"] = args.epochs

    hw = {
        "python": platform.python_version(), "torch": torch.__version__,
        "cuda": torch.version.cuda, "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else
        platform.processor(),
    }
    print("Hardware/software:", json.dumps(hw))
    print("Model:", model_name, "| run:", name, "| settings:", json.dumps(cfg))

    model = YOLO(model_name)
    t0 = time.perf_counter()
    model.train(data=str(config.DATA_YAML), project=str(config.RUNS / "train"), name=name, exist_ok=True,
                **cfg)
    elapsed = time.perf_counter() - t0
    print(f"TRAINING_WALL_TIME_S={elapsed:.1f}  ({elapsed / 60:.1f} min)")

    run_dir = config.RUNS / "train" / name
    out = config.RESULTS / "train" / name
    out.mkdir(parents=True, exist_ok=True)
    for f in ARTIFACTS:
        if (run_dir / f).exists():
            shutil.copy2(run_dir / f, out / f)
    config.WEIGHTS.mkdir(exist_ok=True)
    best = run_dir / "weights" / "best.pt"
    if best.exists():
        shutil.copy2(best, config.WEIGHTS / f"{name}.pt")
    (out / "run_info.json").write_text(json.dumps(
        {"model": model_name, "settings": cfg, "hardware": hw, "train_wall_time_s": round(elapsed, 1)}, indent=2))
    print(f"Copied artifacts to {out}")


if __name__ == "__main__":
    main()
