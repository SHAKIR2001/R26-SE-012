# Experiment Log: Berry Grading and Export Price Forecasting

Last updated: 2026-08-31

This document records dataset versions, model experiments, metrics, observations, and model-selection reasoning. Do not enter fabricated metrics. Use `PENDING` until an experiment is actually run.

## Dataset Versions

| Dataset ID | Type | Source | Status | Notes |
| --- | --- | --- | --- | --- |
| berry_v1 | Image classification | `data/processed/grading_forecast/berry_images_processed/` | LEGACY | 360 processed images, 120 per class, created before current dataset expansion. |
| berry_v2 | Image classification | `data/raw/berry_images/` | PREPARED | 671 readable JPGs. V2 manifest and deterministic sample-level train/validation/test split created with seed 42. |
| price_v1 | Forecasting | `data/processed/grading_forecast/forecast_training_data.csv` | LEGACY | 216 National Grade 1 average rows through 2026-04-21. |
| price_v2 | Forecasting | `data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv` | PREPARED | 7,742 preserved rows. Primary target has 232 National Grade 1 average farm-gate weekly observations through 2026-08-18. |

## Dataset Preparation Entries

| Entry ID | Status | Dataset | Script | Output Artifacts | Validation Result | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| DATASET-BERRY-V2-PREP | COMPLETE | berry_v2 | `ml/grading_forecast/berry_grading/preprocessing/prepare_berry_dataset_v2.py` | `berry_grading_labels_v2.csv`, `berry_dataset_v2_summary.json`, `berry_split_v2/`, `berry_split_v2_manifest.csv` | PASSED | 168 physical sample groups. Split: train 117 samples/467 images, validation 24 samples/95 images, test 27 samples/109 images. No `grade + sample_id` group crosses splits. |
| DATASET-PRICE-V2-PREP | COMPLETE | price_v2 | `ml/grading_forecast/price_forecasting/data/prepare_price_v2_dataset.py` | `cleaned_price_data_v2.csv`, `national_grade1_average_weekly.csv`, `price_v2_coverage_summary.json`, `forecast_train.csv`, `forecast_validation.csv`, `forecast_test.csv` | PASSED | Chronological split: train 2021-02-22 to 2025-03-18, validation 2025-03-25 to 2025-11-25, test 2025-12-02 to 2026-08-18. Missing weeks were documented, not fabricated. |

## Pipeline Preparation Entries

| Entry ID | Status | Scope | Files Updated | Validation Result | Notes |
| --- | --- | --- | --- | --- | --- |
| PIPELINE-BERRY-V2-SAFE | COMPLETE | Berry grading V2 pre-training pipeline | `train_berry_classifier.py`, `evaluate_berry_classifier.py`, `export_berry_model.py`, `predict_berry_grade.py` | PASSED | Added explicit V2 train/val/test and output-path support. Dry-runs resolve to `berry_split_v2` and `models/v2`. No model training performed. |
| PIPELINE-PRICE-V2-SAFE | COMPLETE | Price forecasting V2 pre-execution pipeline | `train_forecast_model.py`, `evaluate_forecast_model.py`, `export_forecast_model.py`, `predict_future_price.py` | PASSED | Added explicit V2 path checks, dry-runs, same-test-timestamp evaluation plan, naive persistence metrics support, and V2 output-path support. No RandomForest training or final test evaluation performed. |

## Integration Validation Entries

| Entry ID | Status | Scope | Evidence | Validation Result | Notes |
| --- | --- | --- | --- | --- | --- |
| INTEGRATION-PHASE5-BACKEND | COMPLETE | Backend grading forecast API | `docs/research/PP2_INTEGRATION_VALIDATION.md` | PASSED WITH LIMITATIONS | FastAPI started and health, price forecast, grade-only, and analyze endpoints returned HTTP 200. Runtime grading used the legacy/root ONNX artifact. Runtime forecasting returned `demo_baseline`. Firebase storage was not configured and returned `saved_to_firebase: false`. |
| AUDIT-PHASE7-IMPLEMENTATION | COMPLETE | Existing implementation audit for berry grading and price forecasting runtime | `docs/research/Pending Work Plan — Berry Grading & Price Forecasting.md`, `docs/research/PROJECT_STATUS.md`, `docs/research/PP2_EXECUTION_CHECKLIST.md` | PASSED | Audit traced Flutter/API to FastAPI routes, services, model/inference, recommendation, Firebase/storage, response handling, configuration, and fallback behavior. At Phase 7 audit time, berry runtime used the legacy/root ONNX model, while the V2 research ONNX existed separately. Forecast runtime can return `demo_baseline`; V2 RF, Phase 4 RF, and Naive Persistence research evidence remain separate from runtime integration. No application code was changed during Phase 7. |
| INTEGRATION-PHASE8-BERRY-V2-RUNTIME | COMPLETE | Berry V2 backend runtime integration | `backend/app/services/grading_forecast/grading_service.py`, `docs/research/PROJECT_STATUS.md`, `docs/research/PP2_EXECUTION_CHECKLIST.md` | PASSED | Berry grading runtime now loads `BERRY-V2-MNV2` from `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`. Service-level validation used `data/processed/grading_forecast/berry_split_v2/test/grade_1/sample_002/20260508_152537.jpg` and returned `Grade 1` with confidence `0.88`; the explanation identified the V2 model path. Existing API response structure was preserved. Forecasting, recommendation rules, Firebase, Flutter, datasets, training, and model artifacts were not changed. |
| INTEGRATION-PHASE9-FORECAST-RUNTIME | COMPLETE | Price forecasting runtime integration | `backend/app/services/grading_forecast/price_forecast_service.py`, `docs/research/PROJECT_STATUS.md`, `docs/research/PP2_EXECUTION_CHECKLIST.md` | PASSED | Requirement check found short-term forecasting/time-series expectations, but no strict runtime mandate to use a trained RandomForest artifact despite weaker V2 test results. Runtime forecasting now uses `naive_persistence` with `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv` and saved V2 naive metrics. Service validation returned current price `1886`, predicted price `1886`, trend `stable`, MAE `16.4094`, RMSE `22.5208`, and deterministic repeat `true`. Missing-file validation returns `forecast_unavailable`, not `demo_baseline`. |
| INTEGRATION-PHASE10-RECOMMENDATION | COMPLETE | Recommendation and decision logic validation | `backend/app/services/grading_forecast/recommendation_service.py`, `backend/app/api/routes/grading_forecast.py`, `docs/research/PROJECT_STATUS.md`, `docs/research/PP2_EXECUTION_CHECKLIST.md` | PASSED | Existing rule-table recommendations were validated without changing business rules. The actual-output chain used `BERRY-V2-MNV2` grading and `naive_persistence` forecasting, producing Grade 1, stable trend, and `SELL_EXPORT`. Representative Grade 1/2/3 upward/downward cases, stable trend, missing optional fields, and invalid schema handling were validated. No application code was modified during Phase 10. |
| INTEGRATION-PHASE11-BACKEND-HARDENING | COMPLETE | Backend reliability and error handling for grading-forecast API | `backend/app/api/routes/grading_forecast.py`, `backend/app/services/grading_forecast/grading_service.py`, `docs/research/PROJECT_STATUS.md`, `docs/research/PP2_EXECUTION_CHECKLIST.md` | PASSED; corrective upload validation passed on 2026-08-30 | Added focused image upload validation and safe service failure handling. Valid V2 grading still identifies `BERRY-V2-MNV2`; valid forecasting still returns `naive_persistence`; analyze still returns grading, forecast, recommendation, and optional storage. Corrective validation fixed a Flutter upload compatibility defect where a valid image could be rejected before byte decoding because the multipart MIME value was unreliable. The backend now accepts valid JPEG/PNG/WEBP bytes even when MIME is missing or `application/octet-stream`; missing/empty/non-image/corrupt/oversized images return safe HTTP errors. Missing V2 model artifacts and invalid V2 class mapping fail explicitly without loading the legacy/root ONNX model. Missing or malformed forecast data returns `forecast_unavailable`, not fabricated prices; API routes that require a forecast return HTTP 503 for unavailable forecasts. Unexpected grading/recommendation failures return safe JSON errors. No datasets, model artifacts, Flutter code, Firebase configuration, recommendation rules, or forecasting method selection were changed. |
| INTEGRATION-PHASE12-FIREBASE-PERSISTENCE | COMPLETE | Firebase persistence implementation | `backend/app/services/grading_forecast/result_storage_service.py`, `backend/app/db/firebase.py`, `docs/guidelines_with_steps.md`, `docs/research/PROJECT_STATUS.md`, `docs/research/PP2_EXECUTION_CHECKLIST.md` | IMPLEMENTATION PASSED; LIVE WRITE NOT VALIDATED | Firebase persistence was implemented for application-level result history. Each persisted analysis uses a generated analysis/document ID and stores component metadata, runtime identifiers, V2 grading result, `naive_persistence` forecast, recommendation, and timestamp in `grading_forecast_results`. Validation confirmed mocked Firebase success returns `saved_to_firebase: true` with a document ID; unconfigured Firebase, initialization failure, write failure, and serialization failure return non-persisted status without breaking valid grading/forecast/recommendation output. No credentials were configured or committed. Retrieval was not required by inspected component requirements. |
| INTEGRATION-PHASE12.5-RUNTIME-DIAGNOSTIC | COMPLETE | Runtime model and forecast diagnostic validation | `ml/grading_forecast/berry_grading/training/train_berry_classifier.py`, `ml/grading_forecast/berry_grading/training/export_berry_model.py`, `backend/app/services/grading_forecast/grading_service.py`, `backend/app/services/grading_forecast/price_forecast_service.py`, `ml/grading_forecast/berry_grading/models/v2/class_names.json`, `ml/grading_forecast/berry_grading/models/v2/onnx_metadata.json`, `data/processed/grading_forecast/price_v2/price_v2_coverage_summary.json` | DIAGNOSTIC COMPLETE; NO CODE CHANGED | Manual app testing raised concerns about berry misclassification and identical price forecasts across grades. A controlled 9-image V2 test diagnostic found direct ONNX and backend service predictions agreed for every image, so no direct ONNX-vs-backend class mapping disagreement was confirmed. The sample was 6/9 correct, with Grade 2 at 0/3; this is diagnostic only and does not replace the saved full-test metrics. A preprocessing mismatch was confirmed for later review: training used direct Keras resize to 224x224, while backend runtime uses RGB letterbox to 224x224. Forecast diagnostics confirmed runtime uses one National Grade 1 average weekly series with `naive_persistence`; latest price 1886.14 is rounded to 1886 and predicted as 1886, so identical forecasts across berry grades are expected under the current single-series design. No application code, Flutter code, models, datasets, preprocessing, class mappings, forecasting logic, recommendation rules, or Firebase code were changed. |
| INTEGRATION-PHASE13-OFFLINE-MOBILE-TFLITE | IMPLEMENTED / BUILD VALIDATION PENDING | Offline Flutter grading-forecast fallback and grade-aware predicted market price display | `ml/grading_forecast/berry_grading/training/export_berry_tflite_model.py`, `mobile/assets/models/berry_mobilenetv2_v2_best.tflite`, `mobile/assets/data/`, `mobile/lib/features/grading_forecast/services/offline_grading_forecast_service.dart`, `mobile/lib/features/grading_forecast/services/grading_forecast_analysis_service.dart`, `mobile/lib/features/grading_forecast/screens/price_forecast_screen.dart`, `backend/app/services/grading_forecast/price_forecast_service.py` | TFLite export metadata checked; backend focused tests passed; Flutter validation pending | Existing selected V2 Keras model was converted to TFLite for on-device grading. Flutter analysis now defaults to offline mode and can use API mode with `PEPPER_ANALYSIS_MODE=api`. The price page now shows one `Predicted market price` for the model-predicted grade and removes manual grade selection. Grade 1 uses the National Grade 1 weekly naive-persistence value; Grade 2 subtracts a rounded 100 LKR/kg discount derived from the latest observed National average Grade 1 vs Grade 2 gap; Grade 3 price is unavailable because no reliable Grade 3 historical price series exists. Offline storage returns `saved_to_firebase: false`. No model training, dataset modification, or new evaluation metrics were produced. Local Flutter formatter/analyzer/build validation did not complete because the toolchain timed out. |

