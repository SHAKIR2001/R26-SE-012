# Full Research Progress Report

**Project:** Multimodal Pepper AI Decision Support System  
**Individual research component:** Berry Grading and Export Price Forecasting (IT22079268)  
**Report date:** 2026-10-06  
**Evidence basis:** Current repository source, Git history, saved datasets, model artifacts, experiment records, and a fresh backend test run.

## 1. Executive Summary

The project is a mobile decision-support system for black pepper farming. At the full-project level it combines pest detection, leaf disease analysis, berry disease analysis, berry quality grading, market-price forecasting, and recommendations. This report gives detailed coverage to the Berry Grading and Export Price Forecasting component because that is the component for which the repository contains a complete research plan, dataset audit, experiment log, saved metrics, integration evidence, and implementation history.

The individual component has progressed from an initial proof of concept to a defensible PP2 research pipeline and an implemented mobile/backend workflow:

- Berry grading uses supervised deep learning with MobileNetV2 transfer learning.
- The current selected berry model was trained on 671 images belonging to 168 physical samples and evaluated using a leakage-safe sample-level split.
- It achieved 80.73% test accuracy, 80.68% macro F1, and 80.76% weighted F1 on 109 untouched test images.
- Price forecasting was evaluated as a time-series regression problem. Random Forest models were compared with Naive Persistence on the same 36 chronological test dates.
- Naive Persistence was selected because it clearly outperformed both Random Forest versions: MAE 16.41 LKR/kg, RMSE 22.52 LKR/kg, MAPE 0.85%, and R2 0.9045.
- The selected berry model is integrated into the FastAPI backend through ONNX.
- The selected price method is integrated into the backend using the National Grade 1 average weekly farm-gate series.
- Recommendation rules combine predicted grade and forecast trend into actions such as sell, wait, monitor, or process locally.
- Optional Firestore result persistence is implemented with fail-safe behavior, but a real Firebase write has not been validated because credentials are not configured.
- An offline Flutter fallback is implemented using TensorFlow Lite. The mobile workflow defaults to offline analysis and retains an API mode.
- Grade-aware price display is implemented: Grade 1 uses the selected price series, Grade 2 uses an estimated discount, and Grade 3 is marked unavailable because the dataset contains no reliable Grade 3 price series.
- A newer 775-image berry dataset has been recreated and exported from Roboflow in YOLOv8 format as `data/raw/Pepper Berry Grading V3.yolov8`. It is structurally complete, but it defines a different two-class detection task and its current image-level split leaks physical sample groups across train, validation, and test. It has not yet replaced the leakage-safe V2 classification dataset or produced model results.

The research experimentation and PP2 documentation are complete. The system is not yet final-production validated. The remaining major work is Flutter formatting/analyzer/build/device validation, ONNX-versus-TFLite parity testing, correction of current backend test regressions, live Firebase validation, manual cross-component integration, broader field/external validation, and final documentation reconciliation.

## 2. Research Problem and Intended Contribution

The component addresses three connected decisions:

1. Estimate the visual grade of a harvested black pepper berry batch from a smartphone image.
2. estimate the short-term market price or price direction from historical market data; and
3. combine quality and market information into an understandable farmer-facing recommendation.

The intended user flow is:

1. A farmer captures or selects a berry image in the Flutter application.
2. The image is analyzed either locally with TensorFlow Lite or through the FastAPI backend.
3. The system returns Grade 1, Grade 2, or Grade 3, confidence, a quality score, and visual indicators.
4. The system obtains the selected short-term price estimate.
5. A rule-based decision layer generates a recommendation.
6. In backend mode, the result may be stored in Firestore when valid credentials are configured.

This is a visual decision-support tool, not an official SLS certification system. It cannot measure moisture, ash, volatile oil, piperine, fibre, bulk density, laboratory hygiene, or adulteration requirements.

## 3. Scope and Responsibility Boundary

### 3.1 Detailed component covered by this report

- Berry image collection, labeling, validation, preprocessing, and splitting.
- Berry grade classification model training and evaluation.
- Historical pepper-price cleaning and target construction.
- Forecast-model and baseline evaluation.
- Backend grading, forecasting, recommendation, error handling, artifact management, and optional persistence.
- Flutter grading/forecast screens, API mode, and offline TFLite mode.
- Research documentation, limitations, experiment logging, and reproduction commands.

### 3.2 Other project components visible in the repository

- Pest detection.
- Leaf disease detection and severity analysis.
- Berry disease detection and remediation advice.
- Shared scanner widgets and YOLO inference infrastructure.

These modules are implemented in the mobile source and were contributed by the wider team. The repository does not contain the same complete metric and experiment record for those components, so this report does not invent progress percentages or model-quality claims for them.

### 3.3 Repository folder structure

The following tree shows the meaningful source, research, data, and application folders. Generated folders such as `.venv`, `.dart_tool`, `build`, pytest caches, and Python `__pycache__` directories are intentionally omitted because they are local tooling output rather than research deliverables.

