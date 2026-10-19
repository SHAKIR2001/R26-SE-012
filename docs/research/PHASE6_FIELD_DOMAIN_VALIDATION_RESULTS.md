# Phase 6 Field and Domain-Shift Validation Results

> **Roadmap clarification:** This blocked/preparation result belongs to the later external field/domain-shift validation stage. It is not the original Phase 6 “Combine grade + price” result, which is documented separately in `PHASE6_GRADE_PRICE_DECISION_ENGINE_RESULTS.md`. No field evaluation is executed by the grade-price fusion phase.

**Status:** `COMPLETE — PREPARATION DONE, FIELD DATA BLOCKED`  
**Prospective evaluation:** `BLOCKED_PENDING_FIELD_DATA`  
**Date:** 2026-10-07

## 1. Executive summary

Phases 0-5 and the Phase 3 follow-up passed the Phase 6 freeze audit. No independent prospective field dataset exists in the repository, so no Phase 6 image inference or field metric was produced. Producing results from V3 or the Phase 3 internet datasets would mislabel historical evidence as prospective validation. The collection protocol, manifest schema, fail-closed evaluation tooling, metrics schema, and integrity record are complete.

No new EAC observation after 2026-09-29 is present, so no additional temporal price evaluation was possible.

## 2. Phase 6 research question

> How well does the frozen berry grading and rejection pipeline generalize to genuinely new, field-like images captured under different acquisition conditions, and what failure modes remain before prospective deployment evaluation?

This question remains empirically unanswered because the required data is unavailable.

## 3. Frozen baseline definition

The system to be evaluated once data becomes available is fixed as:

- Phase 3 follow-up model SHA-256 `e825278e0cf8eaff64cd05a2941cf96794e573027823a0ccd308bbc3f1a418ca`;
- frozen decision configuration `v3_phase3_followup/decision_config_frozen.json`;
- minimum blur variance 10;
- minimum brightness 50;
- minimum dimension 320;
- minimum detected box-area ratio 0.20;
- detection confidence 0.05;
- grade confidence 0.05;
- class margin 0.30.

No model or threshold was changed.

## 4. Freeze verification

The Phase 6 integrity artifact reports 29 PASS, 0 FAIL, and one UNAVAILABLE field-data check. Both model checkpoints are separate and match their recorded hashes. All 775 V3 image hashes and 775 annotation values match. The Phase 3 datasets and Phase 4/5 price artifacts remain identifiable and hash-consistent.

The original Phase 2 test and original Phase 3 evaluation were intentionally reused only for frozen follow-up comparisons; their original historical results remain preserved.

## 5. Dataset provenance

No repository dataset has documented independent Phase 6 field provenance. The two `data/external` collections are internet-negative datasets already used by Phase 3 and cannot satisfy this phase.

Field dataset, images, samples, devices, capture conditions, and independent labels are unavailable.

## 6. Field-data collection methodology

The prospective methodology is frozen in `PHASE6_FIELD_DATA_PROTOCOL.md`. It requires multi-device smartphone capture, varied natural lighting/background/framing, positive and negative conditions, stable physical-sample grouping, independent labels, a calibration subset, and a sealed final evaluation subset.

## 7. Independence and leakage checks

Historical checks pass: V3 sample isolation, negative source-group isolation, image hashes, annotations, manifests, models, and price artifacts remain consistent.

Phase 6 Gate A is unavailable—not failed—because no populated manifest exists. The validator will require unique hashes, zero overlap with all 1,105 prior V3/negative images, physical-group isolation, independent label-source records, valid paths, and valid file hashes before inference.

## 8. Decision pipeline

`evaluate_phase6_field.py` verifies the manifest and frozen model hash before loading YOLO. It uses the frozen decision configuration and writes image decisions, structured errors, grading/rejection metrics, physical-sample results, and count-aware domain breakdowns. It contains no training or threshold-search path and fails closed on absent or invalid data.

## 9. Overall results

