"""Two-stage Phase 3 Follow-up evaluation with a sealed final holdout boundary."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from ml.grading_forecast.berry_grading.quality.phase3.decision_pipeline import FrozenThresholds, decide, quality_scores  # noqa: E402

OUTPUT = ROOT / "ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup"
CONFIG = ROOT / "ml/grading_forecast/berry_grading/quality/phase3_followup/experiment.yaml"
NEGATIVE_MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/phase3_followup_negative_manifest.csv"
V3_MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv"
ORIGINAL_NEGATIVE_MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv"
ORIGINAL_PHASE3_PREDICTIONS = ROOT / "ml/grading_forecast/berry_grading/evaluation/v3_phase3/negative_predictions.csv"
ORIGINAL_PHASE3_METRICS = ROOT / "ml/grading_forecast/berry_grading/evaluation/v3_phase3/phase3_metrics.json"
FOLLOWUP_MODEL = ROOT / "ml/grading_forecast/berry_grading/models/v3_phase3_followup/best.pt"
BASELINE_MODEL = ROOT / "ml/grading_forecast/berry_grading/models/v3_yolo/best.pt"
FREEZE = OUTPUT / "decision_config_frozen.json"
METRICS = OUTPUT / "phase3_followup_metrics.json"
REPORT = ROOT / "docs/research/V3_PHASE3_FOLLOWUP_REJECTION_RESULTS.md"
LOG = ROOT / "docs/research/EXPERIMENT_LOG.md"
ACCEPTED = {"GRADE_1", "GRADE_2"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if not rows:
        return
    fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def verify_row_file(row: dict, path_key: str, hash_key: str = "sha256") -> Path:
    path = ROOT / row[path_key]
    if not path.is_file() or sha256(path) != row[hash_key].lower():
        raise RuntimeError(f"Manifest/file integrity failure: {path}")
    return path


def predict(model: YOLO, rows: list[dict], path_key: str, kind: str, config: dict) -> list[dict]:
    sources = [str(ROOT / row[path_key]) for row in rows]
    started = time.perf_counter()
    results = model.predict(source=sources, imgsz=int(config["image_size"]), conf=0.001, iou=0.70,
                            device=str(config["device"]), batch=int(config["batch_size"]), verbose=False, stream=False)
    if len(results) != len(rows):
        raise RuntimeError("Prediction count mismatch")
    records = []
    for row, result, source in zip(rows, results, sources):
        best, class_conf = None, {0: 0.0, 1: 0.0}
        boxes = result.boxes
        if boxes is not None:
            for index in range(len(boxes)):
                cls, confidence = int(boxes.cls[index].item()), float(boxes.conf[index].item())
                if cls in class_conf:
                    class_conf[cls] = max(class_conf[cls], confidence)
                if best is None or confidence > best["confidence"]:
                    best = {"class": cls, "confidence": confidence, "box": [float(v) for v in boxes.xyxy[index].tolist()]}
        top_class = None if best is None else best["class"]
        top_conf = 0.0 if best is None else best["confidence"]
        other_conf = 0.0 if top_class is None else class_conf[1 - top_class]
        box = None if best is None else best["box"]
        height, width = result.orig_shape
        area = 0.0 if box is None else max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1]) / (width * height)
        records.append({
            "image_id": row.get("negative_id") or Path(source).name,
            "source_path": str(Path(source).relative_to(ROOT)).replace("\\", "/"), "kind": kind,
            "true_class": int(row["v3_class_id"]) if row.get("v3_class_id") not in (None, "") else None,
            "true_grade": row.get("v3_grade", ""), "physical_sample_id": row.get("physical_sample_id", ""),
            "category": row.get("category", ""), "source": row.get("source", ""),
            "split": row.get("split") or row.get("phase3_partition", ""),
            "raw_prediction": top_class, "top_confidence": top_conf, "runner_up_confidence": other_conf,
            "class_margin": top_conf - other_conf, "box_xyxy": box, "box_area_ratio": area,
            "quality": quality_scores(source), "inference_ms": float(result.speed.get("inference", 0.0)),
        })
    print(f"Predicted {len(records)} {kind} images in {time.perf_counter() - started:.1f}s")
    return records


def thresholds(config: dict, detection: float) -> FrozenThresholds:
    quality = config["quality_gate"]
    return FrozenThresholds(
        minimum_blur_variance=float(quality["minimum_blur_variance"]), minimum_brightness=float(quality["minimum_brightness"]),
        minimum_dimension=int(quality["minimum_dimension"]), minimum_box_area_ratio=float(quality["minimum_box_area_ratio"]),
        detection_confidence=float(detection), grade_confidence=0.05,
        grade_margin=float(config["threshold_selection"]["grade_margin"]),
    )


def apply(records: list[dict], selected: FrozenThresholds) -> list[dict]:
    return [{**record, **decide(record, selected)} for record in records]


def positive_metrics(records: list[dict]) -> dict:
    accepted = [r for r in records if r["decision"] in ACCEPTED]
    truth = [r["true_class"] for r in accepted]
    predictions = [0 if r["decision"] == "GRADE_1" else 1 for r in accepted]
    all_truth = [r["true_class"] for r in records]
    all_predictions = [0 if r["decision"] == "GRADE_1" else 1 if r["decision"] == "GRADE_2" else -1 for r in records]
    return {
        "images": len(records), "accepted": len(accepted), "coverage": len(accepted) / len(records),
        "false_rejections": len(records) - len(accepted), "false_rejection_rate": (len(records) - len(accepted)) / len(records),
        "accuracy": accuracy_score(all_truth, all_predictions),
        "balanced_accuracy": balanced_accuracy_score(all_truth, all_predictions),
        "macro_precision": precision_score(all_truth, all_predictions, labels=[0, 1], average="macro", zero_division=0),
        "macro_recall": recall_score(all_truth, all_predictions, labels=[0, 1], average="macro", zero_division=0),
        "macro_f1": f1_score(all_truth, all_predictions, labels=[0, 1], average="macro", zero_division=0),
        "weighted_f1": f1_score(all_truth, all_predictions, labels=[0, 1], average="weighted", zero_division=0),
        "g1_f1": f1_score(all_truth, all_predictions, labels=[0], average="macro", zero_division=0),
        "g2_f1": f1_score(all_truth, all_predictions, labels=[1], average="macro", zero_division=0),
        "accepted_accuracy": accuracy_score(truth, predictions) if accepted else 0.0,
        "accepted_macro_f1": f1_score(truth, predictions, labels=[0, 1], average="macro", zero_division=0) if accepted else 0.0,
        "accepted_confusion_matrix": confusion_matrix(truth, predictions, labels=[0, 1]).tolist() if accepted else [[0, 0], [0, 0]],
        "end_to_end_confusion_matrix": confusion_matrix(all_truth, all_predictions, labels=[0, 1, -1]).tolist(),
        "decision_counts": dict(Counter(r["decision"] for r in records)),
    }


def negative_metrics(records: list[dict]) -> dict:
    rejected = [r for r in records if r["decision"] not in ACCEPTED]
    by_category = {}
    for category in sorted({r["category"] for r in records}):
        subset = [r for r in records if r["category"] == category]
        count = sum(r["decision"] not in ACCEPTED for r in subset)
        by_category[category] = {"n": len(subset), "rejected": count, "accepted": len(subset) - count,
                                         "rejection_rate": count / len(subset), "false_acceptance_rate": (len(subset) - count) / len(subset)}
    # Binary convention: non-pepper is positive and REJECT is the positive prediction. This all-negative set has no true negatives.
    return {
        "images": len(records), "rejected": len(rejected), "accepted": len(records) - len(rejected),
        "rejection_rate": len(rejected) / len(records), "false_acceptance_rate": (len(records) - len(rejected)) / len(records),
        "binary_convention": "positive class = non-pepper; predicted positive = any rejection state",
        "precision": 1.0 if rejected else 0.0, "recall": len(rejected) / len(records),
        "f1": (2 * len(rejected) / (len(records) + len(rejected))) if rejected else 0.0,
        "balanced_accuracy": None, "balanced_accuracy_note": "undefined on an all-non-pepper-only holdout",
        "decision_counts": dict(Counter(r["decision"] for r in records)), "by_category": by_category,
    }


def validation_stage() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if FREEZE.exists() or METRICS.exists():
        raise RuntimeError("Refusing to overwrite an existing frozen/final evaluation")
    checkpoint_hash = sha256(FOLLOWUP_MODEL)
    positives = [r for r in load_csv(V3_MANIFEST) if r["research_partition"] == "VALIDATION"]
    negatives = [r for r in load_csv(NEGATIVE_MANIFEST) if r["split"] == "NEGATIVE_VALIDATION"]
    if len(positives) != 116 or not negatives:
        raise RuntimeError("Validation inputs do not match the controlled design")
    for row in positives:
        verify_row_file(row, "v3_image_path")
    for row in negatives:
        verify_row_file(row, "local_path")
    model = YOLO(str(FOLLOWUP_MODEL))
    positive_raw = predict(model, positives, "v3_image_path", "VALID_PEPPER_VALIDATION", config)
    negative_raw = predict(model, negatives, "local_path", "NEGATIVE_VALIDATION", config)
    scan = []
    for candidate in config["threshold_selection"]["candidates"]:
        selected = thresholds(config, candidate)
        positive = apply(positive_raw, selected)
        negative = apply(negative_raw, selected)
        pm, nm = positive_metrics(positive), negative_metrics(negative)
        scan.append({"threshold": candidate, "valid_accepted": pm["accepted"], "valid_coverage": pm["coverage"],
                     "valid_false_rejection_rate": pm["false_rejection_rate"], "accepted_accuracy": pm["accepted_accuracy"],
                     "accepted_macro_f1": pm["accepted_macro_f1"], "negative_rejected": nm["rejected"],
                     "negative_rejection_rate": nm["rejection_rate"], "negative_false_acceptance_rate": nm["false_acceptance_rate"]})
    eligible = [r for r in scan if r["valid_coverage"] >= float(config["threshold_selection"]["minimum_valid_pepper_coverage"])]
    if not eligible:
        raise RuntimeError("No threshold satisfies the predeclared valid-pepper coverage constraint")
    winner = max(eligible, key=lambda r: (r["negative_rejection_rate"], r["accepted_macro_f1"], r["valid_coverage"], -r["threshold"]))
    selected = thresholds(config, winner["threshold"])
    positive = apply(positive_raw, selected)
    negative = apply(negative_raw, selected)
    write_csv(OUTPUT / "validation_threshold_scan.csv", scan)
    write_csv(OUTPUT / "validation_positive_decisions.csv", positive)
    write_csv(OUTPUT / "validation_negative_decisions.csv", negative)
    freeze = {
        "status": "FROZEN_AFTER_VALIDATION_BEFORE_ANY_FINAL_HOLDOUT_ACCESS", "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "followup_checkpoint": str(FOLLOWUP_MODEL.relative_to(ROOT)).replace("\\", "/"), "followup_checkpoint_sha256": checkpoint_hash,
        "negative_manifest_sha256": sha256(NEGATIVE_MANIFEST), "selected_threshold": winner["threshold"],
        "thresholds": selected.__dict__, "selection_rule": config["threshold_selection"], "selected_validation_row": winner,
        "validation": {"valid_pepper": positive_metrics(positive), "negative": negative_metrics(negative)},
        "sealed_inputs_accessed": {"new_negative_final_holdout": False, "original_phase3_holdout": False, "phase2_positive_test": False},
    }
    write_json(FREEZE, freeze)
    print(json.dumps(freeze, indent=2))
    return 0


def combined_matrix(positives: list[dict], negatives: list[dict]) -> dict:
    rows = []
    for truth in (0, 1):
        subset = [r for r in positives if r["true_class"] == truth]
        rows.append([sum(r["decision"] == "GRADE_1" for r in subset), sum(r["decision"] == "GRADE_2" for r in subset), sum(r["decision"] not in ACCEPTED for r in subset)])
    rows.append([sum(r["decision"] == "GRADE_1" for r in negatives), sum(r["decision"] == "GRADE_2" for r in negatives), sum(r["decision"] not in ACCEPTED for r in negatives)])
    return {"rows": ["VALID_G1", "VALID_G2", "NON_PEPPER"], "columns": ["G1", "G2", "REJECT"], "values": rows}


def binary_gate_metrics(positives: list[dict], negatives: list[dict]) -> dict:
    truth = [0] * len(positives) + [1] * len(negatives)
    predictions = [int(r["decision"] not in ACCEPTED) for r in positives + negatives]
    return {
        "convention": "positive class = non-pepper; predicted positive = any rejection state",
        "precision": precision_score(truth, predictions, zero_division=0),
        "recall": recall_score(truth, predictions, zero_division=0),
        "f1": f1_score(truth, predictions, zero_division=0),
        "balanced_accuracy": balanced_accuracy_score(truth, predictions),
        "confusion_matrix": confusion_matrix(truth, predictions, labels=[0, 1]).tolist(),
    }


def plot_confusion(matrix: dict) -> None:
    values = np.array(matrix["values"])
    fig, ax = plt.subplots(figsize=(6, 5))
    image = ax.imshow(values, cmap="Greens")
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, str(values[i, j]), ha="center", va="center")
    ax.set_xticks(range(3), matrix["columns"]); ax.set_yticks(range(3), matrix["rows"])
    ax.set_xlabel("Prediction"); ax.set_ylabel("True type"); ax.set_title("Phase 3 Follow-up end-to-end outcomes")
    fig.colorbar(image, ax=ax); fig.tight_layout(); fig.savefig(OUTPUT / "confusion_matrix.png", dpi=160); plt.close(fig)


def plot_confidences(groups: dict[str, list[dict]]) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    bins = np.linspace(0, 1, 21)
    for label, records in groups.items():
        ax.hist([r["top_confidence"] for r in records], bins=bins, alpha=0.40, label=label)
    ax.set_xlabel("Detection confidence score"); ax.set_ylabel("Images"); ax.legend(); ax.set_title("Valid-pepper and non-pepper confidence distributions")
    fig.tight_layout(); fig.savefig(OUTPUT / "confidence_distribution.png", dpi=160); plt.close(fig)


def plot_comparison(baseline: dict, treatment: dict) -> None:
    labels = ["New holdout rejection", "Vegetation/crop rejection"]
    hard = {"vegetation_leaves", "agricultural_crops", "aerial_crop_imagery"}
    def hard_rate(metrics: dict) -> float:
        values = [v for k, v in metrics["by_category"].items() if k in hard]
        return sum(v["rejected"] for v in values) / sum(v["n"] for v in values)
    values = [[baseline["rejection_rate"], hard_rate(baseline)], [treatment["rejection_rate"], hard_rate(treatment)]]
    x = np.arange(2); width = 0.36
    fig, ax = plt.subplots(figsize=(8, 5)); ax.bar(x - width/2, values[0], width, label="Frozen Phase 2/3 control"); ax.bar(x + width/2, values[1], width, label="Hard-negative treatment")
    ax.set_xticks(x, labels); ax.set_ylim(0, 1); ax.set_ylabel("Rejection rate"); ax.legend(); fig.tight_layout(); fig.savefig(OUTPUT / "before_after_comparison.png", dpi=160); plt.close(fig)


def qualitative_figure(original: list[dict], new_negative: list[dict], positive: list[dict]) -> None:
    examples = []
    original_errors = [r for r in original if r["decision"] in ACCEPTED]
    new_rejections = [r for r in new_negative if r["decision"] not in ACCEPTED]
    new_errors = [r for r in new_negative if r["decision"] in ACCEPTED]
    positive_ok = [r for r in positive if r["decision"] in ACCEPTED and r["raw_prediction"] == r["true_class"]]
    positive_reject = [r for r in positive if r["decision"] not in ACCEPTED]
    for label, pool in (("Original false accept", original_errors), ("Unseen negative rejected", new_rejections), ("Remaining false accept", new_errors), ("Valid pepper accepted", positive_ok), ("Valid pepper rejected", positive_reject)):
        if pool:
            examples.append((label, max(pool, key=lambda r: r["top_confidence"])))
    if not examples:
        return
    fig, axes = plt.subplots(1, len(examples), figsize=(4 * len(examples), 4))
    axes = np.atleast_1d(axes)
    records = []
    for ax, (label, record) in zip(axes, examples):
        image = cv2.imdecode(np.fromfile(str(ROOT / record["source_path"]), dtype=np.uint8), cv2.IMREAD_COLOR)
        ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)); ax.axis("off"); ax.set_title(f"{label}\n{record['decision']} ({record['top_confidence']:.3f})")
        records.append({"role": label, "image_id": record["image_id"], "source_path": record["source_path"], "decision": record["decision"], "confidence": record["top_confidence"]})
    fig.tight_layout(); fig.savefig(OUTPUT / "representative_examples.png", dpi=150); plt.close(fig); write_json(OUTPUT / "representative_examples.json", records)


def final_stage() -> int:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    phase3_baseline = json.loads(ORIGINAL_PHASE3_METRICS.read_text(encoding="utf-8"))
    if METRICS.exists():
        raise RuntimeError("Refusing to overwrite completed final evaluation")
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    if frozen["status"] != "FROZEN_AFTER_VALIDATION_BEFORE_ANY_FINAL_HOLDOUT_ACCESS":
        raise RuntimeError("Threshold is not validly frozen")
    if sha256(FOLLOWUP_MODEL) != frozen["followup_checkpoint_sha256"] or sha256(NEGATIVE_MANIFEST) != frozen["negative_manifest_sha256"]:
        raise RuntimeError("Model or negative manifest changed after threshold freeze")
    selected = FrozenThresholds(**frozen["thresholds"])
    v3 = load_csv(V3_MANIFEST); negatives = load_csv(NEGATIVE_MANIFEST); original = load_csv(ORIGINAL_NEGATIVE_MANIFEST)
    original_baseline_predictions = [r for r in load_csv(ORIGINAL_PHASE3_PREDICTIONS) if r["negative_partition"] == "EVALUATION" and r["decision"] in ACCEPTED]
    for row in original_baseline_predictions:
        row["top_confidence"] = float(row["top_confidence"])
    test_rows = [r for r in v3 if r["research_partition"] == "TEST"]
    holdout_rows = [r for r in negatives if r["split"] == "NEGATIVE_FINAL_HOLDOUT"]
    original_rows = [r for r in original if r["phase3_partition"] == "EVALUATION"]
    for rows, key in ((test_rows, "v3_image_path"), (holdout_rows, "local_path"), (original_rows, "local_path")):
        for row in rows:
            verify_row_file(row, key)
    treatment_model, baseline_model = YOLO(str(FOLLOWUP_MODEL)), YOLO(str(BASELINE_MODEL))
    test = apply(predict(treatment_model, test_rows, "v3_image_path", "PHASE2_POSITIVE_TEST", config), selected)
    new_holdout = apply(predict(treatment_model, holdout_rows, "local_path", "NEW_NEGATIVE_FINAL_HOLDOUT", config), selected)
    original_holdout = apply(predict(treatment_model, original_rows, "local_path", "ORIGINAL_PHASE3_RETROSPECTIVE", config), selected)
    baseline_thresholds = thresholds(config, 0.55)
    baseline_new = apply(predict(baseline_model, holdout_rows, "local_path", "BASELINE_NEW_NEGATIVE_FINAL_HOLDOUT", config), baseline_thresholds)
    positive = positive_metrics(test); new_metrics = negative_metrics(new_holdout); original_metrics = negative_metrics(original_holdout); baseline_new_metrics = negative_metrics(baseline_new)
    matrix = combined_matrix(test, new_holdout)
    hard = {"vegetation_leaves", "agricultural_crops", "aerial_crop_imagery"}
    hard_values = [v for k, v in new_metrics["by_category"].items() if k in hard]
    vegetation = {"n": sum(v["n"] for v in hard_values), "rejected": sum(v["rejected"] for v in hard_values)}
    vegetation["accepted"] = vegetation["n"] - vegetation["rejected"]; vegetation["rejection_rate"] = vegetation["rejected"] / vegetation["n"]
    errors = []
    for r in new_holdout:
        if r["decision"] in ACCEPTED:
            errors.append({"error_type": "non_pepper_false_accept", "image_id": r["image_id"], "physical_sample_id": "", "true_grade": "NON_PEPPER", "category": r["category"], "source": r["source"], "model_confidence": r["top_confidence"], "predicted_grade": r["decision"], "detection_box": json.dumps(r["box_xyxy"]), "reason": "cause uncertain", "notes": "Final unseen holdout; not used for tuning"})
    for r in test:
        if r["decision"] not in ACCEPTED:
            errors.append({"error_type": "valid_pepper_false_rejection", "image_id": r["image_id"], "physical_sample_id": r["physical_sample_id"], "true_grade": r["true_grade"], "category": "", "source": "V3", "model_confidence": r["top_confidence"], "predicted_grade": r["decision"], "detection_box": json.dumps(r["box_xyxy"]), "reason": r["rejection_reason"], "notes": "Cause not visually assigned; cause uncertain"})
    write_csv(OUTPUT / "final_error_analysis.csv", errors)
    write_csv(OUTPUT / "final_new_negative_decisions.csv", new_holdout)
    write_csv(OUTPUT / "phase2_positive_test_decisions.csv", test)
    write_csv(OUTPUT / "original_phase3_retrospective_decisions.csv", original_holdout)
    category_rows = [{"category": category, **values} for category, values in new_metrics["by_category"].items()]
    write_csv(OUTPUT / "category_wise_negative_metrics.csv", category_rows)
    plot_confusion(matrix); plot_confidences({"Valid pepper (treatment)": test, "New negatives (control)": baseline_new, "New negatives (treatment)": new_holdout}); plot_comparison(baseline_new_metrics, new_metrics); qualitative_figure(original_baseline_predictions, new_holdout, test)
    improvement = new_metrics["rejection_rate"] - baseline_new_metrics["rejection_rate"]
    coverage_ok = positive["coverage"] >= 0.95
    grading_ok = positive["macro_f1"] >= 0.9378  # no more than 0.02 absolute below frozen Phase 2 macro F1
    hypothesis = "SUPPORTED" if improvement >= 0.10 and coverage_ok and grading_ok else "PARTIALLY SUPPORTED" if improvement > 0 and (coverage_ok or grading_ok) else "NOT SUPPORTED"
    decision = "COMPLETE — OPERATIONAL GATE IMPROVED" if hypothesis == "SUPPORTED" else "COMPLETE — OPERATIONAL GATE NOT SUFFICIENT"
    metrics = {
        "phase": "3_followup", "status": "COMPLETE", "baseline_model": str(BASELINE_MODEL.relative_to(ROOT)).replace("\\", "/"),
        "followup_model": str(FOLLOWUP_MODEL.relative_to(ROOT)).replace("\\", "/"), "selected_threshold": selected.detection_confidence,
        "validation": frozen["validation"], "new_negative_holdout": new_metrics,
        "new_negative_holdout_control": baseline_new_metrics, "original_phase3_holdout": original_metrics,
        "phase2_positive_test_regression": positive, "end_to_end": {"matrix": matrix, "vegetation_crop": vegetation,
                                                                       "binary_gate_metrics": binary_gate_metrics(test, new_holdout)},
        "comparison": {"new_holdout_rejection_change": improvement, "frozen_phase3_baseline_rejection": 0.875, "original_phase3_followup_rejection": original_metrics["rejection_rate"],
                       "phase2_accuracy_baseline": 0.9583, "phase2_macro_f1_baseline": 0.9578,
                       "frozen_phase3_validation_baseline": phase3_baseline["consolidated"]["valid_pepper"]},
        "hypothesis": hypothesis, "decision": decision,
        "integrity": {"model_and_threshold_frozen_before_holdout": True, "no_post_final_tuning": True,
                      "base_checkpoint_sha256": sha256(BASELINE_MODEL), "followup_checkpoint_sha256": sha256(FOLLOWUP_MODEL)},
    }
    write_json(METRICS, metrics); write_report(metrics); append_log(metrics)
    print(json.dumps(metrics, indent=2))
    return 0


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def write_report(m: dict) -> None:
    dataset = json.loads((ROOT / "data/processed/grading_forecast/berry_v3/phase3_followup_negative_dataset_summary.json").read_text(encoding="utf-8"))
    training = json.loads((ROOT / "ml/grading_forecast/berry_grading/models/v3_phase3_followup/experiment_metadata.json").read_text(encoding="utf-8"))
    val, new, pos, original = m["validation"], m["new_negative_holdout"], m["phase2_positive_test_regression"], m["original_phase3_holdout"]
    baseline_val = m["comparison"]["frozen_phase3_validation_baseline"]
    hard_categories = {"vegetation_leaves", "agricultural_crops", "aerial_crop_imagery"}
    baseline_hard = [v for k, v in m["new_negative_holdout_control"]["by_category"].items() if k in hard_categories]
    baseline_hard_rate = sum(v["rejected"] for v in baseline_hard) / sum(v["n"] for v in baseline_hard)
    treatment_hard_rate = m["end_to_end"]["vegetation_crop"]["rejection_rate"]
    category_table = "\n".join(f"| {k} | {v['n']} | {v['rejected']} | {v['accepted']} | {pct(v['rejection_rate'])} |" for k, v in new["by_category"].items())
    report = f"""# V3 Phase 3 Follow-up — Non-Pepper Rejection Results

