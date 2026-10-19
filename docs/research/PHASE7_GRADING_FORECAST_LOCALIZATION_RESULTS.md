# Phase 7 Grading and Forecast Localization Results

Date: 2026-10-08

## Objective

Add English, Sinhala, and Tamil presentation support to the authoritative
Berry Grading and Export Price Forecasting mobile workflow without changing
the frozen model, thresholds, Phase 5 evidence, Phase 6 decisions, API schema,
or rejection-first behavior.

## Implementation

All current grading screens now use the application's generated Flutter
localization catalog. This covers the component home, image capture, local
image validation, processing, retry/error state, grading result, rejection and
uncertainty reasons, market outlook, frozen-forecast disclaimer, research
limitations, and research-trace heading.

A presentation adapter maps the finite Phase 6 categories and grading values
to localized text only after `GradingForecastResult` has parsed and validated
the backend response. Internal values such as `GRADE_1`, `NO_PEPPER`,
`UNCERTAIN_GRADE`, `HIGH_UNCERTAINTY_OUTLOOK`, `Grade 1`, and `Grade 2` remain
unchanged for validation, routing, and traceability.

The API client now attaches a stable error kind to each safe failure class.
The UI localizes that kind rather than displaying arbitrary provider or
transport text. HTTP status behavior and the existing safe English diagnostic
message remain available to tests and logs.

## Scientific terminology safeguards

- V3 Grade 1 and V3 Grade 2 remain explicitly project-specific.
- Model scores remain labelled as scores, not calibrated probabilities.
- EAC prices remain farm-gate reference prices, not live prices or buyer offers.
- Frozen forecasts remain research forecasts, not buy/sell instructions.
- `UNCERTAIN_GRADE` remains a grading stop state and is not presented as
  `HIGH_UNCERTAINTY_OUTLOOK`.
- Rejected and uncertain results still cannot display market output.

## Verification

- Flutter localization generation completed for English, Sinhala, and Tamil.
- Direct Dart analysis of `mobile/lib` and `mobile/test` reported no issues.
- The focused grading localization/API/contract suite passed 12/12 tests.
- Tests cover Sinhala and Tamil screen rendering, localized Phase 6 value
  presentation, localized safe API errors, API validation, and strict Phase 7
  response invariants.
- The broader component-integration test still has two unrelated
  scanner-navigation failures in its widget harness; no pass is claimed for
  that full test file from this change.

## Unchanged research/runtime artifacts

No backend source, ONNX or PyTorch model, TFLite model, decision configuration,
price record, forecasting evidence, Phase 6 rule, API endpoint, or response
schema was modified.

## Limitations and manual acceptance

The translations have not received independent professional linguistic
review. An emulator or physical-device check is still required for text
wrapping, font rendering, right-sized controls, capture errors, all five
controlled grading outcomes, and the price screen in Sinhala and Tamil.

This change is deployment and accessibility engineering. It provides no new
predictive accuracy, field robustness, calibration, forecasting reliability,
or economic evidence.

## Status

`IMPLEMENTED; AUTOMATED FOCUSED VERIFICATION PASSED; DEVICE LINGUISTIC/UI REVIEW PENDING`.
