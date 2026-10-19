# Current Project Commands Guide

Status basis: repository source and tests inspected on 2026-10-18.

This is the command reference for the current combined research and Flutter
application repository. The active berry workflow is:

```text
V3 Phase 3 follow-up YOLO model (frozen ONNX)
    -> Phase 6 rejection-first decision engine
    -> approved, grade-specific frozen Phase 5 forecast record
    -> FastAPI Phase 7 POST /analyze
    -> Flutter grading and price-outlook screens
```

Normal application use does **not** train a model, export ONNX, regenerate a
dataset, or create a new price forecast. Older V1/V2 commands and results are
research history, not the current runtime procedure.

## 1. Command locations and environments

Unless a section says otherwise, run commands from the repository root:

```powershell
cd "D:\work\Year - 4\pepper\project\multimodal-pepper-ai-decision-support"
```

Use the existing environments when they are available:

- `.venv` - backend, tests, and general Python tools.
- `.venv-yolo` - YOLO training/evaluation only.

Do not delete either environment if you want to avoid downloading its packages
again. Install requirements only when an environment is missing or incomplete:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

## 2. Run the current backend

Start FastAPI from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app `
  --app-dir backend `
  --host 0.0.0.0 `
  --port 8000
```

The application loads the Phase 7 ONNX runtime and frozen forecast evidence at
startup. A startup failure is intentional fail-closed behavior.

Check liveness and readiness in a second terminal:

```powershell
Invoke-RestMethod `
  "http://127.0.0.1:8000/api/v1/grading-forecast/health" |
  ConvertTo-Json -Depth 10

Invoke-RestMethod `
  "http://127.0.0.1:8000/api/v1/grading-forecast/ready" |
  ConvertTo-Json -Depth 10
```

`/health` proves that the process answers HTTP. `/ready` is stronger: it must
return HTTP 200 with `status: ready`, `runtime: backend_onnx_runtime`, and
`price_strategy: frozen_phase5_forecast_records`.

FastAPI documentation is at `http://127.0.0.1:8000/docs`.

## 3. Use the current API

The only analysis endpoint is:

```text
POST /api/v1/grading-forecast/analyze
multipart field: image
accepted formats: single-frame JPEG, PNG, or WEBP
maximum upload: 10 MB
```

Example using a controlled repository image:

```powershell
curl.exe -X POST `
  "http://127.0.0.1:8000/api/v1/grading-forecast/analyze" `
  -F "image=@data/raw/Pepper Berry Grading V3.yolov8/test/images/20260508_160550_jpg.rf.BUF1sZWo8GvE4UCSfj74.jpg"
```

Rejected or uncertain grading must not produce market output. Accepted Grade 1
and Grade 2 results may retrieve only the matching approved frozen forecast
record. The response is research decision support, not a live market quote or
financial recommendation.

These pre-Phase-7 endpoints are intentionally retired and return HTTP 410:

```text
POST /api/v1/grading-forecast/grade-only
GET  /api/v1/grading-forecast/price-forecast
POST /api/v1/grading-forecast/recommend
```

Use `docs/api/grading_forecast_postman_collection.json` for the maintained
Postman requests.

## 4. Run focused backend tests

The current Phase 7 application boundary is covered by these three files:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  --basetemp=.\backend\pytest-cache-files-phase7 `
  backend\tests\test_main_startup.py `
  backend\tests\test_phase7_integration.py `
  backend\tests\test_phase7_text_integrity.py
```

The latest recorded local run on 2026-10-18 passed all 15 tests. This focused
run checks startup wiring, route/error behavior, rejection-first routing, and
CRLF/LF-safe frozen-text integrity. It does not retrain models or overwrite
frozen results.

The repository-level `pytest.ini` disables pytest's normal cache provider. The
explicit `--basetemp` path avoids known Windows temporary-directory permission
problems in this checkout.

The remaining backend tests include legacy/fallback-service coverage. Run the
entire suite only when changing those services, and interpret failures by
component rather than treating them automatically as a Phase 7 regression:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  --basetemp=.\backend\pytest-cache-files-all
```

## 5. Run the Flutter application

From `mobile/`, use the installed Flutter SDK:

```powershell
cd mobile
$flutter = "C:\test-by-me\flutter\flutter\bin\flutter.bat"
& $flutter devices
```

Dependency resolution can download packages. Skip `flutter pub get` when the
existing cache and lockfile already support the build; run it only when Flutter
reports missing dependencies:

```powershell
& $flutter pub get
```

Browser with a local backend:

```powershell
& $flutter run -d chrome `
  --dart-define=PEPPER_API_BASE_URL=http://127.0.0.1:8000
```

