# V3 Phase 0 Research Decision Record

**Project:** Multimodal Pepper AI Decision Support System  
**Individual component:** Berry Grading and Export Price Forecasting  
**Phase:** 0 — Lock the Research Definition  
**Decision date:** 2026-10-06  
**Status:** **BLOCKED — RESEARCHER DECISION REQUIRED**  
**Nature of this phase:** Documentation and research-definition work only. No dataset, annotation, model, backend, mobile, or price-forecasting implementation was changed.

## Decision Labels Used in This Record

- **VERIFIED FACT** — directly supported by repository data, source, saved artifacts, or project reference documents.
- **LOCKED RESEARCH DECISION** — fixed for V3 by the researcher’s Phase 0 instruction and consistent with available evidence.
- **OPEN DECISION / REQUIRES RESEARCHER CONFIRMATION** — the repository does not contain enough evidence to justify a scientifically defensible conclusion.

## 1. Research Problem

### Final proposed task definition

> Given a smartphone image of a harvested black pepper sample or batch, detect whether a valid pepper sample is present and classify the detected sample as V3 Grade 1 or V3 Grade 2. If no valid pepper sample is detected, image quality is inadequate, detection confidence is insufficient, or grade confidence is insufficient, the system must reject the input and request another image.

### Scope interpretation

**LOCKED RESEARCH DECISION:** The V3 research problem is **YOLO-based harvested pepper sample/batch detection and grade classification**.

It is not individual-berry detection or per-berry grading. The conceptual system is:

```text
Smartphone image
      ↓
Harvested pepper sample/batch detection
      ↓
Is a valid pepper sample present with sufficient evidence?
      ↓
YES ───────────────────────────── NO
 ↓                                ↓
Sample/batch grade classification Reject input
 ↓                                ↓
V3 Grade 1 / V3 Grade 2           Request another image
```

**VERIFIED FACT:** The individual proposal describes smartphone images of harvested pepper berries, asks the grading model to classify the pepper **batch**, and defines the image-capture requirement in terms of pepper berry **samples**. The team TAF describes an export quality score and market forecast for pepper **batches**. These references support a sample/batch-level unit more strongly than an individual-berry unit.

**VERIFIED FACT:** The separate berry-disease component in the TAF explicitly proposes detecting individual berries. The grading component does not make that individual-object claim. Keeping these two research responsibilities distinct prevents scope overlap.

## 2. Unit of Prediction

> **Harvested pepper sample/batch represented in the smartphone image.**

**LOCKED RESEARCH DECISION:**

- The prediction applies to the visible harvested pepper sample or batch as a whole.
- A bounding box represents the sample/batch region, not one berry.
- The returned grade describes the detected sample/batch.
- The system must not output separate grades for individual berries.
- Multiple photographs of the same physical sample are multiple views of one specimen group, not independent physical specimens.

## 3. Grade Taxonomy

### 3.1 Verified V3 export taxonomy

**VERIFIED FACT:** `data.yaml` defines two detector classes:

```yaml
nc: 2
names: ['Grade 1', 'Grade 2']
```

The exported dataset contains 775 images and 775 matching non-empty YOLO label files. Each image has one annotated bounding box.

| V3 class ID | Exported class name | Instances/images |
| ---: | --- | ---: |
| 0 | Grade 1 | 448 |
| 1 | Grade 2 | 327 |

### 3.2 Verified source-to-V3 mapping

Exact file-hash comparison traces every V3 image back to the current authoritative raw hierarchy. All 775 V3 images are byte-identical to an image in `data/raw/berry_images/`.

```text
Original/source grade_1 (224 images) ─┐
                                      ├──→ V3 class 0: Grade 1 (448 images)
Original/source grade_2 (224 images) ─┘

Original/source grade_3 (327 images) ────→ V3 class 1: Grade 2 (327 images)
```

This mapping is a **VERIFIED FACT about the files and labels**.

### 3.3 Meaning of the original labels

The repository establishes the following:

- V1/V2 label-generation code copied the enclosing directory name directly: `grade_1` → Grade 1, `grade_2` → Grade 2, and `grade_3` → Grade 3.
- V1 contained 120 images per class.
- The saved V2 manifest contained 224 Grade 1, 224 Grade 2, and 223 Grade 3 images.
- The current raw hierarchy contains 224, 224, and 327 images respectively.
- V1/V2 fields that could substantiate the labels—size, color, texture, broken berries, light berries, pinheads, foreign matter, mould, and insect damage—are recorded as `unknown` rather than manually verified.
- The repository does not record who assigned the original grade folders, the measurement protocol used, laboratory results, buyer acceptance criteria, or a domain-expert verification record.

Therefore, the original folders are verified **dataset labels**, but their scientific ground-truth basis is not established by the repository.

### 3.4 Relationship to SLS 105 Part 1: 2022

**VERIFIED FACT:** The included SLS reference defines three grades for whole black pepper: Grade 1, Grade 2, and Grade 3. The distinctions include physical requirements such as maximum extraneous matter, foreign matter, light berries, broken berries and pinheads, and minimum bulk density. It also defines chemical requirements including moisture, ash, volatile oils, and piperine.

The camera dataset does not contain verified measurements for those physical/chemical criteria. The proposed V3 collapse also does not preserve the three-grade SLS taxonomy:

```text
SLS-like/source Grade 1 + source Grade 2 → V3 Grade 1
source Grade 3                         → V3 Grade 2
```

Consequently, V3 Grade 1 and V3 Grade 2 must not presently be described as official SLS Grade 1 and official SLS Grade 2.

### 3.5 Relationship to market-price grades

**VERIFIED FACT:** The price dataset is Department of Export Agriculture weekly **farm-gate producer price** data. It contains Grade 1 and Grade 2 strings; Grade 3 is absent. The selected PP2 forecasting target is National Grade 1 average farm-gate price. Grade 2 coverage is sparser.

The repository does not contain the price source’s formal grade definitions or evidence that its Grade 1/2 terminology is equivalent to:

- the original image folders;
- SLS 105 grades; or
- the new collapsed V3 classes.

The shared names `Grade 1` and `Grade 2` are not sufficient evidence of semantic equivalence.

### 3.6 Taxonomy decision status

**LOCKED RESEARCH DECISION:** V3 is intended to study a two-output grading task.

**OPEN DECISION / REQUIRES RESEARCHER CONFIRMATION:** The scientific meaning and public naming of those two outputs is not yet locked. The researcher must decide whether V3 is:

1. a custom operational binary grouping derived from the three source folders; or
2. claimed to correspond to a recognized buyer, Department of Export Agriculture, or SLS grading scheme.

Option 2 requires authoritative definitions and label validation not currently present in the repository. Until supplied, the defensible wording is **V3 Grade 1** and **V3 Grade 2, custom dataset classes**, accompanied by the explicit mapping above. No official-certification or direct price-grade equivalence claim is allowed.

## 4. Detection Task

**LOCKED RESEARCH DECISION:** YOLO is intended to detect and localize the harvested pepper sample/batch region.

The detector is not intended to draw one box around each individual berry. Its research functions are:

1. identify whether the expected harvested pepper sample/batch object is present;
2. localize the sample/batch region;
3. provide object-presence evidence for rejecting images without a detected pepper sample; and
4. provide the region on which the two-grade decision is based.

**VERIFIED FACT:** V3 has one box per image. Mean normalized box width is approximately 0.8505 and mean height is approximately 0.8325. In 355 of 775 images, the box covers at least 80% of both image dimensions. One box covers the full image. This annotation pattern is consistent with sample/batch localization and inconsistent with a true per-berry detection claim.

The architecture may use a single YOLO model that returns a class-specific sample box, or a detector followed by a sample-level classifier. Phase 0 locks the functional task, not an unsupported architecture choice. Any later implementation must preserve separate evaluation of object presence/rejection and grade correctness.

## 5. Classification Task

