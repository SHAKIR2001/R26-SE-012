# PP2 Execution Checklist

Last updated: 2026-08-31

Use this checklist phase-by-phase. Do not jump to model training before Phase 1 is complete.

## Global Rules

- [x] Do not modify raw datasets.
- [x] Do not delete V1 artifacts.
- [x] Do not fabricate labels, prices, or metadata.
- [x] Do not report metrics unless the experiment was actually run.
- [x] Do not tune on the test set.
- [x] Keep V1 and V2 outputs clearly separated.
- [x] Update `EXPERIMENT_LOG.md` after each experiment or dataset preparation entry.
- [x] Update `PP2_RESULTS.md` after each completed phase.

## Phase 0: Repository and Research Audit

Status: COMPLETE

- [x] Official project scope reviewed.
- [x] Individual component scope reviewed.
- [x] SLS standard boundary reviewed.
- [x] Existing guides reviewed.
- [x] Previous ChatGPT plans reviewed.
- [x] Codebase inspected.
- [x] Raw berry dataset inspected.
- [x] Raw price dataset inspected.
- [x] Processed V1 artifacts inspected.
- [x] Current PP2 plan created.

## Phase 1: Dataset V2 Preparation and Audit

Status: COMPLETE

- [x] Create V2 berry manifest.
- [x] Include `sample_id` derived from folder path.
- [x] Validate image existence and readability.
- [x] Count images per grade.
- [x] Count samples per grade.
- [x] Record samples with non-4 image counts.
- [x] Record EXIF camera model and orientation if available.
- [x] Create sample-level train/validation/test split.
- [x] Verify no sample appears in multiple splits.
- [x] Create V2 price cleaned dataset.
- [x] Extract National Grade 1 average farm-gate weekly target.
- [x] Analyze missing weeks and temporal gaps.
- [x] Record Grade 2 coverage limitation.
- [x] Update `PROJECT_STATUS.md`.
- [x] Update `PP2_RESULTS.md`.
- [x] Add dataset entries to `EXPERIMENT_LOG.md`.

Phase 1 validation result: PASSED.

## Phase 2: Berry Grading V2 Baseline

Status: COMPLETE

- [x] Confirm V2 sample-level split exists.
- [x] Make training script accept explicit V2 train and validation directories.
- [x] Make training script accept V2 output directory.
- [x] Make evaluator accept explicit V2 model, test data, and output directories.
- [x] Make exporter support explicit V2 Keras, ONNX, and metadata paths.
- [x] Make inference resolve class names beside an explicit model path.
- [x] Run lightweight dry-run validation without training.
- [x] Train MobileNetV2 baseline on V2 train split.
- [x] Use validation split for early stopping/tuning.
- [x] Evaluate on V2 test split.
- [x] Save metrics JSON.
- [x] Save confusion matrix.
- [x] Save training curves.
- [x] Export V2 ONNX model.
- [x] Save V2 ONNX metadata.
- [x] Compare against V1 MobileNetV2 as historical reference.
- [x] Inspect Grade 2 recall.
- [x] Update `EXPERIMENT_LOG.md`.
- [x] Update `PP2_RESULTS.md`.

Phase 2 validation result: PASSED.

Evidence:

- V2 Keras model: `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.keras`
- V2 ONNX model: `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`
- V2 metrics: `ml/grading_forecast/berry_grading/models/v2/berry_classifier_metrics.json`
- V2 confusion matrix: `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/confusion_matrix.png`
- V2 test accuracy: 0.8073.
- V2 weighted F1: 0.8076.
- V2 Grade 2 recall: 0.8889.

## Phase 3: Price Forecasting V2 Baseline

Status: COMPLETE

