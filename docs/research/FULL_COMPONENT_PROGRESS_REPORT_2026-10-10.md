# Full Component Progress Report: Berry Grading and Export Price Forecasting

**Project:** Multimodal Pepper AI Decision Support System  
**Individual component:** Berry Grading and Export Price Forecasting (IT22079268)  
**Report date:** 2026-10-10  
**Current branch / audited commit:** `integration` / `4f904690c1a9049cbc0505a4ef380aaab6cb34fd`  
**Evidence basis:** Git history, current source, versioned datasets/manifests, saved model artifacts, machine-readable metrics, experiment reports, and the fresh checks recorded in Section 14  
**Scope boundary:** This report covers only the berry-grading, export-price-forecasting, grade-price decision-support, and their backend/mobile integration work. Pest detection, leaf disease, and berry disease are excluded except where shared mobile integration affected this component.

## 1. Executive summary

This component has progressed through three research generations and a deployment/integration phase:

1. A May 2026 proof of concept established a three-grade MobileNetV2 classifier, a Random Forest price model, FastAPI services, Flutter screens, recommendations, and optional Firebase storage.
2. An August 2026 PP2 recovery cycle rebuilt the datasets and evaluation discipline. A leakage-safe V2 MobileNetV2 achieved 80.73% accuracy and 0.8068 macro F1. Naive Persistence decisively beat the V2 Random Forest on the same 36 chronological price-test dates and became the honest runtime baseline.
3. An October 2026 research cycle redefined the visual task as two-class harvested-sample detection/grading, rebuilt a group-aware 775-image split, trained YOLO11n, added non-pepper/quality/uncertainty handling, and then performed controlled hard-negative fine-tuning. The original YOLO model achieved 0.9578 image-level macro F1 on the sealed 120-image positive test and 1.000 sample-level macro F1 over 30 physical samples. The follow-up model retained 0.9583 positive-test accuracy, improved macro F1 to 0.9643, and rejected 49/49 new unseen negative images, subject to important dataset/domain limitations.
4. The price research was rebuilt from dated Sri Lankan Department of Export Agriculture EAC pages. The canonical dataset covers 2016-10-04 to 2026-09-29 with 493 Grade 1 and 358 Grade 2 national-average observations. A validation-selected, separate-grade Ridge model predicts next-observation log returns from completed-return lags and observation gap. On the 147-row final test it achieved return MAE 0.01820, return RMSE 0.02985, direction accuracy 52.38%, price MAE 34.00 LKR/kg, and price RMSE 54.73 LKR/kg. It beat persistence on both final-test MAE and RMSE, but was slightly worse on the ten-observation newest-period external check. The correct research conclusion is therefore **ready with limitations**, not production-ready forecasting.
5. A deterministic Phase 6 engine joins accepted V3 grades to the exact matching Grade 1 or Grade 2 price evidence, blocks rejected/uncertain inputs, preserves an explanation trace, and passed all 28 scenario expectations plus 15 unit tests in the saved experiment.
6. Phase 7 exported the hard-negative YOLO model to a deterministic fixed-shape ONNX model, verified five-case numerical/decision equivalence, integrated it into FastAPI and Flutter, hardened upload/runtime validation, and passed the corrected five-case Android-emulator flow. The active mobile path uses backend ONNX Runtime and frozen approved Phase 5 forecast records. It does **not** claim live price forecasting or V3 on-device TFLite.
7. English, Sinhala, and Tamil presentation and a farmer-oriented UI were added without changing the frozen ML or decision contracts. Saved evidence records clean Flutter analysis and 75/75 tests before the final home-screen-only commit. Manual device UI/linguistic acceptance remains incomplete.

### Current overall status

| Area | Current status | Evidence-based interpretation |
|---|---|---|
| V1/V2 three-grade classifier | Complete, historical baseline | Reproducible evidence; no longer the authoritative Phase 7 grader |
| V3 two-grade YOLO grading | Complete with limitations | Strong internal group-separated test results; shortcut/domain risks remain |
| Non-pepper/quality rejection | Improved, limited | Controlled hard-negative result passed; not field/open-set proof |
| Price data reconstruction | Complete | Provenance-rich canonical Grade 1/2 EAC dataset exists |
| Price movement research | Complete with limitations | Ridge selected; advantage over persistence is mixed outside final test |
| Grade-price decision engine | Complete with limitations | Deterministic, traceable, tested; not an economic-benefit model |
| Backend/mobile integration | Complete with limitations | Controlled backend and emulator paths passed; runtime uses frozen forecast records |
| Field/domain validation | Not executed | Protocol/templates exist, but no prospective field evidence exists |
| Production readiness | Not demonstrated | Authentication, broad security, live forecasting, calibration, field and user studies remain |

## 2. Research problem, contribution, and boundaries

The component addresses a chained decision-support problem:

1. determine whether a submitted image is usable and contains a harvested pepper sample;
2. assign the project-specific visual grade when evidence is sufficient;
3. route only that accepted grade to the corresponding Grade 1 or Grade 2 market series;
4. present a clearly qualified market outlook; and
5. withhold market output when the image is rejected, the grade is uncertain, the views conflict, or price evidence is unavailable.

The component is a research decision-support system. It is not an official SLS/export certification system, a laboratory test, a buyer quotation, an autonomous trading system, or proof of increased farmer income. Image models cannot measure moisture, piperine, volatile oil, fibre, ash, bulk density, adulteration, hygiene, or other laboratory/export criteria.

The repository uses two different phase-numbering eras. The August PP2 workflow called its steps Phase 0 through Phase 13. The October V3 research program restarted at V3 Phase 0 and continued through Phase 7. This report names the generation explicitly to prevent the two numbering schemes from being confused.

## 3. Git-derived development timeline

### 3.1 Foundation and proof of concept — 7 April to 13 May 2026

| Commit(s) | Work completed |
|---|---|
| `31f387f`, `8071258` | Created the project structure and documented the multimodal mobile/FastAPI/ML workflow. |
| `0b6592d` to `51dc57f` | Built the initial FastAPI grading/forecast API, preprocessing, feature extraction, recommendation logic, tests, and Firebase configuration path. |
| `3609cfd`, `a675651` | Added Flutter berry grading, price forecast, and recommendation screens/services. |
| `e28e617` to `524b4c1` | Added label generation, image/price preprocessing, training, evaluation, inference, and export scripts. |
| `39dc308` to `4f5278a` | Added V1 model metadata, ONNX export, forecast/berry metrics, runtime preprocessing corrections, and final V1 evaluation evidence. |
| `6b84efd` | Updated the project overview with this component’s responsibilities. |

