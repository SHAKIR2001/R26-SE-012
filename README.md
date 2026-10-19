# Multimodal Pepper AI Decision Support System

A research-focused Flutter and FastAPI application for black pepper crop
analysis, harvested-sample grading, and qualified market decision support.

The repository combines four mobile analysis areas:

- pest detection;
- leaf disease detection and severity analysis;
- berry disease detection;
- berry grading and grade-specific price outlooks.

The selected berry-grading workflow is a fail-closed Phase 7 integration. It
uses backend ONNX inference and approved frozen research evidence; it is not an
official export-grading service, a live market-price service, or financial
advice.

## Current application flow

```text
Flutter (web or Android)
    |
    | multipart image upload
    v
FastAPI: POST /api/v1/grading-forecast/analyze
    |
    +-> image validation and frozen quality gates
    +-> V3 Phase 3 follow-up YOLO11n model (ONNX Runtime CPU)
    +-> Phase 6 rejection-first decision engine
    +-> exact-grade frozen Phase 5 forecast record, when grading is accepted
    v
Localized result and local History snapshot in Flutter
```

Rejected, poor-quality, non-pepper, and uncertain inputs do not receive market
output. An accepted Grade 1 or Grade 2 result can access only the corresponding
grade-specific frozen forecast record. Uploading an image does not retrain a
model or create a new price forecast.

The pest, leaf-disease, and berry-disease features are separate mobile
components. They use their own bundled TFLite fallback and optional cloud
analysis path; those models are not the Phase 7 berry grader.

## Implemented capabilities

- Flutter application for Android and web development workflows.
- English, Sinhala (`si`), and Tamil (`ta`) presentation.
- Pest, leaf-disease, berry-disease, and berry-grading feature flows.
- V3 two-grade harvested-sample detection and grading with YOLO11n.
- Quality, non-pepper, and uncertainty rejection before price routing.
- Grade-specific frozen price evidence and deterministic Phase 6 decisions.
- Local-first History that stores completed result snapshots and selected image
  copies without rerunning inference when a record is reopened.
- Strict API/mobile validation for image size, format, response schema, routing,
  and error handling.
- Optional Firebase persistence retained outside the core Phase 7 path.

## Research evidence at a glance

| Area | Saved result | Interpretation boundary |
|---|---:|---|
| V3 data | 775 images from 194 physical samples | Group-aware split: 539 train, 116 validation, 120 test |
| V3 follow-up positive test | 115/120 accuracy (95.83%); macro F1 0.9643 | Controlled positive-pepper images, not independent field evidence |
| Original Phase 2 detector | mAP@0.5 0.9791 | Belongs to the original detector test, not the later hard-negative result |
| Phase 3 follow-up negatives | 49/49 rejected | Small sealed external negative holdout, not broad open-set proof |
| Phase 5 selected Ridge model | price MAE 34.00 and RMSE 54.73 LKR/kg over 147 final-test predictions | Chronological research evaluation; newest external check contained only 10 predictions |
| Phase 6 decision engine | 28/28 saved scenarios passed | 13 empirical-compositional and 15 synthetic logic scenarios, not a field study |
| Phase 7 integration | five controlled roles passed ONNX/PyTorch equivalence and corrected emulator flow | Grade 1, Grade 2, non-pepper, poor-image, and uncertain cases |

These results come from different experiments and must not be combined into a
single accuracy claim. See the [full component progress report](docs/research/FULL_COMPONENT_PROGRESS_REPORT_2026-10-10.md)
and the phase-specific records under [`docs/research/`](docs/research/) for the
methods, metrics, and limitations.

## Technology

| Layer | Main technologies |
|---|---|
| Mobile | Flutter, Dart, SQLite, TFLite fallback modules |
| Backend | FastAPI, Pydantic, Uvicorn, Pillow, OpenCV |
| Grading runtime | Ultralytics YOLO11n export, ONNX Runtime CPU |
| Forecast research | Python, pandas, scikit-learn Ridge regression |
| Optional integrations | Firebase, Gemini, Anthropic |

## Repository layout

```text
backend/   FastAPI application, Phase 7 API boundary, schemas, and tests
data/      Raw sources, controlled inputs, manifests, and processed evidence
docs/      Current guides, API resources, and versioned research records
ml/        Active V3 and Phase 4-7 ML workflow plus separated archives
mobile/    Flutter application, local History, localization, and model assets
archive/   Preserved superseded material; not the current runtime
```

The authoritative file-level ownership and cleanup boundaries are documented in
the [repository inventory](docs/guides/repository_inventory.md). Historical
V1/V2/PP2 documents are separated under
[`docs/research/historical/`](docs/research/historical/) and must not be read as
the selected Phase 7 workflow.

## Quick start

The commands below use PowerShell and assume a repository-root Python virtual
environment named `.venv`.

### 1. Install backend dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Dependency installation may access package registries. Skip it when the
existing environment is already complete.

### 2. Start FastAPI

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app `
  --app-dir backend `
  --host 0.0.0.0 `
  --port 8000
```

The application verifies the ONNX runtime and frozen forecast evidence during
startup. Check both endpoints before using a client:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/grading-forecast/health"
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/grading-forecast/ready"
```

`/health` is a liveness check. `/ready` is the required readiness gate and must
return HTTP 200 with `status: ready`. Interactive API documentation is at
`http://127.0.0.1:8000/docs`.

