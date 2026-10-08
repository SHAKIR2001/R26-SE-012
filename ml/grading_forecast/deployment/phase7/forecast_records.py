"""Serve the latest approved frozen Phase 5 forecast record for an exact grade."""

from __future__ import annotations

import csv
import math
from pathlib import Path

from ml.grading_forecast.decision_support.phase6.price_router import MarketForecast, canonical_history, history_context, route_for_grade

from .config import frozen_text_matches, load_config, repo_path


class ForecastRecordError(RuntimeError):
    pass


def validate_frozen_forecast_source() -> Path:
    settings = load_config()["price_runtime"]
    source = repo_path(settings["source"])
    if not frozen_text_matches(
        source,
        raw_sha256=settings["source_sha256"],
        canonical_sha256=settings["source_canonical_text_sha256"],
    ):
        raise ForecastRecordError("Frozen Phase 5 forecast evidence is unavailable or changed")
    return source


def latest_frozen_forecast(v3_grade: str) -> MarketForecast | None:
    route = route_for_grade(v3_grade)
    source = validate_frozen_forecast_source()
    with source.open(newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.DictReader(handle) if row["grade"] == route["price_grade"]]
    if not rows:
        return None
    row = max(rows, key=lambda item: item["feature_date"])
    context = history_context(row["grade"], row["feature_date"], canonical_history())
    actual = float(row["actual_price"])
    ridge_error = abs(float(row["predicted_price"])-actual)
    persistence_error = abs(float(row["current_price"])-actual)
    comparison = "RIDGE_BETTER" if ridge_error < persistence_error else "PERSISTENCE_BETTER" if ridge_error > persistence_error else "TIE"
    return MarketForecast(price_grade=row["grade"], reference_date=row["feature_date"], reference_price=float(row["current_price"]),
        previous_reference_price=context["previous_reference_price"], latest_observed_return=context["latest_observed_return"],
        predicted_log_return=float(row["predicted_target"]), predicted_return=float(row["predicted_return"]),
        forecast_price=float(row["predicted_price"]), forecast_interval_lower=float(row["interval_lower_price"]),
        forecast_interval_upper=float(row["interval_upper_price"]), persistence_price=float(row["current_price"]),
        model_vs_persistence=comparison, forecast_target_date=row["target_date"], source_url=context["source_url"],
        evidence_partition="EXTERNAL_NEWEST_FROZEN_RECORD")
