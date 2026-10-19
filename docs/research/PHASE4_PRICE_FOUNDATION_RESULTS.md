# Phase 4 — Price Data Reconstruction and Market-Aware Forecasting Foundation

**Status:** COMPLETE  
**Date:** 2026-10-07  
**Dataset version:** `eac_reconstructed_v1`  
**Research boundary:** price-data reconstruction and controlled forecasting foundation only; no application integration or deployment

## A. Executive summary

The previous price pipeline was not suitable as the final research formulation. It modelled the next absolute Grade 1 price, was decisively worse than naive persistence in its historical V2 test, and the runtime therefore returned the latest known Grade 1 observation as the forecast. Grade 2 was not independently forecast: runtime artifacts used an observed latest gap and a 113 LKR/kg fallback discount.

Phase 4 rebuilt the price foundation from the Department of Export Agriculture (DEA), Sri Lanka, Economic Research Unit's public **Producers' Prices (Farm Gate) of EAC** dated pages. The reconstruction preserves page-level provenance and actual Grade 1 and Grade 2 observations. It contains 16,903 pepper observations from 2016-10-04 through 2026-09-29, including 493 National Grade 1 average observations and 358 National Grade 2 average observations. Missing Grade 2 values remain missing.

The primary target is now the **percentage return to the next observed EAC observation**. A predicted future price is derived from the dated reference price and predicted movement:

```text
derived forecast = reference price × (1 + predicted return)
```

This explicitly separates the latest known market reference from a forecast. It does not claim a real-time buyer quote or guaranteed transaction price.

A controlled expanding-window comparison evaluated three baselines and four lightweight model/formulation combinations. Separate Ridge was the best ML candidate on the predefined validation model-selection score, but it did **not** beat zero-return persistence on validation. On the final temporal test, it improved return RMSE and directional accuracy, but persistence retained lower return and price MAE. It also failed to beat persistence on the ten newest grade observations. The data foundation is ready for Phase 5 research, but no tested Phase 4 ML model is justified as a superior production forecast.

## B. Existing-data audit

The complete pre-implementation audit is recorded in `docs/research/PHASE4_PRICE_DATA_AUDIT.md`.

| Item | Historical state |
|---|---|
| Principal local raw artifact | `data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv` |
| Claimed versus actual coverage | Filename says 2016–2026; observed range was 2021-02-22 to 2026-08-18 |
| Rows/source dates | 7,742 rows / 232 dates |
| National averages | Grade 1: 232; Grade 2: 161 |
| Provenance limitation | Every row used the index URL rather than its dated source page |
| V2 target | Next absolute National Grade 1 average price |
| V2 learned-model result | Random Forest MAE 82.42, RMSE 88.45, R² -0.474 |
| V2 persistence result | MAE 16.41, RMSE 22.52, R² 0.905 |
| Runtime forecast | Naive persistence: forecast equals latest observation |
| Grade 2 runtime behavior | Latest observed gap plus hard-coded 113 LKR/kg fallback |

The existing local series was incomplete. The authoritative index contained earlier history and five observation dates after its 2026-08-18 cutoff. Historical V2 data, scripts, models, results, backend behavior, and mobile artifacts were preserved without modification.

## C. Source provenance

Primary source:

- Publisher: Department of Export Agriculture, Sri Lanka — Economic Research Unit.
- Series: Producers' Prices (Farm Gate) of EAC.
- Index: `https://exagri.info/mkt/index.html`.
- Retrieval date: 2026-10-07.
- Index snapshot SHA-256: `29f5c5a656177c9e83518233cbd7eeff3d78d6dc5cf1b7aaf4e12c041cb681b5`.
- Pages indexed: 495 dated links; 493 successfully parsed pepper pages.
- Broken source links retained explicitly: 2023-04-25 and 2026-06-23.

Each observation retains its observation date, market, commodity, grade, price type, price, source organization, exact dated page URL, source date, retrieval date, page hash, table type, and market level. The raw index snapshot and extracted source observations are separate from the processed canonical and model-ready datasets.

The source is a published historical farm-gate market-reference series. It is not automatically a farmer's current buyer offer, export contract price, or guaranteed transaction value.

## D. Reconstructed dataset

