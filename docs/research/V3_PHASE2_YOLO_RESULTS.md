# V3 Phase 2 YOLO Results

**Project:** Multimodal Pepper AI Decision Support System  
**Individual component:** Berry Grading and Export Price Forecasting  
**Phase:** 2 - V3 YOLO-Based Harvested Pepper Sample Detection and Grade Classification  
**Experiment date:** 2026-10-07  
**Experiment ID:** `BERRY-V3-YOLO11N-001`  
**Status:** **PHASE 2 COMPLETE**

## 1. Research task and scope

This experiment evaluated YOLO-based harvested pepper sample detection and grade classification. The unit of prediction is the harvested pepper sample/batch shown in one smartphone image. It is not individual-berry detection, individual-berry classification, or berry-by-berry grading.

The model predicts one of two annotated sample-level detection classes:

```text
0 = V3 Grade 1
1 = V3 Grade 2
```

For image-level grading, the highest-confidence detection is used. If no detection exists or its confidence is below the frozen threshold, the image receives `REJECT`. This implements a no-detection state, but Phase 2 does not measure non-pepper rejection accuracy because V3 contains only positive pepper images.

Ultralytics YOLO11 exposes one post-NMS per-box confidence associated with the predicted class; it does not expose a second independent objectness value through the standard result object. The prediction artifacts therefore record predicted grade, this detection/class confidence, bounding box, acceptance state, and inference time without inventing a separate score.

No V1/V2 artifact, canonical V3 image, canonical YOLO annotation, backend, mobile application, or price-forecasting implementation was intentionally changed.

## 2. Data and leakage controls

The experiment used the canonical Roboflow V3 images and YOLO annotations through a manifest-defined derived working layer:

```text
canonical V3 Roboflow export
        +
v3_image_sample_manifest.csv
        +
v3_group_split_manifest.csv
        |
        v
Phase 2 materialized working copies + data.yaml
```

| Partition | Physical samples | Images | V3 Grade 1 | V3 Grade 2 |
| --- | ---: | ---: | ---: | ---: |
| TRAIN | 135 | 539 | 312 | 227 |
| VALIDATION | 29 | 116 | 68 | 48 |
| TEST | 30 | 120 | 68 | 52 |
| **Total** | **194** | **775** | **448** | **327** |

Programmatic preparation checks passed before training:

- all 775 manifest hashes matched the canonical images;
- every image had exactly one YOLO annotation;
- annotation class IDs matched the manifest;
- TRAIN, VALIDATION, and TEST sample-ID intersections were empty;
- all 775 images appeared in exactly one partition; and
- the generated image lists contained exactly 539/116/120 images.

The original Roboflow split was not used as the research split. The final TEST partition was not used for training, checkpoint selection, threshold selection, or preprocessing decisions.

### 2.1 Canonical-data safeguard

An initial framework scan revealed that Ultralytics automatically repairs missing/corrupt JPEG end markers and saves the repaired file. That first scan was stopped before an epoch began. Every affected canonical file was restored byte-for-byte from its exact SHA-256-matched source image, and a complete audit then found 775/775 canonical hashes correct.

The final experiment used ignored materialized working copies so any framework JPEG repair occurred only in the derived layer. A final post-evaluation canonical audit again found:

```text
Canonical images: 775
SHA-256 matches: 775
Mismatches: 0
```

This safeguard did not alter image pixels or annotations in the canonical V3 dataset.

## 3. Model and training configuration

YOLO11n was selected as a small, mobile-conscious detection baseline. Transfer learning used the Ultralytics `yolo11n.pt` COCO-pretrained checkpoint.

