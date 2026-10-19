# Repository Inventory

Status basis: repository source inspected on 2026-10-18.

This inventory distinguishes current application/runtime files from research
evidence, historical material, generated outputs, and ignored local files. It
is a cleanup boundary, not a claim that every retained historical artifact is
used at runtime.

## Top-level ownership

| Path | Role | Cleanup boundary |
|---|---|---|
| `backend/` | FastAPI application, active Phase 7 boundary, retained legacy/fallback services, schemas, and tests | Keep active code and separately classified fallback artifacts. |
| `data/` | Raw sources, manifests, controlled negatives, and processed evidence | Do not delete raw data, frozen inputs, provenance, or tracked research evidence. |
| `docs/` | Current guidance and dated research records | Preserve dated evidence; V1/V2/PP2 records are separated under `docs/research/historical/`. |
| `ml/` | Current V3/Phase 4-7 workflow plus a separated V1/V2 archive | Protect selected models, configurations, metrics, decisions, and integrity evidence. Superseded implementations live under `ml/archive/`. |
| `mobile/` | Current Flutter application and declared assets | Preserve application code and all referenced model/data assets. |
| `archive/` | Byte-preserved superseded material | Do not treat archived material as the current workflow. |
| `notebooks/` | Empty historical scaffolding | No implementation was present at cleanup time. |
| `scripts/` | Former location of the V1 label generator | The generator is preserved under `archive/legacy_v1/`. |
| `weights/` | Ignored local checkpoint cache | Not authoritative; deletion still requires an exact allowlist. |

## Authoritative grading and decision workflow

- V3 training configuration:
  `ml/grading_forecast/berry_grading/training/v3_yolo/experiment.yaml`
- V3 baseline:
  `ml/grading_forecast/berry_grading/models/v3_yolo/best.pt`
- Phase 3 follow-up configuration:
  `ml/grading_forecast/berry_grading/quality/phase3_followup/experiment.yaml`
- Selected grading model:
  `ml/grading_forecast/berry_grading/models/v3_phase3_followup/best.pt`
- Deployed ONNX model:
  `ml/grading_forecast/berry_grading/models/v3_phase3_followup/best.onnx`
- Frozen grading rules:
  `ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup/decision_config_frozen.json`
- Phase 5 configuration and selected specification:
  `ml/grading_forecast/price_forecasting/phase5/phase5_config.yaml` and
  `ml/grading_forecast/price_forecasting/phase5/models/selected_model_spec.json`
- Phase 6 configuration and engine:
  `ml/grading_forecast/decision_support/phase6/phase6_config.yaml` and
  `ml/grading_forecast/decision_support/phase6/decision_engine.py`
- Phase 7 configuration and runtime:
  `ml/grading_forecast/evaluation/phase7/phase7_config.yaml` and
  `ml/grading_forecast/deployment/phase7/`
- Backend boundary:
  `backend/app/services/grading_forecast/phase7_service.py` and
  `backend/app/api/routes/grading_forecast.py`
- Flutter client:
  `mobile/lib/features/grading_forecast/`
- Local-first Flutter History:
  `mobile/lib/features/history/`

The Phase 7 price path retrieves approved frozen Phase 5 forecast records. An
image request does not retrain or generate a new market forecast.

## Research documentation

Current V3 and Phase 4-7 guidance and evidence remain directly under
`docs/research/`. Operational guides are grouped under `docs/guides/`.
Superseded V1/V2/PP2 documents are retained under:

- `docs/research/historical/status/` for dated plans, checklists, status
  snapshots, and progress reports.
- `docs/research/historical/evidence/` for historical dataset, model,
  limitation, integration, and PP2 result evidence.

Historical documents may retain references to their original paths when those
paths are part of the recorded research chronology.

## Retained fallback and historical artifacts

V2 MobileNetV2, price-forecast, recommendation, and storage implementations
remain in the repository as legacy/fallback services with their own tests. The
active route imports `phase7_service.py`; it does not call those services, and
the old `/grade-only`, `/price-forecast`, and `/recommend` endpoints return HTTP
410. Their models and data remain protected until the retained fallback scope is
reviewed separately. The older V1 label manifest and generator are preserved
under `archive/legacy_v1/`; active validation requires an explicit input path.

Superseded ML scripts, generated diagnostics, root-era model artifacts, and V2
Phase 4 variants are separated under
`ml/archive/grading_forecast/legacy_v1_v2/`. Historical documents may retain
their original paths as chronology. The active tree keeps
`berry_grading/models/v2/` and `price_forecasting/models/v2/` temporarily
because dormant backend fallback services still reference those exact paths.

## Current verification boundary

The focused backend check is:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  --basetemp=.\backend\pytest-cache-files-phase7 `
  backend\tests\test_main_startup.py `
  backend\tests\test_phase7_integration.py `
  backend\tests\test_phase7_text_integrity.py
```

The recorded 2026-10-18 run passed 15 tests. This establishes the active Phase
7 startup, route, rejection-first, and text-integrity boundary; it does not
convert legacy/fallback test failures into current Phase 7 failures.

## Ignored local files

Ignored does not mean disposable. Raw image/price sources, virtual environments,
secrets, local model assets, last checkpoints, training-run weights, Flutter
models, and team reference snapshots must not be removed by blanket cleanup.
Never use `git clean -fdX` for this repository.

The V3 training configuration names the ignored root `yolo11n.pt` initialization
checkpoint, so it is retained. The isolated `weights/yolo26n.pt` file was not
referenced by the repository and was approved separately for local deletion.

## Line-ending-sensitive integrity files

Phase 5/6 text hashes recorded by the research configuration correspond to
canonical LF content. A Windows checkout may contain CRLF bytes while remaining
clean in Git. Cleanup must not rewrite or normalize these files; compare raw
hashes to the same checkout baseline and configured hashes to canonical LF
content.
