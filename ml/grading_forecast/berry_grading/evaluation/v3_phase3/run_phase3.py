"""Run Phase 3 with the frozen Phase 2 checkpoint and no sealed-test access."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np
import torch
import yaml
from PIL import Image, ImageDraw, ImageFont
from sklearn.metrics import confusion_matrix, f1_score
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "ml/grading_forecast/berry_grading/quality/phase3"))
from decision_pipeline import FrozenThresholds, decide, quality_scores, read_image  # noqa: E402

CONFIG_PATH = Path(__file__).with_name("phase3_config.yaml")
MODEL_PATH = ROOT / "ml/grading_forecast/berry_grading/models/v3_yolo/best.pt"
MANIFEST_PATH = ROOT / "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv"
NEGATIVE_PATH = ROOT / "data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv"
OUTPUT = Path(__file__).parent
CHALLENGE_ROOT = ROOT / "data/processed/grading_forecast/berry_v3/phase3_quality_challenges"
GRADE_NAME = {0: "V3 Grade 1", 1: "V3 Grade 2"}
FINAL_STATES = ["GRADE_1", "GRADE_2", "POOR_IMAGE", "NO_PEPPER", "UNCERTAIN_GRADE"]


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_inputs() -> tuple[dict, list[dict], list[dict]]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    rows = [r for r in load_csv(MANIFEST_PATH) if r["research_partition"] == "VALIDATION"]
    negatives = load_csv(NEGATIVE_PATH)
    if len(rows) != 116 or Counter(r["v3_class_id"] for r in rows) != Counter({"0": 68, "1": 48}):
        raise RuntimeError("Validation manifest no longer matches the frozen 116-image split")
    if len(negatives) != 80 or Counter(r["phase3_partition"] for r in negatives) != Counter({"CALIBRATION": 40, "EVALUATION": 40}):
        raise RuntimeError("External negative manifest must contain fixed 40/40 partitions")
    for row in rows:
        path = ROOT / row["v3_image_path"]
        if sha256(path) != row["sha256"]:
            raise RuntimeError(f"V3 validation image hash mismatch: {path}")
    for row in negatives:
        path = ROOT / row["local_path"]
        if sha256(path) != row["sha256"]:
            raise RuntimeError(f"External negative hash mismatch: {path}")
    return config, rows, negatives


def predict(model: YOLO, rows: list[dict], path_key: str, config: dict, kind: str) -> tuple[list[dict], float]:
    sources = [str(ROOT / row[path_key]) for row in rows]
    started = time.perf_counter()
    results = model.predict(
        source=sources, imgsz=int(config["image_size"]),
        conf=float(config["raw_prediction_confidence"]), iou=float(config["iou_threshold"]),
        device=str(config["device"]), batch=int(config["batch_size"]), verbose=False, stream=False,
    )
    elapsed = time.perf_counter() - started
    if len(results) != len(rows):
        raise RuntimeError("Prediction count does not match input count")
    records = []
    for row, result, source in zip(rows, results, sources):
        boxes = result.boxes
        best = None
        class_conf = {0: 0.0, 1: 0.0}
        if boxes is not None:
            for index in range(len(boxes)):
                cls = int(boxes.cls[index].item())
                conf = float(boxes.conf[index].item())
                if cls in class_conf:
                    class_conf[cls] = max(class_conf[cls], conf)
                if best is None or conf > best["confidence"]:
                    best = {"class": cls, "confidence": conf, "box": [float(x) for x in boxes.xyxy[index].tolist()]}
        top_class = None if best is None else best["class"]
        top_conf = 0.0 if best is None else best["confidence"]
        other_conf = 0.0 if top_class is None else class_conf[1 - top_class]
        box = None if best is None else best["box"]
        height, width = result.orig_shape
        box_area = 0.0 if box is None else max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1]) / (width * height)
        records.append({
            "image_id": row.get("image_id") or Path(source).name,
            "source_path": str(Path(source).relative_to(ROOT)).replace("\\", "/"),
            "kind": kind,
            "true_class": int(row["v3_class_id"]) if "v3_class_id" in row else None,
            "physical_sample_id": row.get("physical_sample_id", ""),
            "negative_category": row.get("category", ""),
            "negative_partition": row.get("phase3_partition", ""),
            "raw_prediction": top_class,
            "top_confidence": top_conf,
            "runner_up_confidence": other_conf,
            "class_margin": top_conf - other_conf,
            "box_xyxy": box,
            "box_area_ratio": box_area,
            "quality": quality_scores(source),
            "inference_ms": float(result.speed.get("inference", 0.0)),
        })
    return records, elapsed


def make_challenges(validation_rows: list[dict], config: dict) -> tuple[list[dict], dict]:
    rng = random.Random(int(config["seed"]))
    selected = []
    wanted = int(config["quality"]["controlled_challenge_images_per_class"])
    for cls in ("0", "1"):
        candidates = sorted((r for r in validation_rows if r["v3_class_id"] == cls), key=lambda r: r["v3_image_path"])
        rng.shuffle(candidates)
        seen = set()
        for row in candidates:
            if row["physical_sample_id"] not in seen:
                selected.append(row)
                seen.add(row["physical_sample_id"])
            if len(seen) == wanted:
                break
    challenge_records = []
    for row in selected:
        source = read_image(ROOT / row["v3_image_path"])
        stem = Path(row["v3_image_path"]).stem
        variants = {
            "blur": cv2.GaussianBlur(source, (int(config["quality"]["challenge_blur_kernel"]),) * 2, 0),
            "dark": np.clip(source.astype(np.float32) * float(config["quality"]["challenge_dark_factor"]), 0, 255).astype(np.uint8),
        }
        target_dim = int(config["quality"]["challenge_low_resolution_dimension"])
        scale = target_dim / min(source.shape[:2])
        variants["low_resolution"] = cv2.resize(source, (round(source.shape[1] * scale), round(source.shape[0] * scale)), interpolation=cv2.INTER_AREA)
        for variant, image in variants.items():
            output = CHALLENGE_ROOT / variant / f"{stem}.jpg"
            output.parent.mkdir(parents=True, exist_ok=True)
            encoded_ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 92])
            if not encoded_ok:
                raise RuntimeError(f"Could not save {output}")
            encoded.tofile(str(output))
            challenge_records.append({
                "variant": variant, "source_image": row["v3_image_path"],
                "physical_sample_id": row["physical_sample_id"], "true_class": int(row["v3_class_id"]),
                "local_path": str(output.relative_to(ROOT)).replace("\\", "/"), "quality": quality_scores(output),
            })
    summary = {"selected_originals": len(selected), "derived_images": len(challenge_records), "images_per_variant": dict(Counter(r["variant"] for r in challenge_records))}
    return challenge_records, summary


def select_quality(validation: list[dict], challenges: list[dict], config: dict) -> tuple[dict, dict]:
    cap = int(config["quality"]["max_validation_false_rejections_per_gate"])
    specs = {
        "minimum_blur_variance": ("blur_laplacian_variance_candidates", "blur_laplacian_variance", "blur"),
        "minimum_brightness": ("minimum_brightness_candidates", "brightness", "dark"),
        "minimum_dimension": ("minimum_dimension_candidates", "minimum_dimension", "low_resolution"),
    }
    selected, audit = {}, {}
    for name, (candidate_key, score_key, variant) in specs.items():
        rows = []
        for threshold in config["quality"][candidate_key]:
            natural_rejects = sum(r["quality"][score_key] < threshold for r in validation)
            challenge_rejects = sum(r["quality"][score_key] < threshold for r in challenges if r["variant"] == variant)
            rows.append({"threshold": threshold, "natural_validation_rejections": natural_rejects, "controlled_challenge_rejections": challenge_rejects})
        eligible = [r for r in rows if r["natural_validation_rejections"] <= cap]
        winner = max(eligible, key=lambda r: (r["controlled_challenge_rejections"], -r["natural_validation_rejections"], r["threshold"]))
        selected[name] = winner["threshold"]
        audit[name] = {"selected": winner, "candidates": rows}
    area_rows = []
    for threshold in config["quality"]["minimum_box_area_ratio_candidates"]:
        rejects = sum(r["box_area_ratio"] < threshold for r in validation)
        area_rows.append({"threshold": threshold, "natural_validation_rejections": rejects})
    eligible = [r for r in area_rows if r["natural_validation_rejections"] <= cap]
    winner = max(eligible, key=lambda r: (r["threshold"], -r["natural_validation_rejections"]))
    selected["minimum_box_area_ratio"] = winner["threshold"]
    audit["minimum_box_area_ratio"] = {"selected": winner, "candidates": area_rows}
    return selected, audit


def pre_quality_pass(record: dict, q: dict) -> bool:
    return (
        record["quality"]["minimum_dimension"] >= q["minimum_dimension"]
        and record["quality"]["brightness"] >= q["minimum_brightness"]
        and record["quality"]["blur_laplacian_variance"] >= q["minimum_blur_variance"]
        and (record["raw_prediction"] is None or record["box_area_ratio"] >= q["minimum_box_area_ratio"])
    )


def select_detection(validation: list[dict], calibration_negatives: list[dict], q: dict, config: dict) -> tuple[float, list[dict]]:
    rows = []
    for threshold in config["detection_threshold_candidates"]:
        positive_retained = sum(pre_quality_pass(r, q) and r["top_confidence"] >= threshold for r in validation)
        false_accepts = sum(pre_quality_pass(r, q) and r["top_confidence"] >= threshold for r in calibration_negatives)
        rows.append({
            "threshold": threshold, "positive_retained": positive_retained,
            "positive_retention": positive_retained / len(validation),
            "calibration_negative_false_accepts": false_accepts,
            "calibration_negative_false_acceptance_rate": false_accepts / len(calibration_negatives),
        })
    eligible = [r for r in rows if r["positive_retention"] >= float(config["minimum_valid_detection_retention"])]
    if not eligible:
        raise RuntimeError("No detection threshold satisfies the predeclared positive-retention constraint")
    winner = min(eligible, key=lambda r: (r["calibration_negative_false_accepts"], -r["positive_retention"], r["threshold"]))
    return float(winner["threshold"]), rows


def select_uncertainty(validation: list[dict], q: dict, detection_threshold: float, config: dict) -> tuple[dict, list[dict]]:
    candidates = []
    for top_threshold in config["uncertainty"]["top_confidence_candidates"]:
        for margin_threshold in config["uncertainty"]["class_margin_candidates"]:
            accepted = [r for r in validation if pre_quality_pass(r, q) and r["top_confidence"] >= detection_threshold and r["top_confidence"] >= top_threshold and r["class_margin"] >= margin_threshold]
            coverage = len(accepted) / len(validation)
            predictions = [r["raw_prediction"] for r in accepted]
            truth = [r["true_class"] for r in accepted]
            both = set(truth) == {0, 1}
            macro = f1_score(truth, predictions, labels=[0, 1], average="macro", zero_division=0) if both else 0.0
            accuracy = sum(a == b for a, b in zip(truth, predictions)) / len(accepted) if accepted else 0.0
            candidates.append({
                "grade_confidence": top_threshold, "grade_margin": margin_threshold,
                "accepted": len(accepted), "rejected": len(validation) - len(accepted), "coverage": coverage,
                "accepted_accuracy": accuracy, "accepted_macro_f1": macro, "both_classes_accepted": both,
            })
    eligible = [r for r in candidates if r["coverage"] >= float(config["uncertainty"]["minimum_coverage"]) and r["both_classes_accepted"]]
    winner = max(eligible, key=lambda r: (r["accepted_macro_f1"], r["accepted_accuracy"], r["coverage"], -r["grade_confidence"], -r["grade_margin"]))
    return winner, candidates


def baseline_negative_metrics(records: list[dict], thresholds: list[float]) -> dict:
    output = {}
    for threshold in thresholds:
        accepted = [r for r in records if r["top_confidence"] >= threshold]
        by_category = {}
        for category in sorted({r["negative_category"] for r in records}):
            category_rows = [r for r in records if r["negative_category"] == category]
            count = sum(r["top_confidence"] >= threshold for r in category_rows)
            by_category[category] = {"images": len(category_rows), "false_accepts": count, "false_acceptance_rate": count / len(category_rows)}
        output[f"{threshold:.2f}"] = {
            "images": len(records), "rejected": len(records) - len(accepted), "false_accepts": len(accepted),
            "rejection_rate": (len(records) - len(accepted)) / len(records), "false_acceptance_rate": len(accepted) / len(records),
            "predicted_grade_1": sum(r["raw_prediction"] == 0 for r in accepted),
            "predicted_grade_2": sum(r["raw_prediction"] == 1 for r in accepted), "by_category": by_category,
        }
    return output


def apply_decisions(records: list[dict], thresholds: FrozenThresholds) -> list[dict]:
    return [{**record, **decide(record, thresholds)} for record in records]


def matrix_and_metrics(validation: list[dict], evaluation_negatives: list[dict]) -> dict:
    valid_counts = Counter(r["decision"] for r in validation)
    negative_counts = Counter(r["decision"] for r in evaluation_negatives)
    accepted_valid = [r for r in validation if r["decision"] in {"GRADE_1", "GRADE_2"}]
    truth = [r["true_class"] for r in accepted_valid]
    preds = [0 if r["decision"] == "GRADE_1" else 1 for r in accepted_valid]
    return {
        "matrix": {"rows": ["VALID_PEPPER", "NON_PEPPER"], "columns": FINAL_STATES,
                   "values": [[valid_counts[s] for s in FINAL_STATES], [negative_counts[s] for s in FINAL_STATES]]},
        "valid_pepper": {
            "images": len(validation), "accepted_for_grading": len(accepted_valid), "coverage": len(accepted_valid) / len(validation),
            "false_rejections": len(validation) - len(accepted_valid), "false_rejection_rate": (len(validation) - len(accepted_valid)) / len(validation),
            "accepted_accuracy": sum(a == b for a, b in zip(truth, preds)) / len(truth),
            "accepted_macro_f1": f1_score(truth, preds, labels=[0, 1], average="macro", zero_division=0),
            "decision_counts": dict(valid_counts),
            "grade_confusion_matrix_accepted": confusion_matrix(truth, preds, labels=[0, 1]).tolist(),
        },
        "held_out_non_pepper": {
            "images": len(evaluation_negatives), "rejected": sum(r["decision"] not in {"GRADE_1", "GRADE_2"} for r in evaluation_negatives),
            "false_accepts": sum(r["decision"] in {"GRADE_1", "GRADE_2"} for r in evaluation_negatives),
            "rejection_rate": sum(r["decision"] not in {"GRADE_1", "GRADE_2"} for r in evaluation_negatives) / len(evaluation_negatives),
            "false_acceptance_rate": sum(r["decision"] in {"GRADE_1", "GRADE_2"} for r in evaluation_negatives) / len(evaluation_negatives),
            "decision_counts": dict(negative_counts),
        },
    }


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def make_examples(records: list[dict], challenges: list[dict]) -> list[dict]:
    choices = []
    pools = [
        ("confident_valid", [r for r in records if r["kind"] == "VALID_PEPPER" and r["decision"].startswith("GRADE")]),
        ("uncertain_valid", [r for r in records if r["kind"] == "VALID_PEPPER" and r["decision"] == "UNCERTAIN_GRADE"]),
        ("rejected_negative", [r for r in records if r["kind"] == "NON_PEPPER" and r["decision"] not in {"GRADE_1", "GRADE_2"}]),
        ("false_accept_negative", [r for r in records if r["kind"] == "NON_PEPPER" and r["decision"] in {"GRADE_1", "GRADE_2"}]),
    ]
    for label, pool in pools:
        if pool:
            row = min(pool, key=lambda r: r["top_confidence"]) if "uncertain" in label else max(pool, key=lambda r: r["top_confidence"])
            choices.append({"example_type": label, **row})
    for variant in ("blur", "dark", "low_resolution"):
        row = next(r for r in challenges if r["variant"] == variant)
        choices.append({"example_type": f"controlled_{variant}", "source_path": row["local_path"], "image_id": Path(row["local_path"]).name,
                        "decision": "POOR_IMAGE", "rejection_reason": f"controlled_{variant}", "top_confidence": None, "box_xyxy": None})
    return choices


def examples_sheet(examples: list[dict]) -> None:
    cell_w, cell_h = 380, 300
    canvas = Image.new("RGB", (cell_w * 2, cell_h * ((len(examples) + 1) // 2)), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for i, row in enumerate(examples):
        image = Image.open(ROOT / row["source_path"]).convert("RGB")
        original_w, original_h = image.size
        image.thumbnail((cell_w - 16, cell_h - 62), Image.Resampling.LANCZOS)
        x, y = (i % 2) * cell_w, (i // 2) * cell_h
        canvas.paste(image, (x + 8, y + 4))
        if row.get("box_xyxy"):
            sx, sy = image.width / original_w, image.height / original_h
            box = row["box_xyxy"]
            draw.rectangle((x + 8 + box[0] * sx, y + 4 + box[1] * sy, x + 8 + box[2] * sx, y + 4 + box[3] * sy), outline="red", width=3)
        text = f"{row['example_type']} | {row.get('decision')}\n{row['image_id']} | conf={row.get('top_confidence')}\n{row.get('rejection_reason')}"
        draw.multiline_text((x + 8, y + cell_h - 52), text, fill="black", font=font, spacing=2)
    canvas.save(OUTPUT / "representative_phase3_examples.png", optimize=True)


def main() -> int:
    if (OUTPUT / "phase3_metrics.json").exists():
        raise RuntimeError("Phase 3 final metrics already exist; refusing to overwrite the frozen result")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    config, validation_rows, negative_rows = verify_inputs()
    checkpoint_before = sha256(MODEL_PATH)
    model = YOLO(str(MODEL_PATH))
    validation, validation_elapsed = predict(model, validation_rows, "v3_image_path", config, "VALID_PEPPER")
    negatives, negative_elapsed = predict(model, negative_rows, "local_path", config, "NON_PEPPER")
    if sha256(MODEL_PATH) != checkpoint_before:
        raise RuntimeError("Frozen Phase 2 checkpoint changed during Phase 3")

    challenges, challenge_summary = make_challenges(validation_rows, config)
    quality_selected, quality_audit = select_quality(validation, challenges, config)
    calibration_negatives = [r for r in negatives if r["negative_partition"] == "CALIBRATION"]
    evaluation_negatives = [r for r in negatives if r["negative_partition"] == "EVALUATION"]
    detection_threshold, detection_candidates = select_detection(validation, calibration_negatives, quality_selected, config)
    uncertainty_winner, uncertainty_candidates = select_uncertainty(validation, quality_selected, detection_threshold, config)
    thresholds = FrozenThresholds(
        **quality_selected, detection_confidence=detection_threshold,
        grade_confidence=float(uncertainty_winner["grade_confidence"]), grade_margin=float(uncertainty_winner["grade_margin"]),
    )
    validation_final = apply_decisions(validation, thresholds)
    negatives_final = apply_decisions(negatives, thresholds)
    evaluation_final = [r for r in negatives_final if r["negative_partition"] == "EVALUATION"]
    consolidated = matrix_and_metrics(validation_final, evaluation_final)
    baseline = baseline_negative_metrics(negatives, config["negative_baseline_thresholds"])

    quality_payload = {
        "source": "V3 VALIDATION only plus controlled perturbations derived from validation; sealed TEST not accessed",
        "selected_thresholds": quality_selected, "challenge_summary": challenge_summary,
        "natural_validation_combined_quality_rejections": sum(not pre_quality_pass(r, quality_selected) for r in validation),
        "audit": quality_audit,
    }
    uncertainty_payload = {
        "source": "V3 VALIDATION only; heuristic confidence and class-margin abstention, not probability calibration",
        "selected": uncertainty_winner, "detection_threshold": detection_threshold,
        "candidate_results": uncertainty_candidates,
    }
    frozen = {
        "status": "FROZEN_AFTER_VALIDATION_BEFORE_EXTERNAL_EVALUATION_SUMMARY",
        "checkpoint": str(MODEL_PATH.relative_to(ROOT)).replace("\\", "/"), "checkpoint_sha256": checkpoint_before,
        "thresholds": asdict(thresholds), "decision_order": config["final_decision_order"],
        "sealed_phase2_test_accessed": False,
    }
    metrics = {
        "phase": 3, "status": "COMPLETE", "checkpoint_sha256": checkpoint_before,
        "inputs": {"validation_images": 116, "external_negatives": 80, "negative_calibration": 40, "negative_evaluation": 40,
                   "external_negative_visual_audit": "80/80 confirmed non-pepper from contact sheet"},
        "baseline_negative_thresholds": baseline,
        "frozen_thresholds": asdict(thresholds), "consolidated": consolidated,
        "runtime": {"validation_wall_seconds": validation_elapsed, "negative_wall_seconds": negative_elapsed,
                    "mean_model_inference_ms": float(np.mean([r["inference_ms"] for r in validation + negatives]))},
        "integrity": {"phase2_checkpoint_unchanged": sha256(MODEL_PATH) == checkpoint_before, "sealed_phase2_test_accessed": False},
        "limits": ["External negatives are a bounded Wikimedia Commons set, not deployment-distribution field data.",
                   "Confidence/margin thresholds are validation-tuned abstention heuristics, not calibrated probabilities.",
                   "Quality challenges are controlled perturbations and do not replace natural poor-quality field collection."],
    }
    write_json(OUTPUT / "quality_calibration.json", quality_payload)
    write_json(OUTPUT / "uncertainty_calibration.json", uncertainty_payload)
    write_json(OUTPUT / "detection_threshold_calibration.json", {"selected_threshold": detection_threshold, "candidates": detection_candidates})
    write_json(OUTPUT / "negative_baseline_metrics.json", baseline)
    write_json(OUTPUT / "decision_config_frozen.json", frozen)
    write_json(OUTPUT / "phase3_metrics.json", metrics)
    write_csv(OUTPUT / "validation_decisions.csv", validation_final,
              ["image_id", "physical_sample_id", "true_class", "raw_prediction", "top_confidence", "runner_up_confidence", "class_margin", "box_area_ratio", "decision", "rejection_reason", "message", "source_path"])
    write_csv(OUTPUT / "negative_predictions.csv", negatives_final,
              ["image_id", "negative_category", "negative_partition", "raw_prediction", "top_confidence", "runner_up_confidence", "class_margin", "box_area_ratio", "decision", "rejection_reason", "message", "source_path"])
    examples = make_examples(validation_final + negatives_final, challenges)
    write_json(OUTPUT / "representative_phase3_examples.json", examples)
    examples_sheet(examples)
    print(json.dumps({"thresholds": asdict(thresholds), "baseline": baseline, "consolidated": consolidated}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