- [x] Confirm V2 National Grade 1 average target exists.
- [x] Confirm chronological split exists.
- [x] Prepare naive persistence baseline implementation.
- [x] Prepare same-test-timestamp naive-vs-RandomForest evaluation.
- [x] Prepare explicit V2 output directories.
- [x] Verify dry-run path resolution without training/evaluation.
- [x] Update docs for Phase 3 pipeline preparation only.
- [x] Execute/evaluate naive persistence baseline.
- [x] Train/evaluate RandomForest.
- [x] Confirm past-only lag/rolling feature logic.
- [x] Save metrics JSON.
- [x] Save actual vs predicted plot.
- [x] Save feature importance plot if available.
- [x] Compare naive vs RandomForest.
- [x] Update `EXPERIMENT_LOG.md`.
- [x] Update `PP2_RESULTS.md`.

Phase 3 pipeline preparation result: PASSED.

Phase 3 experiment execution result: PASSED.

Evidence:

- V2 RF model: `ml/grading_forecast/price_forecasting/models/v2/forecast_model.joblib`
- V2 metrics: `ml/grading_forecast/price_forecasting/models/v2/forecast_metrics.json`
- V2 naive metrics: `ml/grading_forecast/price_forecasting/models/v2/naive_persistence_metrics.json`
- Actual-vs-predicted plot: `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/actual_vs_predicted.png`
- Feature importance plot: `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/feature_importances.png`
- Naive Persistence MAE/RMSE/MAPE/R2: 16.4094 / 22.5208 / 0.8539 / 0.9045.
- RandomForest MAE/RMSE/MAPE/R2: 82.4179 / 88.4452 / 4.1679 / -0.4736.
- Decision: Naive Persistence outperformed RandomForest on the V2 test period.

## Phase 4: Limited Model Improvement

Status: COMPLETE

- [x] Confirm Phase 2 baseline is complete.
- [x] Confirm Phase 3 baseline is complete.
- [x] Select one berry improvement only.
- [x] Select one forecast improvement only.
- [x] Run improvement on same splits.
- [x] Compare against baseline.
- [x] Record result even if it does not improve.
- [x] Update `EXPERIMENT_LOG.md`.
- [x] Update `PP2_RESULTS.md`.

Phase 4 validation result: PASSED.

Evidence:

- Berry improvement: MobileNetV2 dropout 0.25 -> 0.35, evaluated on the same 109-image V2 test split.
- Berry Phase 4 accuracy: 0.8073.
- Berry Phase 4 weighted F1: 0.8076.
- Berry Phase 4 Grade 2 precision/recall/F1: 0.7805 / 0.8889 / 0.8312.
- Berry decision: dropout 0.35 did not improve or worsen the saved headline metrics compared with Phase 2.
- Forecast improvement: RandomForest extended with `lag_4`, `lag_8`, and `lag_12`.
- Phase 4 RF MAE/RMSE/MAPE/R2: 78.1641 / 84.8622 / 3.9482 / -0.3566.
- Forecast decision: Phase 4 RF improved over Phase 3 RF, but Naive Persistence remained substantially stronger.

## Phase 5: Integration Validation

Status: COMPLETE

- [x] Start FastAPI backend.
- [x] Validate health endpoint.
- [x] Validate price forecast endpoint.
- [x] Validate grade-only endpoint with image.
- [x] Validate analyze endpoint with image.
- [x] Confirm response includes grading, forecast, recommendation, and storage.
- [x] Confirm whether real model or fallback was used.
- [ ] Optionally validate Flutter flow.
- [x] Save API response examples or screenshots.
- [x] Update `PP2_RESULTS.md`.

Phase 5 validation result: PASSED with runtime limitations.

Evidence:

- Integration evidence file: `docs/research/PP2_INTEGRATION_VALIDATION.md`
- Backend startup: successful on `http://127.0.0.1:8000`.
- Health endpoint: HTTP 200.
- Price forecast endpoint: HTTP 200, runtime model `demo_baseline`.
- Grade-only endpoint: HTTP 200, runtime explanation says real ONNX grading model was used.
- Analyze endpoint: HTTP 200 with grading, forecast, recommendation, and storage fields.
- Storage: Firebase not configured; returned `saved_to_firebase: false`.
- Flutter: inspected only; not run.

