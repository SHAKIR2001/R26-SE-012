# Phase 5 — Price Movement Forecasting Research

**Status:** COMPLETE  
**Experiment:** `PRICE-EAC-PHASE5-001`  
**Date:** 2026-10-07  
**Phase 6 readiness:** READY WITH LIMITATIONS

## 1. Phase 5 objective

Determine whether short-term Grade 1 and Grade 2 pepper-price movement can be forecast more effectively than carrying the latest known DEA/EAC price forward. This phase ends with research predictions, evaluation, and uncertainty evidence. It does not implement a decision engine, application integration, deployment, or grade-price fusion.

## 2. Relationship to Phase 4

Phase 4 remains the frozen data foundation. Phase 5 read, but did not overwrite, `eac_reconstructed_v1`. Content hashes confirmed that the Phase 4 canonical dataset and both Phase 4 reports remained unchanged.

Phase 4 found that its separate Ridge model did not beat persistence consistently and predicted all five later Grade 1 movements downward even though all five rose. Phase 5 therefore tested new targets, smaller feature groups, statistical methods, and lightweight ML models without assuming that ML should win.

## 3. Research question

> Can short-term pepper-price movement be forecast more effectively than simply carrying the latest known market price forward?

The answer from this experiment is **partly, but not consistently**. The selected model improved validation and final-test return/price errors and direction recognition, but was fractionally worse than persistence on the ten later observations.

## 4. Dataset

Authoritative input:

```text
data/processed/grading_forecast/price/eac_reconstructed_v1/eac_pepper_price_canonical.csv
```

- Source: DEA Sri Lanka, Producers' Prices (Farm Gate) of EAC.
- Market/price type: National average farm-gate price.
- Coverage: 2016-10-04 through 2026-09-29.
- Canonical SHA-256: `ea800ea576817f07ad54d50317dbd68254fc5dc824447380e58688b6b711c0f6`.
- Missing observations were not interpolated, forward-filled, or replaced.
- The source is a historical market reference, not a real-time farmer/buyer quotation.

## 5. Grade 1 / Grade 2 coverage

| Series | Observations | Mean interval | Median | Maximum gap |
|---|---:|---:|---:|---:|
| Grade 1 | 493 | 7.41 days | 7 days | 49 days |
| Grade 2 | 358 | 10.22 days | 7 days | 231 days |

Grade 2 remains substantially less continuous. The modelling dataset preserves each grade separately and contains no fabricated Grade 2 value.

## 6. Forecast targets

Three next-observation movement targets were compared:

1. Simple return: `P(t+1) / P(t) - 1`.
2. Log return: `log(P(t+1) / P(t))`.
3. Absolute price change: `P(t+1) - P(t)`.

All candidate predictions were converted to an equivalent simple return and derived price for a common evaluation. Validation selected **log return** by the predefined metric hierarchy, although its advantage over simple return was small.

## 7. Forecast horizon

The primary and only evaluated horizon was the **next actual DEA/EAC observation**. Every prediction records its feature date, target date, and elapsed days. No fixed weekly, two-week, or four-week series was created because the source is irregular and a clean calendar target would require resampling or imputation.

## 8. Feature engineering

All features were available at or before the forecast date. Four controlled feature groups were evaluated:

- A — four completed-return lags plus days since the previous observation.
- B — A plus price level, rolling return means/volatility, momentum, and price-versus-rolling-mean trends.
- C — B plus cyclical day-of-year and month terms.
- D — C plus same-date observed G1/G2 spread, ratio, and other-grade completed return.

Validation selected the smallest group, **A_return_lags**. The larger technical and calendar groups worsened macro grade RMSE. Relationship features were evaluated only on a common 131-row cohort where both grades were genuinely observed; no missing Grade 2 values were filled.

## 9. Baselines

The following grade-specific baselines were evaluated:

- persistence / zero return;
- last observed return;
- expanding historical mean return;
- historical price drift, defined as `(current price - first historical price) / number of observed transitions`, converted to a return using the current price.

Seasonal naive was not used. Irregular observations and sparse Grade 2 history do not support a defensible fixed seasonal lag without resampling.

## 10. Statistical models

