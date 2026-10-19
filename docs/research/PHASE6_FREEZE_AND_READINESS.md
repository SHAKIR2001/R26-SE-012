# Phase 6 Freeze and Readiness Record

> **Roadmap clarification:** This document records freeze/readiness work for the later external field/domain-shift validation stage. The original roadmap's Phase 6 “Combine grade + price” objective is evaluated separately in `PHASE6_GRADE_PRICE_DECISION_ENGINE_RESULTS.md`. This readiness record is preserved and not renumbered.

**Date:** 2026-10-07  
**Phase 6 status:** `COMPLETE — PREPARATION DONE, FIELD DATA BLOCKED`  
**Freeze validation:** PASS — 29 checks passed, 0 failed, 1 unavailable because no field dataset exists

## 1. Repository state

The repository was inspected before Phase 6 files were created.

- Current commit at the start of Phase 6: `b6f19d542680fbcae8cd061d9b93e167e1f98226`.
- Initial tracked working tree: no staged or unstaged tracked modifications were reported.
- Initial untracked outputs: none were reported by `git ls-files --others --exclude-standard`.
- Current authorized changes after the audit consist of Phase 6 documentation/tooling, the Phase 6 experiment-log append, and the verified blind-review correction in `PROGRESS_REPORT_FROM_14A39C9.md`.
- No Git commit, reset, clean, checkout, or deletion was performed.

Current tracked modifications are `docs/research/EXPERIMENT_LOG.md` and `docs/research/PROGRESS_REPORT_FROM_14A39C9.md`. Current untracked research outputs are the three `PHASE6_*.md` documents and the new files under `ml/grading_forecast/berry_grading/evaluation/phase6/`. These are the authorized products of this task; they were not present in the clean initial state.

Generated temporary/test directories exist under `.pytest_cache`, `backend/.pytest_cache`, `data/_tmp_tests`, `data/pytest-temp`, `data/tmp_perm_test`, and `data/tmp_py`. Git emitted permission warnings while attempting to enumerate several of them. The visible data temp directories contained no directly enumerable files, but inaccessible descendants prevent an absolute content claim. They were not deleted or changed.

No prior-phase artifact hash failed. The integrity validator found no unexpected changed path outside the authorized Phase 6/documentation scope.

## 2. Completed artifact inventory

The following required research records exist and were inspected:

- `docs/research/V3_DECISION_RECORD.md`
- `docs/research/V3_PHASE1_AUDIT.md`
- `docs/research/V3_PHASE2_YOLO_RESULTS.md`
- `docs/research/V3_PHASE3_REJECTION_RESULTS.md`
- `docs/research/V3_PHASE3_FOLLOWUP_REJECTION_RESULTS.md`
- `docs/research/PHASE4_PRICE_FOUNDATION_RESULTS.md`
- `docs/research/PHASE5_PRICE_FORECASTING_RESULTS.md`
- `docs/research/EXPERIMENT_LOG.md`

The related model, data, training, quality, evaluation, and price directories were resolved from the repository rather than assumed. Required manifests, model metadata, decision freezes, metrics, walk-forward predictions, and integrity records are present.

## 3. Model separation

| Artifact | Bytes | Modified UTC | SHA-256 |
|---|---:|---|---|
| Phase 2 `models/v3_yolo/best.pt` | 5,461,466 | 2026-10-06 20:10:21 | `c35cc40515adcb6130a4bc93e8ad3de161dcf46b263a9d7df8286a5b4239a9c4` |
| Phase 3 follow-up `models/v3_phase3_followup/best.pt` | 5,452,634 | 2026-10-07 10:23:31 | `e825278e0cf8eaff64cd05a2941cf96794e573027823a0ccd308bbc3f1a418ca` |

The paths, sizes, timestamps, and hashes differ. The files are not identical. The follow-up treatment did not replace the Phase 2 baseline.

## 4. V3 data immutability

The Phase 6 validator reused the Phase 1 manifest rather than regenerating the dataset.

- manifest rows: 775;
- current images matching recorded SHA-256: 775/775;
- annotation files matching the recorded class and box values: 775/775;
- annotation aggregate SHA-256 established by Phase 6: `9729e859b10cde8b9c6ba9bdaf103da424b90b0fea0ecafd7a1d08a04d952479`;
- physical sample groups: 194;
- partition counts: TRAIN 539, VALIDATION 116, TEST 120;
- physical-sample partition leaks: 0;
- accidental image movement or relabeling detected: no.

