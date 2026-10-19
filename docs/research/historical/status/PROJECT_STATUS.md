# Project Status: Berry Grading and Export Price Forecasting

Last updated: 2026-08-31

This document is the current source of truth for the PP2 recovery work for the individual component: Berry Grading and Export Price Forecasting.

## Current Phase

Current phase: Phase 13 Offline Mobile TFLite Fallback and grade-aware predicted market price display are implemented and awaiting Flutter build/device validation. Manual cross-component integration remains pending.

Phase 0, Repository and Research Audit, is complete.

Phase 1, Dataset V2 Preparation and Audit, is complete. Raw datasets and V1 artifacts were preserved. No model training was performed during Phase 1.

Phase 2, Berry Grading V2 Baseline, is complete. The V2 MobileNetV2 model was trained on the sample-level V2 train/validation split, evaluated once on the untouched V2 test split, and exported to ONNX under V2-specific artifact paths.

Phase 3, Price Forecasting V2 Baseline, is complete. Naive Persistence and RandomForest were evaluated on the same 36 chronological V2 test timestamps. Naive Persistence outperformed RandomForest on the final test period.

Phase 4, Limited Model Improvement, is complete. The berry dropout experiment and forecasting extended-lag experiment were completed on the same V2 splits.

Phase 5, Integration Validation, is complete with runtime limitations. The backend API demo path is known and recorded.

Phase 6, PP2 Evidence and Documentation, is complete. Final PP2 result tables, speaking points, limitations, and evidence references are recorded.

Phase 7, Existing Implementation Audit, is complete. The current backend/mobile runtime behavior, model paths, fallback behavior, recommendation logic, Firebase/storage behavior, Flutter API contract, and Phase 8+ pending work were documented. No application code was changed during Phase 7.

Phase 8, Berry V2 Runtime Integration, is complete. The berry grading backend service now loads `BERRY-V2-MNV2` from `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`. The existing API contract was preserved. Forecasting, recommendation rules, Firebase, and Flutter were not changed during Phase 8.

Phase 9, Forecast Runtime Integration / Runtime Forecasting-Method Decision, is complete. The backend price forecast service now uses the V2 National Grade 1 average weekly target and the validated `naive_persistence` method instead of `demo_baseline` for the real application forecasting path. Berry grading, recommendation rules, Firebase, Flutter, datasets, training, evaluation, and model artifacts were not changed during Phase 9.

Phase 10, Recommendation & Decision Logic, is complete. The existing recommendation rules were validated with the real Phase 8 berry runtime output and Phase 9 forecast runtime output. No recommendation business rules or application code were changed.

Phase 11, Backend Reliability & Error Handling, is complete. The grading-forecast API now validates image uploads, fails explicitly when the selected V2 grading model is unavailable, preserves the `forecast_unavailable` behavior for bad forecast data, and returns safe HTTP errors for unexpected grading or recommendation failures.

Phase 11 corrective runtime validation on 2026-08-30 fixed a Flutter upload compatibility defect: the backend no longer rejects valid JPEG/PNG/WEBP uploads solely because the multipart MIME value is missing or `application/octet-stream`. Uploaded bytes are validated with Pillow, the 10 MB limit remains enforced, and invalid/corrupt/oversized uploads still fail safely.

Phase 12, Firebase Persistence Implementation, is complete. Firebase persistence is implemented for application-level result history when credentials are configured. Live Firebase validation was not performed because credentials are not configured. Existing fail-safe behavior was preserved: valid analysis still returns grading, forecast, and recommendation when Firebase is unavailable or save fails, with `saved_to_firebase: false`.

Phase 12.5, Runtime Model & Forecast Diagnostic Validation, is complete. Direct ONNX inference and backend service inference agreed on a 9-image V2 test diagnostic sample, but a training-vs-runtime preprocessing mismatch was confirmed for later review: training used direct 224x224 resize, while backend runtime uses RGB letterbox to 224x224. Forecast diagnostics confirmed the current runtime uses a single National Grade 1 average weekly `naive_persistence` series, so identical forecasts across berry grades are expected under the current design.

Phase 13, Offline Mobile TFLite Fallback, is implemented and awaiting Flutter validation. The existing selected V2 Keras model was converted to a TensorFlow Lite artifact for on-device berry grading. Flutter now routes grading-forecast analysis through an analysis service that defaults to offline mode and can still use the backend API when built with `--dart-define=PEPPER_ANALYSIS_MODE=api`. No model retraining, dataset modification, or new evaluation metrics were produced during this phase.

Phase 13 price-display correction is implemented. The price page no longer allows manual grade selection and no longer shows separate current/predicted prices. It shows one `Predicted market price` for the model-predicted grade from the uploaded image. Grade 1 uses the National Grade 1 average weekly naive-persistence value. Grade 2 uses a documented gap adjustment from observed National average Grade 1 vs Grade 2 rows. The latest overlapping date, 2026-08-18, had Grade 1 = 1886.14 LKR/kg and Grade 2 = 1800.00 LKR/kg, so the app uses a rounded 100 LKR/kg Grade 2 discount. Grade 3 price is reported as unavailable because no reliable Grade 3 historical price series exists.

