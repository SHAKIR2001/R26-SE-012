from __future__ import annotations

from flask import Blueprint, request, jsonify

from predictors.ai.config import DATA_MAP, MODEL_REGISTRY
from predictors.ai.predictor import predictor

bp = Blueprint("ai_vision", __name__, url_prefix="/vision")

def _read_target():
    # Accept either 'image' or 'target' as the field name
    for field in ("image", "target"):
        f = request.files.get(field)
        if f and f.filename:
            return f.read()
    return None


@bp.post("/<model_name>")
def predict_vision(model_name: str):
    """
    Hidden GPT-4o few-shot endpoint.
    Reference images are auto-loaded from the data folder — only send the target.

    Field:
      image  (or 'target') — image to classify (jpg / png / webp / heic)
    """
    if model_name not in MODEL_REGISTRY:
        return jsonify({"error": f"Unknown model '{model_name}'. Valid: {list(MODEL_REGISTRY)}"}), 404

    target_bytes = _read_target()
    if target_bytes is None:
        return jsonify({"error": "Missing image field. Send file as 'image' or 'target'"}), 400

    cfg = MODEL_REGISTRY[model_name]

    try:
        result = predictor.predict(model_name, cfg.CLASSES, target_bytes)
        return jsonify({"model": model_name, "description": cfg.DESCRIPTION, **result}), 200
    except FileNotFoundError as e:
        return jsonify({"error": f"Reference data missing: {str(e)}"}), 503
    except EnvironmentError as e:
        return jsonify({"error": str(e)}), 503
    except Exception:
        return jsonify({
            "error": "Could not recognize the image. Please upload a clear, relevant pepper image.",
        }), 400


@bp.get("/<model_name>/info")
def info(model_name: str):
    """Shows classes and how many reference images are loaded per class."""
    if model_name not in MODEL_REGISTRY:
        return jsonify({"error": f"Unknown model '{model_name}'"}), 404

    import os
    class_info = {
        cls: len([f for f in os.listdir(folder) if not f.startswith(".")])
        for cls, folder in DATA_MAP[model_name].items()
    }
    return jsonify({
        "model":       model_name,
        "description": MODEL_REGISTRY[model_name].DESCRIPTION,
        "classes":     class_info,
        "usage":       f"POST /vision/{model_name}  — field: target (image file)",
    }), 200
