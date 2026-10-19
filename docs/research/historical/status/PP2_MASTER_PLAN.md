# PP2 Master Plan: Berry Grading and Export Price Forecasting

Last updated: 2026-08-31

This plan is designed for the four-day Progress Presentation 2 constraint. It focuses on academically defensible progress, not model proliferation.

## PP2 Strategy

The PP2 goal is to show:

- the project has been recovered and audited;
- V1 artifacts are understood as historical baselines;
- V2 datasets are prepared correctly;
- berry grading avoids sample leakage;
- forecasting uses a defensible target;
- at least one fresh baseline experiment exists for each subproblem;
- software integration can be demonstrated through the existing backend/mobile flow.

Do not train many models for PP2. The required comparison is intentionally small:

Berry:

- Existing V1 MobileNetV2 as historical baseline.
- V2 MobileNetV2 using sample-level train/validation/test split.
- One limited improvement experiment if time permits.

Forecasting:

- Naive persistence baseline.
- RandomForest with lag/rolling features.
- One limited improvement experiment if time permits.

## Phase 0 — Repository and Research Audit

Status: COMPLETE

### Objective

Recover the real project state and identify the difference between completed V1 work, current V2 datasets, incomplete work, and PP2 priorities.

### Research Purpose

Prevents continuing from incorrect assumptions and creates a defensible foundation for the remaining research work.

### Prerequisites

- Existing repository available locally.
- Official TAF, individual proposal, team proposals, and SLS standard available.
- Raw berry and price datasets available.

### Exact Tasks

- Inspect official research documents.
- Inspect existing project guides.
- Inspect ChatGPT plan 1 and plan 2.
- Inspect codebase structure.
- Inspect raw and processed datasets.
- Inspect existing model artifacts and metrics.
- Identify outdated/obsolete files.
- Define PP2-ready scope.

### Expected Inputs

- `docs/references/TAF_R26-SE-012.pdf`
- `docs/references/R26-SE-012_IT22079268_PremathilakaGGRT.pdf`
- Other member proposal PDFs.
- `docs/references/SLS 105 Part 1_ 2022 - Compiled Black Pepper Standards.pdf`
- Existing guides under `docs/agent_guide/` and `docs/research/`
- `data/raw/berry_images/`
- `data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv`
- `ml/grading_forecast/`
- `backend/app/services/grading_forecast/`
- `mobile/lib/features/grading_forecast/`

### Expected Outputs

- Audit conclusions captured in this PP2 documentation set.
- V1/V2 distinction clarified.
- Next execution phase defined.

### Files/Scripts Likely To Be Involved

- Read-only inspection only.

### Validation Criteria

- Repository status and dataset counts are based on local files.
- Official project requirements are reflected.
- Major risks are identified.

### Completion Criteria

- This phase is complete when `PROJECT_STATUS.md`, `PP2_MASTER_PLAN.md`, `EXPERIMENT_LOG.md`, `PP2_RESULTS.md`, `PP2_LIMITATIONS.md`, and `PP2_EXECUTION_CHECKLIST.md` exist.

### Risks

- PDF extraction may be imperfect.
- Some requirements may have changed after proposal submission.

### Fallback/Contingency

- Treat official documents as highest-priority evidence.
- Treat local data/code audit as current implementation evidence.
- Mark uncertain items explicitly.

### Estimated Priority

CRITICAL. Completed.

## Phase 1 — Dataset V2 Preparation and Audit

Status: COMPLETE

### Objective

Create a clean V2 dataset foundation without modifying raw data or deleting V1 artifacts.

### Research Purpose

PP2 results must be based on the current datasets and must avoid data leakage or fabricated observations.

### Prerequisites

- Phase 0 complete.
- Raw berry images remain in `data/raw/berry_images/`.
- Raw price CSV remains in `data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv`.

### Exact Tasks

- Generate a V2 berry manifest from the folder structure.
- Include automatically derived fields: `image_id`, `image_path`, `grade`, `sample_id`.
- Preserve optional/unknown annotation fields only as placeholders.
- Validate all image paths.
- Record image counts by grade and by sample.
- Record samples with fewer/more than four images.
- Record EXIF device and orientation if available.
- Create a sample-level train/validation/test split.
- Ensure all images from the same physical sample remain in the same split.
- Clean the V2 price dataset into a standardized full table.
- Extract the primary forecasting target: National + Grade 1 + average + farm_gate + weekly.
- Analyze missing weeks and temporal gaps.
- Report Grade 2 coverage as descriptive evidence only.

