"""Build separate empirical-compositional and synthetic logic scenarios."""

from __future__ import annotations

import csv
from pathlib import Path

from .config import load_config, repo_path
from .decision_rules import forecast_direction, outlook_category, signal_classification
from .price_router import canonical_history, history_context


OUTPUT = Path(__file__).with_name("phase6_decision_scenarios.csv")
FIELDS = [
    "scenario_id", "scenario_type", "source_grading_id", "source_price_id", "grading_decision", "grade",
    "grading_confidence", "detection_confidence", "class_margin", "quality_status", "rejection_reason",
    "physical_sample_id", "price_grade", "reference_date", "reference_price", "previous_reference_price",
    "latest_observed_return", "predicted_log_return", "predicted_return", "forecast_price",
    "interval_lower", "interval_upper", "persistence_price", "model_vs_persistence", "forecast_target_date",
    "source_url", "evidence_partition", "expected_category", "expected_rationale", "measurement_status",
    "actual_category", "check_passed", "decision_hash",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def empirical_scenarios(config: dict) -> list[dict]:
    settings = config["historical_scenarios"]
    positives = read_csv(repo_path(settings["positive_decisions_path"]))
    negatives = read_csv(repo_path(settings["negative_decisions_path"]))
    forecasts = read_csv(repo_path(config["frozen_price"]["external_predictions_path"]))
    histories = canonical_history(config)
    accepted_by_grade = {
        grade: [row for row in positives if row["decision"] == decision]
        for grade, decision in (("Grade 1", "GRADE_1"), ("Grade 2", "GRADE_2"))
    }
    grade_offsets = {"Grade 1": 0, "Grade 2": 0}
    output = []
    for index, forecast in enumerate(forecasts, start=1):
        grade = forecast["grade"]
        grading_row = accepted_by_grade[grade][grade_offsets[grade]]
        grade_offsets[grade] += 1
        context = history_context(grade, forecast["feature_date"], histories)
        actual = float(forecast["actual_price"])
        ridge_error = abs(float(forecast["predicted_price"]) - actual)
        persistence_error = abs(float(forecast["current_price"]) - actual)
        comparison = "RIDGE_BETTER" if ridge_error < persistence_error else "PERSISTENCE_BETTER" if ridge_error > persistence_error else "TIE"
        direction = forecast_direction(float(forecast["current_price"]), float(forecast["predicted_price"]))
        signal = signal_classification(float(forecast["current_price"]), float(forecast["interval_lower_price"]), float(forecast["interval_upper_price"]), comparison)
        output.append({
            "scenario_id": f"EMP-{index:03d}", "scenario_type": "EMPIRICAL_COMPOSITIONAL",
            "source_grading_id": grading_row["image_id"],
            "source_price_id": f"{forecast['grade']}|{forecast['feature_date']}|{forecast['target_date']}",
            "grading_decision": grading_row["decision"], "grade": grading_row["grade"],
            "grading_confidence": grading_row["model_confidence"], "detection_confidence": grading_row["detection_confidence"],
            "class_margin": grading_row["class_margin"], "quality_status": "PASSED",
            "rejection_reason": grading_row["rejection_reason"], "physical_sample_id": grading_row["physical_sample_id"],
            "price_grade": grade, "reference_date": forecast["feature_date"], "reference_price": forecast["current_price"],
            "previous_reference_price": context["previous_reference_price"], "latest_observed_return": context["latest_observed_return"],
            "predicted_log_return": forecast["predicted_target"], "predicted_return": forecast["predicted_return"],
            "forecast_price": forecast["predicted_price"], "interval_lower": forecast["interval_lower_price"],
            "interval_upper": forecast["interval_upper_price"], "persistence_price": forecast["current_price"],
            "model_vs_persistence": comparison, "forecast_target_date": forecast["target_date"],
            "source_url": context["source_url"], "evidence_partition": forecast["partition"],
            "expected_category": outlook_category(direction, signal),
            "expected_rationale": "Frozen grading decision composed with a same-grade frozen Phase 5 external prediction; not an end-to-end observation.",
            "measurement_status": "RECORDED_FROZEN_EVIDENCE",
        })
    selected = [
        next(row for row in negatives if row["decision"] == "NO_PEPPER"),
        next(row for row in negatives if row["decision"] == "POOR_IMAGE"),
        next(row for row in positives if row["decision"] == "UNCERTAIN_GRADE"),
    ]
    for offset, grading_row in enumerate(selected, start=len(output) + 1):
        expected = "REJECT" if grading_row["decision"] in {"NO_PEPPER", "POOR_IMAGE"} else "UNCERTAIN_GRADE"
        output.append({
            "scenario_id": f"EMP-{offset:03d}", "scenario_type": "EMPIRICAL_COMPOSITIONAL",
            "source_grading_id": grading_row["image_id"], "source_price_id": "",
            "grading_decision": grading_row["decision"], "grade": grading_row["grade"],
            "grading_confidence": grading_row["model_confidence"], "detection_confidence": grading_row["detection_confidence"],
            "class_margin": grading_row["class_margin"],
            "quality_status": "FAILED" if grading_row["decision"] == "POOR_IMAGE" else "NOT_APPLICABLE",
            "rejection_reason": grading_row["rejection_reason"], "physical_sample_id": grading_row["physical_sample_id"],
            "expected_category": expected,
            "expected_rationale": "Frozen rejection/uncertainty must prevent grade-specific price routing.",
            "measurement_status": "RECORDED_FROZEN_EVIDENCE",
        })
    return output


def _logic(
    scenario_id: str, decision: str, grade: str | None, expected: str, *,
    price_grade: str | None = None, reference: float | None = None, forecast: float | None = None,
    log_return: float | None = None, simple_return: float | None = None,
    lower: float | None = None, upper: float | None = None,
    comparison: str = "MIXED", reason: str = "synthetic deterministic branch test",
) -> dict:
    return {
        "scenario_id": scenario_id, "scenario_type": "LOGIC_TEST", "source_grading_id": "SYNTHETIC_LOGIC_ONLY",
        "source_price_id": "SYNTHETIC_LOGIC_ONLY", "grading_decision": decision, "grade": grade or "",
        "grading_confidence": 0.8 if grade else "", "detection_confidence": 0.8 if grade else "",
        "class_margin": 0.5 if grade else "",
        "quality_status": "FAILED" if decision == "POOR_IMAGE" else "PASSED" if grade else "NOT_APPLICABLE",
        "rejection_reason": "logic_test_reason" if not grade else "", "physical_sample_id": scenario_id,
        "price_grade": price_grade or "", "reference_date": "2026-01-01" if reference is not None else "",
        "reference_price": reference if reference is not None else "", "previous_reference_price": 95.0 if reference is not None else "",
        "latest_observed_return": 0.01 if reference is not None else "", "predicted_log_return": log_return if log_return is not None else "",
        "predicted_return": simple_return if simple_return is not None else "", "forecast_price": forecast if forecast is not None else "",
        "interval_lower": lower if lower is not None else "", "interval_upper": upper if upper is not None else "",
        "persistence_price": reference if reference is not None else "", "model_vs_persistence": comparison,
        "forecast_target_date": "2026-01-08" if forecast is not None else "", "source_url": "SYNTHETIC_LOGIC_ONLY",
        "evidence_partition": "LOGIC_TEST", "expected_category": expected, "expected_rationale": reason,
        "measurement_status": "SYNTHETIC_LOGIC_TEST_NOT_EMPIRICAL",
    }


def logic_scenarios() -> list[dict]:
    return [
        _logic("LOGIC-001", "NO_PEPPER", None, "REJECT", reason="non-pepper blocks market output"),
        _logic("LOGIC-002", "POOR_IMAGE", None, "REJECT", reason="quality rejection blocks market output"),
        _logic("LOGIC-003", "UNCERTAIN_GRADE", None, "UNCERTAIN_GRADE", reason="uncertain grade blocks routing"),
        _logic("LOGIC-004", "GRADE_1", "V3 Grade 1", "UPWARD_PRICE_OUTLOOK", price_grade="Grade 1", reference=100, forecast=110, log_return=.09531, simple_return=.10, lower=105, upper=115, comparison="RIDGE_BETTER"),
        _logic("LOGIC-005", "GRADE_1", "V3 Grade 1", "DOWNWARD_PRICE_OUTLOOK", price_grade="Grade 1", reference=100, forecast=90, log_return=-.10536, simple_return=-.10, lower=85, upper=95, comparison="RIDGE_BETTER"),
        _logic("LOGIC-006", "GRADE_2", "V3 Grade 2", "UPWARD_PRICE_OUTLOOK", price_grade="Grade 2", reference=100, forecast=110, log_return=.09531, simple_return=.10, lower=105, upper=115, comparison="RIDGE_BETTER"),
        _logic("LOGIC-007", "GRADE_2", "V3 Grade 2", "DOWNWARD_PRICE_OUTLOOK", price_grade="Grade 2", reference=100, forecast=90, log_return=-.10536, simple_return=-.10, lower=85, upper=95, comparison="RIDGE_BETTER"),
        _logic("LOGIC-008", "GRADE_1", "V3 Grade 1", "FLAT_PRICE_OUTLOOK", price_grade="Grade 1", reference=100, forecast=100.004, log_return=.00004, simple_return=.00004, lower=100, upper=100, comparison="TIE"),
        _logic("LOGIC-009", "CONFLICTING_SAMPLE_VIEWS", None, "CONFLICTING_SAMPLE_VIEWS", reason="conflicting accepted views block routing"),
        _logic("LOGIC-010", "GRADE_1", "V3 Grade 1", "PRICE_DATA_UNAVAILABLE", price_grade=None, reason="missing reference price fails closed"),
        _logic("LOGIC-011", "GRADE_1", "V3 Grade 1", "FORECAST_UNAVAILABLE", price_grade="Grade 1", reference=100, reason="missing forecast fails closed"),
        _logic("LOGIC-012", "GRADE_1", "V3 Grade 1", "HIGH_UNCERTAINTY_OUTLOOK", price_grade="Grade 1", reference=100, forecast=110, log_return=.09531, simple_return=.10, lower=80, upper=120, comparison="RIDGE_BETTER", reason="interval crosses reference price"),
        _logic("LOGIC-013", "GRADE_1", "V3 Grade 1", "UPWARD_PRICE_OUTLOOK", price_grade="Grade 1", reference=100, forecast=110, log_return=.09531, simple_return=.10, lower=105, upper=115, comparison="PERSISTENCE_BETTER", reason="direction remains visible but signal is limited"),
        _logic("LOGIC-014", "GRADE_1", "V3 Grade 1", "UPWARD_PRICE_OUTLOOK", price_grade="Grade 1", reference=100, forecast=110, log_return=.09531, simple_return=.10, lower=105, upper=115, comparison="RIDGE_BETTER", reason="relative support requires documented advantage and non-crossing interval"),
        _logic("LOGIC-015", "GRADE_1", "V3 Grade 1", "ERROR_GRADE_PRICE_MISMATCH", price_grade="Grade 2", reference=100, forecast=110, log_return=.09531, simple_return=.10, lower=105, upper=115, comparison="RIDGE_BETTER", reason="wrong-series routing must raise"),
    ]


def build() -> list[dict]:
    config = load_config()
    rows = empirical_scenarios(config) + logic_scenarios()
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == "__main__":
    print(f"wrote {len(build())} scenarios to {OUTPUT}")