**LOCKED RESEARCH DECISION:** When a valid harvested pepper sample/batch is detected with sufficient evidence, the detected region is classified into exactly one of two V3 research classes:

- V3 Grade 1; or
- V3 Grade 2.

The grade is assigned to the sample/batch shown in the image. It is not assigned berry by berry.

**Historical context only:** V2 used a three-class closed-set MobileNetV2 classifier and achieved 0.8073 image-level accuracy and 0.8068 macro F1 on its leakage-safe 109-image test split. V2 remains unchanged and is a historical baseline. Its three-class metrics are not directly comparable with a future two-class YOLO detection/classification evaluation.

## 6. Rejection Task

### Required behavior

```text
Valid pepper sample detected + sufficient detection/grade confidence + adequate quality
    → accept and return V3 Grade 1 or V3 Grade 2

No valid pepper sample detected
    → reject and request another image

Detection confidence insufficient
    → reject and request another image

Image quality inadequate
    → reject and request another image

Grade confidence insufficient
    → reject and request another image
```

**LOCKED RESEARCH DECISION:** V3 must not behave as an unconditional closed-set classifier that always forces an arbitrary input into one of the known grades.

**LOCKED RESEARCH DECISION:** Final confidence and image-quality thresholds will not be chosen in Phase 0. They must be calibrated on validation data after the split and evaluation datasets are locked. The final held-out test set must not be used for threshold selection.

**VERIFIED LIMITATION:** Every current V3 image contains a labeled pepper sample and every label file is non-empty. The current V3 export therefore contains no documented non-pepper/background-negative images. YOLO does not automatically guarantee non-pepper rejection merely because it has an objectness signal.

**OPEN DECISION / REQUIRES RESEARCHER CONFIRMATION:** Before rejection can become an evaluated research claim, a later phase needs an approved, independently sourced protocol for non-pepper images, invalid captures, poor-quality pepper images, and valid-but-difficult pepper samples. Phase 0 does not add or create those data.

## 7. Claims and Non-Claims

### 7.1 Intended research claims, subject to later experimental evidence

The research may investigate:

- YOLO-based detection/localization of a harvested black pepper sample or batch;
- two-grade classification of the detected sample/batch;
- rejection of non-pepper and invalid inputs;
- confidence-aware acceptance and rejection;
- smartphone image-based visual grading;
- multi-image, physical-sample-level aggregation if explicitly implemented and evaluated later; and
- integration of grading with price forecasting and decision support, once grade semantics are reconciled.

### 7.2 Claims that are prohibited under the current definition

The research must not claim:

- per-berry grading;
- individual berry detection;
- individual berry classification;
- berry-by-berry grade assignment;
- true per-berry object detection;
- official SLS certification;
- measurement of non-visual SLS properties such as moisture, bulk density, ash, volatile oil, or piperine;
- semantic equivalence between V3 image grades and price-data grades without supporting definitions;
- reliable non-pepper rejection merely because YOLO is used; or
- external/field generalization before independent testing supports it.

## 8. Evaluation Protocol

### 8.1 Physical-sample leakage prevention

**LOCKED RESEARCH DECISION:** Final V3 research splits must be physical-sample/group-aware.

The authoritative raw hierarchy identifies 194 physical sample groups:

| Original folder | Physical groups | Images | Intended V3 class |
| --- | ---: | ---: | --- |
| `grade_1` | 56 | 224 | V3 Grade 1 |
| `grade_2` | 56 | 224 | V3 Grade 1 |
| `grade_3` | 82 | 327 | V3 Grade 2 |
| **Total** | **194** | **775** | — |

**VERIFIED FACT:** The current Roboflow image-level split is not suitable as the final research split. A filename-to-source-group audit found that 146 of 194 physical sample groups cross train/validation/test boundaries, involving 584 images. Only 48 groups are exclusive to one split, and those are train-only.

Phase 0 does not alter this export. A later data-preparation phase must regenerate manifests/splits so every view of one physical sample remains in exactly one partition.

### 8.2 Test-set discipline