| Setting | Value |
| --- | --- |
| Framework | Ultralytics 8.4.174 |
| Deep-learning runtime | PyTorch 2.14.1+cu130 |
| Model | YOLO11n detection |
| Pretrained checkpoint | `yolo11n.pt` |
| Input size | 640 x 640 |
| Maximum epochs | 75 |
| Completed epochs | 57; early stopped |
| Best epoch | 45 |
| Early-stopping patience | 12 epochs |
| Batch size | 4 |
| Optimizer | AdamW |
| Initial learning rate | 0.001 |
| Final LR fraction | 0.01 |
| Momentum | 0.937 |
| Weight decay | 0.0005 |
| Warm-up | 3 epochs |
| Seed | 42 |
| Deterministic mode | enabled |
| Workers | 2 |
| Device | NVIDIA GeForce RTX 2050, 4 GB |

The 640-pixel input was chosen as a single controlled, reasonably high-resolution baseline rather than a size sweep. Lightweight color, rotation, translation, scale, and horizontal-flip augmentation was used. Mosaic, MixUp, CutMix, copy-paste, vertical flip, shear, and perspective augmentation were disabled to avoid synthetic multi-sample compositions and unnecessary experimental expansion.

Training wall time recorded by the wrapper was 4,829.93 seconds (80 minutes 29.93 seconds); Ultralytics reported 1.295 hours for its training phase. The frozen checkpoint is `ml/grading_forecast/berry_grading/models/v3_yolo/best.pt`.

## 4. Validation and threshold decision

The documented baseline confidence threshold was 0.25. Validation-only calibration examined 0.05 through 0.90 in 0.01 increments and maximized image-level macro F1, treating rejection of a valid pepper image as an error. The predeclared tie break selected the lowest tied threshold.

Both 0.05 and the 0.25 baseline produced the same validation macro F1 (0.9562), full coverage, and zero rejections. The frozen Phase 2 threshold is therefore **0.05** under the predeclared tie rule. This low value is an experiment-specific result, not a universal scientific or deployment threshold. It also shows that this positive-only validation set provides little evidence for calibrating rejection.

### 4.1 Validation detection metrics

| Metric | Result |
| --- | ---: |
| Precision | 0.9479 |
| Recall | 0.9682 |
| mAP@0.5 | 0.9879 |
| mAP@0.5:0.95 | 0.8617 |

### 4.2 Validation image-level grade metrics

| Metric | Result |
| --- | ---: |
| Accuracy | 0.9569 |
| Balanced accuracy | 0.9632 |
| Macro F1 | 0.9562 |
| Weighted F1 | 0.9571 |
| Coverage | 1.0000 |
| Rejections | 0/116 |

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| V3 Grade 1 | 1.0000 | 0.9265 | 0.9618 | 68 |
| V3 Grade 2 | 0.9057 | 1.0000 | 0.9505 | 48 |

Validation confusion matrix, rows = true Grade 1/Grade 2 and columns = predicted Grade 1/Grade 2/REJECT:

```text
[[63, 5, 0],
 [ 0,48, 0]]
```

The checkpoint and threshold were frozen at this point. No test evidence was used to alter them.

## 5. Single sealed test evaluation

The TEST partition was evaluated once after checkpoint and threshold freezing. No retraining, new threshold, architecture change, preprocessing change, or augmentation change was made after viewing these results.

### 5.1 Primary image-level results

| Metric | Result |
| --- | ---: |
| Macro F1 | **0.9578** |
| V3 Grade 1 F1 | **0.9624** |
| V3 Grade 2 F1 | **0.9533** |
| Balanced accuracy | **0.9610** |
| Accuracy | 0.9583 (115/120) |
| Weighted F1 | 0.9584 |
| Coverage | 1.0000 |
| Rejections | 0/120 |

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| V3 Grade 1 | 0.9846 | 0.9412 | 0.9624 | 68 |
| V3 Grade 2 | 0.9273 | 0.9808 | 0.9533 | 52 |

Test confusion matrix, rows = true Grade 1/Grade 2 and columns = predicted Grade 1/Grade 2/REJECT:

```text
[[64, 4, 0],
 [ 1,51, 0]]
```

The result did not collapse on Grade 2: 51/52 Grade 2 test images were correct.