- Simple exponential smoothing of observed returns, with fixed alpha values 0.2 and 0.5.
- ARIMA(1,0,0) and ARIMA(2,0,0), implemented as conditional OLS autoregressions over completed returns.

`statsmodels` was unavailable. MA/ARMA variants were not recreated manually or added through a new dependency. The AR models provide the requested controlled autoregressive comparison without expanding the environment.

## 11. ML models

- Ridge, `alpha=1.0`, with `StandardScaler` fit separately inside each expanding training window.
- Random Forest, 100 trees, maximum depth 5, minimum leaf size 5, single-threaded deterministic execution.
- Gradient Boosting, 100 estimators, learning rate 0.05, maximum depth 2, minimum leaf size 5.

Each was evaluated as separate grade models and as a shared model with a grade indicator. Seed 42 was used. No deep-learning model, XGBoost dependency, or large search was introduced.

## 12. Walk-forward protocol

- Minimum training history: 50 completed target observations.
- Expanding window: a historical row entered training only after its target observation date was on or before the current forecast origin.
- No random split or shuffle.
- Ridge scaling was re-fit on the current training window only.
- Each later evaluation observation could enter subsequent windows only after its outcome would have become known.

The complete prediction CSV was regenerated twice after enabling single-threaded Random Forest. Its SHA-256 was identical on both runs: `D06F8C195A475E30EB78B5AEEDE55658DCFAAA0F5D09FECFDA6DE0F435B19E93`.

## 13. Validation/test separation

| Partition | Target-date range | Grade 1 | Grade 2 |
|---|---|---:|---:|
| TRAIN | 2016-10-11 to 2023-09-19 | 340 | 213 |
| VALIDATION | 2023-09-26 to 2025-02-25 | 73 | 66 |
| FINAL TEST | 2025-03-04 to 2026-08-18 | 74 | 73 |
| EXTERNAL NEWEST | 2026-08-25 to 2026-09-29 | 5 | 5 |

Feature group, target, formulation, algorithm, and hyperparameters were selected using validation only. Final test and external observations were not used for tuning.

## 14. External temporal reality check

The five later dates per grade were evaluated after selection was frozen. This is useful temporal evidence but is too small to establish production generalization.

| Grade | Reference date | Target date | Predicted movement | Forecast | Actual | Direction |
|---|---|---|---:|---:|---:|---|
| G1 | 2026-08-18 | 2026-08-25 | -0.01% | 1885.97 | 1892.43 | wrong |
| G1 | 2026-08-25 | 2026-09-01 | +0.18% | 1895.81 | 1918.57 | correct |
| G1 | 2026-09-01 | 2026-09-08 | +0.07% | 1919.94 | 1957.50 | correct |
| G1 | 2026-09-08 | 2026-09-15 | +0.04% | 1958.34 | 1987.50 | correct |
| G1 | 2026-09-15 | 2026-09-29 | +0.16% | 1990.60 | 1999.43 | correct |
| G2 | 2026-08-18 | 2026-08-25 | -0.15% | 1797.37 | 1800.00 | wrong |
| G2 | 2026-08-25 | 2026-09-01 | -0.15% | 1797.38 | 1740.00 | correct |
| G2 | 2026-09-01 | 2026-09-08 | +0.44% | 1747.62 | 1887.50 | correct |
| G2 | 2026-09-08 | 2026-09-15 | -1.59% | 1857.49 | 1940.00 | wrong |
| G2 | 2026-09-15 | 2026-09-29 | -0.46% | 1931.13 | 1890.00 | correct |

Unlike Phase 4 Ridge, Phase 5 correctly predicted four of the five later Grade 1 directions. This is encouraging directional evidence, not conclusive generalization.

## 15. Metrics

Primary metrics were return MAE and RMSE. R² is reported descriptively. Return MAPE was omitted because returns include and approach zero. Derived-price MAE, RMSE, and MAPE were calculated because eventual decision support requires an interpretable price. Direction reporting includes overall accuracy, non-flat accuracy, per-class precision/recall/F1, and a `[DOWN, FLAT, UP]` confusion matrix.

## 16. Model comparison

Validation feature ablation with separate Ridge/simple return:

| Feature group | Macro grade return RMSE | Macro grade return MAE |
|---|---:|---:|
| A — return lags | **0.04188** | **0.03121** |
| B — technical | 0.04633 | 0.03666 |
| C — technical + calendar | 0.04645 | 0.03593 |

