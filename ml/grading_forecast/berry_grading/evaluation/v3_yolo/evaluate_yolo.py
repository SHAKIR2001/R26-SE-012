"""Evaluate the frozen Phase 2 V3 YOLO checkpoint without test-set tuning.

Run validation first. That run selects and freezes the image-level confidence
threshold. A separate explicit test invocation consumes the frozen threshold
and refuses to overwrite an existing sealed-test result.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from PIL import Image, ImageDraw
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[5]
CONFIG = ROOT / "ml/grading_forecast/berry_grading/training/v3_yolo/experiment.yaml"
DATA_YAML = ROOT / "data/processed/grading_forecast/berry_v3/yolo_phase2/data.yaml"
MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv"
MODEL = ROOT / "ml/grading_forecast/berry_grading/models/v3_yolo/best.pt"
OUTPUT = ROOT / "ml/grading_forecast/berry_grading/evaluation/v3_yolo"
THRESHOLD_FILE = OUTPUT / "threshold_selection.json"
GRADE_NAMES = {0: "V3 Grade 1", 1: "V3 Grade 2", 2: "REJECT"}


def read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_manifest(partition: str) -> list[dict]:
    with MANIFEST.open(newline="", encoding="utf-8-sig") as handle:
        rows = [r for r in csv.DictReader(handle) if r["research_partition"] == partition]
    expected = {"VALIDATION": 116, "TEST": 120}[partition]
    if len(rows) != expected:
        raise RuntimeError(f"Expected {expected} {partition} rows, found {len(rows)}")
    return rows


def materialized_image(row: dict, split: str) -> Path:
    return ROOT / "data/processed/grading_forecast/berry_v3/yolo_phase2/materialized" / split / "images" / Path(row["v3_image_path"]).name


def predict_raw(model: YOLO, rows: list[dict], split: str, config: dict) -> list[dict]:
    sources = [str(materialized_image(row, split)) for row in rows]
    start = time.perf_counter()
    results = model.predict(
        source=sources,
        imgsz=int(config["image_size"]),
        conf=0.001,
        iou=0.7,
        device=str(config["device"]),
        batch=int(config["batch_size"]),
        verbose=False,
        stream=False,
    )
    elapsed = time.perf_counter() - start
    by_name = {Path(result.path).name: result for result in results}
    records = []
    for row in rows:
        name = Path(row["v3_image_path"]).name
        result = by_name[name]
        best = None
        if result.boxes is not None and len(result.boxes):
            index = int(torch.argmax(result.boxes.conf).item())
            best = {
                "raw_prediction": int(result.boxes.cls[index].item()),
                "confidence": float(result.boxes.conf[index].item()),
                "box_xyxy": [float(v) for v in result.boxes.xyxy[index].tolist()],
            }
        records.append(
            {
                **row,
                "image_id": name,
                "true_class": int(row["v3_class_id"]),
                "raw_prediction": None if best is None else best["raw_prediction"],
                "confidence": 0.0 if best is None else best["confidence"],
                "box_xyxy": None if best is None else best["box_xyxy"],
                "inference_ms": float(result.speed.get("inference", 0.0)),
            }
        )
    if len(records) != len(rows) or set(by_name) != {Path(p).name for p in sources}:
        raise RuntimeError("Prediction/image identity verification failed")
    return records, elapsed


def apply_threshold(records: list[dict], threshold: float) -> list[dict]:
    output = []
    for record in records:
        pred = record["raw_prediction"]
        accepted = pred is not None and record["confidence"] >= threshold
        output.append({**record, "predicted_class": pred if accepted else 2, "accepted": accepted})
    return output


def classification_metrics(records: list[dict]) -> dict:
    y_true = [r["true_class"] for r in records]
    y_pred = [r["predicted_class"] for r in records]
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=[0, 1], zero_division=0
    )
    total = len(records)
    correct = sum(a == b for a, b in zip(y_true, y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])[:2, :]
    class_metrics = {
        GRADE_NAMES[i]: {
            "precision": float(precision[i]), "recall": float(recall[i]),
            "f1": float(f1[i]), "support": int(support[i]),
        }
        for i in (0, 1)
    }
    weights = support / support.sum()
    return {
        "images": total,
        "accepted": sum(r["accepted"] for r in records),
        "rejected": sum(not r["accepted"] for r in records),
        "coverage": sum(r["accepted"] for r in records) / total,
        "accuracy": correct / total,
        "balanced_accuracy": float(np.mean(recall)),
        "macro_f1": float(np.mean(f1)),
        "weighted_f1": float(np.sum(f1 * weights)),
        "per_class": class_metrics,
        "confusion_matrix": {
            "rows": [GRADE_NAMES[0], GRADE_NAMES[1]],
            "columns": [GRADE_NAMES[0], GRADE_NAMES[1], GRADE_NAMES[2]],
            "values": cm.tolist(),
        },
    }


def calibrate(records: list[dict], config: dict) -> tuple[float, list[dict]]:
    calibration = config["calibration"]
    candidates = np.arange(
        float(calibration["candidate_min"]),
        float(calibration["candidate_max"]) + 0.0001,
        float(calibration["candidate_step"]),
    )
    scored = []
    for threshold in candidates:
        metrics = classification_metrics(apply_threshold(records, float(threshold)))
        scored.append({"threshold": round(float(threshold), 2), **metrics})
    # max is stable: candidates are ascending, implementing the lower-threshold tie break.
    best = max(scored, key=lambda item: item["macro_f1"])
    return float(best["threshold"]), scored


def detection_metrics(model: YOLO, split: str, config: dict) -> dict:
    split_name = {"validation": "val", "test": "test"}[split]
    result = model.val(
        data=str(DATA_YAML), split=split_name, imgsz=int(config["image_size"]),
        batch=int(config["batch_size"]), device=str(config["device"]),
        conf=0.001, iou=0.7, plots=False, verbose=False,
        project=str(OUTPUT / "framework_validation"), name=split, exist_ok=True,
    )
    return {
        "precision": float(result.box.mp), "recall": float(result.box.mr),
        "map50": float(result.box.map50), "map50_95": float(result.box.map),
        "per_class_map50_95": {
            GRADE_NAMES[i]: float(value) for i, value in enumerate(result.box.maps.tolist())
        },
    }


def sample_metrics(records: list[dict]) -> dict:
    grouped = defaultdict(list)
    for record in records:
        grouped[record["physical_sample_id"]].append(record)
    majority_rows, weighted_rows = [], []
    unanimous = conflicting = 0
    for sample_id, views in sorted(grouped.items()):
        truth = {v["true_class"] for v in views}
        if len(truth) != 1:
            raise RuntimeError(f"Inconsistent truth within physical sample {sample_id}")
        accepted = [v for v in views if v["accepted"]]
        accepted_classes = {v["predicted_class"] for v in accepted}
        unanimous += int(len(accepted) == len(views) and len(accepted_classes) == 1)
        conflicting += int(len(accepted_classes) > 1)
        if not accepted:
            majority = weighted = 2
        else:
            counts = Counter(v["predicted_class"] for v in accepted)
            max_count = max(counts.values())
            tied = [label for label, count in counts.items() if count == max_count]
            confidence_sums = {label: sum(v["confidence"] for v in accepted if v["predicted_class"] == label) for label in tied}
            majority = max(tied, key=lambda label: (confidence_sums[label], -label))
            all_sums = {label: sum(v["confidence"] for v in accepted if v["predicted_class"] == label) for label in (0, 1)}
            weighted = max((0, 1), key=lambda label: (all_sums[label], -label))
        base = {"physical_sample_id": sample_id, "true_class": next(iter(truth)), "views": len(views)}
        majority_rows.append({**base, "predicted_class": majority, "accepted": majority != 2})
        weighted_rows.append({**base, "predicted_class": weighted, "accepted": weighted != 2})
    return {
        "groups": len(grouped), "unanimous_samples": unanimous,
        "conflicting_samples": conflicting,
        "majority_vote": classification_metrics(majority_rows),
        "confidence_weighted": classification_metrics(weighted_rows),
    }


def subgroup_metrics(records: list[dict]) -> dict:
    output = {}
    keys = {
        "camera_model": lambda r: r["camera_model"] or "EXIF unavailable",
        "resolution": lambda r: f'{r["width"]}x{r["height"]}',
    }
    for dimension, key_fn in keys.items():
        groups = defaultdict(list)
        for record in records:
            groups[key_fn(record)].append(record)
        output[dimension] = {
            name: classification_metrics(items) for name, items in sorted(groups.items())
        }
    return output


def intersection_over_union(record: dict, split: str) -> float | None:
    if record["box_xyxy"] is None:
        return None
    # Use the stored JPEG dimensions seen by YOLO. Manifest dimensions are
    # EXIF-oriented and can be transposed relative to model coordinates.
    with Image.open(materialized_image(record, split)) as source_image:
        width, height = map(float, source_image.size)
    cx, cy = float(record["box_x_center"]) * width, float(record["box_y_center"]) * height
    bw, bh = float(record["box_width"]) * width, float(record["box_height"]) * height
    truth = [cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2]
    pred = record["box_xyxy"]
    ix1, iy1, ix2, iy2 = max(truth[0], pred[0]), max(truth[1], pred[1]), min(truth[2], pred[2]), min(truth[3], pred[3])
    intersection = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = (truth[2] - truth[0]) * (truth[3] - truth[1]) + (pred[2] - pred[0]) * (pred[3] - pred[1]) - intersection
    return intersection / union if union else 0.0


def error_analysis(records: list[dict], output_dir: Path, split: str) -> list[dict]:
    candidates = {
        "correct_grade_1": lambda r: r["true_class"] == 0 and r["predicted_class"] == 0,
        "incorrect_grade_1": lambda r: r["true_class"] == 0 and r["predicted_class"] != 0,
        "correct_grade_2": lambda r: r["true_class"] == 1 and r["predicted_class"] == 1,
        "incorrect_grade_2": lambda r: r["true_class"] == 1 and r["predicted_class"] != 1,
        "low_confidence": lambda r: True,
    }
    selected, used = [], set()
    for category, predicate in candidates.items():
        pool = [r for r in records if predicate(r) and r["image_id"] not in used]
        if category == "low_confidence":
            pool.sort(key=lambda r: r["confidence"])
        else:
            pool.sort(key=lambda r: (-r["confidence"], r["image_id"]))
        if pool:
            item = pool[0]
            used.add(item["image_id"])
            selected.append((category, item))
    conflicting_samples = {
        sample for sample in {r["physical_sample_id"] for r in records}
        if len({r["predicted_class"] for r in records if r["physical_sample_id"] == sample and r["accepted"]}) > 1
    }
    mixed = [r for r in records if r["physical_sample_id"] in conflicting_samples and r["image_id"] not in used]
    if mixed:
        selected.append(("conflicting_physical_sample", sorted(mixed, key=lambda r: r["confidence"])[0]))

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    artifacts = []
    for axis, choice in zip(axes.flat, selected):
        category, record = choice
        image_path = materialized_image(record, split)
        image = Image.open(image_path).convert("RGB")
        original_width, original_height = image.size
        image.thumbnail((1400, 1050), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(image)
        if record["box_xyxy"]:
            scale_x, scale_y = image.width / original_width, image.height / original_height
            display_box = [
                record["box_xyxy"][0] * scale_x, record["box_xyxy"][1] * scale_y,
                record["box_xyxy"][2] * scale_x, record["box_xyxy"][3] * scale_y,
            ]
            draw.rectangle(display_box, outline="red", width=max(3, image.width // 350))
        iou = intersection_over_union(record, split)
        interpretation = "no sufficiently confident detection" if not record["accepted"] else (
            "predicted box substantially overlaps annotated pepper sample" if iou is not None and iou >= 0.5
            else "predicted box has weak overlap; wrong-region attention is concerning"
        )
        axis.imshow(image)
        axis.set_title(f'{category}\ntrue={GRADE_NAMES[record["true_class"]]} pred={GRADE_NAMES[record["predicted_class"]]} conf={record["confidence"]:.3f}')
        axis.axis("off")
        artifacts.append({
            "category": category, "image_id": record["image_id"],
            "physical_sample_id": record["physical_sample_id"],
            "true_class": GRADE_NAMES[record["true_class"]],
            "predicted_class": GRADE_NAMES[record["predicted_class"]],
            "confidence": record["confidence"], "box_xyxy": record["box_xyxy"],
            "box_iou": iou, "interpretation": interpretation,
        })
    for axis in axes.flat[len(selected):]:
        axis.axis("off")
    fig.suptitle("Representative Phase 2 predictions (red = model box; diagnostic, not causal explanation)")
    fig.tight_layout()
    fig.savefig(output_dir / "representative_error_analysis.png", dpi=150)
    plt.close(fig)
    with (output_dir / "representative_error_analysis.json").open("w", encoding="utf-8") as handle:
        json.dump(artifacts, handle, indent=2)
    return artifacts


def write_predictions(records: list[dict], path: Path) -> None:
    fields = ["image_id", "physical_sample_id", "camera_model", "width", "height", "true_class", "predicted_class", "confidence", "accepted", "box_xyxy", "inference_ms"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in records)


def plot_confusion(metrics: dict, path: Path) -> None:
    values = np.array(metrics["confusion_matrix"]["values"])
    fig, axis = plt.subplots(figsize=(7, 5))
    image = axis.imshow(values, cmap="Blues")
    for (row, col), value in np.ndenumerate(values):
        axis.text(col, row, str(value), ha="center", va="center")
    axis.set_xticks(range(3), metrics["confusion_matrix"]["columns"], rotation=20)
    axis.set_yticks(range(2), metrics["confusion_matrix"]["rows"])
    axis.set_xlabel("Predicted")
    axis.set_ylabel("True")
    fig.colorbar(image, ax=axis)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", required=True, choices=["validation", "test"])
    args = parser.parse_args()
    os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".ultralytics"))
    config = read_yaml(CONFIG)
    output_dir = OUTPUT / args.split
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "metrics.json"
    if args.split == "test" and metrics_path.exists():
        raise RuntimeError("Sealed test metrics already exist; refusing a repeated test evaluation")
    if not MODEL.exists():
        raise FileNotFoundError(f"Frozen best checkpoint not found: {MODEL}")
    partition = args.split.upper()
    rows = read_manifest(partition)
    model = YOLO(str(MODEL))
    raw_records, elapsed = predict_raw(model, rows, args.split, config)

    if args.split == "validation":
        threshold, calibration = calibrate(raw_records, config)
        threshold_record = {
            "status": "FROZEN_BEFORE_TEST", "source": "VALIDATION only",
            "objective": config["calibration"]["objective"],
            "tie_break": config["calibration"]["tie_break"],
            "selected_threshold": threshold,
            "baseline_threshold": float(config["baseline_confidence_threshold"]),
            "baseline_metrics": classification_metrics(apply_threshold(raw_records, float(config["baseline_confidence_threshold"]))),
            "selected_validation_metrics": classification_metrics(apply_threshold(raw_records, threshold)),
            "candidate_results": calibration,
        }
        with THRESHOLD_FILE.open("w", encoding="utf-8") as handle:
            json.dump(threshold_record, handle, indent=2)
    else:
        if not THRESHOLD_FILE.exists():
            raise RuntimeError("Run validation first to freeze the threshold")
        with THRESHOLD_FILE.open(encoding="utf-8") as handle:
            frozen = json.load(handle)
        if frozen.get("status") != "FROZEN_BEFORE_TEST":
            raise RuntimeError("Threshold is not marked frozen before test")
        threshold = float(frozen["selected_threshold"])

    records = apply_threshold(raw_records, threshold)
    grade = classification_metrics(records)
    detection = detection_metrics(model, args.split, config)
    samples = sample_metrics(records)
    subgroups = subgroup_metrics(records)
    inference_times = [r["inference_ms"] for r in records]
    operational = {
        "ultralytics_reported_inference_ms_mean": statistics.fmean(inference_times),
        "ultralytics_reported_inference_ms_median": statistics.median(inference_times),
        "end_to_end_prediction_seconds": elapsed,
        "model_size_bytes": MODEL.stat().st_size,
        "parameter_count": sum(p.numel() for p in model.model.parameters()),
        "input_resolution": int(config["image_size"]),
        "batch_size": int(config["batch_size"]),
        "python": platform.python_version(), "torch": torch.__version__,
        "ultralytics": __import__("ultralytics").__version__,
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "cuda_runtime": torch.version.cuda,
    }
    payload = {
        "experiment_id": config["experiment_id"], "split": partition,
        "checkpoint": str(MODEL.relative_to(ROOT)), "confidence_threshold": threshold,
        "image_level_grade_metrics": grade, "detection_metrics": detection,
        "physical_sample_level": samples, "camera_resolution_diagnostic": subgroups,
        "operational": operational,
        "prediction_rule": "highest-confidence YOLO detection; reject when absent or below frozen threshold",
        "no_detection_state_supported": True,
        "non_pepper_rejection_accuracy_claimed": False,
    }
    write_predictions(records, output_dir / "predictions.csv")
    plot_confusion(grade, output_dir / "image_level_confusion_matrix.png")
    error_analysis(records, output_dir, args.split)
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
