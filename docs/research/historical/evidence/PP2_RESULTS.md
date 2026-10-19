# PP2 Results

Last updated: 2026-08-31

This document records PP2 evidence from completed audit, dataset preparation, and baseline experiments. Metrics are included only when backed by saved artifacts.

## Current Result Status

Phase 0 audit result: COMPLETE.

Phase 1 dataset preparation result: COMPLETE.

Phase 2 Berry Grading V2 baseline result: COMPLETE.

Phase 3 Price Forecasting V2 baseline result: COMPLETE.

Phase 4 Limited Model Improvement result: COMPLETE.

Phase 5 Integration Validation result: COMPLETE with runtime limitations.

Phase 6 PP2 Evidence and Documentation result: COMPLETE.

Post-PP2 runtime update: Phase 8 integrated the selected Berry V2 ONNX into the backend runtime, Phase 9 changed the price forecast runtime from `demo_baseline` to the validated `naive_persistence` method using the V2 National Grade 1 average weekly target, Phase 10 validated the existing recommendation logic with the real runtime grading and forecasting outputs, Phase 11 hardened backend error handling for this component, Phase 12 implemented Firebase persistence with fail-safe behavior when credentials are unavailable, and Phase 13 implemented an offline Flutter TFLite fallback plus grade-aware predicted-market-price display that still requires successful Flutter build/device validation.

## Final PP2 Evidence Summary

### V2 Dataset Summary

| Dataset | Primary Artifact | Size | Split | Key Validation |
| --- | --- | --- | --- | --- |
| Berry images V2 | `data/processed/grading_forecast/berry_dataset_v2_summary.json` | 671 images, 168 physical samples | Train 467 images, validation 95, test 109 | Sample-level split, no sample crosses splits |
| Price target V2 | `data/processed/grading_forecast/price_v2/price_v2_coverage_summary.json` | 232 National Grade 1 average weekly observations | Train 162 rows, validation 34, test 36 | Chronological split, no fabricated weeks, Grade 2 not imputed |

### Berry Grading Experiments

| Experiment | Dataset/Split | Model | Accuracy | Macro F1 | Weighted F1 | Grade 2 Precision | Grade 2 Recall | Grade 2 F1 | Conclusion |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Phase 2 baseline | `berry_v2`, sample-level V2 test | MobileNetV2 dropout 0.25 | 0.8073 | 0.8068 | 0.8076 | 0.7805 | 0.8889 | 0.8312 | Selected PP2 berry baseline |
| Phase 4 limited improvement | Same V2 test split | MobileNetV2 dropout 0.35 | 0.8073 | 0.8068 | 0.8076 | 0.7805 | 0.8889 | 0.8312 | Did not improve saved test metrics |

### Forecasting Experiments

Target: National + Grade 1 + average + farm_gate + weekly.

| Experiment | Method | Test Rows | MAE | RMSE | MAPE | R2 | Conclusion |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Phase 3 baseline | Naive Persistence | 36 | 16.4094 | 22.5208 | 0.8539 | 0.9045 | Strongest current forecasting result |
| Phase 3 baseline | RandomForest, original 11 features | 36 | 82.4179 | 88.4452 | 4.1679 | -0.4736 | Required ML baseline, underperformed naive |
| Phase 4 limited improvement | RandomForest plus `lag_4`, `lag_8`, `lag_12` | 36 | 78.1641 | 84.8622 | 3.9482 | -0.3566 | Improved over Phase 3 RF, still worse than naive |

### Integration Validation

| Item | Result | Runtime Evidence |
| --- | --- | --- |
| FastAPI startup | PASS | Backend started on `http://127.0.0.1:8000` |
| Health endpoint | PASS | HTTP 200, `status: ok` |
| Price forecast endpoint | PASS with fallback | HTTP 200, runtime model `demo_baseline` |
| Grade-only endpoint | PASS | HTTP 200, response indicated real ONNX grading model use |
| Analyze endpoint | PASS | HTTP 200 with grading, forecast, recommendation, and storage |
| Firebase storage | Safe fallback | `saved_to_firebase: false` |
| Flutter | Inspected only | API service points to backend endpoints; Flutter was not run |

