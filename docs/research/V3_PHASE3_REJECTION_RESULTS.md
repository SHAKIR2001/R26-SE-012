# V3 Phase 3 Rejection, Image-Quality, and Uncertainty Results

**Project:** Multimodal Pepper AI Decision Support System  
**Individual component:** Berry Grading and Export Price Forecasting  
**Phase:** 3 - Non-Pepper Rejection, Image-Quality Gating, and Uncertainty Calibration  
**Experiment date:** 2026-10-07  
**Experiment ID:** `BERRY-V3-YOLO11N-PHASE3-001`  
**Status:** **PHASE 3 EVALUATION COMPLETE - OPERATIONAL REJECTION NOT YET SUFFICIENT**

## 1. Scope and preservation

Phase 3 evaluated the frozen Phase 2 YOLO11n checkpoint at:

```text
ml/grading_forecast/berry_grading/models/v3_yolo/best.pt
```

The checkpoint SHA-256 was verified before and after inference:

```text
c35cc40515adcb6130a4bc93e8ad3de161dcf46b263a9d7df8286a5b4239a9c4
```

No model was trained or modified. No V3 image or YOLO annotation was changed. The Phase 2 sealed 120-image TEST partition was not loaded, inspected, or used. Calibration used only the 116-image group-aware VALIDATION partition and a predeclared 40-image calibration subset of the external negatives. The other 40 external negatives remained held out until the decision rules were frozen.

No V1/V2 artifact, backend, mobile application, price-forecasting implementation, or Phase 4 component was modified.

## 2. External negative dataset

The evaluation created a separate, versioned 80-image non-pepper dataset from Wikimedia Commons thumbnails. It is not mixed into V3 and is not training data.

| Property | Result |
| --- | ---: |
| Images | 80 |
| Retrieval strata | 10 |
| Images per stratum | 8 |
| Calibration negatives | 40 |
| Held-out evaluation negatives | 40 |
| Unique SHA-256 hashes | 80 |
| Hash overlap with V3 | 0 |
| Download size | 20,540,794 bytes |
| Source-page metadata present | 80/80 |
| License metadata present | 80/80 |

The retrieval strata were people, vehicles/transport, buildings/interiors, leaves/plants, other crops, other spices/food, soil/ground/outdoor scenes, containers, random objects, and empty/background scenes. These are retrieval strata rather than formal semantic labels: broad search results sometimes include adjacent scene types. The contact sheet was manually inspected before evaluation and all 80 images were confirmed to be non-pepper.

The manifest records image ID, retrieval stratum, Phase 3 partition, search query, source page, download URL, Commons title, creator, license name/URL, attribution text, local path, SHA-256, and byte size. Wikimedia Commons' reuse guidance and the MediaWiki `imageinfo` API were used to retain source and license metadata: <https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia> and <https://www.mediawiki.org/wiki/API:Imageinfo>.

Important limitation: this is a bounded public-image diagnostic set, not a statistically representative sample of real smartphone misuse or field deployment inputs.

## 3. Frozen-model baseline on all 80 negatives

The unmodified model was evaluated at the two requested operating points before the consolidated gate was interpreted.

| Detection confidence | Correctly rejected | Rejection rate | False accepts | False-acceptance rate | Predicted Grade 1 | Predicted Grade 2 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.05 | 58/80 | 72.5% | 22/80 | 27.5% | 6 | 16 |
| 0.25 | 65/80 | 81.25% | 15/80 | 18.75% | 6 | 9 |

The strongest baseline confusion was vegetation-like imagery. At confidence 0.25, 6/8 leaves/plants and 4/8 other-crop images were falsely accepted. This confirms that YOLO detection alone does not reliably solve non-pepper rejection for this checkpoint.

## 4. Validation-only threshold calibration

All candidate grids and deterministic selection rules were recorded in `phase3_config.yaml` before inference.

### 4.1 Detection threshold

The detector threshold was selected from 0.05-0.95 using the 116 valid validation images and 40 calibration negatives. The rule minimized calibration-negative false acceptance subject to retaining at least 95% of valid validation images, then maximized positive retention, then chose the lower tied threshold.