Android emulator with a local backend:

```powershell
& $flutter run -d emulator-5554 `
  --dart-define=PEPPER_API_BASE_URL=http://10.0.2.2:8000
```

Physical Android device over USB:

```powershell
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb reverse tcp:8000 tcp:8000
& $flutter run -d YOUR_DEVICE_ID `
  --dart-define=PEPPER_API_BASE_URL=http://127.0.0.1:8000
```

`PEPPER_API_BASE_URL` is a build-time value. Without it, the client uses local
development defaults: `127.0.0.1:8000` for web/desktop and `10.0.2.2:8000` for
Android.

The optional ignored `mobile/.env` may provide restricted development cloud
keys for the pest, leaf, and berry-disease features. Phase 7 berry grading does
not require Gemini or Anthropic keys. Never distribute an APK or web bundle
containing unrestricted provider keys.

## 6. Flutter validation and History

Run from `mobile/`:

```powershell
& $flutter analyze
& $flutter test
```

These commands validate source and widget/unit behavior. They do not prove a
successful Android build, device installation, hosted backend, or field
performance.

The current app stores completed analyses and the original selected image in
local History storage. Opening a saved History detail reconstructs the stored
snapshot and must not rerun inference or call an API. Clearing History removes
the app's local database records and saved image copies; it does not delete
source images outside the app's private storage.

## 7. Build a local Android release candidate

The Android project still uses `com.example.mobile` and signs release builds
with the debug key. The resulting APK is suitable only for controlled local
testing:

```powershell
& $flutter build apk --release `
  --dart-define=PEPPER_API_BASE_URL=https://YOUR_PHASE7_BACKEND
```

Output: `mobile/build/app/outputs/flutter-apk/app-release.apk`.

Before public distribution, choose a permanent application ID, configure a
private release keystore outside Git, use an authenticated HTTPS backend, and
remove client-side permanent cloud secrets. See `build_guide.md` for the full
release checklist.

## 8. Research artifact verification

The authoritative current paths are listed in `repository_inventory.md`.
Read-only checks that are safe during routine cleanup include:

```powershell
git diff --check
git status --short --untracked-files=all
Get-FileHash -Algorithm SHA256 `
  ml\grading_forecast\berry_grading\models\v3_phase3_followup\best.pt, `
  ml\grading_forecast\berry_grading\models\v3_phase3_followup\best.onnx, `
  ml\grading_forecast\berry_grading\evaluation\v3_phase3_followup\decision_config_frozen.json, `
  ml\grading_forecast\price_forecasting\phase5\models\selected_model_spec.json
```

Do not run training, export, dataset preparation, Phase 5 experiment runners,
or integrity/evaluation generators merely to check a documentation or cleanup
change. Several research scripts write result files. Run them only as part of
an explicitly planned experiment with protected outputs and a recorded reason.

## 9. Historical workflows

- The byte-preserved V1 label generator and artifacts are under
  `archive/legacy_v1/`.
- V1/V2/PP2 status and evidence documents are under
  `docs/research/historical/`.
- Superseded V1/V2 ML implementations are under
  `ml/archive/grading_forecast/legacy_v1_v2/`. The two V2 model directories
  still referenced by dormant backend fallback services remain in the active
  tree as compatibility holds; none define the Phase 7 `/analyze` path.
- Current V3 and Phase 4-7 evidence remains under `docs/research/`.

Historical commands may be useful for reproduction, but do not run them against
current data or model paths without first reviewing every input and output.

## 10. Repository safety rules

- Do not use `git clean -fdX`.
- Do not delete `.venv` or `.venv-yolo` if package re-downloads must be avoided.
- Do not delete raw data, trained models, frozen results, manifests, or
  provenance because they are ignored or appear unreferenced.
- Do not normalize Phase 5/6 text files; configured integrity hashes use
  canonical LF content while Windows working-tree bytes may use CRLF.
- Do not stage, commit, reset, or rewrite history as part of routine cleanup.
