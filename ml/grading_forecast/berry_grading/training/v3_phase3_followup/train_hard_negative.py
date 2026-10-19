"""Run the one-shot Phase 3 Follow-up hard-negative fine-tuning treatment."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import shutil
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import torch
import ultralytics
import yaml
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[5]
DEFAULT_CONFIG = ROOT / "ml/grading_forecast/berry_grading/quality/phase3_followup/experiment.yaml"
DEFAULT_DATA = ROOT / "data/processed/grading_forecast/berry_v3/phase3_followup_yolo/data.yaml"
DEFAULT_MODELS = ROOT / "ml/grading_forecast/berry_grading/models/v3_phase3_followup"
NEGATIVE_MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/phase3_followup_negative_manifest.csv"
V3_MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--models-dir", type=Path, default=DEFAULT_MODELS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume the interrupted one-shot run from training_run/weights/last.pt.",
    )
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    data = yaml.safe_load(args.data.read_text(encoding="utf-8"))
    if data.get("names") != {0: "V3 Grade 1", 1: "V3 Grade 2"}:
        raise RuntimeError(f"Unexpected class mapping: {data.get('names')}")
    base = ROOT / config["base_checkpoint"]
    if not base.is_file():
        raise RuntimeError(f"Missing frozen Phase 2 checkpoint: {base}")
    base_hash = sha256(base)
    if base_hash != "c35cc40515adcb6130a4bc93e8ad3de161dcf46b263a9d7df8286a5b4239a9c4":
        raise RuntimeError(f"Frozen Phase 2 checkpoint hash changed: {base_hash}")
    negatives = csv_rows(NEGATIVE_MANIFEST)
    positives = csv_rows(V3_MANIFEST)
    split_counts = Counter(r["split"] for r in negatives)
    positive_counts = Counter(r["research_partition"] for r in positives)
    if split_counts["NEGATIVE_FINAL_HOLDOUT"] == 0 or split_counts["NEGATIVE_TRAIN"] == 0 or split_counts["NEGATIVE_VALIDATION"] == 0:
        raise RuntimeError(f"Incomplete negative partitions: {split_counts}")
    if positive_counts["TRAIN"] != 539 or positive_counts["VALIDATION"] != 116 or positive_counts["TEST"] != 120:
        raise RuntimeError(f"Frozen positive split changed: {positive_counts}")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required; CPU fallback is disabled")
    payload = {
        "experiment": config,
        "data_yaml": str(args.data.relative_to(ROOT)).replace("\\", "/"),
        "counts": {
            "positive_train": positive_counts["TRAIN"], "negative_train": split_counts["NEGATIVE_TRAIN"],
            "positive_validation": positive_counts["VALIDATION"], "negative_validation": split_counts["NEGATIVE_VALIDATION"],
            "sealed_positive_test": positive_counts["TEST"], "sealed_negative_final_holdout": split_counts["NEGATIVE_FINAL_HOLDOUT"],
        },
        "integrity": {"base_checkpoint_sha256_before": base_hash, "sealed_holdouts_accessed_during_training": False},
        "environment": {
            "executed_at_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
            "platform": platform.platform(), "torch": torch.__version__, "torch_cuda": torch.version.cuda,
            "ultralytics": ultralytics.__version__, "device": torch.cuda.get_device_name(0),
            "device_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
        },
    }
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0
    resume_checkpoint = args.models_dir / "training_run" / "weights" / "last.pt"
    if args.resume:
        if not resume_checkpoint.is_file():
            raise RuntimeError(f"Cannot resume; missing checkpoint: {resume_checkpoint}")
    elif args.models_dir.exists() and any(args.models_dir.iterdir()):
        raise RuntimeError(f"Refusing to overwrite non-empty model directory: {args.models_dir}")
    args.models_dir.mkdir(parents=True, exist_ok=True)
    run_dir = args.models_dir / "training_run"
    os.environ.setdefault("YOLO_CONFIG_DIR", str((ROOT / ".ultralytics").resolve()))
    model = YOLO(str(resume_checkpoint if args.resume else base))
    aug = config["augmentations"]
    started = time.perf_counter()
    if args.resume:
        # Ultralytics restores the original arguments, optimizer, scheduler, epoch,
        # and early-stopping state embedded in last.pt. Supplying new training
        # arguments here would weaken the controlled continuation.
        model.train(resume=True)
    else:
        model.train(
            data=str(args.data.resolve()), imgsz=int(config["image_size"]), batch=int(config["batch_size"]),
            epochs=int(config["epochs"]), patience=int(config["patience"]), seed=int(config["seed"]), deterministic=True,
            device=config["device"], workers=int(config["workers"]), optimizer=config["optimizer"],
            lr0=float(config["learning_rate_initial"]), lrf=float(config["learning_rate_final_fraction"]),
            momentum=float(config["momentum"]), weight_decay=float(config["weight_decay"]), warmup_epochs=float(config["warmup_epochs"]),
            hsv_h=float(aug["hsv_h"]), hsv_s=float(aug["hsv_s"]), hsv_v=float(aug["hsv_v"]),
            degrees=float(aug["degrees"]), translate=float(aug["translate"]), scale=float(aug["scale"]),
            shear=float(aug["shear"]), perspective=float(aug["perspective"]), flipud=float(aug["flip_up_down"]),
            fliplr=float(aug["flip_left_right"]), mosaic=float(aug["mosaic"]), mixup=float(aug["mixup"]),
            cutmix=float(aug["cutmix"]), copy_paste=float(aug["copy_paste"]),
            project=str(args.models_dir.resolve()), name="training_run", exist_ok=False, pretrained=True,
            plots=True, verbose=True, val=True, save=True, save_period=-1, cache=False,
        )
    duration = time.perf_counter() - started
    for name in ("best.pt", "last.pt"):
        source = run_dir / "weights" / name
        if source.is_file():
            shutil.copy2(source, args.models_dir / name)
    best = args.models_dir / "best.pt"
    if not best.is_file():
        raise RuntimeError("Training completed without best.pt")
    if sha256(base) != base_hash:
        raise RuntimeError("Frozen Phase 2 checkpoint changed during follow-up training")
    payload["integrity"]["base_checkpoint_sha256_after"] = sha256(base)
    results_path = run_dir / "results.csv"
    cumulative_training_seconds = duration
    if results_path.is_file():
        result_rows = csv_rows(results_path)
        recorded_times = [float(row["time"]) for row in result_rows if row.get("time")]
        if recorded_times:
            # Ultralytics resets the CSV `time` column when a run is resumed.
            # Sum the completed time segments so the research metadata records
            # total training wall time rather than only the final invocation.
            completed_segments, previous = 0.0, recorded_times[0]
            for current in recorded_times[1:]:
                if current < previous:
                    completed_segments += previous
                previous = current
            cumulative_training_seconds = completed_segments + previous
    payload["training"] = {
        "strategy": "one-shot hard-negative fine-tuning", "resume_used": args.resume,
        "final_invocation_duration_seconds": duration,
        "duration_seconds": cumulative_training_seconds,
        "best_checkpoint": str(best.relative_to(ROOT)).replace("\\", "/"), "best_checkpoint_sha256": sha256(best),
        "last_checkpoint": str((args.models_dir / "last.pt").relative_to(ROOT)).replace("\\", "/"),
        "run_directory": str(run_dir.relative_to(ROOT)).replace("\\", "/"),
        "positive_test_accessed": False, "negative_final_holdout_accessed": False, "original_phase3_holdout_accessed": False,
    }
    (args.models_dir / "experiment_metadata.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["training"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