### Expected Inputs

- `data/raw/berry_images/grade_1/sample_*/`
- `data/raw/berry_images/grade_2/sample_*/`
- `data/raw/berry_images/grade_3/sample_*/`
- `data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv`
- Existing V1 scripts as references.

### Expected Outputs

- `data/annotations/grading_forecast/berry_grading_labels_v2.csv`
- `data/processed/grading_forecast/berry_dataset_v2_summary.json`
- `data/processed/grading_forecast/berry_split_v2/`
- `data/processed/grading_forecast/berry_split_v2_manifest.csv`
- `data/processed/grading_forecast/price_v2/cleaned_price_data_v2.csv`
- `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`
- `data/processed/grading_forecast/price_v2/price_v2_coverage_summary.json`
- `data/processed/grading_forecast/price_v2/forecast_train.csv`
- `data/processed/grading_forecast/price_v2/forecast_validation.csv`
- `data/processed/grading_forecast/price_v2/forecast_test.csv`

### Files/Scripts Likely To Be Involved

- `scripts/generate_grading_labels.py`
- `ml/grading_forecast/berry_grading/preprocessing/validate_dataset.py`
- `ml/grading_forecast/berry_grading/preprocessing/prepare_training_images.py`
- New likely script: `ml/grading_forecast/berry_grading/preprocessing/create_sample_level_split.py`
- `ml/grading_forecast/price_forecasting/data/clean_price_data.py`
- `ml/grading_forecast/price_forecasting/data/prepare_forecast_training_data.py`
- `ml/grading_forecast/price_forecasting/data/create_forecast_split.py`

### Validation Criteria

- V2 berry manifest row count matches raw readable image count.
- Every manifest path exists.
- No duplicate image paths.
- All three classes are represented.
- Every split contains all three classes.
- No sample_id appears in more than one split.
- Price target has exactly one row per observed date.
- Missing weeks are documented, not silently fabricated.
- Grade 2 sparse coverage is documented.

### Completion Criteria

- V2 dataset summaries and split files exist.
- V1 artifacts remain untouched.
- `PP2_RESULTS.md` is updated with dataset evidence.
- `EXPERIMENT_LOG.md` has a dataset version entry.

Completion result:

- Berry V2 manifest contains 671 readable images from the current raw folder structure.
- Berry split is deterministic with seed 42 and uses `grade + sample_id` groups.
- Berry split validation passed with zero sample groups crossing train, validation, and test.
- Price V2 cleaned dataset contains 7,742 preserved observations.
- Primary target contains 232 National Grade 1 average farm-gate weekly observations.
- Chronological forecast split was created without shuffling or future leakage.

### Risks

- Existing scripts may overwrite V1 filenames by default.
- Some image paths may be missing from old labels.
- Weekly dates may not align to a fixed weekday.
- Grade 2 history is too sparse for reliable forecasting.

### Fallback/Contingency

- Add V2-specific output paths instead of overwriting old outputs.
- Use current folder structure as label source.
- Use observed weekly sequence and gap reporting rather than forcing a rigid calendar grid.
- Keep Grade 2 as limitation/future work.

### Estimated Priority

CRITICAL. Completed.

### Script Safety Note

The older V1 scripts were inspected before Phase 1 execution. Several still default to V1 output paths. Do not run them for V2 without checking command arguments:

- `scripts/generate_grading_labels.py` can overwrite `data/annotations/grading_forecast/berry_grading_labels.csv`.
- `ml/grading_forecast/berry_grading/preprocessing/prepare_training_images.py` can write into `data/processed/grading_forecast/berry_images_processed`.
- The original price-processing scripts can overwrite `cleaned_price_data.csv`, `forecast_training_data.csv`, `train_forecast_data.csv`, or `test_forecast_data.csv`.

For V2 dataset work, use:

- `ml/grading_forecast/berry_grading/preprocessing/prepare_berry_dataset_v2.py`
- `ml/grading_forecast/price_forecasting/data/prepare_price_v2_dataset.py`

## Phase 2 — Berry Grading V2 Baseline

Status: COMPLETE

### Objective

