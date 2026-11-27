from pathlib import Path

import cv2
import numpy as np
import pytest

from src import config
from src.data_prep.validate import check_label_text, source_stem, validate_split

NC = len(config.CLASS_NAMES)


def test_valid_label():
    r = check_label_text("0 0.5 0.5 0.2 0.3\n5 0.1 0.1 0.05 0.05\n", NC)
    assert r.ok and r.n_boxes == 2 and r.classes == [0, 5]


def test_empty_label_is_background_not_error():
    r = check_label_text("", NC)
    assert r.ok and r.n_boxes == 0


@pytest.mark.parametrize("line,msg", [
    ("0 0.5 0.5 0.2", "expected 5 fields"),
    ("10 0.5 0.5 0.2 0.2", "out of range"),
    ("-1 0.5 0.5 0.2 0.2", "out of range"),
    ("0 1.5 0.5 0.2 0.2", "outside [0,1]"),
    ("0 0.5 0.5 0 0.2", "zero/negative"),
    ("a 0.5 0.5 0.2 0.2", "non-numeric"),
])
def test_invalid_labels(line, msg):
    r = check_label_text(line, NC)
    assert not r.ok and any(msg in e for e in r.errors)


def test_duplicate_box_flagged():
    r = check_label_text("1 0.5 0.5 0.2 0.2\n1 0.5 0.5 0.2 0.2\n", NC)
    assert not r.ok


def test_source_stem():
    assert source_stem("youtube-51_jpg.rf.083f4487f9a468d9ff42aa13953f377a.jpg") == "youtube-51_jpg"
    assert source_stem("plain.jpg") == "plain"


def test_validate_split_handles_corrupt_and_missing(tmp_path: Path):
    (tmp_path / "images").mkdir()
    (tmp_path / "labels").mkdir()
    cv2.imwrite(str(tmp_path / "images" / "good.jpg"), np.zeros((8, 8, 3), np.uint8))
    (tmp_path / "labels" / "good.txt").write_text("0 0.5 0.5 0.5 0.5\n")
    (tmp_path / "images" / "corrupt.jpg").write_bytes(b"not an image")
    (tmp_path / "labels" / "corrupt.txt").write_text("0 0.5 0.5 0.5 0.5\n")
    cv2.imwrite(str(tmp_path / "images" / "nolabel.jpg"), np.zeros((8, 8, 3), np.uint8))
    (tmp_path / "labels" / "orphan.txt").write_text("")
    r = validate_split(tmp_path, NC)
    assert r["corrupt_images"] == ["corrupt.jpg"]
    assert r["images_without_label"] == ["nolabel"]
    assert r["labels_without_image"] == ["orphan"]
    assert [p.name for p in r["kept"]] == ["good.jpg"]


@pytest.mark.skipif(not config.DATASET_ROOT.exists(), reason="real dataset not on this machine")
def test_real_dataset_split_sizes():
    """Counts measured on the real dataset; guards against the path silently changing."""
    for folder, n in (("train", 2605), ("valid", 114), ("test", 82)):
        assert len(list((config.DATASET_ROOT / folder / "images").glob("*.jpg"))) == n