**LOCKED RESEARCH DECISION:**

- Training data is used to fit model parameters.
- Validation data is used for model comparison, preprocessing choices, hyperparameters, detection threshold selection, grade-confidence threshold selection, image-quality/rejection threshold selection, and any stopping decision.
- The final held-out test set remains sealed while those decisions are made.
- The test set is evaluated after the candidate model and thresholds are locked.
- Repeated test-set inspection or tuning invalidates the test set as a final unbiased estimate.
- Any later model revision after inspecting final test results requires transparent versioning and, ideally, a new untouched test set.

### 8.3 Required future metrics

No new metrics are calculated in Phase 0.

#### Sample/batch grading

- accuracy;
- macro F1;
- per-class precision;
- per-class recall;
- per-class F1; and
- confusion matrix.

#### Detection and invalid-input rejection

- detection precision;
- detection recall;
- mAP where appropriate for the chosen detector/evaluation setup;
- false-positive rate on non-pepper/invalid inputs;
- rejection rate on invalid inputs; and
- false-rejection rate on valid pepper inputs.

#### Confidence-aware behavior

- coverage/acceptance rate;
- accuracy and macro F1 among accepted predictions;
- rejection performance by input category;
- risk-versus-coverage or equivalent selective-prediction analysis; and
- calibration metrics if calibration is implemented later.

#### Group-aware reporting

Because several images may represent one physical sample, final reporting must include physical-sample/group-aware results. Image-level results may also be reported, but must not be presented as if every image were an independent physical specimen. If multi-view aggregation is implemented, the aggregation rule must be selected using validation data and evaluated at sample level on the held-out test groups.

### 8.4 Reproducibility requirements

A future V3 experiment must record:

- the V3 taxonomy version and mapping;
- source image and annotation checksums or a reproducible manifest;
- the group-aware split manifest and random seed;
- training/validation/test group and image counts;
- model configuration and dependency versions;
- preprocessing and augmentation;
- confidence/rejection calibration procedure;
- commands and artifact paths;
- image-level and group-level metrics; and
- known limitations and failed cases.

## 9. Research Targets

No repository document inspected establishes a numeric V3 target for accuracy, F1, mAP, false-positive rate, false-rejection rate, coverage, calibration, or latency.

Therefore, **no numeric target is locked in Phase 0**.

The earlier V2 result—0.8073 accuracy and 0.8068 macro F1—is a historical three-class baseline, not a guaranteed V3 target and not directly comparable to a two-class detection/rejection task.

Research success will be assessed as a combination of:

1. correct V3 two-grade sample/batch classification;
2. reliable localization/presence detection of valid harvested pepper samples;
3. demonstrated rejection of unrelated/non-pepper inputs;
4. acceptable false rejection of genuine pepper samples;
5. performance on unseen physical sample groups;
6. stable behavior on smartphone-style images;
7. reproducible evaluation and artifact versioning; and
8. zero physical-sample overlap between training and final evaluation.

Any numeric product or research target proposed later must be labeled as a target, justified from stakeholder needs or prior evidence, and kept separate from achieved results.

## 10. Known Limitations and Risks

1. **One box per image:** V3 contains exactly one annotation per image; it cannot support per-berry detection claims.
2. **Large boxes:** Boxes generally cover most of each image. Detection may behave similarly to foreground cropping or image classification rather than challenging object localization.
3. **No negative examples in V3:** Non-pepper rejection is not trainable or testable from the current positive-only export alone.
4. **Background/camera shortcuts:** Images use a small number of camera devices and recurring backgrounds. A model may learn capture context rather than pepper quality.
5. **Current split leakage:** Alternate views of the same physical samples cross the current Roboflow splits.
6. **Unverified original ground truth:** The original folder grades lack documented measurement or expert-validation provenance in the repository.
7. **Taxonomy mismatch:** SLS defines three grades, while V3 collapses them to two custom classes.
8. **Price-grade mismatch risk:** The price data uses Grade 1/2 names but does not provide definitions proving compatibility with V3.
9. **Visual-only limitation:** Chemical properties and bulk density required by formal standards cannot be inferred reliably from ordinary smartphone images.
10. **Limited external validation:** The repository contains no completed V3 field/external evaluation across unseen farms, devices, backgrounds, and collection conditions.
11. **Confidence is not correctness:** A high YOLO confidence score does not by itself establish calibration or valid rejection behavior.
12. **Image-quality rejection undefined:** Blur, exposure, occlusion, framing, and minimum sample visibility criteria still require a validation-backed protocol.
13. **Existing application contract is three-class:** Current backend/mobile V2 schemas and recommendations still include Grade 3. Phase 0 does not modify them; V3 integration will require a later, explicitly scoped contract migration.