| Measure | Result |
|---|---:|
| Canonical pepper observations | 16,903 |
| Unique source dates | 493 |
| Full date range | 2016-10-04 to 2026-09-29 |
| National Grade 1 averages | 493 |
| National Grade 2 averages | 358 |
| Dates with both national grades | 358 |
| Dates missing National Grade 1 relative to union | 0 |
| Dates missing National Grade 2 relative to union | 135 |
| Exact duplicate canonical keys | 0 |
| Conflicting duplicates | 0 |

The old local artifact ended on 2026-08-18. The reconstruction adds five genuinely later dates for each national grade: 2026-08-25, 2026-09-01, 2026-09-08, 2026-09-15, and 2026-09-29. Across the full history, it contains 261 more National Grade 1 rows and 197 more National Grade 2 rows than the old local artifact; this difference includes earlier recovered history as well as the five later dates.

No row was generated for a source dash, missing table value, or broken page. There was no interpolation, forward filling, fixed Grade 2 discount, resampling, or model-generated replacement in the canonical observations.

## E. Grade relationship

Spread and ratio were calculated only for the 358 dates on which both national averages were observed:

```text
spread = Grade 1 price - Grade 2 price
ratio  = Grade 2 price / Grade 1 price
```

| Statistic | G1-G2 spread (LKR/kg) | G2/G1 ratio |
|---|---:|---:|
| Mean | 93.99 | 0.924 |
| Median | 62.19 | 0.935 |
| Minimum | -42.87 | 0.718 |
| Maximum | 549.71 | 1.032 |
| Standard deviation | 86.19 | 0.051 |

Grade 2 was above Grade 1 on 9 of 358 overlap dates, so a fixed positive Grade 1 premium is not universally supported. The relationship also changed over time: annual mean spread was about 36.89 LKR/kg in 2018, 180.22 in 2024, and 102.77 in 2026. This evidence rejects an invariant 100/113 LKR discount assumption and supports treating Grade 2 as a first-class observed series.

## F. Data quality

The series is approximately weekly but not perfectly regular.

| Grade | Observations | Min interval | Median | Mean | Max |
|---|---:|---:|---:|---:|---:|
| Grade 1 | 493 | 3 days | 7 days | 7.41 days | 49 days |
| Grade 2 | 358 | 3 days | 7 days | 10.22 days | 231 days |

Grade 1 has three gaps longer than 14 days. Grade 2 has materially weaker historical continuity, particularly during 2020–2023, including a 231-day maximum gap. Grade 2 observations by year fell to 5 in 2021 and 6 in 2022 before recovering to 48 in 2024 and 51 in 2025. This makes Grade 2 evidence weaker and more regime-dependent than Grade 1 evidence.

The research plots show every observed point and break connecting lines across gaps longer than 14 days; they do not visually imply interpolated weekly values.

The source manifest contains no duplicate dated page URLs or duplicate non-empty page hashes. Two public index links were broken and were not silently filled. Complete interval and gap lists are available in `eac_pepper_price_quality_report.json`.

## G. Forecast target and leakage controls

**Primary target:** next-observation percentage return:

```text
return(t+1) = P(t+1) / P(t) - 1
```

The model-ready dataset also contains log return and direction. Actual direction is `UP`, `DOWN`, or `FLAT`, where `FLAT` means exact equality in the source-published price. For continuous predictions, `FLAT` means that the derived price equals the reference after both are rounded to the source resolution of 0.01 LKR. No arbitrary percentage band was introduced.

**Horizon:** the next observed EAC market observation. Actual intervals are retained; no artificial daily or weekly rows were created.

Features are deliberately small and backward-looking:

- reference price at `t`;
- prices at `t-1` and `t-2`;
- return at `t` and return at `t-1`;
- three-observation rolling price mean;
- three-observation rolling return standard deviation;
- days since the previous observation;
- grade indicator for shared models only.

The model-ready dataset contains analytical same-date spread and ratio, but they were not used in the initial models because their inclusion would discard Grade 1-only dates and disproportionately reduce evidence. Scaling for Ridge was fit separately inside every expanding training window. A row was eligible for training only when its next-observation target date was on or before the current forecast origin.

## H. Temporal protocol

The boundaries were established over target dates at or before the old local cutoff. The five later dates per grade were isolated before model selection.

