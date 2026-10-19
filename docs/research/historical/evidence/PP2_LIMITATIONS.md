# PP2 Limitations

Last updated: 2026-08-31

This document records limitations that must be stated honestly during PP2.

## Camera-Based Grading Limitation

The berry grading system is a camera-based visual estimation system. It can support visual grading indicators such as color, texture, visible defects, visible foreign matter, and rough apparent quality.

It cannot measure:

- moisture content;
- total ash;
- acid-insoluble ash;
- volatile oil;
- piperine;
- non-volatile ether extract;
- crude fibre;
- bulk density;
- laboratory-level hygiene or adulteration compliance.

Therefore, the system must not be presented as official SLS certification.

Recommended wording:

Camera-based visual estimate only. Chemical requirements and bulk density are not measured. Laboratory testing is required for official certification.

## Berry Dataset Limitations

Known limitations:

- Dataset is small for deep learning: 168 physical sample groups and 671 readable images.
- Multiple images from the same physical sample exist.
- Some samples have fewer or more than four images.
- Images were taken with at least two smartphone devices.
- Some images may have different orientations.
- Some images may have background-heavy framing.
- Some images may include hand, white paper, or metal sheet backgrounds.
- Some images may be blurred or less focused.
- Supporting labels such as size quality, color quality, texture quality, broken level, light berry level, pinhead level, mould, insect damage, and foreign matter are not manually verified for V2.
- V2 has five non-4-image samples: Grade 1 sample_028, Grade 1 sample_030, Grade 3 sample_010, Grade 1 sample_002, and Grade 1 sample_018.

Required mitigation:

- Use sample-level train/validation/test splitting.
- Do not split images from the same physical sample across different sets.
- Do not fabricate missing metadata.
- Use only automatically recoverable metadata for PP2.

## Price Dataset Limitations

Known limitations:

- The raw source is farm-gate market price data, not confirmed export transaction price data.
- Some weeks are missing from the source.
- Dates are mostly weekly but not perfectly regular.
- Grade 2 has sparse historical coverage, especially in earlier years.
- V2 National Grade 2 average has 161 observed dates only: 2022: 6, 2023: 27, 2024: 49, 2025: 49, 2026: 30.
- District-level Grade 2 coverage is inconsistent.
- Missing Grade 2 values must not be treated as zero.
- Missing Grade 2 values must not be invented or interpolated as if they were observed.

Required mitigation:

- Use National Grade 1 average farm-gate weekly price as the primary PP2 forecasting target.
- Document Grade 2 as a limitation and future work.
- Track missing weeks and temporal gaps.
- Avoid leakage-causing backfill from future data.

## Model Limitations

Berry:

- V1 MobileNetV2 was trained on an old 360-image dataset.
- V1 split had no separate test set.
- V1 Grade 2 recall was weak.
- V2 MobileNetV2 was evaluated on the leakage-safe sample-level test split with accuracy 0.8073, weighted F1 0.8076, and Grade 2 recall 0.8889.
- V1 and V2 metric differences are not directly equivalent because V2 uses a different expanded dataset and a sample-level train/validation/test methodology.
- V2 Grade 3 remains the weakest class by F1 in the completed baseline.
- The completed V2 model is still trained from a small dataset, so external generalization to new devices, lighting conditions, and backgrounds is not proven yet.
- Phase 4 tested only one berry improvement: dropout 0.25 -> 0.35.
- The Phase 4 berry dropout experiment did not improve the saved headline test metrics over the Phase 2 V2 baseline.
- Phase 4 berry `training_history.json` was not present in the `v2_phase4` artifact directory during finalization, so exact completed epoch counts are not available from saved artifacts.

Forecasting:

- V1 RandomForest had poor test R2.
- Price forecasting is short-horizon only.
- Phase 3 V2 forecasting used the National Grade 1 average farm-gate weekly target only.
- Grade 2 historical data remains too sparse for reliable primary forecasting.
- V2 lag and rolling features use previous available observations, not guaranteed previous calendar weeks, because the source has missing weekly intervals.
- No macroeconomic, export volume, weather, exchange rate, or global market features are included before PP2.
- RandomForest did not outperform Naive Persistence on the 36-row V2 test period.
- RandomForest is a baseline ML model, not an optimized final forecasting model.
- No hyperparameter search, advanced time-series model, or additional forecasting algorithm was evaluated in Phase 3.
- R2 may be unstable because the test period is short and may have limited variance.
- Phase 4 tested only one forecasting improvement: adding `lag_4`, `lag_8`, and `lag_12`.
- Phase 4 extended-lag RandomForest improved over the Phase 3 RandomForest baseline but still did not outperform Naive Persistence.
- The forecasting results should not be generalized beyond the current V2 dataset and 36-row test period.

## Integration Limitations