Unavailable. Total images, accepted, rejected, uncertain, coverage, and error rates are recorded as `null`, not zero, in `phase6_metrics.json`.

## 10. Grading results

Unavailable. No independently verified prospective pepper grades exist.

Frozen internal evidence remains separate: Phase 2 test accuracy 95.83% and macro F1 0.9578; follow-up regression coverage 98.33%, accuracy 95.83%, and macro F1 0.9643. These are not Phase 6 field results.

## 11. Rejection results

Unavailable for prospective data.

Frozen internet-negative evidence remains separate: original Phase 3 rejection 35/40 (87.5%); follow-up new holdout rejection 49/49 (100%); follow-up retrospective rejection on the original Phase 3 evaluation 40/40 (100%). These results do not prove universal or field rejection.

## 12. Domain-shift breakdown

Unavailable. There are no independent device, lighting, background, framing, density, quality, or negative-category field denominators.

## 13. Physical-sample analysis

Unavailable. No prospective physical-sample groups or independent sample-level truth exist.

## 14. Error analysis

No Phase 6 predictions were made, so no Phase 6 errors exist to record. The evaluator will create `phase6_error_analysis.csv` after a valid evaluation; creating populated errors now would fabricate evidence.

## 15. Price temporal evaluation

`NO NEW TEMPORAL PRICE EVALUATION AVAILABLE`

The frozen canonical EAC series ends on 2026-09-29. No later official observations exist in the repository. Phase 5 Ridge and persistence were not refit or reevaluated.

## 16. Comparison with frozen baselines

No prospective comparison is possible. The internal V3 test, internet-negative benchmarks, and Phase 5 temporal results remain three separate evidence sources. They are not pooled into an artificial overall accuracy.

## 17. Failure modes

Unresolved risks remain camera/device confounding, lighting/background changes, distance and partial framing, containers/surfaces, mixed or sparse pepper, occlusion, small pepper regions, blur/low light, vegetation/crop/object false positives, and uncalibrated uncertainty. Their field frequency and impact remain unknown.

## 18. Limitations

- No independent field images or labels are available.
- Exact-hash checking cannot address semantic duplication until data exists.
- Internal grading labels remain project-specific and are not official-grade evidence.
- Model confidence remains uncalibrated.
- Existing negative benchmarks are internet-domain evidence.
- The price signal remains limited, persistence remains strong, Grade 2 error/intervals remain large, and exogenous variables remain absent.

## 19. Acceptance-gate results

| Gate | Result | Reason |
|---|---|---|
| A — Dataset independence | UNAVAILABLE | No Phase 6 field manifest/data |
| B — Grading performance | UNAVAILABLE | No prospective reference grades |
| C — Rejection performance | UNAVAILABLE | No prospective positives/negatives |
| D — Domain-shift stability | UNAVAILABLE | No acquisition-condition groups |
| E — Uncertainty behavior | UNAVAILABLE | No prospective decisions |

The historical freeze is PASS. The prospective gates are unavailable rather than passed or failed.

## 20. Research conclusion

Phase 6 infrastructure and protocol are complete, but prospective field evaluation is blocked because no independent field dataset is currently available. This is the scientifically valid outcome. Generalization cannot be assumed from strong controlled internal and internet-negative results.

## 21. What Phase 6 does not prove

This phase does not prove production readiness, camera independence, universal non-pepper rejection, calibrated confidence, SLS/buyer/export-grade equivalence, field grading accuracy, live buyer pricing, consistent forecasting superiority, or safe automated decisions.

## 22. Recommended next research question

After a protocol-compliant dataset is collected and sealed:

> Does the unchanged Phase 3 follow-up pipeline retain acceptable grading coverage and non-pepper rejection across independently labelled physical samples, devices, lighting, backgrounds, and framing conditions, and where does performance materially degrade relative to the frozen internal benchmarks?

If the frozen pipeline performs poorly, record the failure. Any improvement becomes a separately authorized Phase 7 experiment and must not tune on the Phase 6 final set.
