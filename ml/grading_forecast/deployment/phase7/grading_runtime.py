"""ONNX Runtime inference with the frozen Phase 3 decision pipeline."""

from __future__ import annotations

from functools import lru_cache

import cv2
import numpy as np

from ml.grading_forecast.berry_grading.quality.phase3.decision_pipeline import FrozenThresholds, decide
from ml.grading_forecast.decision_support.phase6.grading_adapter import GradingResult

from .config import load_config, repo_path, sha256


class GradingRuntimeError(RuntimeError):
    pass


def _thresholds() -> FrozenThresholds:
    frozen = load_config()["grading"]
    import json
    payload = json.loads(repo_path(frozen["decision_config"]).read_text(encoding="utf-8"))
    return FrozenThresholds(**payload["thresholds"])


@lru_cache(maxsize=1)
def session():
    try:
        import onnxruntime as ort
        settings = load_config()["grading"]
        model = repo_path(settings["onnx"])
        if not model.is_file():
            raise GradingRuntimeError("Frozen V3 ONNX artifact is unavailable")
        return ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
    except GradingRuntimeError:
        raise
    except Exception as exc:
        raise GradingRuntimeError("Frozen V3 ONNX runtime initialization failed") from exc


def initialize_grading_runtime() -> None:
    session()


def _decode(image_bytes: bytes) -> np.ndarray:
    try:
        # Match the frozen Phase 3 and Ultralytics OpenCV decode path exactly.
        # Pillow may expose the stored pixel orientation differently for images
        # carrying EXIF orientation metadata.
        bgr = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("OpenCV decode returned no image")
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    except Exception as exc:
        raise GradingRuntimeError("Image is unreadable") from exc


def _quality(rgb: np.ndarray) -> dict:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    height, width = gray.shape
    return {"width": int(width), "height": int(height), "minimum_dimension": int(min(width, height)),
            "brightness": float(gray.mean()), "blur_laplacian_variance": float(cv2.Laplacian(gray, cv2.CV_64F).var())}


def _letterbox(rgb: np.ndarray, size: int) -> tuple[np.ndarray, float, tuple[float, float]]:
    height, width = rgb.shape[:2]
    scale = min(size / height, size / width)
    resized = cv2.resize(rgb, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((size, size, 3), 114, dtype=np.uint8)
    pad_x, pad_y = (size - resized.shape[1]) / 2, (size - resized.shape[0]) / 2
    left, top = round(pad_x - 0.1), round(pad_y - 0.1)
    canvas[top:top + resized.shape[0], left:left + resized.shape[1]] = resized
    tensor = np.ascontiguousarray(canvas.transpose(2, 0, 1)[None], dtype=np.float32) / 255.0
    return tensor, scale, (left, top)


def infer_raw(image_bytes: bytes) -> dict:
    rgb = _decode(image_bytes)
    settings = load_config()["grading"]
    tensor, scale, padding = _letterbox(rgb, int(settings["image_size"]))
    try:
        output = np.asarray(session().run([settings["output_name"]], {settings["input_name"]: tensor})[0])[0]
    except Exception as exc:
        raise GradingRuntimeError("Frozen V3 ONNX inference failed") from exc
    valid = output[output[:, 4] > 0]
    class_conf = {0: 0.0, 1: 0.0}
    best = None
    for row in valid:
        cls, confidence = int(round(float(row[5]))), float(row[4])
        if cls not in class_conf:
            continue
        class_conf[cls] = max(class_conf[cls], confidence)
        if best is None or confidence > best["confidence"]:
            x1, y1, x2, y2 = map(float, row[:4])
            left, top = padding
            height, width = rgb.shape[:2]
            box = [max(0.0, min(width, (x1-left)/scale)), max(0.0, min(height, (y1-top)/scale)),
                   max(0.0, min(width, (x2-left)/scale)), max(0.0, min(height, (y2-top)/scale))]
            best = {"class": cls, "confidence": confidence, "box": box}
    top_class = None if best is None else best["class"]
    top_conf = 0.0 if best is None else best["confidence"]
    other_conf = 0.0 if top_class is None else class_conf[1-top_class]
    box = None if best is None else best["box"]
    height, width = rgb.shape[:2]
    area = 0.0 if box is None else max(0.0, box[2]-box[0]) * max(0.0, box[3]-box[1]) / (width*height)
    return {"raw_prediction": top_class, "top_confidence": top_conf, "runner_up_confidence": other_conf,
            "class_margin": top_conf-other_conf, "box_xyxy": box, "box_area_ratio": area,
            "quality": _quality(rgb), "detection_count": int(len(valid))}


def grade_image(image_bytes: bytes, input_id: str) -> tuple[GradingResult, dict]:
    raw = infer_raw(image_bytes)
    outcome = decide(raw, _thresholds())
    result = GradingResult(input_id=input_id, decision=outcome["decision"], grade=outcome["grade"],
        model_confidence=outcome["model_confidence"], detection_confidence=outcome["detection_confidence"],
        class_margin=outcome["class_margin"], quality_status="FAILED" if outcome["decision"] == "POOR_IMAGE" else "PASSED",
        rejection_reason=outcome["rejection_reason"], physical_sample_id=None)
    return result, {**raw, **outcome}
