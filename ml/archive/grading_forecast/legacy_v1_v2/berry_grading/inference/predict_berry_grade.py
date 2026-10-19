from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _softmax(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.float32)
    x = x - np.max(x, axis=-1, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=-1, keepdims=True)


def _resize(img: Image.Image, size: tuple[int, int] = (224, 224)) -> Image.Image:
    target_w, target_h = size
    img = img.convert("RGB")
    w, h = img.size
    if w <= 0 or h <= 0:
        raise ValueError("Invalid image dimensions.")
    return img.resize((target_w, target_h), resample=Image.BILINEAR)


def _load_class_names(models_dir: Path) -> list[str]:
    p = models_dir / "class_names.json"
    if p.exists():
        return list(json.loads(p.read_text(encoding="utf-8")))
    return ["Grade 1", "Grade 2", "Grade 3"]


def _predict_with_onnx(onnx_path: Path, image_arr: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    import onnxruntime as ort

    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    input_name = sess.get_inputs()[0].name
    outputs = sess.run(None, {input_name: image_arr})
    out = outputs[0]
    meta = {"input_name": input_name, "output_count": len(outputs)}
    return np.asarray(out), meta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Predict pepper berry grade from an image using ONNX runtime.")
    parser.add_argument("image", type=Path, help="Path to input image.")
    parser.add_argument("--model", type=Path, default=None, help="Path to berry_mobilenetv2_best.onnx.")
    parser.add_argument("--class-names", type=Path, default=None, help="Path to class_names.json. Defaults beside --model.")
    parser.add_argument("--topk", type=int, default=3, help="Top-k to print (default 3).")
    parser.add_argument("--runs", type=int, default=30, help="Timing runs (after warmup).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate image/model/class-name paths without running ONNX inference.",
    )
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    default_models_dir = repo_root / "ml" / "grading_forecast" / "berry_grading" / "models"
    onnx_path = args.model or (default_models_dir / "berry_mobilenetv2_best.onnx")
    class_names_path = args.class_names or (onnx_path.parent / "class_names.json")
    models_dir = class_names_path.parent

    if args.dry_run:
        payload = {
            "mode": "dry_run",
            "image_path": str(args.image),
            "image_exists": args.image.exists(),
            "onnx_model_path": str(onnx_path),
            "onnx_model_exists": onnx_path.exists(),
            "class_names_path": str(class_names_path),
            "class_names_exists": class_names_path.exists(),
        }
        print(json.dumps(payload, indent=2))
        return 0

    if not onnx_path.exists():
        print(f"Missing ONNX model: {onnx_path}")
        return 2

    class_names = _load_class_names(models_dir)

    if not args.image.exists():
        print(f"Missing image: {args.image}")
        return 3

    with Image.open(args.image) as img:
        img224 = _resize(img, (224, 224))
    # IMPORTANT:
    # The exported ONNX graph includes the Keras MobileNetV2 `preprocess_input` operation.
    # Therefore, feed raw 0..255 float32 RGB into the model (do NOT pre-scale to [-1, 1]).
    arr_0_255 = np.asarray(img224, dtype=np.float32)
    x = arr_0_255[None, ...]  # (1,224,224,3)

    # Predict
    logits_or_probs, meta = _predict_with_onnx(onnx_path, x)
    vec = logits_or_probs.reshape(-1).astype(np.float32)
    if vec.size != len(class_names):
        # If output isn't already probs for 3 classes, apply softmax over last dim.
        probs = _softmax(vec)
    else:
        probs = vec
        # Normalize if needed.
        s = float(np.sum(probs))
        if not math.isfinite(s) or s <= 0:
            probs = _softmax(vec)
        else:
            probs = probs / s

    probs = probs.astype(float)
    idx = int(np.argmax(probs))
    confidence = float(probs[idx])

    out = {
        "predicted_grade": class_names[idx],
        "confidence": round(confidence, 4),
        "probabilities": {class_names[i]: round(float(probs[i]), 6) for i in range(min(len(class_names), probs.shape[0]))},
        "meta": {"onnx": str(onnx_path), **meta},
    }

    # Timing (single-image)
    times: list[float] = []
    for _ in range(5):
        _ = _predict_with_onnx(onnx_path, x)
    for _ in range(max(1, int(args.runs))):
        t0 = time.perf_counter()
        _ = _predict_with_onnx(onnx_path, x)
        times.append((time.perf_counter() - t0) * 1000.0)
    times_sorted = sorted(times)
    out["timing_ms"] = {
        "runs": int(args.runs),
        "avg": round(float(sum(times) / len(times)), 3),
        "p95": round(float(times_sorted[int(0.95 * (len(times_sorted) - 1))]), 3),
        "min": round(float(times_sorted[0]), 3),
    }

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