Train and evaluate the V2 MobileNetV2 baseline using the leakage-safe sample-level split.

### Research Purpose

Produces a current grading result that can be compared against the historical V1 MobileNetV2 baseline.

### Prerequisites

- Phase 1 berry V2 manifest complete.
- Phase 1 sample-level train/validation/test split complete.
- Training environment dependencies available.

### Exact Tasks

- Update or parameterize training script to use `berry_split_v2`.
- Train MobileNetV2 with pretrained ImageNet backbone.
- Use training split only for model fitting.
- Use validation split for early stopping/tuning.
- Use test split only for final evaluation.
- Save metrics, confusion matrix, and training curves under V2-specific names/paths.
- Compare against V1 metrics.

### Expected Inputs

- `data/processed/grading_forecast/berry_split_v2/train/`
- `data/processed/grading_forecast/berry_split_v2/val/`
- `data/processed/grading_forecast/berry_split_v2/test/`
- `data/annotations/grading_forecast/berry_grading_labels_v2.csv`

### Expected Outputs

- `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.keras`
- `ml/grading_forecast/berry_grading/models/v2/class_names.json`
- `ml/grading_forecast/berry_grading/models/v2/training_history.json`
- `ml/grading_forecast/berry_grading/models/v2/berry_classifier_metrics.json`
- `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx`
- `ml/grading_forecast/berry_grading/models/v2/onnx_metadata.json`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/confusion_matrix.png`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/training_curves.png`

### Files/Scripts Likely To Be Involved

- `ml/grading_forecast/berry_grading/training/train_berry_classifier.py`
- `ml/grading_forecast/berry_grading/training/evaluate_berry_classifier.py`
- `ml/grading_forecast/berry_grading/training/export_berry_model.py`
- `ml/grading_forecast/berry_grading/inference/predict_berry_grade.py`

### Validation Criteria

- Training uses only train split.
- Validation metrics are not reported as final test metrics.
- Test metrics are calculated once on test split.
- Classification report includes all three grades.
- Confusion matrix is saved.
- Grade 2 recall is examined specifically.

### Completion Criteria

- V2 MobileNetV2 baseline metrics are available.
- `EXPERIMENT_LOG.md` is updated.
- `PP2_RESULTS.md` includes V1 vs V2 comparison.

Completion result:

- V2 MobileNetV2 was trained using `berry_split_v2/train` and `berry_split_v2/val`.
- Final evaluation was performed once on the untouched `berry_split_v2/test` split.
- Test accuracy: 0.8073.
- Macro F1: 0.8068.
- Weighted F1: 0.8076.
- Grade 2 precision/recall/F1: 0.7805 / 0.8889 / 0.8312.
- V2 Keras and ONNX artifacts were saved under `ml/grading_forecast/berry_grading/models/v2/`.
- V2 confusion matrix and training curves were saved under `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/`.

### Risks

- Training may take too long on CPU.
- Accuracy may be lower under leakage-safe splitting.
- Grade 2 may remain difficult to separate from Grade 3.

### Fallback/Contingency

- Reduce epochs.
- Freeze backbone and skip fine-tuning if needed.
- Report lower accuracy honestly as more reliable due to sample-level split.
- Keep V1 as historical baseline only.

### Estimated Priority

CRITICAL. Completed.

## Phase 3 — Price Forecasting V2 Baseline

Status: COMPLETE

### Objective

Build and evaluate the V2 forecasting baseline using the primary target: National + Grade 1 + average + farm_gate + weekly.

### Research Purpose

Produces a defensible short-term forecasting result while avoiding fabricated Grade 2 history.

### Prerequisites

- Phase 1 price V2 target series complete.
- Missing weeks and date gaps documented.
- Chronological train/validation/test split complete.

### Exact Tasks

- Build naive persistence baseline: next price equals current price.
- Train RandomForest using past-only lag and rolling features.
- Evaluate both methods on the same chronological test period.
- Report MAE, RMSE, MAPE, and R2.
- Plot actual vs predicted values.
- Record feature importance for RandomForest.

### Expected Inputs

- `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`
- `data/processed/grading_forecast/price_v2/forecast_train.csv`
- `data/processed/grading_forecast/price_v2/forecast_validation.csv`
- `data/processed/grading_forecast/price_v2/forecast_test.csv`

### Expected Outputs

