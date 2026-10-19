# Current Grading and Forecasting Workflow

This directory contains the active research/application workflow:

```text
V3 YOLO baseline and Phase 3 follow-up
    -> Phase 5 grade-specific frozen forecasting evidence
    -> Phase 6 deterministic decision engine
    -> Phase 7 ONNX backend integration
```

## Current areas

- `berry_grading/training/v3_yolo/`: V3 baseline preparation and training.
- `berry_grading/training/v3_phase3_followup/`: selected hard-negative
  follow-up training.
- `berry_grading/evaluation/v3_yolo/`, `v3_phase3/`, and
  `v3_phase3_followup/`: current grading evidence and frozen thresholds.
- `berry_grading/quality/` and `rejection/`: current quality and rejection
  pipeline.
- `berry_grading/models/v3_yolo/` and `v3_phase3_followup/`: current frozen
  checkpoints and deployed ONNX model.
- `price_forecasting/phase4/`: protected price-data foundation and lineage.
- `price_forecasting/phase5/`: selected forecasting specification, frozen
  records, metrics, and integrity evidence.
- `decision_support/phase6/`: authoritative deterministic decision engine.
- `deployment/phase7/`: deployed ONNX and frozen-forecast runtime.
- `evaluation/phase7/`: Phase 7 configuration and verification evidence.
- `requirements-yolo.txt`: current V3 YOLO training/evaluation environment.

## Compatibility holds

`berry_grading/models/v2/` and `price_forecasting/models/v2/` remain only
because retained backend fallback services still reference them. They are not
used by the active Phase 7 `/analyze` route.

Superseded V1/V2 implementations are under
`../archive/grading_forecast/legacy_v1_v2/`.