```text
multimodal-pepper-ai-decision-support/
├── backend/
│   ├── app/
│   │   ├── api/                       # FastAPI routers and HTTP endpoints
│   │   ├── core/                      # Configuration, constants, and security helpers
│   │   ├── db/                        # Firebase/Firestore initialization
│   │   ├── schemas/                   # Request and response data contracts
│   │   ├── services/
│   │   │   └── grading_forecast/      # Grading, forecast, recommendation, artifacts, storage
│   │   └── main.py                    # FastAPI application entry point
│   ├── tests/                         # Backend unit and integration-focused tests
│   └── requirements.txt               # Backend Python dependencies
├── data/
│   ├── annotations/                   # Versioned labels and dataset summaries
│   ├── interim/                       # Intermediate data-processing outputs
│   ├── processed/
│   │   └── grading_forecast/          # V1/V2 processed images, splits, manifests, price data
│   └── raw/                           # Original/local source datasets; detailed below
├── docs/
│   ├── api/                           # Postman/API documentation
│   ├── architecture/                  # System architecture material
│   ├── field_visit/                   # Field/data-collection documentation
│   ├── references/                    # Research and domain references
│   └── research/                      # Plans, logs, results, limitations, and this report
├── ml/
│   ├── berry_disease/                 # Wider-team berry-disease ML work
│   ├── grading_forecast/
│   │   ├── berry_grading/
│   │   │   ├── evaluation/            # Metrics, plots, and evaluation helpers
│   │   │   ├── feature_extraction/    # Berry visual-feature work
│   │   │   ├── inference/             # Standalone model prediction
│   │   │   ├── models/                # V1, V2, and Phase 4 model artifacts/metadata
│   │   │   ├── preprocessing/         # Dataset validation and preparation
│   │   │   └── training/              # Train, evaluate, ONNX, and TFLite export scripts
│   │   ├── dataset_v2/                # Combined V2 dataset preparation
│   │   └── price_forecasting/
│   │       ├── data/                  # Price cleaning and split construction
│   │       ├── evaluation/            # Forecast evaluation utilities
│   │       ├── inference/             # Current/future price prediction scripts
│   │       ├── models/                # RF, baseline metrics, and metadata
│   │       └── training/              # Baseline and Phase 4 training/evaluation
│   ├── leaf_disease/                  # Wider-team leaf-disease ML work
│   ├── pest_detection/                # Wider-team pest-detection ML work
│   └── shared/                        # Shared ML resources
├── mobile/
│   ├── assets/
│   │   ├── data/                      # Bundled class names, prices, and metrics
│   │   ├── images/                    # Application images/logo
│   │   └── models/                    # Bundled TFLite models
│   ├── lib/
│   │   ├── core/                      # Theme and shared application services
│   │   ├── features/
│   │   │   ├── berry_disease/         # Berry-disease mobile flow
│   │   │   ├── grading_forecast/      # Models, services, and screens for this component
│   │   │   ├── home/                  # Main dashboard/navigation
│   │   │   ├── leaf_disease/          # Leaf-disease mobile flow
│   │   │   ├── pest_detection/        # Pest-detection mobile flow
│   │   │   ├── plant_health/          # Combined plant-health flow
│   │   │   └── recommendations/       # AI analysis and remediation UI/services
│   │   ├── shared/                    # Shared scanner models and widgets
│   │   └── main.dart                  # Flutter application entry point
│   ├── test/                          # Flutter unit and widget tests
│   └── android|ios|web|windows|...    # Flutter platform projects
├── notebooks/
│   ├── eda/                           # Exploratory data analysis
│   ├── experiments/                   # Research notebooks/experiments
│   └── forecasting/                   # Forecast-oriented notebooks
├── scripts/
│   ├── preprocessing/                 # General preprocessing helpers
│   ├── setup/                         # Project setup helpers
│   └── utilities/                     # General utilities
├── README.md                          # Project overview
└── details.md                         # Concise model/result explanation
```

Key grading/forecast backend service files:

```text
backend/app/services/grading_forecast/
├── artifact_service.py               # Resolves/downloads required runtime artifacts
├── feature_extractor.py              # Extracts visual quality indicators
├── grading_service.py                # Runs selected V2 ONNX berry grading
├── image_preprocessor.py             # Decodes and prepares uploaded images
├── price_forecast_service.py         # Naive Persistence and grade-price behavior
├── recommendation_service.py         # Grade/trend decision table
└── result_storage_service.py         # Optional Firestore result persistence
```

Key grading/forecast mobile structure:

```text
mobile/lib/features/grading_forecast/
├── models/
│   └── grading_forecast_result.dart  # Shared result/JSON models
├── screens/
│   ├── grading_forecast_home_screen.dart
│   ├── berry_capture_screen.dart
│   ├── processing_screen.dart
│   ├── berry_quality_result_screen.dart
│   └── price_forecast_screen.dart
└── services/
    ├── grading_forecast_analysis_service.dart  # Offline/API mode router
    ├── grading_forecast_api_service.dart       # FastAPI client
    └── offline_grading_forecast_service.dart   # TFLite and bundled-price path
```

### 3.4 Raw dataset folder structure

The raw data area contains local source datasets for several project components:

```text
data/raw/
├── berry_images/                     # Original physical-sample berry hierarchy
├── leaf_images/                      # Leaf-disease source images
├── market_prices/                    # Pepper price source files and legacy data
├── Pepper Berry Grading V3.yolov8/   # New Roboflow YOLOv8 export
└── pest_images/                      # Pest-detection source images
```

Both `berry_images/` and `Pepper Berry Grading V3.yolov8/` are ignored by Git because they are large local raw datasets. The report and versioned summary/manifest artifacts should hold the reproducible audit evidence needed by other researchers.

#### Original physical-sample berry hierarchy

The current source hierarchy preserves the identity needed for a group-aware split:

```text
data/raw/berry_images/
├── grade_1/                          # 56 physical samples, 224 images
│   ├── sample_001/
│   │   ├── <view_1>.jpg
│   │   ├── <view_2>.jpg
│   │   └── ...
│   ├── sample_002/
│   └── ... sample_056/
├── grade_2/                          # 56 physical samples, 224 images
│   ├── sample_001/
│   └── ... sample_056/
└── grade_3/                          # 82 physical samples, 327 images
    ├── sample_001/
    └── ... sample_082/
```

Summary:

| Source folder | Physical sample folders | Images |
| --- | ---: | ---: |
| `grade_1` | 56 | 224 |
| `grade_2` | 56 | 224 |
| `grade_3` | 82 | 327 |
| **Total** | **194** | **775** |

The `sample_###` directory is the grouping key. All images under one sample directory are alternate views of the same physical berry sample and must remain in the same train, validation, or test partition.