Selected threshold:

```text
detection confidence >= 0.55
```

At this point, 116/116 validation pepper images were detected and 6/40 calibration negatives still passed detection. Increasing the threshold to 0.75 reduced calibration false accepts to 5/40 but retained only 109/116 valid images (93.97%), violating the predeclared 95% retention constraint. A threshold alone therefore could not remove the systematic hard negatives without excessive valid-input rejection.

### 4.2 Quality thresholds

Quality thresholds used simple interpretable features:

| Feature | Selected rule |
| --- | ---: |
| Laplacian blur variance | at least 10 |
| Mean grayscale brightness | at least 50/255 |
| Minimum image dimension | at least 320 pixels |
| Detected-box area / image area | at least 0.20 |

Calibration used 12 validation originals, balanced across grades and physical groups, to create 36 controlled challenges: 12 Gaussian-blurred, 12 darkened, and 12 low-resolution images. Each selected threshold rejected 12/12 of its corresponding controlled challenge and rejected 0/116 unmodified validation images. The box-area threshold also rejected 0/116 natural validation images.

These results demonstrate deterministic behavior on controlled perturbations only. They do not establish field sensitivity or specificity for naturally blurred, dark, distant, or low-resolution smartphone images.

### 4.3 Uncertainty rule

The standard YOLO result exposes post-NMS per-box class confidence. For each image, Phase 3 recorded the highest confidence for each grade class where present and defined:

```text
class margin = highest-class confidence - other-class confidence
```

This is an abstention heuristic, not probability calibration. Only 11/116 validation images had a non-zero runner-up class after post-processing, so the margin has limited resolution.

Validation-only selection required at least 90% coverage and both grades among accepted predictions. It maximized macro F1 among accepted predictions, then accepted accuracy, coverage, and lower thresholds.

Selected rules:

```text
grade confidence >= 0.05
class margin >= 0.30
```

The margin rule rejected five validation images as `UNCERTAIN_GRADE`: three would otherwise have been correct and two would have been incorrect.

## 5. Consolidated decision logic

The frozen decision order is:

```text
1. image readability / minimum dimension / brightness / blur
2. pepper detection confidence
3. detected-box area
4. grade confidence and class margin
5. Grade 1 or Grade 2
```

The implementation returns exactly one of:

- `GRADE_1`
- `GRADE_2`
- `POOR_IMAGE`
- `NO_PEPPER`
- `UNCERTAIN_GRADE`

It also returns a user-facing message, grade when applicable, model/detection confidence, class margin, quality scores, rejection reason, bounding box, and the frozen threshold set.

## 6. Final consolidated evaluation

The final matrix uses all 116 validation pepper images and the 40 held-out external evaluation negatives. Rows are input type; columns are final decision.

| Input | GRADE_1 | GRADE_2 | POOR_IMAGE | NO_PEPPER | UNCERTAIN_GRADE |
| --- | ---: | ---: | ---: | ---: | ---: |
| Valid pepper (116) | 61 | 50 | 0 | 0 | 5 |
| Held-out non-pepper (40) | 3 | 2 | 2 | 33 | 0 |

### 6.1 Valid validation pepper

| Metric | Result |
| --- | ---: |
| Coverage / accepted for grading | 111/116 = 95.69% |
| False rejections | 5/116 = 4.31% |
| Accepted-subset accuracy | 108/111 = 97.30% |
| Accepted-subset macro F1 | 0.9725 |
| Accepted confusion matrix, true rows Grade 1/2 | `[[61, 3], [0, 47]]` |

All five false rejections were uncertainty abstentions. No natural validation image was rejected for quality or absence of pepper.

### 6.2 Held-out non-pepper

| Metric | Result |
| --- | ---: |
| Correctly rejected | 35/40 = 87.5% |
| False accepts | 5/40 = 12.5% |
| `NO_PEPPER` | 33 |
| `POOR_IMAGE` | 2 |
| Falsely graded as Grade 1 | 3 |
| Falsely graded as Grade 2 | 2 |

