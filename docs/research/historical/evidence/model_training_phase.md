# Model Training Phase (Phase 3) — Berry Grading + Export Price Forecasting

This document describes the **real model training** work completed for the **Berry Grading and Export Price Forecasting** component of the `multimodal-pepper-ai-decision-support` project.

It focuses on:

1. Berry grading (image classification)
2. Short-horizon export price forecasting (one-step ahead, weekly)

Important: This is a **camera-based visual estimation** system. It **does not** measure moisture, piperine, volatile oil, ash, or bulk density, and it must **not** be presented as official SLS certification.

PP2 evidence update, 2026-08-28:

- Berry V2 MobileNetV2 baseline training, final test evaluation, and ONNX export are complete.
- The V2 berry baseline uses the sample-level split under `data/processed/grading_forecast/berry_split_v2/`.
- V2 model artifacts are stored under `ml/grading_forecast/berry_grading/models/v2/`.
- The old 360-image processed berry dataset and root-level model artifacts are historical V1 artifacts only.
- Price Forecasting V2 baseline training/evaluation is complete.
- Naive Persistence outperformed RandomForest on the V2 forecasting test period.
- Phase 4 limited improvement is complete.
- Berry Phase 4 changed only dropout from 0.25 to 0.35 and did not improve saved V2 test metrics.
- Forecasting Phase 4 added `lag_4`, `lag_8`, and `lag_12`; it improved over Phase 3 RandomForest but still underperformed Naive Persistence.
- Phase 5 integration validation is complete with runtime limitations.
- Phase 6 PP2 evidence documentation is complete.

---

## 1) Model Architectures

### 1.1 Berry grading model (MobileNetV2 transfer learning)

- Task: image classification
- Input: `224x224` RGB image (letterboxed)
- Output classes: `Grade 1`, `Grade 2`, `Grade 3`
- Base model: `MobileNetV2(weights="imagenet", include_top=False)`
- Head: GlobalAveragePooling → Dropout → Dense softmax (3 classes)
- Training: two-stage transfer learning (freeze → fine-tune)
- Goal: **lightweight**, laptop-friendly, mobile-friendly baseline.

### 1.2 Price forecasting model (RandomForestRegressor)

- Task: one-step ahead regression (predict next week price)
- Model: `RandomForestRegressor`
- Goal: **explainable**, stable baseline suitable for academic defense.

---

## 2) Dataset Summary

### 2.1 Berry grading dataset

Current PP2 V2 dataset:

- V2 split directory:
  - `data/processed/grading_forecast/berry_split_v2/`
- Split folders:
  - `train/`, `val/`, `test/`
- V2 manifest:
  - `data/annotations/grading_forecast/berry_grading_labels_v2.csv`
- V2 split manifest:
  - `data/processed/grading_forecast/berry_split_v2_manifest.csv`
- Dataset size:
  - 671 images from 168 physical sample groups
  - Grade 1: 224 images
  - Grade 2: 224 images
  - Grade 3: 223 images
- Leakage-safe split:
  - Train: 117 samples, 467 images
  - Validation: 24 samples, 95 images
  - Test: 27 samples, 109 images
  - No `grade + sample_id` group crosses train, validation, and test.

Historical V1 dataset:

- Processed dataset directory:
  - `data/processed/grading_forecast/berry_images_processed/`
- Class folders:
  - `grade_1/`, `grade_2/`, `grade_3/`
- Dataset size:
  - 360 images total (120 per class)
- Status:
  - Historical only. Do not use this directory for PP2 V2 training.

### 2.2 Forecasting dataset

Current PP2 V2 dataset:

- Full target series:
  - `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`
- Chronological split:
  - `data/processed/grading_forecast/price_v2/forecast_train.csv`
  - `data/processed/grading_forecast/price_v2/forecast_validation.csv`
  - `data/processed/grading_forecast/price_v2/forecast_test.csv`
- Target:
  - National + Grade 1 + average + farm_gate + weekly