#### New V3 Roboflow YOLOv8 export structure

```text
data/raw/Pepper Berry Grading V3.yolov8/
├── data.yaml                         # YOLO dataset configuration and two class names
├── README.dataset.txt                # Roboflow project URL and CC BY 4.0 license
├── README.roboflow.txt               # Export date, size, format, processing statement
├── train/
│   ├── images/                       # 543 JPEG images
│   └── labels/                       # 543 matching YOLO text labels
├── valid/
│   ├── images/                       # 155 JPEG images
│   └── labels/                       # 155 matching YOLO text labels
└── test/
    ├── images/                       # 77 JPEG images
    └── labels/                       # 77 matching YOLO text labels
```

Each YOLO label file has the same base filename as its image:

```text
train/images/20260508_152150_jpg.rf.<roboflow-id>.jpg
train/labels/20260508_152150_jpg.rf.<roboflow-id>.txt
```

Each label contains one normalized YOLO bounding-box row:

```text
<class_id> <x_center> <y_center> <width> <height>
```

The current `data.yaml` defines:

```yaml
nc: 2
names: ['Grade 1', 'Grade 2']
```

Its stored split paths are `../train/images`, `../valid/images`, and `../test/images`, while the actual split folders are direct children of the directory containing `data.yaml`. These paths should be checked with the chosen YOLO training command and corrected to `train/images`, `valid/images`, and `test/images` or an explicit dataset `path` if the trainer resolves them relative to the YAML location.

The raw physical-sample hierarchy is the authoritative source for rebuilding a leakage-safe V3 split. The flattened Roboflow filenames retain the original image name but not the `grade/sample_id` directory in their visible export path, which is why the current random image-level export separated alternate views of the same sample.

## 4. Development and Research Timeline

### Stage A: Project foundation — 6 to 7 April 2026

- Initialized the repository and core directory structure.
- Defined the high-level multimodal research concept.
- Documented the proposed Flutter, FastAPI, ML, data, and cloud architecture.
- Defined the main workflow from mobile image capture to model inference and decision support.

### Stage B: First working application and V1 component — 5 to 13 May 2026

- Initialized the Flutter application and platform projects.
- Created the FastAPI backend and grading/forecast API structure.
- Implemented image preprocessing and visual feature extraction.
- Added berry grading, price forecasting, recommendation, and result-storage service layers.
- Prepared the first 360-image berry dataset, balanced at 120 images for each grade.
- Trained the V1 MobileNetV2 berry classifier.
- Trained and evaluated the V1 RandomForest price model.
- Added ONNX export and inference support.
- Added backend tests, a Postman collection, CORS support, and metric documentation.
- Integrated the grading/forecast UI and backend client into Flutter.

V1 established a working end-to-end baseline, but its research methodology was limited. The berry evaluation used the smaller dataset and did not have the later physical-sample leakage control. The price Random Forest generalized poorly.

### Stage C: Mobile dashboard and shared project integration — July to August 2026

- Expanded the Flutter home/dashboard experience.
- Added navigation to crop-analysis functions.
- Integrated the wider team's pest, leaf disease, and berry disease screens.
- Added shared scanner, detection overlay, scan-result widgets, and YOLOv8 TFLite support.
- Added theme management, app assets, tests, and AI-assisted analysis paths used by other project components.

### Stage D: PP2 recovery plan and V2 dataset preparation — 25 to 27 August 2026

- Audited the earlier datasets, scripts, models, and runtime assumptions.
- Created the PP2 master plan, execution checklist, experiment log, results document, status document, and limitations document.
- Preserved V1 artifacts instead of overwriting them.
- Created safe V2-specific script arguments and artifact directories.
- Rebuilt the berry dataset as a physical-sample-aware V2 dataset.
- Rebuilt the price dataset as a chronological V2 time series with explicit coverage and gap analysis.

### Stage E: V2 model training and evaluation — 27 August 2026

- Trained and evaluated the V2 MobileNetV2 baseline.
- Exported the selected V2 berry model to ONNX.
- Trained and evaluated the V2 RandomForest price baseline.
- Evaluated Naive Persistence on the identical test timestamps.
- Performed one controlled improvement experiment for each subproblem.
- Selected models based on test evidence instead of model complexity.

### Stage F: Integration, hardening, and persistence — 28 to 30 August 2026

- Validated the backend API path.
- Audited differences between research artifacts and application runtime behavior.
- Replaced the legacy berry runtime model with the selected V2 ONNX artifact.
- Replaced demo forecast behavior with the selected Naive Persistence method.
- Validated the recommendation rule table with real runtime outputs.
- Hardened image upload handling and service error responses.
- Fixed Flutter multipart compatibility by validating uploaded image bytes rather than trusting MIME values alone.
- Implemented optional Firestore result-history persistence with non-blocking failure behavior.
- Diagnosed berry prediction and identical-price concerns without changing the trained results.

### Stage G: Offline mobile support and grade-aware price presentation — 31 August to 1 September 2026

- Exported the selected V2 Keras model to TensorFlow Lite.
- Bundled model metadata, class names, the Grade 1 price series, and forecast metrics in Flutter assets.
- Added a mode router: offline TFLite by default and backend API through `PEPPER_ANALYSIS_MODE=api`.
- Updated grading/forecast screens to consume the shared analysis result contract.
- Removed manual grade selection from the price page.
- Added one predicted market price based on the image-predicted grade.
- Kept Grade 3 price unavailable because no reliable Grade 3 price history exists.

### Stage H: Berry Grading V3 dataset recreation — 24 September to 6 October 2026