### Evidence Map

| Evidence Item | Source |
| --- | --- |
| Berry V2 dataset counts and split | `data/processed/grading_forecast/berry_dataset_v2_summary.json` |
| Price V2 target counts and split | `data/processed/grading_forecast/price_v2/price_v2_coverage_summary.json` |
| Phase 2 berry baseline metrics | `ml/grading_forecast/berry_grading/models/v2/berry_classifier_metrics.json` |
| Phase 4 berry dropout metrics | `ml/grading_forecast/berry_grading/models/v2_phase4/berry_classifier_metrics.json` |
| Phase 3 naive and RF metrics | `ml/grading_forecast/price_forecasting/models/v2/forecast_metrics.json`, `naive_persistence_metrics.json` |
| Phase 4 forecast metrics | `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_metrics.json` |
| Phase 5 API validation | `docs/research/PP2_INTEGRATION_VALIDATION.md` |
| Phase 13 offline mobile fallback | `mobile/assets/models/berry_mobilenetv2_v2_best.tflite`, `mobile/lib/features/grading_forecast/services/offline_grading_forecast_service.dart`, `mobile/lib/features/grading_forecast/services/grading_forecast_analysis_service.dart` |
| Berry confusion matrix figure | `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/confusion_matrix.png` |
| Forecast actual-vs-predicted figure | `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/actual_vs_predicted.png` |
| Phase 4 forecast figures | `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/actual_vs_predicted.png`, `feature_importances.png`, `residuals.png` |

## Dataset Evidence From Audit

### Berry Dataset

Raw dataset path: `data/raw/berry_images/`

| Item | Audit Result |
| --- | --- |
| Total raw image files | 671 |
| Grade 1 images | 224 |
| Grade 2 images | 224 |
| Grade 3 images | 223 |
| Sample folders per grade | 56 |
| Root-level images | 0 |
| Unreadable images | 0 |
| Duplicate content groups | 0 |
| Main image dimensions | 4000x3000 and 4080x3060 |
| EXIF camera models | SM-A127F, Galaxy A06 |
| Known issue | Some samples have 3 or 5 images instead of 4 |

Interpretation:

The berry dataset is suitable for a meaningful PP2 classification experiment if it is split at physical-sample level. The current folder structure supports deriving `grade` and `sample_id` automatically. Manual annotation of unavailable metadata is not required for PP2.

## Phase 1 Dataset Preparation Results

### Berry V2 Manifest and Audit

Artifacts:

- `data/annotations/grading_forecast/berry_grading_labels_v2.csv`
- `data/processed/grading_forecast/berry_dataset_v2_summary.json`

| Item | V2 Result |
| --- | ---: |
| Manifest rows | 671 |
| Readable images | 671 |
| Unreadable images | 0 |
| Missing files | 0 |
| Duplicate image paths | 0 |
| Duplicate image-content groups | 0 |
| Total physical sample groups | 168 |
| Samples per grade | 56 |

Images per grade:

| Grade | Images |
| --- | ---: |
| Grade 1 | 224 |
| Grade 2 | 224 |
| Grade 3 | 223 |

Non-4-image samples:

| Grade | Sample | Image Count |
| --- | --- | ---: |
| Grade 1 | sample_028 | 3 |
| Grade 1 | sample_030 | 3 |
| Grade 3 | sample_010 | 3 |
| Grade 1 | sample_002 | 5 |
| Grade 1 | sample_018 | 5 |

### Berry V2 Sample-Level Split

Artifacts:

- `data/processed/grading_forecast/berry_split_v2/`
- `data/processed/grading_forecast/berry_split_v2_manifest.csv`

Split seed: 42.

