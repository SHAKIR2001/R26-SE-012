"""Reproducibly export the frozen Phase 3 follow-up YOLO checkpoint."""

from __future__ import annotations

import json
import platform
from pathlib import Path

import onnx
import torch
import ultralytics
from ultralytics import YOLO

from .config import ROOT, load_config, repo_path, sha256


def _set_metadata(model: onnx.ModelProto, values: dict[str, str]) -> None:
    current = {item.key: item.value for item in model.metadata_props}
    current.update(values)
    del model.metadata_props[:]
    for key in sorted(current):
        item = model.metadata_props.add()
        item.key, item.value = key, current[key]


def export() -> dict:
    config = load_config()
    settings = config["grading"]
    source = repo_path(settings["source_pt"])
    target = repo_path(settings["onnx"])
    if sha256(source) != settings["source_pt_sha256"]:
        raise RuntimeError("Frozen source checkpoint hash mismatch")
    exported = Path(YOLO(str(source)).export(
        format="onnx", imgsz=int(settings["image_size"]), opset=int(settings["opset"]),
        simplify=True, dynamic=False, nms=True, batch=1, device="cpu",
        conf=float(settings["export_confidence_floor"]), iou=float(settings["export_iou_threshold"]),
        max_det=int(settings["maximum_detections"]),
    ))
    if exported.resolve() != target.resolve():
        raise RuntimeError(f"Unexpected export target: {exported}")
    graph = onnx.load(target)
    _set_metadata(graph, {
        "date": config["experiment"]["deterministic_timestamp_utc"],
        "phase7_source_pt": settings["source_pt"],
        "phase7_source_pt_sha256": settings["source_pt_sha256"],
        "phase7_preprocessing": "Ultralytics letterbox to 640 square, RGB, float32 divided by 255, BCHW",
        "phase7_output": "[batch,300,6] rows [x1,y1,x2,y2,confidence,class_id], zero padded",
    })
    onnx.checker.check_model(graph)
    onnx.save(graph, target)
    manifest = {
        "experiment_id": config["experiment"]["id"], "source_pt": settings["source_pt"],
        "source_pt_sha256": sha256(source), "onnx_path": settings["onnx"], "onnx_sha256": sha256(target),
        "python": platform.python_version(), "ultralytics": ultralytics.__version__, "pytorch": torch.__version__,
        "onnx_version": onnx.__version__, "opset": settings["opset"], "image_size": settings["image_size"],
        "export_timestamp_utc": config["experiment"]["deterministic_timestamp_utc"],
        "class_names": settings["class_names"], "input": {"name": settings["input_name"], "shape": settings["input_shape"]},
        "output": {"name": settings["output_name"], "shape": settings["output_shape"], "nms_embedded": True},
        "preprocessing": "Ultralytics letterbox, RGB, float32 / 255, BCHW",
    }
    output = ROOT / "ml/grading_forecast/evaluation/phase7/phase7_model_manifest.json"
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(export(), indent=2))
