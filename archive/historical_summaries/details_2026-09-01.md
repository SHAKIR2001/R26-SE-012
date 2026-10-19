Here is the simple version you can use for presentation/viva.

**Berry Grading Models**
You used **supervised learning** for berry grading, because the images had known labels: `Grade 1`, `Grade 2`, and `Grade 3`.

The main algorithm was a **CNN using transfer learning**, specifically **MobileNetV2**.

| Stage | Model | Accuracy | F1 Score | Notes |
|---|---:|---:|---:|---|
| PP1 / early baseline | MobileNetV2 | 77.78% | 74.47% weighted F1 | Used smaller 360-image dataset. Grade 2 recall was weak. |
| PP2 / current | MobileNetV2 transfer learning | 80.73% | 80.76% weighted F1, 80.68% macro F1 | Used improved dataset split and better evaluation. |
| Fine-tuned attempt | MobileNetV2 with dropout 0.35 | 80.73% | 80.76% weighted F1 | Same result as current baseline, so it did not replace the selected model. |

Current model per-grade results:

| Grade | Precision | Recall | F1 |
|---|---:|---:|---:|
| Grade 1 | 90.63% | 76.32% | 82.86% |
| Grade 2 | 78.05% | 88.89% | 83.12% |
| Grade 3 | 75.00% | 77.14% | 76.06% |

You chose the current MobileNetV2 approach because it gave better overall performance than the PP1 model, improved Grade 2 recognition, and is lightweight enough for mobile/offline use through TensorFlow Lite.

**Price Forecasting Models**
Price forecasting is **time-series regression**, not classification. So you do **not** report accuracy or F1 score for price forecasting. Instead, you report **MAE, RMSE, MAPE, and R²**.

| Stage | Model / Approach | MAE | RMSE | MAPE | R² |
|---|---:|---:|---:|---:|---:|
| PP1 baseline | Random Forest Regressor | 45.83 | 47.76 | - | -6.13 |
| PP2 ML baseline | Random Forest Regressor | 82.42 | 88.45 | 4.17% | -0.47 |
| Improved RF | Extended-lag Random Forest | 78.16 | 84.86 | 3.95% | -0.36 |
| Current selected | Naive persistence forecast | 16.41 | 22.52 | 0.85% | 0.90 |

The current selected price approach is **naive persistence**, where the next price is predicted using the most recent known market price. You chose it because it performed much better than Random Forest on the available test data. The price dataset is limited and stable, so a simple time-series baseline was more reliable than a more complex model.

**Fine-Tuning / Improvements Made**
For berry grading, you improved the model by:

- Moving from the smaller PP1 dataset to a larger V2 dataset.
- Using **sample-level splitting** to avoid data leakage.
- Using **MobileNetV2 transfer learning** with ImageNet weights.
- Training in two stages:
  - First, freeze the MobileNetV2 backbone.
  - Then, fine-tune the top layers using a lower learning rate.
- Adding image augmentation such as horizontal flip, small rotation, zoom, and brightness changes.
- Testing a dropout improvement, but it gave the same metrics, so the original V2 model stayed selected.

For price forecasting, you improved it by:

- Moving from older processed data to the larger raw market price dataset.
- Preserving chronological order for time-series evaluation.
- Testing Random Forest with lag and rolling-window features.
- Adding extra lag features such as `lag_4`, `lag_8`, and `lag_12`.
- Finally selecting naive persistence because it gave the best real test performance.

**Preprocessing Steps**
For berry grading:

- Images were organized by grade folders.
- Labels were taken from the folder names: `Grade 1`, `Grade 2`, `Grade 3`.
- Images were checked for readability and duplicates.
- Images were resized to `224 x 224`.
- Images were converted to RGB.
- MobileNetV2 preprocessing was applied inside the model.
- Data augmentation was used during training.

For price forecasting:

- Historical pepper price records were cleaned.
- The main target was **National Grade 1 average weekly farm-gate price**.
- Dates and price values were parsed and cleaned.
- Data was kept in time order.
- Missing weeks were documented, not artificially fabricated.
- Lag features and rolling average features were created from past prices only.

**Dataset Split**
For berry grading V2:

| Split | Samples | Images |
|---|---:|---:|
| Train | 117 samples | 467 images |
| Validation | 24 samples | 95 images |
| Test | 27 samples | 109 images |

The berry dataset was split by **physical sample**, not just by image. This is important because images from the same sample should not appear in both training and testing.

For price forecasting:

| Split | Date Range | Rows |
|---|---|---:|
| Train | 2021-02-22 to 2025-03-18 | 162 |
| Validation | 2025-03-25 to 2025-11-25 | 34 |
| Test | 2025-12-02 to 2026-08-18 | 36 |

The price dataset was split chronologically because it is time-series data. No shuffling was used.

Short answer: berry grading used **supervised CNN classification with MobileNetV2**. Price forecasting used **time-series regression**, and the final selected approach was **naive persistence** because it was the most accurate on the available test data.


Yes, you used **both ML and DL**, but for different parts.

**Berry grading:**  
You used **Deep Learning**, specifically a **CNN model: MobileNetV2 transfer learning**.  
Because the berry images are labeled as `Grade 1`, `Grade 2`, and `Grade 3`, this is also **supervised learning**.

So the correct wording is:

> For berry grading, I used supervised deep learning with a CNN-based MobileNetV2 transfer learning model.

**Price forecasting:**  
You used **Machine Learning / time-series forecasting**, not deep learning.  
You tested **RandomForestRegressor**, but the selected current approach is **Naive Persistence**, because it performed better on the V2 test data.

So the correct wording is:

> For price forecasting, I used supervised regression/time-series forecasting. I tested Random Forest, but selected Naive Persistence because it gave the lowest error on the test period.

Important: price forecasting does **not** have accuracy or F1 score because it is not classification. It uses `MAE`, `RMSE`, `MAPE`, and `R²`.

**Where This Is Stored**

Main reference docs:

- [model_training_phase.md](</d:/work/Year - 4/pepper/project/multimodal-pepper-ai-decision-support/docs/research/model_training_phase.md:30>)  
  Contains model details, MobileNetV2, RandomForest, preprocessing, training setup, evaluation metrics, and why Naive Persistence was selected.

- [EXPERIMENT_LOG.md](</d:/work/Year - 4/pepper/project/multimodal-pepper-ai-decision-support/docs/research/EXPERIMENT_LOG.md:54>)  
  Contains the experiment table from PP1 to now, including model names, datasets, metrics, and decisions.

- [PROJECT_STATUS.md](</d:/work/Year - 4/pepper/project/multimodal-pepper-ai-decision-support/docs/research/PROJECT_STATUS.md:631>)  
  Contains the final selected approach and summary decisions.

- [project_commands_guide.md](</d:/work/Year - 4/pepper/project/multimodal-pepper-ai-decision-support/docs/research/project_commands_guide.md:209>)  
  Contains training/evaluation commands and completed metric summaries.

Metric artifact files:

- [berry_classifier_metrics.json](</d:/work/Year - 4/pepper/project/multimodal-pepper-ai-decision-support/ml/grading_forecast/berry_grading/models/v2/berry_classifier_metrics.json>)  
  Stores current berry grading accuracy, precision, recall, and F1 scores.

- `ml/grading_forecast/price_forecasting/models/v2/`  
  Stores forecasting model artifacts and metrics for Random Forest / Naive Persistence evidence.

In short: your official explanation should come mainly from `docs/research/model_training_phase.md`, `docs/research/EXPERIMENT_LOG.md`, and `docs/research/PROJECT_STATUS.md`.
