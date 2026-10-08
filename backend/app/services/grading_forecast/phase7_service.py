"""Backend boundary for the frozen Phase 7 integrated research pipeline."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.grading_forecast.deployment.phase7.forecast_records import (  # noqa: E402
    ForecastRecordError,
    validate_frozen_forecast_source,
)
from ml.grading_forecast.deployment.phase7.grading_runtime import (  # noqa: E402
    GradingRuntimeError,
    initialize_grading_runtime as initialize_onnx_runtime,
)
from ml.grading_forecast.deployment.phase7.integrated_service import analyze_image_bytes  # noqa: E402


def analyze(image_bytes: bytes, analysis_id: str) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    return analyze_image_bytes(image_bytes, analysis_id, timestamp_utc=timestamp)


def initialize_phase7_runtime() -> None:
    initialize_onnx_runtime()
    validate_frozen_forecast_source()


__all__ = [
    "ForecastRecordError",
    "GradingRuntimeError",
    "analyze",
    "initialize_phase7_runtime",
]
