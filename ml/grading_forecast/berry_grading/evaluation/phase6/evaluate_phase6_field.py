"""Evaluate an independently labelled Phase 6 field set with frozen artifacts.

The evaluator never trains, tunes, or changes thresholds. It validates the
manifest and independence first, then uses the frozen Phase 3 follow-up model
and decision configuration. Run the integrity validator before this script.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from ml.grading_forecast.berry_grading.quality.phase3.decision_pipeline import (  # noqa: E402
    FrozenThresholds,
    decide,
    quality_scores,
)

PHASE6 = ROOT / "ml/grading_forecast/berry_grading/evaluation/phase6"
MODEL = ROOT / "ml/grading_forecast/berry_grading/models/v3_phase3_followup/best.pt"
FREEZE = ROOT / "ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup/decision_config_frozen.json"
INTEGRITY = PHASE6 / "phase6_integrity.json"
ACCEPTED = {"GRADE_1", "GRADE_2"}
GRADE_TO_ID = {"V3 Grade 1": 0, "V3 Grade 2": 1}
DOMAIN_FIELDS = ("device_model", "lighting", "background", "framing", "pepper_density", "quality_challenge", "negative_category")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, values: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(values)


def validated_inputs(manifest: Path) -> list[dict[str, str]]:
    if not INTEGRITY.is_file():
        raise RuntimeError("Run validate_phase6_integrity.py before field evaluation")
    integrity = json.loads(INTEGRITY.read_text(encoding="utf-8"))
    if integrity.get("freeze_status") != "PASS":
        raise RuntimeError("Historical freeze integrity is not PASS")
    values = read_csv(manifest) if manifest.is_file() else []
    if not values:
        raise RuntimeError("BLOCKED_PENDING_FIELD_DATA: the field manifest has no data rows")

    known_hashes = set()
    for relative in (
        "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv",
        "data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv",
        "data/processed/grading_forecast/berry_v3/phase3_followup_negative_manifest.csv",
    ):
        known_hashes.update(row["sha256"].lower() for row in read_csv(ROOT / relative))

    ids, hashes = set(), set()
    group_partitions: dict[str, set[str]] = defaultdict(set)
    for row in values:
        image_id = row.get("image_id", "").strip()
        sample_id = row.get("physical_sample_id", "").strip()
        if not image_id or image_id in ids:
            raise RuntimeError(f"Missing or duplicate image_id: {image_id!r}")
        ids.add(image_id)
        if not sample_id:
            raise RuntimeError(f"Missing physical_sample_id for {image_id}")
        if row.get("partition") not in {"CALIBRATION", "FINAL_EVALUATION"}:
            raise RuntimeError(f"Invalid partition for {image_id}")
        required_metadata = ("label_source", "device_model", "lighting", "background", "framing", "provenance_note", "consent_or_authorization")
        missing_metadata = [field for field in required_metadata if not row.get(field, "").strip()]
        if missing_metadata:
            raise RuntimeError(f"Required metadata missing for {image_id}: {missing_metadata}")
        if row.get("partition") == "FINAL_EVALUATION" and not row.get("sealed_at_utc", "").strip():
            raise RuntimeError(f"Final-evaluation row is not sealed: {image_id}")
        group_partitions[sample_id].add(row["partition"])
        if row.get("reference_type") not in {"PEPPER", "NON_PEPPER", "UNCERTAIN"}:
            raise RuntimeError(f"Invalid reference_type for {image_id}")
        if row.get("reference_type") == "PEPPER" and row.get("reference_grade") not in GRADE_TO_ID:
            raise RuntimeError(f"Definite pepper row lacks an independent V3 grade: {image_id}")
        if not row.get("label_source", "").strip():
            raise RuntimeError(f"Independent label source is not recorded: {image_id}")
        image = (ROOT / row.get("relative_path", "")).resolve()
        try:
            image.relative_to(ROOT.resolve())
        except ValueError as error:
            raise RuntimeError(f"Image path leaves repository: {image}") from error
        if not image.is_file():
            raise RuntimeError(f"Missing image: {image}")
        actual = sha256(image)
        if actual != row.get("sha256", "").lower():
            raise RuntimeError(f"Hash mismatch: {image_id}")
        if actual in known_hashes:
            raise RuntimeError(f"Prior-dataset hash overlap: {image_id}")
        if actual in hashes:
            raise RuntimeError(f"Duplicate Phase 6 image hash: {image_id}")
        hashes.add(actual)
    leaks = {key: value for key, value in group_partitions.items() if len(value) != 1}
    if leaks:
        raise RuntimeError(f"Physical-sample partition leakage: {leaks}")
    return values


def frozen_thresholds() -> tuple[FrozenThresholds, dict]:
    payload = json.loads(FREEZE.read_text(encoding="utf-8"))
    expected_hash = payload["followup_checkpoint_sha256"]
    if sha256(MODEL) != expected_hash:
        raise RuntimeError("Frozen follow-up model hash mismatch")
    values = payload["thresholds"]
    return FrozenThresholds(**values), payload


def predict(values: list[dict[str, str]], thresholds: FrozenThresholds) -> list[dict]:
    try:
        from ultralytics import YOLO
    except ImportError as error:
        raise RuntimeError(
            "Ultralytics is required only after a valid independent field manifest is available. "
            "Run this evaluator in the frozen YOLO environment recorded by Phase 3 follow-up."
        ) from error
    model = YOLO(str(MODEL))
    sources = [str(ROOT / row["relative_path"]) for row in values]
    results = model.predict(source=sources, imgsz=640, conf=0.001, iou=0.70, device=0, batch=4, verbose=False, stream=False)
    if len(results) != len(values):
        raise RuntimeError("Prediction count does not match manifest")
    decisions = []
    for row, result, source in zip(values, results, sources):
        best = None
        class_confidence = {0: 0.0, 1: 0.0}
        if result.boxes is not None:
            for index in range(len(result.boxes)):
                class_id = int(result.boxes.cls[index].item())
                confidence = float(result.boxes.conf[index].item())
                if class_id not in class_confidence:
                    continue
                class_confidence[class_id] = max(class_confidence[class_id], confidence)
                if best is None or confidence > best["confidence"]:
                    best = {"class": class_id, "confidence": confidence, "box": [float(value) for value in result.boxes.xyxy[index].tolist()]}
        top_class = None if best is None else best["class"]
        top_confidence = 0.0 if best is None else best["confidence"]
        runner_up = 0.0 if top_class is None else class_confidence[1 - top_class]
        box = None if best is None else best["box"]
        height, width = result.orig_shape
        box_area_ratio = 0.0 if box is None else max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1]) / (width * height)
        raw = {
            "raw_prediction": top_class,
            "top_confidence": top_confidence,
            "class_margin": top_confidence - runner_up,
            "box_xyxy": box,
            "box_area_ratio": box_area_ratio,
            "quality": quality_scores(source),
        }
        decision = decide(raw, thresholds)
        decisions.append({
            **row,
            **decision,
            "raw_prediction": top_class,
            "runner_up_confidence": runner_up,
            "box_area_ratio": box_area_ratio,
            "inference_ms": float(result.speed.get("inference", 0.0)),
        })
    return decisions


def grade_metrics(records: list[dict]) -> dict:
    definite = [record for record in records if record["reference_type"] == "PEPPER" and record["reference_grade"] in GRADE_TO_ID]
    accepted = [record for record in definite if record["decision"] in ACCEPTED]
    truth = [GRADE_TO_ID[record["reference_grade"]] for record in accepted]
    predictions = [0 if record["decision"] == "GRADE_1" else 1 for record in accepted]
    if not accepted:
        return {"eligible_pepper_images": len(definite), "accepted_images": 0, "accuracy": None, "balanced_accuracy": None, "macro_f1": None, "weighted_f1": None, "per_class": None, "confusion_matrix": None}
    precision, recall, f1, support = precision_recall_fscore_support(truth, predictions, labels=[0, 1], zero_division=0)
    return {
        "eligible_pepper_images": len(definite),
        "accepted_images": len(accepted),
        "accuracy": accuracy_score(truth, predictions),
        "balanced_accuracy": balanced_accuracy_score(truth, predictions),
        "macro_f1": f1_score(truth, predictions, labels=[0, 1], average="macro", zero_division=0),
        "weighted_f1": f1_score(truth, predictions, labels=[0, 1], average="weighted", zero_division=0),
        "per_class": {
            "V3 Grade 1": {"precision": precision[0], "recall": recall[0], "f1": f1[0], "support": int(support[0])},
            "V3 Grade 2": {"precision": precision[1], "recall": recall[1], "f1": f1[1], "support": int(support[1])},
        },
        "confusion_matrix": confusion_matrix(truth, predictions, labels=[0, 1]).tolist(),
        "metric_scope": "independently labelled accepted definite-pepper images only",
    }


def rejection_metrics(records: list[dict]) -> dict:
    pepper = [record for record in records if record["reference_type"] == "PEPPER" and record["reference_grade"] in GRADE_TO_ID]
    negatives = [record for record in records if record["reference_type"] == "NON_PEPPER"]
    false_rejections = sum(record["decision"] not in ACCEPTED for record in pepper)
    rejected_negatives = sum(record["decision"] not in ACCEPTED for record in negatives)
    return {
        "valid_pepper_images": len(pepper),
        "valid_pepper_accepted": len(pepper) - false_rejections,
        "valid_pepper_coverage": (len(pepper) - false_rejections) / len(pepper) if pepper else None,
        "valid_pepper_false_rejections": false_rejections,
        "valid_pepper_false_rejection_rate": false_rejections / len(pepper) if pepper else None,
        "non_pepper_images": len(negatives),
        "non_pepper_rejected": rejected_negatives,
        "non_pepper_rejection_rate": rejected_negatives / len(negatives) if negatives else None,
        "non_pepper_false_accepts": len(negatives) - rejected_negatives,
        "non_pepper_false_acceptance_rate": (len(negatives) - rejected_negatives) / len(negatives) if negatives else None,
    }


def physical_sample_metrics(records: list[dict]) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        groups[record["physical_sample_id"]].append(record)
    rows = []
    for sample_id, sample in sorted(groups.items()):
        accepted = [record for record in sample if record["decision"] in ACCEPTED]
        votes = Counter(record["decision"] for record in accepted)
        majority = None
        if votes:
            top = votes.most_common()
            majority = top[0][0] if len(top) == 1 or top[0][1] > top[1][1] else "UNCERTAIN_GRADE"
        weighted = {"GRADE_1": 0.0, "GRADE_2": 0.0}
        for record in accepted:
            weighted[record["decision"]] += float(record["model_confidence"])
        weighted_decision = None if not accepted else max(weighted, key=weighted.get) if weighted["GRADE_1"] != weighted["GRADE_2"] else "UNCERTAIN_GRADE"
        accepted_labels = {record["decision"] for record in accepted}
        references = {record["reference_grade"] for record in sample if record["reference_grade"] in GRADE_TO_ID}
        reference = next(iter(references)) if len(references) == 1 else None
        rows.append({"physical_sample_id": sample_id, "images": len(sample), "accepted_images": len(accepted), "reference_grade": reference, "majority_vote": majority, "confidence_weighted": weighted_decision, "conflicting_views": len(accepted_labels) > 1})
    eligible = [row for row in rows if row["reference_grade"] is not None]
    majority_correct = sum(row["majority_vote"] == ("GRADE_1" if row["reference_grade"] == "V3 Grade 1" else "GRADE_2") for row in eligible)
    weighted_correct = sum(row["confidence_weighted"] == ("GRADE_1" if row["reference_grade"] == "V3 Grade 1" else "GRADE_2") for row in eligible)
    return {
        "samples": len(rows),
        "samples_with_independent_grade": len(eligible),
        "majority_vote_accuracy": majority_correct / len(eligible) if eligible else None,
        "confidence_weighted_accuracy": weighted_correct / len(eligible) if eligible else None,
        "conflicting_view_samples": sum(row["conflicting_views"] for row in rows),
        "conflicting_view_rate": sum(row["conflicting_views"] for row in rows) / len(rows) if rows else None,
        "sample_results": rows,
    }


def domain_breakdown(records: list[dict], minimum_count: int) -> dict:
    output = {}
    for field in DOMAIN_FIELDS:
        values = {}
        for value in sorted({record.get(field, "").strip() or "UNSPECIFIED" for record in records}):
            subset = [record for record in records if (record.get(field, "").strip() or "UNSPECIFIED") == value]
            if len(subset) < minimum_count:
                values[value] = {"n": len(subset), "reported": False, "reason": f"fewer than {minimum_count} images"}
            else:
                values[value] = {"n": len(subset), "reported": True, "rejection": rejection_metrics(subset), "grading": grade_metrics(subset)}
        output[field] = values
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=PHASE6 / "phase6_field_manifest.csv")
    parser.add_argument("--partition", choices=["CALIBRATION", "FINAL_EVALUATION"], default="FINAL_EVALUATION")
    parser.add_argument("--minimum-domain-count", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, default=PHASE6)
    args = parser.parse_args()
    manifest = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    output = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    values = [row for row in validated_inputs(manifest) if row["partition"] == args.partition]
    if not values:
        raise RuntimeError(f"No rows exist in requested partition {args.partition}")
    thresholds, freeze = frozen_thresholds()
    decisions = predict(values, thresholds)
    grades = grade_metrics(decisions)
    rejection = rejection_metrics(decisions)
    samples = physical_sample_metrics(decisions)
    uncertain = sum(record["decision"] == "UNCERTAIN_GRADE" for record in decisions)
    rejected = sum(record["decision"] in {"NO_PEPPER", "POOR_IMAGE"} for record in decisions)
    accepted = sum(record["decision"] in ACCEPTED for record in decisions)
    metrics = {
        "phase": 6,
        "status": "COMPLETE_FIELD_EVALUATION_EXECUTED",
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "freeze": {"model_path": str(MODEL.relative_to(ROOT)).replace("\\", "/"), "model_sha256": sha256(MODEL), "decision_config_path": str(FREEZE.relative_to(ROOT)).replace("\\", "/"), "thresholds": freeze["thresholds"], "model_or_threshold_tuned": False},
        "dataset": {"manifest": str(manifest.relative_to(ROOT)).replace("\\", "/"), "manifest_sha256": sha256(manifest), "partition": args.partition, "images": len(decisions), "physical_samples": len({record["physical_sample_id"] for record in decisions}), "devices": len({(record.get("device_make", ""), record.get("device_model", "")) for record in decisions}), "independent": True},
        "overall": {"total_images": len(decisions), "accepted": accepted, "rejected": rejected, "abstained_uncertain": uncertain, "decision_counts": dict(Counter(record["decision"] for record in decisions))},
        "grading": grades,
        "rejection": rejection,
        "domain_shift": domain_breakdown(decisions, args.minimum_domain_count),
        "physical_sample": samples,
        "price_temporal": {"status": "NO_NEW_TEMPORAL_PRICE_EVALUATION_AVAILABLE", "phase5_cutoff": "2026-09-29"},
        "acceptance_gates": {"gate_a_dataset_independence": "PASS", "gate_b_grading_performance": "REPORT_ONLY_NO_POST_TEST_THRESHOLD", "gate_c_rejection_performance": "REPORT_ONLY_NO_POST_TEST_THRESHOLD", "gate_d_domain_shift_stability": "REPORT_ONLY", "gate_e_uncertainty_behavior": "REPORT_ONLY_NOT_CALIBRATED"},
        "limitations": ["No model or threshold changes are permitted from these results.", "Confidence scores are not calibrated probabilities.", "Small domain subgroups are shown with counts and suppressed below the configured reporting minimum."],
    }
    error_rows = []
    for record in decisions:
        expected = GRADE_TO_ID.get(record.get("reference_grade"))
        predicted = 0 if record["decision"] == "GRADE_1" else 1 if record["decision"] == "GRADE_2" else None
        is_error = record["reference_type"] == "NON_PEPPER" and record["decision"] in ACCEPTED
        is_error = is_error or (expected is not None and predicted != expected)
        if is_error:
            error_rows.append({**record, "error_category": "FALSE_ACCEPT" if record["reference_type"] == "NON_PEPPER" else "FALSE_REJECT" if predicted is None else "GRADE_ERROR", "interpretation": "Requires independent review; no causal explanation inferred."})
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase6_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    decision_fields = list(decisions[0])
    write_csv(output / "phase6_decisions.csv", decisions, decision_fields)
    error_fields = decision_fields + ["error_category", "interpretation"]
    write_csv(output / "phase6_error_analysis.csv", error_rows, error_fields)
    print(json.dumps({"status": metrics["status"], "overall": metrics["overall"], "grading": grades, "rejection": rejection}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