- Target observations:
  - 232
- Split:
  - Train: 162 rows, 2021-02-22 to 2025-03-18
  - Validation: 34 rows, 2025-03-25 to 2025-11-25
  - Test: 36 rows, 2025-12-02 to 2026-08-18

Historical V1 dataset:

- Cleaned weekly price dataset:
  - `data/processed/grading_forecast/cleaned_price_data.csv`
- Forecast training series (National + Grade 1 + average):
  - `data/processed/grading_forecast/forecast_training_data.csv`
- Chronological split:
  - `data/processed/grading_forecast/train_forecast_data.csv`
  - `data/processed/grading_forecast/test_forecast_data.csv`
- Status:
  - Historical only for PP2 V2 forecasting. Do not use these files for Phase 3 V2 metrics.

---

## 3) Preprocessing Pipelines

### 3.1 Berry image preprocessing

- Uses letterbox resizing to keep aspect ratio and produce `224x224` RGB.
- Lightweight augmentation only (training-time):
  - random flip
  - small random rotation
  - small random zoom
  - brightness adjustment

### 3.2 Forecasting feature engineering

Features are **past-only** (no leakage) and aligned to predict **next week's** price:

- Lags:
  - `lag_1`, `lag_2`, `lag_3`
- Rolling stats (computed on shifted history):
  - `rolling_mean_3`, `rolling_std_3`
  - `rolling_mean_5`, `rolling_std_5`
- Time features:
  - `month`
  - `week_of_year` (ISO week)
- Change features:
  - `price_change_1w`
  - `price_change_pct_1w`

Target:

- `y = next_week_price`

---

## 4) Training Strategy (Reproducible + Maintainable)

### 4.1 Deterministic reproducibility

All training scripts fix random seeds and attempt deterministic execution:

- `PYTHONHASHSEED`
- Python `random`
- NumPy seed
- TensorFlow seed (`tf.keras.utils.set_random_seed`)
- scikit-learn `random_state`

### 4.2 Berry grading: two-stage transfer learning

Stage 1 (feature extractor):

- Freeze MobileNetV2 backbone
- Train only classification head
- Early stopping + model checkpoint + reduce LR on plateau

Stage 2 (fine-tuning):

- Unfreeze top ~20 MobileNetV2 layers
- Fine-tune with a low learning rate
- Early stopping to prevent overfitting

Class weights:

- Always computed from the training split counts (future-proofing for imbalance).

### 4.3 Forecasting model training

- Preserve chronological ordering (no shuffle)
- Train RandomForestRegressor baseline
- Optionally compare against a LinearRegression baseline (for academic discussion)

---

## 5) Evaluation Metrics

### 5.1 Berry grading evaluation

- Accuracy
- Precision / Recall / F1-score
- Confusion matrix + classification report

Completed PP2 V2 result:

- Test set: `data/processed/grading_forecast/berry_split_v2/test/`
- Test images: 109
- Accuracy: 0.8073
- Macro F1: 0.8068
- Weighted F1: 0.8076
- Grade 2 precision: 0.7805
- Grade 2 recall: 0.8889
- Grade 2 F1: 0.8312
- Confusion matrix:

```text
[[29,  3,  6],
 [ 1, 32,  3],
 [ 2,  6, 27]]
```

Artifacts:

- V2 metrics: `ml/grading_forecast/berry_grading/models/v2/berry_classifier_metrics.json`
- V2 confusion matrix: `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/confusion_matrix.png`
- V2 training curves: `ml/grading_forecast/berry_grading/evaluation/_outputs/v2/training_curves.png`
- V1 historical metrics: `ml/grading_forecast/berry_grading/models/berry_classifier_metrics.json`

### 5.2 Forecasting evaluation

- MAE
- RMSE
- MAPE
- R²

Explainability:

- Random Forest feature importance plot + numeric importances

Artifacts:

- `ml/grading_forecast/price_forecasting/models/forecast_metrics.json`
- Plots under `ml/grading_forecast/price_forecasting/evaluation/_outputs/` (generated locally)

Completed PP2 V2 forecasting result:

- Target: National + Grade 1 + average + farm_gate + weekly.
- Test prediction timestamps: 36.
- Naive Persistence MAE/RMSE/MAPE/R2: 16.4094 / 22.5208 / 0.8539 / 0.9045.
- RandomForest MAE/RMSE/MAPE/R2: 82.4179 / 88.4452 / 4.1679 / -0.4736.
- Decision: Naive Persistence is the stronger Phase 3 forecasting baseline on the V2 test period.

V2 artifacts:

- `ml/grading_forecast/price_forecasting/models/v2/forecast_model.joblib`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_features.json`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_metrics.json`
- `ml/grading_forecast/price_forecasting/models/v2/naive_persistence_metrics.json`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_model_metadata.json`
- `ml/grading_forecast/price_forecasting/models/v2/forecast_export_manifest.json`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/actual_vs_predicted.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2/feature_importances.png`

### 5.3 Phase 4 limited improvement evaluation

Berry grading limited improvement:

- Selected change: dropout 0.25 -> 0.35.
- Dataset/split: same `berry_split_v2` sample-level train/validation/test split.
- Test set: `data/processed/grading_forecast/berry_split_v2/test/`.
- Test images: 109.
- Accuracy: 0.8073.
- Macro F1: 0.8068.
- Weighted F1: 0.8076.
- Grade 2 precision/recall/F1: 0.7805 / 0.8889 / 0.8312.
- Decision: the dropout 0.35 experiment did not improve or worsen the saved headline metrics compared with the Phase 2 V2 baseline.

Berry Phase 4 artifacts:

- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_mobilenetv2_v2_phase4_best.keras`
- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_classifier_metrics.json`
- `ml/grading_forecast/berry_grading/models/v2_phase4/berry_model_metadata.json`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v2_phase4/confusion_matrix.png`

Forecasting limited improvement:

- Selected change: add `lag_4`, `lag_8`, and `lag_12`.
- Dataset/split: same V2 National Grade 1 average target and same 36 chronological test timestamps.
- Past-only feature logic preserved.

| Model | MAE | RMSE | MAPE | R2 |
| --- | ---: | ---: | ---: | ---: |
| Naive Persistence | 16.4094 | 22.5208 | 0.8539 | 0.9045 |
| Phase 3 RandomForest | 82.4179 | 88.4452 | 4.1679 | -0.4736 |
| Phase 4 Extended-Lag RandomForest | 78.1641 | 84.8622 | 3.9482 | -0.3566 |

Forecasting Phase 4 artifacts:

- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_model.joblib`
- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_features.json`
- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_metrics.json`
- `ml/grading_forecast/price_forecasting/models/v2_phase4/forecast_model_metadata.json`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/actual_vs_predicted.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/feature_importances.png`
- `ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4/residuals.png`

Phase 4 conclusion:

The berry dropout change did not improve the saved test metrics. The forecasting extended-lag change improved over the Phase 3 RandomForest baseline, but Naive Persistence remained the strongest forecasting result on the V2 test period.

---

## 6) Model Limitations (Must Be Stated)

Berry grading model limitations:

- Camera-based visual estimate only
- Does not measure chemical or lab-based quality indicators
- Not an official certification tool (no SLS certification claims)

Forecasting limitations:

- One-step ahead baseline forecasting (short-horizon)
- Uses only National + Grade 1 + average as the first academically justified baseline

---

## 7) Performance + Deployment Readiness

### 7.1 Inference performance measurements

The berry evaluation script records:

- average and p95 single-image inference latency (after warmup)
- model size on disk
- memory usage estimate (RSS delta)

### 7.2 Backend-friendly exports

- Berry grading is exported to ONNX for backend inference via `onnxruntime`
- Forecasting is exported as `joblib` (scikit-learn model)

Backend requirements:

- Lazy loading + caching to avoid per-request model reload
- Graceful fallback to baseline logic if artifacts are missing

---

## 8) Maintainability + MLOps Practices

### 8.1 Model versioning metadata

Each model stores a metadata JSON (v1 baseline) including:

- model name + version
- trained timestamp (UTC)
- seed / random_state
- image size / class list / feature spec
- dataset paths and split counts/date ranges
- git SHA (best effort)

### 8.2 Clear separation of concerns

- Training scripts are isolated under `ml/.../training/`
- Evaluation scripts under `ml/.../evaluation/`
- Inference scripts under `ml/.../inference/`
- Backend uses inference-only dependencies and avoids TensorFlow runtime.

---

## 9) How To Run (High Level)

Berry grading V2 baseline commands used for PP2:

Train:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/berry_grading/training/train_berry_classifier.py --train-dir data/processed/grading_forecast/berry_split_v2/train --val-dir data/processed/grading_forecast/berry_split_v2/val --output-dir ml/grading_forecast/berry_grading/models/v2 --model-filename berry_mobilenetv2_v2_best.keras --metadata-version v2 --batch-size 16 --stage1-epochs 15 --stage2-epochs 5 --stage1-lr 1e-3 --stage2-lr 1e-5 --patience 3
```