### 3.2 PP2 dataset/model recovery and honest baselines — 26 to 31 August 2026

| Commit(s) | Work completed |
|---|---|
| `addb6a1`, `1191ccd`, `9db62a7` | Built the V2 price preparation path, PP2 plan/log/results documents, dry-run controls, and readiness checks. |
| `2bf0e6e`, `745c262`, `3d623a8` | Trained/evaluated V2 MobileNetV2, saved metrics and metadata, and exported ONNX. |
| `e794ac6`, `a938e44` | Trained/evaluated V2 Random Forest and Naive Persistence on aligned chronological timestamps. |
| `94feb16`, `ed8c240` | Ran the bounded improvement experiments: higher berry dropout and extended price lags. |
| `70c0a59` to `36b9a3a` | Validated API integration, aligned runtime to selected artifacts, validated recommendation rules, and hardened upload/error behavior. |
| `8d6ee0c`, `dd121a0` | Added explicit missing/corrupt/unsupported/oversized image handling and safe service failures. |
| `881a857`, `8e9a9df` | Added optional fail-safe Firestore history persistence without saving image bytes. |
| `26d9885`, `1967293` | Recorded ONNX/backend diagnostic agreement, preprocessing risk, and cleaned stale split files. |
| `943459c` to `73302fd` | Added artifact download/readiness handling and bundled fallback support. |
| `e8142f4`, `4b35a37`, `c1dd6cd` | Added historical V2 TFLite offline mode and grade-aware price presentation. |
| `bb40c92` | Consolidated the V1/V2 model documentation. |

### 3.3 V3 research, price reconstruction, decision support, and deployment — 6 to 9 October 2026

| Commit | Research/deployment milestone |
|---|---|
| `14a39c9` | V3 Phase 0 research decision record. |
| `6b03e16` | V3 Phase 1 audit, group manifests, blind-review evidence, background contact sheet, and V2 saliency diagnostic. |
| `3651c83` | V3 Phase 2 group-aware YOLO preparation, training, sealed evaluation, model and metrics. |
| `8301141` | V3 Phase 3 external-negative, image-quality, and uncertainty decision pipeline. |
| `831cb1a` | Price Phase 4 EAC source reconstruction, canonical datasets, walk-forward foundation, and integrity evidence. |
| `614296e` | Price Phase 5 candidate experiments, validation-only selection, final test, external check, plots, and 19-check integrity report. |
| `39592c6` | Controlled hard-negative dataset, training, evaluation, adapted model, and follow-up report. |
| `b6f19d5`, `c10deb5` | Consolidated progress report and froze prospective field/domain-validation protocol; no field study was executed. |
| `564ee15` | Phase 6 deterministic grade-price decision engine, scenarios, metrics, trace, unit tests, and integrity validation. |
| `1388632` | Phase 7 ONNX export/equivalence, backend integration, Flutter contract, and controlled verification. |
| `700f19a`, `33cd42c` | Removed client resizing/recompression and documented corrected 5/5 emulator acceptance. |
| `40c9a36` | Fixed CRLF/LF frozen-text integrity and strengthened startup/readiness checks. |
| `e443cc2` | Hardened upload, schema, runtime, privacy/logging, and client failure handling. |
| `36e224f`, `17aea54` | Integrated the wider mobile shell and added English/Sinhala/Tamil localization while preserving the grading contract. |
| `8dd8a4c` | Farmer-oriented UI/UX refinement; saved evidence records clean analysis and 75/75 Flutter tests. |
| `374d98b`, `4f90469` | Final presentation/home navigation refinements. These commits did not alter backend, ML, datasets, model artifacts, or price evidence. |

## 4. Detailed work completed, step by step

### Step 1 — Initial backend, mobile workflow, and service decomposition

The first implementation established the full application skeleton:

- FastAPI routes for image grading, price forecasting, combined analysis, and recommendations;
- image decoding/resizing and OpenCV-derived quality features;
- a grading service and model-loading path;
- a forecasting service and artifact-loading path;
- deterministic recommendation rules;
- optional Firebase/Firestore storage;
- Flutter capture, processing, grading result, price result, and API-client code;
- backend tests and a Postman collection.

This was important engineering proof, but the earliest fallbacks and model paths were not yet a defensible research pipeline. Later phases explicitly replaced demo/stale runtime behavior and tightened evidence boundaries.

### Step 2 — V1 berry dataset and MobileNetV2 classifier

The first berry dataset contained 360 images, balanced at 120 images each for Grade 1, Grade 2, and Grade 3. A MobileNetV2 transfer-learning classifier was trained at 224 × 224 RGB and exported for runtime inference.

Saved V1 test results on 72 images:

| Metric | Result |
|---|---:|
| Accuracy | 77.78% |
| Macro F1 | 0.7447 |
| Weighted F1 | 0.7447 |
| Grade 1 F1 | 0.9600 |
| Grade 2 F1 | 0.5000 |
| Grade 3 F1 | 0.7742 |
| Average single-image inference | 80.97 ms in the recorded environment |
| Model size | 18.439 MB |

The confusion matrix showed the main weakness: 14 of 24 Grade 2 images were predicted as Grade 3. The legacy split also lacked the later physical-sample grouping discipline, so V1 remains historical proof of concept rather than the selected scientific result.

### Step 3 — V1 price Random Forest

The initial price formulation predicted the next absolute price using lag and rolling features. The V1 Random Forest used lag 1–3, rolling means/standard deviations, price change, percentage change, month, and week-of-year features.

| V1 Random Forest test metric | Result |
|---|---:|
| MAE | 45.83 LKR/kg |
| RMSE | 47.76 LKR/kg |
| MAPE | 2.29% |
| R² | -6.1315 |

The negative R² showed poor generalization. This motivated the later chronological rebuild and mandatory comparison with persistence.

### Step 4 — PP2 evidence plan and V2 dataset reconstruction