## Documentation Finalization Entries

| Entry ID | Status | Scope | Evidence | Validation Result | Notes |
| --- | --- | --- | --- | --- | --- |
| DOCS-PHASE6-PP2-EVIDENCE | COMPLETE | PP2 evidence and documentation | `PP2_RESULTS.md`, `PROJECT_STATUS.md`, `PP2_LIMITATIONS.md`, `PP2_EXECUTION_CHECKLIST.md`, `PP2_MASTER_PLAN.md` | PASSED | Final dataset, berry, forecasting, integration, evidence-map, limitations, and speaking-point sections were completed from existing saved artifacts only. No experiments or API calls were run during Phase 6. |

## Experiment Register

| Experiment ID | Status | Dataset | Split | Model/Method | Purpose | Key Config | Metrics | Artifact Path | Observation | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BERRY-V1-MNV2 | COMPLETE | berry_v1 | image-level/dir train-val split | MobileNetV2 | Historical baseline | 224x224, transfer learning, augmentation, fine-tune top layers | Accuracy 0.7778, weighted F1 0.7447 | `ml/grading_forecast/berry_grading/models/berry_classifier_metrics.json` | Grade 2 recall was weak at 0.3333. No separate test split. | Keep as historical baseline only. |
| PRICE-V1-RF | COMPLETE | price_v1 | chronological train-test | RandomForestRegressor | Historical forecasting baseline | lag_1..3, rolling 3/5, time features | Test MAE 45.8347, RMSE 47.7556, R2 -6.1315 | `ml/grading_forecast/price_forecasting/models/forecast_metrics.json` | Weak future generalization despite strong train metrics. | Keep as historical baseline only. |
| BERRY-V2-MNV2 | COMPLETE | berry_v2 | sample-level train-val-test | MobileNetV2 | Primary PP2 berry baseline | ImageNet, 224x224 RGB, batch 16, Adam, sparse categorical cross-entropy, stage1 15 max epochs LR 0.001, stage2 5 max epochs LR 0.00001 | Accuracy 0.8073, macro F1 0.8068, weighted F1 0.8076, Grade 2 precision 0.7805, Grade 2 recall 0.8889, Grade 2 F1 0.8312 | `ml/grading_forecast/berry_grading/models/v2/` | Trained on V2 train/val only, evaluated once on untouched V2 test set. ONNX export succeeded. | Select as PP2 berry baseline. |
| BERRY-V2-IMPROVE-1 | COMPLETE | berry_v2 | same as BERRY-V2-MNV2 | MobileNetV2 dropout 0.35 | Limited berry improvement | Same as Phase 2 baseline except dropout 0.25 -> 0.35 | Accuracy 0.8073, macro F1 0.8068, weighted F1 0.8076, Grade 2 precision 0.7805, Grade 2 recall 0.8889, Grade 2 F1 0.8312 | `ml/grading_forecast/berry_grading/models/v2_phase4/` | Saved headline metrics matched Phase 2 baseline; model hash differs from Phase 2. | Do not replace Phase 2 baseline based on this result. |
| PRICE-V2-NAIVE | COMPLETE | price_v2 | chronological train-val-test | Naive persistence | Required forecast baseline | prediction(t+1) = observed price(t) | MAE 16.4094, RMSE 22.5208, MAPE 0.8539, R2 0.9045 | `ml/grading_forecast/price_forecasting/models/v2/naive_persistence_metrics.json` | Evaluated on same 36 V2 test timestamps as RF. | Selected as stronger Phase 3 forecast baseline. |
| PRICE-V2-RF | COMPLETE | price_v2 | chronological train-val-test | RandomForestRegressor | Primary PP2 ML forecast baseline | 400 trees, random_state 42, lag/rolling past-only features | MAE 82.4179, RMSE 88.4452, MAPE 4.1679, R2 -0.4736 | `ml/grading_forecast/price_forecasting/models/v2/` | Underperformed naive persistence on the V2 test period. | Keep as required ML baseline; do not claim superiority. |
| PRICE-V2-IMPROVE-1 | COMPLETE | price_v2 | same as PRICE-V2-RF | Extended-lag RandomForest | Limited forecast improvement | Phase 3 RF plus `lag_4`, `lag_8`, `lag_12` | MAE 78.1641, RMSE 84.8622, MAPE 3.9482, R2 -0.3566 | `ml/grading_forecast/price_forecasting/models/v2_phase4/` | Improved over Phase 3 RF, but still underperformed Naive Persistence. | Record as limited RF improvement; keep Naive Persistence as strongest forecast baseline. |

## Required Metric Fields

Berry grading:

- accuracy
- precision per class
- recall per class
- F1 per class
- macro F1
- weighted F1
- confusion matrix
- inference latency if measured

Price forecasting:

- MAE
- RMSE
- MAPE
- R2
- actual vs predicted plot
- residual plot if available
- feature importance if RandomForest is used

## Model Selection Rules

Berry:

- Do not select a model using validation performance only.
- Use the untouched test split for final PP2 metric reporting.
- Inspect Grade 2 recall and confusion with Grade 3.
- Prefer the model with reliable generalization, not only highest apparent accuracy.

Forecasting:

- The RandomForest model must beat or reasonably justify itself against naive persistence.
- If RandomForest does not beat naive, report that honestly and keep the best method as the PP2 baseline.
- Use MAE/RMSE/MAPE as the main practical metrics; R2 may be unstable in short or low-variance test windows.

## Logging Template

Use this template for each new experiment:

```text
Experiment ID:
Date:
Dataset version:
Split version:
Model/method:
Objective:
Configuration:
Training command:
Evaluation command:
Metrics:
Artifacts:
Observation:
Decision:
Limitations:
```

## Prepared Phase 3 Commands

These commands are prepared for Phase 3 execution. Do not run them until Phase 3 execution is explicitly started.

RandomForest training command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/training/train_forecast_model.py --train-csv data/processed/grading_forecast/price_v2/forecast_train.csv --validation-csv data/processed/grading_forecast/price_v2/forecast_validation.csv --test-csv data/processed/grading_forecast/price_v2/forecast_test.csv --target-csv data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv --models-dir ml/grading_forecast/price_forecasting/models/v2 --dataset-version v2 --artifact-version v2 --seed 42 --n-estimators 400 --min-samples-leaf 1 --n-jobs -1 --require-v2-paths
```

Same-test-timestamp evaluation command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/training/evaluate_forecast_model.py --target-csv data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv --test-csv data/processed/grading_forecast/price_v2/forecast_test.csv --models-dir ml/grading_forecast/price_forecasting/models/v2 --output-dir ml/grading_forecast/price_forecasting/evaluation/_outputs/v2 --split-name test --require-v2-paths
```

Forecast export-manifest command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/training/export_forecast_model.py --models-dir ml/grading_forecast/price_forecasting/models/v2 --require-v2-paths
```

V2 inference command after model creation:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/inference/predict_future_price.py --data-csv data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv --models-dir ml/grading_forecast/price_forecasting/models/v2 --require-v2-paths
```

Dry-run validation result from pre-execution preparation:

- Training dry-run resolves to V2 train/validation/test/target paths and `models/v2`.
- Training feature rows available from V2 train split: 156 from 162 input rows.
- Evaluation dry-run resolves to V2 target/test/model/output paths.
- Evaluation dry-run predicts exactly 36 timestamps, matching the 36-row V2 test split.
- `feature_date_before_prediction_date` is true for planned test predictions.
- No Phase 3 model training, final evaluation metrics, or final plots were generated during preparation.

## Completed Experiment Details

### BERRY-V2-MNV2

Date: 2026-08-27.

Dataset version: `berry_v2`.

Split version: `data/processed/grading_forecast/berry_split_v2_manifest.csv`.

Image/sample counts:

- Train: 117 samples, 467 images.
- Validation: 24 samples, 95 images.
- Test: 27 samples, 109 images.
- Leakage validation: no `grade + sample_id` group crosses train, validation, and test.

Model/method:

- MobileNetV2 transfer learning.
- ImageNet initialization.
- `include_top=False`.
- 224x224 RGB input.
- MobileNetV2 preprocessing inside the model.
- Light augmentation: horizontal flip, rotation 0.06, zoom 0.10, brightness factor 0.12.
- Classification head: global average pooling, dropout, dense softmax with 3 classes.

Configuration:

- Batch size: 16.
- Seed: 42.
- Loss: sparse categorical cross-entropy.
- Optimizer: Adam.
- Stage 1: frozen backbone, maximum 15 epochs, learning rate 0.001, patience 3; 14 epochs completed.
- Stage 2: limited fine-tuning of final MobileNetV2 layers, maximum 5 epochs, learning rate 0.00001, patience 2; 5 epochs completed.
- Best validation-loss checkpoint: Stage 2 epoch 5, validation loss 0.5248714089, validation accuracy 0.7473683953.

Training command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/berry_grading/training/train_berry_classifier.py --train-dir data/processed/grading_forecast/berry_split_v2/train --val-dir data/processed/grading_forecast/berry_split_v2/val --output-dir ml/grading_forecast/berry_grading/models/v2 --model-filename berry_mobilenetv2_v2_best.keras --metadata-version v2 --batch-size 16 --stage1-epochs 15 --stage2-epochs 5 --stage1-lr 1e-3 --stage2-lr 1e-5 --patience 3
```

Evaluation command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/berry_grading/training/evaluate_berry_classifier.py --model ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.keras --models-dir ml/grading_forecast/berry_grading/models/v2 --data-dir data/processed/grading_forecast/berry_split_v2/test --output-dir ml/grading_forecast/berry_grading/evaluation/_outputs/v2 --use-full-data-dir --split-name test
```

Export command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/berry_grading/training/export_berry_model.py --model ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.keras --out ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx --metadata-out ml/grading_forecast/berry_grading/models/v2/onnx_metadata.json
```

Metrics:

- Accuracy: 0.8073.
- Grade 1 precision/recall/F1: 0.9063 / 0.7632 / 0.8286.
- Grade 2 precision/recall/F1: 0.7805 / 0.8889 / 0.8312.
- Grade 3 precision/recall/F1: 0.7500 / 0.7714 / 0.7606.
- Macro precision/recall/F1: 0.8122 / 0.8078 / 0.8068.
- Weighted precision/recall/F1: 0.8145 / 0.8073 / 0.8076.
- Inference timing: average 78.487 ms, p95 107.546 ms, 80 single-image runs.

Artifacts:

- `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.keras`
- `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`
- `ml/grading_forecast/berry_grading/models/v2/class_names.json`
- `ml/grading_forecast/berry_grading/models/v2/training_history.json`
- `ml/grading_forecast/berry_grading/models/v2/berry_model_metadata.json`
- `ml/grading_forecast/berry_grading/models/v2/berry_classifier_metrics.json`
- `ml/grading_forecast/berry_grading/models/v2/onnx_metadata.json`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/confusion_matrix.png`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/training_curves.png`

Observation:

V2 Grade 2 recall improved compared with the historical V1 metric, but V1 and V2 are not directly equivalent experiments because V2 uses the expanded dataset and leakage-safe sample-level split.

Decision:

Use `BERRY-V2-MNV2` as the PP2 berry grading baseline.

Limitations:

- Small dataset: 168 physical sample groups and 671 images.
- Camera-based visual grading only; no chemical or official SLS certification measurements.
- Native Windows TensorFlow used CPU only in the observed training environment.
- Initial write attempts for training/evaluation/export hit permission errors and were rerun with permission escalation using the same commands and methodology.

### FORECAST-V2-RF

Date: 2026-08-27.

Dataset version: `price_v2`.

Target definition: National + Grade 1 + average + farm_gate + weekly.

Split version:

- Full target: `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`.
- Train: `data/processed/grading_forecast/price_v2/forecast_train.csv`.
- Validation: `data/processed/grading_forecast/price_v2/forecast_validation.csv`.
- Test: `data/processed/grading_forecast/price_v2/forecast_test.csv`.

Rows/date ranges:

- Target: 232 rows, 2021-02-22 to 2026-08-18.
- Train: 162 rows, 2021-02-22 to 2025-03-18.
- Validation: 34 rows, 2025-03-25 to 2025-11-25.
- Test: 36 rows, 2025-12-02 to 2026-08-18.

Model/methods:

- Required baseline: Naive Persistence, `prediction(t+1) = observed price(t)`.
- ML baseline: RandomForestRegressor.

RandomForest configuration:

- `n_estimators`: 400.
- `random_state`: 42.
- `n_jobs`: -1.
- `max_depth`: None.
- `min_samples_leaf`: 1.

Feature list:

- `lag_1`
- `lag_2`
- `lag_3`
- `rolling_mean_3`
- `rolling_std_3`
- `rolling_mean_5`
- `rolling_std_5`
- `month`
- `week_of_year`
- `price_change_1w`
- `price_change_pct_1w`

Temporal feature methodology:

- Lag features use previous available observations, not guaranteed previous calendar weeks.
- Rolling features use previous available observations with shifted history.
- Test features use full target context but each feature date is before its prediction date.
- No missing calendar weeks were fabricated or interpolated.
- Grade 2 observations were not used as the forecasting target.

Training command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/training/train_forecast_model.py --train-csv data/processed/grading_forecast/price_v2/forecast_train.csv --validation-csv data/processed/grading_forecast/price_v2/forecast_validation.csv --test-csv data/processed/grading_forecast/price_v2/forecast_test.csv --target-csv data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv --models-dir ml/grading_forecast/price_forecasting/models/v2 --dataset-version v2 --artifact-version v2 --seed 42 --n-estimators 400 --min-samples-leaf 1 --n-jobs -1 --require-v2-paths
```

Evaluation command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/training/evaluate_forecast_model.py --target-csv data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv --test-csv data/processed/grading_forecast/price_v2/forecast_test.csv --models-dir ml/grading_forecast/price_forecasting/models/v2 --output-dir ml/grading_forecast/price_forecasting/evaluation/_outputs/v2 --split-name test --require-v2-paths
```

Export-manifest command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/training/export_forecast_model.py --models-dir ml/grading_forecast/price_forecasting/models/v2 --require-v2-paths
```

Execution durations:

- RandomForest training command duration: 5.6078 seconds.
- Evaluation command duration: 5.2312 seconds.
- Export-manifest command duration: 0.0932 seconds.

Final test metrics:

| Method | MAE | RMSE | MAPE | R2 |
| --- | ---: | ---: | ---: | ---: |
| Naive Persistence | 16.4094 | 22.5208 | 0.8539 | 0.9045 |
| RandomForest | 82.4179 | 88.4452 | 4.1679 | -0.4736 |

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

Observation:

Naive Persistence clearly outperformed RandomForest on the 36-row V2 test period. The RandomForest model had strong training metrics but poor test generalization, suggesting overfitting and/or a test period where simple persistence is stronger.

Decision:

Use Naive Persistence as the stronger Phase 3 forecasting baseline for PP2. Keep RandomForest as the required ML baseline result and report honestly that it did not outperform the naive baseline.

Limitations:

- Primary target is Grade 1 only.
- Grade 2 coverage is sparse and remains out of scope for Phase 3.
- Missing calendar weeks exist, including a historical 316-day gap.
- Lags and rolling windows mean previous available observations, not exact calendar weeks.
- Test period is short: 36 prediction timestamps.
- No hyperparameter search or advanced time-series model was performed.
- Initial write attempts for training/evaluation/export hit permission errors and were rerun with permission escalation using the same commands and methodology.

### BERRY-V2-IMPROVE-1

Date: 2026-08-27.

Dataset version: `berry_v2`.

Split version: `data/processed/grading_forecast/berry_split_v2_manifest.csv`.

Objective:

Test one limited berry grading improvement by changing only dropout from the Phase 2 baseline value of 0.25 to 0.35.

Configuration:

- Model: MobileNetV2 transfer learning.
- ImageNet initialization: true.
- Input: 224x224 RGB.
- Batch size: 16.
- Seed: 42.
- Stage 1 maximum epochs: 15, learning rate 0.001.
- Stage 2 maximum epochs: 5, learning rate 0.00001.
- Fine-tuned MobileNetV2 layers: final 20 layers.
- Selected improvement variable: dropout 0.35.
- Same V2 train/validation/test split as Phase 2.

Training command for reproduction:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/berry_grading/training/train_berry_classifier.py --train-dir data/processed/grading_forecast/berry_split_v2/train --val-dir data/processed/grading_forecast/berry_split_v2/val --output-dir ml/grading_forecast/berry_grading/models/v2_phase4 --model-filename berry_mobilenetv2_v2_phase4_best.keras --metadata-version v2_phase4 --batch-size 16 --stage1-epochs 15 --stage2-epochs 5 --stage1-lr 1e-3 --stage2-lr 1e-5 --patience 3 --dropout 0.35
```

Evaluation command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/berry_grading/training/evaluate_berry_classifier.py --model ml/grading_forecast/berry_grading/models/v2_phase4/berry_mobilenetv2_v2_phase4_best.keras --models-dir ml/grading_forecast/berry_grading/models/v2_phase4 --data-dir data/processed/grading_forecast/berry_split_v2/test --output-dir ml/grading_forecast/berry_grading/evaluation/_outputs/v2_phase4 --use-full-data-dir --split-name test
```

Metrics:

- Accuracy: 0.8073.
- Grade 1 precision/recall/F1: 0.9063 / 0.7632 / 0.8286.
- Grade 2 precision/recall/F1: 0.7805 / 0.8889 / 0.8312.
- Grade 3 precision/recall/F1: 0.7500 / 0.7714 / 0.7606.
- Macro precision/recall/F1: 0.8122 / 0.8078 / 0.8068.
- Weighted precision/recall/F1: 0.8145 / 0.8073 / 0.8076.

Artifacts:

- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_mobilenetv2_v2_phase4_best.keras`
- `ml/grading_forecast/berry_grading/models/v2_phase4/class_names.json`
- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_classifier_metrics.json`
- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_model_metadata.json`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v2_phase4/confusion_matrix.png`