The five held-out false accepts were three leaves/plants and two other-crop images. Their confidences were 0.589, 0.703, 0.782, 0.812, and 0.943. The 0.943 false positive was an aerial crop image whose predicted box covered the full image. This is a systematic vegetation/crop failure pattern rather than only a borderline-threshold problem.

## 7. Error analysis

Representative artifacts include:

- a confident valid Grade 1 prediction;
- a validation uncertainty abstention;
- a correctly rejected non-pepper scene;
- a high-confidence crop false acceptance; and
- controlled blur, darkness, and low-resolution quality failures.

The negative false-acceptance pattern is consistent with the Phase 1 shortcut risk: the detector can respond to broad green/textured plant or crop regions that resemble the training image's sample-scale texture. Bounding boxes show where detections occurred but do not prove causal reasoning.

The quality gate solves a different problem from semantic non-pepper rejection. Blur, brightness, size, and area tests can reject unreadable images, but a sharp, bright, full-frame crop or leaf image can pass all quality checks and still be semantically invalid.

## 8. Scientific interpretation

### Demonstrated

- The frozen YOLO11n pipeline exposes a deterministic no-detection state.
- A validation-calibrated five-state decision interface can preserve 95.69% coverage while raising accepted-subset accuracy to 97.30%.
- Simple quality rules reject all predeclared controlled blur/dark/low-resolution challenges without rejecting the natural validation images.
- The held-out external set provides direct evidence that the current checkpoint rejects many ordinary non-pepper images.
- The experiment identifies a reproducible, high-confidence vegetation/crop false-positive failure mode.

### Not demonstrated

- Operationally reliable non-pepper rejection.
- Calibrated probabilities or open-set recognition.
- Field performance on naturally poor smartphone images.
- Official SLS or buyer-grade recognition.
- Per-berry detection or grading.
- Camera-independent reasoning, mobile runtime, or price correctness.

## 9. Retraining decision and gate

The frozen checkpoint has a clear systematic hard-negative failure: 5/40 held-out negatives are accepted after the complete gate, and all five are vegetation/crop images with confidence as high as 0.943. Raising the confidence threshold enough to remove these errors would violate the predeclared valid-pepper retention constraint.

Therefore, controlled hard-negative retraining or another explicitly authorized open-set strategy is scientifically justified. It was not performed because Phase 3 forbids silent retraining and requires stopping when such evidence appears.

```text
PHASE 3 STATUS: COMPLETE
OPERATIONAL REJECTION GATE: NOT PASSED
PHASE 4 READINESS: NO
NEXT DECISION: AUTHORIZE A SEPARATE CONTROLLED HARD-NEGATIVE EXPERIMENT
```

This does not erase the Phase 2 grading result. It narrows the claim: the frozen model grades positive V3 pepper samples well, but it does not yet reject visually related non-pepper content reliably enough for deployment.

## 10. Reproducible artifacts

- `data/external/phase3_rejection/non_pepper/`
- `data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv`
- `data/processed/grading_forecast/berry_v3/phase3_negative_dataset_summary.json`
- `ml/grading_forecast/berry_grading/rejection/phase3/download_external_negatives.py`
- `ml/grading_forecast/berry_grading/rejection/phase3/make_negative_contact_sheet.py`
- `ml/grading_forecast/berry_grading/quality/phase3/decision_pipeline.py`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/phase3_config.yaml`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/run_phase3.py`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/external_negative_contact_sheet.png`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/negative_baseline_metrics.json`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/detection_threshold_calibration.json`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/quality_calibration.json`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/uncertainty_calibration.json`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/decision_config_frozen.json`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/validation_decisions.csv`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/negative_predictions.csv`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/phase3_metrics.json`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/representative_phase3_examples.json`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/representative_phase3_examples.png`

The controlled challenge pixels under `data/processed/grading_forecast/berry_v3/phase3_quality_challenges/` are reproducibly generated and ignored by Git; their generation parameters and results are preserved in code and JSON.