## 1. Objective

Determine whether controlled YOLO11n hard-negative fine-tuning reduces non-pepper vegetation/crop false acceptance without unacceptable loss of genuine-pepper coverage or G1/G2 grading performance. This is a research experiment, not production or field validation.

## 2. Phase 3 baseline

The frozen Phase 3 result was 35/40 (87.5%) held-out non-pepper rejection, 5/40 (12.5%) false acceptance, and all five false accepts were vegetation/crop images. Valid-pepper validation coverage was 111/116 (95.69%) with five false rejections.

## 3. Research hypothesis

Adding diverse, source-controlled non-pepper images as empty-label YOLO hard negatives will reduce vegetation/crop false acceptance without unacceptable valid-pepper or grading regression. Final result: **{m['hypothesis']}**.

## 4. Dataset construction

Open-license results were collected through the Wikimedia Commons API, with Openverse available as a documented fallback, using resumable per-file caching. Actual source counts are `{json.dumps(dataset['source_counts'], sort_keys=True)}`. The manifest records creator, license, source page, media URL, timestamp, dimensions, and SHA-256. Exact SHA-256 deduplication excluded overlap with all 775 V3 images and the frozen 80-image Phase 3 set. Creator/source groups were kept in one partition. Collected {dataset['total_usable']} usable images; split counts: `{json.dumps(dataset['split_counts'], sort_keys=True)}`. The final holdout remained sealed until model and threshold freeze.