The August audit identified leakage, target-definition, stale-artifact, silent-fallback, and documentation risks. V1 artifacts were preserved while V2-specific data, scripts, and output paths were created.

#### Berry V2 dataset

- 671 readable images from 168 physical samples;
- Grade 1: 224 images; Grade 2: 224; Grade 3: 223;
- deterministic seed 42;
- split key: `grade + sample_id`, so alternate views of one physical sample never crossed partitions;
- no unreadable images, missing paths, duplicate paths, or duplicate-content groups in the saved audit.

| Split | Physical samples | Images |
|---|---:|---:|
| Train | 117 | 467 |
| Validation | 24 | 95 |
| Test | 27 | 109 |
| Total | 168 | 671 |

#### Price V2 dataset

- cleaned 7,742 source rows;
- selected National Grade 1 average weekly farm-gate price as the target;
- retained 232 observed target rows from 2021-02-22 to 2026-08-18;
- preserved missing intervals instead of filling them as zero;
- documented 12 gaps longer than eight days, including a 316-day maximum gap;
- chronological 70/15/15 observed-row split with no shuffle.

| Split | Rows | Coverage |
|---|---:|---|
| Train | 162 | 2021-02-22 to 2025-03-18 |
| Validation | 34 | 2025-03-25 to 2025-11-25 |
| Test | 36 | 2025-12-02 to 2026-08-18 |

### Step 5 — V2 MobileNetV2 training and controlled improvement

The selected V2 model used:

- MobileNetV2 initialized with ImageNet weights;
- 224 × 224 RGB input;
- global average pooling, dropout 0.25, and three-class softmax;
- horizontal flip, small rotation, zoom, and brightness augmentation;
- sparse categorical cross-entropy and Adam;
- batch size 16 and seed 42;
- frozen-backbone stage: up to 15 epochs, learning rate 0.001, patience 3; 14 completed;
- limited fine-tuning: up to 5 epochs, learning rate 0.00001, patience 2; all 5 completed.

The best checkpoint came from fine-tuning epoch 5 with validation loss 0.52487 and validation accuracy 0.74737. It was evaluated once on the untouched 109-image test set.

| V2 test metric | Result |
|---|---:|
| Accuracy | 80.73% |
| Macro precision | 0.8122 |
| Macro recall | 0.8078 |
| Macro F1 | 0.8068 |
| Weighted F1 | 0.8076 |
| Grade 1 F1 | 0.8286 |
| Grade 2 F1 | 0.8312 |
| Grade 3 F1 | 0.7606 |

A single controlled change increased dropout to 0.35. It produced the same headline test metrics and did not replace the baseline. The selected V2 model was exported to ONNX and later to TFLite without retraining.

### Step 6 — V2 Random Forest, persistence baseline, and limited improvement

The V2 Random Forest used 400 trees, seed 42, chronological evaluation, and only past-derived features: lags 1–3; rolling mean/std windows 3 and 5; calendar features; price change; and percentage change.

| Model on the same 36 test dates | MAE | RMSE | MAPE | R² |
|---|---:|---:|---:|---:|
| Random Forest V2 | 82.42 | 88.45 | 4.17% | -0.4736 |
| Random Forest with lags 4/8/12 | 78.16 | 84.86 | 3.95% | -0.3566 |
| Naive Persistence | **16.41** | **22.52** | **0.85%** | **0.9045** |

The extended-lag experiment improved the learned model but remained far worse than persistence. The evidence-based decision was to deploy persistence for the legacy V2 runtime rather than claim that the more complex model was superior.

### Step 7 — V2 runtime alignment, reliability, storage, and offline fallback

The integration phases then:

- replaced the legacy/root berry model with the selected V2 ONNX artifact;
- replaced demo forecast behavior with the selected persistence method;
- validated the grade/trend recommendation table;
- returned explicit `forecast_unavailable` instead of invented prices;
- validated image bytes instead of trusting client MIME alone;
- added missing, empty, corrupt, unsupported, and over-10-MB upload failures;
- stored structured results in Firestore when configured, but never raw image bytes;
- kept inference available when Firestore was unavailable;
- added artifact download/readiness and bundled fallbacks;
- exported V2 to TFLite for historical offline mobile use;
- added grade-aware display, with an explicitly estimated Grade 2 discount and no Grade 3 price claim.

A nine-image diagnostic showed exact agreement between direct ONNX and backend predictions, but only 6/9 were correct: Grade 1 3/3, Grade 2 0/3, Grade 3 3/3. This was a small diagnostic, not a replacement for the official 109-image test. It also exposed inconsistent training/runtime spatial preprocessing. These findings helped motivate the V3 redesign.

### Step 8 — V3 Phase 0: task redefinition

V3 reframed the task from three-class whole-image classification to two project-specific harvested-sample detection/grading classes:

```text
0 = V3 Grade 1
1 = V3 Grade 2
```

The unit of prediction is the broad harvested pepper sample/batch visible in a smartphone image, not individual berries. V3 Grade 1 combines the old raw Grade 1 and Grade 2 groups; V3 Grade 2 corresponds to the old Grade 3 group. These project labels are not proven equivalent to SLS, buyer, or export grades.

### Step 9 — V3 Phase 1: audit, relabeling analysis, split repair, and shortcut diagnosis

The Roboflow YOLOv8 export contained 775 readable JPEG images and 775 valid one-box annotations, but its image-level split leaked physical samples: 146 of 194 physical groups crossed partitions, involving 584 images. The visible taxonomy also differed from V2.

Phase 1 therefore:

- matched all images back to the physical-sample hierarchy by hash;
- created image/sample and group-split manifests;
- reconstructed a group-aware split;
- produced background/contact-sheet and saliency diagnostics;
- recorded a high shortcut risk because camera/resolution were confounded with class;
- preserved the canonical images and annotations.

### Step 10 — V3 Phase 2: YOLO11n training and sealed positive evaluation

#### Dataset and split

| Partition | Physical samples | Images | V3 Grade 1 | V3 Grade 2 |
|---|---:|---:|---:|---:|
| Train | 135 | 539 | 312 | 227 |
| Validation | 29 | 116 | 68 | 48 |
| Test | 30 | 120 | 68 | 52 |
| Total | 194 | 775 | 448 | 327 |

All 775 canonical hashes matched, each image had one annotation, the group intersections were empty, and every image occurred in exactly one partition. Materialized working copies prevented Ultralytics JPEG repair from changing canonical inputs.

