"""Strict grade-to-price routing over frozen Phase 4/5 artifacts."""

from __future__ import annotations

import csv
from dataclasses import dataclass

from .config import load_config, repo_path


@dataclass(frozen=True)
class MarketForecast:
    price_grade: str
    reference_date: str
    reference_price: float | None
    previous_reference_price: float | None
    latest_observed_return: float | None
    predicted_log_return: float | None
    predicted_return: float | None
    forecast_price: float | None
    forecast_interval_lower: float | None
    forecast_interval_upper: float | None
    persistence_price: float | None
    model_vs_persistence: str
    forecast_target_date: str | None
    source_url: str | None
    evidence_partition: str | None


def route_for_grade(v3_grade: str, config: dict | None = None) -> dict:
    config = config or load_config()
    routing = config["grade_routing"]
    if v3_grade not in routing:
        raise ValueError(f"No price route exists for grade: {v3_grade!r}")
    return dict(routing[v3_grade])


def validate_route(v3_grade: str, forecast: MarketForecast, config: dict | None = None) -> dict:
    route = route_for_grade(v3_grade, config)
    if forecast.price_grade != route["price_grade"]:
        raise ValueError(
            f"Grade/price-series mismatch: {v3_grade} must use {route['price_grade']}, "
            f"not {forecast.price_grade}"
        )
    return route


def canonical_history(config: dict | None = None) -> dict[str, list[dict]]:
    config = config or load_config()
    path = repo_path(config["frozen_price"]["canonical_dataset_path"])
    output = {"Grade 1": [], "Grade 2": []}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row["market"] == "National" and row["price_type"] == "average" and row["grade"] in output:
                output[row["grade"]].append(row)
    for values in output.values():
        values.sort(key=lambda row: row["date"])
    return output


def history_context(grade: str, reference_date: str, histories: dict[str, list[dict]]) -> dict:
    values = histories.get(grade)
    if not values:
        raise ValueError(f"No canonical history for {grade}")
    index = next((i for i, row in enumerate(values) if row["date"] == reference_date), None)
    if index is None:
        raise ValueError(f"No {grade} canonical observation on {reference_date}")
    current = values[index]
    previous = values[index - 1] if index > 0 else None
    current_price = float(current["price_lkr_per_kg"])
    previous_price = float(previous["price_lkr_per_kg"]) if previous else None
    return {
        "reference_price": current_price,
        "previous_reference_price": previous_price,
        "latest_observed_return": None if previous_price is None else current_price / previous_price - 1.0,
        "source_url": current["source_url"],
    }