Observation:

The dropout 0.35 model produced the same saved headline test metrics and confusion matrix as the Phase 2 V2 baseline. The Phase 4 model file has a different SHA256 hash from the Phase 2 model, so it is a separate artifact, but it did not produce measurable test-metric improvement.

Decision:

Record the dropout experiment as a valid limited Phase 4 result, but keep `BERRY-V2-MNV2` as the selected PP2 berry grading baseline.

Limitations:

- Only one berry improvement was tested.
- No hyperparameter search was performed.
- `training_history.json` was not present in the Phase 4 berry artifact directory during finalization, so exact completed epoch counts are unavailable from saved artifacts.

### PRICE-V2-IMPROVE-1

Date: 2026-08-27.

Dataset version: `price_v2`.

Target definition: National + Grade 1 + average + farm_gate + weekly.

Objective:

Test one limited forecasting improvement by adding longer historical lag features to the Phase 3 RandomForest baseline.

Configuration:

- Model: RandomForestRegressor.
- `n_estimators`: 400.
- `random_state`: 42.
- `n_jobs`: -1.
- `max_depth`: None.
- `min_samples_leaf`: 1.
- Added features: `lag_4`, `lag_8`, `lag_12`.
- Same 36 V2 test timestamps as Phase 3.

Feature list:

- `lag_1`
- `lag_2`
- `lag_3`
- `lag_4`
- `lag_8`
- `lag_12`
- `rolling_mean_3`
- `rolling_std_3`
- `rolling_mean_5`
- `rolling_std_5`
- `month`
- `week_of_year`
- `price_change_1w`
- `price_change_pct_1w`

Training command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/training/train_forecast_model_phase4.py --train-csv data/processed/grading_forecast/price_v2/forecast_train.csv --validation-csv data/processed/grading_forecast/price_v2/forecast_validation.csv --test-csv data/processed/grading_forecast/price_v2/forecast_test.csv --target-csv data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv --models-dir ml/grading_forecast/price_forecasting/models/v2_phase4 --dataset-version v2 --artifact-version v2_phase4 --seed 42 --n-estimators 400 --min-samples-leaf 1 --n-jobs -1 --require-v2-paths
```

Evaluation command:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/training/evaluate_forecast_model_phase4.py --target-csv data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv --test-csv data/processed/grading_forecast/price_v2/forecast_test.csv --models-dir ml/grading_forecast/price_forecasting/models/v2_phase4 --phase3-models-dir ml/grading_forecast/price_forecasting/models/v2 --output-dir ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4 --split-name test --require-v2-paths
```

Final test metrics:

| Method | MAE | RMSE | MAPE | R2 |
| --- | ---: | ---: | ---: | ---: |
| Naive Persistence | 16.4094 | 22.5208 | 0.8539 | 0.9045 |
| Phase 3 RandomForest | 82.4179 | 88.4452 | 4.1679 | -0.4736 |
| Phase 4 Extended-Lag RandomForest | 78.1641 | 84.8622 | 3.9482 | -0.3566 |

Artifacts:

- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_model.joblib`
- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_features.json`
- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_metrics.json`
- `ml/grading_forecast/price_forecasting/models/v2_phase4/naive_persistence_metrics.json`
- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_model_metadata.json`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/actual_vs_predicted.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/feature_importances.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/residuals.png`

Observation:

The extended-lag RandomForest improved over the Phase 3 RandomForest baseline on MAE, RMSE, MAPE, and R2. However, Naive Persistence remained much stronger on the same 36 test timestamps.

Decision:

Record the extended-lag result as a valid limited RF improvement, but keep Naive Persistence as the strongest PP2 forecasting method for the current V2 test period.

Limitations:

- Only one forecasting improvement was tested.
- Missing calendar weeks remain; lags represent previous available observations.
- Test period contains only 36 prediction timestamps.
- Grade 2 forecasting remains out of scope.

## Phase 0 V3 Research Definition Decision

### V3-PHASE0-RESEARCH-DEFINITION

Date: 2026-10-06.

Phase: 0 — Research-definition lock; documentation decision, not a model experiment.

Dataset version: `berry_v3` source/export review.

Research decision:

- The V3 unit of prediction is the harvested pepper sample/batch represented in a smartphone image, not an individual berry.
- The intended task is YOLO-based sample/batch detection/localization followed by sample/batch-level classification as V3 Grade 1 or V3 Grade 2.
- The system must reject non-pepper/invalid inputs, inadequate-quality images, and insufficient-confidence detections or grades instead of always forcing a grade.
- Confidence and quality thresholds will be selected later using validation data; no Phase 0 thresholds were invented.
- Final V3 evaluation must use physical-sample/group-aware splits and a sealed held-out test set. The current Roboflow image-level split is not accepted as the final research split because 146 of 194 physical sample groups cross split boundaries.
- V1 and V2 remain unchanged historical baselines. V3 will use separate versioned artifacts.

Verified taxonomy mapping:

```text
Original/source Grade 1 + Original/source Grade 2 -> V3 Grade 1
Original/source Grade 3                           -> V3 Grade 2
```

Open decisions:

- The repository does not establish scientific equivalence between this custom two-class collapse and SLS grades. The included SLS standard defines three whole-pepper grades.
- The original folder-label provenance and expert/measurement validation are not recorded.
- The Department of Export Agriculture price data uses Grade 1/2 names, but its definitions are not stored, so compatibility with V3 image classes is unproven.
- V3 contains only positive pepper images with one box each; a later approved negative/invalid-input protocol is required to train/calibrate/evaluate rejection.

Decision record: `docs/research/V3_DECISION_RECORD.md`.

Gate result: `BLOCKED — RESEARCHER DECISION REQUIRED` before Phase 1/model development.

## Phase 1 V3 Audit and Grading Diagnosis

### V3-PHASE1-AUDIT

Date: 2026-10-06.

Phase: 1 - dataset audit and grading diagnosis; no model training.

Dataset version: `berry_v3`.

Physical-sample grouping source:

- `D:/work/Year - 4/pepper/project/datset reorder/`
- This pre-Roboflow source was used only for image-to-physical-sample identity.
- Roboflow V3 remains the source of YOLO bounding-box annotations and V3 class labels.

Source and exact-hash mapping result:

- Source structure: `grade_1` = 112 physical samples/448 images; `grade_2` = 82 physical samples/327 images.
- Total: 194 physical samples and 775 images.
- SHA-256 exact V3-to-source matches: 775/775.
- Unmatched: 0.
- Ambiguous matches: 0.
- Duplicate source-hash groups: 0.
- Class consistency: all 448 source `grade_1` images map to V3 Grade 1 and all 327 source `grade_2` images map to V3 Grade 2.

Group-aware split, seed 42:

- TRAIN: 135 groups, 539 images; V3 Grade 1 = 312 images, V3 Grade 2 = 227 images.
- VALIDATION: 29 groups, 116 images; V3 Grade 1 = 68 images, V3 Grade 2 = 48 images.
- TEST: 30 groups, 120 images; V3 Grade 1 = 68 images, V3 Grade 2 = 52 images.
- Pairwise physical-sample intersections are empty.
- The partition union contains all 194 groups and every V3 image appears exactly once.

Blind-review status:

- A validation-only blind package was prepared with 20 V3 Grade 1 and 20 V3 Grade 2 images, neutral IDs, seed 42, and a separate concealed key.
- Status: complete; all 40 responses were valid and the key was opened only after completion.
- Overall agreement: 32/40 = 80.0%.
- V3 Grade 1 agreement: 18/20 = 90.0%.
- V3 Grade 2 agreement: 14/20 = 70.0%.
- Uncertain: 4/40 = 10.0%, with two from each V3 grade.
- Agreement among 36 non-uncertain responses: 32/36 = 88.9%.
- Confusion matrix, rows = true V3 Grade 1/Grade 2 and columns = researcher Grade 1/Grade 2/Uncertain: `[[18, 0, 2], [4, 14, 2]]`.
- Cohen's kappa across all 40 responses, treating Uncertain as a third response category: 0.636.
- Supplementary accepted-only binary kappa across 36 non-uncertain responses: 0.778.
- All four incorrect decisive responses were V3 Grade 2 labeled Grade 1 and came from two physical samples, with two views from each sample.

Shortcut audit result:

- Risk: **HIGH**.
- All images are 4:3 and mean brightness is similar by class.
- Device/resolution is strongly class-correlated: Galaxy A06 appears in 144/448 V3 Grade 1 images but only 1/327 V3 Grade 2 images; 4080x3060 or 8160x6120 occurs in 144 Grade 1 images but only one Grade 2 image.
- Background contact-sheet inspection found hands, pale paper/surfaces, and grey/metal-like surfaces in both classes; it did not prove an exclusive background rule.

V2 saliency result:

- Existing frozen V2 MobileNetV2 only; no retraining or model change.
- 109 historical test images were screened to select nine deterministic examples: three correct and six incorrect, covering all three historical classes.
- Input-gradient saliency classifications: three PEPPER-FOCUSED, six MIXED, zero BACKGROUND-FOCUSED, zero UNCLEAR.
- Hands and surrounding surfaces contributed visibly in multiple examples. Saliency is diagnostic and does not prove causal reasoning.

Final Phase 1 verdict:

```text
LABEL QUALITY: acceptable
SHORTCUT RISK: high
SPLIT: leakage-free
TASK: feasible
```

Unresolved issues:

- The high camera/resolution shortcut risk must be mitigated and evaluated if the task proceeds.
- Dataset label agreement still does not establish equivalence to official SLS, buyer, or price-data grades.
- The blind review is a small single-researcher diagnostic and not definitive statistical or external validation.
- V3 Grade 2 had lower human agreement than V3 Grade 1 and requires explicit per-class monitoring.

Artifacts:

- `docs/research/V3_PHASE1_AUDIT.md`
- `data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv`
- `data/processed/grading_forecast/berry_v3/v3_group_split_manifest.csv`
- `data/processed/grading_forecast/berry_v3/v3_phase1_audit_summary.json`
- `data/processed/grading_forecast/berry_v3/v3_background_contact_sheet.jpg`
- `data/processed/grading_forecast/berry_v3/blind_review/`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v3_phase1_v2_saliency/`
- `ml/grading_forecast/berry_grading/preprocessing/audit_berry_v3_phase1.py`
- `ml/grading_forecast/berry_grading/evaluation/diagnose_v2_saliency.py`