- Expanded the current raw berry collection to 775 images from 194 physical sample groups.
- Exported the images and bounding-box annotations from Roboflow in YOLOv8 format.
- Created train, validation, and test folders with matching image/label files.
- Changed the exported learning task from the earlier three-class whole-image classification problem to a two-class object-detection problem.
- Performed the repository audit recorded in this report. File integrity and annotation syntax passed, but the audit identified class-definition incompatibility with V2 and substantial physical-sample leakage across the Roboflow splits.
- No V3 training, evaluation, export, or application integration artifact was found. V3 is therefore a dataset-preparation milestone, not a new model result.

## 5. Step-by-Step Research Work Completed

### Phase 0 — Repository and research audit

Completed actions:

- Mapped the research requirements to source code and artifacts.
- Identified V1 datasets, models, scripts, and integration paths.
- Identified risks: data leakage, weak price target definition, stale runtime artifacts, silent demo fallbacks, and incomplete validation evidence.
- Established a rule that saved research metrics must not be replaced by unverified runtime observations.

Outcome: a traceable plan for producing PP2 evidence without losing the earlier work.

### Phase 1 — Berry and price dataset V2 preparation

Berry V2 work:

- Inspected 671 readable images from 168 physical sample groups.
- Retained 224 Grade 1, 224 Grade 2, and 223 Grade 3 images.
- Verified that there were no unreadable images, missing files, duplicate paths, or duplicate-content groups in the saved audit.
- Preserved unusual but readable samples and documented five samples that did not contain exactly four images.
- Recorded image dimensions, aspect ratios, camera models, and EXIF orientations.
- Split by `grade + sample_id`, not randomly by individual image, to prevent images of the same physical sample appearing in multiple splits.
- Used seed 42 for deterministic preparation.

Berry V2 split:

| Split | Physical samples | Images |
| --- | ---: | ---: |
| Train | 117 | 467 |
| Validation | 24 | 95 |
| Test | 27 | 109 |
| Total | 168 | 671 |

Price V2 work:

- Preserved and cleaned 7,742 source rows.
- Standardized date, district, grade, price type, and price fields.
- Selected National Grade 1 average weekly farm-gate price as the primary target.
- Retained Grade 2 observations for analysis but did not pretend that sparse missing values were zero.
- Produced 232 primary-target observations from 22 February 2021 through 18 August 2026.
- Documented missing intervals rather than fabricating a complete weekly calendar.
- Found 12 gaps over eight days; the largest was 316 days between the isolated 2021 observation and the 2022 sequence.
- Created chronological 70/15/15 observed-row splits with no shuffling.

Price V2 split:

| Split | Rows | Date range |
| --- | ---: | --- |
| Train | 162 | 2021-02-22 to 2025-03-18 |
| Validation | 34 | 2025-03-25 to 2025-11-25 |
| Test | 36 | 2025-12-02 to 2026-08-18 |

### Berry Grading V3 — Recreated YOLOv8 dataset

Dataset location and provenance:

- Path: `data/raw/Pepper Berry Grading V3.yolov8`.
- Roboflow project: `pepper-berry-grading-v3`.
- Export date recorded by Roboflow: 24 September 2026 at 08:46 GMT.
- License recorded in the export: CC BY 4.0.
- Format: YOLOv8 object-detection labels.
- Roboflow states that no preprocessing or augmentation was applied.

V3 file and split summary:

| Split | Images | Label files | Share | V3 Grade 1 | V3 Grade 2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 543 | 543 | 70.06% | 322 | 221 |
| Validation | 155 | 155 | 20.00% | 81 | 74 |
| Test | 77 | 77 | 9.94% | 45 | 32 |
| Total | 775 | 775 | 100% | 448 | 327 |

Structural audit results:

- All 775 images are readable JPEG files.
- Image dimensions are 630 at 4000 x 3000, 141 at 4080 x 3060, and 4 at 8160 x 6120.
- All 775 images have a matching label file and all label files have a matching image.
- No empty labels, malformed rows, invalid class IDs, or out-of-range normalized coordinates were found.
- No exact duplicate image hashes were found inside the V3 export.
- There is exactly one bounding box per image: 775 annotated objects in total.
- Bounding boxes are generally large: average normalized width 0.8505 and height 0.8325; 355 boxes cover at least 80% of both image dimensions.
- The class distribution is moderately imbalanced: 448 V3 Grade 1 objects (57.81%) and 327 V3 Grade 2 objects (42.19%).

Important class-definition finding:

Hash comparison confirmed that the 775 V3 images are exactly the same files as the 775 images currently under `data/raw/berry_images`; no V3 image is new or byte-modified relative to that current raw folder. However, the V3 labels do not preserve the previous three-class definition:

| Current raw source folder | Images | V3 class assignment |
| --- | ---: | --- |
| `grade_1` | 224 | Class 0, named `Grade 1` |
| `grade_2` | 224 | Class 0, named `Grade 1` |
| `grade_3` | 327 | Class 1, named `Grade 2` |

Therefore, V3 collapses the earlier Grade 1 and Grade 2 source folders into the new V3 `Grade 1`, and renames the earlier Grade 3 source group as the new V3 `Grade 2`. The repository does not currently document the research or domain rationale for this relabeling. This makes V3 incompatible with the current backend/mobile contract, which expects three outputs named Grade 1, Grade 2, and Grade 3.

Important split-leakage finding:

- The current raw hierarchy identifies 194 physical sample groups: 56 old Grade 1, 56 old Grade 2, and 82 old Grade 3 groups.
- The Roboflow split was performed at individual-image level rather than keeping all views of one physical sample together.
- 146 of 194 physical sample groups cross split boundaries.
- Those crossing groups contain 584 of the 775 images.
- Only 48 sample groups are exclusive to one split, and all 48 are train-only.
- Consequently, validation and test contain alternate views of physical samples also represented elsewhere, mainly in training.

This leakage can make validation/test performance look better than real performance on unseen berry samples. Before any V3 model result is treated as research evidence, V3 must be regenerated with a group-aware split using the original `grade/sample_id` identity. The existing V2 metrics remain the selected defensible results until that correction and a new experiment are completed.