#### Training environment/configuration

| Setting | Value |
|---|---|
| Model | Ultralytics YOLO11n detection, COCO-pretrained |
| Framework | Ultralytics 8.4.174 |
| Runtime | PyTorch 2.14.1+cu130 |
| Hardware | NVIDIA GeForce RTX 2050, 4 GB |
| Input | 640 × 640 |
| Optimizer | AdamW |
| Batch / seed | 4 / 42 |
| Learning rate / weight decay | 0.001 / 0.0005 |
| Max epochs / patience | 75 / 12 |
| Completed / best epoch | 57 / 45 |
| Training wrapper time | 4,829.93 s (80 min 29.93 s) |

Light color/geometric augmentation was retained; mosaic, MixUp, CutMix, copy-paste, vertical flip, shear, and perspective were disabled. Validation-only threshold scanning selected 0.05 under the predeclared lowest-tied-threshold rule.

#### Sealed-test results

| Metric | Result |
|---|---:|
| Image accuracy | 0.9583 (115/120) |
| Image macro F1 | 0.9578 |
| Grade 1 F1 | 0.9624 |
| Grade 2 F1 | 0.9533 |
| Balanced accuracy | 0.9610 |
| Coverage | 1.0000 |
| Detection mAP@0.5 | 0.9791 |
| Detection mAP@0.5:0.95 | 0.8505 |
| Sample-level majority-vote accuracy/macro F1 | 1.0000 / 1.0000 over 30 samples |

The model made five image-level mistakes across four physical samples. All occurred under the SM-A127F/4000×3000 condition. The Galaxy A06/4080×3060 subgroup contained only Grade 1, so its perfect score cannot separate morphology from a device shortcut. The positive-only test also could not establish non-pepper rejection.

### Step 11 — V3 Phase 3: rejection, image-quality, and uncertainty calibration

An 80-image external non-pepper set was collected from Wikimedia Commons across ten retrieval strata, with source/license metadata and no hash overlap with V3. Forty images were used for calibration and 40 remained held out.

The frozen Phase 2 model at confidence 0.25 rejected 65/80 (81.25%) negatives. Validation-only calibration selected:

- detection confidence at least 0.55;
- Laplacian blur variance at least 10;
- mean brightness at least 50/255;
- minimum dimension at least 320 pixels;
- detected-box area at least 0.20 of the image;
- grade confidence at least 0.05;
- class margin at least 0.30.

The five-state output became `GRADE_1`, `GRADE_2`, `POOR_IMAGE`, `NO_PEPPER`, or `UNCERTAIN_GRADE`.

| Phase 3 result | Value |
|---|---:|
| Validation pepper coverage | 111/116 = 95.69% |
| Accepted validation accuracy | 108/111 = 97.30% |
| Accepted validation macro F1 | 0.9725 |
| Held-out negative rejection | 35/40 = 87.5% |
| Held-out negative false acceptance | 5/40 = 12.5% |

All five false accepts were vegetation/crop images, including one 0.943-confidence aerial-crop false positive. Thresholds alone could not eliminate these errors without violating the predeclared pepper-retention rule, so the operational rejection gate did not pass and a separate hard-negative experiment was justified.

### Step 12 — V3 Phase 3 follow-up: controlled hard-negative adaptation

The follow-up collected 250 source-controlled negatives and split them by creator/source group:

- 152 negative training images;
- 49 validation negatives;
- 49 sealed final negative holdout images.

There was no exact-hash overlap with the 775 V3 images or the original 80 Phase 3 negatives. Hard negatives were empty-label YOLO images, not new pepper classes.

Training initialized from the frozen Phase 2 checkpoint and used only 539 Phase 1 train positives plus 152 negative-train images. Configuration: YOLO11n, 640 px, batch 4, seed 42, AdamW, LR 0.0001, weight decay 0.0005, maximum 30 epochs, patience 8. Training stopped after epoch 27 and selected epoch 19. Cumulative interrupted/resumed training time was 2,620.8 seconds.

Validation-only threshold selection chose 0.05 while retaining the existing quality and 0.30 class-margin rules.

| Metric | Frozen control | Adapted model | Interpretation |
|---|---:|---:|---|
| Validation pepper coverage | 95.69% | 98.28% | Improved |
| Validation accepted macro F1 | 0.9725 | 0.9539 | Small decrease |
| New 49-image negative rejection | 71.43% | 100.00% | +28.57 pp |
| Vegetation/crop/aerial rejection | 60.00% | 100.00% | +40.00 pp |
| Original Phase 3 negative rejection | 87.50% | 100.00% | Retrospective, not independent |
| Positive sealed-test coverage | — | 98.33% | 2 rejections |
| Positive sealed-test accuracy | 0.9583 | 0.9583 | Preserved |
| Positive sealed-test macro F1 | 0.9578 | 0.9643 | Slightly higher |

The predeclared hypothesis was supported. However, the new negative holdout is small and internet-derived, semantic-near-duplicate freedom was not proven, and field/device/open-set robustness remains unknown.

### Step 13 — Price Phase 4: authoritative EAC reconstruction

The historical V2 source was incomplete and its row-level provenance pointed to an index rather than each dated page. Phase 4 reconstructed the series from the Sri Lankan Department of Export Agriculture Economic Research Unit’s dated Producers’ Prices (Farm Gate) of EAC pages.

Key reconstruction evidence:

- index snapshot and exact dated page URLs/hashes retained;
- 495 indexed dated links, 493 successfully parsed pepper pages;
- two broken links retained explicitly: 2023-04-25 and 2026-06-23;
- 16,903 pepper observations from 2016-10-04 through 2026-09-29;
- 493 National Grade 1 average observations;
- 358 National Grade 2 average observations;
- missing Grade 2 remained missing;
- canonical dataset SHA-256 recorded as `ea800ea576817f07ad54d50317dbd68254fc5dc824447380e58688b6b711c0f6`.

The target changed from next absolute price to next-observation return, with future price derived from the dated reference price. Phase 4 evaluated simple baselines and lightweight models with expanding windows. It established the data foundation but did not prove a consistently superior forecast.

### Step 14 — Price Phase 5: controlled forecasting experiment