Evaluate on the untouched V2 test split:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/berry_grading/training/evaluate_berry_classifier.py --model ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.keras --models-dir ml/grading_forecast/berry_grading/models/v2 --data-dir data/processed/grading_forecast/berry_split_v2/test --output-dir ml/grading_forecast/berry_grading/evaluation/_outputs/v2 --use-full-data-dir --split-name test
```

Export ONNX:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/berry_grading/training/export_berry_model.py --model ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.keras --out ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx --metadata-out ml/grading_forecast/berry_grading/models/v2/onnx_metadata.json
```

CLI inference with explicit V2 model:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/berry_grading/inference/predict_berry_grade.py path\to\test.jpg --model ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.keras --class-names ml/grading_forecast/berry_grading/models/v2/class_names.json
```

Warning: the no-argument berry training/evaluation/export commands may still target historical V1 defaults. For PP2 V2 evidence, use the explicit V2 paths above.

Forecasting:

Prepared forecasting V2 commands:

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/training/train_forecast_model.py --train-csv data/processed/grading_forecast/price_v2/forecast_train.csv --validation-csv data/processed/grading_forecast/price_v2/forecast_validation.csv --test-csv data/processed/grading_forecast/price_v2/forecast_test.csv --target-csv data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv --models-dir ml/grading_forecast/price_forecasting/models/v2 --dataset-version v2 --artifact-version v2 --seed 42 --n-estimators 400 --min-samples-leaf 1 --n-jobs -1 --require-v2-paths
```

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/training/evaluate_forecast_model.py --target-csv data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv --test-csv data/processed/grading_forecast/price_v2/forecast_test.csv --models-dir ml/grading_forecast/price_forecasting/models/v2 --output-dir ml/grading_forecast/price_forecasting/evaluation/_outputs/v2 --split-name test --require-v2-paths
```

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/training/export_forecast_model.py --models-dir ml/grading_forecast/price_forecasting/models/v2 --require-v2-paths
```

```powershell
.\.venv\Scripts\python.exe ml/grading_forecast/price_forecasting/inference/predict_future_price.py --data-csv data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv --models-dir ml/grading_forecast/price_forecasting/models/v2 --require-v2-paths
```

Warning: Phase 3 V2 execution has already run. Rerun these commands only if intentionally reproducing the same baseline, and keep all outputs under explicit V2 paths.

---

## 10) Future Improvements

- Collect more images for better generalization across lighting and camera quality.
- Add probability calibration (temperature scaling) for confidence reliability.
- Export and validate TensorFlow Lite model for on-device mobile inference.
- Expand forecasting to district-level and multiple grades once dataset coverage supports it.