### 5.2 Test detection results

| Metric | Result |
| --- | ---: |
| Precision | 0.9402 |
| Recall | 0.9552 |
| mAP@0.5 | 0.9791 |
| mAP@0.5:0.95 | 0.8505 |
| Grade 1 mAP@0.5:0.95 | 0.8810 |
| Grade 2 mAP@0.5:0.95 | 0.8200 |

## 6. Physical-sample-level aggregation

Each of the 30 unseen test physical samples had its image predictions aggregated. Majority vote was the primary rule; a tied vote was resolved by summed detection confidence. A supplementary confidence-weighted result was also calculated.

| Result | Majority vote | Confidence weighted |
| --- | ---: | ---: |
| Accuracy | 1.0000 (30/30) | 1.0000 (30/30) |
| Macro F1 | 1.0000 | 1.0000 |
| Grade 1 samples correct | 17/17 | 17/17 |
| Grade 2 samples correct | 13/13 | 13/13 |

Twenty-six samples had unanimous image predictions. Four samples contained conflicting view predictions, but aggregation produced the correct grade for all four. This is promising evidence that multiple views can improve stability on this split; it is not proof of field robustness, and the sample-level estimate contains only 30 test groups.

## 7. Camera and resolution diagnostic

The Phase 1 shortcut risk remains **HIGH** and is not resolved by strong aggregate test metrics.

| Test subgroup | Images | Grade 1 / Grade 2 | Accuracy | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Galaxy A06 | 24 | 24 / 0 | 1.0000 | Not class-comparable; this device subgroup contains only Grade 1. |
| SM-A127F | 96 | 44 / 52 | 0.9479 | Macro F1 0.9472; all five image errors occurred here. |
| 4080x3060 | 24 | 24 / 0 | 1.0000 | Same confounded Galaxy A06 subset. |
| 4000x3000 | 96 | 44 / 52 | 0.9479 | Same mixed-class SM-A127F subset. |

The mixed-class SM-A127F/4000x3000 subgroup performed strongly, indicating the model can distinguish V3 grades within that capture condition. However, the Galaxy A06/4080x3060 condition remains perfectly correlated with Grade 1 in TEST, so its 100% accuracy cannot separate pepper appearance from camera/resolution shortcut use. No claim of camera-invariant grading is justified.

## 8. Error analysis

There were five incorrect image-level grades from four physical samples:

- two views from `grade_1/sample_072` were predicted Grade 2;
- one view from `grade_1/sample_042` was predicted Grade 2;
- one view from `grade_1/sample_039` was predicted Grade 2; and
- one view from `grade_2/sample_026` was predicted Grade 1.

All five errors were SM-A127F/4000x3000 images. Representative correct and incorrect boxes visually covered the broad pepper sample region, consistent with sample/batch detection rather than per-berry detection. Corrected box IoUs for the six representative examples ranged from approximately 0.906 to 0.987. The lowest-confidence representative prediction was correct at 0.345 and still localized the sample; it would also have been accepted by both the selected 0.05 and baseline 0.25 thresholds.

The representative contact sheet includes a hand-held sample. Its box covers the pepper in the hand rather than only the background, but the image also illustrates the documented possibility of hand/background influence. Bounding boxes are localization evidence, not causal explanations of the grade decision.

## 9. Operational results

| Property | Result |
| --- | ---: |
| Checkpoint size | 5,461,466 bytes (5.21 MiB) |
| Parameters | 2,590,230 in loaded checkpoint; 2,582,542 fused |
| Compute | approximately 6.4 GFLOPs at 640 |
| Mean reported inference | 7.12 ms/image on RTX 2050 |
| Median reported inference | 7.12 ms/image on RTX 2050 |
| End-to-end 120-image prediction pass | 44.27 seconds |
| Approximate end-to-end rate | 369 ms/image, including high-resolution decode/I/O and batching |

