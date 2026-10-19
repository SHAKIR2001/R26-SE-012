# Phase 6 — Grade + Price Decision Engine Results

**Status:** `COMPLETE WITH LIMITATIONS`  
**Experiment:** `PHASE6-GRADE-PRICE-DECISION-001`  
**Evaluation type:** `HISTORICAL COMPOSITIONAL EVALUATION`  
**Date:** 2026-10-07

> Phase 6 is a deterministic decision-support fusion layer. It does not create a new predictive model and does not demonstrate independent end-to-end field performance.

## 1. Executive summary

Phase 6 implemented a transparent rule-based layer that combines a frozen berry grading/rejection result with a matching grade-specific frozen Phase 5 forecast record. Rejection and grading uncertainty stop the pipeline before pricing. Accepted V3 Grade 1 routes only to Grade 1 EAC evidence; V3 Grade 2 routes only to Grade 2. Latest observed reference price, forecast price, persistence, interval, direction, signal limitation, source, and model provenance remain structurally separate.

The evaluation used 13 empirical-compositional scenarios—ten recorded external Phase 5 forecasts combined with ten same-grade recorded grading decisions, plus one recorded non-pepper rejection, one quality rejection, and one uncertain grade—and 15 explicitly synthetic logic tests. All 28 scenarios matched their predeclared categories. The focused 15-test unit suite and all 33 integrity checks passed. Two deterministic evaluation runs were identical.

All ten empirical accepted scenarios were classified `HIGH_UNCERTAINTY_OUTLOOK` because their validation-derived intervals crossed the contemporaneous reference price. This exposes, rather than hides, the weak directional certainty in the frozen evidence. It is not a finding that Phase 6 improved forecast accuracy.

## 2. Phase 6 research question

> Can the frozen berry grading/rejection result and the frozen grade-specific price forecast be combined into a transparent decision-support output that is useful for interpreting the expected market outlook of a pepper sample while explicitly representing rejection, uncertainty, grade, current reference price, forecast movement, and forecast limitations?

**Answer:** yes at the deterministic logic, traceability, and research-presentation level. Whether this representation is more useful to real users requires a later user/field study; no human-usefulness claim is made from compositional scenarios alone.

## 3. Frozen grading baseline

- Model: `ml/grading_forecast/berry_grading/models/v3_phase3_followup/best.pt`
- SHA-256: `e825278e0cf8eaff64cd05a2941cf96794e573027823a0ccd308bbc3f1a418ca`
- Decision configuration SHA-256: `39ca99a7e0049fb620a141cde80d539700945b2f812cc6cf7b15f289f8e158b8`
- Frozen thresholds: blur 10, brightness 50, minimum dimension 320, minimum area ratio 0.20, detection/grade confidence 0.05, margin 0.30.

The adapter accepts only the frozen decisions `GRADE_1`, `GRADE_2`, `NO_PEPPER`, `POOR_IMAGE`, and `UNCERTAIN_GRADE`, plus the Phase 6 sample-level state `CONFLICTING_SAMPLE_VIEWS`. V3 grades remain project-specific sample/batch labels, not official, certified, per-berry, SLS, buyer, or laboratory grades.

## 4. Frozen price baseline

The engine references the unchanged Phase 4 canonical EAC dataset and Phase 5 method/results. The selected method is separate grade-specific Ridge over next-observation log return with four completed-return lags and observation gap. It has no single serialized checkpoint: the Phase 5 research protocol refits the estimator/scaler at each expanding origin. Phase 6 therefore consumes recorded frozen Phase 5 forecast outputs; it does not refit Ridge or claim a new forecast after the 2026-09-29 cutoff.

The preserved conclusion is `MIXED`: Ridge improved validation and final-test error but was fractionally worse than persistence on the ten newest external error metrics. The output labels prices as **EAC farm-gate reference prices**, not buyer offers, live transactions, export contracts, guaranteed values, or trading signals.

## 5. Decision-engine architecture