Phase 5 used chronological expanding-window/walk-forward evaluation and kept the newest five observations per grade outside model selection and final testing as an external reality check.

Candidate families included:

- persistence/zero return;
- last-observed return;
- expanding mean return;
- historical price drift;
- simple exponential smoothing at multiple alphas;
- conditional ARIMA(1,0,0) and ARIMA(2,0,0);
- Ridge;
- Random Forest;
- Gradient Boosting;
- separate-grade and relationship-aware formulations;
- simple-return and log-return targets;
- return-lag, technical, and calendar feature groups.

Selection used validation only. The chosen candidate was separate Grade 1/Grade 2 Ridge regression predicting next-observation log return from four completed-return lags plus observation gap (`model_bakeoff|ridge|log_return|A_return_lags|separate`). Test and external partitions were not used for selection.

#### Final temporal test — 147 predictions

| Metric | Selected Ridge | Persistence |
|---|---:|---:|
| Return MAE | **0.01820** | 0.01858 |
| Return RMSE | **0.02985** | 0.03187 |
| Price MAE | **33.996 LKR/kg** | 34.622 LKR/kg |
| Price RMSE | **54.728 LKR/kg** | 58.119 LKR/kg |
| Directional accuracy | **52.38%** | 10.20% |

By grade, Ridge price MAE/RMSE was 15.19/20.84 LKR/kg for Grade 1 and 53.06/74.77 LKR/kg for Grade 2. Grade 2 therefore remains markedly weaker.

#### External newest-period check — 10 predictions

| Metric | Selected Ridge | Persistence |
|---|---:|---:|
| Return MAE | 0.02330 | **0.02305** |
| Return RMSE | 0.03259 | **0.03259** (slightly lower) |
| Price MAE | 42.830 | **42.329** |
| Price RMSE | 58.536 | **58.218** |
| Directional accuracy | **70%** | 10% |

Ridge captured direction better but did not beat persistence on external error magnitude. The experiment’s comparison verdict is `MIXED`.

The validation-residual 90% intervals covered 96.60% of final-test observations, but their mean width was 275.18 LKR/kg. Grade 2 intervals averaged 456.56 LKR/kg versus 96.26 for Grade 1. These are empirical uncertainty diagnostics, not guaranteed probability intervals.

All 19 saved integrity checks passed, covering frozen-input hashes, unchanged V3 artifacts, temporal causality, validation-only selection, mandatory persistence, and external-holdout exclusion. Current conclusion: **READY WITH LIMITATIONS for decision-support research; not reliable live/production forecasting.**

### Step 15 — Prospective field protocol and freeze

The repository contains a field/domain-shift protocol, manifest template, metrics schema, and integrity checks. This is preparation only. No prospective field images, independent labels, new-camera results, domain-shift metrics, or field-user outcomes have been collected. Protocol readiness must not be described as completed field validation.

### Step 16 — Phase 6 grade-price decision engine

The engine did not retrain grading or forecasting. It froze hashes for the selected/adapted grading artifacts, price dataset, selected model specification, predictions, thresholds, and decision configuration.

Decision sequence:

1. run grading/quality/rejection first;
2. stop `NO_PEPPER` and `POOR_IMAGE` as `REJECT`;
3. stop `UNCERTAIN_GRADE` and conflicting sample views without price output;
4. route accepted V3 Grade 1 only to the Grade 1 series and V3 Grade 2 only to Grade 2;
5. fail closed on route mismatch or missing evidence;
6. classify price direction only after rounding prices to LKR 0.01;
7. label an interval crossing the reference price as `HIGH_UNCERTAINTY`;
8. preserve grading evidence, price evidence, rationale, and provenance in a trace.

Evidence:

- 13 empirical compositional scenarios plus 15 explicitly synthetic logic-only scenarios;
- 28/28 expectations passed;
- Grade 1 routing 12/12, Grade 2 routing 7/7, and rejection/uncertainty blocking 7/7;
- deliberate wrong-series route failed closed;
- 28/28 outputs contained complete explainability traces;
- deterministic repeated evaluation matched;
- 15/15 saved unit tests passed.

All ten accepted empirical compositions became `HIGH_UNCERTAINTY_OUTLOOK` because their intervals crossed the reference price. This conservatism reflects weak price certainty rather than an engine defect. The scenarios are compositional, not contemporaneous field grade-plus-sale outcomes, so they do not prove farmer utility or economic benefit.

### Step 17 — Phase 7 ONNX, backend, and Flutter integration

The adapted V3 checkpoint was exported without overwriting the `.pt` model:

- fixed input `[1,3,640,640]`;
- output `[1,300,6]` with embedded NMS;
- ONNX opset 20;
- size 10,636,719 bytes;
- normalized repeat export was byte-identical;
- ONNX SHA-256 `f8bb36b3ce9c354fd0707f555dbff88bc4f24606b4b93be99a74b03e6db54d38`.

Five fixed Grade 1, Grade 2, non-pepper, poor-image, and uncertain cases passed ONNX/PyTorch equivalence. Maximum confidence difference was `1.78813934326172e-07`; maximum original-image box difference was `0.000823974609375` pixels. An initial EXIF decoder mismatch was corrected by preserving the frozen OpenCV path rather than loosening tolerances.

The selected runtime is backend ONNX Runtime. V3 TFLite was not produced. The old MobileNet TFLite asset is not presented as the V3 model, and the legacy offline path fails explicitly for Phase 7.

The FastAPI analyze path now:

- bounds multipart reads at 10 MB;
- verifies one-frame JPEG/PNG/WEBP bytes;
- limits decoded size to 50 million pixels and 12,000 pixels per axis;
- initializes and checks both ONNX and frozen price evidence;
- returns explicit 400/413/415/503 classes and sanitized unexpected failures;
- validates response enums, numeric finiteness, intervals, routing, and rejection-first invariants;
- logs only an analysis UUID, processing stage/error type, and final category—not bytes or filenames;
- processes images in memory;
- retires bypassing legacy endpoints with HTTP 410.

The price runtime deliberately selects the latest approved frozen Phase 5 record for the exact grade. It does not refit Ridge and is not live forecasting. A cross-platform CRLF/LF canonical text hash fixed Railway/Linux verification without accepting changed forecast content.