### Phase 2 — Berry grading V2 baseline

Model and training design:

- MobileNetV2 transfer learning with ImageNet initialization.
- Input: 224 x 224 RGB.
- Classification head: global average pooling, dropout, and three-class softmax.
- Augmentation: horizontal flip, small rotation, zoom, and brightness adjustment.
- Loss: sparse categorical cross-entropy.
- Optimizer: Adam.
- Batch size: 16.
- Seed: 42.
- Stage 1: frozen backbone, maximum 15 epochs, learning rate 0.001, patience 3; 14 epochs completed.
- Stage 2: limited fine-tuning, maximum 5 epochs, learning rate 0.00001, patience 2; all 5 epochs completed.
- Best saved checkpoint: stage 2 epoch 5, validation loss 0.52487 and validation accuracy 0.74737.

The model was evaluated once on the untouched 109-image test split and exported to ONNX under a V2-specific path.

### Phase 3 — Price forecasting V2 baseline

The target was a one-step-ahead estimate for the National Grade 1 average weekly farm-gate price.

RandomForest configuration:

- 400 trees.
- Random seed 42.
- Past-only features: lags 1, 2, and 3; rolling means and standard deviations over 3 and 5 observations; month; week of year; one-observation price change; and percentage change.
- Chronological evaluation with no shuffle.
- Features were constructed from observations before each prediction date.

Baseline comparison:

- Naive Persistence predicts the next value as the most recent observed price.
- Both methods were compared on the same 36 test timestamps.
- The simple baseline substantially outperformed Random Forest, so it was selected honestly as the runtime method.

### Phase 4 — Limited model improvements

Berry experiment:

- Changed only dropout from 0.25 to 0.35.
- Kept dataset, split, and other core settings aligned with the V2 baseline.
- Obtained identical saved headline test metrics.
- Decision: do not replace the selected Phase 2 model.

Forecast experiment:

- Added lag 4, lag 8, and lag 12 to the RandomForest feature set.
- The extended-lag model improved all four regression metrics relative to the Phase 3 RandomForest.
- It still remained much worse than Naive Persistence.
- Decision: record it as a useful controlled experiment, but keep Naive Persistence selected.

### Phase 5 — Initial backend integration validation

- Started the FastAPI service.
- Called health, price forecast, grade-only, and analyze endpoints.
- Confirmed HTTP 200 responses during the recorded validation pass.
- Recorded an important limitation: at that time runtime grading still used the legacy/root ONNX model and forecasting returned a demo baseline.
- Kept this evidence separate from the later V2 runtime integration.

### Phase 6 — PP2 evidence and documentation

- Consolidated dataset evidence, experiment tables, metrics, decisions, limitations, speaking points, and reproduction commands.
- Explicitly documented that this phase organized existing evidence; it did not rerun models or fabricate missing results.

### Phase 7 — Existing implementation audit

- Traced Flutter screens and API calls through FastAPI routes and service layers.
- Audited model paths, fallback behavior, recommendation rules, storage behavior, schemas, configuration, and response handling.
- Identified the exact work required to align research artifacts with runtime behavior.

### Phase 8 — V2 berry runtime integration

- Updated backend grading to load `BERRY-V2-MNV2` from the selected V2 ONNX path.
- Preserved the API response contract.
- Prevented missing V2 artifacts from silently loading the legacy model.
- Service validation returned Grade 1 with confidence 0.88 for the recorded V2 test image.

### Phase 9 — Forecast runtime decision and integration

- Checked whether the application requirement mandated a trained RandomForest artifact. It did not.
- Integrated Naive Persistence because it was the strongest validated V2 method.
- Runtime source became `national_grade1_average_weekly.csv`.
- Recorded output was current price 1886, predicted price 1886, stable trend, MAE 16.4094, and RMSE 22.5208.
- Missing or malformed data returns `forecast_unavailable` rather than a fabricated demo value.

### Phase 10 — Recommendation logic validation

- Validated the grade-and-trend rule table.
- Tested representative Grade 1, Grade 2, and Grade 3 cases across upward, stable, and downward trends.
- Tested missing optional fields and invalid request schemas.
- Verified a real runtime chain using `BERRY-V2-MNV2` plus `naive_persistence`, producing Grade 1, stable trend, and `SELL_EXPORT` in the recorded case.
- Did not change the business-rule table because this phase was validation.

### Phase 11 — Backend reliability and error handling

- Added validation for missing, empty, corrupt, unsupported, and oversized uploads.
- Retained the 10 MB upload limit.
- Accepted valid JPEG, PNG, and WEBP content even when Flutter sends no useful MIME type or `application/octet-stream`.
- Used Pillow decoding as the authoritative content check.
- Returned explicit failures when the selected grading model is unavailable.
- Returned `forecast_unavailable` for bad forecast data.
- Converted unexpected failures into safe JSON/HTTP errors.

### Phase 12 — Firebase persistence

- Implemented application-level result history in `grading_forecast_results`.
- Stored generated analysis/document ID, timestamp, runtime identifiers, grading, forecast, recommendation, and supporting metadata.
- Avoided storing raw image bytes.
- Validated mocked success, initialization failure, write failure, serialization failure, and unconfigured Firebase behavior.
- Kept inference usable when storage is unavailable: the response returns `saved_to_firebase: false` instead of discarding the analysis.
- Did not configure or commit credentials.

### Phase 12.5 — Runtime diagnostic investigation

Berry investigation:

- Compared direct ONNX inference with backend service inference on nine V2 test images.
- Both paths agreed on all nine predictions, so no ONNX/backend class-order disagreement was found.
- Diagnostic accuracy was 6/9: Grade 1 was 3/3, Grade 2 was 0/3, and Grade 3 was 3/3.
- This small diagnostic does not replace the official 109-image test result.
- Confirmed a preprocessing concern recorded for later correction: the training input path and runtime letterbox path were not treated consistently in the documented diagnostic.

