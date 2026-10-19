"""Pure Phase 3 quality and decision logic for the frozen V3 YOLO model."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

import cv2
import numpy as np


class Decision(str, Enum):
    GRADE_1 = "GRADE_1"
    GRADE_2 = "GRADE_2"
    POOR_IMAGE = "POOR_IMAGE"
    NO_PEPPER = "NO_PEPPER"
    UNCERTAIN_GRADE = "UNCERTAIN_GRADE"


MESSAGES = {
    Decision.GRADE_1: "Pepper sample detected: Grade 1.",
    Decision.GRADE_2: "Pepper sample detected: Grade 2.",
    Decision.POOR_IMAGE: "Image quality is insufficient. Please retake the photo in good light and focus.",
    Decision.NO_PEPPER: "No valid pepper sample was detected. Please photograph the harvested pepper sample.",
    Decision.UNCERTAIN_GRADE: "The pepper sample was detected, but the grade is uncertain. Please retake the photo.",
}


@dataclass(frozen=True)
class FrozenThresholds:
    minimum_blur_variance: float
    minimum_brightness: float
    minimum_dimension: int
    minimum_box_area_ratio: float
    detection_confidence: float
    grade_confidence: float
    grade_margin: float


def read_image(path: str | Path) -> np.ndarray:
    payload = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unreadable image: {path}")
    return image


def quality_scores(path: str | Path) -> dict:
    image = read_image(path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    return {
        "width": int(width),
        "height": int(height),
        "minimum_dimension": int(min(width, height)),
        "brightness": float(gray.mean()),
        "blur_laplacian_variance": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
    }


def decide(record: dict, thresholds: FrozenThresholds) -> dict:
    quality = record["quality"]
    reason = None
    decision = None
    if quality["minimum_dimension"] < thresholds.minimum_dimension:
        decision, reason = Decision.POOR_IMAGE, "resolution_below_minimum"
    elif quality["brightness"] < thresholds.minimum_brightness:
        decision, reason = Decision.POOR_IMAGE, "brightness_below_minimum"
    elif quality["blur_laplacian_variance"] < thresholds.minimum_blur_variance:
        decision, reason = Decision.POOR_IMAGE, "blur_variance_below_minimum"
    elif record["raw_prediction"] is None or record["top_confidence"] < thresholds.detection_confidence:
        decision, reason = Decision.NO_PEPPER, "no_detection_above_threshold"
    elif record["box_area_ratio"] < thresholds.minimum_box_area_ratio:
        decision, reason = Decision.POOR_IMAGE, "detected_sample_area_below_minimum"
    elif record["top_confidence"] < thresholds.grade_confidence:
        decision, reason = Decision.UNCERTAIN_GRADE, "grade_confidence_below_minimum"
    elif record["class_margin"] < thresholds.grade_margin:
        decision, reason = Decision.UNCERTAIN_GRADE, "grade_margin_below_minimum"
    else:
        decision = Decision.GRADE_1 if record["raw_prediction"] == 0 else Decision.GRADE_2
    return {
        "decision": decision.value,
        "message": MESSAGES[decision],
        "grade": "V3 Grade 1" if decision == Decision.GRADE_1 else "V3 Grade 2" if decision == Decision.GRADE_2 else None,
        "model_confidence": record["top_confidence"],
        "detection_confidence": record["top_confidence"],
        "class_margin": record["class_margin"],
        "quality_scores": quality,
        "rejection_reason": reason,
        "bbox_xyxy": record["box_xyxy"],
        "thresholds": asdict(thresholds),
    }