Controlled backend output passed Grade 1, Grade 2, non-pepper, poor-image, and uncertain cases and was deterministic. The first emulator pass achieved only 3/5 because Flutter resized/recompressed selected files. Removing application-requested resize/quality conversion preserved the frozen pixels; the corrected emulator rerun passed 5/5:

| Controlled role | Corrected result | Market behavior |
|---|---|---|
| Grade 1 | `GRADE_1`, score 0.9238 | Grade 1 evidence only |
| Grade 2 | `GRADE_2`, score 0.9046 | Grade 2 evidence only |
| Non-pepper | `NO_PEPPER` | No market output |
| Poor image | `POOR_IMAGE`, blur gate failed | No market output |
| Uncertain | `UNCERTAIN_GRADE`, margin gate failed | No market output |

The saved Phase 7 integrity result passed 22/22 checks. Hosted accepted-grade verification was documented as pending immediately after the CRLF/LF correction; the broader Phase 7 report later records researcher-operated emulator, physical-device, and hosted-backend smoke checks, but no independently instrumented field/device study.

### Step 18 — Localization and farmer-facing UI

English, Sinhala, and Tamil presentation was added after strict API parsing. Internal categories, grade routes, thresholds, price evidence, and scientific trace values remain unchanged. The UI:

- presents the farmer-readable grade first;
- keeps rejection and uncertainty fail-closed;
- emphasizes the frozen forecast price while retaining plain uncertainty wording;
- removes fabricated farm status/mock recent results and redundant capture navigation;
- keeps detailed trace/model evidence out of the normal farmer view while preserving it in the API;
- adds practical guide and history-empty-state screens;
- retains explicit research limitations rather than trading instructions.

Saved evidence for the farmer UI change records `flutter analyze` with no issues and 75/75 Flutter tests. The later October 9 commits changed presentation/home navigation and did not change the backend, ML, models, or data. A new debug APK and post-change physical-device UI acceptance were not evidenced.

## 5. Current models and algorithms

| Generation | Model/method | Role | Current standing |
|---|---|---|---|
| Berry V1 | MobileNetV2, 3-class softmax | Early whole-image grading | Historical baseline |
| Berry V2 | MobileNetV2 transfer learning, 3 classes | Leakage-safer PP2 classifier; ONNX/TFLite historical runtime | Selected V2 evidence; superseded by V3 in Phase 7 |
| Berry V3 Phase 2 | YOLO11n, 2 sample-level detection classes | Positive pepper localization/grading | Strong sealed positive-test baseline |
| Berry V3 adapted | YOLO11n hard-negative fine-tune | Current grading/rejection checkpoint | Authoritative Phase 7 model, with field limitations |
| Price V1/V2 | Random Forest regressors | Absolute next-price prediction | Rejected against persistence |
| Legacy runtime | Naive Persistence | Honest V2 runtime baseline | Historical runtime method |
| Price Phase 4/5 | Expanding-window Ridge on next log return | Current research forecast specification | Selected with mixed external evidence |
| Phase 6 | Deterministic rule engine | Grade gate, exact price routing, uncertainty category, trace | Authoritative fusion logic |
| Phase 7 runtime | ONNX Runtime + frozen Phase 5 records | Deployable controlled research path | Current application path; not live refitting |

## 6. Datasets and changes

| Dataset/version | Size and task | Important change/control |
|---|---|---|
| Berry V1 | 360 images; 3-class classification | Balanced proof-of-concept; weaker split discipline |
| Berry V2 | 671 images, 168 physical samples; 3-class classification | Group-aware split, deterministic audit, untouched 109-image test |
| Raw/V3 corpus | 775 images, 194 physical samples | Same underlying images reorganized into 2 project-specific classes |
| Roboflow V3 export | 775 images and one YOLO box/image | Structurally valid but original image-level splits leaked groups |
| V3 group-aware split | 539/116/120 images | Zero physical-group overlap; canonical hashes protected |
| Phase 3 negatives | 80 images | 40 calibration + 40 held-out; source/license manifest |
| Hard-negative follow-up | 250 images | 152 train + 49 validation + 49 sealed final holdout; source-group split |
| Price V2 | 232 Grade 1 target observations | Chronological observed-row split; gaps preserved |
| EAC reconstructed V1 | 16,903 raw pepper observations; 493 G1 and 358 G2 national averages | Dated-page provenance, missing G2 preserved, 2016-10-04 to 2026-09-29 |
| Phase 5 model data | G1/G2 return rows with external newest holdout | Past-only features; validation-only selection; final/external isolation |

No dataset should be described as official export-grade ground truth. V3 class merging/relabeling is project-specific, and negative internet images are not representative field misuse samples.

## 7. Technology stack and environments

### Machine learning and data

- Python 3.13;
- TensorFlow 2.21.0 for historical V2 MobileNet training;
- tf2onnx 1.17.0 for historical export support;
- PyTorch 2.14.1+cu130 and Ultralytics 8.4.174 for V3;
- ONNX/ONNX Runtime for Phase 7 backend inference;
- OpenCV, Pillow, NumPy, pandas, scikit-learn, Matplotlib, PyYAML, joblib, and psutil;
- CUDA 13.0 on NVIDIA GeForce RTX 2050 4 GB for V3 training;
- separate `.venv-yolo` environment and repository-local `YOLO_CONFIG_DIR=.ultralytics` to avoid the inaccessible user roaming settings directory.

The recorded Phase 5 environment was Python 3.13.14, pandas 3.0.1, NumPy 2.4.3, scikit-learn 1.8.0, PyYAML 6.0.3, and Windows 11.

### Backend and storage

- FastAPI, Uvicorn, Pydantic v2, multipart upload handling;
- ONNX Runtime CPU for the deployed grading path;
- optional Firebase Admin/Firestore history storage;
- environment-driven artifact/runtime configuration;
- health and strict readiness endpoints.

### Mobile

- Flutter/Dart (`sdk: ^3.11.0`);
- HTTP multipart API client and image picker;
- generated Flutter localization for English, Sinhala, and Tamil;
- `shared_preferences` for locale persistence;
- historical `tflite_flutter` dependency for other/legacy local models, but no V3 TFLite claim;
- Android emulator/device testing and Railway-hosted backend smoke work.

## 8. Current application architecture

