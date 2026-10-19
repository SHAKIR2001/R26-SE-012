# Price Dataset Description

Last updated: 2026-08-27

Source: Department of Export Agriculture.

Market level: Farm-gate producer price.

Commodity: Black pepper.

Country: Sri Lanka.

Frequency: Weekly source records with some missed or irregular collection intervals.

Grades available in source: Grade 1 and Grade 2.

Grade 3 availability: Not available in selected source.

Raw dataset:

- `data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv`
- Raw rows: 7,742.
- Raw date range: 2021-02-22 to 2026-08-18.
- Practical main coverage begins from early January 2022.
- Grade 1 rows: 6,930.
- Grade 2 rows: 812.

PP2 V2 processed dataset:

- `data/processed/grading_forecast/price_v2/cleaned_price_data_v2.csv`
- Cleaned rows: 7,742.
- The V2 cleaned dataset preserves observed rows and does not fabricate missing prices.

Primary PP2 forecasting target:

- `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`
- Target definition: National + Grade 1 + average + farm_gate + weekly.
- Target observations: 232.
- Target date range: 2021-02-22 to 2026-08-18.
- Duplicate target dates: 0.
- Missing target prices: 0.

Reason for target selection:

National Grade 1 average farm-gate weekly price is the most defensible PP2 forecasting target because it has stronger coverage than Grade 2 and avoids inventing sparse observations.

Chronological PP2 split:

- Train: 162 rows, 2021-02-22 to 2025-03-18.
- Validation: 34 rows, 2025-03-25 to 2025-11-25.
- Test: 36 rows, 2025-12-02 to 2026-08-18.

Missing-week and gap notes:

- Target gaps greater than 8 days: 12.
- Largest target gap: 316 days, from 2021-02-22 to 2022-01-04.
- Missing weeks are documented only; they are not filled, interpolated, or treated as zero.

Grade 2 limitation:

- All observed Grade 2 rows are preserved.
- National Grade 2 average has 161 observed dates.
- National Grade 2 observed dates by year: 2022: 6, 2023: 27, 2024: 49, 2025: 49, 2026: 30.
- Grade 2 forecasting is out of scope for the primary PP2 forecasting baseline because historical coverage is sparse.
