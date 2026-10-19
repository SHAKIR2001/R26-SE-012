from __future__ import annotations

import json
from pathlib import Path

from ml.grading_forecast.deployment.phase7.config import load_config, repo_path
from ml.grading_forecast.deployment.phase7.integrated_service import analyze_image_bytes
from ml.grading_forecast.evaluation.phase7.verify_onnx_equivalence import verification_set

HERE = Path(__file__).parent


def run() -> dict:
    config = load_config()
    timestamp = config["experiment"]["deterministic_timestamp_utc"]
    outputs = []
    for row in verification_set():
        result = analyze_image_bytes(repo_path(row["source_path"]).read_bytes(), row["image_id"], timestamp_utc=timestamp)
        outputs.append({"image_id": row["image_id"], "role": row["decision"], "source_path": row["source_path"],
                        "grading_decision": result["grading"]["decision"], "grade": result["grading"]["grade"],
                        "market_status": result["market"]["status"], "price_grade": result["market"]["price_grade"],
                        "category": result["decision_support"]["category"], "result": result})
    second = [analyze_image_bytes(repo_path(row["source_path"]).read_bytes(), row["image_id"], timestamp_utc=timestamp) for row in verification_set()]
    expected = {"GRADE_1": "Grade 1", "GRADE_2": "Grade 2"}
    routing = all(not expected.get(item["grading_decision"]) or item["price_grade"] == expected[item["grading_decision"]] for item in outputs)
    blocked = all(item["market_status"] != "AVAILABLE" for item in outputs if item["grading_decision"] in {"NO_PEPPER","POOR_IMAGE","UNCERTAIN_GRADE"})
    payload = {"experiment_id": config["experiment"]["id"], "status": "PASS" if routing and blocked and [o["result"] for o in outputs] == second else "FAIL",
               "cases": outputs, "checks": {"grade_routing": routing, "rejection_uncertainty_blocking": blocked,
               "deterministic_repeat": [o["result"] for o in outputs] == second, "phase6_schema_preserved": all("trace" in o["result"] for o in outputs)}}
    (HERE/"phase7_verification_results.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (HERE/"mobile_response_fixture.json").write_text(json.dumps(outputs[0]["result"], indent=2, sort_keys=True), encoding="utf-8")
    matrix = {"selected_mobile_runtime": "BACKEND_ONNX_RUNTIME", "pytorch_backend": "REFERENCE_ONLY",
              "onnx_backend": "IMPLEMENTED_AND_VERIFIED", "onnx_runtime_mobile": "NOT_SELECTED",
              "tflite_v3": "NOT_PRODUCED_OR_CLAIMED", "backend_api": "IMPLEMENTED",
              "flutter_api_consumption": "IMPLEMENTED_STATICALLY_VERIFIED",
              "android_debug_build": "INCOMPLETE_STALLED_IN_GRADLE_AND_STOPPED",
              "device_or_emulator": "NOT_EXECUTED"}
    (HERE/"phase7_runtime_matrix.json").write_text(json.dumps(matrix, indent=2, sort_keys=True), encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = run(); print(json.dumps({"status": result["status"], "checks": result["checks"]}, indent=2)); raise SystemExit(0 if result["status"] == "PASS" else 1)