## 5. Training method

One-shot hard-negative fine-tuning initialized from the frozen Phase 2 checkpoint. Only 539 Phase 1 TRAIN positives and {training['counts']['negative_train']} empty-label negatives were used. Validation contained 116 Phase 1 VALIDATION positives and {training['counts']['negative_validation']} negatives. YOLO11n, 640 px, batch 4, seed 42, AdamW, LR 0.0001, weight decay 0.0005, maximum 30 epochs, patience 8. Duration: {training['training']['duration_seconds']:.1f} seconds.

## 6. Threshold selection

The complete validation-only scan is in `validation_threshold_scan.csv`. Candidates were 0.05–0.90 in 0.05 increments. Thresholds below 95% valid-pepper coverage were excluded; the remaining point with maximum negative rejection, then accepted-pepper macro F1, then coverage, then lowest threshold was selected: **{m['selected_threshold']:.2f}**. The Phase 3 quality thresholds and 0.30 class-margin rule were preserved.

## 7. Validation results

- Valid coverage: {val['valid_pepper']['accepted']}/{val['valid_pepper']['images']} ({pct(val['valid_pepper']['coverage'])})
- Valid false rejection: {val['valid_pepper']['false_rejections']}/{val['valid_pepper']['images']} ({pct(val['valid_pepper']['false_rejection_rate'])})
- Accepted-subset accuracy/macro F1: {pct(val['valid_pepper']['accepted_accuracy'])} / {val['valid_pepper']['accepted_macro_f1']:.4f}
- Negative rejection: {val['negative']['rejected']}/{val['negative']['images']} ({pct(val['negative']['rejection_rate'])})

