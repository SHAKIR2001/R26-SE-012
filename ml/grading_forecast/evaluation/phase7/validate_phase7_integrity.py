from __future__ import annotations

import json
from pathlib import Path

import onnx

from ml.grading_forecast.deployment.phase7.config import ROOT, load_config, repo_path, sha256
from ml.grading_forecast.deployment.phase7.integrated_service import analyze_image_bytes
from ml.grading_forecast.evaluation.phase7.verify_onnx_equivalence import verification_set

HERE = Path(__file__).parent
OUTPUT = HERE / "phase7_integrity.json"


def run() -> dict:
    config = load_config(); checks = []
    def check(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "detail": detail})
    frozen = {
        config["grading"]["source_pt"]: config["grading"]["source_pt_sha256"],
        config["grading"]["decision_config"]: config["grading"]["decision_config_sha256"],
        "data/processed/grading_forecast/price/eac_reconstructed_v1/eac_pepper_price_canonical.csv": "ea800ea576817f07ad54d50317dbd68254fc5dc824447380e58688b6b711c0f6",
        config["price_runtime"]["source"]: config["price_runtime"]["source_sha256"],
        "ml/grading_forecast/price_forecasting/phase5/outputs/phase5_integrity_validation.json": "085faac5e47a47780dc875effb8e313f5394fe27743bbb8ee277502facbb6d74",
        config["phase6"]["config"]: config["phase6"]["config_sha256"],
    }
    for relative, expected in frozen.items():
        actual = sha256(repo_path(relative)) if repo_path(relative).is_file() else "MISSING"
        check(f"frozen:{relative}", actual == expected, f"expected={expected}; actual={actual}")
    phase6_dir = repo_path("ml/grading_forecast/decision_support/phase6")
    for name, expected in config["phase6"]["authoritative_hashes"].items():
        check(f"phase6_authoritative:{name}", sha256(phase6_dir/name) == expected)
    model = repo_path(config["grading"]["onnx"]); manifest = json.loads((HERE/"phase7_model_manifest.json").read_text(encoding="utf-8"))
    check("onnx_hash_recorded", model.is_file() and sha256(model) == manifest["onnx_sha256"], manifest["onnx_sha256"])
    graph = onnx.load(model)
    check("onnx_graph_valid", not bool(onnx.checker.check_model(graph)))
    check("pt_not_replaced", sha256(repo_path(config["grading"]["source_pt"])) == config["grading"]["source_pt_sha256"])
    equivalence = json.loads((HERE/"onnx_equivalence.json").read_text(encoding="utf-8"))
    verification = json.loads((HERE/"phase7_verification_results.json").read_text(encoding="utf-8"))
    check("onnx_equivalence", equivalence["status"] == "PASS")
    check("routing_integrity", verification["checks"]["grade_routing"])
    check("rejection_first_integrity", verification["checks"]["rejection_uncertainty_blocking"])
    check("verification_reproducible", verification["checks"]["deterministic_repeat"])
    check("phase6_schema_preserved", verification["checks"]["phase6_schema_preserved"])
    check("tflite_not_falsely_claimed", config["mobile"]["tflite_attempted"] is False)
    check("backend_runtime_selected", config["mobile"]["selected_runtime"] == "BACKEND_ONNX_RUNTIME")
    check("price_runtime_is_frozen_records", config["price_runtime"]["strategy"] == "FROZEN_FORECAST_RECORD_SERVICE")
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in [
        repo_path("ml/grading_forecast/deployment/phase7/integrated_service.py"),
        repo_path("backend/app/api/routes/grading_forecast.py")])
    check("no_composite_or_trading_logic", "decision_score" not in text and "BUY NOW" not in text and "SELL NOW" not in text)
    payload = {"experiment_id": config["experiment"]["id"], "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
               "summary": {"passed": sum(c["status"] == "PASS" for c in checks), "failed": sum(c["status"] == "FAIL" for c in checks)},
               "checks": checks, "boundary": "Deployment equivalence and integration evidence only; no Phase 8 or new predictive claim."}
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = run(); print(json.dumps({"status": result["status"], "summary": result["summary"]}, indent=2)); raise SystemExit(0 if result["status"] == "PASS" else 1)