- `ml/grading_forecast/price_forecasting/models/v2/forecast_model.joblib`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_features.json`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_metrics.json`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/actual_vs_predicted.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/feature_importances.png`

### Files/Scripts Likely To Be Involved

- `ml/grading_forecast/price_forecasting/training/train_forecast_model.py`
- `ml/grading_forecast/price_forecasting/training/evaluate_forecast_model.py`
- `ml/grading_forecast/price_forecasting/inference/predict_future_price.py`

### Validation Criteria

- Chronological split is used.
- No shuffle is used.
- Feature engineering uses past-only observations.
- Missing Grade 2 values are not fabricated.
- Naive baseline and RandomForest are evaluated on the same test rows.

### Completion Criteria

- Naive vs RandomForest table exists.
- V2 forecast metrics are recorded in `EXPERIMENT_LOG.md`.
- `PP2_RESULTS.md` includes target justification and metrics.

Completion result:

- Target: National + Grade 1 + average + farm_gate + weekly.
- Chronological split: train 162 rows, validation 34 rows, test 36 rows.
- Naive Persistence and RandomForest were evaluated on the same 36 V2 test timestamps.
- Naive Persistence MAE/RMSE/MAPE/R2: 16.4094 / 22.5208 / 0.8539 / 0.9045.
- RandomForest MAE/RMSE/MAPE/R2: 82.4179 / 88.4452 / 4.1679 / -0.4736.
- Decision: Naive Persistence outperformed RandomForest and is the stronger Phase 3 forecasting baseline.
- V2 forecast artifacts were saved under `ml/grading_forecast/price_forecasting/models/v2/`.
- V2 forecast plots were saved under `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/`.

### Risks

- RandomForest may not outperform naive baseline.
- Missing weeks may reduce effective training rows.
- R2 may be poor due to low variance in test period.

### Fallback/Contingency

- Present naive as a required baseline and RandomForest as the first ML attempt.
- Use MAE/RMSE/MAPE as primary discussion if R2 is unstable.
- Keep Grade 2 forecasting as future work.

### Estimated Priority

CRITICAL. Completed.

## Phase 4 — Limited Model Improvement

Status: COMPLETE

### Objective

Run one small improvement experiment for berry grading and one small improvement experiment for forecasting, only if Phases 1-3 finish in time.

### Research Purpose

Shows research iteration beyond "trained one model" while respecting the four-day constraint.

### Prerequisites

- Phase 2 baseline complete.
- Phase 3 baseline complete.
- Enough time remains before PP2.

### Exact Tasks

Berry selected improvement:

- Tune dropout only: Phase 2 dropout 0.25 -> Phase 4 dropout 0.35.

Forecasting selected improvement:

- Add extended historical lag features: `lag_4`, `lag_8`, and `lag_12`.

### Expected Inputs

- Phase 2 and Phase 3 baseline outputs.

### Expected Outputs

- Completed berry dropout experiment entry.
- Completed forecast extended-lag experiment entry.
- Updated baseline vs improvement comparison tables.

### Files/Scripts Likely To Be Involved

- `ml/grading_forecast/berry_grading/training/train_berry_classifier.py`
- `ml/grading_forecast/berry_grading/training/evaluate_berry_classifier.py`
- `ml/grading_forecast/price_forecasting/training/train_forecast_model_phase4.py`
- `ml/grading_forecast/price_forecasting/training/evaluate_forecast_model_phase4.py`

### Validation Criteria

- Improvement is compared against baseline on the same split.
- No test-set tuning.
- If performance worsens, result is still recorded.

### Completion Criteria

- `EXPERIMENT_LOG.md` and `PP2_RESULTS.md` contain baseline vs improvement comparisons.

Completion result:

- Berry improvement: MobileNetV2 dropout changed from 0.25 to 0.35 and evaluated on the same untouched V2 test split.
- Berry Phase 4 metrics: accuracy 0.8073, macro F1 0.8068, weighted F1 0.8076, Grade 2 precision/recall/F1 0.7805 / 0.8889 / 0.8312.
- Berry conclusion: dropout 0.35 did not improve or worsen the saved headline test metrics compared with the Phase 2 V2 baseline.
- Forecasting improvement: RandomForest extended with `lag_4`, `lag_8`, and `lag_12`.
- Forecast Phase 4 RandomForest MAE/RMSE/MAPE/R2: 78.1641 / 84.8622 / 3.9482 / -0.3566.
- Forecast conclusion: extended lags improved over the Phase 3 RandomForest baseline, but did not beat Naive Persistence.
- Berry artifacts: `ml/grading_forecast/berry_grading/models/v2_phase4/` and `ml/grading_forecast/berry_grading/evaluation/_outputs/v2_phase4/`.
- Forecast artifacts: `ml/grading_forecast/price_forecasting/models/v2_phase4/` and `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/`.

### Risks

- Improvement does not improve.
- Training time runs out.

### Fallback/Contingency

- Present the Phase 2 berry baseline as the selected PP2 berry model because the dropout change did not improve test metrics.
- Present Naive Persistence as the strongest PP2 forecasting method because both RandomForest variants underperformed it.

### Estimated Priority

HIGH. Completed.

## Phase 5 — Integration Validation

Status: COMPLETE

### Objective

Verify that the existing backend/mobile flow can demonstrate the component without changing the application implementation unless a blocking issue is found later.

### Research Purpose

Shows that the research artifact is not notebook-only and fits the shared system architecture.

### Prerequisites

- At least one usable berry model artifact or V1 artifact.
- At least one usable forecast artifact or fallback forecast service.
- Backend dependencies installed.
- Flutter project available.

### Exact Tasks

- Start FastAPI backend.
- Call health endpoint.
- Call price forecast endpoint.
- Call grade-only endpoint with a sample image.
- Call analyze endpoint with a sample image.
- Confirm response includes grading, forecast, recommendation, and storage.
- Confirm response indicates whether real model or fallback was used.
- Optionally run Flutter flow against backend.

### Expected Inputs

- Existing backend implementation.
- Existing mobile implementation.
- Model artifacts from V1 or V2.

### Expected Outputs

- API response examples for PP2.
- Optional screenshots from Flutter flow.
- Integration validation notes in `PP2_RESULTS.md`.

### Files/Scripts Likely To Be Involved

- `backend/app/api/routes/grading_forecast.py`
- `backend/app/services/grading_forecast/grading_service.py`
- `backend/app/services/grading_forecast/price_forecast_service.py`
- `mobile/lib/features/grading_forecast/`
- `docs/api/grading_forecast_postman_collection.json`

### Validation Criteria

- Backend starts successfully.
- `/api/v1/grading-forecast/health` returns status ok.
- `/api/v1/grading-forecast/analyze` returns complete response.
- No silent claim of real model use if fallback is used.

### Completion Criteria

- PP2 demo path is known and recorded.

Completion result:

- FastAPI backend started successfully on `http://127.0.0.1:8000`.
- Health endpoint returned HTTP 200 and `status: ok`.
- Price forecast endpoint returned HTTP 200 using `demo_baseline`.
- Grade-only endpoint returned HTTP 200 using the real legacy/root ONNX grading model.
- Analyze endpoint returned HTTP 200 with grading, forecast, recommendation, and storage fields.
- Firebase was not configured; storage safely returned `saved_to_firebase: false`.
- Runtime evidence is recorded in `docs/research/PP2_INTEGRATION_VALIDATION.md`.
- Important runtime distinction at Phase 5 validation time: the backend did not automatically load PP2 V2 or Phase 4 artifact directories. Research metrics remained V2 evidence, while the Phase 5 backend demo used legacy/root grading ONNX and forecast fallback behavior. Later Phase 8/9 post-PP2 runtime work integrated Berry V2 runtime and Naive Persistence forecast runtime.