On the same 116 validation images, the frozen Phase 3 baseline had {pct(m['comparison']['frozen_phase3_validation_baseline']['coverage'])} coverage, {pct(m['comparison']['frozen_phase3_validation_baseline']['false_rejection_rate'])} false rejection, {pct(m['comparison']['frozen_phase3_validation_baseline']['accepted_accuracy'])} accepted accuracy, and {m['comparison']['frozen_phase3_validation_baseline']['accepted_macro_f1']:.4f} accepted macro F1.

## 8. Final unseen negative results

The holdout was evaluated once after freezing. Rejected {new['rejected']}/{new['images']} ({pct(new['rejection_rate'])}); false accepted {new['accepted']}/{new['images']} ({pct(new['false_acceptance_rate'])}). Binary precision={new['precision']:.4f}, recall={new['recall']:.4f}, F1={new['f1']:.4f}; balanced accuracy is undefined because this holdout contains only the non-pepper class.

| Category | N | Rejected | Accepted | Rejection rate |
|---|---:|---:|---:|---:|
{category_table}

## 9. Genuine pepper regression

On the once-accessed Phase 2 positive TEST: coverage {pct(pos['coverage'])}, false rejection {pct(pos['false_rejection_rate'])}, accuracy {pos['accuracy']:.4f}, balanced accuracy {pos['balanced_accuracy']:.4f}, macro precision {pos['macro_precision']:.4f}, macro recall {pos['macro_recall']:.4f}, macro F1 {pos['macro_f1']:.4f}, weighted F1 {pos['weighted_f1']:.4f}, G1 F1 {pos['g1_f1']:.4f}, G2 F1 {pos['g2_f1']:.4f}.