Forecast investigation:

- Confirmed runtime uses one National Grade 1 series.
- Confirmed the selected method is Naive Persistence.
- Latest recorded Grade 1 price is 1886.14 LKR/kg on 18 August 2026, displayed as 1886.
- Explained why the earlier single-series implementation produced identical forecast values for all predicted grades.

### Phase 13 — Offline mobile TensorFlow Lite fallback

- Converted the selected V2 Keras model to TensorFlow Lite without retraining.
- Verified saved tensor metadata: input `[1, 224, 224, 3]`, float32 RGB values in the documented 0–255 range, and output `[1, 3]`.
- Bundled class names and price artifacts with the Flutter app.
- Added an analysis service that defaults to offline inference.
- Preserved API mode through `--dart-define=PEPPER_ANALYSIS_MODE=api`.
- Kept offline storage explicitly false because Firestore persistence remains a backend function.
- Implemented grade-aware display logic, while acknowledging that the Grade 2 value is an adjustment rather than an independently trained Grade 2 forecast.

## 6. Current Results

V3 currently has no training or evaluation result. All numerical model results below remain V1/V2 evidence and must not be attributed to V3.

### 6.1 Berry grading results

| Experiment | Dataset/evaluation | Accuracy | Macro F1 | Weighted F1 | Decision |
| --- | --- | ---: | ---: | ---: | --- |
| V1 MobileNetV2 | 360-image legacy dataset | 77.78% | 74.47% | 74.47% | Historical only |
| V2 MobileNetV2 | 109-image untouched, sample-separated test set | 80.73% | 80.68% | 80.76% | Selected |
| V2 dropout 0.35 | Same V2 test set | 80.73% | 80.68% | 80.76% | Did not replace baseline |

Selected V2 per-class results:

| Class | Precision | Recall | F1 | Test support |
| --- | ---: | ---: | ---: | ---: |
| Grade 1 | 90.63% | 76.32% | 82.86% | 38 |
| Grade 2 | 78.05% | 88.89% | 83.12% | 36 |
| Grade 3 | 75.00% | 77.14% | 76.06% | 35 |

V2 confusion matrix, where rows are actual and columns are predicted:

| Actual / predicted | Grade 1 | Grade 2 | Grade 3 |
| --- | ---: | ---: | ---: |
| Grade 1 | 29 | 3 | 6 |
| Grade 2 | 1 | 32 | 3 |
| Grade 3 | 2 | 6 | 27 |

Interpretation:

- V2 improved overall accuracy and especially Grade 2 recall compared with V1.
- Grade 3 has the weakest V2 class F1.
- Grade 1 precision is strong, but some actual Grade 1 images are confused with Grade 3.
- The test set is still small, so performance on different phones, lighting, backgrounds, and farms is not proven.

### 6.2 Price forecasting results

| Experiment | MAE (LKR/kg) | RMSE (LKR/kg) | MAPE | R2 | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| V1 RandomForest | 45.83 | 47.76 | 2.29% | -6.1315 | Historical only |
| V2 RandomForest | 82.42 | 88.45 | 4.17% | -0.4736 | Not selected |
| V2 extended-lag RandomForest | 78.16 | 84.86 | 3.95% | -0.3566 | Improved RF, still not selected |
| V2 Naive Persistence | 16.41 | 22.52 | 0.85% | 0.9045 | Selected |

Interpretation:

- The RandomForest models fit training data well but generalized poorly to the future test period.
- Extended lags provided a modest improvement but did not solve the generalization problem.
- On the available stable and limited time series, the simple persistence method was more reliable.
- The result supports selecting the simpler method; it does not prove that persistence will remain best on larger or more volatile datasets.

### 6.3 Runtime price behavior

- Grade 1: uses the National Grade 1 Naive Persistence estimate.
- Grade 2: uses a gap-adjusted estimate derived from observed Grade 1/Grade 2 data; this is not a separately trained Grade 2 forecast.
- Grade 3: returns price unavailable because there is no reliable Grade 3 series.

Current documentation and the bundled mobile adjustment artifact need reconciliation. Older status text describes a rounded 100 LKR/kg discount from the latest 86.14 LKR/kg gap, while the current mobile asset stores 113 LKR/kg. This discrepancy must be resolved before the value is presented as final research evidence.

## 7. Current Implemented System

### Backend

Implemented endpoints include:

- `GET /api/v1/grading-forecast/health`
- `POST /api/v1/grading-forecast/grade-only`
- `GET /api/v1/grading-forecast/price-forecast`
- `POST /api/v1/grading-forecast/analyze`
- `POST /api/v1/grading-forecast/recommend`

Implemented backend services include:

- image validation and preprocessing;
- visual feature extraction;
- ONNX berry grading;
- selected Naive Persistence price forecasting;
- grade-aware price adjustment/unavailable behavior;
- rule-based recommendation generation;
- runtime artifact resolution/download support;
- optional Firestore result storage; and
- safe startup and runtime failure behavior.

### Mobile application

Implemented grading/forecast screens include:

- feature home screen;
- image capture/selection screen;
- processing screen;
- berry quality result screen; and
- predicted market price screen.

The mobile component includes:

- backend API client with fallback URL/retry handling;
- offline TFLite grading and local forecast path;
- result models aligned with the backend JSON contract;
- a mode router for offline or API execution; and
- bundled model/data assets.

### Research and reproducibility assets

- V1 and V2 datasets and summaries.
- Deterministic preparation scripts.
- Training, evaluation, export, and inference scripts.
- Keras, ONNX, TensorFlow Lite, and joblib artifacts where applicable.
- Saved metrics, metadata, class mappings, plots, and training histories.
- Postman collection and command guide.
- Master plan, checklist, experiment log, results, limitations, integration evidence, and status documentation.