### Risks

- Dependency mismatch.
- Backend loads V1 artifacts instead of V2.
- Firebase credentials unavailable.
- Flutter environment issues.

### Fallback/Contingency

- Demonstrate backend API directly with curl/Postman.
- Use V1 artifacts for software demo while clearly presenting V2 results separately.
- Keep Firebase storage as safe fallback if live credentials are unavailable.

### Estimated Priority

HIGH. Completed.

## Phase 6 — PP2 Evidence and Documentation

Status: COMPLETE

### Objective

Convert implementation and experiment outputs into presentation-ready research evidence.

### Research Purpose

PP2 should demonstrate methodology, data quality awareness, model evidence, limitations, and integration progress.

### Prerequisites

- Phase 1 complete.
- Phase 2 and Phase 3 preferably complete.
- Phase 5 preferably complete.

### Exact Tasks

- Update `PROJECT_STATUS.md`.
- Update `PP2_RESULTS.md`.
- Update `EXPERIMENT_LOG.md`.
- Update `PP2_LIMITATIONS.md`.
- Update `PP2_EXECUTION_CHECKLIST.md`.
- Prepare tables for dataset counts and model metrics.
- Prepare figures: confusion matrix, actual vs predicted forecast, sample UI/API response.
- Create concise PP2 speaking points.