The checkpoint is lightweight enough to justify later ONNX/TFLite feasibility investigation, but Phase 2 did not export or benchmark either format. GPU timings do not establish smartphone latency.

The optional conventional-classifier comparison was not retrained. V2 MobileNetV2 remains the historical closed-set classifier baseline; expanding Phase 2 into another classifier experiment was not necessary to answer the primary YOLO question.

## 10. What Phase 2 demonstrates

Within this leakage-free V3 experiment, the selected YOLO11n model:

- learned the two V3 sample/batch detection classes;
- localized the annotated harvested pepper sample regions reliably;
- achieved image-level macro F1 0.9578 on unseen physical-sample groups;
- maintained strong Grade 2 performance rather than collapsing to the majority class;
- produced perfect majority-vote grades for the 30 held-out physical samples;
- exposed a deterministic no-detection/rejection state; and
- produced a small 5.21 MiB checkpoint suitable for later deployment feasibility work.

These results are substantially above a random two-class baseline and make the model promising for the defined V3 research task.

## 11. What Phase 2 does not demonstrate

This experiment does not establish:

- official SLS grade recognition;
- universal buyer/export-grade recognition;
- semantic equivalence between image grades and price-data grades;
- individual-berry detection or per-berry grading;
- non-pepper/invalid-input rejection accuracy;
- calibrated rejection under distribution shift;
- camera-independent or background-independent reasoning;
- field robustness on new capture setups;
- smartphone latency; or
- market-price correctness.

## 12. Limitations and interpretation

The test set is group-separated but small: 30 physical samples and 120 images. Multiple images within a test sample remain correlated, which is why both image- and group-level metrics are reported. All images are positive examples with one broad sample box, and the selected threshold rejected none of them. Negative and poor-quality inputs are required before rejection performance can be claimed.

The strong camera/grade imbalance remains the main validity risk. The results show that the model performs strongly within the available mixed-camera evidence, but they cannot prove it learned only pepper morphology. Label ambiguity also remains: Phase 1 found lower human agreement for Grade 2, and the V3 labels are not established as official SLS or buyer-grade definitions.

## 13. Phase 2 conclusion and gate

```text
PHASE 2 STATUS: COMPLETE
MODEL: Ultralytics YOLO11n, best epoch 45
IMAGE-LEVEL TEST MACRO F1: 0.9578
SAMPLE-LEVEL TEST MACRO F1: 1.0000
SHORTCUT RISK: HIGH / UNRESOLVED
NON-PEPPER REJECTION: NOT YET EVALUATED
```

**Phase 3 readiness: YES, with constraints.** The frozen Phase 2 model is ready for a separately authorized Phase 3 focused on genuine non-pepper/invalid-input rejection and confidence calibration. Phase 3 must preserve test discipline, explicitly address the camera shortcut risk, and must not interpret this positive-only result as rejection validation.

Phase 2 stops here. No ONNX/TFLite conversion, mobile/backend integration, negative-data addition, price-forecasting work, or post-test retraining was performed.

## 14. Reproducibility artifacts

- Dataset definition: `data/processed/grading_forecast/berry_v3/yolo_phase2/`
- Training configuration/script: `ml/grading_forecast/berry_grading/training/v3_yolo/`
- Frozen checkpoint and training record: `ml/grading_forecast/berry_grading/models/v3_yolo/`
- Validation/test metrics and predictions: `ml/grading_forecast/berry_grading/evaluation/v3_yolo/`
- Machine-readable test metrics: `ml/grading_forecast/berry_grading/evaluation/v3_yolo/test/metrics.json`
- Sample aggregation: `ml/grading_forecast/berry_grading/evaluation/v3_yolo/test/sample_level_metrics.json`
- Camera diagnostic: `ml/grading_forecast/berry_grading/evaluation/v3_yolo/test/camera_resolution_diagnostic.json`
- Error-analysis contact sheet: `ml/grading_forecast/berry_grading/evaluation/v3_yolo/test/representative_error_analysis.png`
