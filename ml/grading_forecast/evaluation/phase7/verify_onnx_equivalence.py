"""Compare frozen PyTorch and NMS-embedded ONNX inference on fixed evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from ml.grading_forecast.berry_grading.quality.phase3.decision_pipeline import decide
from ml.grading_forecast.deployment.phase7.config import ROOT, load_config, repo_path
from ml.grading_forecast.deployment.phase7.grading_runtime import _thresholds, infer_raw

OUTPUT = Path(__file__).with_name("onnx_equivalence.json")
REPORT = Path(__file__).with_name("onnx_equivalence_report.md")


def _rows(relative: str) -> list[dict]:
    with repo_path(relative).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def verification_set() -> list[dict]:
    positives = _rows("ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup/phase2_positive_test_decisions.csv")
    negatives = _rows("ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup/final_new_negative_decisions.csv")
    selected = [next(row for row in positives if row["decision"] == "GRADE_1"),
                next(row for row in positives if row["decision"] == "GRADE_2"),
                next(row for row in negatives if row["decision"] == "NO_PEPPER"),
                next(row for row in negatives if row["decision"] == "POOR_IMAGE"),
                next(row for row in positives if row["decision"] == "UNCERTAIN_GRADE")]
    return selected


def _pt_raw(result) -> dict:
    boxes = result.boxes
    class_conf, best = {0: 0.0, 1: 0.0}, None
    if boxes is not None:
        for index in range(len(boxes)):
            cls, confidence = int(boxes.cls[index].item()), float(boxes.conf[index].item())
            if cls not in class_conf:
                continue
            class_conf[cls] = max(class_conf[cls], confidence)
            if best is None or confidence > best["confidence"]:
                best = {"class": cls, "confidence": confidence, "box": [float(v) for v in boxes.xyxy[index].tolist()]}
    top_class = None if best is None else best["class"]
    top_conf = 0.0 if best is None else best["confidence"]
    box = None if best is None else best["box"]
    height, width = result.orig_shape
    area = 0.0 if box is None else max(0, box[2]-box[0])*max(0, box[3]-box[1])/(width*height)
    return {"raw_prediction": top_class, "top_confidence": top_conf,
            "runner_up_confidence": 0.0 if top_class is None else class_conf[1-top_class],
            "class_margin": top_conf-(0.0 if top_class is None else class_conf[1-top_class]),
            "box_xyxy": box, "box_area_ratio": area}


def run() -> dict:
    from ultralytics import YOLO

    config, selected = load_config(), verification_set()
    settings, tolerances = config["grading"], config["equivalence"]
    paths = [repo_path(row["source_path"]) for row in selected]
    model = YOLO(str(repo_path(settings["source_pt"])))
    pt_results = model.predict(source=[str(path) for path in paths], imgsz=settings["image_size"], conf=settings["export_confidence_floor"],
                               iou=settings["export_iou_threshold"], max_det=settings["maximum_detections"], device="cpu", verbose=False)
    cases = []
    for row, path, pt_result in zip(selected, paths, pt_results):
        pt, ort = _pt_raw(pt_result), infer_raw(path.read_bytes())
        pt["quality"], ort_quality = ort["quality"], ort["quality"]
        pt_decision, ort_decision = decide(pt, _thresholds()), decide(ort, _thresholds())
        confidence_delta = abs(pt["top_confidence"]-ort["top_confidence"])
        bbox_delta = None if pt["box_xyxy"] is None and ort["box_xyxy"] is None else max(
            abs(a-b) for a, b in zip(pt["box_xyxy"] or [0]*4, ort["box_xyxy"] or [0]*4))
        class_agreement = pt["raw_prediction"] == ort["raw_prediction"]
        confidence_pass = confidence_delta <= float(tolerances["confidence_absolute_tolerance"])
        bbox_pass = bbox_delta is None or bbox_delta <= float(tolerances["bounding_box_absolute_tolerance_pixels"])
        decision_agreement = pt_decision["decision"] == ort_decision["decision"]
        cases.append({"image_id": row["image_id"], "source_path": row["source_path"], "reference_role": row["decision"],
            "pytorch_class": pt["raw_prediction"], "onnx_class": ort["raw_prediction"], "class_agreement": class_agreement,
            "pytorch_confidence": pt["top_confidence"], "onnx_confidence": ort["top_confidence"],
            "confidence_absolute_difference": confidence_delta, "confidence_tolerance_pass": confidence_pass,
            "bbox_max_absolute_difference_pixels": bbox_delta, "bbox_tolerance_pass": bbox_pass,
            "pytorch_decision": pt_decision["decision"], "onnx_decision": ort_decision["decision"],
            "decision_agreement": decision_agreement, "rejection_agreement": (pt_decision["decision"] in {"NO_PEPPER","POOR_IMAGE"}) == (ort_decision["decision"] in {"NO_PEPPER","POOR_IMAGE"}),
            "passed": class_agreement and confidence_pass and bbox_pass and decision_agreement})
    payload = {"experiment_id": config["experiment"]["id"], "status": "PASS" if all(c["passed"] for c in cases) else "FAIL",
        "tolerances_predeclared": tolerances, "model_load": "PASS", "cases": cases,
        "summary": {"cases": len(cases), "passed": sum(c["passed"] for c in cases),
                    "decision_agreement": sum(c["decision_agreement"] for c in cases),
                    "rejection_agreement": sum(c["rejection_agreement"] for c in cases)}}
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = ["# Phase 7 ONNX Equivalence", "", f"**Status:** {payload['status']}", "",
             f"Fixed cases: {len(cases)}; passed: {payload['summary']['passed']}; decision agreement: {payload['summary']['decision_agreement']}/{len(cases)}.", "",
             "Tolerances were fixed before evaluation: confidence absolute difference <= 0.0001 and bounding-box coordinate difference <= 1.0 original-image pixel.", "",
             "This verifies runtime equivalence on a small controlled set; it is not new predictive or field evidence."]
    REPORT.write_text("\n".join(lines)+"\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = run()
    print(json.dumps(result["summary"] | {"status": result["status"]}, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