On the common relationship-eligible cohort, the selected small feature group achieved RMSE 0.04182, whereas adding relationship features worsened it to 0.06090.

Validation target comparison with Ridge showed macro RMSE 0.04161 for separate log return, 0.04169 for separate price delta, and 0.04188 for separate simple return. Shared formulations were consistently slightly worse.

The final selected ML candidate was:

```text
Separate Grade 1 / Grade 2 Ridge
Target: next-observation log return
Features: four completed-return lags + days since previous observation
```

## 17. Directional performance

Final-test selected-model confusion matrix, rows actual and columns predicted `[DOWN, FLAT, UP]`:

```text
[[30, 0, 35],
 [11, 0,  4],
 [20, 0, 47]]
```

- Overall directional accuracy: 52.38%.
- Non-flat directional accuracy: 58.33%.
- DOWN precision/recall: 49.18% / 46.15%.
- UP precision/recall: 54.65% / 70.15%.
- FLAT precision/recall: 0% / 0%.

The continuous model never predicted an exact 0.01-LKR-resolution FLAT result. Direction performance is better than persistence's deterministic FLAT convention, but is still modest and asymmetric toward UP.

## 18. Derived-price performance

| Method | Return MAE | Return RMSE | Direction accuracy | Price MAE | Price RMSE |
|---|---:|---:|---:|---:|---:|
| Selected log-return Ridge | **0.01820** | **0.02985** | **52.38%** | **33.996** | **54.728** |
| ARIMA(1,0,0) conditional OLS | 0.01898 | 0.03037 | 46.94% | 35.56 | 56.11 |
| Persistence | 0.01858 | 0.03187 | 10.20% | 34.62 | 58.12 |
| Expanding mean return | 0.01924 | 0.03202 | 45.58% | 35.96 | 58.77 |
| Last observed return | 0.02991 | 0.05428 | 47.62% | 55.49 | 98.29 |

On final test, selected Ridge improved both return MAE and RMSE and both price MAE and RMSE relative to persistence. Its price MAPE was 1.815%, versus 1.853% for persistence.

## 19. Prediction intervals

A validation-calibrated empirical interval was implemented. For each grade, the 90th percentile of absolute validation return residuals was frozen and applied symmetrically around later predicted returns.

| Evaluation | Coverage | Mean width |
|---|---:|---:|
| Final test overall | 96.60% | 275.18 LKR/kg |
| Final Grade 1 | 94.59% | 96.26 LKR/kg |
| Final Grade 2 | 98.63% | 456.56 LKR/kg |
| External overall | 100% | 271.77 LKR/kg |

Although coverage exceeded the nominal 90%, Grade 2 intervals are extremely wide because validation residuals were volatile. These intervals are useful as empirical uncertainty diagnostics but are not sufficiently precise or externally validated for production confidence claims.

## 20. Error analysis

The largest selected-model errors were dominated by Grade 2. The five largest final-test errors ranged from approximately 160 to 216 LKR/kg. Several forecasts got direction correct while substantially underestimating movement magnitude—for example, Grade 2 on 2026-02-24 to 2026-03-03 was correctly predicted UP but missed by 215.64 LKR/kg.

The largest external error was Grade 2 on 2026-09-01 to 2026-09-08: direction was correctly UP, but the forecast was 1747.62 versus 1887.50, an error of 139.88 LKR/kg. This reinforces that direction correctness is not equivalent to accurate price magnitude.

## 21. Persistence comparison

**Did the selected Phase 5 model beat persistence? `MIXED`.**

- Validation: selected Ridge improved both macro-grade return MAE and RMSE.
- Final test: selected Ridge improved return MAE/RMSE and price MAE/RMSE.
- External newest check: selected Ridge was fractionally worse on return and price error.
- Direction: selected Ridge was materially more informative than persistence, which always predicted FLAT.

External comparison:

| Method | Return MAE | Return RMSE | Direction accuracy | Price MAE | Price RMSE |
|---|---:|---:|---:|---:|---:|
| Selected Ridge | 0.02330 | 0.03259 | **70%** | 42.83 | 58.54 |
| Persistence | **0.02305** | **0.03259** | 10% | **42.33** | **58.22** |