Gate result: `PHASE 1 COMPLETE`. The task is feasible for a separately authorized Phase 2, subject to the documented shortcut and semantic limitations. No Phase 2 work was started.

## Phase 2 V3 YOLO-Based Sample Detection and Grade Classification

### BERRY-V3-YOLO11N-001

Date: 2026-10-07.

Objective: train and evaluate one lightweight YOLO-based harvested pepper sample/batch detector and two-grade classifier using the leakage-free physical-sample split. This was not per-berry detection or grading.

Dataset and split:

- Dataset version: `berry_v3`; 775 images, 194 physical samples, one sample-level YOLO box per image.
- TRAIN: 135 groups/539 images; V3 Grade 1 = 312, V3 Grade 2 = 227.
- VALIDATION: 29 groups/116 images; V3 Grade 1 = 68, V3 Grade 2 = 48.
- TEST: 30 groups/120 images; V3 Grade 1 = 68, V3 Grade 2 = 52.
- Pairwise sample-ID intersections were empty; all 775 images appeared exactly once.
- The Roboflow split was not used as the experimental split. The original source hierarchy remained grouping/reference metadata only.

Dataset preparation and preservation:

- Generated a manifest-driven Ultralytics configuration and minimum materialized working layer from the canonical Roboflow V3 images/labels.
- Ultralytics was observed repairing JPEG end markers during its first scan. The scan was stopped before epoch training; every affected canonical image was restored by exact source mapping and all 775 canonical SHA-256 values were reverified.
- Final training/evaluation used derived, ignored working copies so framework repairs could not touch canonical data.
- Final post-evaluation canonical audit: 775/775 SHA-256 matches; zero mismatches.

Model and environment:

- Framework: Ultralytics 8.4.174; PyTorch 2.14.1+cu130.
- Model: YOLO11n detection, transfer learning from `yolo11n.pt`.
- Image size 640; batch 4; AdamW; initial LR 0.001; weight decay 0.0005; seed 42; deterministic mode; NVIDIA GeForce RTX 2050 4 GB.
- Maximum 75 epochs; patience 12; early stopped after 57 epochs. Best checkpoint: epoch 45.
- Training wrapper wall time: 4,829.93 seconds (80 minutes 29.93 seconds); Ultralytics training time: 1.295 hours.
- Best checkpoint: `ml/grading_forecast/berry_grading/models/v3_yolo/best.pt`.

Threshold decision:

- Baseline threshold: 0.25.
- Validation-only scan: 0.05-0.90 by 0.01, maximizing macro F1 with rejected valid inputs counted as errors; predeclared tie break = lowest threshold.
- Selected/frozen before test: 0.05.
- Selected 0.05 and baseline 0.25 both produced validation macro F1 0.9562, 100% coverage, and zero rejections. This is not a universal threshold and the positive-only data cannot validate non-pepper rejection.

Validation result:

- Detection: precision 0.9479; recall 0.9682; mAP@0.5 0.9879; mAP@0.5:0.95 0.8617.
- Grade: accuracy 0.9569; balanced accuracy 0.9632; macro F1 0.9562; weighted F1 0.9571.
- Grade 1 precision/recall/F1: 1.0000/0.9265/0.9618.
- Grade 2 precision/recall/F1: 0.9057/1.0000/0.9505.
- Confusion matrix, true rows Grade 1/2 and predicted columns Grade 1/2/REJECT: `[[63, 5, 0], [0, 48, 0]]`.

Single sealed TEST result; no post-test tuning or retraining:

- Primary grade metrics: macro F1 0.9578; Grade 1 F1 0.9624; Grade 2 F1 0.9533; balanced accuracy 0.9610.
- Secondary grade metrics: accuracy 0.9583 (115/120); weighted F1 0.9584; Grade 1 precision/recall 0.9846/0.9412; Grade 2 precision/recall 0.9273/0.9808.
- Confusion matrix, true rows Grade 1/2 and predicted columns Grade 1/2/REJECT: `[[64, 4, 0], [1, 51, 0]]`.
- Detection: precision 0.9402; recall 0.9552; mAP@0.5 0.9791; mAP@0.5:0.95 0.8505.
- Coverage 1.0000; zero rejections among the 120 positive pepper images.

Physical-sample result:

- Majority vote: 30/30 correct; accuracy and macro F1 1.0000.
- Confidence-weighted aggregation: 30/30 correct; accuracy and macro F1 1.0000.
- 26 samples unanimous; four samples had conflicting view predictions, all resolved correctly by aggregation.

Operational result:

- Checkpoint size: 5,461,466 bytes (5.21 MiB); 2,590,230 loaded parameters; approximately 6.4 GFLOPs.
- RTX 2050 reported inference: mean/median 7.12 ms/image at batch 4 and 640 input.
- End-to-end 120-image prediction pass: 44.27 seconds, including high-resolution file decode/I/O and batching.

Camera/resolution diagnostic:

- Shortcut risk remains HIGH/unresolved.
- Galaxy A06/4080x3060 test subset: 24 images, all V3 Grade 1, accuracy 1.0000; not class-comparable because Grade 2 support is zero.
- SM-A127F/4000x3000 test subset: 96 images, 44 Grade 1/52 Grade 2; accuracy 0.9479, macro F1 0.9472.
- All five image errors were in the mixed-class SM-A127F subset. Strong performance within that condition is encouraging, but the confounded Galaxy A06 subset prevents a camera-invariance claim.

Error analysis:

- Five incorrect images came from four physical samples. Four Grade 1 images were predicted Grade 2 and one Grade 2 image was predicted Grade 1.
- Representative boxes covered broad pepper sample regions; corrected representative IoUs were approximately 0.906-0.987.
- Box visualizations are diagnostic localization evidence, not proof of causal grade reasoning.

Conclusion:

- Phase 2 demonstrates strong detection and two-grade V3 classification on unseen physical-sample groups, plus promising multi-view consistency and a lightweight checkpoint.
- It does not demonstrate official SLS/buyer-grade recognition, per-berry grading, non-pepper rejection accuracy, camera-independent reasoning, field robustness, mobile latency, or price correctness.
- Status: `PHASE 2 COMPLETE`.
- Phase 3 readiness: yes for a separately authorized negative/invalid-input rejection and calibration study, with the high camera shortcut risk explicitly retained.

Artifacts:

- `docs/research/V3_PHASE2_YOLO_RESULTS.md`
- `data/processed/grading_forecast/berry_v3/yolo_phase2/`
- `ml/grading_forecast/requirements-yolo.txt`
- `ml/grading_forecast/berry_grading/training/v3_yolo/`
- `ml/grading_forecast/berry_grading/models/v3_yolo/`
- `ml/grading_forecast/berry_grading/evaluation/v3_yolo/`

Gate result: `PHASE 2 COMPLETE`. Stop for researcher review; Phase 3 was not started.

## Phase 3 Non-Pepper Rejection, Image-Quality Gating, and Uncertainty Calibration

### BERRY-V3-YOLO11N-PHASE3-001

Date: 2026-10-07.

Objective: evaluate the frozen Phase 2 YOLO11n checkpoint on external non-pepper inputs and add validation-calibrated quality and uncertainty rejection logic. No training, V3 modification, application integration, or sealed-test reuse was permitted.

Preservation and data discipline:

- Frozen checkpoint: `ml/grading_forecast/berry_grading/models/v3_yolo/best.pt`.
- Checkpoint SHA-256 before/after: `c35cc40515adcb6130a4bc93e8ad3de161dcf46b263a9d7df8286a5b4239a9c4`; unchanged.
- Phase 2 sealed TEST accessed: no.
- Calibration positives: the 116-image V3 VALIDATION partition only.
- External negatives: 80 Wikimedia Commons thumbnails across 10 retrieval strata; deterministic seed-42 split into 40 CALIBRATION and 40 held-out EVALUATION images.
- External manifest: 80 unique hashes, zero V3 hash overlap, and complete source-page/license metadata. Contact-sheet audit confirmed 80/80 were non-pepper.

Frozen-model negative baseline over all 80 images:

- Confidence 0.05: 58/80 rejected (72.5%); 22/80 falsely accepted (27.5%).
- Confidence 0.25: 65/80 rejected (81.25%); 15/80 falsely accepted (18.75%).
- At 0.25, false acceptance was concentrated in leaves/plants (6/8) and other crops (4/8).

Validation-only/calibration-negative decisions:

- Detection confidence: 0.55, selected by minimizing calibration-negative false acceptance while retaining at least 95% of validation pepper images. It retained 116/116 and falsely accepted 6/40 calibration negatives.
- Quality rules: Laplacian variance >= 10; brightness >= 50/255; minimum dimension >= 320; detected-box area ratio >= 0.20.
- Controlled quality diagnostic: 12 source validation images produced 36 derived challenges; the respective gates rejected 12/12 blur, 12/12 dark, and 12/12 low-resolution variants, with 0/116 natural validation quality rejections.
- Uncertainty rules: top grade confidence >= 0.05 and class margin >= 0.30. These are abstention heuristics, not calibrated probabilities.

Final consolidated result:

- Valid validation images: 111/116 accepted (95.69% coverage); 5/116 uncertainty rejections (4.31% false-rejection rate); accepted accuracy 108/111 = 97.30%; accepted macro F1 0.9725.
- Accepted grade confusion matrix, true rows Grade 1/2: `[[61, 3], [0, 47]]`.
- Held-out non-pepper images: 35/40 rejected (87.5%); 5/40 falsely accepted (12.5%). Decisions: 33 `NO_PEPPER`, 2 `POOR_IMAGE`, 3 false Grade 1, 2 false Grade 2.
- Consolidated matrix, rows valid pepper/non-pepper and columns Grade 1/Grade 2/Poor Image/No Pepper/Uncertain: `[[61, 50, 0, 0, 5], [3, 2, 2, 33, 0]]`.

