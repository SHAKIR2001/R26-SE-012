# Legacy V1/V2 Grading and Forecasting Archive

This archive was created on 2026-10-18 to keep the active
`ml/grading_forecast/` tree focused on the current V3 and Phase 4-7 workflow.
No archived source file or model artifact was intentionally modified during
the move.

## Archived material

- `requirements-training.txt`: TensorFlow/MobileNetV2 training environment.
- `dataset_v2/`: combined V2 dataset-preparation utility.
- `berry_grading/evaluation/`: V2 diagnostics and ignored generated plots.
- `berry_grading/inference/`: legacy MobileNetV2 inference CLI.
- `berry_grading/models/`: root-era V1 artifacts and the V2 Phase 4
  experimental variant.
- `berry_grading/preprocessing/`: V1/V2 validation and preparation utilities.
- `berry_grading/training/`: MobileNetV2 training, evaluation, ONNX export,
  and TFLite export utilities.
- `price_forecasting/data/`, `evaluation/`, `inference/`, and `training/`:
  pre-Phase-5 forecasting utilities.
- `price_forecasting/models/`: root-era forecasting artifacts and the V2
  Phase 4 Random Forest variant.

## Deliberately retained in the active tree

The following older artifacts remain under `ml/grading_forecast/` because
dormant backend fallback services still reference them:

- `berry_grading/models/v2/`
- `price_forecasting/models/v2/`

They can move only when those backend services and their tests are retired or
redirected in the same change.

The Phase 4 price foundation remains active research lineage for Phase 5 and
was not archived. All V3, Phase 5, Phase 6, and Phase 7 code and evidence remain
in their original locations.

Ignored binary artifacts such as `.keras`, `.onnx`, `.joblib`, and generated
plots remain local-only unless the repository ignore policy is changed.