| Partition | Target-date range | Grade 1 rows | Grade 2 rows |
|---|---|---:|---:|
| TRAIN | 2016-10-11 to 2023-09-19 | 340 | 213 |
| VALIDATION | 2023-09-26 to 2025-02-25 | 73 | 66 |
| FINAL TEST | 2025-03-04 to 2026-08-18 | 74 | 73 |
| EXTERNAL NEWEST | 2026-08-25 to 2026-09-29 | 5 | 5 |

Validation, final test, and external predictions used an expanding window. Model formulation, features, hyperparameters, and selection criterion were frozen using validation only. Final-test observations were not used for candidate selection. For a later prediction within a walk-forward partition, only earlier outcomes that would already have become known were eligible for refitting.

## I. Baselines and initial models

Baselines actually evaluated:

- zero-return / naive persistence;
- last observed return;
- expanding historical mean return, grade-specific.

ML candidates actually evaluated:

- separate Grade 1 and Grade 2 Ridge models, `alpha=1.0`;
- separate Grade 1 and Grade 2 Random Forest models, 100 trees, max depth 5, minimum leaf size 5;
- shared Ridge with grade indicator, `alpha=1.0`;
- shared Random Forest with grade indicator and the same tree settings.

Seed 42 was used. Environment: Python 3.13.14, pandas 3.0.1, NumPy 2.4.3, scikit-learn 1.8.0 on Windows 11. No large search or deep-learning model was run.

## J. Walk-forward validation

The predefined selection score was the macro-average of the two grade-specific return RMSE values. Lower is better.

| Method | Selection RMSE | Overall return MAE | Direction accuracy | Derived-price MAE (LKR/kg) |
|---|---:|---:|---:|---:|
| Zero-return persistence | **0.04319** | **0.03060** | 5.76% | **49.64** |
| Expanding mean return | 0.04352 | 0.03083 | 50.36% | 50.12 |
| Separate Ridge | 0.04434 | 0.03377 | 46.04% | 54.61 |
| Shared Ridge | 0.04462 | 0.03381 | 48.20% | 54.90 |
| Separate Random Forest | 0.04682 | 0.03549 | 48.20% | 57.18 |
| Shared Random Forest | 0.04834 | 0.03461 | **51.08%** | 55.34 |
| Last observed return | 0.07121 | 0.04917 | 48.92% | 79.30 |

Separate Ridge was the best ML candidate, narrowly ahead of shared Ridge, and was frozen for the final ML comparison. However, it did not beat persistence on the validation selection score or error metrics. It therefore remains a research candidate, not an evidence-supported replacement for persistence.

## K. Final temporal test

The final test contains 147 forecasts through 2026-08-18. MAPE is omitted for return because returns include and approach zero. Derived-price percentage error is mathematically safe and is reported separately.

| Metric | Separate Ridge | Persistence |
|---|---:|---:|
| Return MAE | 0.01989 | **0.01858** |
| Return RMSE | **0.02954** | 0.03187 |
| Return R² | **0.1398** | -0.0010 |
| Three-class directional accuracy | **46.26%** | 10.20% |
| Non-flat UP/DOWN directional accuracy | **51.52%** | 0.00% |
| Derived-price MAE | 37.29 LKR/kg | **34.62 LKR/kg** |
| Derived-price RMSE | **54.55 LKR/kg** | 58.12 LKR/kg |
| Derived-price MAPE | 1.98% | **1.85%** |

Per grade for separate Ridge:

| Grade | Return MAE | Return RMSE | R² | Direction accuracy | Price MAE | Price RMSE |
|---|---:|---:|---:|---:|---:|---:|
| Grade 1 (74) | 0.00934 | 0.01287 | -0.4575 | 47.30% | 18.41 | 25.23 |
| Grade 2 (73) | 0.03057 | 0.03987 | 0.1743 | 45.21% | 56.43 | 73.12 |

Ridge directional confusion matrix, rows actual and columns predicted `[DOWN, FLAT, UP]`:

```text
[[47, 0, 18],
 [12, 0,  3],
 [46, 0, 21]]
```

The ML model never produced an exact source-resolution `FLAT` prediction. The test result is mixed: Ridge reduced larger errors enough to improve RMSE and provided nontrivial direction predictions, but it increased typical absolute error. It cannot be claimed to outperform persistence overall.

## L. Newest-observation reality check

