# V3 Phase 1 Dataset Audit and Grading Diagnosis

**Project:** Multimodal Pepper AI Decision Support System  
**Individual component:** Berry Grading and Export Price Forecasting  
**Phase:** 1 - V3 Audit and Grading Diagnosis  
**Audit date:** 2026-10-06  
**Dataset version:** `berry_v3`  
**Status:** **PHASE 1 COMPLETE**

This phase audited the V3 dataset without training a model or changing any source image, YOLO annotation, V1/V2 artifact, backend, mobile application, or price-forecasting implementation. The external pre-Roboflow source is used only for physical-sample identity. The Roboflow V3 export remains the source of YOLO boxes and V3 class labels.

## 1. Locked Scope

The prediction unit remains the harvested pepper sample/batch shown in a smartphone image. This is not individual-berry detection or per-berry grading.

Phase 1 answers five questions:

1. Are the V3 labels visually meaningful?
2. Is there obvious background/camera leakage?
3. Can physical sample identity be reconstructed reliably?
4. What does the old V2 model actually look at?
5. Can the V3 task reasonably proceed to model development?

The blind review has now been completed and unblinded. All five Phase 1 questions have a recorded result.

## 2. Evidence Inspected

The audit inspected:

- `docs/research/V3_DECISION_RECORD.md`
- `docs/research/EXPERIMENT_LOG.md`
- `data/raw/Pepper Berry Grading V3.yolov8/`, including `data.yaml`, README files, 775 images, and 775 YOLO label files
- `D:/work/Year - 4/pepper/project/datset reorder/`, the pre-Roboflow grouping/reference hierarchy
- the V2 split and manifest under `data/processed/grading_forecast/berry_split_v2/`
- the frozen V2 model and metrics under `ml/grading_forecast/berry_grading/models/v2/`
- the existing V2 training/evaluation implementation, to reproduce the input and class conventions without changing V2

## 3. Q3 - Physical-Sample Identity Reconstruction

### 3.1 Actual source hierarchy

The external source has two grade directories. Sample names repeat across grades, so the globally unique identity is `source_grade/sample_id`.

```text
D:/work/Year - 4/pepper/project/datset reorder/
|-- grade_1/
|   |-- sample_001/ ... sample_112/
|   `-- 448 JPG images across 112 physical samples
`-- grade_2/
    |-- sample_001/ ... sample_082/
    `-- 327 JPG images across 82 physical samples
