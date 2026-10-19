"""Normalize frozen grading decisions and aggregate repeated sample views."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable


ACCEPTED = {"GRADE_1": "V3 Grade 1", "GRADE_2": "V3 Grade 2"}
REJECTED = {"NO_PEPPER", "POOR_IMAGE"}
UNCERTAIN = {"UNCERTAIN_GRADE", "CONFLICTING_SAMPLE_VIEWS"}


@dataclass(frozen=True)
class GradingResult:
    input_id: str
    decision: str
    grade: str | None
    model_confidence: float | None
    detection_confidence: float | None
    class_margin: float | None
    quality_status: str
    rejection_reason: str | None
    physical_sample_id: str | None = None

    @property
    def status(self) -> str:
        if self.decision in ACCEPTED:
            return "ACCEPTED"
        if self.decision in REJECTED:
            return "REJECTED"
        return "UNCERTAIN"


def from_mapping(row: dict) -> GradingResult:
    decision = str(row.get("decision", "")).strip()
    if decision not in set(ACCEPTED) | REJECTED | UNCERTAIN:
        raise ValueError(f"Unsupported grading decision: {decision!r}")
    grade = ACCEPTED.get(decision)
    supplied_grade = str(row.get("grade", "")).strip() or None
    if grade and supplied_grade and supplied_grade != grade:
        raise ValueError(f"Decision/grade mismatch: {decision} versus {supplied_grade}")

    def number(name: str) -> float | None:
        value = row.get(name)
        return None if value in (None, "") else float(value)

    quality_status = "PASSED" if decision in ACCEPTED or decision == "UNCERTAIN_GRADE" else "FAILED" if decision == "POOR_IMAGE" else "NOT_APPLICABLE"
    return GradingResult(
        input_id=str(row.get("image_id") or row.get("input_id") or ""), decision=decision, grade=grade,
        model_confidence=number("model_confidence") if row.get("model_confidence") not in (None, "") else number("top_confidence"),
        detection_confidence=number("detection_confidence") if row.get("detection_confidence") not in (None, "") else number("top_confidence"),
        class_margin=number("class_margin"), quality_status=quality_status,
        rejection_reason=str(row.get("rejection_reason", "")).strip() or None,
        physical_sample_id=str(row.get("physical_sample_id", "")).strip() or None,
    )


def aggregate_sample(results: Iterable[GradingResult], sample_id: str) -> tuple[GradingResult, dict]:
    views = list(results)
    if not views:
        raise ValueError("At least one image-level result is required")
    accepted = [item for item in views if item.status == "ACCEPTED"]
    accepted_grades = {item.grade for item in accepted}
    if not accepted:
        decision = "UNCERTAIN_GRADE" if any(item.status == "UNCERTAIN" for item in views) else "NO_PEPPER"
        aggregate = GradingResult(sample_id, decision, None, None, None, None, "NOT_ESTABLISHED", "no_accepted_sample_view", sample_id)
        return aggregate, {"views": len(views), "accepted_views": 0, "majority_grade": None, "confidence_weighted_grade": None, "conflict": False}
    if len(accepted_grades) != 1:
        aggregate = GradingResult(sample_id, "CONFLICTING_SAMPLE_VIEWS", None, None, None, None, "CONFLICTING", "accepted_views_disagree", sample_id)
        return aggregate, {"views": len(views), "accepted_views": len(accepted), "majority_grade": None, "confidence_weighted_grade": None, "conflict": True}
    votes = Counter(item.grade for item in accepted)
    majority_grade = votes.most_common(1)[0][0]
    weighted = Counter()
    for item in accepted:
        weighted[item.grade] += item.model_confidence or 0.0
    weighted_grade = weighted.most_common(1)[0][0]
    if majority_grade != weighted_grade:
        aggregate = GradingResult(sample_id, "CONFLICTING_SAMPLE_VIEWS", None, None, None, None, "CONFLICTING", "aggregation_methods_disagree", sample_id)
        return aggregate, {"views": len(views), "accepted_views": len(accepted), "majority_grade": majority_grade, "confidence_weighted_grade": weighted_grade, "conflict": True}
    decision = "GRADE_1" if majority_grade == "V3 Grade 1" else "GRADE_2"
    aggregate = GradingResult(
        sample_id, decision, majority_grade,
        sum((item.model_confidence or 0.0) for item in accepted) / len(accepted),
        sum((item.detection_confidence or 0.0) for item in accepted) / len(accepted),
        min((item.class_margin for item in accepted if item.class_margin is not None), default=None),
        "PASSED", None, sample_id,
    )
    return aggregate, {"views": len(views), "accepted_views": len(accepted), "majority_grade": majority_grade, "confidence_weighted_grade": weighted_grade, "conflict": False}
