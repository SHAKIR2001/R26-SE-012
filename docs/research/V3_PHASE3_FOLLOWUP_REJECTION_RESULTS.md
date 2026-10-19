# V3 Phase 3 Follow-up — Non-Pepper Rejection Results

## 1. Objective

Determine whether controlled YOLO11n hard-negative fine-tuning reduces non-pepper vegetation/crop false acceptance without unacceptable loss of genuine-pepper coverage or G1/G2 grading performance. This is a research experiment, not production or field validation.

## 2. Phase 3 baseline

The frozen Phase 3 result was 35/40 (87.5%) held-out non-pepper rejection, 5/40 (12.5%) false acceptance, and all five false accepts were vegetation/crop images. Valid-pepper validation coverage was 111/116 (95.69%) with five false rejections.

## 3. Research hypothesis

Adding diverse, source-controlled non-pepper images as empty-label YOLO hard negatives will reduce vegetation/crop false acceptance without unacceptable valid-pepper or grading regression. Final result: **SUPPORTED**.

## 4. Dataset construction

Open-license results were collected through the Wikimedia Commons API, with Openverse available as a documented fallback, using resumable per-file caching. Actual source counts are `{"Wikimedia Commons": 250}`. The manifest records creator, license, source page, media URL, timestamp, dimensions, and SHA-256. Exact SHA-256 deduplication excluded overlap with all 775 V3 images and the frozen 80-image Phase 3 set. Creator/source groups were kept in one partition. Collected 250 usable images; split counts: `{"NEGATIVE_FINAL_HOLDOUT": 49, "NEGATIVE_TRAIN": 152, "NEGATIVE_VALIDATION": 49}`. The final holdout remained sealed until model and threshold freeze.

## 5. Training method

One-shot hard-negative fine-tuning initialized from the frozen Phase 2 checkpoint. Only 539 Phase 1 TRAIN positives and 152 empty-label negatives were used. Validation contained 116 Phase 1 VALIDATION positives and 49 negatives. YOLO11n, 640 px, batch 4, seed 42, AdamW, LR 0.0001, weight decay 0.0005, maximum 30 epochs, patience 8. Early stopping ended training after epoch 27 and selected epoch 19 as the best checkpoint. Cumulative training duration across the interrupted and resumed invocations: 2620.8 seconds.

## 6. Threshold selection

The complete validation-only scan is in `validation_threshold_scan.csv`. Candidates were 0.05–0.90 in 0.05 increments. Thresholds below 95% valid-pepper coverage were excluded; the remaining point with maximum negative rejection, then accepted-pepper macro F1, then coverage, then lowest threshold was selected: **0.05**. The Phase 3 quality thresholds and 0.30 class-margin rule were preserved.

## 7. Validation results

- Valid coverage: 114/116 (98.28%)
- Valid false rejection: 2/116 (1.72%)
- Accepted-subset accuracy/macro F1: 95.61% / 0.9539
- Negative rejection: 49/49 (100.00%)

On the same 116 validation images, the frozen Phase 3 baseline had 95.69% coverage, 4.31% false rejection, 97.30% accepted accuracy, and 0.9725 accepted macro F1.

## 8. Final unseen negative results

The holdout was evaluated once after freezing. Rejected 49/49 (100.00%); false accepted 0/49 (0.00%). Binary precision=1.0000, recall=1.0000, F1=1.0000; balanced accuracy is undefined because this holdout contains only the non-pepper class.

| Category | N | Rejected | Accepted | Rejection rate |
|---|---:|---:|---:|---:|
| aerial_crop_imagery | 2 | 2 | 0 | 100.00% |
| agricultural_crops | 14 | 14 | 0 | 100.00% |
| agricultural_materials | 5 | 5 | 0 | 100.00% |
| background_scenes | 2 | 2 | 0 | 100.00% |
| ordinary_objects | 2 | 2 | 0 | 100.00% |
| other_spices_food | 5 | 5 | 0 | 100.00% |
| vegetation_leaves | 19 | 19 | 0 | 100.00% |

## 9. Genuine pepper regression

On the once-accessed Phase 2 positive TEST: coverage 98.33%, false rejection 1.67%, accuracy 0.9583, balanced accuracy 0.9542, macro precision 0.9753, macro recall 0.9542, macro F1 0.9643, weighted F1 0.9661, G1 F1 0.9781, G2 F1 0.9505.

## 10. Original Phase 3 comparison

Frozen baseline: 87.5% rejection. Frozen follow-up model, retrospectively evaluated after all selection: 100.00% rejection. This retrospective set is not an independent test set for the adapted model and did not trigger tuning.

## 11. Phase 2 grading regression

Frozen Phase 2: accuracy 0.9583, macro F1 0.9578, G1 F1 0.9624, G2 F1 0.9533. Follow-up: accuracy 0.9583, macro F1 0.9643, G1 F1 0.9781, G2 F1 0.9505. Rejections: 2.

## 12. Error analysis

Every new-holdout false accept and Phase 2 TEST false rejection is listed in `final_error_analysis.csv`. Causes are marked uncertain unless directly supported; no causal explanation was invented. Representative successes and failures are shown in `representative_examples.png`.

## 13. Hard-negative effectiveness

On the same new unseen holdout, the frozen control rejected 71.43%; the treatment rejected 100.00%, a +28.57 percentage-point change. Vegetation/crop/aerial results are separately preserved in the metrics JSON. The hypothesis is **SUPPORTED**.

| Metric | Frozen control | Follow-up | Change |
|---|---:|---:|---:|
| Validation valid-pepper coverage (same 116 images) | 95.69% | 98.28% | +2.59 pp |
| Validation false rejection (same 116 images) | 4.31% | 1.72% | -2.59 pp |
| Validation accepted accuracy | 97.30% | 95.61% | -1.68 pp |
| Validation accepted macro F1 | 0.9725 | 0.9539 | -0.0186 |
| New unseen negative rejection (same 49 images) | 71.43% | 100.00% | +28.57 pp |
| New unseen vegetation/crop/aerial rejection | 60.00% | 100.00% | +40.00 pp |
| Original Phase 3 negative rejection (same 40 images) | 87.50% | 100.00% | +12.50 pp |

The predeclared interpretation implemented before final access requires at least a 10 percentage-point same-holdout rejection improvement, at least 95% Phase 2 TEST coverage, and no more than 0.02 absolute macro-F1 loss for `SUPPORTED`. A positive improvement meeting only part of the safety/grading constraints is `PARTIALLY SUPPORTED`; otherwise it is `NOT SUPPORTED`.

## 14. Limitations

Internet imagery does not represent field deployment; categories and creator groups remain finite; semantic near-duplicate detection was not claimed; camera/domain shift and confidence calibration were not solved; confidence values are model confidence scores, not probabilities; and the unseen holdout is modest. Collection froze at 250 usable images, below the nominal 300-image target, after repeated Wikimedia transfer failures dominated progress; the resumable manifest records 199 failed attempts and four rejected downloads. The original five Phase 3 false accepts were not used for training.

## 15. Decision

**COMPLETE — OPERATIONAL GATE IMPROVED**

This result does not establish production readiness or camera-independent field robustness. Do not proceed to Phase 6 automatically.