```

Total: 194 physical samples and 775 images. Of the 194 sample folders, 189 contain four images, two contain five images, and three contain three images.

This newer, researcher-supplied source clarifies the grouping metadata used in Phase 1. Unlike the older repository hierarchy discussed in Phase 0, it is already organized according to the two V3 grades: `grade_1` contains 112 source groups/448 images and `grade_2` contains 82 source groups/327 images.

### 3.2 Exact identity method

SHA-256 was calculated for every source image and every Roboflow V3 image. A V3 image was assigned a physical sample only when its full file hash matched exactly one source image hash. Filenames, dimensions, visual similarity, and perceptual hashes were not used as identity evidence.

| Mapping check | Result |
| --- | ---: |
| Source images | 775 |
| V3 images | 775 |
| Exact SHA-256 matches | 775 |
| Unmatched V3 images | 0 |
| Ambiguous V3 matches | 0 |
| Duplicate source-hash groups | 0 |
| Physical samples reconstructed | 194 |

The mapping also confirmed complete class consistency:

```text
source grade_1 -> V3 class 0 / V3 Grade 1: 448 images
source grade_2 -> V3 class 1 / V3 Grade 2: 327 images
```

This establishes image identity, grouping, and dataset-label consistency. It does not establish that the labels are official SLS or market/buyer grades.

**Q3 answer:** Yes. Physical-sample identity was reconstructed reliably for all 775 V3 images using exact hashes.

## 4. Q3b - Group-Aware Research Split

The split was generated deterministically with seed 42, stratified by V3 grade at the physical-sample level. Approximate 70/15/15 allocation was secondary to group separation and class representation.

| Partition | Groups | Images | V3 Grade 1 groups/images | V3 Grade 2 groups/images |
| --- | ---: | ---: | ---: | ---: |
| TRAIN | 135 | 539 | 78 / 312 | 57 / 227 |
| VALIDATION | 29 | 116 | 17 / 68 | 12 / 48 |
| TEST | 30 | 120 | 17 / 68 | 13 / 52 |
| **Total** | **194** | **775** | **112 / 448** | **82 / 327** |

Programmatic validation passed:

```text
TRAIN sample_ids intersection VALIDATION sample_ids = empty
TRAIN sample_ids intersection TEST sample_ids       = empty
VALIDATION sample_ids intersection TEST sample_ids  = empty
TRAIN union VALIDATION union TEST                    = all 194 mapped samples
Every V3 image belongs to exactly one partition      = true
```

The manifests define a research split over the existing images and annotations. They do not move or duplicate the V3 files. The original Roboflow split remains physically unchanged and must not be mistaken for the new research partition.

**Split result:** **leakage-free** with respect to the 194 reconstructed physical-sample groups.

## 5. Q1 - Blind Visual Label Audit

### 5.1 Prepared review

A deterministic blind-review package was prepared from the new VALIDATION partition only, avoiding the final TEST partition:

- 20 V3 Grade 1 images;
- 20 V3 Grade 2 images;
- neutral identifiers `blind_001` through `blind_040`;
- randomized, reproducible selection using seed 42;
- multiple physical samples represented within each class;
- re-encoded review copies with EXIF removed; and
- no filename, source folder, grade, class ID, or sample ID visible to the reviewer.

The researcher-facing sheet and response file are separate from `internal/blind_review_key.csv`, which contains the concealed mapping and must not be opened before responses are complete.

### 5.2 Completed blind-review results

All 40 researcher responses were present and used an allowed value. The concealed key was opened only after response completion.

| Measure | Result |
| --- | ---: |
| Correct researcher labels | 32 / 40 |
| Overall agreement | 80.0% |
| V3 Grade 1 agreement | 18 / 20 = 90.0% |
| V3 Grade 2 agreement | 14 / 20 = 70.0% |
| Uncertain judgments | 4 / 40 = 10.0% |
| Agreement among non-uncertain responses | 32 / 36 = 88.9% |

The confusion matrix uses dataset label as rows and researcher response as columns:

| True V3 grade | Researcher Grade 1 | Researcher Grade 2 | Researcher Uncertain | Total |
| --- | ---: | ---: | ---: | ---: |
| V3 Grade 1 | 18 | 0 | 2 | 20 |
| V3 Grade 2 | 4 | 14 | 2 | 20 |
| **Total** | **22** | **14** | **4** | **40** |

Cohen's kappa across all 40 items, treating `Uncertain` as a third researcher-response category, is **0.636**. Because the dataset reference has no corresponding uncertain class, this value should be interpreted cautiously. As a supplementary accepted-only calculation, removing the four uncertain responses gives binary kappa **0.778** across 36 decisions; that conditional value must not replace the 80.0% primary agreement result.

### 5.3 Qualitative interpretation

The disagreement pattern is asymmetric:

- no V3 Grade 1 image was labeled Grade 2;
- four V3 Grade 2 images were labeled Grade 1;
- two images from each dataset grade were marked uncertain; and
- the four incorrect Grade 2-to-Grade 1 responses came from only two physical Grade 2 samples (`grade_2/sample_051` and `grade_2/sample_036`), with two views of each sample selected.

This clustering suggests that particular physical samples, rather than random isolated views, account for the decisive errors. It also confirms that image-level judgments are not statistically independent when multiple views belong to one physical sample.

The 80.0% overall result, 88.9% agreement among decisive responses, and positive kappa provide diagnostic evidence that the two dataset classes are visually distinguishable under the sampled conditions. Grade 2 is clearly less consistently recognized than Grade 1, so the result is acceptable rather than conclusive or strong validation. The small, single-researcher, validation-only study does not establish official grade correctness or generalization beyond the current capture conditions.

**Q1 answer:** The V3 labels have **acceptable diagnostic visual separability**, with a meaningful Grade 2 weakness that must remain visible in later evaluation.

## 6. Q2 - Background and Camera Shortcut Audit

### 6.1 Counts, dimensions, and aspect ratio

| Measure | V3 Grade 1 | V3 Grade 2 |
| --- | ---: | ---: |
| Images | 448 | 327 |
| Physical samples | 112 | 82 |
| 4000 x 3000 | 304 | 326 |
| 4080 x 3060 | 140 | 1 |
| 8160 x 6120 | 4 | 0 |
| Mean width | 4062.14 | 4000.24 |
| Width range | 4000-8160 | 4000-4080 |
| Mean height | 3046.61 | 3000.18 |
| Height range | 3000-6120 | 3000-3060 |
| Aspect ratio | 4:3 for every image | 4:3 for every image |

Aspect ratio does not distinguish the classes. Resolution does: 144 of 448 Grade 1 images use a resolution other than 4000 x 3000, compared with only one of 327 Grade 2 images.

### 6.2 EXIF camera/device information

EXIF was present in the original V3 files rather than stripped by the export.

| Camera model | V3 Grade 1 | V3 Grade 2 |
| --- | ---: | ---: |
| Samsung Galaxy A06 | 144 (32.1%) | 1 (0.3%) |
| Samsung SM-A127F | 304 (67.9%) | 326 (99.7%) |

All 775 images report Samsung as the camera make. This near-deterministic relationship between the Galaxy A06 and V3 Grade 1 is a clear shortcut risk. It does not prove a future model will use device-specific image properties, but it makes that behavior plausible unless controlled experimentally.

EXIF orientation also differs. V3 Grade 1 has orientation values 1/3/6/8 in counts 36/158/246/8; V3 Grade 2 has counts 2/48/263/14. Orientation is therefore another capture-condition imbalance, although weaker than device/resolution.

### 6.3 Brightness and color summaries

Brightness is the mean grayscale intensity on a 0-255 scale. Saturation and border brightness are lightweight diagnostics rather than semantic background classifiers.

| Measure | V3 Grade 1 | V3 Grade 2 |
| --- | ---: | ---: |
| Mean brightness | 142.85 | 141.20 |
| Brightness range | 92.89-191.35 | 112.77-177.84 |
| Brightness standard deviation | 19.53 | 10.20 |
| Mean saturation | 31.66 | 30.00 |
| Mean border brightness | 194.04 | 191.90 |

The class means are close, so average brightness, saturation, and border brightness do not provide the same obvious class separation as device/resolution. Grade 1 has substantially wider brightness variation, which may still encode collection conditions.

### 6.4 Visual background/capture review

The validation-only contact sheet contains 12 representative images from each V3 class. Both classes include:

- pepper piles on white paper or pale surfaces;
- grey/metal-like surfaces;
- samples held in a person's hand; and
- differing framing, shadow, and pile layout.

No background type in this small visual sample is exclusive to one grade. However, the recurrence of hands, paper, surfaces, and device-specific capture patterns means context is available to a model. The contact sheet is a qualitative inspection aid, not proof of a learned shortcut.

### 6.5 Shortcut conclusion

**SHORTCUT RISK: HIGH.**

The principal evidence is the strong class association with camera model and resolution, not brightness or a visually exclusive surface. A robust Phase 2 design must preserve group separation and explicitly measure performance by device/capture subgroup; otherwise apparently strong grade accuracy may partly reflect capture conditions. No test-set images were used in the contact sheet or blind review.

**Q2 answer:** Yes, there is obvious capture-condition leakage risk, especially from camera model and resolution. Background-only separation was not established by the lightweight visual audit.

## 7. Q4 - Frozen V2 Saliency Diagnosis

### 7.1 Method

The existing three-class V2 MobileNetV2 model was loaded without retraining or modification. Its 109-image historical test set was screened to select nine deterministic examples: one correct and two incorrect predictions from each historical class. An input-gradient saliency overlay was used because it is a lightweight method supported by the saved Keras model. It visualizes local sensitivity to the predicted class, not causal reasoning.

| ID | True | V2 prediction | Result | Attention | Qualitative observation |
| --- | --- | --- | --- | --- | --- |
| `v2_saliency_01` | Grade 1 | Grade 1 | Correct | PEPPER-FOCUSED | Strongest response is distributed over the berry pile with limited response on the pale surface. |
| `v2_saliency_02` | Grade 1 | Grade 2 | Incorrect | MIXED | Response covers berries and also extends broadly across the palm and fingers. |
| `v2_saliency_03` | Grade 1 | Grade 2 | Incorrect | MIXED | Response is present on the berry pile, hand, and nearby pale surface. |
| `v2_saliency_04` | Grade 2 | Grade 2 | Correct | MIXED | Response follows many berries but remains visible across the supporting hand. |
| `v2_saliency_05` | Grade 2 | Grade 1 | Incorrect | PEPPER-FOCUSED | Response is concentrated on the spread berry cluster and its edges. |
| `v2_saliency_06` | Grade 2 | Grade 1 | Incorrect | PEPPER-FOCUSED | Response is concentrated across the berry cluster, with some surface response. |
| `v2_saliency_07` | Grade 3 | Grade 3 | Correct | MIXED | Response covers berries/debris and extends into the surrounding grey surface. |
| `v2_saliency_08` | Grade 3 | Grade 2 | Incorrect | MIXED | Response covers the sample and substantial portions of the palm and fingers. |
| `v2_saliency_09` | Grade 3 | Grade 1 | Incorrect | MIXED | Response is distributed across berries and the supporting hand. |

Summary: three PEPPER-FOCUSED, six MIXED, zero BACKGROUND-FOCUSED, and zero UNCLEAR examples. The three correct examples consist of one PEPPER-FOCUSED and two MIXED. The six incorrect examples consist of two PEPPER-FOCUSED and four MIXED.

### 7.2 Interpretation and limitations

V2 often responds to pepper texture and pile structure, but attention is not consistently isolated to the pepper. Hands and surfaces contribute visibly in multiple correct and incorrect cases. This supports the concern that capture context can influence predictions, but the selected examples and input-gradient method cannot prove what caused any prediction.

The diagnostic deliberately selected errors and is not prevalence-weighted. Its nine examples must not be interpreted as an estimate that two-thirds of all V2 predictions use mixed evidence. V2 also used the earlier three-class taxonomy, so this result is historical diagnostic evidence rather than a direct V3 performance result.

**Q4 answer:** The old V2 model is sensitive to pepper regions, but frequently also to hands and surrounding surfaces. It is not reliably pepper-only in this small diagnostic set.

## 8. Q5 - Final Phase 1 Verdict

The task can proceed to controlled model development because exact sample identity was reconstructed, a leakage-free split exists, and the blind review found acceptable diagnostic visual separability. Feasibility is conditional on explicitly controlling and evaluating the high device/resolution shortcut risk.

```text
LABEL QUALITY:
acceptable