## Phase 6: PP2 Evidence and Documentation

Status: COMPLETE

- [x] Finalize dataset summary table.
- [x] Finalize berry experiment table.
- [x] Finalize forecast experiment table.
- [x] Finalize limitations.
- [x] Prepare final PP2 speaking points.
- [x] Confirm all pending metrics are either completed or marked pending.
- [x] Confirm no unsupported claims are included.

Phase 6 validation result: PASSED.

Evidence:

- Final dataset summary table: `docs/research/PP2_RESULTS.md`
- Final berry experiment table: `docs/research/PP2_RESULTS.md`
- Final forecast experiment table: `docs/research/PP2_RESULTS.md`
- Final integration validation table: `docs/research/PP2_RESULTS.md`
- Final limitations: `docs/research/PP2_LIMITATIONS.md`
- PP2 speaking points: `docs/research/PP2_RESULTS.md`
- Evidence map: `docs/research/PP2_RESULTS.md`
- Phase 6 did not run model training, model evaluation, backend execution, Flutter, or dataset modification.

## Phase 7: Existing Implementation Audit

Status: COMPLETE

- [x] Trace Flutter/API to FastAPI route, service, model/inference, recommendation, Firebase/storage, and response.
- [x] Identify current berry runtime model path.
- [x] Identify current forecasting runtime behavior and fallback reason.
- [x] Distinguish runtime artifacts from V2 research artifacts.
- [x] Identify recommendation logic and pending validation need.
- [x] Identify Firebase/storage fallback behavior.
- [x] Identify Flutter API contract and pending end-to-end validation.
- [x] Record Phase 8+ pending work list.
- [x] Confirm no application code was changed during Phase 7.

Phase 7 validation result: PASSED.

Evidence:

- At Phase 7 audit time, berry runtime used legacy/root ONNX: `ml/grading_forecast/berry_grading/models/berry_mobilenetv2_best.onnx`.
- Berry V2 research ONNX exists separately: `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`.
- At Phase 7 audit time, forecast runtime used the legacy/root forecast model directory and could return `demo_baseline` because default raw input candidates did not point to the V2 forecasting dataset.
- Forecast V2 RandomForest and Phase 4 RandomForest artifacts exist separately under `ml/grading_forecast/price_forecasting/models/v2/` and `ml/grading_forecast/price_forecasting/models/v2_phase4/`.
- Naive Persistence remains the strongest research forecasting method on the V2 test period.
- Firebase/storage is optional/fail-safe and was not configured during Phase 5.
- Flutter API integration exists; end-to-end Flutter validation remains pending.
- Phase 7 changed documentation only.

## Phase 8+ Pending Work

- [x] Berry V2 runtime integration.
- [x] Forecast runtime integration and runtime forecasting-method decision.
- [x] Recommendation validation using real runtime research outputs.
- [x] Firebase/storage validation if required.
- [x] Error handling/API hardening.
- [ ] Later manual integration with other components.
- [ ] Later Flutter offline TFLite build/device validation.
- [ ] Later Flutter backend API end-to-end validation.
- [ ] Later UI/UX improvements.
- [ ] Final integrated validation.

## Phase 8: Berry V2 Runtime Integration

Status: COMPLETE

- [x] Verify V2 ONNX artifact exists.
- [x] Verify V2 class names sidecar exists.
- [x] Verify V2 ONNX metadata/preprocessing requirements from saved artifacts.
- [x] Update berry grading runtime loader to use `BERRY-V2-MNV2`.
- [x] Prevent silent legacy/root ONNX selection in normal berry runtime loading.
- [x] Preserve existing grading API response structure.
- [x] Validate one existing V2 test image through the berry service path.
- [x] Confirm runtime evidence identifies `BERRY-V2-MNV2`.
- [x] Confirm no forecasting, recommendation, Firebase, Flutter, dataset, training, or model-artifact changes were made.

Phase 8 validation result: PASSED.

Evidence:

- New runtime model: `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`.
- Runtime model ID: `BERRY-V2-MNV2`.
- V2 class order: `Grade 1`, `Grade 2`, `Grade 3`.
- V2 ONNX input shape: `[null, 224, 224, 3]`.
- Runtime preprocessing: RGB letterbox to 224x224, raw 0..255 float32 input into ONNX graph with MobileNetV2 preprocessing inside the model.
- Test image: `data/processed/grading_forecast/berry_split_v2/test/grade_1/sample_002/20260508_152537.jpg`.
- Service validation result: predicted `Grade 1`, confidence `0.88`, quality score `82.3`, and explanation identified `BERRY-V2-MNV2`.
- Legacy/root ONNX filename is no longer selected by the berry grading service.

## Phase 9: Forecast Runtime Integration / Runtime Forecasting-Method Decision

Status: COMPLETE

- [x] Official project/TAF requirement regarding ML forecasting was checked.
- [x] Runtime forecasting method was explicitly selected.
- [x] Current `demo_baseline` real-application behavior was removed.
- [x] Actual research-backed forecasting logic is connected.
- [x] Correct runtime data/artifact source is verified.
- [x] Forecast output is deterministic/reproducible.
- [x] Current/latest price is real data.
- [x] Predicted price is research-backed.
- [x] Forecast method/model identifier is returned.
- [x] Focused backend/service-level validation passed.
- [x] Relevant research documentation updated.
- [x] PP2 execution checklist updated.
- [x] No unrelated application areas were modified.

Phase 9 validation result: PASSED.

Evidence:

- Requirement decision: inspected official/research documents require short-term price forecasting using machine-learning/time-series techniques, but no inspected requirement explicitly forced the application runtime to use a trained RandomForest artifact when Naive Persistence is the stronger validated forecasting method.
- Selected runtime method: `naive_persistence`.
- Runtime data source: `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`.
- Runtime metrics source: `ml/grading_forecast/price_forecasting/models/v2/naive_persistence_metrics.json`.
- Focused service validation returned model `naive_persistence`, current price `1886`, predicted price `1886`, trend `stable`, MAE `16.4094`, and RMSE `22.5208`.
- Repeat validation with the same input returned the same forecast.
- Missing-file validation returned `forecast_unavailable` instead of fabricated demo values.
- No berry grading, recommendation-rule, Firebase, Flutter, dataset, training, evaluation, or model-artifact changes were made.

## Phase 10: Recommendation & Decision Logic

Status: COMPLETE

- [x] Locate recommendation service and route wiring.
- [x] Identify recommendation inputs.
- [x] Confirm `analyze` passes actual grading output into recommendation logic.
- [x] Confirm `analyze` passes actual forecast output into recommendation logic.
- [x] Confirm `demo_baseline` does not reach the validated recommendation path.
- [x] Validate Grade 1 upward and downward cases.
- [x] Validate Grade 2 upward and downward cases.
- [x] Validate Grade 3 upward and downward cases.
- [x] Validate stable trend behavior.
- [x] Validate missing optional quality/price inputs.
- [x] Validate invalid grade handling through the API schema.
- [x] Confirm no recommendation business rules were changed.
- [x] Confirm no application code was modified.
- [x] Update relevant research documentation.

Phase 10 validation result: PASSED.

Evidence:

- Recommendation service: `backend/app/services/grading_forecast/recommendation_service.py`.
- Route wiring: `backend/app/api/routes/grading_forecast.py`.
- Actual-output chain: `BERRY-V2-MNV2` returned Grade 1 and quality score `82.3`; `naive_persistence` returned current price `1886`, predicted price `1886`, and trend `stable`; recommendation returned `SELL_EXPORT`.
- Representative rule tests passed for Grade 1/2/3 with upward and downward trends.
- Stable trend test passed.
- Missing optional fields test passed.
- Invalid grade values are rejected by the API schema.

## Phase 11: Backend Reliability & Error Handling

Status: COMPLETE

