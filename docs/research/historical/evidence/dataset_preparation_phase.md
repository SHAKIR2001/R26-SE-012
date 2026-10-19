# Dataset Preparation Phase (Phase 2) — Berry Grading + Export Price Forecasting

This file mirrors the Phase 2 dataset preparation guidance used during implementation.

Canonical guide:

- `docs/agent_guide/dataset_preparation_phase.md`

Key outputs produced by Phase 2 scripts:

- `data/processed/grading_forecast/cleaned_price_data.csv`
- `data/processed/grading_forecast/forecast_training_data.csv`
- `data/processed/grading_forecast/train_forecast_data.csv`
- `data/processed/grading_forecast/test_forecast_data.csv`
- `data/processed/grading_forecast/berry_images_processed/`

PP2 V2 update, 2026-08-27:

The outputs above are historical V1/old processed artifacts. For PP2, the authoritative V2 dataset-preparation outputs are:

- `data/annotations/grading_forecast/berry_grading_labels_v2.csv`
- `data/processed/grading_forecast/berry_dataset_v2_summary.json`
- `data/processed/grading_forecast/berry_split_v2/`
- `data/processed/grading_forecast/berry_split_v2_manifest.csv`
- `data/processed/grading_forecast/price_v2/cleaned_price_data_v2.csv`
- `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`
- `data/processed/grading_forecast/price_v2/price_v2_coverage_summary.json`
- `data/processed/grading_forecast/price_v2/forecast_train.csv`
- `data/processed/grading_forecast/price_v2/forecast_validation.csv`
- `data/processed/grading_forecast/price_v2/forecast_test.csv`

Berry V2 dataset facts:

- 671 readable images.
- 168 physical sample groups.
- Grade 1: 224 images.
- Grade 2: 224 images.
- Grade 3: 223 images.
- Sample-level split with seed 42.
- Train: 117 samples, 467 images.
- Validation: 24 samples, 95 images.
- Test: 27 samples, 109 images.
- No `grade + sample_id` group crosses train, validation, and test.

Price V2 dataset facts:

- Raw rows preserved: 7,742.
- Primary target: National Grade 1 average farm-gate weekly price.
- Target observations: 232.
- Target date range: 2021-02-22 to 2026-08-18.
- Chronological split: train 162 rows, validation 34 rows, test 36 rows.
- Grade 2 observations were preserved but not fabricated or used as the primary PP2 forecasting target.

Do not rerun old V1 preparation scripts for PP2 V2 work unless the output paths have been checked carefully. Accidentally running old defaults can overwrite or mix into V1 processed artifacts.