## Project Scope

Full research project: Multimodal AI-Based Pest, Disease Detection and Export Price Prediction System for Black Pepper.

Individual component: Berry Grading and Export Price Forecasting.

Component responsibilities:

- Classify harvested black pepper berry batches into Grade 1, Grade 2, and Grade 3 using smartphone images.
- Forecast short-term black pepper price trends from historical market data.
- Combine grading and forecasting outputs into sell, wait, or process recommendations.
- Provide outputs through the shared FastAPI backend and Flutter mobile application.
- Store results in Firebase when credentials are configured.

Non-responsibilities:

- Pest detection.
- Leaf disease detection and severity scoring.
- Pepper berry disease detection, lesion segmentation, or remediation.
- Official SLS certification.

## Official Requirement Summary

The proposal and TAF require:

- Berry image dataset collection and preprocessing.
- Historical market price dataset collection and preprocessing.
- Visual quality feature extraction from berry images.
- Machine learning model for berry grading.
- Time-series or machine learning model for short-term price forecasting.
- Standard model evaluation.
- Integration into a mobile/backend decision-support workflow.

Important implementation boundary:

The SLS 105 Part 1: 2022 reference includes visual, physical, and chemical requirements. This project can only estimate camera-visible indicators. It cannot measure moisture, ash, volatile oil, piperine, non-volatile ether extract, or bulk density from images.

## Repository Status Summary

| Area | Status | Notes |
| --- | --- | --- |
| Research audit | COMPLETE | Official documents, guides, codebase, raw data, processed data, and model artifacts were inspected. |
| Backend API | VALIDATED WITH LIMITATIONS | FastAPI started and required grading-forecast endpoints returned HTTP 200 during Phase 5. |
| Flutter UI | OFFLINE FALLBACK + GRADE-AWARE PRICE DISPLAY IMPLEMENTED / BUILD VALIDATION PENDING | Component screens now route grading-forecast analysis through an offline-aware service. The price screen shows one predicted market price for the model-predicted grade, with no manual grade selector. |
| Firebase storage | IMPLEMENTED / LIVE VALIDATION NOT CONFIGURED | Phase 12 implemented Firestore result-history persistence using generated analysis IDs and runtime evidence. Analyze returns `saved_to_firebase: false` without blocking grading, forecast, and recommendation when Firebase is unavailable or save fails. |
| Berry V1 model | COMPLETED BUT OUTDATED | MobileNetV2 model exists, trained on old 360-image processed dataset. |
| Berry V2 model | COMPLETE | MobileNetV2 V2 baseline trained, tested, and exported under `ml/grading_forecast/berry_grading/models/v2/`. |
| Forecast V1 model | COMPLETED BUT OUTDATED | RandomForest artifact exists, trained on old processed price data through 2026-04-21. |
| Forecast V2 baseline | COMPLETE | Naive Persistence and RandomForest V2 were evaluated on identical test timestamps under `ml/grading_forecast/price_forecasting/models/v2/`. |
| Berry V2 data | PREPARED | V2 manifest, audit summary, and leakage-safe sample-level train/validation/test split were created. |
| Price V2 data | PREPARED | V2 cleaned data, National Grade 1 average weekly target, coverage summary, and chronological split were created. |
| EDA notebooks | NOT STARTED | Notebook folders exist only as scaffolds. |
| Limited improvement | COMPLETE | Phase 4 berry dropout 0.35 and forecast extended-lag RF experiments were completed and documented. |
| PP2 evidence | COMPLETE | Phase 1-6 dataset, model, integration, limitations, speaking points, and evidence references are recorded for PP2. |
| Existing implementation audit | COMPLETE | Phase 7 identified that runtime berry grading used the legacy/root ONNX model before Phase 8, runtime forecasting can return `demo_baseline`, Firebase is optional/fail-safe, and Flutter end-to-end validation remains pending. |
| Berry V2 runtime integration | COMPLETE | Phase 8 updated the berry grading service to load `BERRY-V2-MNV2` from `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx` and verified one V2 test image through the service path. |
| Forecast runtime integration | COMPLETE | Phase 9 selected Naive Persistence for runtime because it is the strongest validated V2 forecasting method and no inspected requirement forced the weaker trained RF artifact into runtime. |
| Recommendation validation | COMPLETE | Phase 10 confirmed that `analyze` passes actual grading and forecast outputs into the existing rule table and that representative grade/trend cases behave as implemented. |
| Backend reliability | COMPLETE | Phase 11 added focused request validation and safe error handling for the grading-forecast API without changing datasets, artifacts, model choices, Firebase, or Flutter. |
| Firebase persistence | COMPLETE / LIVE WRITE NOT VALIDATED | Phase 12 implemented application-level Firestore result persistence, validated mocked success and failure behavior, and made no credential changes. |
| Runtime diagnostic validation | COMPLETE / ACTION REQUIRED LATER | Phase 12.5 confirmed direct ONNX and backend predictions agree, identified a training-vs-runtime resize/letterbox mismatch for later review, and confirmed forecast output is intentionally single-series under the current Grade 1 target design. |
| Offline mobile TFLite fallback | IMPLEMENTED / BUILD VALIDATION PENDING | Phase 13 added a TFLite export from the existing V2 Keras model, bundled mobile class/forecast assets, wired Flutter analysis/recommendation through an offline service, and added grade-aware predicted-market-price display. Local Flutter formatting/analyze/build did not complete because the toolchain timed out. |