These observations post-date the old local dataset cutoff and were excluded from model selection. The table reports the frozen separate-Ridge formulation in sequential expanding-window use.

| Grade | Reference date/price | Target date | Predicted movement | Derived forecast | Actual EAC price | Abs. error | % error | Direction |
|---|---|---|---:|---:|---:|---:|---:|---|
| G1 | 2026-08-18 / 1886.14 | 2026-08-25 | -0.77% | 1871.63 | 1892.43 | 20.80 | 1.10% | wrong |
| G2 | 2026-08-18 / 1800.00 | 2026-08-25 | -1.08% | 1780.51 | 1800.00 | 19.49 | 1.08% | wrong |
| G1 | 2026-08-25 / 1892.43 | 2026-09-01 | -0.32% | 1886.35 | 1918.57 | 32.22 | 1.68% | wrong |
| G2 | 2026-08-25 / 1800.00 | 2026-09-01 | -1.07% | 1780.68 | 1740.00 | 40.68 | 2.34% | correct |
| G1 | 2026-09-01 / 1918.57 | 2026-09-08 | -0.65% | 1906.06 | 1957.50 | 51.44 | 2.63% | wrong |
| G2 | 2026-09-01 / 1740.00 | 2026-09-08 | +0.56% | 1749.74 | 1887.50 | 137.76 | 7.30% | correct |
| G1 | 2026-09-08 / 1957.50 | 2026-09-15 | -0.82% | 1941.47 | 1987.50 | 46.03 | 2.32% | wrong |
| G2 | 2026-09-08 / 1887.50 | 2026-09-15 | -3.43% | 1822.71 | 1940.00 | 117.29 | 6.05% | wrong |
| G1 | 2026-09-15 / 1987.50 | 2026-09-29 | -0.79% | 1971.84 | 1999.43 | 27.59 | 1.38% | wrong |
| G2 | 2026-09-15 / 1940.00 | 2026-09-29 | -2.14% | 1898.56 | 1890.00 | 8.56 | 0.45% | correct |

Across these ten observations, Ridge return MAE/RMSE were 0.02714/0.03557, direction accuracy was 30%, and price MAE/RMSE were 50.19/64.68 LKR/kg. Persistence achieved lower return MAE/RMSE of 0.02305/0.03259 and lower price MAE/RMSE of 42.33/58.22 LKR/kg. Ridge therefore did not improve the genuine-newest reality check.

The latest available verified EAC observation in this reconstruction is **2026-09-29** for both grades. It must not be called today's or a real-time price.

## M. Integrity validation

Focused automated validation passed all checks:

- zero duplicate canonical observation keys;
- canonical values exactly match the normalized raw extraction;
- all canonical rows are marked as observed source values;
- no fabricated Grade 2 observations;
- every target is strictly later than its feature date;
- target returns reproduce the next observed price;
- tested lag features are backward-looking;
- no random temporal split;
- no final-test or external-period model selection;
- external newest observations remain after the old cutoff;
- broken source links remain explicitly recorded.

Historical V2 files were not overwritten. No backend, mobile, berry-grading, ONNX/TFLite, or deployment file was modified.

## N. Limitations and Phase 5 readiness

Important limitations:

- The EAC observations are market references, not buyer-specific quotes or guaranteed farm transactions.
- Observation intervals are irregular, and Grade 2 has substantial gaps and only 358 observations.
- Two public dated links were broken at retrieval time; their values were not inferred.
- Price formation may depend on supply, demand, weather, export conditions, policy, and other covariates absent from this univariate foundation.
- The small external check contains only five target dates per grade.
- Direction remains difficult: final Ridge non-flat direction accuracy was close to chance, and all five external Grade 1 movements were predicted in the wrong direction.
- Initial ML candidates did not demonstrate consistent improvement over persistence.
- No result establishes a current market price, future buyer quote, export contract value, or guaranteed forecast.

**PHASE 5 READINESS: READY — for separately authorized forecasting research, not deployment.**

The reconstructed data, return target, temporal protocol, provenance, and evaluation code form a defensible Phase 5 foundation. Phase 5 should investigate whether carefully justified features or formulations can improve on persistence under the same frozen temporal discipline. It must not treat the Phase 4 Ridge candidate as a successful production model, fabricate Grade 2 values, or tune on the final/external results reported here.

Phase 5 was not started.