- [x] Inspect relevant grading-forecast backend route and services.
- [x] Validate missing image upload handling.
- [x] Validate empty image upload handling.
- [x] Validate unsupported/invalid image content handling without trusting client MIME alone.
- [x] Validate corrupt/unreadable image handling.
- [x] Validate oversized image handling.
- [x] Confirm valid V2 grading still uses `BERRY-V2-MNV2`.
- [x] Confirm missing V2 model artifacts fail explicitly and do not load the legacy/root ONNX model.
- [x] Confirm invalid V2 class mapping fails explicitly.
- [x] Confirm invalid ONNX output shape and inference failure fail explicitly.
- [x] Confirm valid forecasting still uses `naive_persistence`.
- [x] Confirm missing or malformed forecast data returns `forecast_unavailable`.
- [x] Confirm unavailable forecast state returns HTTP 503 in API routes that require a forecast.
- [x] Confirm `demo_baseline` is not returned by the valid runtime forecast path.
- [x] Confirm invalid recommendation schema values are rejected safely.
- [x] Confirm unexpected grading failures return safe JSON errors.
- [x] Confirm unexpected recommendation failures return safe JSON errors.
- [x] Confirm optional Firebase/storage failure remains non-blocking for valid analyze output.
- [x] Confirm no datasets, model artifacts, Flutter code, Firebase configuration, recommendation rules, or forecasting method selection were changed.

Phase 11 validation result: PASSED.

Corrective validation note, 2026-08-30:

- Root cause fixed: Flutter multipart uploads were sent without an explicit image MIME type, so the backend could see `application/octet-stream` and reject a valid image with HTTP 415 before decoding the file.
- Backend upload validation now treats Pillow-verified image bytes as authoritative and accepts valid JPEG, PNG, and WEBP uploads even when the multipart MIME value is missing or `application/octet-stream`.
- The 10 MB upload limit remains enforced.
- Focused validation passed for a V2 JPEG berry image through `grade-only` and `analyze`, generated PNG and WEBP uploads, missing image, empty upload, text/non-image content, corrupted image, and oversized upload.
- Valid JPEG upload reached `BERRY-V2-MNV2`; valid analyze still returned `naive_persistence` forecasting and optional Firebase status.
- Flutter code, datasets, model artifacts, forecasting, recommendation rules, and Firebase implementation were not modified by this correction.

Evidence:

- Valid grade-only request with V2 test image returned HTTP 200, predicted `Grade 1`, and identified `BERRY-V2-MNV2`.
- Valid price forecast returned model `naive_persistence`, current price `1886`, predicted price `1886`, and did not return `demo_baseline`.
- Valid analyze returned V2 grading, `naive_persistence` forecast, recommendation `SELL_EXPORT`, and `saved_to_firebase: false`.
- Missing image: HTTP 400.
- Empty image: HTTP 400.
- Unsupported text/non-image upload: HTTP 400 safe rejection after content decode failed.
- Corrupt image: HTTP 400.
- Oversized image: HTTP 413.
- Missing V2 model artifacts and invalid V2 class mapping: explicit grading failure, no legacy/root ONNX fallback.
- Invalid ONNX output shape and ONNX inference failure: explicit grading failure.
- Forecast unavailable state: HTTP 503 for API routes that require a forecast.
- Invalid recommendation inputs: HTTP 422.
- Unexpected grading/recommendation failures: safe JSON HTTP 500 responses.

## Phase 12: Firebase Persistence Implementation

Status: COMPLETE