## 10. Original Phase 3 comparison

Frozen baseline: 87.5% rejection. Frozen follow-up model, retrospectively evaluated after all selection: {pct(original['rejection_rate'])} rejection. This retrospective set is not an independent test set for the adapted model and did not trigger tuning.

## 11. Phase 2 grading regression

Frozen Phase 2: accuracy 0.9583, macro F1 0.9578, G1 F1 0.9624, G2 F1 0.9533. Follow-up: accuracy {pos['accuracy']:.4f}, macro F1 {pos['macro_f1']:.4f}, G1 F1 {pos['g1_f1']:.4f}, G2 F1 {pos['g2_f1']:.4f}. Rejections: {pos['false_rejections']}.

## 12. Error analysis

Every new-holdout false accept and Phase 2 TEST false rejection is listed in `final_error_analysis.csv`. Causes are marked uncertain unless directly supported; no causal explanation was invented. Representative successes and failures are shown in `representative_examples.png`.

## 13. Hard-negative effectiveness

On the same new unseen holdout, the frozen control rejected {pct(m['new_negative_holdout_control']['rejection_rate'])}; the treatment rejected {pct(new['rejection_rate'])}, a {m['comparison']['new_holdout_rejection_change'] * 100:+.2f} percentage-point change. Vegetation/crop/aerial results are separately preserved in the metrics JSON. The hypothesis is **{m['hypothesis']}**.