The external error differences are small, but they do not support a claim of consistent ML superiority.

## 22. Grade-specific findings

Final selected-model results:

| Grade | Return MAE | Return RMSE | R² | Direction accuracy | Price MAE | Price RMSE |
|---|---:|---:|---:|---:|---:|---:|
| Grade 1 | 0.00770 | 0.01066 | 0.0005 | 54.05% | 15.19 | 20.84 |
| Grade 2 | 0.02884 | 0.04098 | 0.1276 | 50.68% | 53.06 | 74.77 |

Grade 2 has substantially higher errors and much wider intervals. Only two validation forecasts followed a previous Grade 2 gap longer than 14 days, and none did in final test or the external check, so the effect of very long gaps cannot be estimated reliably from these evaluation partitions.

## 23. Feature-ablation findings

The strongest result came from the smallest feature group. Technical, calendar, and same-date grade-relationship features did not improve validation performance. This suggests that the available predictive signal is weak and concentrated in recent return dynamics rather than the larger engineered feature set. It also reduces the risk that model performance merely reflects the long-term price level.

## 24. Leakage/integrity validation

The automated Phase 5 integrity record verifies:

- Phase 4 canonical data and reports unchanged by SHA-256.
- All 775 V3 images still match their Phase 1 SHA-256 values.
- All 775 V3 annotation files still match the recorded class and box values.
- No tracked backend, mobile, V2, berry-grading, or other out-of-scope change.
- Canonical observations remain source-observed and duplicate-free.
- Every target occurs after its feature date.
- Target values reproduce the next observed price.
- Return lags are backward-looking.
- No random split or full-dataset scaling.
- Validation-only selection and minimum 50-observation training window.
- Persistence included in validation, final test, and external evaluation.
- All required Phase 5 artifacts present.

The complete walk-forward prediction artifact was also reproduced byte-for-byte with seed 42 and deterministic single-threaded Random Forest execution.

## 25. Limitations

- The source is a dated EAC market reference, not a live buyer quotation or guaranteed transaction price.
- Only 493 Grade 1 and 358 Grade 2 observations are available.
- Grade 2 has major historical gaps and substantially weaker magnitude accuracy.
- The external reality check contains only ten predictions.
- No model predicts FLAT effectively under the exact published-price rule.
- Important exogenous price drivers are absent.
- Empirical intervals—especially Grade 2—are too wide for strong operational claims.
- The selected model's validation advantage over alternate return targets is small.
- No fixed calendar horizon was tested because doing so cleanly would require a separately justified temporal construction.

## 26. Selected model/formulation

The selected research candidate is separate grade-specific Ridge regression over next-observation log return, using four completed-return lags and days since the previous observation. It has no single serialized checkpoint because the research protocol refits the estimator and scaler at every expanding forecast origin. `selected_model_spec.json` records the complete method.

## 27. Whether persistence was beaten

```text
MIXED
```

The selected formulation beat persistence in validation and final test, but not in the small external period. It should not replace persistence as an unqualified final production forecaster.

## 28. Research conclusion

Phase 5 found limited evidence of short-horizon predictive value beyond persistence. A small log-return Ridge formulation improved error and direction metrics on the main chronological evaluation and corrected four of the five later Grade 1 directions that Phase 4 missed. However, its external price error was slightly worse than persistence, Grade 2 errors remained large, and interval widths exposed substantial uncertainty.

The scientifically defensible conclusion is not “ML is superior.” It is that recent return lags contain some useful directional and magnitude information under the main temporal test, but the improvement is not yet consistent across the newest observations. Persistence remains an essential transparent comparator and fallback.

## 29. Phase 6 readiness

```text
READY WITH LIMITATIONS
```

The forecasting behavior is sufficiently understood for a separately authorized, controlled Phase 6 decision-support experiment, provided that:

- the forecast is treated as uncertain supporting evidence;
- persistence remains visible as a reference;
- dated EAC reference prices are never presented as live buyer prices;
- Grade 2 uncertainty is explicitly exposed;
- no production reliability claim is made;
- Phase 6 does not tune the Phase 5 model using final-test or external outcomes.

Phase 6 was not implemented.
