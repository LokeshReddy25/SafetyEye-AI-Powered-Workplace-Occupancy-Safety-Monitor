# SafetyEye – Results summary

Every number below comes from a command whose full output is in `results/raw/`. Measured 2026-11-27.

**Hardware:** NVIDIA GeForce RTX 3050 Ti Laptop GPU (4 GB) · Intel Core i5-12500H · 15.7 GB RAM · Windows 11 ·
Python 3.11.9 · torch 2.6.0+cu124 · ultralytics 8.4.220

**Dataset:** Kaggle "Construction Site Safety Image Dataset (Roboflow)", 10 classes, official splits:
train 2605 (2603 used, 2 excluded for duplicate-box labels) / val 114 / test 82 images.
Log: [results/raw/data_validation.txt](results/raw/data_validation.txt)

## Model selection (validation split)
| Run | Model / change | Epochs | Train time | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---:|---:|---:|---:|
| A | YOLOv8n, default aug | 50 | 50.9 min | 0.767 | 0.455 |
| B | YOLOv8n, stronger aug (rot 5°, scale 0.7, mixup 0.15) | 50 | 68.2 min | 0.737 | 0.375 |
| **C** | **YOLOv8s, default aug** | 50 | 103.2 min | **0.842** | **0.563** |

Common settings: imgsz 640, batch 16, seed 0, deterministic, SGD lr0 0.01, COCO-pretrained.
Winner: **C**. Full table: [results/tuning_comparison.md](results/tuning_comparison.md).

## Final model C on the TEST split (82 images, 760 boxes)
| | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|
| all classes | 0.911 | 0.728 | 0.790 | 0.498 |
| NO-Hardhat | 0.864 | 0.618 | 0.591 | 0.314 |
| NO-Safety Vest | 0.943 | 0.741 | 0.809 | 0.503 |
| Person | 0.937 | 0.799 | 0.879 | 0.569 |

Per-class table for all 10 classes: [results/eval/test_C_v8s_default_aug/per_class.md](results/eval/test_C_v8s_default_aug/per_class.md).
Raw log: [results/raw/eval_test_C_v8s_default_aug.txt](results/raw/eval_test_C_v8s_default_aug.txt)

## Real-time pipeline (hardhat.mp4, 640×360, 500 frames after 20 warm-up)
| Model | Device | FPS | End-to-end mean / p95 |
|---|---|---:|---:|
| YOLOv8s (selected) | RTX 3050 Ti Laptop GPU | 96.1 | 10.4 / 12.9 ms |
| YOLOv8n | RTX 3050 Ti Laptop GPU | 115.4 | 8.7 / 13.0 ms |
| YOLOv8s (selected) | i5-12500H CPU | 11.2 | 89.7 / 98.1 ms |

## Tests
29/29 pytest tests pass: [results/raw/pytest.txt](results/raw/pytest.txt)

## Not measured
Violation-level (rule engine) accuracy on real video · webcam input · real SMTP delivery (mock only) ·
run-to-run variance (single seed). See the README's "Not measured / limitations" section.