## 11. OPEN DECISIONS / REQUIRES RESEARCHER CONFIRMATION

### Open Decision 1 — Meaning and naming of the two V3 grades

1. **Inconsistency:** V3 combines source Grade 1 and source Grade 2 as V3 Grade 1, and renames source Grade 3 as V3 Grade 2. SLS defines three distinct grades.
2. **Evidence:** Exact image mapping proves the collapse; SLS 105 in the repository explicitly lists Grades 1, 2, and 3; the repository contains no authority approving the collapse.
3. **Why it matters:** Calling the outputs simply Grade 1/2 may imply official equivalence that is not established and may make thesis claims misleading.
4. **Decision required:** Confirm that V3 is a **custom binary operational taxonomy**, or provide the authoritative buyer/DEA/domain-expert rule establishing it as a recognized two-grade scheme. If it is custom, confirm whether public labels should remain `V3 Grade 1/2` or use neutral names such as `V3 Higher-grade group` and `V3 Lower-grade group`.

### Open Decision 2 — Ground-truth provenance of original grade folders

1. **Inconsistency:** Folder grades exist, but the measurable quality fields are all `unknown` and no expert/laboratory annotation record is stored.
2. **Evidence:** Label CSVs and generation scripts copy folder names without deriving or validating grade criteria.
3. **Why it matters:** Model performance can only demonstrate reproduction of dataset labels unless those labels are grounded in a defensible grading protocol.
4. **Decision required:** Identify who assigned the original grades and under what criteria, or approve a future domain-expert relabel/verification step before final claims.

### Open Decision 3 — Compatibility with price-data Grade 1 and Grade 2

1. **Inconsistency:** The image task and farm-gate price data share names but do not share documented definitions.
2. **Evidence:** The price file identifies source, market level, and grade string, but no grade specification; SLS has three grades; V3 uses a custom two-class collapse.
3. **Why it matters:** A grading output should not select or adjust a price series unless the grade semantics are compatible.
4. **Decision required:** Obtain DEA/buyer grade definitions and confirm the mapping, or keep V3 grading and grade-specific price forecasting semantically separate and disclose that limitation.

### Open Decision 4 — Rejection evaluation data and protocol

1. **Inconsistency:** Rejection is a required V3 contribution, but the current export contains only positive pepper images with one box each.
2. **Evidence:** All 775 label files are non-empty; no documented negative/non-pepper set exists in the inspected V3 dataset.
3. **Why it matters:** Without negatives and difficult valid cases, false-positive and false-rejection behavior cannot be calibrated or evaluated.
4. **Decision required:** Approve a later protocol for independently sourced non-pepper, invalid-quality, and challenging valid-pepper validation/test inputs. These must be collected and split without contaminating the final test evaluation.

### Open Decision 5 — Single-stage versus two-stage implementation

1. **Inconsistency:** The functional definition requires localization, grade classification, and rejection, while Phase 0 intentionally does not choose a specific architecture.
2. **Evidence:** Current V3 labels are class-specific sample boxes and can support joint YOLO detection/classification; the previous V2 implementation is a separate closed-set classifier.
3. **Why it matters:** Confidence definitions and evaluation details differ between a joint detector and detector-plus-classifier pipeline.
4. **Decision required:** This may be selected experimentally in a later phase, but the researcher should confirm that Phase 1 may compare these architecture options while preserving the same locked task and evaluation protocol.