```text
frozen grading result
        |
        +-- NO_PEPPER / POOR_IMAGE ----------> REJECT; market unavailable
        +-- UNCERTAIN / conflicting views ----> UNCERTAIN; market unavailable
        |
        +-- accepted V3 grade
                 |
                 +-- strict one-to-one grade route
                 +-- grade-specific EAC reference and frozen forecast record
                 +-- exact Phase 5 direction rule
                 +-- interval and persistence interpretation
                 +-- category, explanation, limitations, trace
```

There is no learned fusion model, composite score, hidden weight, price discount, cross-grade average, interpolation, or autonomous action.

## 6. Input/output contract

Grading input records decision, grade, model/detection scores, margin, quality status, rejection reason, input ID, and optional physical-sample ID. Market input records grade-specific reference date/price, previous observed price, observed return, predicted log/simple return, forecast price, validation-derived interval, persistence price, comparison context, target date, source URL, and evidence partition.

Accepted output contains separate `grading`, `market`, `decision_support`, and `trace` objects. Latest reference price and forecast price occupy different fields and carry different interpretations. Rejected/uncertain outputs have null market values. Confidence is labelled a model score, not a probability.

## 7. Grade-to-price routing

| Grading result | Permitted price series | Model scope |
|---|---|---|
| V3 Grade 1 | Grade 1 | Separate Grade 1 Ridge |
| V3 Grade 2 | Grade 2 | Separate Grade 2 Ridge |
| Invalid/unknown grade | None | Fail closed |

An explicit mismatch raises an error. Phase 6 never averages grades, applies a Grade 2 discount, infers one grade from the other, or synthesizes a missing observation.

## 8. Rejection/uncertainty propagation

`NO_PEPPER` and `POOR_IMAGE` produce `REJECT`; price output is unavailable. `UNCERTAIN_GRADE` produces the same-named category with no grade-specific routing. Multi-image aggregation preserves individual views; a sample routes only when at least one view is accepted, all accepted views have one grade, and majority/confidence-weighted grades agree. Conflicting accepted grades produce `CONFLICTING_SAMPLE_VIEWS` and no market outlook.

Missing grade-specific reference price produces `PRICE_DATA_UNAVAILABLE`. Missing frozen forecast produces `FORECAST_UNAVAILABLE`. Neither path fabricates a replacement.

## 9. Direction rule

Phase 6 reuses the Phase 5 rule exactly:

1. Round reference and forecast prices to the published resolution of 0.01 LKR.
2. Forecast greater than reference: `UP`.
3. Forecast lower than reference: `DOWN`.
4. Equal rounded values: `FLAT`.

No near-flat percentage band was added or tuned.

## 10. Forecast signal interpretation

- `HIGH_UNCERTAINTY`: the validation-derived interval contains prices on both sides of the reference price, so it does not support one direction exclusively.
- `RELATIVE_SUPPORT`: Ridge is documented as better than persistence for the supplied evaluation context and the interval does not cross the reference.
- `LIMITED_SIGNAL`: default; also used when persistence is better or the evidence remains mixed.

These are evidence labels, not calibrated probabilities. Intervals remain explicitly “validation-derived forecast intervals.” Wide intervals are exposed.

## 11. Decision-support categories

- `REJECT`
- `UNCERTAIN_GRADE`
- `CONFLICTING_SAMPLE_VIEWS`
- `PRICE_DATA_UNAVAILABLE`
- `FORECAST_UNAVAILABLE`
- `UPWARD_PRICE_OUTLOOK`
- `DOWNWARD_PRICE_OUTLOOK`
- `FLAT_PRICE_OUTLOOK`
- `HIGH_UNCERTAINTY_OUTLOOK`

No category instructs a user to buy, sell, transact, or expect profit.

## 12. Historical compositional evaluation

The 13 empirical scenarios are not a joint real-world dataset. They compose separately frozen evidence to validate routing and presentation:

- 10 accepted grading outputs paired deterministically with same-grade Phase 5 external forecast rows;
- 1 recorded `NO_PEPPER` case;
- 1 recorded `POOR_IMAGE` case;
- 1 recorded `UNCERTAIN_GRADE` case.

Results:

| Measure | Result |
|---|---:|
| Empirical scenarios | 13 |
| Market outlooks produced | 10/13 = 76.92% |
| Rejected | 2/13 = 15.38% |
| Uncertain | 1/13 = 7.69% |
| Accepted empirical outlook category | 10/10 high uncertainty |