## Dataset Status

### Berry Image Dataset

Raw root: `data/raw/berry_images/`

Audit facts:

- Total raw image files: 671 JPG files.
- Grade 1 images: 224.
- Grade 2 images: 224.
- Grade 3 images: 223.
- Sample folders per grade: 56.
- Root-level grade images: 0.
- Unreadable images found during audit: 0.
- Duplicate image-content groups found during audit: 0.
- Image dimensions observed: 4000x3000, 4080x3060, 8160x6120.
- Aspect ratio: 4:3 for all audited images.
- EXIF camera models found: SM-A127F and Galaxy A06.
- EXIF orientation values found: 1, 3, 6, 8.
- Most samples contain 4 images.
- Samples with non-4 image counts exist and must be documented, not manually fabricated.

Current issue:

`data/annotations/grading_forecast/berry_grading_labels.csv` has 360 rows and is outdated. It corresponds to V1, not the current 671-image raw dataset.

V2 artifacts:

- `data/annotations/grading_forecast/berry_grading_labels_v2.csv`
- `data/processed/grading_forecast/berry_dataset_v2_summary.json`
- `data/processed/grading_forecast/berry_split_v2/`
- `data/processed/grading_forecast/berry_split_v2_manifest.csv`

V2 split:

- Fixed random seed: 42.
- Train: 117 samples, 467 images.
- Validation: 24 samples, 95 images.
- Test: 27 samples, 109 images.
- Leakage validation: no `grade + sample_id` group crosses train, validation, and test.

### Price Dataset

Raw file: `data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv`

Audit facts:

- Total rows: 7,742.
- Columns include date, commodity, country, district, grade, price_type, price_lkr_per_kg, currency, unit, market_level, frequency, source, source_url.
- Date range: 2021-02-22 to 2026-08-18.
- Practical main coverage begins from early January 2022.
- Commodity: black_pepper.
- Country: Sri Lanka.
- Market level: farm_gate.
- Frequency: weekly.
- Price types: highest and average.
- Grades: Grade 1 and Grade 2.
- Grade 1 rows: 6,930.
- Grade 2 rows: 812.
- Duplicate rows by date, district, grade, and price_type: 0.

Recommended primary forecasting target:

`National + Grade 1 + average + farm_gate + weekly`

Reason:

National Grade 1 average has the strongest and most continuous historical coverage. Grade 2 has sparse early historical coverage and should not be fabricated.

V2 artifacts:

- `data/processed/grading_forecast/price_v2/cleaned_price_data_v2.csv`
- `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`
- `data/processed/grading_forecast/price_v2/price_v2_coverage_summary.json`
- `data/processed/grading_forecast/price_v2/forecast_train.csv`
- `data/processed/grading_forecast/price_v2/forecast_validation.csv`
- `data/processed/grading_forecast/price_v2/forecast_test.csv`

V2 target:

- Target observations: 232.
- Target date range: 2021-02-22 to 2026-08-18.
- Chronological split: train 2021-02-22 to 2025-03-18, validation 2025-03-25 to 2025-11-25, test 2025-12-02 to 2026-08-18.
- Missing target gaps greater than 8 days: 12.
- Largest target gap: 316 days from 2021-02-22 to 2022-01-04.

## V1 Artifact Status

Berry V1 artifacts:

- `ml/grading_forecast/berry_grading/models/berry_mobilenetv2_best.keras`
- `ml/grading_forecast/berry_grading/models/berry_mobilenetv2_best.onnx`
- `ml/grading_forecast/berry_grading/models/berry_classifier_metrics.json`
- `ml/grading_forecast/berry_grading/models/berry_model_metadata.json`

Berry V1 result:

- Accuracy: 0.7778.
- Weighted precision: 0.8516.
- Weighted recall: 0.7778.
- Weighted F1: 0.7447.
- Grade 2 recall: 0.3333.

Forecast V1 artifacts:

- `ml/grading_forecast/price_forecasting/models/forecast_model.joblib`
- `ml/grading_forecast/price_forecasting/models/forecast_features.json`
- `ml/grading_forecast/price_forecasting/models/forecast_metrics.json`
- `ml/grading_forecast/price_forecasting/models/forecast_model_metadata.json`