Failure pattern and conclusion:

- All five held-out false accepts were leaves/plants or other crops, with confidence 0.589-0.943. The highest-confidence error was a full-image aerial-crop detection at 0.943.
- Raising the threshold enough to eliminate this pattern would violate the predeclared valid-pepper retention constraint.
- Phase 3 evaluation is complete, but operational non-pepper rejection is not solved. A separately authorized controlled hard-negative/open-set experiment is justified; no retraining was performed in this phase.
- Status: `PHASE 3 COMPLETE - OPERATIONAL REJECTION GATE NOT PASSED`.
- Phase 4 readiness: no; researcher authorization/decision is required before any hard-negative retraining or integration.

Artifacts:

- `docs/research/V3_PHASE3_REJECTION_RESULTS.md`
- `data/external/phase3_rejection/non_pepper/`
- `data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv`
- `data/processed/grading_forecast/berry_v3/phase3_negative_dataset_summary.json`
- `ml/grading_forecast/berry_grading/rejection/phase3/`
- `ml/grading_forecast/berry_grading/quality/phase3/`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/`

Gate result: `PHASE 3 COMPLETE`. Stop for researcher review. Do not begin retraining, Phase 4, backend/mobile integration, or price-forecasting work without separate authorization.

## Phase 4 Price Data Reconstruction and Market-Aware Forecasting Foundation

### PRICE-EAC-RECONSTRUCTED-V1-001

Date: 2026-10-07.

Objective: replace the incomplete Grade-1/absolute-price foundation with a source-reconstructed, grade-aware EAC farm-gate dataset, next-observation return target, and strict chronological evaluation protocol. No backend/mobile integration, deployment, or later phase was authorized.

Source and reconstruction:

- Authoritative source: DEA Sri Lanka Economic Research Unit, Producers' Prices (Farm Gate) of EAC; index `https://exagri.info/mkt/index.html`.
- Retrieval date 2026-10-07; dataset version `eac_reconstructed_v1`.
- 495 dated index links; 493 successfully parsed pepper pages; broken dated links for 2023-04-25 and 2026-06-23 were retained as missing.
- 16,903 canonical pepper observations from 2016-10-04 through 2026-09-29; zero duplicate canonical keys and zero conflicting duplicates.
- National average series: Grade 1 = 493 observations; Grade 2 = 358; both observed = 358 dates; Grade 2 missing on 135 dates relative to the union.
- No Grade 2 discount, interpolation, resampling, forward fill, or invented observation was used. Raw observations retain exact dated-page provenance.

Existing-data correction:

- Old local range was 2021-02-22 through 2026-08-18 despite its 2016–2026 filename; National averages were Grade 1 = 232 and Grade 2 = 161.
- Five later source dates per grade were isolated: 2026-08-25 through 2026-09-29.
- Historical V2 absolute-price Random Forest and runtime persistence/Grade 2 adjustment artifacts were preserved unchanged.

Target and features:

- Primary target: next-observation percentage return; derived price = dated reference price × (1 + predicted return).
- Horizon: next actual EAC observation; irregular intervals retained.
- Direction: source-exact UP/DOWN/FLAT; predicted FLAT only after equality at the published 0.01 LKR resolution.
- Features: reference price, two price lags, current/prior return, backward three-observation mean and return volatility, and days since prior observation; shared models also used a grade indicator.

Temporal protocol:

- Expanding walk-forward evaluation; a historical row entered training only once its next-observation outcome was known.
- TRAIN targets: 2016-10-11 to 2023-09-19, Grade 1/2 rows 340/213.
- VALIDATION targets: 2023-09-26 to 2025-02-25, rows 73/66.
- FINAL TEST targets: 2025-03-04 to 2026-08-18, rows 74/73.
- EXTERNAL NEWEST targets: 2026-08-25 to 2026-09-29, rows 5/5; excluded from model selection.

Baselines and models actually evaluated:

- Baselines: zero-return persistence, last observed return, expanding grade-specific mean return.
- Models: separate and shared Ridge (`alpha=1.0`); separate and shared Random Forest (100 trees, max depth 5, minimum leaf size 5). Shared variants used a grade indicator.
- Selection score: validation macro-average per-grade return RMSE. Separate Ridge was the best ML candidate at 0.04434, but persistence was better at 0.04319. No tested ML candidate established validation superiority.

Frozen final temporal test, separate Ridge versus persistence:

- Ridge return MAE/RMSE/R²: 0.01989/0.02954/0.1398; persistence: 0.01858/0.03187/-0.0010.
- Ridge directional accuracy: 46.26% overall and 51.52% for non-flat UP/DOWN observations; persistence: 10.20%/0.00% because it always predicts FLAT.
- Ridge derived-price MAE/RMSE: 37.29/54.55 LKR/kg; persistence: 34.62/58.12 LKR/kg.
- Return MAPE was omitted because returns contain and approach zero.
- Result is mixed: Ridge improved RMSE/direction but worsened MAE. It is not established as a superior final forecaster.

Newest temporal reality check:

- Ten observations (five per grade) were evaluated after all selection decisions.
- Ridge return MAE/RMSE: 0.02714/0.03557; direction accuracy 30%; derived-price MAE/RMSE 50.19/64.68 LKR/kg.
- Persistence return MAE/RMSE: 0.02305/0.03259; derived-price MAE/RMSE 42.33/58.22 LKR/kg.
- The best Phase 4 ML candidate did not beat persistence on the genuinely newer observations.

Integrity and conclusion:

- Focused integrity validation passed: source/canonical identity, no duplicates/fabrication, chronological targets, backward lags, no random split, and no test/external selection contamination.
- The reconstructed data foundation and evaluation protocol are ready for a separately authorized Phase 5 experiment, but Phase 4 does not support deployment of the Ridge candidate or a claim of ML superiority.
- Latest verified source, Grade 1, and Grade 2 dates are all 2026-09-29. This is a dated EAC reference, not a real-time buyer quote.
- Status: `PHASE 4 COMPLETE — DATA FOUNDATION READY; FORECASTING IMPROVEMENT NOT YET DEMONSTRATED`.

Artifacts:

- `docs/research/PHASE4_PRICE_DATA_AUDIT.md`
- `docs/research/PHASE4_PRICE_FOUNDATION_RESULTS.md`
- `data/raw/market_prices/eac_phase4/`
- `data/processed/grading_forecast/price/eac_reconstructed_v1/`
- `ml/grading_forecast/price_forecasting/phase4/`

Gate result: `PHASE 4 COMPLETE`. Stop for researcher review. Phase 5, application integration, and deployment were not started.

## Phase 5 Price Movement Forecasting Research

### PRICE-EAC-PHASE5-001

Date: 2026-10-07.

Objective: determine whether short-term Grade 1 and Grade 2 movement can be forecast more usefully than persistence using the frozen `eac_reconstructed_v1` foundation. No Phase 4 overwrite, decision engine, backend/mobile integration, berry-grading change, or Phase 6 work was permitted.

Dataset and preservation:

- Canonical input: 493 National Grade 1 and 358 National Grade 2 averages, 2016-10-04 through 2026-09-29.
- Phase 4 canonical SHA-256 remained `ea800ea576817f07ad54d50317dbd68254fc5dc824447380e58688b6b711c0f6`.
- No interpolation, resampling, forward filling, or fabricated Grade 2 observation.
- Phase 4 reports/data, V2 artifacts, all 775 V3 images/annotations, berry pipeline, backend, and mobile remained unchanged.

Targets and horizon:

- Compared next-observation simple return, log return, and absolute price delta.
- Validation selected next-observation log return.
- Fixed calendar horizons were not evaluated because the source is irregular and no resampling/imputation was authorized.

Features and ablation:

- Tested recent return lags; technical/rolling features; calendar features; and a common-cohort grade-relationship experiment.
- Selected feature group: four completed-return lags plus days since previous observation.
- Macro-grade validation RMSE: return lags 0.04188; technical 0.04633; technical/calendar 0.04645.
- On the same 131-row relationship-eligible cohort, return lags scored 0.04182 versus 0.06090 after adding spread/ratio/other-grade return.

Methods:

- Baselines: persistence, last return, expanding mean return, and explicitly defined historical price drift.
- Statistical: SES alpha 0.2/0.5; ARIMA(1,0,0) and ARIMA(2,0,0) as conditional OLS autoregressions.
- ML: Ridge, Random Forest, and Gradient Boosting; separate and shared-grade formulations.
- Selected ML candidate: separate Grade 1/Grade 2 Ridge, log-return target, smallest return-lag feature group.
- Minimum history 50; seed 42; expanding walk-forward; per-window scaler fitting; no random split.

Final temporal test, 147 forecasts through 2026-08-18:

- Selected Ridge return MAE/RMSE/R²: 0.01820/0.02985/0.1215.
- Selected Ridge direction accuracy: 52.38%; non-flat accuracy: 58.33%.
- Selected Ridge price MAE/RMSE/MAPE: 34.00 LKR/kg / 54.73 LKR/kg / 1.815%.
- Persistence return MAE/RMSE: 0.01858/0.03187; price MAE/RMSE: 34.62/58.12 LKR/kg; direction accuracy 10.20% under deterministic FLAT prediction.
- Grade 1 price MAE/RMSE: 15.19/20.84 LKR/kg; Grade 2: 53.06/74.77 LKR/kg.

External later-observation reality check, ten forecasts:

- Selected Ridge return MAE/RMSE: 0.02330/0.03259; price MAE/RMSE: 42.83/58.54 LKR/kg; direction accuracy 70%.
- Persistence return MAE/RMSE: 0.02305/0.03259; price MAE/RMSE: 42.33/58.22 LKR/kg; direction accuracy 10%.
- Ridge correctly predicted four of five later Grade 1 directions, improving the Phase 4 directional failure, but remained fractionally worse than persistence on external price/return error.

Prediction intervals:

- Grade-specific 90th-percentile absolute validation-return residual intervals were frozen before final evaluation.
- Final coverage 96.60%, mean width 275.18 LKR/kg.
- Grade 2 mean width was 456.56 LKR/kg, too broad for strong production confidence claims.

Decision and limitations:

- Persistence comparison: `MIXED` — selected Ridge won validation and final test but not the small external check.
- Main conclusion: recent return lags contain limited predictive information, especially for direction, but consistent ML superiority is not established.
- Grade 2 magnitude error, exact-FLAT failure, absent exogenous variables, irregular frequency, and the ten-observation external sample remain important limitations.
- Phase 6 readiness: `READY WITH LIMITATIONS` for controlled combination research only, not production deployment.
- Complete prediction CSV reproduced byte-for-byte under deterministic configuration.

Artifacts:

- `docs/research/PHASE5_PRICE_FORECASTING_RESULTS.md`
- `ml/grading_forecast/price_forecasting/phase5/phase5_config.yaml`
- `ml/grading_forecast/price_forecasting/phase5/data/phase5_modeling_dataset.csv`
- `ml/grading_forecast/price_forecasting/phase5/scripts/`
- `ml/grading_forecast/price_forecasting/phase5/models/selected_model_spec.json`
- `ml/grading_forecast/price_forecasting/phase5/outputs/`

Gate result: `PHASE 5 COMPLETE — MIXED EVIDENCE BEYOND PERSISTENCE`. Stop for researcher review. Phase 6 was not started.


## Phase 3 Follow-up — Controlled Hard-Negative Training

### BERRY-V3-YOLO11N-PHASE3-FOLLOWUP-001

Date: 2026-10-07.

- Objective: reduce vegetation/crop false acceptance without unacceptable genuine-pepper or G1/G2 regression.
- Hypothesis: controlled empty-label hard negatives improve the operational rejection gate.
- Dataset: licensed/provenanced Wikimedia negatives, SHA-256 deduplicated, creator-group-aware 60/20/20 split; frozen V3 TRAIN/VALIDATION/TEST preserved.
- Model: frozen Phase 2 YOLO11n checkpoint plus one-shot hard-negative fine-tuning; architecture unchanged.
- Training configuration: 640 px, batch 4, AdamW, LR 0.0001, seed 42, deterministic, maximum 30 epochs/patience 8; early stopped after epoch 27 with epoch 19 selected.
- Threshold rule: validation-only grid; require at least 95% valid coverage, maximize negative rejection, then accepted macro F1, then coverage, then lowest threshold. Selected 0.05.
- Validation: valid coverage 98.28%; negative rejection 100.00%.
- Final new holdout: 49/49 rejected (100.00%); 0 false accepts.
- Phase 2 TEST regression: accuracy 0.9583; macro F1 0.9643; G1/G2 F1 0.9781/0.9505; 2 rejections.
- Decision: `COMPLETE — OPERATIONAL GATE IMPROVED`; hypothesis `SUPPORTED`.
- Limitations: internet-domain negatives, finite unseen holdout, unresolved field/camera shift, no confidence calibration, exact-hash but not semantic deduplication.
- Next phase: stop for researcher review; do not proceed to Phase 6 automatically.

## Phase 6 — Final Freeze and Prospective Field/Domain-Shift Readiness

### BERRY-V3-PHASE6-FREEZE-AND-FIELD-READINESS-001

Date: 2026-10-07.

Research question:

> How well does the frozen berry grading and rejection pipeline generalize to genuinely new, field-like images captured under different acquisition conditions, and what failure modes remain before prospective deployment evaluation?

Frozen artifacts:

- Phase 2 model: `ml/grading_forecast/berry_grading/models/v3_yolo/best.pt`, SHA-256 `c35cc40515adcb6130a4bc93e8ad3de161dcf46b263a9d7df8286a5b4239a9c4`.
- Phase 3 follow-up model: `ml/grading_forecast/berry_grading/models/v3_phase3_followup/best.pt`, SHA-256 `e825278e0cf8eaff64cd05a2941cf96794e573027823a0ccd308bbc3f1a418ca`.
- Frozen follow-up decision configuration retained without threshold changes.
- Phase 4 canonical data and Phase 5 method/results retained without retraining, feature changes, or retrospective tuning.

Freeze and integrity:

- Phase 6 validator: 29 PASS, 0 FAIL, 1 UNAVAILABLE.
- All 775 V3 images matched Phase 1 SHA-256 values.
- All 775 annotations matched recorded class and box values.
- Phase 1 split remained TRAIN 539 / VALIDATION 116 / TEST 120 across 194 non-leaking physical-sample groups.
- Original Phase 3 negatives remained 40 calibration / 40 evaluation with 80/80 file-hash matches.
- Follow-up negatives remained 152 train / 49 validation / 49 final, 250/250 file-hash matches, 250 unique hashes, and 172 non-leaking source groups.
- Phase 4 canonical price data remained 16,903 rows through 2026-09-29 and matched its protected hash.
- Phase 5 specification, metrics, predictions, and ten-row external comparison matched their Phase 6 freeze hashes.
- Phase 2 and follow-up model files are separate and non-identical.

Historical reuse clarification:

- The original Phase 2 test was frozen as historical baseline evidence, then intentionally re-evaluated under the frozen Phase 3 follow-up pipeline for regression analysis. Its original Phase 2 metrics remain preserved.
- The original Phase 3 evaluation subset was intentionally reused for controlled frozen-model comparison. Its original 35/40 result remains preserved.

Blind-review correction:

- The response CSV and concealed key confirm 32/40 = 80.0% overall, Grade 1 18/20 = 90.0%, Grade 2 14/20 = 70.0%, and 4/40 uncertain.
- Agreement among decisive responses is 32/36 = 88.9%; kappa is 0.636 including `Uncertain` and supplementary binary kappa is 0.778 excluding uncertain responses.
- `V3_PHASE1_AUDIT.md` and this experiment log already held the correct result. The later progress report's 85%/95%/75% summary was corrected; underlying evidence and the historical Phase 1 report were not changed.

Prospective dataset:

- No clearly identifiable new field/prospective dataset exists in the repository.
- Existing V3 images and Phase 3 internet negatives were not relabelled as field evidence.
- Field image, physical-sample, device, label, and domain-shift counts are unavailable.
- No model inference was run for Phase 6.

Prepared methodology and artifacts:

- Multi-device field collection and independent-label protocol.
- Physical-sample-aware calibration/final partition policy.
- Field manifest schema and template.
- Fail-closed frozen-model evaluation script.
- Machine-readable blocked metrics with unavailable values represented as `null`.
- Freeze/integrity validator and result.
- Phase 6 readiness and results reports.

Price temporal continuation:

- No verified official EAC observations after the frozen 2026-09-29 cutoff exist in the repository.
- Result: `NO NEW TEMPORAL PRICE EVALUATION AVAILABLE`.

Limitations:

- Field generalization, device stability, lighting/background sensitivity, field rejection, physical-sample grading, and uncertainty behavior remain unknown.
- Exact-hash controls do not establish semantic independence for a future dataset.
- Existing model scores remain uncalibrated.
- Phase 5 retains limited/mixed evidence beyond persistence and substantial Grade 2 uncertainty.

Decision:

`COMPLETE — PREPARATION DONE, FIELD DATA BLOCKED`

All Phases 0-5 and the Phase 3 follow-up are frozen. A future prospective evaluation is justified only after protocol-compliant independent field data is collected and sealed. Any model or threshold improvement after observing that final set must become a separately authorized Phase 7 experiment.

Artifacts:

- `docs/research/PHASE6_FREEZE_AND_READINESS.md`
- `docs/research/PHASE6_FIELD_DATA_PROTOCOL.md`
- `docs/research/PHASE6_FIELD_DOMAIN_VALIDATION_RESULTS.md`
- `ml/grading_forecast/berry_grading/evaluation/phase6/phase6_field_manifest_template.csv`
- `ml/grading_forecast/berry_grading/evaluation/phase6/evaluate_phase6_field.py`
- `ml/grading_forecast/berry_grading/evaluation/phase6/validate_phase6_integrity.py`
- `ml/grading_forecast/berry_grading/evaluation/phase6/phase6_metrics.json`
- `ml/grading_forecast/berry_grading/evaluation/phase6/phase6_integrity.json`

## Phase 6 — Grade + Price Decision Engine

### BERRY-V3-PHASE6-GRADE-PRICE-DECISION-001

Date: 2026-10-07.

Research question:

> Can the frozen V3 grading/rejection pipeline and frozen Phase 5 grade-specific price forecasts be combined into a deterministic, traceable decision-support engine without retraining, leakage, fabricated measurements, or hidden scoring?

Frozen inputs:

- Phase 2 grading model SHA-256: `c35cc40515adcb6130a4bc93e8ad3de161dcf46b263a9d7df8286a5b4239a9c4`.
- Phase 3 follow-up grading model SHA-256: `e825278e0cf8eaff64cd05a2941cf96794e573027823a0ccd308bbc3f1a418ca`.
- Frozen follow-up decision configuration SHA-256: `39ca99a7e0049fb620a141cde80d539700945b2f812cc6cf7b15f289f8e158b8`.
- Phase 4 canonical price dataset SHA-256: `ea800ea576817f07ad54d50317dbd68254fc5dc824447380e58688b6b711c0f6`.
- Phase 5 configuration, selected-model specification, metrics, walk-forward predictions, and external predictions were hash-pinned in the Phase 6 configuration.
- No grading or price model was retrained or refit.

Engine design:

- The grading gate runs first. `NO_PEPPER` and `POOR_IMAGE` terminate with `REJECT`; `UNCERTAIN_GRADE` and conflicting physical-sample views terminate without a market outlook.
- Accepted `V3 Grade 1` routes only to the `Grade 1` market series; accepted `V3 Grade 2` routes only to `Grade 2`. A mismatch fails closed.
- Price direction uses the Phase 5 rule exactly: compare forecast and reference prices after rounding both to LKR 0.01; classify as `UP`, `DOWN`, or exact `FLAT`.
- A forecast interval crossing the current reference price is classified `HIGH_UNCERTAINTY`. A documented Ridge advantage with a non-crossing interval gives `RELATIVE_SUPPORT`; other visible directions remain `LIMITED_SIGNAL`.
- The output preserves grading evidence, market evidence, routing, rationale, source identifiers, and configuration provenance. It does not use a composite score or fixed price discount.

