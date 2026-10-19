"""Executable rejection-first bridge into the authoritative Phase 6 engine."""

from __future__ import annotations

from ml.grading_forecast.decision_support.phase6.decision_engine import decide
from ml.grading_forecast.decision_support.phase6.grading_adapter import aggregate_sample

from .forecast_records import latest_frozen_forecast
from .grading_runtime import grade_image


def _complete(grading, *, timestamp_utc: str | None = None) -> dict:
    market = latest_frozen_forecast(grading.grade) if grading.status == "ACCEPTED" else None
    result = decide(grading, market, timestamp_utc=timestamp_utc)
    result["runtime"] = {"grading": "ONNX_RUNTIME_CPU", "price": "FROZEN_PHASE5_FORECAST_RECORD",
                         "mobile": "BACKEND_API", "tflite": "NOT_IMPLEMENTED_OR_CLAIMED"}
    return result


def analyze_image_bytes(image_bytes: bytes, input_id: str, *, timestamp_utc: str | None = None) -> dict:
    grading, raw = grade_image(image_bytes, input_id)
    result = _complete(grading, timestamp_utc=timestamp_utc)
    result["trace"]["detection_count"] = raw["detection_count"]
    result["trace"]["bbox_xyxy"] = raw["box_xyxy"]
    result["trace"]["quality_scores"] = raw["quality"]
    return result


def analyze_sample_bytes(images: list[tuple[str, bytes]], sample_id: str, *, timestamp_utc: str | None = None) -> dict:
    if not images:
        raise ValueError("At least one image is required")
    views = [grade_image(payload, name)[0] for name, payload in images]
    grading, aggregation = aggregate_sample(views, sample_id)
    result = _complete(grading, timestamp_utc=timestamp_utc)
    result["grading"]["image_decisions"] = [view.__dict__ for view in views]
    result["grading"]["aggregation"] = aggregation
    return result