Forecast V1 result:

- Train MAE: 15.7114.
- Train RMSE: 24.3440.
- Train R2: 0.9841.
- Test MAE: 45.8347.
- Test RMSE: 47.7556.
- Test R2: -6.1315.

Interpretation:

V1 artifacts are useful as historical baselines and software integration evidence. They should not be treated as final PP2 research results for the current dataset.

## V1 Script Safety Notes

- `scripts/generate_grading_labels.py` defaults to `data/annotations/grading_forecast/berry_grading_labels.csv`, so accidental execution may overwrite the old V1 label CSV.
- `ml/grading_forecast/berry_grading/preprocessing/validate_dataset.py` defaults to the V1 labels path and writes a V1-style validation summary.
- `ml/grading_forecast/berry_grading/preprocessing/prepare_training_images.py` defaults to `data/processed/grading_forecast/berry_images_processed`, so accidental execution may overwrite or mix into the old processed image directory.
- `ml/grading_forecast/price_forecasting/data/clean_price_data.py`, `prepare_forecast_training_data.py`, and `create_forecast_split.py` default to V1 processed output filenames.
- For PP2 V2 work, use the new V2-specific scripts and output paths unless an old script is explicitly parameterized and checked first.

## Berry V2 Model Result

Status: COMPLETE.

The berry training pipeline now supports the authoritative V2 data flow:

`data/raw/berry_images/` -> Phase 1 V2 preparation -> `berry_split_v2/train` and `berry_split_v2/val` -> MobileNetV2 training -> V2 model artifacts -> `berry_split_v2/test` final evaluation.

Required V2 output locations:

- Models: `ml/grading_forecast/berry_grading/models/v2/`
- Evaluation plots: `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/`

Phase 2 artifacts:

- `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.keras`
- `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`
- `mobile/assets/models/berry_mobilenetv2_v2_best.tflite`
- `ml/grading_forecast/berry_grading/models/v2/class_names.json`
- `ml/grading_forecast/berry_grading/models/v2/training_history.json`
- `ml/grading_forecast/berry_grading/models/v2/berry_model_metadata.json`
- `ml/grading_forecast/berry_grading/models/v2/berry_classifier_metrics.json`
- `ml/grading_forecast/berry_grading/models/v2/onnx_metadata.json`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/confusion_matrix.png`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/training_curves.png`

Final V2 test result:

- Test images: 109.
- Accuracy: 0.8073.
- Macro F1: 0.8068.
- Weighted F1: 0.8076.
- Grade 2 precision: 0.7805.
- Grade 2 recall: 0.8889.
- Grade 2 F1: 0.8312.

Environment note:

- Training/export used the project `.venv`, where TensorFlow and tf2onnx are available.
- Native Windows TensorFlow ran on CPU; GPU support was not available in that environment.

## Price Forecasting V2 Result

Status: COMPLETE.

The price forecasting pipeline used the authoritative V2 target:

`National + Grade 1 + average + farm_gate + weekly`

Phase 3 artifacts:

- `ml/grading_forecast/price_forecasting/models/v2/forecast_model.joblib`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_features.json`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_metrics.json`
- `ml/grading_forecast/price_forecasting/models/v2/naive_persistence_metrics.json`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_model_metadata.json`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_export_manifest.json`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/actual_vs_predicted.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/feature_importances.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/residuals.png`

Final V2 test result:

- Test prediction timestamps: 36.
- Same timestamps for naive and RandomForest: true.
- Feature dates before prediction dates: true.
- Naive Persistence MAE/RMSE/MAPE/R2: 16.4094 / 22.5208 / 0.8539 / 0.9045.
- RandomForest MAE/RMSE/MAPE/R2: 82.4179 / 88.4452 / 4.1679 / -0.4736.
- Decision: Naive Persistence is the stronger Phase 3 forecasting baseline on the V2 test period.

## Phase 4 Limited Improvement Result

Status: COMPLETE.

Berry selected improvement:

- Phase 2 baseline: MobileNetV2 dropout 0.25.
- Phase 4 experiment: MobileNetV2 dropout 0.35.
- Dataset/split: same `berry_split_v2` sample-level train/validation/test split.
- Final test metrics: accuracy 0.8073, macro F1 0.8068, weighted F1 0.8076.
- Grade 2 precision/recall/F1: 0.7805 / 0.8889 / 0.8312.
- Decision: dropout 0.35 did not improve or worsen the saved headline metrics compared with Phase 2, so the Phase 2 V2 model remains the selected PP2 berry baseline.

Berry Phase 4 artifacts:

- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_mobilenetv2_v2_phase4_best.keras`
- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_classifier_metrics.json`
- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_model_metadata.json`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v2_phase4/confusion_matrix.png`

Forecasting selected improvement:

- Phase 3 baseline: RandomForest with `lag_1`, `lag_2`, `lag_3`, rolling 3/5, date, and change features.
- Phase 4 experiment: add `lag_4`, `lag_8`, and `lag_12`.
- Dataset/split: same V2 National Grade 1 average weekly target and same 36 chronological V2 test timestamps.
- Phase 4 RF MAE/RMSE/MAPE/R2: 78.1641 / 84.8622 / 3.9482 / -0.3566.
- Decision: extended lags improved over the Phase 3 RF baseline, but did not outperform Naive Persistence.

Forecasting Phase 4 artifacts:

- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_model.joblib`
- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_metrics.json`
- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_model_metadata.json`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/actual_vs_predicted.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/feature_importances.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/residuals.png`

## Current Pending Work

- Flutter offline TFLite integration exists, but successful Flutter build/device validation remains pending.
- Flutter API mode still exists, but hosted-backend end-to-end validation remains pending because production API calls were rate limited/timed out during manual testing.
- Mobile/backend grade-aware price behavior needs emulator/API screenshot validation: Grade 1 should show the Grade 1 predicted market price, Grade 2 should show the gap-adjusted predicted market price, and Grade 3 should show price unavailable.
- Manual cross-component integration remains pending.

## Phase 7 Existing Implementation Audit Result

Status: COMPLETE.

Audit findings:

- At Phase 7 audit time, berry runtime used the legacy/root ONNX model: `ml/grading_forecast/berry_grading/models/berry_mobilenetv2_best.onnx`.
- Berry V2 research model exists separately: `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`.
- At Phase 7 audit time, forecast runtime used the legacy/root forecast model directory and could return `demo_baseline` because default raw input candidates did not point to the V2 forecasting dataset.
- Forecast V2 RandomForest and Phase 4 RandomForest artifacts exist separately under `ml/grading_forecast/price_forecasting/models/v2/` and `ml/grading_forecast/price_forecasting/models/v2_phase4/`.
- Naive Persistence is currently the strongest research forecasting method on the V2 test period.
- Recommendation logic exists and still needs validation using real runtime research outputs.
- Firebase/storage is implemented as optional fail-safe storage and was not configured during Phase 5.
- Flutter API integration exists, but end-to-end validation remains pending.
- Existing error handling and fallback behavior were identified.

Phase 7 changed documentation only. No backend, Flutter, dataset, model artifact, or configuration file was modified.

## Phase 8 Berry V2 Runtime Integration Result

Status: COMPLETE.

Runtime change:

- Previous berry runtime model: `ml/grading_forecast/berry_grading/models/berry_mobilenetv2_best.onnx`.
- New berry runtime model: `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`.
- Runtime model ID: `BERRY-V2-MNV2`.

Validation evidence:

- V2 artifact exists with sidecar `class_names.json` containing `Grade 1`, `Grade 2`, and `Grade 3`.
- ONNX metadata records input shape `[null, 224, 224, 3]`.
- Runtime preprocessing remains RGB letterbox to 224x224 with raw 0..255 float32 input because the ONNX graph includes MobileNetV2 preprocessing.
- Service-level validation used `data/processed/grading_forecast/berry_split_v2/test/grade_1/sample_002/20260508_152537.jpg`.
- Validation returned predicted grade `Grade 1`, confidence `0.88`, quality score `82.3`, and explanation identifying `BERRY-V2-MNV2` with the V2 ONNX path.
- The berry grading service no longer selects the legacy/root ONNX filename during normal real-model loading.

No forecasting, recommendation-rule, Firebase, Flutter, dataset, training, or model-artifact changes were made during Phase 8.

## Phase 9 Forecast Runtime Integration Result

Status: COMPLETE.

Requirement decision:

- Official/research documents checked: `docs/references/TAF_R26-SE-012.pdf`, `docs/references/R26-SE-012_IT22079268_PremathilakaGGRT.pdf`, `docs/research/PROJECT_STATUS.md`, `docs/research/PP2_RESULTS.md`, and `docs/research/Pending Work Plan — Berry Grading & Price Forecasting.md`.
- Confirmed requirement: short-term price forecasting using machine-learning/time-series techniques.
- Not confirmed: a strict requirement that the application runtime must use a trained RandomForest artifact even when a validated time-series baseline performs better.
- Runtime decision: use `naive_persistence`, because it is the strongest validated forecasting method on the V2 test period.

Runtime configuration:

- Method/model ID: `naive_persistence`.
- Runtime target data: `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`.
- Metrics source: `ml/grading_forecast/price_forecasting/models/v2/naive_persistence_metrics.json`.
- Latest observed target price used by runtime validation: 2026-08-18, 1886.14 LKR/kg, rounded to `1886` for the existing integer API schema.

Validation evidence:

- Service-level forecast validation returned model `naive_persistence`.
- Current price: `1886`.
- Predicted price: `1886`.
- Trend: `stable`.
- Saved metric fields returned by the existing API schema: MAE `16.4094`, RMSE `22.5208`.
- Same input produced the same forecast on repeat.
- Missing-file validation returned `forecast_unavailable`, not `demo_baseline`.
- The real application forecasting path no longer returns fabricated demo values.

No berry grading, recommendation-rule, Firebase, Flutter, dataset, training, evaluation, or model-artifact changes were made during Phase 9.

## Phase 10 Recommendation & Decision Logic Result

Status: COMPLETE.

Implementation found:

- Recommendation service: `backend/app/services/grading_forecast/recommendation_service.py`.
- Analyze route: `backend/app/api/routes/grading_forecast.py`.
- Inputs used: predicted grade, forecast trend, optional quality score, optional current price, and optional predicted price.
- Inputs not used directly: grading confidence and forecast model identifier.

Runtime data-flow validation:

- Berry grading output came from `BERRY-V2-MNV2`.
- Forecast output came from `naive_persistence`.
- `demo_baseline` did not reach the recommendation path in the validated service-level flow.
- Recommendation result used the existing rule table without changing business rules.

Validation evidence:

- Actual-output chain used `data/processed/grading_forecast/berry_split_v2/test/grade_1/sample_002/20260508_152537.jpg`.
- Grading: Grade 1, quality score 82.3, runtime model `BERRY-V2-MNV2`.
- Forecast: `naive_persistence`, current price 1886, predicted price 1886, trend stable.
- Recommendation: `SELL_EXPORT`.
- Representative Grade 1/2/3 upward and downward cases passed.
- Stable trend and missing optional quality/price inputs passed.
- Invalid grade values are rejected by the API schema before reaching the service.

No application code was modified during Phase 10.

## Phase 11 Backend Reliability & Error Handling Result

Status: COMPLETE.

Files changed:

- `backend/app/api/routes/grading_forecast.py`
- `backend/app/services/grading_forecast/grading_service.py`

Validation evidence:

- Valid V2 grade-only request returned HTTP 200, predicted `Grade 1`, and identified `BERRY-V2-MNV2` without exposing an absolute filesystem path.
- Valid price forecast request returned HTTP 200 with model `naive_persistence`, current price `1886`, predicted price `1886`, and no `demo_baseline`.
- Valid analyze request returned HTTP 200 with V2 grading, `naive_persistence` forecast, recommendation `SELL_EXPORT`, and optional storage result `saved_to_firebase: false`.
- Missing image, empty image, unsupported non-image upload, corrupt image, and oversized upload returned safe HTTP errors.
- Corrective validation, 2026-08-30: Flutter-style multipart uploads with `application/octet-stream` now pass when the decoded bytes are valid JPEG, PNG, or WEBP; valid JPEG reached `BERRY-V2-MNV2`, and valid analyze still used `naive_persistence`.
- Missing V2 model artifacts raised explicit grading failure and did not load the legacy/root ONNX model.
- Invalid V2 class mapping raised explicit grading failure.
- Invalid ONNX output shape and ONNX inference failure raised explicit grading failure.
- Missing or malformed forecast data returned `forecast_unavailable`.
- API-level unavailable forecast checks returned HTTP 503 for `price-forecast` and `analyze` instead of generating a normal recommendation.
- Invalid recommendation schema values returned HTTP 422.
- Unexpected grading and recommendation service failures returned safe JSON HTTP 500 responses.

No datasets, model artifacts, Flutter code, Firebase configuration, recommendation rules, or forecasting method selection were changed during Phase 11 or the corrective upload-validation fix.

## Phase 12 Firebase Persistence Result

Status: COMPLETE.

Decision: Firebase persistence is required final functionality for application-level historical result storage, while live inference results must remain available when Firebase is unavailable.

Evidence used:

- `docs/guidelines_with_steps.md` identifies Firebase result storage for the component.
- The current Phase 12 requirement states persistence of prediction/analysis results and historical forecast information is required for the application.
- `docs/guidelines_with_steps.md` also says not to require Firebase credentials for local demo and to safely fall back when Firebase is not configured.

Implementation result:

- `backend/app/services/grading_forecast/result_storage_service.py` now generates an `analysis_id` and Firestore document ID for each persisted analysis.
- Stored documents include application metadata, image identifier, grading result, forecast result, recommendation, runtime identifiers, and timestamp.
- `backend/app/db/firebase.py` now safely handles Firebase configuration path-resolution errors.
- No Firebase credentials, service-account JSON, `.env` secrets, or private keys were created or committed.
- Existing code uses `FIREBASE_SERVICE_ACCOUNT_PATH`, `FIREBASE_PROJECT_ID`, and optional `FIREBASE_RESULTS_COLLECTION`.
- Default Firestore collection is `grading_forecast_results`.
- Persistence is application-level/non-user-scoped because no existing authenticated user identity was found for this component.
- Retrieval is not implemented and was not required by the inspected component requirements.

Validation evidence:

- Mocked Firebase success: analyze returned HTTP 200 with valid V2 grading, `naive_persistence` forecast, recommendation `SELL_EXPORT`, `saved_to_firebase: true`, and a generated document ID.
- Firebase unconfigured: analyze returned HTTP 200 with valid V2 grading, `naive_persistence` forecast, recommendation `SELL_EXPORT`, and `saved_to_firebase: false`.
- Firebase initialization failure: returned no client without crashing.
- Simulated Firebase save failure: analyze returned HTTP 200 with valid grading/forecast/recommendation and `saved_to_firebase: false`, `document_id: null`.
- Document serialization failure: storage returned `saved_to_firebase: false`, `document_id: null`.
- Mocked successful save document contains analysis ID, component, component version, persistence scope, user ID placeholder, image ID, processed flag, runtime identifiers, grading, forecast, recommendation, limitation note, and timestamp.
- Current storage code does not store raw image bytes.
- Live Firebase write validation was not performed because Firebase credentials are not configured.

No datasets, model artifacts, Flutter code, Firebase credentials, recommendation rules, forecasting logic, or grading logic were changed during Phase 12.

## Phase 12.5 Runtime Diagnostic Validation Result

Status: COMPLETE.

Purpose:

Manual runtime testing reported suspicious berry classifications and identical price forecasts across different berry grades. Phase 12.5 diagnosed root cause candidates without changing application code, models, datasets, preprocessing, class mappings, forecasting logic, recommendation rules, Firebase, or Flutter.

Berry diagnostic findings:

- Direct ONNX inference and backend service inference agreed on all 9 selected V2 test images.
- Diagnostic sample accuracy was 6/9: Grade 1 = 3/3 correct, Grade 2 = 0/3 correct, Grade 3 = 3/3 correct.
- This 9-image result is diagnostic only and does not replace the saved full V2 test result.
- Class order was confirmed as Grade 1, Grade 2, Grade 3.
- ONNX input is float tensor `image` with shape `[None, 224, 224, 3]`; output is `probs` with shape `[None, 3]`.
- Confirmed issue for later implementation review: training loaded images with direct Keras resize to 224x224, while backend runtime uses RGB letterbox to 224x224 before ONNX inference.
- ONNX graph contains arithmetic preprocessing operations, so runtime correctly supplies raw 0..255 float32 RGB input to the graph.

Forecast diagnostic findings:

- Runtime forecast source is `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`.
- This is a single National Grade 1 average weekly price target, not a grade-specific Grade 1/2/3 runtime forecast.
- Latest observed price used by runtime diagnostics was 2026-08-18, 1886.14 LKR/kg, rounded to `1886`.
- Runtime method `naive_persistence` predicts `1886` from the latest available observation and returns `stable`.
- Identical price forecasts across different berry grades are expected under the current single-series forecasting design.

Recommendation impact:

The recommendation receives the actual runtime grade and actual `naive_persistence` forecast. Therefore, an incorrect berry grade can propagate into an incorrect recommendation even when forecast and recommendation services behave as implemented.

## Phase 13 Offline Mobile TFLite Fallback Result

Status: IMPLEMENTED / BUILD VALIDATION PENDING.

Purpose:

Manual hosted-backend testing was blocked by timeout and HTTP 429 behavior. Phase 13 adds an offline mobile fallback so the grading-forecast flow can run without Railway, Hugging Face, or a local FastAPI backend.

Implementation result:

- Added TFLite export script: `ml/grading_forecast/berry_grading/training/export_berry_tflite_model.py`.
- Exported mobile model: `mobile/assets/models/berry_mobilenetv2_v2_best.tflite`.
- Exported mobile metadata: `mobile/assets/models/berry_mobilenetv2_v2_best_metadata.json`.
- Bundled mobile data assets: `mobile/assets/data/berry_grading_class_names.json`, `mobile/assets/data/naive_persistence_metrics.json`, and `mobile/assets/data/national_grade1_average_weekly.csv`.
- Added Flutter offline inference service: `mobile/lib/features/grading_forecast/services/offline_grading_forecast_service.dart`.
- Added Flutter mode router: `mobile/lib/features/grading_forecast/services/grading_forecast_analysis_service.dart`.
- Updated grading-forecast screens to use the mode router instead of directly depending on the API client.

Runtime behavior:

- Default mobile mode is offline because `PEPPER_ANALYSIS_MODE` defaults to `offline`.
- API mode can be enabled with `--dart-define=PEPPER_ANALYSIS_MODE=api` and still uses `GradingForecastApiService`.
- Offline grading uses the TFLite model with input shape `[1, 224, 224, 3]`, float32 RGB pixels in the `0..255` range, and output shape `[1, 3]`.
- Offline forecasting uses the same bundled National Grade 1 average weekly series and returns `naive_persistence_mobile`.
- Offline persistence returns `saved_to_firebase: false`; live Firebase persistence remains a backend responsibility.
- Price display is grade-aware: Grade 1 uses the Grade 1 series directly, Grade 2 subtracts the documented 100 LKR/kg Grade 2 discount, and Grade 3 shows unavailable instead of a fabricated predicted price.
- The Flutter price page shows one label, `Predicted market price`, and does not let the user manually select a different grade.

Validation status:

- TFLite export completed from the existing V2 Keras model; no training was run.
- TFLite tensor metadata inspection confirmed input `[1, 224, 224, 3]` float32 and output `[1, 3]` float32.
- Backend artifact tests passed separately after the bundled-artifact fallback work.
- Focused backend tests for grade-aware pricing and route behavior passed: `14 passed`.
- Flutter formatting/analyze/build validation is still pending because local Flutter/Dart tooling timed out.

## Phase 6 Evidence and Documentation Result

Status: COMPLETE.

Completed documentation outputs:

- Final dataset summary table in `docs/research/PP2_RESULTS.md`.
- Final berry experiment table in `docs/research/PP2_RESULTS.md`.
- Final forecast experiment table in `docs/research/PP2_RESULTS.md`.
- Final integration validation table in `docs/research/PP2_RESULTS.md`.
- Evidence map in `docs/research/PP2_RESULTS.md`.
- PP2 speaking points in `docs/research/PP2_RESULTS.md`.
- Final limitations in `docs/research/PP2_LIMITATIONS.md`.
- Phase execution checklist in `docs/research/PP2_EXECUTION_CHECKLIST.md`.

Phase 6 was documentation-only. No model training, evaluation, backend execution, Flutter execution, dataset modification, or artifact regeneration was performed during Phase 6.

## Phase 5 Integration Validation Result

Status: COMPLETE with runtime limitations.

Evidence file:

- `docs/research/PP2_INTEGRATION_VALIDATION.md`

Backend startup:

- FastAPI started successfully on `http://127.0.0.1:8000`.