## 8. Validation Status as of 6 October 2026

### Confirmed by saved evidence

- V2 dataset preparation and leakage-safe berry splitting.
- Chronological price splitting.
- V1, V2, and limited-improvement metric artifacts.
- ONNX and TensorFlow Lite artifacts exist.
- V2 ONNX is wired into the backend source.
- Naive Persistence is wired into the backend source.
- Grade-aware price behavior exists in backend and mobile source.
- Optional Firestore storage and fail-safe behavior exist in source.
- Offline/API analysis routing exists in Flutter source.
- V3 contains 775 readable images, 775 matching YOLO labels, valid two-class annotation syntax, and no exact duplicate image content.
- V3 is not leakage-safe: 146 of 194 physical sample groups cross its current splits.

### Fresh verification performed for this report

The backend test suite was run with a repository-local pytest temporary directory:

- 36 tests collected.
- 33 passed.
- 3 failed.

The failures are:

1. `test_grading_service_probability_weighted_quality_score`: the test mock returns the old three-item predictor tuple, while the current service expects five items including model ID and path.
2. `test_runtime_forecast_applies_grade_2_gap_adjustment`: the test expects the 113 LKR/kg default discount, while the current service derives/returns a rounded 100 LKR/kg adjustment for its fixture.
3. `test_storage_service_handles_initialization_failure_safely`: the test calls grading with no image, but the hardened grading service now correctly requires image bytes.

These appear to be test/contract drift around newer implementation behavior, but the Grade 2 discount disagreement is also a documentation and product-definition issue and should be decided explicitly before merely updating a test.

The current environment contains Flutter and Dart commands, but a fresh read-only formatting check (`dart format --output=none --set-exit-if-changed lib test`) produced no output after 60 seconds and had to be stopped. This reproduces the previously documented toolchain timeout, so formatting, analysis, test, build, and device success must remain marked as pending rather than assumed.

### Not currently proven

- Successful Flutter formatter run.
- Successful Flutter analyzer run.
- Successful APK build for the current branch.
- Real-device or emulator grading/forecast flow.
- Numerical parity between Flutter TFLite and backend ONNX on a fixed image set.
- Hosted-backend API mode without timeout or rate-limit problems.
- Live Firestore write using real credentials.
- Full integration with all other team components.
- Field testing with new farms, phones, lighting, and backgrounds.
- Domain-expert validation of grading labels and recommendation rules.
- Production security, authentication, rate limiting, monitoring, and deployment readiness.

## 9. What Is Still Left To Do

### Priority 1 — Reconcile current correctness issues

1. Decide and document the Grade 2 adjustment method.
   - Confirm whether the intended value is latest-gap rounded to 100, mean/other statistic producing 113, or another agronomically supported rule.
   - Make backend, mobile asset, tests, and all research documents use the same definition.
2. Update the two stale backend tests to the current hardened service contracts, provided those contracts are confirmed as intended.
3. Rerun all backend tests and require a clean result.
4. Reconcile status dates and Phase 13 wording across README, status, results, experiment log, checklist, and command guide.

### Priority 1A — Correct and define the V3 research dataset

1. Decide and document the intended grading taxonomy:
   - retain the existing three-class Grade 1/2/3 classification contract; or
   - formally define the new two-class V3 task and explain why old Grade 1+2 become new Grade 1 and old Grade 3 becomes new Grade 2.
2. Confirm whether the research objective is whole-image classification, object detection/localization, or a detection-then-classification pipeline.
3. Regenerate train/validation/test splits at physical `grade/sample_id` group level.
4. Keep every view of the same physical berry sample in exactly one split.
5. Preserve an untouched, sample-independent test set.
6. Recheck class balance and annotation boxes after the new split.
7. Create a versioned V3 manifest and dataset audit JSON in the repository rather than relying only on the ignored raw export.
8. Only then train a V3 baseline and compare it fairly against V2; do not compare incompatible two-class detection metrics directly with three-class classification accuracy/F1.

### Priority 2 — Validate the offline mobile implementation

1. Run Dart formatter.
2. Run Flutter analyzer.
3. Run Flutter unit/widget tests.
4. Build a debug APK.
5. Run the app on an emulator or Android device.
6. Test gallery/camera input for Grade 1, Grade 2, Grade 3, corrupt input, and unsupported input.
7. Verify navigation, loading, success, unavailable-price, and error states.
8. Capture screenshots and logs as evidence.

### Priority 3 — Perform model parity and preprocessing validation

1. Select a fixed, balanced sample of V2 test images.
2. Run the same bytes through Keras, ONNX/backend, and TFLite/mobile.
3. Compare class order, predicted class, probabilities, preprocessing, quality score, and latency.
4. Resolve the documented direct-resize versus letterbox inconsistency.
5. Re-evaluate the selected model after the preprocessing path is made consistent.
6. Do not replace the official saved metrics without a clearly versioned new experiment.

### Priority 4 — Complete API and persistence validation

1. Validate Flutter API mode against a stable reachable backend.
2. Test all API endpoints using valid and invalid requests.
3. Configure Firebase credentials outside source control.
4. Perform and read back a real Firestore write.
5. Confirm collection name, document schema, timestamps, and failure behavior.
6. Decide whether results need authenticated user ownership and retrieval/history UI.

### Priority 5 — Complete research validation

1. Collect more physical berry samples across farms, devices, lighting conditions, seasons, and backgrounds.
2. Obtain domain-expert review of Grade 1/2/3 labels.
3. Add external or field validation data that was never used during model development.
4. Investigate Grade 1-to-Grade 3 and Grade 3-to-Grade 2 confusion.
5. Repeat experiments with clearly versioned datasets and untouched external testing.
6. Expand price data and consider additional features such as weather, exchange rate, export volume, and international prices.
7. Use walk-forward/time-series validation rather than relying only on one 36-row final window.
8. Compare additional forecast methods only after the data foundation is improved.
9. Have agricultural/business stakeholders review recommendation thresholds and wording.