- [x] Check whether Firebase persistence is required by relevant project/research guidance.
- [x] Classify Firebase persistence as required final functionality for application-level result history.
- [x] Confirm no Firebase credentials are required for the local/demo component flow.
- [x] Implement generated analysis/result ID persistence.
- [x] Persist V2 grading result, `naive_persistence` forecast, recommendation, and runtime identifiers.
- [x] Verify existing unconfigured Firebase behavior.
- [x] Verify valid analyze response still includes grading, forecast, and recommendation when Firebase is unavailable.
- [x] Verify `saved_to_firebase: false` and `document_id: null` when Firebase is unavailable.
- [x] Verify mocked Firebase success returns `saved_to_firebase: true` and a generated document ID.
- [x] Verify simulated Firebase save failure remains non-blocking.
- [x] Verify Firebase initialization failure remains non-blocking.
- [x] Verify document serialization failure remains non-blocking.
- [x] Inspect stored document structure through a mocked successful save.
- [x] Confirm no raw image bytes are stored by the current storage service.
- [x] Confirm retrieval is not required by inspected component requirements.
- [x] Confirm no Firebase credentials, secrets, or service-account files were created.
- [x] Confirm live Firebase write was not claimed because credentials are unavailable.

Phase 12 validation result: IMPLEMENTATION PASSED; LIVE FIREBASE WRITE NOT VALIDATED.

Evidence:

- Requirement decision: Firebase persistence is required for application-level result history, but must remain non-blocking for live inference results.
- Implementation files: `backend/app/services/grading_forecast/result_storage_service.py`, `backend/app/db/firebase.py`.
- Firebase unconfigured analyze result: HTTP 200 with valid V2 grading, `naive_persistence` forecast, recommendation `SELL_EXPORT`, and `saved_to_firebase: false`.
- Mocked Firebase success result: HTTP 200 with `saved_to_firebase: true` and generated document ID.
- Simulated save failure result: HTTP 200 with valid grading/forecast/recommendation, `saved_to_firebase: false`, and `document_id: null`.
- Firebase initialization failure and document serialization failure returned safe non-persisted status.
- Mocked successful document fields: analysis ID, component, component version, persistence scope, user ID placeholder, image ID, processed flag, runtime identifiers, grading, forecast, recommendation, limitation note, and timestamp.
- Environment variables used by existing code: `FIREBASE_SERVICE_ACCOUNT_PATH`, `FIREBASE_PROJECT_ID`, optional `FIREBASE_RESULTS_COLLECTION`.
- User scoping: application-level/non-user-scoped because no existing authenticated user identity was found for this component.
- Live Firebase write: not validated because credentials are not configured.

## Phase 12.5: Runtime Model & Forecast Diagnostic Validation

Status: COMPLETE

- [x] Compare Berry V2 training/export preprocessing against backend runtime preprocessing.
- [x] Validate V2 ONNX metadata, input shape, output shape, and class mapping.
- [x] Run a controlled 9-image diagnostic sample from `berry_split_v2/test`.
- [x] Compare direct ONNX inference against backend service inference for the same images.
- [x] Confirm whether backend and direct ONNX disagree.
- [x] Confirm whether the current forecast is single-series or grade-specific.
- [x] Confirm whether identical forecast values across grades are expected under the current design.
- [x] Record recommendation impact.
- [x] Update diagnostic documentation.

Phase 12.5 validation result: DIAGNOSTIC COMPLETE; NO APPLICATION CODE CHANGED.

Evidence:

- Direct ONNX and backend service predictions agreed on all 9 selected V2 test images.
- Diagnostic sample result: 6/9 correct; Grade 1 = 3/3, Grade 2 = 0/3, Grade 3 = 3/3. This is diagnostic only, not a replacement for the saved full-test metrics.
- ONNX metadata: input `image`, shape `[None, 224, 224, 3]`, float tensor; output `probs`, shape `[None, 3]`.
- Class order: index 0 = Grade 1, index 1 = Grade 2, index 2 = Grade 3.
- Confirmed preprocessing mismatch requiring later review: training used direct Keras resize to 224x224, while backend runtime uses RGB letterbox to 224x224 before ONNX inference.
- ONNX graph contains arithmetic preprocessing operations, so runtime supplies raw 0..255 float32 RGB input.
- Current forecast runtime loads `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`, a single National Grade 1 average weekly target.
- Latest observed runtime price: 2026-08-18, 1886.14 LKR/kg, rounded to `1886`; `naive_persistence` predicts the same value and returns `stable`.
- Same forecast for Grade 1, Grade 2, and Grade 3 is expected under the current single-series runtime design; grade-specific forecasting is not currently implemented.

