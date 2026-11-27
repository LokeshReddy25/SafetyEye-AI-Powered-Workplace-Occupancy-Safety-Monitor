# Resume claims check

Each claim you might write, whether the evidence in this repo supports it, and the evidence file.

| # | Claim | Supported? | Evidence / note |
|---|---|---|---|
| 1 | Fine-tuned YOLOv8 to detect 10 PPE/site classes on the Construction Site Safety dataset (~2.6k training images) | **Yes** | [train_C log](raw/train_C_v8s_default_aug.txt), [data_validation](raw/data_validation.txt) |
| 2 | Achieved **0.79 mAP@0.5** (0.50 mAP@0.5:0.95) on a held-out test set | **Yes** (test split, 82 images) | [eval_test log](raw/eval_test_C_v8s_default_aug.txt): 0.790 / 0.498 |
| 3 | "91% precision, 73% recall" on test | **Yes**, overall averaged over classes at the max-F1 threshold | same log: P 0.911, R 0.728 |
| 4 | "~80% accuracy" / "95% accuracy" | **No.** Detection has no single "accuracy" number. Use mAP. | – |
| 5 | Detects missing hardhats with high reliability | **Weak, avoid.** NO-Hardhat test recall is 0.618 and mAP@0.5 is 0.591 | [per_class.md](eval/test_C_v8s_default_aug/per_class.md) |
| 6 | Compared 3 training configurations (model size, augmentation) and improved val mAP@0.5 from 0.767 to 0.842 | **Yes** (validation split, single seed) | [tuning_comparison.md](tuning_comparison.md) |
| 7 | "Data augmentation improved accuracy" | **No.** The stronger-augmentation run was worse (0.737 vs 0.767 val mAP@0.5). The model-size change is what helped. | [tuning_comparison.md](tuning_comparison.md) |
| 8 | Real-time inference at **~96 FPS (10.4 ms/frame end-to-end) on an RTX 3050 Ti laptop GPU** | **Yes**, on a 640×360 video file, display excluded | [benchmark GPU log](raw/benchmark_C_v8s_default_aug_gpu.txt) |
| 9 | Runs in real time on CPU | **No.** 11.2 FPS on an i5-12500H with YOLOv8s, below the video's 30 fps | [benchmark CPU log](raw/benchmark_C_v8s_default_aug_cpu.txt) |
| 10 | Built a rule engine flagging missing hardhat/vest per worker, with alert cooldown, unit-tested | **Yes** | [src/rules.py](../src/rules.py), [pytest log](raw/pytest.txt) |
| 11 | "Violation detection accuracy X%" (event level) | **Not measured.** No labelled video exists. Do not claim it. | – |
| 12 | Alerts via console, SQLite log with snapshots, and SMTP email | **Partly.** Console, SQLite and snapshots ran on real video. Email is tested only with a mocked SMTP server, not sent for real. | [detect_hardhat_full log](raw/detect_hardhat_full.txt), [tests/test_alerts.py](../tests/test_alerts.py) |
| 13 | Streamlit dashboard with live feed, compliance charts and searchable violation history | **Yes** | [docs/dashboard_*.png](../docs/) |
| 14 | Works with a webcam | **Implemented, not tested.** No webcam run was done. | – |
| 15 | "Production-ready" / "deployed" | **No.** It ran locally only, on a small test set, with no field validation. | – |
| 16 | Validated dataset integrity and checked train/test leakage | **Yes** | [data_validation](raw/data_validation.txt), [leakage_visual_check](raw/leakage_visual_check.txt) |
| 17 | 29 automated tests | **Yes** | [pytest log](raw/pytest.txt) |

## Suggested resume bullet (supported by the evidence above)

> Built **SafetyEye**, a real-time PPE-violation monitor: fine-tuned YOLOv8s on a 10-class construction-safety dataset
> (0.79 mAP@0.5 / 0.50 mAP@0.5:0.95 on a held-out test set), selected from 3 training configurations by validation mAP.
> Added a unit-tested rule engine (missing hardhat or vest per worker, with alert cooldown), SQLite logging with snapshots,
> email alerts and a Streamlit compliance dashboard. The full pipeline runs at about 96 FPS end-to-end on an RTX 3050 Ti laptop GPU.