| Metric | Frozen control | Follow-up | Change |
|---|---:|---:|---:|
| Validation valid-pepper coverage (same 116 images) | {pct(baseline_val['coverage'])} | {pct(val['valid_pepper']['coverage'])} | {(val['valid_pepper']['coverage'] - baseline_val['coverage']) * 100:+.2f} pp |
| Validation false rejection (same 116 images) | {pct(baseline_val['false_rejection_rate'])} | {pct(val['valid_pepper']['false_rejection_rate'])} | {(val['valid_pepper']['false_rejection_rate'] - baseline_val['false_rejection_rate']) * 100:+.2f} pp |
| Validation accepted accuracy | {pct(baseline_val['accepted_accuracy'])} | {pct(val['valid_pepper']['accepted_accuracy'])} | {(val['valid_pepper']['accepted_accuracy'] - baseline_val['accepted_accuracy']) * 100:+.2f} pp |
| Validation accepted macro F1 | {baseline_val['accepted_macro_f1']:.4f} | {val['valid_pepper']['accepted_macro_f1']:.4f} | {val['valid_pepper']['accepted_macro_f1'] - baseline_val['accepted_macro_f1']:+.4f} |
| New unseen negative rejection (same 49 images) | {pct(m['new_negative_holdout_control']['rejection_rate'])} | {pct(new['rejection_rate'])} | {m['comparison']['new_holdout_rejection_change'] * 100:+.2f} pp |
| New unseen vegetation/crop/aerial rejection | {pct(baseline_hard_rate)} | {pct(treatment_hard_rate)} | {(treatment_hard_rate - baseline_hard_rate) * 100:+.2f} pp |
| Original Phase 3 negative rejection (same 40 images) | 87.50% | {pct(original['rejection_rate'])} | {(original['rejection_rate'] - 0.875) * 100:+.2f} pp |