The high-uncertainty result follows directly from the existing intervals crossing each reference price. It does not alter the recorded Phase 5 direction or price errors.

## 13. Logic-test evaluation

Fifteen deterministic tests covered non-pepper, quality rejection, uncertain grade, Grade 1/2 up/down routing, exact flat direction, conflicting views, missing price, missing forecast, wide interval, persistence better, Ridge better, and invalid grade/series mismatch. All 15 passed.

Synthetic numbers appear only in rows labelled `LOGIC_TEST` and `SYNTHETIC_LOGIC_TEST_NOT_EMPIRICAL`. They test branches and are never presented as observed research measurements.

## 14. Decision consistency results

| Check | Result |
|---|---:|
| Total scenario expectations | 28/28 passed |
| Grade 1 routing checks | 12/12 correct |
| Grade 2 routing checks | 7/7 correct |
| Rejection blocking checks | 4/4 correct |
| Uncertainty/conflict blocking checks | 3/3 correct |
| Combined blocking checks | 7/7 correct |
| Deliberate wrong-series request | Failed closed |
| Fabricated empirical values | None |
| Hidden composite score | None |
| Integrity checks | 33/33 passed |
| Two deterministic in-memory evaluations | Identical |

The scenario CSV SHA-256 is `7f1505070848d393c295e3d8aa49366c725a402b21fdc9b9725e27a51e10373d`; the trace CSV SHA-256 is `75f93026c3cd2c209b4fa14db3cb4702e9295c98c98c53ebde28b789f390d0bc`.

## 15. Explainability and traceability

All 28 traces contain a category, explanation, grading-model hash, decision-config hash, and—where applicable—price series, dated reference price, Phase 5 model-specification hash, return, forecast, direction, persistence, and signal class. The configured timestamp is fixed for reproducible research artifacts. No personal information is stored.

## 16. Limitations

- Grading and price evidence were collected separately; composition is not an independent end-to-end test.
- No human-subject usefulness evaluation compared combined versus disconnected presentation.
- Synthetic logic tests demonstrate code behavior only.
- Phase 5 signal is limited/mixed and persistence won the newest external error comparison.
- Grade 2 price error and intervals are substantially larger than Grade 1.
- The selected price method has no single serialized fitted checkpoint; future forecast generation requires a deliberate implementation of the frozen expanding-window specification.
- V3 grading has unresolved field/device/domain-shift risk and project-specific labels.
- Confidence is uncalibrated, and interval coverage does not imply a guaranteed future-price probability.

## 17. What Phase 6 proves

Phase 6 demonstrates that frozen grading/rejection and recorded grade-specific price forecasts can be combined into one deterministic, reproducible, rejection-first, grade-consistent, traceable research output. It demonstrates correct routing, uncertainty propagation, missing-data behavior, provenance, and explicit limitations across the defined scenarios.

## 18. What Phase 6 does NOT prove

It does not prove improved grading or forecasting accuracy, causal value from combining modalities, independent end-to-end performance, field robustness, calibrated confidence, official grading, user usefulness, live pricing, a guaranteed forecast, production readiness, or the safety/profitability of any buying or selling decision.

## 19. Research conclusion

The original Phase 6 objective is complete with limitations. The answer to “can grade and grade-specific price outlook be combined transparently?” is yes. The engine adds coherent routing and interpretation, not new predictive evidence. Its most important empirical behavior is conservative: all ten accepted external compositional scenarios surface high directional uncertainty rather than presenting weak price movements as strong advice.

The earlier freeze/field documents remain preserved as preparation for the later external-validation stage and are not evidence for this fusion experiment.

## 20. Phase 7 readiness

`READY WITH LIMITATIONS FOR A SEPARATELY AUTHORIZED INTEGRATION SPECIFICATION`

The input/output contract, categories, strict routing, missing-data behavior, trace fields, and scientific wording are sufficiently specified for later ONNX/TFLite/backend/mobile planning. Phase 7 was not started. A later implementation must decide how to package or execute the Phase 5 expanding-window forecast method without silently treating its research specification as a serialized production model.

The prospective field protocol remains available for the later external/field-validation stage. It was not executed in this phase.