The Phase 1 split remains unchanged and the 120-row Phase 2 TEST remains identifiable.

The original Phase 2 test was frozen as historical baseline evidence, then intentionally re-evaluated under the frozen Phase 3 follow-up decision pipeline for regression analysis. Its original Phase 2 metrics remain preserved. It must not be described as never accessed.

## 5. Negative-set immutability and historical reuse

The original Phase 3 manifest remains identifiable with 80 images: 40 calibration and 40 evaluation. All 80 current files match their manifest hashes.

The original Phase 3 evaluation subset was intentionally reused after the follow-up model and threshold were frozen, solely for a controlled historical comparison. The original 35/40 result remains preserved.

The Phase 3 follow-up manifest remains identifiable with 250 images:

- 152 `NEGATIVE_TRAIN`;
- 49 `NEGATIVE_VALIDATION`;
- 49 `NEGATIVE_FINAL_HOLDOUT`;
- 172 source groups;
- 250/250 files matching manifest hashes;
- 250 unique exact hashes;
- zero source-group partition leaks.

## 6. Price artifact immutability

The Phase 4 canonical file matches its protected SHA-256 `ea800ea576817f07ad54d50317dbd68254fc5dc824447380e58688b6b711c0f6`. It contains 16,903 source-observed rows and retains the 2026-09-29 latest date.

The selected Phase 5 method specification, forecasting metrics, walk-forward predictions, and ten-row external-newest comparison all match their Phase 6 freeze hashes. The Phase 5 external observations remain separately identifiable.

No official EAC observations after the frozen 2026-09-29 cutoff are present. Therefore:

`NO NEW TEMPORAL PRICE EVALUATION AVAILABLE`

No Ridge refit, price-feature change, interpolation, Grade 2 synthesis, or retrospective tuning was performed.

## 7. Blind-review inconsistency resolution

The response file and concealed key were joined by `blind_id` and recalculated row by row. They contain 40 completed responses: 20 V3 Grade 1 and 20 V3 Grade 2 reference images.

Authoritative results from the underlying rows are:

- overall agreement: 32/40 = 80.0%;
- V3 Grade 1 agreement: 18/20 = 90.0%;
- V3 Grade 2 agreement: 14/20 = 70.0%;
- uncertain responses: 4/40, two in each reference class;
- agreement excluding uncertain responses: 32/36 = 88.9%;
- Cohen's kappa retaining `Uncertain` as a third response category: 0.636;
- supplementary binary kappa excluding uncertain responses: 0.778.

`V3_PHASE1_AUDIT.md` and the Phase 1 entry in `EXPERIMENT_LOG.md` already contained these correct figures. The later `PROGRESS_REPORT_FROM_14A39C9.md` incorrectly stated 85%/95%/75% and was corrected to the authoritative values. No response, concealed-key, Phase 1 metric, or original Phase 1 report was altered.

## 8. Prospective field-data readiness

Repository inspection found no path named or documented as a Phase 6, field, or prospective dataset. The only external image roots are the already-used Phase 3 original and follow-up negative collections. Existing V3 images, historical tests, and internet negatives cannot be reused and called prospective field validation.

| Item | State |
|---|---|
| Independent field dataset | Not available |
| Images | Unavailable |
| Physical samples | Unavailable |
| Smartphone devices | Unavailable |
| Independent reference labels | Unavailable |
| Hash/leakage result | Unavailable until data exists |
| Prospective evaluation | `BLOCKED_PENDING_FIELD_DATA` |

The collection protocol, manifest schema, fail-closed evaluator, metrics schema, and integrity validator are now available. No inference was run on historical data under a Phase 6 label.

## 9. Freeze declaration

- **PHASE 0: FROZEN**
- **PHASE 1: FROZEN**
- **PHASE 2: FROZEN**
- **PHASE 3: FROZEN**
- **PHASE 3 FOLLOW-UP: FROZEN**
- **PHASE 4: FROZEN**
- **PHASE 5: FROZEN**

This freeze prohibits automatic retraining, threshold optimization, dataset/model replacement, backend/mobile integration, ONNX/TFLite conversion, new price features, and new negative download campaigns. A later change requires explicit authorization and a separately defined research experiment.

## 10. Readiness decision

The historical freeze passes. Phase 6 preparation is complete, but the scientific evaluation cannot begin without genuinely new, independently labelled, grouped field data.

**Decision:** `COMPLETE — PREPARATION DONE, FIELD DATA BLOCKED`