The predeclared interpretation implemented before final access requires at least a 10 percentage-point same-holdout rejection improvement, at least 95% Phase 2 TEST coverage, and no more than 0.02 absolute macro-F1 loss for `SUPPORTED`. A positive improvement meeting only part of the safety/grading constraints is `PARTIALLY SUPPORTED`; otherwise it is `NOT SUPPORTED`.

## 14. Limitations

Internet imagery does not represent field deployment; categories and creator groups remain finite; semantic near-duplicate detection was not claimed; camera/domain shift and confidence calibration were not solved; confidence values are model confidence scores, not probabilities; and the unseen holdout is modest. Collection froze at 250 usable images, below the nominal 300-image target, after repeated Wikimedia transfer failures dominated progress; the resumable manifest records 199 failed attempts and four rejected downloads. The original five Phase 3 false accepts were not used for training.

## 15. Decision

**{m['decision']}**

This result does not establish production readiness or camera-independent field robustness. Do not proceed to Phase 6 automatically.
"""
    REPORT.write_text(report, encoding="utf-8")


def append_log(m: dict) -> None:
    marker = "### BERRY-V3-YOLO11N-PHASE3-FOLLOWUP-001"
    existing = LOG.read_text(encoding="utf-8")
    if marker in existing:
        raise RuntimeError("Experiment log already contains the follow-up entry")
    val, new, pos = m["validation"], m["new_negative_holdout"], m["phase2_positive_test_regression"]
    entry = f"""