```text
Flutter capture/selection
        |
        | original selected bytes (no requested resize/recompression)
        v
FastAPI POST /api/v1/grading-forecast/analyze
        |
        +--> bounded upload + image/size/frame validation
        |
        +--> V3 ONNX Runtime grading
        |      quality -> detection -> uncertainty -> accepted grade
        |
        +--> exact-grade frozen Phase 5 record lookup
        |
        +--> authoritative Phase 6 decision engine
        |
        v
Strict grading + market + decision_support + trace response
        |
        v
Localized farmer UI (EN/SI/TA)
```

Rejected/poor/uncertain inputs never proceed to price routing. Accepted grades never use the other grade’s price series. The runtime exposes frozen historical forecast evidence rather than recomputing a live forecast.

## 9. Current result summary

### 9.1 Grading

| Result set | Accuracy | Macro F1 | Coverage/rejection note |
|---|---:|---:|---|
| V1 MobileNetV2 | 77.78% | 0.7447 | Legacy 72-image test |
| V2 MobileNetV2 | 80.73% | 0.8068 | Leakage-safer 109-image test |
| V3 YOLO positive test | 95.83% | 0.9578 | 120/120 accepted |
| V3 adapted positive test | 95.83% | 0.9643 | 98.33% coverage; 2 rejections |
| V3 adapted new negative holdout | — | — | 49/49 rejected |

### 9.2 Price forecasting

| Result set | Selected method | Main finding |
|---|---|---|
| V1 | Random Forest absolute price | Poor generalization; R² -6.1315 |
| V2 | Random Forest vs persistence | Persistence decisively better: MAE 16.41, RMSE 22.52 |
| Phase 5 final test | Separate-grade Ridge, next log return | Beat persistence modestly on error; 52.38% direction accuracy |
| Phase 5 newest external check | Same frozen selection | 70% direction accuracy but slightly worse error than persistence |

### 9.3 Integration

- Phase 6: 28/28 scenario expectations; complete traces; 15 saved unit tests passed.
- Phase 7: 5/5 ONNX equivalence cases; 22/22 saved integrity checks.
- Corrected emulator: 5/5 controlled decision outcomes.
- Farmer UI: saved evidence reports clean Flutter analysis and 75/75 tests.
- Fresh report-time focused backend/decision tests: 30/30 passed on 2026-10-10.

## 10. Testing and verification history

The repository contains several kinds of evidence that must not be conflated:

1. **Model evidence:** frozen test predictions, confusion matrices, metrics JSON, checkpoint hashes, and plots.
2. **Integrity evidence:** dataset hashes, partition isolation, temporal causality, selection discipline, routing, and frozen-artifact checks.
3. **Software evidence:** unit/API/parser/widget tests, static analysis, startup/readiness checks, and failure handling.
4. **Runtime evidence:** controlled backend calls, Railway smoke tests, and a researcher-operated Android emulator flow.
5. **Missing evidence:** prospective field data, independent labels, farmer usefulness/economic outcomes, professional translation review, and production security/load testing.

Fresh checks during this report audit:

```text
.\.venv\Scripts\python.exe -m pytest \
  backend/tests/test_phase7_integration.py \
  backend/tests/test_phase7_text_integrity.py \
  backend/tests/test_main_startup.py \
  ml/grading_forecast/decision_support/phase6/tests/test_decision_engine.py \
  -q -p no:cacheprovider

30 passed in 9.32s
```

Fresh `flutter analyze` and `flutter test` invocations produced no output for several minutes and were stopped. No fresh Flutter pass is claimed. The latest committed successful evidence remains the October 8 clean analysis and 75/75 test run recorded in `MOBILE_UI_UX_REFINEMENT_RESULTS.md`; the October 9 changes were not freshly revalidated in this audit.

The Phase 5 validator was not rerun because its implementation rewrites the versioned integrity JSON and the workspace denied that write. Direct execution of two other validators also required module/PYTHONPATH invocation. Their versioned saved results were inspected, but this report does not mislabel them as fresh runs.

## 11. Limitations

### Grading and rejection

- V3 grades are project-specific and are not official export/SLS/buyer grades.
- V3 is sample/batch detection and grading, not individual-berry grading.
- Only 30 physical samples were in the positive test; images within a sample are correlated.
- Camera/resolution/class confounding remains a high unresolved shortcut risk.
- Confidence and class margin are model scores/heuristics, not calibrated probabilities.
- The 49-image negative holdout is small and internet-derived.
- Exact-hash deduplication was performed; semantic near-duplicate freedom was not claimed.
- Controlled blur/darkness/size tests do not prove behavior on natural field degradation.
- No prospective independent-camera, farm, season, background, cultivar, or post-harvest-condition validation exists.

### Price forecasting

- Observations are irregularly spaced and sample sizes are limited, especially Grade 2.
- Only past price/time features are used; no weather, production, imports/exports, exchange rate, demand, policy, or buyer variables are present.
- The external newest check has only ten predictions.
- Ridge’s external error is slightly worse than persistence even though direction is better.
- Directional accuracy is modest and the model does not predict flat movements well.
- Grade 2 intervals are very wide and performance is weaker.
- EAC farm-gate references are not live buyer offers or guaranteed transaction prices.
- Phase 7 serves frozen approved forecast records; it does not run live retraining/inference.

### System and deployment

- Controlled integration success does not prove predictive generalization or production readiness.
- No independent field E2E study or user-usability/economic-benefit study exists.
- No V3 TFLite/on-device runtime exists; the authoritative implementation is backend ONNX Runtime.
- Public-endpoint authentication, distributed rate limiting, adversarial robustness, and production load/security testing are incomplete.
- Firestore is optional and fail-safe, but live credentialed persistence is not central to the active Phase 7 research path.
- Sinhala/Tamil translations need independent linguistic review and device layout/accessibility checks.
- Final October 9 UI changes lack a fresh full Flutter validation and debug APK/device acceptance record.

## 12. Work still left to do

### Priority 1 — Execute prospective field/domain-shift validation

- Freeze the already prepared protocol before collection.
- Collect independent images across phones, lighting, backgrounds, farms, seasons, sample presentations, and poor-quality conditions.
- Obtain blinded independent/subject-matter labels and preserve inter-rater agreement.
- Keep physical samples grouped and keep the new test sealed.
- Measure grade accuracy/macro F1, coverage, rejection, uncertainty, per-device/per-condition results, and failure categories.
- Decide whether camera shortcut risk is tolerable or requires another redesign.

