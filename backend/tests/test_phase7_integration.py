from __future__ import annotations

import base64
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
TINY_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")


def _result(decision: str = "NO_PEPPER", category: str = "REJECT") -> dict:
    rejected = decision in {"NO_PEPPER", "POOR_IMAGE"}
    return {"schema_version": "phase6_decision_support_v1",
        "grading": {"status": "REJECTED" if rejected else "ACCEPTED", "decision": decision,
            "grade": None if rejected else "V3 Grade 1", "model_confidence": 0.0 if rejected else 0.9,
            "detection_confidence": 0.0 if rejected else 0.9, "class_margin": 0.0 if rejected else 0.8,
            "quality_status": "NOT_APPLICABLE", "rejection_reason": "no_detection_above_threshold" if rejected else None,
            "physical_sample_id": None, "confidence_interpretation": "model score; not a calibrated probability"},
        "market": {"status": "NOT_AVAILABLE_REJECTED_INPUT" if rejected else "AVAILABLE", "source": None if rejected else "EAC farm-gate reference price",
            "price_grade": None if rejected else "Grade 1", "latest_reference_date": None,
            "latest_reference_price": None if rejected else 1987.5,
            "previous_reference_price": None, "latest_observed_return": None, "forecast_target_date": None,
            "forecast_log_return": None, "forecast_return": None,
            "forecast_price": None if rejected else 1990.6,
            "forecast_direction": None if rejected else "UP",
            "forecast_interval": None, "persistence_price": None, "model_vs_persistence": None, "forecast_signal": None},
        "decision_support": {"category": category, "summary": "research result", "limitations": ["research only"]},
        "trace": {"grading_model_sha256": "hash", "final_decision_support_category": category},
        "runtime": {"grading": "ONNX_RUNTIME_CPU", "price": "FROZEN_PHASE5_FORECAST_RECORD", "mobile": "BACKEND_API", "tflite": "NOT_IMPLEMENTED_OR_CLAIMED"}}


def test_invalid_image_returns_400() -> None:
    response = client.post("/api/v1/grading-forecast/analyze", files={"image": ("bad.jpg", b"bad", "image/jpeg")})
    assert response.status_code == 400


def test_rejection_response_has_no_market_forecast(monkeypatch) -> None:
    from app.api.routes import grading_forecast as routes
    monkeypatch.setattr(routes, "analyze_phase7", lambda *_: _result())
    response = client.post("/api/v1/grading-forecast/analyze", files={"image": ("x.png", TINY_PNG, "image/png")})
    assert response.status_code == 200
    body = response.json()
    assert body["decision_support"]["category"] == "REJECT"
    assert body["market"]["forecast_price"] is None


def test_accepted_response_preserves_phase6_schema(monkeypatch) -> None:
    from app.api.routes import grading_forecast as routes
    monkeypatch.setattr(routes, "analyze_phase7", lambda *_: _result("GRADE_1", "HIGH_UNCERTAINTY_OUTLOOK"))
    response = client.post("/api/v1/grading-forecast/analyze", files={"image": ("x.png", TINY_PNG, "image/png")})
    assert response.status_code == 200
    assert response.json()["market"]["price_grade"] == "Grade 1"


def test_missing_price_and_forecast_categories_are_preserved(monkeypatch) -> None:
    from app.api.routes import grading_forecast as routes
    for category in ("PRICE_DATA_UNAVAILABLE", "FORECAST_UNAVAILABLE"):
        payload = _result("GRADE_1", category)
        payload["market"]["status"] = category
        payload["market"]["forecast_price"] = None
        monkeypatch.setattr(routes, "analyze_phase7", lambda *_, value=payload: value)
        response = client.post("/api/v1/grading-forecast/analyze", files={"image": ("x.png", TINY_PNG, "image/png")})
        assert response.status_code == 200
        assert response.json()["decision_support"]["category"] == category
        assert response.json()["market"]["forecast_price"] is None


def test_inference_failure_returns_503(monkeypatch) -> None:
    from app.api.routes import grading_forecast as routes
    monkeypatch.setattr(routes, "analyze_phase7", lambda *_: (_ for _ in ()).throw(routes.GradingRuntimeError("failed")))
    response = client.post("/api/v1/grading-forecast/analyze", files={"image": ("x.png", TINY_PNG, "image/png")})
    assert response.status_code == 503


def test_forecast_integrity_failure_returns_specific_503(monkeypatch) -> None:
    from app.api.routes import grading_forecast as routes
    monkeypatch.setattr(
        routes,
        "analyze_phase7",
        lambda *_: (_ for _ in ()).throw(routes.ForecastRecordError("changed")),
    )
    response = client.post(
        "/api/v1/grading-forecast/analyze",
        files={"image": ("x.png", TINY_PNG, "image/png")},
    )
    assert response.status_code == 503
    assert "forecast evidence" in response.json()["detail"]


def test_oversized_upload_is_rejected_before_inference(monkeypatch) -> None:
    from app.api.routes import grading_forecast as routes
    called = False

    def should_not_run(*_):
        nonlocal called
        called = True
        return _result()

    monkeypatch.setattr(routes, "analyze_phase7", should_not_run)
    response = client.post(
        "/api/v1/grading-forecast/analyze",
        files={
            "image": (
                "large.jpg",
                b"x" * (routes.MAX_IMAGE_UPLOAD_BYTES + 1),
                "image/jpeg",
            )
        },
    )
    assert response.status_code == 413
    assert called is False


def test_rejected_response_with_market_data_is_withheld(monkeypatch) -> None:
    from app.api.routes import grading_forecast as routes
    payload = _result()
    payload["market"]["status"] = "AVAILABLE"
    payload["market"]["price_grade"] = "Grade 1"
    payload["market"]["forecast_price"] = 1900.0
    monkeypatch.setattr(routes, "analyze_phase7", lambda *_: payload)
    response = client.post(
        "/api/v1/grading-forecast/analyze",
        files={"image": ("x.png", TINY_PNG, "image/png")},
    )
    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Integrated analysis produced an invalid response and was withheld."
    )


def test_ready_returns_503_when_runtime_is_not_ready(monkeypatch) -> None:
    from app.api.routes import grading_forecast as routes
    monkeypatch.setattr(
        routes,
        "initialize_phase7_runtime",
        lambda: (_ for _ in ()).throw(routes.ForecastRecordError("missing")),
    )
    response = client.get("/api/v1/grading-forecast/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_legacy_trading_endpoint_is_retired() -> None:
    assert client.post("/api/v1/grading-forecast/recommend", json={}).status_code == 410


def test_real_grade1_api_path() -> None:
    root = Path(__file__).resolve().parents[2]
    path = root / "data/raw/Pepper Berry Grading V3.yolov8/test/images/20260508_160550_jpg.rf.BUF1sZWo8GvE4UCSfj74.jpg"
    response = client.post("/api/v1/grading-forecast/analyze", files={"image": (path.name, path.read_bytes(), "image/jpeg")})
    assert response.status_code == 200
    body = response.json()
    assert body["grading"]["decision"] == "GRADE_1"
    assert body["market"]["price_grade"] == "Grade 1"
    assert body["decision_support"]["category"] == "HIGH_UNCERTAINTY_OUTLOOK"