| Split | Samples | Images |
| --- | ---: | ---: |
| Train | 117 | 467 |
| Validation | 24 | 95 |
| Test | 27 | 109 |

Sample counts by grade:

| Split | Grade 1 | Grade 2 | Grade 3 |
| --- | ---: | ---: | ---: |
| Train | 39 | 39 | 39 |
| Validation | 8 | 8 | 8 |
| Test | 9 | 9 | 9 |

Image counts by grade:

| Split | Grade 1 | Grade 2 | Grade 3 |
| --- | ---: | ---: | ---: |
| Train | 155 | 156 | 156 |
| Validation | 31 | 32 | 32 |
| Test | 38 | 36 | 35 |

Leakage validation:

- Every V2 image appears exactly once in the split manifest.
- Every split contains Grade 1, Grade 2, and Grade 3.
- No `grade + sample_id` group appears in more than one split.
- The split is sample-level, not image-level.

### Price Dataset

Raw dataset path: `data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv`

| Item | Audit Result |
| --- | --- |
| Total rows | 7,742 |
| Date range | 2021-02-22 to 2026-08-18 |
| Main practical coverage | early January 2022 to 2026-08-18 |
| Commodity | black_pepper |
| Country | Sri Lanka |
| Market level | farm_gate |
| Frequency | weekly |
| Price types | highest, average |
| Grades | Grade 1, Grade 2 |
| Grade 1 rows | 6,930 |
| Grade 2 rows | 812 |
| Duplicate date/district/grade/price_type rows | 0 |

Primary forecasting target:

`National + Grade 1 + average + farm_gate + weekly`

Reason:

This target is the most defensible PP2 forecasting series because it has stronger historical coverage than Grade 2 and avoids fabricating sparse observations.

### Price V2 Cleaned Dataset and Target

Artifacts:

- `data/processed/grading_forecast/price_v2/cleaned_price_data_v2.csv`
- `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`
- `data/processed/grading_forecast/price_v2/price_v2_coverage_summary.json`

| Item | V2 Result |
| --- | ---: |
| Raw rows | 7,742 |
| Cleaned rows | 7,742 |
| Target observations | 232 |
| Duplicate target dates | 0 |
| Target missing prices | 0 |
| Target gaps greater than 8 days | 12 |
| Largest target gap | 316 days |

Target date range:

- Minimum date: 2021-02-22.
- Maximum date: 2026-08-18.
- Largest gap: 2021-02-22 to 2022-01-04.

Observed target interval distribution in days:

| Interval Days | Count |
| ---: | ---: |
| 2 | 1 |
| 5 | 1 |
| 6 | 14 |
| 7 | 189 |
| 8 | 14 |
| 13 | 1 |
| 14 | 9 |
| 22 | 1 |
| 316 | 1 |

### Price V2 Chronological Split

Artifacts:

- `data/processed/grading_forecast/price_v2/forecast_train.csv`
- `data/processed/grading_forecast/price_v2/forecast_validation.csv`
- `data/processed/grading_forecast/price_v2/forecast_test.csv`

| Split | Rows | Date Range |
| --- | ---: | --- |
| Train | 162 | 2021-02-22 to 2025-03-18 |
| Validation | 34 | 2025-03-25 to 2025-11-25 |
| Test | 36 | 2025-12-02 to 2026-08-18 |

Grade 2 coverage:

- All observed Grade 2 rows: 812.
- National Grade 2 average observations: 161.
- Grade 2 observed dates by year: 2022: 6, 2023: 27, 2024: 49, 2025: 49, 2026: 30.
- Grade 2 remains out of scope for the primary PP2 forecasting target.

## Historical V1 Results

### Berry V1 MobileNetV2

Source: `ml/grading_forecast/berry_grading/models/berry_classifier_metrics.json`

| Metric | Result |
| --- | --- |
| Accuracy | 0.7778 |
| Weighted precision | 0.8516 |
| Weighted recall | 0.7778 |
| Weighted F1 | 0.7447 |
| Grade 1 recall | 1.0000 |
| Grade 2 recall | 0.3333 |
| Grade 3 recall | 1.0000 |