Scenario construction:

- 13 empirical compositional scenarios: ten frozen Phase 5 external predictions paired deterministically with same-grade recorded grading decisions, plus recorded `NO_PEPPER`, `POOR_IMAGE`, and `UNCERTAIN_GRADE` cases.
- 15 explicitly synthetic logic-only scenarios cover the mandatory branches, including both grades and directions, exact flat, conflicting views, missing inputs, interval uncertainty, persistence/Ridge comparisons, and wrong-series routing.
- Synthetic branch cases are labelled `SYNTHETIC_LOGIC_TEST_NOT_EMPIRICAL` and are not counted as observed performance.

Results:

- 28/28 scenario expectations passed.
- Routing checks passed for Grade 1 (12/12), Grade 2 (7/7), and rejection/uncertainty blocking (7/7); deliberate grade/price mismatch failed closed as required.
- All 28 outputs contained complete explainability traces.
- Empirical market-outlook coverage was 10/13 (76.92%); two scenarios rejected and one remained grade-uncertain.
- All ten accepted empirical compositions were `HIGH_UNCERTAINTY_OUTLOOK` because the frozen empirical forecast interval crossed the current reference price. This is a conservative consequence of Phase 5 uncertainty, not an engine failure.
- Deterministic repeated evaluation reproduced identical scenario and trace artifacts.
- Unit tests: 15 passed, 0 failed. Final integrity validation is recorded in `phase6_integrity.json`.

Limitations and interpretation:

- This is a deterministic integration experiment, not a newly trained predictive model; conventional accuracy is therefore not the primary metric.
- The empirical scenarios are compositional rather than contemporaneously observed grade-plus-sale outcomes. They test controlled compatibility and traceability, not end-to-end field utility or causal pricing benefit.
- Phase 5 exposes frozen prediction artifacts rather than one portable serialized forecasting checkpoint; the engine consumes those recorded outputs and never refits the model.
- The ten-row external price sample is small, Grade 2 evidence remains weak, intervals are wide, and no exogenous market variables are available.
- Grading confidence remains uncalibrated, field/domain-shift behavior remains unknown, and no production, backend, mobile, or deployment integration was attempted.

Decision:

`PHASE 6 COMPLETE WITH LIMITATIONS`

The rule engine is reproducible, traceable, scientifically conservative, and ready to inform a separately authorized Phase 7 decision-support design. Phase 7 was not started. The later repository work labelled Phase 6 field/domain-shift readiness remains a separate protocol-preparation record; it did not supply field evidence to this experiment and field validation remains unexecuted.

Artifacts:

- `docs/research/PHASE6_GRADE_PRICE_DECISION_ENGINE_RESULTS.md`
- `ml/grading_forecast/decision_support/phase6/phase6_config.yaml`
- `ml/grading_forecast/decision_support/phase6/decision_engine.py`
- `ml/grading_forecast/decision_support/phase6/phase6_decision_scenarios.csv`
- `ml/grading_forecast/decision_support/phase6/phase6_decision_trace.csv`
- `ml/grading_forecast/decision_support/phase6/phase6_metrics.json`
- `ml/grading_forecast/decision_support/phase6/phase6_integrity.json`

## Phase 7 — ONNX/TFLite + Backend/Mobile Integration

### PHASE7-ONNX-BACKEND-MOBILE-001

Date: 2026-10-07.

- Objective: convert the frozen V3 grading/rejection model and Phase 6 rule layer into an executable backend/mobile research path without retraining or changing research decisions.
- Frozen inputs: Phase 3 follow-up `.pt` and decision thresholds, Phase 4 canonical data, Phase 5 external predictions/model specification, and the Phase 6 configuration and decision modules were hash-pinned.
- Conversion: exported a fixed `[1,3,640,640]` YOLO11n ONNX opset-20 graph with embedded NMS and `[1,300,6]` output. Normalized export metadata made two exports byte-identical. ONNX SHA-256: `f8bb36b3ce9c354fd0707f555dbff88bc4f24606b4b93be99a74b03e6db54d38`.
- Equivalence: five fixed Grade 1, Grade 2, non-pepper, poor-quality, and uncertain cases passed 5/5 at predeclared tolerances. Decision and rejection agreement were 5/5; maximum confidence difference was `1.78813934326172e-07` and maximum box difference was `0.000823974609375` original-image pixel.
- Runtime: backend ONNX Runtime was selected. V3 TFLite was not produced or claimed; the older bundled MobileNet TFLite model is not the frozen V3 detector. Direct ONNX Runtime Mobile was not selected because the existing API architecture can preserve one verified implementation of preprocessing, decisions, pricing, and trace logic.
- Price service: selected the latest approved frozen Phase 5 forecast record for the exact grade. This is not live forecasting and does not pretend a serialized Phase 5 checkpoint exists.
- Integration: `POST /api/v1/grading-forecast/analyze` now returns Phase 6-compatible `grading`, `market`, `decision_support`, and `trace` structures. Legacy standalone grading/forecast/recommendation paths are retired to prevent older three-grade, discounted-price, and trading-style behavior.
- Mobile: Flutter consumes the backend schema and exposes rejection, uncertainty, accepted outlook, source, interval, persistence comparison, limitations, and trace states. Static analysis passed with no issues and 2/2 focused parser tests passed.
- Backend tests: 8/8 focused tests passed, including a real Grade 1 multipart API path and explicit missing-price/missing-forecast responses.
- End-to-end controlled set: Grade 1 and Grade 2 routed correctly; non-pepper, poor-quality, and uncertain inputs were blocked from pricing; deterministic repeat passed.
- Integrity: 22/22 checks passed. Frozen research artifacts remained unchanged.
- Mobile runtime boundary: Android debug build entered Gradle but did not complete within the bounded window and was stopped. No emulator or physical-device execution is claimed.
- Limitations: no field/domain-shift evidence, uncalibrated grading scores, project-specific V3 taxonomy, mixed Phase 5 signal, weaker Grade 2 price performance, wide intervals, frozen rather than live forecasts, and no independent end-to-end field or user-usefulness evaluation.
- Decision: `COMPLETE WITH LIMITATIONS`. This phase establishes conversion and integration behavior, not new predictive accuracy or production readiness.
- Next phase: Phase 8 is ready with limitations for separately authorized prospective field validation. It was not started.

### PHASE7-MOBILE-PREPROCESSING-CORRECTION-001

Date: 2026-10-08.

- Trigger: the first researcher-operated emulator run passed Grade 1, Grade 2, and non-pepper behavior but failed the controlled poor-image and uncertain-grade outcomes (3/5 overall).
- Diagnosis: `BerryCaptureScreen` requested `imageQuality: 75`, `maxWidth: 1280`, and `maxHeight: 1280`. The resulting resize/recompression changed the image evaluated by the frozen blur and class-margin gates. The poor-image case became `NO_PEPPER` with quality passed; the uncertain case became accepted Grade 2 and proceeded to pricing.
- Correction: removed application-requested resizing and recompression from the Phase 7 image picker. No grading model, ONNX artifact, backend threshold, price evidence, or Phase 6 decision rule changed.
- Acceptance status: pending a complete researcher-operated rerun of Grade 1, Grade 2, non-pepper, poor-image, and uncertain cases. `UNCERTAIN_GRADE` must stop before pricing and is not equivalent to `HIGH_UNCERTAINTY_OUTLOOK`.
- Gate: Phase 8 must not start until the corrected mobile path passes all five controlled cases and the result is recorded.

### PHASE7-MOBILE-CORRECTED-VERIFICATION-001

Date: 2026-10-08.

- Method: researcher-operated Android emulator rerun after rebuilding the Flutter client with application-requested picker resize/recompression removed. The same five controlled files were selected from emulator storage.
- Grade 1: `GRADE_1`, V3 Grade 1, quality passed, score `0.9238`; Grade 1 frozen EAC evidence only; final category `HIGH_UNCERTAINTY_OUTLOOK`.
- Grade 2: `GRADE_2`, V3 Grade 2, quality passed, score `0.9046`; Grade 2 frozen EAC evidence only; final category `HIGH_UNCERTAINTY_OUTLOOK`.
- Non-pepper: `NO_PEPPER`, quality passed, score `0.0000`, reason `no_detection_above_threshold`; `REJECT` with no market output.
- Poor image: `POOR_IMAGE`, quality failed, score `0.0000`, reason `blur_variance_below_minimum`; `REJECT` with no market output.
- Uncertain: `UNCERTAIN_GRADE`, quality passed, score `0.7011`, reason `grade_margin_below_minimum`; no market output.
- Result: 5/5 controlled emulator cases matched the frozen decision-level expectations. `UNCERTAIN_GRADE` correctly stopped before pricing; it was not conflated with `HIGH_UNCERTAINTY_OUTLOOK`.
- Decision: Phase 7 mobile acceptance gate closed. Overall Phase 7 status is `COMPLETE WITH LIMITATIONS`; this adds deployment/integration evidence, not new predictive accuracy or field robustness.
- Next phase: Phase 8 is ready with limitations for separately authorized prospective field/domain-shift validation. It was not started.

### PHASE7-RAILWAY-TEXT-INTEGRITY-CORRECTION-001

Date: 2026-10-08.

- Trigger: the Railway-hosted API returned HTTP 200 for rejection cases but HTTP 500 for accepted berry cases when price routing began.
- Diagnosis: the frozen Phase 5 forecast CSV raw SHA-256 was recorded from a Windows CRLF checkout. Railway's Linux checkout materialized the same tracked CSV with LF endings, producing a different byte hash while preserving the CSV content.
- Correction: retained the original raw hash and added an explicit LF-normalized canonical text hash. Runtime validation accepts either the exact original bytes or the exact canonical text and continues to fail closed for any content change. No forecast value, model, threshold, route, or Phase 6 decision rule changed.
- Readiness hardening: application startup and `/ready` now validate both the ONNX runtime and the frozen forecast source, preventing a deployment that can reject images but cannot complete accepted-grade pricing from reporting ready.
- Verification: focused cross-platform integrity, startup, API, and real Grade 1 tests passed locally. Hosted Grade 1/2 verification is pending redeployment.