## Phase 13: Offline Mobile TFLite Fallback

Status: IMPLEMENTED / BUILD VALIDATION PENDING

- [x] Create a separate implementation branch from the current branch.
- [x] Export the selected V2 Keras berry model to TensorFlow Lite without retraining.
- [x] Preserve the ONNX/backend runtime path.
- [x] Bundle the TFLite model under Flutter assets.
- [x] Bundle class names, Naive Persistence metrics, and the National Grade 1 weekly price series under Flutter assets.
- [x] Add a Flutter offline grading-forecast service.
- [x] Add a Flutter analysis mode router with default offline behavior.
- [x] Keep backend API mode available with `PEPPER_ANALYSIS_MODE=api`.
- [x] Keep offline Firebase persistence disabled and report `saved_to_firebase: false`.
- [x] Confirm TFLite tensor metadata without running model training.
- [x] Remove manual grade selection from the price forecast page.
- [x] Show one `Predicted market price` label instead of separate current and predicted prices.
- [x] Apply Grade 2 predicted market price adjustment from the observed Grade 1 vs Grade 2 historical gap.
- [x] Mark Grade 3 predicted market price unavailable because Grade 3 historical price data is unavailable.
- [x] Run focused backend tests for grade-aware pricing and route behavior.
- [ ] Run Flutter formatter successfully.
- [ ] Run Flutter analyzer successfully.
- [ ] Build APK successfully.
- [ ] Validate emulator/gallery image analysis in offline mode.
- [ ] Compare a small fixed image sample between mobile TFLite and backend ONNX outputs.

Phase 13 validation result: IMPLEMENTATION COMPLETE; FLUTTER TOOLCHAIN VALIDATION PENDING.

Evidence:

- Branch: `feature/offline-grading-forecast-mobile`.
- Export script: `ml/grading_forecast/berry_grading/training/export_berry_tflite_model.py`.
- Mobile model: `mobile/assets/models/berry_mobilenetv2_v2_best.tflite`.
- Mobile metadata: `mobile/assets/models/berry_mobilenetv2_v2_best_metadata.json`.
- Mobile data assets: `mobile/assets/data/berry_grading_class_names.json`, `mobile/assets/data/naive_persistence_metrics.json`, `mobile/assets/data/national_grade1_average_weekly.csv`.
- Flutter services: `mobile/lib/features/grading_forecast/services/offline_grading_forecast_service.dart`, `mobile/lib/features/grading_forecast/services/grading_forecast_analysis_service.dart`.
- TFLite input: `[1, 224, 224, 3]` float32 RGB `0..255`.
- TFLite output: `[1, 3]` float32.
- Grade 2 price adjustment: 100 LKR/kg discount, based on latest overlapping National average Grade 1 vs Grade 2 gap on 2026-08-18.
- Grade 3 price behavior: unavailable, not displayed as a fabricated price.
- Focused backend validation command: `.\.venv\Scripts\python.exe -m pytest --basetemp=C:\tmp\pytest-pepper backend\tests\test_price_forecast_service.py backend\tests\test_grading_forecast_routes.py`, result `14 passed`.
- No model training, dataset modification, or new evaluation metrics were produced.
- Flutter formatter/analyzer/build validation is pending because local Flutter/Dart tooling timed out.

## Four-Day Schedule Tracker

Day 1:

- [x] Finish Phase 1.

Day 2:

- [x] Finish Phase 2 baseline.
- [x] Finish Phase 3 baseline.

Day 3:

- [x] Run Phase 4 if time permits.
- [x] Start Phase 5.

Day 4:

- [x] Finish Phase 5.
- [x] Finish Phase 6.

## Stop Conditions

Stop and reassess if:

- V2 manifest does not match raw files.
- Any sample appears in more than one berry split.
- Price target has duplicated dates after filtering.
- A script would overwrite V1 artifacts without explicit V2 output paths.
- A model result is being reported without saved metrics.