- Historical backend behavior could fall back to heuristic/demo mode if real model artifacts or input files were unavailable.
- Current post-Phase 11 runtime handling for this component is designed to fail safely and identify unavailable results instead of silently presenting legacy/demo outputs as research results.
- PP2/demo evidence must explicitly identify whether real artifacts or unavailable/fallback states were used.
- Phase 5 backend validation showed the grade-only and analyze endpoints returning HTTP 200 with real ONNX grading model use.
- Phase 5 runtime grading used the legacy/root ONNX artifact path, not the PP2 V2 or Phase 4 berry artifact directories; Phase 8 later integrated the selected Berry V2 ONNX runtime.
- Phase 5 price forecast endpoint returned `demo_baseline`, not the Phase 3 or Phase 4 V2 forecasting research artifacts; Phase 9 later replaced the real application forecasting path with `naive_persistence`.
- Phase 9 runtime forecasting uses Naive Persistence because it was the strongest validated V2 forecasting method and no inspected requirement forced the weaker trained RandomForest artifact into runtime.
- Phase 10 validated the existing recommendation rule table with real Phase 8 and Phase 9 runtime outputs, but the rules remain hard-coded and should be reviewed with domain/project stakeholders before final deployment.
- Phase 11 added focused backend hardening for image validation, V2 model failure handling, forecast unavailable handling, and safe API errors; it did not replace full production security, rate limiting, authentication, or Flutter end-to-end validation.
- Phase 11 corrective validation on 2026-08-30 fixed a Flutter multipart upload issue by validating actual image bytes instead of rejecting solely on unreliable client MIME values. Supported runtime upload formats are JPEG, PNG, and WEBP, with the existing 10 MB limit.
- Phase 12 implemented Firebase persistence for application-level result history, but live Firebase writes are not guaranteed unless credentials are configured.
- When Firebase is unconfigured or save fails, the current component returns `saved_to_firebase: false` and keeps the valid grading, forecast, and recommendation response available.
- Phase 12 validated mocked Firebase success and failure paths, but did not perform live Firebase validation because no credentials were configured.
- Stored records are currently application-level/non-user-scoped because no existing authenticated user identity was found for this component.
- Phase 12.5 diagnostic validation found that direct ONNX inference and backend service inference agreed on the selected 9-image V2 test sample, so a direct runtime class-mapping disagreement was not confirmed.
- Phase 12.5 confirmed a training-vs-runtime preprocessing mismatch for later review: training used direct 224x224 resize, while backend runtime uses RGB letterbox to 224x224 before ONNX inference.
- The 9-image diagnostic sample showed weak Grade 2 behavior, but it is not a replacement for the saved full-test evaluation.
- Runtime forecasting currently uses a single National Grade 1 average weekly `naive_persistence` series, so forecasts do not vary by berry grade.
- If grade-specific price forecasts are required later, they need a separate documented design decision and supporting data validation.
- Flutter flow exists and points to the backend endpoints, but Flutter was not run during Phase 5.
- Phase 13 added an offline Flutter TFLite fallback after hosted-backend timeout/rate-limit testing, but successful Flutter build/device validation is still pending.
- The offline TFLite model is an export of the existing selected V2 Keras model, not a retrained model and not new evaluation evidence.
- Offline mobile visual-feature extraction is implemented in Dart and should be compared against the backend OpenCV-derived feature values before final reporting.
- Offline mobile forecasting uses the bundled National Grade 1 average weekly series and `naive_persistence_mobile`; it remains single-series and not grade-specific.
- Offline mobile mode does not write to Firebase. It returns `saved_to_firebase: false`; backend mode is still required for live Firestore persistence.
- The Grade 2 predicted market price is an estimated adjustment, not an independently trained Grade 2 forecast. It subtracts a rounded 100 LKR/kg discount derived from the latest observed National average Grade 1 vs Grade 2 gap.
- Grade 3 predicted market price is intentionally unavailable because there is no reliable Grade 3 historical price series in the current market dataset.

## Script Safety Limitation

Several older scripts still default to V1 output paths. Accidentally running them without V2-specific arguments can overwrite old label or processed CSV artifacts. Before using any old data-preparation script, check its default input/output paths and prefer the V2 scripts created for Phase 1.

For berry model work after Phase 2, do not run the V1 default training/evaluation/export commands unless the intention is explicitly to reproduce V1. Use the explicit V2 arguments recorded in `docs/research/EXPERIMENT_LOG.md` and keep all V2 model outputs under `ml/grading_forecast/berry_grading/models/v2/`.

For price forecasting after Phase 3 preparation, do not run the no-argument forecasting commands for V2 work. Use explicit `price_v2`, `models/v2`, and `_outputs/v2` paths so V1 artifacts are not overwritten.

## PP2 Scope Limitations

Not required before PP2:

- LSTM.
- ARIMA/SARIMA.
- XGBoost.
- Prophet.
- Segmentation-based berry isolation.
- Manual annotation of detailed visual defect labels.
- Full Firebase deployment validation.
- TFLite/on-device inference before PP2. A post-PP2 offline fallback has been implemented, but build/device validation is still pending.
- Production deployment.

## Phase 6 Documentation Limitation

Phase 6 was documentation-only. It organized and verified existing evidence for PP2 presentation readiness. It did not rerun experiments, recalculate metrics, regenerate figures, start the backend, run Flutter, modify datasets, or modify model artifacts.
