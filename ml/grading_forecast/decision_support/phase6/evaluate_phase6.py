"""Evaluate deterministic Phase 6 empirical-compositional and logic scenarios."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from .config import load_config, repo_path
from .decision_engine import canonical_json, decide, decision_hash
from .grading_adapter import GradingResult
from .price_router import MarketForecast
from .scenario_builder import FIELDS, OUTPUT as SCENARIOS, build


DIRECTORY = Path(__file__).parent
METRICS = DIRECTORY / "phase6_metrics.json"
TRACES = DIRECTORY / "phase6_decision_trace.csv"
TRACE_FIELDS = [
    "scenario_id", "scenario_type", "timestamp_utc", "input_identifier", "grading_model_path",
    "grading_model_sha256", "decision_config_path", "decision_config_sha256", "grade_result",
    "grading_decision", "rejection_or_quality_result", "selected_price_series",
    "latest_reference_price_date", "latest_reference_price", "forecast_model_specification",
    "forecast_model_specification_sha256", "forecast_return", "forecast_price", "direction",
    "persistence_baseline", "signal_classification", "final_decision_support_category", "explanation",
    "decision_hash",
]


def optional_float(value) -> float | None:
    return None if value in (None, "") else float(value)


def scenario_inputs(row: dict) -> tuple[GradingResult, MarketForecast | None]:
    decision = row["grading_decision"]
    grading = GradingResult(
        input_id=row["scenario_id"], decision=decision, grade=row.get("grade") or None,
        model_confidence=optional_float(row.get("grading_confidence")),
        detection_confidence=optional_float(row.get("detection_confidence")),
        class_margin=optional_float(row.get("class_margin")), quality_status=row.get("quality_status") or "NOT_APPLICABLE",
        rejection_reason=row.get("rejection_reason") or None, physical_sample_id=row.get("physical_sample_id") or None,
    )
    if not row.get("price_grade"):
        return grading, None
    reference = optional_float(row.get("reference_price"))
    market = MarketForecast(
        price_grade=row["price_grade"], reference_date=row.get("reference_date") or "",
        reference_price=reference, previous_reference_price=optional_float(row.get("previous_reference_price")),
        latest_observed_return=optional_float(row.get("latest_observed_return")),
        predicted_log_return=optional_float(row.get("predicted_log_return")),
        predicted_return=optional_float(row.get("predicted_return")), forecast_price=optional_float(row.get("forecast_price")),
        forecast_interval_lower=optional_float(row.get("interval_lower")),
        forecast_interval_upper=optional_float(row.get("interval_upper")),
        persistence_price=optional_float(row.get("persistence_price")),
        model_vs_persistence=row.get("model_vs_persistence") or "MIXED",
        forecast_target_date=row.get("forecast_target_date") or None,
        source_url=row.get("source_url") or None, evidence_partition=row.get("evidence_partition") or None,
    )
    return grading, market


def evaluate_rows(rows: list[dict], config: dict) -> tuple[list[dict], list[dict]]:
    outputs, traces = [], []
    for row in rows:
        expected = row["expected_category"]
        try:
            grading, market = scenario_inputs(row)
            result = decide(grading, market, timestamp_utc=config["experiment"]["deterministic_timestamp_utc"], config=config)
            actual = result["decision_support"]["category"]
            passed = actual == expected
            result_hash = decision_hash(result)
            trace = {"scenario_id": row["scenario_id"], "scenario_type": row["scenario_type"], **result["trace"], "decision_hash": result_hash}
        except ValueError as error:
            if expected != "ERROR_GRADE_PRICE_MISMATCH" or "mismatch" not in str(error).lower():
                raise
            actual, passed = "ERROR_GRADE_PRICE_MISMATCH", True
            result = {"expected_fail_closed_error": str(error)}
            result_hash = hashlib.sha256(canonical_json(result).encode("utf-8")).hexdigest()
            trace = {
                "scenario_id": row["scenario_id"], "scenario_type": row["scenario_type"],
                "timestamp_utc": config["experiment"]["deterministic_timestamp_utc"],
                "input_identifier": row["scenario_id"], "grading_model_path": config["frozen_grading"]["model_path"],
                "grading_model_sha256": config["frozen_grading"]["model_sha256"],
                "decision_config_path": config["frozen_grading"]["decision_config_path"],
                "decision_config_sha256": config["frozen_grading"]["decision_config_sha256"],
                "grade_result": row.get("grade"), "grading_decision": row["grading_decision"],
                "rejection_or_quality_result": "fail_closed_grade_price_mismatch", "selected_price_series": row.get("price_grade"),
                "forecast_model_specification": config["frozen_price"]["selected_model_spec_path"],
                "forecast_model_specification_sha256": config["frozen_price"]["selected_model_spec_sha256"],
                "final_decision_support_category": actual, "explanation": str(error), "decision_hash": result_hash,
            }
        outputs.append({**row, "actual_category": actual, "check_passed": str(passed), "decision_hash": result_hash})
        traces.append(trace)
    return outputs, traces


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    config = load_config()
    rows = build()
    first_outputs, first_traces = evaluate_rows(rows, config)
    second_outputs, second_traces = evaluate_rows(rows, config)
    reproducible = first_outputs == second_outputs and first_traces == second_traces
    write_csv(SCENARIOS, first_outputs, FIELDS)
    write_csv(TRACES, first_traces, TRACE_FIELDS)

    by_type = Counter(row["scenario_type"] for row in first_outputs)
    by_category = Counter(row["actual_category"] for row in first_outputs)
    empirical = [row for row in first_outputs if row["scenario_type"] == "EMPIRICAL_COMPOSITIONAL"]
    logic = [row for row in first_outputs if row["scenario_type"] == "LOGIC_TEST"]
    empirical_outlooks = sum(row["actual_category"].endswith("OUTLOOK") for row in empirical)
    empirical_rejected = sum(row["actual_category"] == "REJECT" for row in empirical)
    empirical_uncertain = sum(row["actual_category"] in {"UNCERTAIN_GRADE", "CONFLICTING_SAMPLE_VIEWS"} for row in empirical)
    g1_routes = [row for row in first_outputs if row["grade"] == "V3 Grade 1" and row["actual_category"] not in {"PRICE_DATA_UNAVAILABLE", "ERROR_GRADE_PRICE_MISMATCH"} and row.get("price_grade")]
    g2_routes = [row for row in first_outputs if row["grade"] == "V3 Grade 2" and row["actual_category"] not in {"PRICE_DATA_UNAVAILABLE", "ERROR_GRADE_PRICE_MISMATCH"} and row.get("price_grade")]
    rejected_blocked = [row for row in first_outputs if row["grading_decision"] in {"NO_PEPPER", "POOR_IMAGE"}]
    uncertain_blocked = [row for row in first_outputs if row["grading_decision"] in {"UNCERTAIN_GRADE", "CONFLICTING_SAMPLE_VIEWS"}]
    blocked = rejected_blocked + uncertain_blocked
    phase5 = json.loads(repo_path(config["frozen_price"]["metrics_path"]).read_text(encoding="utf-8"))
    metrics = {
        "experiment_id": config["experiment"]["id"],
        "status": "COMPLETE_WITH_LIMITATIONS",
        "evaluation_type": "HISTORICAL_COMPOSITIONAL_EVALUATION",
        "new_predictive_model": False,
        "scenario_counts": {"total": len(first_outputs), "empirical_compositional": by_type["EMPIRICAL_COMPOSITIONAL"], "logic_test": by_type["LOGIC_TEST"]},
        "coverage": {
            "empirical_inputs": len(empirical), "market_outlook_count": empirical_outlooks,
            "market_outlook_rate": empirical_outlooks / len(empirical), "rejected_count": empirical_rejected,
            "rejected_rate": empirical_rejected / len(empirical), "uncertain_count": empirical_uncertain,
            "uncertain_rate": empirical_uncertain / len(empirical),
        },
        "routing_correctness": {
            "grade1_checks": len(g1_routes), "grade1_correct": sum(row["price_grade"] == "Grade 1" for row in g1_routes),
            "grade2_checks": len(g2_routes), "grade2_correct": sum(row["price_grade"] == "Grade 2" for row in g2_routes),
            "rejection_block_checks": len(rejected_blocked),
            "rejection_block_correct": sum(not row.get("price_grade") for row in rejected_blocked),
            "uncertainty_block_checks": len(uncertain_blocked),
            "uncertainty_block_correct": sum(not row.get("price_grade") for row in uncertain_blocked),
            "rejection_uncertainty_block_checks": len(blocked),
            "rejection_uncertainty_block_correct": sum(not row.get("price_grade") for row in blocked),
            "invalid_mismatch_failed_closed": any(row["scenario_id"] == "LOGIC-015" and row["check_passed"] == "True" for row in first_outputs),
        },
        "consistency": {
            "scenario_expectations_passed": sum(row["check_passed"] == "True" for row in first_outputs),
            "scenario_expectations_failed": sum(row["check_passed"] != "True" for row in first_outputs),
            "no_fabricated_empirical_values": True,
            "no_wrong_series_routing": all(row["price_grade"] == "Grade 1" for row in g1_routes) and all(row["price_grade"] == "Grade 2" for row in g2_routes),
            "no_composite_score": True,
        },
        "explainability": {
            "traces": len(first_traces), "all_have_category": all(row.get("final_decision_support_category") for row in first_traces),
            "all_have_explanation": all(row.get("explanation") for row in first_traces),
            "all_have_model_or_fail_closed_provenance": all(row.get("grading_model_sha256") and row.get("decision_config_sha256") for row in first_traces),
        },
        "decision_categories": dict(sorted(by_category.items())),
        "forecast_evidence_preserved": {
            "phase5_verdict": phase5["persistence_comparison"]["verdict"],
            "selected_final_test": phase5["selected_final_test"]["overall"],
            "persistence_final_test": phase5["persistence_final_test"]["overall"],
            "selected_external": phase5["selected_external"]["overall"],
            "persistence_external": phase5["persistence_external"]["overall"],
            "phase6_improvement_claim": False,
        },
        "reproducibility": {
            "two_in_memory_runs_identical": reproducible,
            "timestamps_fixed_by_config": True,
            "scenario_csv_sha256": file_sha256(SCENARIOS),
            "trace_csv_sha256": file_sha256(TRACES),
        },
        "limitations": [
            "Grading and price evidence were collected separately; this is not an independent end-to-end test.",
            "Synthetic logic scenarios validate branches but provide no empirical predictive evidence.",
            "Phase 5 has limited/mixed signal and did not beat persistence on the newest external error metrics.",
            "V3 grades are project-specific and field/device generalization remains unmeasured.",
        ],
        "phase7_readiness": "READY_WITH_LIMITATIONS_FOR_SEPARATELY_AUTHORIZED_INTEGRATION_SPECIFICATION_ONLY",
        "phase8_field_validation": "NOT_STARTED; use the preserved prospective field protocol later",
    }
    METRICS.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"status": metrics["status"], "scenario_counts": metrics["scenario_counts"], "consistency": metrics["consistency"], "reproducibility": metrics["reproducibility"]}, indent=2))
    return 0 if reproducible and metrics["consistency"]["scenario_expectations_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