SHORTCUT RISK:
high

SPLIT:
leakage-free

TASK:
feasible
```

`Acceptable` means adequate visual separability for a diagnostic 40-image study, not verified ground-truth correctness. `Feasible` means model development is scientifically reasonable under the locked sample/batch definition; it does not remove the need for device-aware analysis, group-aware evaluation, rejection testing, or external validation. The blind result does not establish official SLS/buyer-grade correctness.

## 9. Phase 1 Gate

**PHASE 1 COMPLETE.**

The Phase 1 requirements are satisfied. If a later Phase 2 is authorized, it must:

1. use the locked group-aware research split rather than the original Roboflow split;
2. preserve the final TEST partition for final evaluation rather than model or threshold selection;
3. explicitly mitigate and report the high camera/resolution shortcut risk;
4. report Grade 2 performance separately because it was weaker in the blind review;
5. retain the sample/batch-level task and avoid per-berry claims; and
6. preserve the distinction between custom V3 dataset grades and unverified official/market-grade equivalence.

The unresolved Phase 0 semantic limitations remain: exact dataset-label agreement does not prove equivalence to official SLS grades, buyer grades, or price-data grades.

## 10. Reproducibility and Artifacts

Core manifests and summaries:

- `data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv`
- `data/processed/grading_forecast/berry_v3/v3_group_split_manifest.csv`
- `data/processed/grading_forecast/berry_v3/v3_phase1_audit_summary.json`
- `data/processed/grading_forecast/berry_v3/v3_background_contact_sheet.jpg`

Blind review:

- `data/processed/grading_forecast/berry_v3/blind_review/README.md`
- `data/processed/grading_forecast/berry_v3/blind_review/researcher_labels.csv`
- `data/processed/grading_forecast/berry_v3/blind_review/blind_review_sheet.jpg`
- `data/processed/grading_forecast/berry_v3/blind_review/review_images/blind_001.jpg` through `blind_040.jpg`
- `data/processed/grading_forecast/berry_v3/blind_review/internal/blind_review_key.csv`

V2 diagnostic:

- `ml/grading_forecast/berry_grading/evaluation/_outputs/v3_phase1_v2_saliency/v2_saliency_contact_sheet.jpg`
- `ml/grading_forecast/berry_grading/evaluation/_outputs/v3_phase1_v2_saliency/v2_saliency_manifest.csv`
- nine paired original/overlay panels in the same directory

Reproduction scripts:

- `ml/grading_forecast/berry_grading/preprocessing/audit_berry_v3_phase1.py`
- `ml/grading_forecast/berry_grading/evaluation/diagnose_v2_saliency.py`

No Phase 2 model, weights, threshold, export, or application change was created.