### Priority 6 — Final integrated project validation

1. Merge and test pest, leaf disease, berry disease, and grading/forecasting flows together.
2. Confirm shared navigation, theme, camera permissions, model loading, and memory use.
3. Test offline and online failure modes.
4. Validate performance on the target Android hardware.
5. Finalize the dissertation/report tables, figures, screenshots, architecture, limitations, and reproducibility appendix.

## 10. Key Limitations That Must Remain in the Final Research Report

- Camera grading is only a visual estimate and cannot replace laboratory/SLS certification.
- The berry dataset contains only 168 physical samples and is too small to establish broad real-world generalization.
- The V2 experiment used 168 physical samples/671 images, while the newer current raw/V3 collection contains 194 samples/775 images; no V3 model metrics exist yet.
- V3 changes the task from three classes to two YOLO detection classes and currently lacks a documented scientific rationale for the relabeling.
- V3's current image-level split leaks 146 physical sample groups across splits and is unsuitable for defensible final evaluation until regenerated.
- The current test evidence is internal; independent external validation is absent.
- Grade 3 is the weakest V2 class by F1.
- The small nine-image diagnostic showed Grade 2 instability even though the full saved test recall was stronger.
- Preprocessing consistency across training, ONNX runtime, and TFLite runtime still needs direct parity evidence.
- Price data is farm-gate data, not confirmed export transaction data.
- The primary price target is National Grade 1 only.
- Grade 2 price is an estimated adjustment, not an independently validated forecast.
- Grade 3 price is unavailable.
- Missing weeks and irregular intervals exist; lag features represent previous available observations, not always the previous calendar week.
- Naive Persistence won on only 36 final test timestamps and should not be generalized beyond this evidence.
- Recommendation rules are hard-coded and not yet validated by domain stakeholders.
- Live Firebase, mobile build/device, and complete cross-component validation remain pending.

## 11. Overall Completion Assessment

| Area | Status | Assessment |
| --- | --- | --- |
| Research definition and planning | Complete | Scope, phases, risks, and evidence rules are documented. |
| Dataset collection/preparation | V2 complete; V3 prepared but requires correction | V2 has a leakage-safe audit. V3 adds 775 YOLO images/labels but changes taxonomy and leaks physical samples across splits. |
| Berry model experimentation | Complete for PP2 | Baseline and one controlled improvement are evaluated. |
| Price model experimentation | Complete for PP2 | Naive and two RF configurations are compared fairly. |
| Model selection | Complete | V2 MobileNetV2 and Naive Persistence are selected from saved evidence. |
| Backend integration | Implemented | Current source uses selected runtime methods; test suite is not fully green. |
| Recommendation logic | Implemented and internally validated | Still needs stakeholder/domain validation. |
| Firebase persistence | Implemented, live validation pending | Mocked/fail-safe paths exist; no real credentialed proof. |
| Offline Flutter path | Implemented, validation pending | TFLite and routing exist; build/device/parity proof is absent. |
| Full mobile/backend E2E | Pending | Must be run on current source. |
| Cross-component integration | Pending | Wider team modules have not been fully validated together. |
| Field/external validation | Pending | Necessary for strong final research claims. |
| Final documentation | Mostly complete, reconciliation required | Current discount/test/status discrepancies must be corrected. |

## 12. Final Current Conclusion

The work has passed the proof-of-concept stage. It now has versioned datasets, reproducible scripts, saved model artifacts, defensible V2 test metrics, explicit model-selection reasoning, a functional backend design, optional persistence, and an implemented offline mobile path. The strongest completed research result is the V2 MobileNetV2 berry classifier at 80.73% accuracy and the finding that Naive Persistence substantially outperformed the tested RandomForest price models on the current 36-date test period. V3 is valuable new dataset work, but it is not yet a replacement research result because its taxonomy differs and its current split is not sample-independent.

The correct current claim is not that the entire system is finished. The correct claim is that the PP2 research and core implementation are substantially complete, while final engineering validation and real-world validation remain open. The immediate release gate is to reconcile the Grade 2 price rule, restore a fully passing backend suite, validate Flutter on a real build/device, compare TFLite and ONNX outputs, and verify a live Firebase write. Only after those steps should the component be described as fully integrated and validated.

## 13. Primary Evidence Locations

- `docs/research/PROJECT_STATUS.md` — phase-by-phase implementation status.
- `docs/research/EXPERIMENT_LOG.md` — experiment configurations, metrics, observations, and decisions.
- `docs/research/PP2_RESULTS.md` — consolidated PP2 evidence and narrative.
- `docs/research/PP2_LIMITATIONS.md` — mandatory limitations.
- `docs/research/PP2_INTEGRATION_VALIDATION.md` — recorded API integration evidence.
- `docs/research/PP2_EXECUTION_CHECKLIST.md` — completed and pending phase items.
- `docs/research/project_commands_guide.md` — reproduction and runtime commands.
- `data/processed/grading_forecast/berry_dataset_v2_summary.json` — V2 image/sample audit and split.
- `data/raw/Pepper Berry Grading V3.yolov8/data.yaml` and its Roboflow README files — ignored raw V3 definition and export metadata; the directory is not currently tracked by Git.
- `data/processed/grading_forecast/price_v2/price_v2_coverage_summary.json` — V2 price coverage, gaps, and split.
- `ml/grading_forecast/berry_grading/models/v2/berry_classifier_metrics.json` — selected berry metrics.
- `ml/grading_forecast/price_forecasting/models/v2/forecast_metrics.json` — V2 RandomForest and Naive Persistence comparison.
- `backend/app/services/grading_forecast/` — current backend runtime implementation.
- `mobile/lib/features/grading_forecast/` — current Flutter workflow and offline/API services.