## 12. Versioning and Preservation Rules

**LOCKED RESEARCH DECISION:**

- V1 and V2 are immutable historical evidence.
- Do not overwrite, delete, rename, or silently reinterpret V1/V2 datasets, metrics, models, or documentation.
- V3 work must use explicit V3 identifiers and paths.
- Preferred future versioned locations are:

```text
data/processed/grading_forecast/berry_v3/
ml/grading_forecast/berry_grading/models/v3/
ml/grading_forecast/berry_grading/evaluation/v3/
```

No directories were created solely for Phase 0.

## 13. Phase 0 Gate

### Decisions successfully locked

- Unit of prediction: harvested pepper sample/batch in a smartphone image.
- No individual-berry or per-berry grading claim.
- YOLO is used for sample/batch localization and object-presence evidence.
- Accepted inputs receive one of two V3 class outputs at sample/batch level.
- Non-pepper, invalid-quality, and low-confidence inputs must be rejectable.
- Thresholds will be calibrated later on validation data, not invented in Phase 0.
- Final evaluation must use physical-sample/group-aware splitting.
- Validation is used for model/threshold decisions; the held-out test set is sealed until the candidate is locked.
- Future evaluation covers grading, detection, rejection, confidence-aware behavior, and sample-level results.
- V1/V2 remain unchanged and separately versioned.

### Gate result

```text
BLOCKED — RESEARCHER DECISION REQUIRED
```

Phase 1/model development should not begin until the researcher confirms at minimum:

1. the scientific meaning and public naming of the V3 two-grade taxonomy;
2. how the original source grades were assigned or how they will be verified;
3. whether V3 grades are intended to map to DEA price grades or remain separate; and
4. that a later negative/invalid-input data and evaluation protocol is required for the rejection claim.

After these decisions, Phase 1 may prepare a versioned, physical-sample-group-aware V3 manifest and split without altering V1/V2.

## 14. Evidence Inspected

### V3 and original images

- `data/raw/Pepper Berry Grading V3.yolov8/data.yaml`
- `data/raw/Pepper Berry Grading V3.yolov8/README.dataset.txt`
- `data/raw/Pepper Berry Grading V3.yolov8/README.roboflow.txt`
- V3 `train`, `valid`, and `test` image/label directories
- `data/raw/berry_images/grade_1/sample_*`
- `data/raw/berry_images/grade_2/sample_*`
- `data/raw/berry_images/grade_3/sample_*`

### Labels, prior datasets, and results

- `data/annotations/grading_forecast/berry_grading_labels.csv`
- `data/annotations/grading_forecast/berry_grading_labels_v2.csv`
- `data/processed/grading_forecast/berry_dataset_v2_summary.json`
- `ml/grading_forecast/berry_grading/models/v2/berry_classifier_metrics.json`
- `scripts/generate_grading_labels.py`
- `ml/grading_forecast/berry_grading/preprocessing/prepare_berry_dataset_v2.py`

### Price evidence

- `data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv`
- `data/processed/grading_forecast/price_v2/price_v2_coverage_summary.json`
- `docs/research/price_dataset_description.md`

### Requirements and standards

- `docs/references/R26-SE-012_IT22079268_PremathilakaGGRT.pdf`
- `docs/references/TAF_R26-SE-012.pdf`
- `docs/references/SLS 105 Part 1_ 2022 - Compiled Black Pepper Standards.pdf`

### Research and implementation context

- `docs/research/EXPERIMENT_LOG.md`
- `docs/research/PROJECT_STATUS.md`
- `docs/research/PP2_MASTER_PLAN.md`
- `docs/research/PP2_RESULTS.md`
- `docs/research/PP2_LIMITATIONS.md`
- `docs/research/FULL_PROGRESS_REPORT.md`
- `docs/evaluation_metrics.md`
- `backend/app/schemas/grading_forecast.py`
- Current berry-grading backend and mobile service contracts, inspected for historical terminology only