Validated endpoints:

- `GET /api/v1/grading-forecast/health`: HTTP 200, `status: ok`.
- `GET /api/v1/grading-forecast/price-forecast`: HTTP 200, runtime model `demo_baseline`.
- `POST /api/v1/grading-forecast/grade-only`: HTTP 200 using sample image from `berry_split_v2/test`; response indicated real ONNX grading model use.
- `POST /api/v1/grading-forecast/analyze`: HTTP 200 with grading, forecast, recommendation, and storage fields.

Runtime model/fallback status:

- During Phase 5, berry grading runtime used legacy/root artifacts: `ml/grading_forecast/berry_grading/models/berry_mobilenetv2_best.onnx` and `class_names.json`. Phase 8 later changed the berry runtime to `BERRY-V2-MNV2`.
- Price forecasting runtime returned `demo_baseline`; it did not use the Phase 3 or Phase 4 V2 forecasting research artifacts.
- Storage returned `saved_to_firebase: false` because Firebase was not configured.

Mobile status:

- Flutter grading forecast API service was inspected. It calls the backend analyze and recommend endpoints and defaults to `localhost:8000` or Android emulator `10.0.2.2:8000`.
- Flutter was not run during Phase 5.

## Current Decision Record

- Use V1 MobileNetV2 as historical baseline only.
- Use V2 MobileNetV2 as the primary PP2 berry grading model.
- Phase 4 berry dropout 0.35 did not improve the saved test metrics; keep the Phase 2 V2 MobileNetV2 model as the selected PP2 berry baseline.
- Use National Grade 1 average farm-gate weekly price as the primary forecasting target.
- Use Naive Persistence as the stronger Phase 3 forecasting baseline because it outperformed RandomForest on the V2 test period.
- Keep V2 RandomForest as the required ML baseline and evidence that the simple method generalized better on the current short test window.
- Phase 4 extended-lag RandomForest improved over the Phase 3 RandomForest baseline, but still did not beat Naive Persistence.
- Phase 5 backend API validation is sufficient for PP2 demo path evidence, but the runtime model/fallback behavior must be described separately from the V2 research metrics.
- Keep the backend API as the canonical integrated runtime when hosted or local backend infrastructure is available.
- Use the offline mobile TFLite path as the practical fallback when hosted backend, Hugging Face, or local backend access is unavailable.
- Do not treat the TFLite conversion as a new trained model or as new model-evaluation evidence; it is an export of the selected V2 Keras model.
- Do not make ARIMA, SARIMA, XGBoost, Prophet, or LSTM mandatory before PP2.
- Do not fabricate missing Grade 2 price observations.
- Do not manually annotate unavailable camera/background/capture metadata for PP2.

## Next Exact Action

Validate the Phase 13 Flutter offline build and emulator flow on a working Flutter toolchain, then compare a small fixed image sample between mobile TFLite output and backend ONNX output before presenting offline mode as final integrated evidence.
