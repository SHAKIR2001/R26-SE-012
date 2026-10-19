# Phase 6 Prospective Field Data Protocol

> **Roadmap clarification:** This protocol is preparation for the later external field/domain-shift validation stage, not the original Phase 6 “Combine grade + price” objective. The grade-price fusion result is documented separately in `PHASE6_GRADE_PRICE_DECISION_ENGINE_RESULTS.md`; this protocol remains available for future use and is not executed here.

**Status:** READY FOR DATA COLLECTION  
**Evaluation status:** `BLOCKED_PENDING_FIELD_DATA`  
**Purpose:** collect genuinely new smartphone field/domain-shift evidence for the already frozen Phase 3 follow-up decision pipeline. This protocol does not authorize training, threshold tuning, model conversion, or application integration.

## 1. Research question

> How well does the frozen berry grading and rejection pipeline generalize to genuinely new, field-like images captured under different acquisition conditions, and what failure modes remain before prospective deployment evaluation?

The collection is prospective: capture and labeling must follow this protocol, and the final subset must be sealed before it is evaluated.

## 2. Independence requirements

Every Phase 6 image must be independent of:

- the 775 V3 images;
- the 80 original Phase 3 negatives;
- the 250 Phase 3 follow-up negatives;
- all training, validation, and historical test images;
- derivatives, crops, recompressions, or alternate downloads of those images.

An image is eligible only when its provenance, capture metadata, physical-sample group, independent reference label, and SHA-256 are recorded. Exact-hash overlap is prohibited. Similar-looking images are not automatically independent; repeated views must be linked by `physical_sample_id`.

Internet images are not a substitute for this field collection. A future supplementary internet benchmark must be named and reported separately.

## 3. Collection design

Use at least three smartphone models where practicable. Do not assign one grade or one image type exclusively to one device. Each device should cover more than one pepper condition, background, lighting condition, and negative category so device identity is not a label shortcut.

Capture the following naturally and safely where available:

| Dimension | Required coverage |
|---|---|
| Lighting | outdoor daylight, shade, indoor natural light, indoor artificial light, bright conditions, moderately difficult lighting |
| Background | plain surface, agricultural surface, sack/bag, tray/container, wood, concrete-like surface, natural background |
| Framing | close, medium, farther framing, partial crop |
| Pepper condition | independently verified Grade 1, independently verified Grade 2, borderline, mixed-quality, partially occluded, sparse, dense pile |
| Negatives | leaves, vegetation, agricultural crops, soil/background, agricultural materials, ordinary objects, visually similar non-pepper objects |
| Quality challenge | none, mild blur, moderate blur, low light, partial occlusion, small pepper region, difficult framing |

Do not deliberately create dangerous conditions or unusable photographs. Natural variation is more valuable than artificial degradation.

Counts must be reported for every subgroup. The evaluation tooling suppresses subgroup metrics below five images by default; five is a reporting floor, not evidence of adequate statistical power. A useful collection should distribute physical samples across conditions rather than obtain many nearly identical frames from a few samples.

## 4. Physical-sample grouping and partitioning

Assign a stable opaque `physical_sample_id` before photography. All views of the same physical pepper sample must use that ID. A negative scene/object that is photographed repeatedly should likewise receive one stable group ID.

Split at the physical-group level into:

- `CALIBRATION`: development-only images used to verify ingestion, metadata quality, and execution—not to change the model or frozen thresholds;
- `FINAL_EVALUATION`: a sealed prospective evaluation subset that remains unopened by the model until the manifest, labels, integrity checks, pipeline, and reporting rules are frozen.

No physical group may cross these partitions. Record `sealed_at_utc` for final rows. Human label review may occur before sealing, but model predictions must not be used to create or resolve the reference label.

## 5. Independent reference labels

Allowed `reference_type` values are:

- `PEPPER`
- `NON_PEPPER`
- `UNCERTAIN`

For definite pepper rows, `reference_grade` must be `V3 Grade 1` or `V3 Grade 2` and must come from a documented independent source such as an expert/manual assessment, verified sample record, or documented producer/buyer classification whose relationship to the project labels is explained. The model prediction is never a label source.

Use `UNCERTAIN` when the material or grade is genuinely ambiguous. Do not force a binary grade. Record the method in `label_source`, an ethically appropriate reviewer identifier in `reviewer_id`, and the label date. Do not include unnecessary personal data.

The V3 labels remain project-specific. A source label may be mapped to V3 Grade 1/2 only when the mapping procedure is documented; this protocol does not establish SLS, buyer-grade, export-certification, or laboratory equivalence.

## 6. File and manifest handling

Store eligible images in a new clearly named Phase 6 directory; do not place them inside any historical train, validation, test, or negative-set directory. Use repository-relative paths. Do not modify, rename, or move historical images.

