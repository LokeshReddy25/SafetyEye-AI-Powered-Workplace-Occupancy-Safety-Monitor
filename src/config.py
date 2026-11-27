"""Central configuration. Values can be overridden via environment / .env."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = Path(os.getenv("SAFETYEYE_DATASET", r"C:/Users/acer/Desktop/DataSet/css-data"))
SOURCE_VIDEOS = DATASET_ROOT.parent / "source_files" / "source_files"

CONFIGS = ROOT / "configs"
DATA_YAML = CONFIGS / "data.yaml"
SPLITS_DIR = ROOT / "data" / "splits"          # gitignored: cleaned image lists
RESULTS = ROOT / "results"
RAW = RESULTS / "raw"
RUNS = ROOT / "runs"
WEIGHTS = ROOT / "weights"                     # gitignored
VIOLATIONS_DIR = ROOT / "violations"           # gitignored: snapshots + sqlite
VIOLATIONS_DB = VIOLATIONS_DIR / "violations.db"

# Class names exactly as in the dataset's own YAML (ppe_data.yaml shipped with the Kaggle dataset).
# Index order matches the label files (ids 0..9).
CLASS_NAMES = [
    "Hardhat", "Mask", "NO-Hardhat", "NO-Mask", "NO-Safety Vest",
    "Person", "Safety Cone", "Safety Vest", "machinery", "vehicle",
]

# Dataset split folder names (the dataset uses "valid", not "val")
SPLITS = {"train": "train", "val": "valid", "test": "test"}
