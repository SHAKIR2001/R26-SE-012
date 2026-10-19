"""Transparent rule-based fusion of frozen grading and market evidence."""

from __future__ import annotations

import hashlib
import json

from .config import load_config
from .decision_rules import forecast_direction, outlook_category, signal_classification
from .grading_adapter import GradingResult
from .price_router import MarketForecast, validate_route


def _empty_market(status: str) -> dict:
    return {
        "status": status, "source": None, "price_grade": None, "latest_reference_date": None,
        "latest_reference_price": None, "previous_reference_price": None, "latest_observed_return": None,
        "forecast_target_date": None, "forecast_log_return": None, "forecast_return": None,
        "forecast_price": None, "forecast_direction": None, "forecast_interval": None,
        "persistence_price": None, "model_vs_persistence": None, "forecast_signal": None,
    }


def decide(
    grading: GradingResult,
    market: MarketForecast | None,
    *,
    timestamp_utc: str | None = None,
    config: dict | None = None,
) -> dict:
    config = config or load_config()
    timestamp = timestamp_utc or config["experiment"]["deterministic_timestamp_utc"]
    frozen_grading = config["frozen_grading"]
    frozen_price = config["frozen_price"]
    grading_payload = {
        "status": grading.status, "decision": grading.decision, "grade": grading.grade,
        "model_confidence": grading.model_confidence, "detection_confidence": grading.detection_confidence,
        "class_margin": grading.class_margin, "quality_status": grading.quality_status,
        "rejection_reason": grading.rejection_reason, "physical_sample_id": grading.physical_sample_id,
        "confidence_interpretation": "model score; not a calibrated probability",
    }
    common_limitations = [
        "V3 grades are project-specific and are not official SLS, buyer, export-certification, or laboratory grades.",
        "This is research decision support, not an autonomous trading recommendation.",
        "The Phase 5 price signal is limited/mixed and persistence remains a strong baseline.",
    ]

    if grading.status == "REJECTED":
        category = "REJECT"
        summary = "Valid pepper was not established; no grade-specific market outlook was generated."
        market_payload = _empty_market("NOT_AVAILABLE_REJECTED_INPUT")
    elif grading.status == "UNCERTAIN":
        category = "CONFLICTING_SAMPLE_VIEWS" if grading.decision == "CONFLICTING_SAMPLE_VIEWS" else "UNCERTAIN_GRADE"
        summary = "A reliable grade was not established; no grade-specific market outlook was generated."
        market_payload = _empty_market("NOT_AVAILABLE_UNCERTAIN_GRADE")
    elif market is None or market.reference_price is None:
        category = "PRICE_DATA_UNAVAILABLE"
        summary = "The grade was accepted, but the required grade-specific reference price is unavailable."
        market_payload = _empty_market("PRICE_DATA_UNAVAILABLE")
    elif market.forecast_price is None or market.predicted_return is None or market.predicted_log_return is None:
        validate_route(grading.grade, market, config)
        category = "FORECAST_UNAVAILABLE"
        summary = "The grade-specific reference price is available, but no frozen Phase 5 forecast is available."
        market_payload = _empty_market("FORECAST_UNAVAILABLE") | {
            "source": frozen_price["price_source_label"], "price_grade": market.price_grade,
            "latest_reference_date": market.reference_date, "latest_reference_price": market.reference_price,
            "previous_reference_price": market.previous_reference_price,
            "latest_observed_return": market.latest_observed_return, "persistence_price": market.persistence_price,
        }
    else:
        route = validate_route(grading.grade, market, config)
        direction = forecast_direction(market.reference_price, market.forecast_price)
        signal = signal_classification(
            market.reference_price, market.forecast_interval_lower,
            market.forecast_interval_upper, market.model_vs_persistence,
        )
        category = outlook_category(direction, signal)
        interval = None
        if market.forecast_interval_lower is not None and market.forecast_interval_upper is not None:
            interval = {
                "lower": market.forecast_interval_lower, "upper": market.forecast_interval_upper,
                "label": config["uncertainty_handling"]["interval_label"],
                "probability_claim": False,
            }
        market_payload = {
            "status": "AVAILABLE", "source": frozen_price["price_source_label"],
            "source_organization": frozen_price["price_source_organization"], "source_url": market.source_url,
            "unit": frozen_price["unit"], "price_grade": market.price_grade,
            "model_scope": route["model_scope"], "latest_reference_date": market.reference_date,
            "latest_reference_price": market.reference_price,
            "latest_price_interpretation": "observed EAC reference; not a forecast or guaranteed transaction price",
            "previous_reference_price": market.previous_reference_price,
            "latest_observed_return": market.latest_observed_return,
            "forecast_target_date": market.forecast_target_date,
            "forecast_log_return": market.predicted_log_return,
            "forecast_return": market.predicted_return,
            "forecast_price": market.forecast_price,
            "forecast_direction": direction, "forecast_interval": interval,
            "persistence_price": market.persistence_price,
            "model_vs_persistence": market.model_vs_persistence,
            "forecast_signal": signal,
            "evidence_partition": market.evidence_partition,
        }
        summary = (
            f"Accepted as {grading.grade}. The frozen {market.price_grade} forecast indicates {direction.lower()} "
            f"movement, with signal classified as {signal}. This is a limited research outlook, not a buy/sell instruction."
        )

    trace = {
        "timestamp_utc": timestamp, "input_identifier": grading.input_id,
        "grading_model_path": frozen_grading["model_path"], "grading_model_sha256": frozen_grading["model_sha256"],
        "decision_config_path": frozen_grading["decision_config_path"], "decision_config_sha256": frozen_grading["decision_config_sha256"],
        "grade_result": grading.grade, "grading_decision": grading.decision,
        "rejection_or_quality_result": grading.rejection_reason or grading.quality_status,
        "selected_price_series": market_payload.get("price_grade"),
        "latest_reference_price_date": market_payload.get("latest_reference_date"),
        "latest_reference_price": market_payload.get("latest_reference_price"),
        "forecast_model_specification": frozen_price["selected_model_spec_path"],
        "forecast_model_specification_sha256": frozen_price["selected_model_spec_sha256"],
        "forecast_return": market_payload.get("forecast_return"), "forecast_price": market_payload.get("forecast_price"),
        "direction": market_payload.get("forecast_direction"), "persistence_baseline": market_payload.get("persistence_price"),
        "signal_classification": market_payload.get("forecast_signal"),
        "final_decision_support_category": category, "explanation": summary,
    }
    return {
        "schema_version": "phase6_decision_support_v1", "grading": grading_payload,
        "market": market_payload,
        "decision_support": {"category": category, "summary": summary, "limitations": common_limitations},
        "trace": trace,
    }


def canonical_json(result: dict) -> str:
    return json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def decision_hash(result: dict) -> str:
    return hashlib.sha256(canonical_json(result).encode("utf-8")).hexdigest()