Copy `ml/grading_forecast/berry_grading/evaluation/phase6/phase6_field_manifest_template.csv` to `phase6_field_manifest.csv` and populate one row per image. Required schema:

| Column | Meaning |
|---|---|
| `image_id` | Unique opaque Phase 6 image identifier |
| `relative_path` | Repository-relative image path |
| `sha256` | SHA-256 of the exact evaluated file |
| `physical_sample_id` | Stable group identifier shared by repeated views |
| `partition` | `CALIBRATION` or `FINAL_EVALUATION` |
| `reference_type` | `PEPPER`, `NON_PEPPER`, or `UNCERTAIN` |
| `reference_grade` | `V3 Grade 1`, `V3 Grade 2`, `UNCERTAIN`, or `NA` as appropriate |
| `label_source` | Independent reference procedure/source |
| `reviewer_id` | Non-sensitive reviewer identifier where appropriate |
| `label_date` | ISO date of reference labeling |
| `device_make`, `device_model` | Capture device metadata |
| `lighting` | Controlled category from this protocol |
| `background` | Controlled category from this protocol |
| `framing` | close, medium, farther, or partial crop |
| `pepper_density` | sparse, moderate, dense, mixed, or NA |
| `quality_challenge` | none or a defined challenge category |
| `negative_category` | Defined negative type or NA |
| `capture_date` | ISO capture date where ethically appropriate |
| `provenance_note` | Who/where/how provenance without unnecessary personal data |
| `consent_or_authorization` | Collection/use authorization record |
| `sealed_at_utc` | Final-subset freeze time, or blank before sealing |

Do not put secrets, exact private addresses, personal phone numbers, or unnecessary identities in the manifest.

## 7. Pre-evaluation checklist

Before any model inference:

1. Complete all required manifest fields.
2. Compute SHA-256 from the exact stored files.
3. Confirm every path stays inside the repository and every file is readable.
4. Confirm unique image IDs and hashes.
5. Compare hashes with all V3 and Phase 3 datasets.
6. Confirm each physical group belongs to one partition only.
7. Confirm labels were created independently of model output.
8. Confirm device and condition categories are not perfectly confounded with grade/type where avoidable.
9. Seal the final manifest and record its SHA-256.
10. Run `validate_phase6_integrity.py` and require Gate A to pass.

## 8. Frozen evaluation

The evaluator must use:

- model: `ml/grading_forecast/berry_grading/models/v3_phase3_followup/best.pt`;
- model SHA-256: `e825278e0cf8eaff64cd05a2941cf96794e573027823a0ccd308bbc3f1a418ca`;
- decision configuration: `ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup/decision_config_frozen.json`;
- detection/grade confidence 0.05, class margin 0.30, minimum box-area ratio 0.20, minimum dimension 320, minimum brightness 50, and minimum blur variance 10.

No Phase 6 result may change these values. Run:

```powershell
.\.venv-yolo\Scripts\python.exe ml/grading_forecast/berry_grading/evaluation/phase6/validate_phase6_integrity.py
.\.venv-yolo\Scripts\python.exe ml/grading_forecast/berry_grading/evaluation/phase6/evaluate_phase6_field.py --manifest ml/grading_forecast/berry_grading/evaluation/phase6/phase6_field_manifest.csv --partition FINAL_EVALUATION
```

The second command must fail closed if the manifest is absent, empty, overlapping, improperly grouped, missing independently sourced labels, or inconsistent with file hashes.

## 9. Required analysis

Keep internal V3, internet-negative, and prospective field evidence separate. Report:

- total accepted, rejected, and uncertain/abstained decisions;
- valid-pepper coverage and false-rejection rate;
- non-pepper rejection and false-acceptance rate;
- accepted definite-pepper accuracy, balanced accuracy, macro/weighted F1, class metrics, and confusion matrix;
- image-level and physical-sample majority/confidence-weighted results where independent sample truth exists;
- conflicting-view rate;
- device, lighting, background, framing, density, quality, and negative-category breakdowns with counts where denominators support interpretation;
- every false accept, false reject, and grade error in `phase6_error_analysis.csv`.

Confidence is a model score, not a calibrated probability. Failure interpretation must remain observational unless independently proven.

## 10. Acceptance framework

- **Gate A — Dataset independence:** pass only after hash, provenance, label-source, group isolation, and non-reuse checks pass.
- **Gate B — Grading performance:** compare with the frozen internal benchmark and report material degradation without inventing a post-test cutoff.
- **Gate C — Rejection performance:** report valid-pepper false rejection and non-pepper false acceptance separately.
- **Gate D — Domain-shift stability:** identify condition-specific collapse with visible denominators.
- **Gate E — Uncertainty behavior:** determine whether abstentions concentrate in genuinely difficult images; do not claim calibration.

Poor results are recorded, not optimized away. Any retraining, new negatives, augmentation, architecture, or threshold change belongs to a separately authorized Phase 7 hypothesis and protocol.
