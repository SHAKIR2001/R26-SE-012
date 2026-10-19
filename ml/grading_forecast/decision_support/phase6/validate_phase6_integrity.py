"""Integrity and reproducibility validation for Phase 6 grade-price fusion."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

from .config import CONFIG_PATH, ROOT, load_config, repo_path
from .evaluate_phase6 import METRICS, SCENARIOS, TRACES, evaluate_rows


OUTPUT = Path(__file__).with_name("phase6_integrity.json")
FROZEN = {
    "ml/grading_forecast/berry_grading/models/v3_yolo/best.pt": "c35cc40515adcb6130a4bc93e8ad3de161dcf46b263a9d7df8286a5b4239a9c4",
    "ml/grading_forecast/berry_grading/models/v3_phase3_followup/best.pt": "e825278e0cf8eaff64cd05a2941cf96794e573027823a0ccd308bbc3f1a418ca",
    "ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup/decision_config_frozen.json": "39ca99a7e0049fb620a141cde80d539700945b2f812cc6cf7b15f289f8e158b8",
    "data/processed/grading_forecast/price/eac_reconstructed_v1/eac_pepper_price_canonical.csv": "ea800ea576817f07ad54d50317dbd68254fc5dc824447380e58688b6b711c0f6",
    "ml/grading_forecast/price_forecasting/phase5/phase5_config.yaml": "039b6eb3b7e394ba16a69cd72ad3e847b451741624f9324b4701ff19ec081046",
    "ml/grading_forecast/price_forecasting/phase5/models/selected_model_spec.json": "e98277d6ced450d47ee67e987217a45a1b2a717b0f467c3ac70b1607677e14f9",
    "ml/grading_forecast/price_forecasting/phase5/outputs/walk_forward_predictions.csv": "d06f8c195a475e30eb78b5aeede55658dcfaaa0f5d09fecfda6de0f435b19e93",
    "ml/grading_forecast/price_forecasting/phase5/outputs/external_reality_check_selected.csv": "0b3e5a4ede8f6839f831f008a4655114413c6369a1b9549dca240cc685288c4a",
    "ml/grading_forecast/price_forecasting/phase5/outputs/phase5_forecasting_metrics.json": "aa25b60f75d3b5bdfbfcdf37f126d3d826e77818241a68f16d00ed6292ed5e2c",
    "ml/grading_forecast/price_forecasting/phase5/outputs/phase5_integrity_validation.json": "085faac5e47a47780dc875effb8e313f5394fe27743bbb8ee277502facbb6d74",
    "ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup/phase2_positive_test_decisions.csv": "349e981d862952e39c034a2ed083b7a67627acc056de82f9b71d1f0c120c80de",
    "ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup/final_new_negative_decisions.csv": "c04097e17b053366c602b78410b01fb682cd45f993c3e8303b938a9f57ca6455",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name: str, passed: bool, detail: str = "") -> dict:
    return {"check": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    config = load_config()
    checks = []
    frozen_hashes = {}
    for relative, expected in FROZEN.items():
        path = repo_path(relative)
        actual = sha256(path) if path.is_file() else None
        frozen_hashes[relative] = {"expected": expected, "actual": actual}
        checks.append(check(f"frozen:{relative}", actual == expected, f"expected={expected}; actual={actual}"))

    scenarios = read_csv(SCENARIOS)
    traces = read_csv(TRACES)
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    first_outputs, first_traces = evaluate_rows(scenarios, config)
    second_outputs, second_traces = evaluate_rows(scenarios, config)
    empirical = [row for row in scenarios if row["scenario_type"] == "EMPIRICAL_COMPOSITIONAL"]
    logic = [row for row in scenarios if row["scenario_type"] == "LOGIC_TEST"]

    routing = config["grade_routing"]
    checks.extend([
        check("phase6_config_exists", CONFIG_PATH.is_file(), str(CONFIG_PATH.relative_to(ROOT))),
        check("grade_routing_one_to_one", routing == {"V3 Grade 1": {"price_grade": "Grade 1", "model_scope": "separate_grade_1_ridge"}, "V3 Grade 2": {"price_grade": "Grade 2", "model_scope": "separate_grade_2_ridge"}}, json.dumps(routing, sort_keys=True)),
        check("direction_rule_matches_phase5", config["direction_rule"]["price_resolution_lkr"] == 0.01 and config["direction_rule"]["near_flat_band"] is None, config["direction_rule"]["method"]),
        check("no_synthetic_empirical_values", all(row["measurement_status"] == "RECORDED_FROZEN_EVIDENCE" for row in empirical), f"empirical={len(empirical)}"),
        check("logic_values_explicitly_synthetic", all(row["measurement_status"] == "SYNTHETIC_LOGIC_TEST_NOT_EMPIRICAL" for row in logic), f"logic={len(logic)}"),
        check("all_scenario_expectations_pass", all(row["check_passed"] == "True" for row in scenarios), f"passed={sum(row['check_passed'] == 'True' for row in scenarios)}/{len(scenarios)}"),
        check("rejected_inputs_have_no_price", all(not row["price_grade"] for row in scenarios if row["grading_decision"] in {"NO_PEPPER", "POOR_IMAGE"})),
        check("uncertain_inputs_have_no_price", all(not row["price_grade"] for row in scenarios if row["grading_decision"] in {"UNCERTAIN_GRADE", "CONFLICTING_SAMPLE_VIEWS"})),
        check("grade1_never_routes_grade2", all(row["price_grade"] in {"", "Grade 1"} for row in scenarios if row["grade"] == "V3 Grade 1" and row["scenario_id"] != "LOGIC-015")),
        check("grade2_never_routes_grade1", all(row["price_grade"] in {"", "Grade 2"} for row in scenarios if row["grade"] == "V3 Grade 2")),
        check("invalid_route_fails_closed", next(row for row in scenarios if row["scenario_id"] == "LOGIC-015")["actual_category"] == "ERROR_GRADE_PRICE_MISMATCH"),
        check("missing_price_fails_closed", next(row for row in scenarios if row["scenario_id"] == "LOGIC-010")["actual_category"] == "PRICE_DATA_UNAVAILABLE"),
        check("missing_forecast_fails_closed", next(row for row in scenarios if row["scenario_id"] == "LOGIC-011")["actual_category"] == "FORECAST_UNAVAILABLE"),
        check("decision_traces_complete", len(traces) == len(scenarios) and all(row["grading_model_sha256"] and row["decision_config_sha256"] and row["final_decision_support_category"] and row["explanation"] for row in traces), f"traces={len(traces)}"),
        check("in_memory_reproducibility", first_outputs == second_outputs and first_traces == second_traces),
        check("recorded_reproducibility", metrics["reproducibility"]["two_in_memory_runs_identical"] is True and metrics["reproducibility"]["scenario_csv_sha256"] == sha256(SCENARIOS) and metrics["reproducibility"]["trace_csv_sha256"] == sha256(TRACES)),
    ])

    canonical = read_csv(repo_path(config["frozen_price"]["canonical_dataset_path"]))
    checks.extend([
        check("no_synthetic_grade2_price", all(row["observation_status"] == "observed_source_value" for row in canonical if row["grade"] == "Grade 2")),
        check("no_interpolation_or_fixed_discount", "interpol" not in CONFIG_PATH.read_text(encoding="utf-8").lower() and "discount" not in CONFIG_PATH.read_text(encoding="utf-8").lower()),
        check("no_hidden_composite_weight", all(token not in (Path(__file__).with_name(name).read_text(encoding="utf-8")) for name in ("decision_engine.py", "decision_rules.py") for token in ("0.6 *", "0.4 *", "decision_score"))),
        check("phase5_metrics_preserved_not_improved", metrics["forecast_evidence_preserved"]["phase5_verdict"] == "MIXED" and metrics["forecast_evidence_preserved"]["phase6_improvement_claim"] is False),
    ])

    status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, text=True, capture_output=True, check=True)
    changed = [line[3:].replace("\\", "/") for line in status.stdout.splitlines() if len(line) >= 4]
    allowed = ("ml/grading_forecast/decision_support/phase6/", "docs/research/PHASE6_", "docs/research/EXPERIMENT_LOG.md")
    unexpected = [path for path in changed if not path.startswith(allowed)]
    checks.append(check("historical_artifacts_not_overwritten", not unexpected, f"unexpected_changes={unexpected}"))

    passed = all(item["status"] == "PASS" for item in checks)
    payload = {
        "experiment_id": config["experiment"]["id"], "status": "PASS" if passed else "FAIL",
        "frozen_artifact_hashes": frozen_hashes,
        "phase6_artifacts": {
            "config_sha256": sha256(CONFIG_PATH), "scenarios_sha256": sha256(SCENARIOS),
            "traces_sha256": sha256(TRACES), "metrics_sha256": sha256(METRICS),
        },
        "checks": checks,
        "summary": {"passed": sum(item["status"] == "PASS" for item in checks), "failed": sum(item["status"] == "FAIL" for item in checks)},
        "git_changed_paths": changed,
        "reproducibility": "PASS" if first_outputs == second_outputs and first_traces == second_traces else "FAIL",
        "boundary": "No training, model conversion, backend/mobile modification, deployment, or field validation was performed.",
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "summary": payload["summary"], "reproducibility": payload["reproducibility"]}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
