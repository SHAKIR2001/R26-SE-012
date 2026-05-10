from __future__ import annotations

from flask import request, jsonify

from config import ALLOWED_EXTENSIONS
from predictors.base import BasePredictor


def get_image_bytes() -> tuple[bytes | None, str | None]:
    if "image" not in request.files:
        return None, "No 'image' field in request"
    file = request.files["image"]
    if not file.filename:
        return None, "Empty filename"
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return None, f"Unsupported file type '.{ext}'. Allowed: {ALLOWED_EXTENSIONS}"
    return file.read(), None


def run_prediction(predictor: BasePredictor, model_name: str):
    image_bytes, error = get_image_bytes()
    if error:
        return jsonify({"error": error}), 400
    try:
        result = predictor.predict(image_bytes)
        return jsonify({"model": model_name, "description": predictor.description, **result}), 200
    except ValueError:
        return jsonify({
            "error": "Could not recognize the image. Please upload a clear, relevant pepper image.",
        }), 400
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500