## Phase 3 Follow-up — Controlled Hard-Negative Training

{marker}

Date: 2026-10-07.

- Objective: reduce vegetation/crop false acceptance without unacceptable genuine-pepper or G1/G2 regression.
- Hypothesis: controlled empty-label hard negatives improve the operational rejection gate.
- Dataset: licensed/provenanced Wikimedia negatives, SHA-256 deduplicated, creator-group-aware 60/20/20 split; frozen V3 TRAIN/VALIDATION/TEST preserved.
- Model: frozen Phase 2 YOLO11n checkpoint plus one-shot hard-negative fine-tuning; architecture unchanged.
- Training configuration: 640 px, batch 4, AdamW, LR 0.0001, seed 42, deterministic, maximum 30 epochs/patience 8.
- Threshold rule: validation-only grid; require at least 95% valid coverage, maximize negative rejection, then accepted macro F1, then coverage, then lowest threshold. Selected {m['selected_threshold']:.2f}.
- Validation: valid coverage {pct(val['valid_pepper']['coverage'])}; negative rejection {pct(val['negative']['rejection_rate'])}.
- Final new holdout: {new['rejected']}/{new['images']} rejected ({pct(new['rejection_rate'])}); {new['accepted']} false accepts.
- Phase 2 TEST regression: accuracy {pos['accuracy']:.4f}; macro F1 {pos['macro_f1']:.4f}; G1/G2 F1 {pos['g1_f1']:.4f}/{pos['g2_f1']:.4f}; {pos['false_rejections']} rejections.
- Decision: `{m['decision']}`; hypothesis `{m['hypothesis']}`.
- Limitations: internet-domain negatives, finite unseen holdout, unresolved field/camera shift, no confidence calibration, exact-hash but not semantic deduplication.
- Next phase: stop for researcher review; do not proceed to Phase 6 automatically.
"""
    LOG.write_text(existing + entry, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=["validation", "final"])
    args = parser.parse_args()
    return validation_stage() if args.stage == "validation" else final_stage()


if __name__ == "__main__":
    raise SystemExit(main())
