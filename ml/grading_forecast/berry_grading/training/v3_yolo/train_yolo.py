"""Run the single controlled Phase 2 YOLO11n training experiment."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
import ultralytics
import yaml
from ultralytics import YOLO


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("ml/grading_forecast/berry_grading/training/v3_yolo/experiment.yaml"))
    parser.add_argument("--data", type=Path, default=Path("data/processed/grading_forecast/berry_v3/yolo_phase2/data.yaml"))
    parser.add_argument("--models-dir", type=Path, default=Path("ml/grading_forecast/berry_grading/models/v3_yolo"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    data = yaml.safe_load(args.data.read_text(encoding="utf-8"))
    if data.get("names") != {0: "V3 Grade 1", 1: "V3 Grade 2"}:
        raise RuntimeError(f"Unexpected class mapping: {data.get('names')}")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this configured experiment; CPU fallback is disabled")
    payload = {
        "experiment": config,
        "data_yaml": str(args.data),
        "environment": {
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "ultralytics": ultralytics.__version__,
            "device": torch.cuda.get_device_name(0),
            "device_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
            "git_sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip() or None,
        },
    }
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0
    if args.models_dir.exists() and any(args.models_dir.iterdir()):
        raise RuntimeError(f"Refusing to overwrite non-empty model directory: {args.models_dir}")
    args.models_dir.mkdir(parents=True, exist_ok=True)
    run_dir = args.models_dir / "training_run"
    os.environ.setdefault("YOLO_CONFIG_DIR", str((Path.cwd() / ".ultralytics").resolve()))
    model = YOLO(config["model"])
    aug = config["augmentations"]
    started = time.perf_counter()
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
    best_source = run_dir / "weights" / "best.pt"
    last_source = run_dir / "weights" / "last.pt"
    if not best_source.is_file():
        raise RuntimeError(f"Training completed without best checkpoint: {best_source}")
    shutil.copy2(best_source, args.models_dir / "best.pt")
    if last_source.is_file():
        shutil.copy2(last_source, args.models_dir / "last.pt")
    payload["training"] = {"duration_seconds": duration, "best_checkpoint": str(args.models_dir / "best.pt"), "last_checkpoint": str(args.models_dir / "last.pt"), "run_directory": str(run_dir), "test_partition_accessed": False}
    (args.models_dir / "experiment_metadata.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["training"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