Interpretation:

This is a useful historical baseline, but it is not final PP2 evidence because it used the old 360-image dataset and did not include a proper sample-level train/validation/test split.

### Forecast V1 RandomForest

Source: `ml/grading_forecast/price_forecasting/models/forecast_metrics.json`

| Metric | Train | Test |
| --- | ---: | ---: |
| MAE | 15.7114 | 45.8347 |
| RMSE | 24.3440 | 47.7556 |
| MAPE | 0.9527 | 2.2911 |
| R2 | 0.9841 | -6.1315 |

Interpretation:

The V1 RandomForest model showed overfitting or poor future generalization. This motivates a cleaner V2 comparison against naive persistence.

## V2 Berry Results

Status: COMPLETE.

Source artifacts:

- Model: `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.keras`
- ONNX: `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`
- Metrics: `ml/grading_forecast/berry_grading/models/v2/berry_classifier_metrics.json`
- Metadata: `ml/grading_forecast/berry_grading/models/v2/berry_model_metadata.json`
- Training history: `ml/grading_forecast/berry_grading/models/v2/training_history.json`
- Confusion matrix: `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/confusion_matrix.png`
- Training curves: `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/training_curves.png`

V2 training summary:

- Dataset: `berry_v2`.
- Split: sample-level train/validation/test.
- Train: 117 samples, 467 images.
- Validation: 24 samples, 95 images.
- Test: 27 samples, 109 images.
- Training input: `data/processed/grading_forecast/berry_split_v2/train/`.
- Validation input: `data/processed/grading_forecast/berry_split_v2/val/`.
- Test input: `data/processed/grading_forecast/berry_split_v2/test/`.
- Model: MobileNetV2, ImageNet initialization, `include_top=False`.
- Input: 224x224 RGB.
- Optimizer/loss: Adam with sparse categorical cross-entropy.
- Stage 1: frozen backbone, maximum 15 epochs, learning rate 0.001, patience 3; 14 epochs completed.
- Stage 2: limited fine-tuning, maximum 5 epochs, learning rate 0.00001, patience 2; 5 epochs completed.
- Recorded training duration: 1216.447 seconds.
- Evaluation duration: 31.934 seconds.
- ONNX export duration: 10.209 seconds.

V2 final test metrics:

| Metric | Result |
| --- | ---: |
| Accuracy | 0.8073 |
| Macro precision | 0.8122 |
| Macro recall | 0.8078 |
| Macro F1 | 0.8068 |
| Weighted precision | 0.8145 |
| Weighted recall | 0.8073 |
| Weighted F1 | 0.8076 |

Per-class V2 test metrics:

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| Grade 1 | 0.9063 | 0.7632 | 0.8286 | 38 |
| Grade 2 | 0.7805 | 0.8889 | 0.8312 | 36 |
| Grade 3 | 0.7500 | 0.7714 | 0.7606 | 35 |

Confusion matrix:

```text
[[29,  3,  6],
 [ 1, 32,  3],
 [ 2,  6, 27]]
```

Historical comparison:

| Experiment | Dataset | Split | Accuracy | Macro F1 | Weighted F1 | Grade 2 Recall | Decision |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| V1 MobileNetV2 | berry_v1 | legacy train-val | 0.7778 | 0.7447 | 0.7447 | 0.3333 | Historical baseline |
| V2 MobileNetV2 | berry_v2 | sample-level train-val-test | 0.8073 | 0.8068 | 0.8076 | 0.8889 | Selected PP2 berry baseline |
| V2 dropout 0.35 | berry_v2 | same sample-level test split | 0.8073 | 0.8068 | 0.8076 | 0.8889 | Limited Phase 4 experiment; no metric improvement |

Interpretation:

The V2 model is the selected PP2 berry grading baseline because it was trained on the expanded V2 dataset, used the leakage-safe sample-level split, and was evaluated once on the untouched V2 test set. The V1 and V2 metrics are useful for historical comparison, but they are not directly equivalent experiments because V1 used the older 360-image dataset and did not include the same sample-level train/validation/test methodology.

## V2 Forecast Results

Status: COMPLETE.

Target:

`National + Grade 1 + average + farm_gate + weekly`

Reason for Grade 1 target:

National Grade 1 average has the strongest usable coverage for PP2. Grade 2 is preserved in the cleaned dataset but remains too sparse for the primary forecasting baseline.

Artifacts:

- `ml/grading_forecast/price_forecasting/models/v2/forecast_model.joblib`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_features.json`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_metrics.json`
- `ml/grading_forecast/price_forecasting/models/v2/naive_persistence_metrics.json`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_model_metadata.json`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_export_manifest.json`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/actual_vs_predicted.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/feature_importances.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/residuals.png`

Chronological split:

| Split | Rows | Date Range |
| --- | ---: | --- |
| Train | 162 | 2021-02-22 to 2025-03-18 |
| Validation | 34 | 2025-03-25 to 2025-11-25 |
| Test | 36 | 2025-12-02 to 2026-08-18 |

Test methodology:

- Naive Persistence and RandomForest were evaluated on the same 36 V2 test timestamps.
- RandomForest was trained only on `forecast_train.csv`.
- Test feature rows were built from full target context, but every feature date is before its prediction date.
- Lag and rolling features use previous available observations, not guaranteed previous calendar weeks.
- No missing weeks or prices were fabricated.

Final comparison:

| Experiment | Target | Split | MAE | RMSE | MAPE | R2 | Decision |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Naive persistence | National Grade 1 average | 36 identical test timestamps | 16.4094 | 22.5208 | 0.8539 | 0.9045 | Stronger Phase 3 baseline |
| RandomForest | National Grade 1 average | 36 identical test timestamps | 82.4179 | 88.4452 | 4.1679 | -0.4736 | Required ML baseline, did not outperform naive |
| Extended-lag RandomForest | National Grade 1 average | same 36 test timestamps | 78.1641 | 84.8622 | 3.9482 | -0.3566 | Improved over Phase 3 RF, but not over naive |

Interpretation:

Naive Persistence outperformed RandomForest on every final V2 test metric. This does not invalidate the experiment; it is the Phase 3 finding. For PP2, the defensible conclusion is that the simple persistence baseline generalizes better than the current RandomForest configuration on this short and mostly stable test period.

## Phase 4 Limited Improvement Results

Status: COMPLETE.

### Berry Limited Improvement

Selected change:

- Phase 2 baseline dropout: 0.25.
- Phase 4 dropout: 0.35.
- All other core settings remained aligned with the Phase 2 MobileNetV2 baseline.
- Evaluation used the same untouched `berry_split_v2/test` directory with 109 images.

| Model | Accuracy | Macro F1 | Weighted F1 | Grade 2 Precision | Grade 2 Recall | Grade 2 F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Phase 2 V2 MobileNetV2 | 0.8073 | 0.8068 | 0.8076 | 0.7805 | 0.8889 | 0.8312 |
| Phase 4 Dropout 0.35 | 0.8073 | 0.8068 | 0.8076 | 0.7805 | 0.8889 | 0.8312 |

Phase 4 per-class berry metrics:

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| Grade 1 | 0.9063 | 0.7632 | 0.8286 | 38 |
| Grade 2 | 0.7805 | 0.8889 | 0.8312 | 36 |
| Grade 3 | 0.7500 | 0.7714 | 0.7606 | 35 |

Berry interpretation:

The dropout 0.35 experiment did not improve or worsen the saved headline test metrics compared with the Phase 2 baseline. This is still a valid Phase 4 finding because the experiment used the same leakage-safe split and records that this limited change did not produce measurable benefit on the V2 test set.

Berry Phase 4 artifacts:

- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_mobilenetv2_v2_phase4_best.keras`
- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_classifier_metrics.json`
- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_model_metadata.json`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v2_phase4/confusion_matrix.png`

### Forecasting Limited Improvement

Selected change:

- Phase 3 RandomForest baseline features plus `lag_4`, `lag_8`, and `lag_12`.
- Same V2 National Grade 1 average weekly target.
- Same 36 V2 test timestamps.
- Past-only feature construction preserved.

| Model | MAE | RMSE | MAPE | R2 |
| --- | ---: | ---: | ---: | ---: |
| Naive Persistence | 16.4094 | 22.5208 | 0.8539 | 0.9045 |
| Phase 3 RandomForest | 82.4179 | 88.4452 | 4.1679 | -0.4736 |
| Phase 4 Extended-Lag RandomForest | 78.1641 | 84.8622 | 3.9482 | -0.3566 |

Forecasting interpretation:

The Phase 4 extended-lag RandomForest improved over the Phase 3 RandomForest baseline on all four metrics. However, Naive Persistence remained substantially stronger on the same test period. Therefore, the limited forecasting improvement did not produce the best forecasting model for PP2; it shows a modest RF improvement but confirms the simple persistence baseline as the strongest current forecasting result.

Forecasting Phase 4 artifacts:

- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_model.joblib`
- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_metrics.json`
- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_model_metadata.json`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/actual_vs_predicted.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/feature_importances.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/residuals.png`

## Integration Evidence

Status: COMPLETE with runtime limitations.

Evidence file:

- `docs/research/PP2_INTEGRATION_VALIDATION.md`

Backend validation:

| Endpoint | Method | HTTP Status | Runtime Result |
| --- | --- | ---: | --- |
| `/api/v1/grading-forecast/health` | GET | 200 | Returned `status: ok` |
| `/api/v1/grading-forecast/price-forecast` | GET | 200 | Returned forecast using `demo_baseline` |
| `/api/v1/grading-forecast/grade-only` | POST multipart | 200 | Returned Grade 1 prediction and indicated real ONNX grading model use |
| `/api/v1/grading-forecast/analyze` | POST multipart | 200 | Returned grading, forecast, recommendation, and storage fields |

Sample image used:

- `data/processed/grading_forecast/berry_split_v2/test/grade_1/sample_002/20260508_152537.jpg`

Observed endpoint details:

- Health response: `{"status":"ok","component":"berry_grading_export_price_forecasting"}`.
- Price forecast response model: `demo_baseline`.
- Grade-only predicted grade: Grade 1.
- Grade-only quality score/confidence: 79.7 / 0.65.
- Analyze decision: `SELL_EXPORT`.
- Analyze storage: `saved_to_firebase: false`.

Runtime model/fallback interpretation at Phase 5 validation time:

- At Phase 5, the backend resolved berry grading ONNX from the legacy/root artifact path: `ml/grading_forecast/berry_grading/models/berry_mobilenetv2_best.onnx`.
- Phase 8 later changed the berry runtime to `BERRY-V2-MNV2`: `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`.
- At Phase 5, the price forecast endpoint returned `demo_baseline`, not the Phase 3 or Phase 4 V2 forecasting models.
- Phase 9 later changed the real application forecast runtime to `naive_persistence` using `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`.
- Firebase was not configured; the analyze response still completed with storage fallback.

Mobile inspection:

- Flutter API service exists and calls `/api/v1/grading-forecast/analyze` and `/api/v1/grading-forecast/recommend`.
- Default backend URL is `localhost:8000` for desktop/web and `10.0.2.2:8000` for Android emulator.
- Flutter was not run during Phase 5.

### Post-PP2 Runtime Hardening

Phase 11 backend reliability validation passed for the grading-forecast API path.

Verified behavior:

- Valid grade-only request used `BERRY-V2-MNV2`.
- Valid price forecast request used `naive_persistence` and did not return `demo_baseline`.
- Valid analyze request returned V2 grading, `naive_persistence` forecast, recommendation, and optional storage.
- Missing, empty, unsupported/non-image, corrupt, and oversized image uploads returned safe HTTP errors.
- Corrective validation on 2026-08-30 confirmed Flutter-style multipart uploads are accepted when the actual bytes decode to supported JPEG, PNG, or WEBP, even if the client MIME value is missing or `application/octet-stream`.
- Missing V2 berry model artifacts failed explicitly without loading the legacy/root ONNX model.
- Missing or malformed forecast data returned `forecast_unavailable`.
- Unexpected grading and recommendation failures returned safe JSON errors.

Phase 11 and the corrective upload-validation fix did not modify datasets, model artifacts, Firebase configuration, Flutter code, recommendation rules, or forecasting method selection.

### Post-PP2 Persistence Implementation

Phase 12 implemented Firebase persistence for application-level result history.

Validated behavior:

- Firebase credentials are not required for the local/demo component flow.
- With Firebase unconfigured, analyze returned valid V2 grading, `naive_persistence` forecast, recommendation, and `saved_to_firebase: false`.
- With simulated Firebase save failure, analyze still returned valid grading/forecast/recommendation and `saved_to_firebase: false`, `document_id: null`.
- A mocked successful save returned `saved_to_firebase: true` with a generated document ID.
- A mocked successful save confirmed the intended Firestore collection `grading_forecast_results` and result metadata structure, including runtime identifiers for `BERRY-V2-MNV2` and `naive_persistence`.
- Current storage code does not store raw image bytes.
- Stored records are currently application-level/non-user-scoped because no existing authenticated user identity was found for this component.
- Live Firebase write validation was not performed because credentials are not configured.

No Firebase credentials were configured or committed during Phase 12.

### Phase 12.5 Runtime Diagnostic Validation

Manual application testing raised two diagnostic concerns: suspicious berry classifications and identical forecast values for different berry grades. Phase 12.5 investigated these concerns without changing code, datasets, models, preprocessing, class mappings, forecasting logic, recommendation rules, Firebase, or Flutter.

Berry diagnostic summary:

| Check | Result |
| --- | --- |
| Direct ONNX vs backend service | Agreed on all 9 selected V2 test images |
| 9-image diagnostic accuracy | 6/9 correct |
| Grade 1 diagnostic result | 3/3 correct |
| Grade 2 diagnostic result | 0/3 correct |
| Grade 3 diagnostic result | 3/3 correct |
| Class order | Grade 1, Grade 2, Grade 3 |
| ONNX input | `image`, float tensor, `[None, 224, 224, 3]` |
| ONNX output | `probs`, `[None, 3]` |
| Confirmed preprocessing concern | Training used direct 224x224 resize; backend runtime uses RGB letterbox to 224x224 |

This 9-image result is diagnostic only and does not replace the saved full V2 test metrics.

Forecast diagnostic summary:

| Check | Result |
| --- | --- |
| Runtime forecast source | `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv` |
| Runtime method | `naive_persistence` |
| Target scope | Single National Grade 1 average weekly series |
| Latest observed price | 2026-08-18, 1886.14 LKR/kg, rounded to `1886` |
| Runtime prediction | `1886`, stable trend |
| Grade-specific forecast behavior | Not implemented; identical forecasts across berry grades are expected under the current single-series design |

Recommendation impact:

The recommendation service receives the actual runtime grade and actual `naive_persistence` forecast. Therefore, an incorrect berry grade can propagate into an incorrect recommendation even if forecasting and recommendation logic are operating as implemented.

### Phase 13 Offline Mobile TFLite Fallback

Phase 13 was added after hosted-backend testing showed timeout and HTTP 429 behavior. It is implementation work, not a new research experiment.

Implemented behavior:

- The existing selected V2 Keras berry model was exported to `mobile/assets/models/berry_mobilenetv2_v2_best.tflite`.
- Flutter bundles class names, the National Grade 1 average weekly price series, and Naive Persistence metrics under `mobile/assets/data/`.
- The grading-forecast UI now uses an analysis service that defaults to offline TFLite mode and can switch back to backend API mode with `--dart-define=PEPPER_ANALYSIS_MODE=api`.
- Offline forecast output uses `naive_persistence_mobile` and the same single-series Grade 1 target limitation as the backend runtime.
- Offline storage reports `saved_to_firebase: false`; Firebase persistence remains backend-only.
- The price screen now shows a single `Predicted market price` value for the model-predicted grade and no longer provides a manual grade selector.
- Grade 2 predicted market price uses a 100 LKR/kg discount derived from the latest observed National average Grade 1 vs Grade 2 gap: 1886.14 minus 1800.00 LKR/kg on 2026-08-18, rounded for display.
- Grade 3 predicted market price is shown as unavailable because no reliable Grade 3 historical price series exists.

Validation status:

- TFLite export and tensor metadata inspection completed without retraining.
- Confirmed TFLite input is `[1, 224, 224, 3]` float32 RGB `0..255`, with output `[1, 3]` float32.
- Focused backend tests for grade-aware pricing and route behavior passed.
- Flutter build, analyzer, formatter, and emulator validation remain pending because local Flutter/Dart tooling timed out.

Validated API endpoints:

- `GET /api/v1/grading-forecast/health`
- `POST /api/v1/grading-forecast/grade-only`
- `GET /api/v1/grading-forecast/price-forecast`
- `POST /api/v1/grading-forecast/analyze`

Documented but not separately called during the Phase 5 pass:

- `POST /api/v1/grading-forecast/recommend`

Expected PP2 evidence:

- backend health response: complete;
- one grade-only response: complete;
- one full analyze response: complete;
- note showing whether real model or fallback was used: complete;
- optional Flutter screenshots: not performed.

## PP2 Result Narrative

Recommended narrative:

The V1 implementation established a working end-to-end baseline. After PP1, the datasets were expanded substantially. The PP2 work corrects the methodology by creating V2 datasets, preventing berry sample leakage, selecting a defensible price forecasting target, comparing against simple baselines, and validating integration with the shared mobile/backend architecture.

## PP2 Speaking Points

- Research problem: support black pepper farmers/export preparation with camera-based berry grading, short-term price forecasting, and a sell/wait/process recommendation flow.
- Data preparation: PP2 rebuilt the dataset foundation as V2, with 671 berry images from 168 physical samples and a sample-level split to prevent leakage.
- Price target: forecasting uses National Grade 1 average farm-gate weekly price because Grade 2 coverage is too sparse for a defensible primary target.
- Berry baseline: the V2 MobileNetV2 model achieved 0.8073 accuracy and 0.8076 weighted F1 on the untouched V2 test split.
- Berry improvement: dropout 0.35 was tested as one limited Phase 4 change and did not improve the saved test metrics.
- Forecasting baseline: Naive Persistence strongly outperformed the Phase 3 RandomForest on the same 36 test timestamps.
- Forecasting improvement: adding `lag_4`, `lag_8`, and `lag_12` improved RandomForest, but it still remained worse than Naive Persistence.
- Integration validation: FastAPI endpoints started and returned usable responses during Phase 5; later Phase 8/9 work integrated Berry V2 runtime and Naive Persistence forecast runtime.
- Offline fallback: Phase 13 added an on-device TFLite path for Flutter when hosted or local backend access is unavailable; build/device validation is still pending.
- Limitations: camera grading is not official SLS certification; Grade 2 forecasting is out of scope; Firebase, Flutter E2E, and final integrated validation remain pending.
- Current conclusion: PP2 has defensible V2 datasets, completed baseline experiments, one limited improvement per subproblem, honest limitations, and a known backend demo path.
- Future work: complete cross-component integration, validate the Flutter live flow, perform live Firebase validation when credentials are available, improve forecasting features with additional evidence, and perform broader post-PP2 model evaluation.