### Priority 2 — Strengthen price evidence

- Continue collecting future EAC observations prospectively without changing historical test results.
- Re-evaluate Ridge versus persistence on a larger truly future holdout.
- Report Grade 1 and Grade 2 separately.
- Investigate justified exogenous variables only with provenance and leakage-safe availability timestamps.
- Define a retraining/reselection schedule and model registry if live forecasting is required.
- Do not convert frozen Phase 5 records into a “live forecast” claim without implementing and validating live inference.

### Priority 3 — Independent end-to-end field evaluation

- Capture a real sample, produce a blinded reference grade, obtain contemporaneous market/reference price evidence, and run the full mobile/backend path.
- Evaluate whether the presented uncertainty is understandable and useful.
- Measure failures and user decisions without treating synthetic/compositional scenarios as field outcomes.
- Conduct farmer/usability and, if required, economic-benefit evaluation.

### Priority 4 — Final mobile/runtime acceptance

- Rerun `flutter analyze` and all Flutter tests at current HEAD.
- Produce a current debug/release APK with the intended hosted/local URL configuration.
- Test on an emulator and at least one physical Android phone.
- Recheck Grade 1, Grade 2, non-pepper, poor-image, and uncertain cases after the final UI commits.
- Review Sinhala/Tamil wording professionally and test text scaling, wrapping, fonts, and accessibility.

### Priority 5 — Production hardening, only if deployment is in scope

- Add authentication/authorization and distributed rate limiting.
- Add monitored artifact/version rollout and rollback.
- Perform dependency, secret, abuse, resource, load, privacy, and adversarial-input reviews.
- Validate hosted readiness and Grade 1/2 accepted paths after every deployment.
- Define retention/deletion rules and obtain ethics/privacy approval for real user images and study data.

### Priority 6 — Final documentation reconciliation

- Make this report or an updated successor the primary status document.
- Treat `historical/status/FULL_PROGRESS_REPORT.md` as an October 6 snapshot so its statement that V3 was untrained is not mistaken for current status.
- Keep the experiment log, phase reports, README, limitations, architecture, and presentation consistent.
- Use “complete with limitations,” “controlled integration,” and “field validation pending” consistently.

## 13. Completion assessment

| Requirement/workstream | Assessment |
|---|---|
| Dataset collection/preparation | Complete for current internal research datasets; external field dataset pending |
| Leakage-controlled visual model experiment | Complete |
| Non-pepper/quality/uncertainty experiment | Complete with bounded external evidence |
| Price source reconstruction | Complete |
| Controlled price candidate comparison | Complete with mixed conclusion |
| Exact grade-price routing and explanation | Complete |
| ONNX/backend/mobile controlled integration | Complete with limitations |
| Localization and farmer-oriented presentation | Implemented; independent/device review pending |
| Prospective field/domain validation | Not started |
| Live price forecasting service | Not implemented; frozen records are served |
| Production security/reliability certification | Not demonstrated |
| Economic impact/farmer-benefit validation | Not demonstrated |

The component is research- and demonstration-ready within its frozen controlled evidence. It is not field-validated or production-ready.

## 14. Principal evidence locations

### Research records

- `docs/research/LITERATURE_REVIEW_GAPS_BERRY_GRADING_PRICE_FORECASTING.md`
- `docs/research/EXPERIMENT_LOG.md`
- `docs/research/V3_DECISION_RECORD.md`
- `docs/research/V3_PHASE1_AUDIT.md`
- `docs/research/V3_PHASE2_YOLO_RESULTS.md`
- `docs/research/V3_PHASE3_REJECTION_RESULTS.md`
- `docs/research/V3_PHASE3_FOLLOWUP_REJECTION_RESULTS.md`
- `docs/research/PHASE4_PRICE_DATA_AUDIT.md`
- `docs/research/PHASE4_PRICE_FOUNDATION_RESULTS.md`
- `docs/research/PHASE5_PRICE_FORECASTING_RESULTS.md`
- `docs/research/PHASE6_FREEZE_AND_READINESS.md`
- `docs/research/PHASE6_FIELD_DATA_PROTOCOL.md`
- `docs/research/PHASE6_GRADE_PRICE_DECISION_ENGINE_RESULTS.md`
- `docs/research/PHASE7_ONNX_TFLITE_BACKEND_MOBILE_RESULTS.md`
- `docs/research/PHASE7_GRADING_FORECAST_LOCALIZATION_RESULTS.md`
- `docs/research/MOBILE_UI_UX_REFINEMENT_RESULTS.md`

### Data, models, and machine-readable metrics

- `data/processed/grading_forecast/berry_v3/`
- `data/external/phase3_rejection/`
- `data/external/phase3_followup_negatives/`
- `data/processed/grading_forecast/price/eac_reconstructed_v1/`
- `ml/grading_forecast/berry_grading/models/v3_yolo/`
- `ml/grading_forecast/berry_grading/models/v3_phase3_followup/`
- `ml/grading_forecast/berry_grading/evaluation/v3_yolo/`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup/`
- `ml/grading_forecast/price_forecasting/phase5/`
- `ml/grading_forecast/decision_support/phase6/`
- `ml/grading_forecast/evaluation/phase7/`

### Active integration code

- `backend/app/api/routes/grading_forecast.py`
- `backend/app/schemas/grading_forecast.py`
- `backend/app/services/grading_forecast/phase7_service.py`
- `ml/grading_forecast/deployment/phase7/`
- `mobile/lib/features/grading_forecast/`

## 15. Final conclusion

The work has moved well beyond the original proof of concept. The present repository contains a traceable, group-aware V3 grading experiment; an adapted rejection model; a provenance-rich Grade 1/Grade 2 price dataset; a validation-selected but honestly limited Ridge forecast; a deterministic grade-price decision engine; and a controlled ONNX/FastAPI/Flutter implementation with localized farmer-facing presentation.

The strongest defensible claim is:

> The component is a reproducible research decision-support prototype with strong internal harvested-sample grading results, improved bounded non-pepper rejection, a mixed but transparent price-movement model, and verified controlled integration. Its field robustness, official-grade equivalence, future-price reliability, economic value, and production readiness remain unproven and require prospective independent validation.