### Expected Inputs

- V2 dataset summaries.
- V2 metrics.
- Integration validation notes.

### Expected Outputs

- Final PP2 evidence documents.
- Clear current-status statement for presentation.

### Files/Scripts Likely To Be Involved

- Documentation only.

### Validation Criteria

- No fabricated results.
- All metrics reference actual artifacts.
- Limitations are explicit.
- Next work after PP2 is clear.

### Completion Criteria

- Documents are complete enough for PP2 preparation.

Completion result:

- `PP2_RESULTS.md` contains final presentation-facing tables for V2 datasets, berry experiments, forecasting experiments, and Phase 5 integration validation.
- `PP2_RESULTS.md` contains an evidence map linking final values to saved artifacts.
- `PP2_RESULTS.md` contains PP2 speaking points.
- `PP2_LIMITATIONS.md` explicitly records dataset, model, forecasting, integration, Firebase, Flutter, and runtime artifact limitations.
- `PROJECT_STATUS.md` identifies all PP2 phases as complete and records post-PP2/future work.
- `PP2_EXECUTION_CHECKLIST.md` records Phase 6 as complete.
- No new metrics were fabricated or recalculated during Phase 6.
- No model training, evaluation, backend execution, Flutter execution, dataset modification, or artifact regeneration was performed during Phase 6.

### Risks

- Experiments may not finish before documentation day.

### Fallback/Contingency

- Present dataset audit, corrected methodology, V1 historical results, and planned V2 experiment execution if training cannot complete.

### Estimated Priority

CRITICAL. Completed.

## Four-Day Execution Schedule

### Day 1

Priority: Phase 1.

- Create V2 berry manifest.
- Create sample-level berry split.
- Create V2 price target series.
- Save coverage and missingness summaries.
- Update PP2 docs with dataset evidence.

### Day 2

Priority: Phase 2 and Phase 3.

- Train V2 MobileNetV2 baseline.
- Evaluate V2 berry model on test split.
- Build naive persistence forecast baseline.
- Train/evaluate RandomForest V2.

### Day 3

Priority: Phase 4, then Phase 5.

- Run one limited berry improvement if Day 2 baseline is complete.
- Run one limited forecast improvement if baseline is complete.
- Start integration validation.

### Day 4

Priority: Phase 5 and Phase 6.

- Confirm backend demo path.
- Optional Flutter demo check.
- Finalize PP2 result tables.
- Finalize limitations and next-work slides.

## Not Mandatory Before PP2

- LSTM.
- ARIMA/SARIMA.
- XGBoost.
- Prophet.
- Manual camera/background/capture setup annotation.
- Manual image cropping.
- Advanced segmentation.
- TFLite export before PP2. A post-PP2 offline mobile TFLite fallback has now been implemented, but Flutter build/device validation is still pending.
- Production deployment.
- Full Firebase live validation.

## Post-PP2 Phase 13 Note

Phase 13 adds a practical offline Flutter fallback for grading-forecast analysis after hosted backend testing was blocked by timeout and HTTP 429 behavior.

Scope:

- Export the existing selected V2 Keras berry model to TensorFlow Lite without retraining.
- Bundle class names, Naive Persistence metrics, and the National Grade 1 weekly price series into Flutter assets.
- Route Flutter grading-forecast screens through an analysis service that defaults to offline mode.
- Keep backend API mode available through `--dart-define=PEPPER_ANALYSIS_MODE=api`.
- Show one `Predicted market price` for the model-predicted grade instead of separate current/predicted prices.
- Use the observed Grade 1 vs Grade 2 market-price gap for Grade 2 adjustment and show Grade 3 price as unavailable.

Validation boundary:

- TFLite tensor metadata has been checked.
- No new model metrics are claimed.
- Flutter formatter/analyzer/build/emulator validation remains pending because the local Flutter/Dart toolchain timed out.
