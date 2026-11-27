# Hyperparameter / model comparison (selection on the VALIDATION split only)

All runs: 50 epochs, imgsz 640, batch 16, seed 0, deterministic, SGD lr0=0.01, COCO-pretrained weights,
RTX 3050 Ti Laptop GPU (4 GB). Val split = 114 images / 697 boxes. Metrics from `src/evaluate.py --split val --device cpu`
(Ultralytics val, conf=0.001, IoU=0.7).

| Run | Model | Augmentation (differences from Ultralytics default) | Train time | Val P | Val R | Val mAP@0.5 | Val mAP@0.5:0.95 | Log |
|---|---|---|---:|---:|---:|---:|---:|---|
| A | YOLOv8n | default (hsv 0.015/0.7/0.4, translate 0.1, scale 0.5, fliplr 0.5, mosaic 1.0, close_mosaic 10) | 50.9 min | 0.885 | 0.685 | 0.767 | 0.455 | [train](raw/train_A_v8n_default_aug.txt), [eval](raw/eval_val_A_v8n_default_aug.txt) |
| B | YOLOv8n | stronger: degrees 5, scale 0.7, mixup 0.15 | 68.2 min | 0.874 | 0.653 | 0.737 | 0.375 | [train](raw/train_B_v8n_strong_aug.txt), [eval](raw/eval_val_B_v8n_strong_aug.txt) |
| **C** | **YOLOv8s** | default (same as A) | 103.2 min | **0.907** | **0.770** | **0.842** | **0.563** | [train](raw/train_C_v8s_default_aug.txt), [eval](raw/eval_val_C_v8s_default_aug.txt) |

**Winner: C (YOLOv8s, default augmentation)**. It has the highest val mAP@0.5 (+0.075 over A) and mAP@0.5:0.95 (+0.108),
and is ahead of A on every class's val mAP@0.5. Only run C was then evaluated on the test split.

**Why B lost:** the dataset was already exported by Roboflow with heavy augmentation (5 copies per source image with flip,
crop, ±12° rotation, shear, brightness/exposure, blur; some images are mosaics with cutout squares). Adding more geometric
augmentation and mixup on top lowered every overall val metric. This is one run per setting (seed 0), so a small gap could be
noise, but A beat B on all four overall metrics.

**Cost of C:** about 2x the training time of A, and about 3.5x the compute (28.7 vs 8.2 GFLOPs; 11.1M vs 3.0M parameters, from the Ultralytics model summary in the training logs).
Its inference latency is measured in `results/raw/benchmark_*.txt`.

Not done: no grid/evolutionary search (`model.tune`), no multiple seeds, no YOLOv8m (would not fit comfortably in 4 GB at batch 16).
