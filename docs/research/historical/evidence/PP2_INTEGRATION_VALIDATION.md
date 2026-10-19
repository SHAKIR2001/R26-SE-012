# PP2 Integration Validation

Validation date: 2026-08-28

Scope: Phase 5 backend/mobile integration validation for the Berry Grading and Export Price Forecasting component.

## Startup

Backend startup method:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend
```

Observed result:

- FastAPI application startup completed.
- Validation host: `http://127.0.0.1:8000`.
- Endpoint calls completed in one controlled validation pass.

## Runtime Artifact Resolution

Observed from backend code:

- Berry grading runtime attempts to load `ml/grading_forecast/berry_grading/models/berry_mobilenetv2_best.onnx` and `ml/grading_forecast/berry_grading/models/class_names.json`.
- Price forecasting runtime attempts to use default raw input files `data/raw/market_prices/black_pepper_prices.csv` or `data/raw/market_prices/sample_black_pepper_prices.csv` before loading the default forecast model directory.
- The current backend runtime does not automatically resolve the PP2 V2 research artifact directories `models/v2/` or `models/v2_phase4/`.

Runtime status:

- Berry endpoint used the legacy/root ONNX model artifact.
- Price endpoint returned `demo_baseline`.
- Firebase storage was not configured, so storage was skipped safely.

## Sample Image

Image used:

`data/processed/grading_forecast/berry_split_v2/test/grade_1/sample_002/20260508_152537.jpg`

The image was not modified.

## Health Endpoint

Request:

`GET /api/v1/grading-forecast/health`

HTTP status: 200

Response:

```json
{
  "status": "ok",
  "component": "berry_grading_export_price_forecasting"
}
```

Result: PASS.

## Price Forecast Endpoint

Request:

`GET /api/v1/grading-forecast/price-forecast`

HTTP status: 200

Response:

```json
{
  "status": "success",
  "component": "berry_grading_export_price_forecasting",
  "forecast": {
    "model": "demo_baseline",
    "current_price_lkr_per_kg": 1394,
    "predicted_price_lkr_per_kg": 1379,
    "trend": "stable",
    "forecast_period": "next_period",
    "metrics": {
      "mae": null,
      "rmse": null
    }
  }
}
```

Result: PASS with fallback.

Important note: this runtime response is not using the Phase 3 or Phase 4 V2 forecasting research artifacts.

## Grade-Only Endpoint

Request:

`POST /api/v1/grading-forecast/grade-only`

Multipart field:

- `image`: `data/processed/grading_forecast/berry_split_v2/test/grade_1/sample_002/20260508_152537.jpg`

HTTP status: 200

Observed grading result:

```json
{
  "predicted_grade": "Grade 1",
  "quality_score": 79.7,
  "confidence": 0.65,
  "model_indicator": "Real grading model (ONNX) was used for predicted grade."
}
```

Result: PASS.

Important note: the runtime ONNX path is the legacy/root model path, not the PP2 V2 model directory.

## Analyze Endpoint

Request:

`POST /api/v1/grading-forecast/analyze`

Multipart field:

- `image`: `data/processed/grading_forecast/berry_split_v2/test/grade_1/sample_002/20260508_152537.jpg`

HTTP status: 200

Observed response summary:

```json
{
  "status": "success",
  "component": "berry_grading_export_price_forecasting",
  "image_analysis": {
    "image_id": "20260508_152537.jpg",
    "processed": true,
    "note": "Camera-based visual analysis only"
  },
  "grading": {
    "predicted_grade": "Grade 1",
    "quality_score": 79.7,
    "confidence": 0.65,
    "model_indicator": "Real grading model (ONNX) was used for predicted grade."
  },
  "forecast": {
    "model": "demo_baseline",
    "current_price_lkr_per_kg": 1594,
    "predicted_price_lkr_per_kg": 1609,
    "trend": "stable"
  },
  "recommendation": {
    "decision": "SELL_EXPORT",
    "urgency_level": "MEDIUM"
  },
  "storage": {
    "saved_to_firebase": false,
    "document_id": null
  }
}
```

Result: PASS with forecast/storage fallback.

## Mobile Flow

Read-only inspection result:

- Flutter service exists at `mobile/lib/features/grading_forecast/services/grading_forecast_api_service.dart`.
- Mobile analyze flow calls `POST /api/v1/grading-forecast/analyze`.
- Mobile recommend flow calls `POST /api/v1/grading-forecast/recommend`.
- Default backend URL is `http://localhost:8000` for desktop/web and `http://10.0.2.2:8000` for Android emulator.

Flutter was not run during this validation pass to conserve time and tooling.

## Phase 5 Conclusion

PP2 demo path is known and recorded:

- Start FastAPI backend.
- Use the existing API endpoints.
- Demonstrate grade-only and analyze using an existing sample image.
- State honestly that the current backend runtime uses the legacy/root ONNX model for grading and demo fallback for price forecasting.

Phase 5 status: COMPLETE with runtime limitations.