### 3. Run Flutter

From `mobile/`:

```powershell
flutter pub get

# Web with a local backend
flutter run -d chrome `
  --dart-define=PEPPER_API_BASE_URL=http://127.0.0.1:8000

# Android emulator with a local backend
flutter run -d emulator-5554 `
  --dart-define=PEPPER_API_BASE_URL=http://10.0.2.2:8000
```

Replace `emulator-5554` with the identifier printed by `flutter devices`.
For a physical Android device connected over USB, run
`adb reverse tcp:8000 tcp:8000` and use `http://127.0.0.1:8000`.

`PEPPER_API_BASE_URL` is a build-time value. Phase 7 grading does not require
Gemini or Anthropic credentials. Optional restricted development keys for the
other mobile analysis features may be stored in the ignored `mobile/.env` file.
Never commit keys or distribute unrestricted provider keys inside an APK or web
bundle.

For browser, emulator, device, localization, controlled-image, and Android
release procedures, use the
[Phase 7 application guide](docs/guides/PHASE7_APPLICATION_RUN_GUIDE.md).

## API contract

| Method and path | Purpose |
|---|---|
| `GET /api/v1/grading-forecast/health` | Process liveness only |
| `GET /api/v1/grading-forecast/ready` | ONNX and frozen-evidence readiness |
| `POST /api/v1/grading-forecast/analyze` | Rejection-first integrated analysis |

`POST /analyze` expects multipart field `image`, accepts a single-frame JPEG,
PNG, or WEBP, and limits uploads to 10 MB. The backend also bounds decoded
dimensions and pixel count.

The pre-Phase-7 `/grade-only`, `/price-forecast`, and `/recommend` routes are
retired and intentionally return HTTP 410. The maintained Postman collection is
[`docs/api/grading_forecast_postman_collection.json`](docs/api/grading_forecast_postman_collection.json).

## Validation

Run the focused, non-generating Phase 7 backend suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  --basetemp=.\backend\pytest-cache-files-phase7 `
  backend\tests\test_main_startup.py `
  backend\tests\test_phase7_integration.py `
  backend\tests\test_phase7_text_integrity.py
```

The latest recorded run on 2026-10-18 passed 15/15 tests. That evidence covers
startup wiring, active routes, rejection-first behavior, error handling, and
cross-platform frozen-text integrity. It does not prove model retraining,
hosted availability, device behavior, or field performance.

Validate Flutter separately from `mobile/`:

```powershell
flutter analyze
flutter test
```

Static analysis and widget/unit tests do not replace an Android build,
installation, live backend check, or manual device acceptance.

### CI/CD workflow

The [GitHub Actions workflow](.github/workflows/ci-cd.yml) runs on pull requests
and pushes targeting `integration` or `main`, and can also be started manually.
It performs the focused Phase 7 backend tests plus `flutter analyze` and
`flutter test`. After both jobs pass on a branch push, it publishes a
14-day `phase7-backend-<commit>` delivery artifact containing the tracked
FastAPI and ML runtime source.

One real-image integration assertion uses an intentionally ignored V3 dataset
image. It runs in complete local research checkouts and is reported as skipped
in clean CI checkouts; the tracked upload, response-contract, readiness,
rejection-first, retired-route, startup, and frozen-integrity tests remain
mandatory in CI.

The workflow does not automatically deploy to Railway or another production
environment because no deployment target or credentials are defined. It also
does not publish an APK: the three current pest/leaf/berry-disease TFLite assets
are intentionally local/ignored in this checkout, so a GitHub-built APK would
not contain the complete mobile runtime.

## Important limitations

- V3 Grade 1 and Grade 2 are project-specific visual labels, not official SLS,
  laboratory, buyer, or export certification grades.
- The grader evaluates harvested sample/batch images; it does not grade each
  individual berry or measure moisture, piperine, volatile oil, fibre, ash,
  hygiene, adulteration, or other laboratory criteria.
- Controlled results do not establish generalization across farms, phones,
  seasons, lighting, backgrounds, cultivars, or post-harvest conditions.
- Confidence and margin values are model scores and heuristics, not calibrated
  probabilities.
- Phase 5 uses historical EAC national-average farm-gate observations. Its
  frozen records are not live buyer offers, guaranteed transaction prices, or
  trading signals. Grade 2 forecasting evidence is materially weaker than
  Grade 1 evidence.
- Prospective field validation, independent user/economic-benefit studies,
  production authentication, distributed rate limiting, adversarial testing,
  and load testing remain incomplete.
- The current Android application ID and release-signing setup are suitable for
  controlled local testing, not public store distribution.

## Documentation

- [Current guides index](docs/guides/README.md)
- [Project commands](docs/guides/project_commands_guide.md)
- [Phase 7 run and acceptance guide](docs/guides/PHASE7_APPLICATION_RUN_GUIDE.md)
- [Flutter build and distribution guide](docs/guides/build_guide.md)
- [Repository inventory](docs/guides/repository_inventory.md)
- [Current research records](docs/research/)

## Project status and license

This is an academic research system. The selected Phase 7 integration is
complete with documented limitations; production readiness and independent
field validity have not been demonstrated.

No standalone software license is currently declared in the repository. Do not
assume permission for external redistribution until the project owners add one.
