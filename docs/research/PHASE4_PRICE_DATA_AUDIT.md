# Phase 4 Initial Price-Data Audit

**Audit date:** 2026-10-07  
**Scope:** read-only audit completed before Phase 4 reconstruction or modelling

## Existing local data

- The principal local file is `data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv`.
- Despite its filename, its observed range is 2021-02-22 through 2026-08-18, not 2016 through 2026.
- It contains 7,742 rows over 232 source dates: 6,930 Grade 1 rows and 812 Grade 2 rows.
- National average coverage is 232 Grade 1 observations and 161 Grade 2 observations.
- It mixes districts, National values, Grade 1/Grade 2, and highest/average price types in a normalized long format.
- Every row records only the index URL (`https://exagri.info/mkt/index.html`), not its dated source page. There is no repository extraction manifest or downloader that proves page-level lineage for each row.
- The local raw file is ignored by Git and is not historical V2 evidence in the tracked repository. The tracked `price_v2` processed artifacts remain preserved.
- Legacy local files are unrelated IPC monthly/sample datasets and are not substitutes for the DEA EAC national grade series.

## Existing forecasting formulation

- V2 selects only National Grade 1 average farm-gate price as its target.
- V2 predicts the next absolute price level with lagged price/rolling features and a Random Forest.
- Its chronological test contains 36 observations from 2025-12-02 through 2026-08-18.
- The V2 Random Forest test MAE/RMSE were 82.42/88.45 LKR/kg, compared with 16.41/22.52 for naive persistence. The learned model therefore did not beat persistence.
- Runtime behavior deliberately prefers `naive_persistence`; its forecast equals the latest observed Grade 1 value.
- Runtime/mobile artifacts derive Grade 2 using a latest overlapping Grade 1-Grade 2 gap and include a hard-coded fallback discount of 113 LKR/kg. These application files are historical findings only and are outside the Phase 4 modification scope.
- The older scripts called `phase4` merely extend absolute-price Random Forest lags on V2; they do not implement the newly authorized return-based Phase 4 design and will remain untouched as historical artifacts.

## Preprocessing and evaluation findings

- V2 standardizes values, drops invalid rows, and de-duplicates on date/district/grade/price type.
- V2 does not fabricate missing weekly dates and uses a chronological 70/15/15 split.
- V2 forecasting uses an absolute next-price target rather than future return/change.
- Historical rolling features are shifted backward, but the final research question, grade-aware target, page-level provenance, external-newest holdout, walk-forward model selection, and actual Grade 2 forecasting are absent.
- No random temporal split was found in the V2 research pipeline.

## Authoritative-source comparison

- The authoritative public DEA/Economic Research Unit index identifies the series as Producers' Prices (Farm Gate) of EAC and links dated observation pages.
- The public index was last updated on 2026-09-29 at audit time.
- It lists five dated pages after the local file's 2026-08-18 cutoff: 2026-08-25, 2026-09-01, 2026-09-08, 2026-09-15, and 2026-09-29.
- Public sample pages confirm separate PEPPER columns for GR-1 highest/average, GR-2 highest/average, and district plus National values. A dash represents an unreported observation and must remain missing.
- The index includes earlier years that are absent from the local file; their usable pepper-table availability must be established by page-by-page reconstruction rather than inferred from the index alone.

## Locked Phase 4 corrections

- Preserve each actual Grade 1 and Grade 2 source observation separately; never create a Grade 2 discount observation.
- Use National average farm-gate Grade 1 and Grade 2 as the primary series.
- Preserve dated source-page URLs and retrieval metadata.
- Keep raw reconstruction, canonical observations, analytical grade relationships, and model-ready features separate.
- Forecast next-observation return/change; convert it to price using the dated reference observation.
- Retain persistence only as a baseline.
- Reserve post-2026-08-18 observations as a genuine external temporal reality check.
- Use chronological expanding-window validation and a frozen temporal test; never shuffle.

This audit records the pre-implementation state. It does not claim that the local file is complete or that the public pages are error-free.
