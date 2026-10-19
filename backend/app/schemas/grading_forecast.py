"""Stable API contract for the frozen Phase 7 decision-support workflow.

The enums and validators in this module are intentionally stricter than the
retired legacy response models below. An invalid or internally inconsistent
integrated result must be withheld instead of being presented as advice.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

class Phase7GradingStatus(str, Enum):
    accepted = "ACCEPTED"
    rejected = "REJECTED"
    uncertain = "UNCERTAIN"


class Phase7GradingDecision(str, Enum):
    grade_1 = "GRADE_1"
    grade_2 = "GRADE_2"
    no_pepper = "NO_PEPPER"
    poor_image = "POOR_IMAGE"
    uncertain_grade = "UNCERTAIN_GRADE"
    conflicting_sample_views = "CONFLICTING_SAMPLE_VIEWS"


class Phase7QualityStatus(str, Enum):
    passed = "PASSED"
    failed = "FAILED"
    not_applicable = "NOT_APPLICABLE"


class Phase7DecisionCategory(str, Enum):
    reject = "REJECT"
    uncertain_grade = "UNCERTAIN_GRADE"
    conflicting_sample_views = "CONFLICTING_SAMPLE_VIEWS"
    price_data_unavailable = "PRICE_DATA_UNAVAILABLE"
    forecast_unavailable = "FORECAST_UNAVAILABLE"
    upward_price_outlook = "UPWARD_PRICE_OUTLOOK"
    downward_price_outlook = "DOWNWARD_PRICE_OUTLOOK"
    flat_price_outlook = "FLAT_PRICE_OUTLOOK"
    high_uncertainty_outlook = "HIGH_UNCERTAINTY_OUTLOOK"


class Phase7GradingResult(BaseModel):
    status: Phase7GradingStatus
    decision: Phase7GradingDecision
    grade: str | None = None
    model_confidence: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    detection_confidence: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    class_margin: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    quality_status: Phase7QualityStatus
    rejection_reason: str | None = None
    physical_sample_id: str | None = None
    confidence_interpretation: str
    image_decisions: list[dict] | None = None
    aggregation: dict | None = None


class Phase7ForecastInterval(BaseModel):
    lower: float = Field(ge=0.0, allow_inf_nan=False)
    upper: float = Field(ge=0.0, allow_inf_nan=False)
    label: str
    probability_claim: bool

    @model_validator(mode="after")
    def validate_bounds(self) -> "Phase7ForecastInterval":
        """Reject reversed ranges and any claim of calibrated probability."""
        if self.lower > self.upper:
            raise ValueError("Forecast interval lower bound exceeds upper bound")
        if self.probability_claim:
            raise ValueError("Phase 7 intervals must not claim calibrated probability")
        return self


class Phase7MarketResult(BaseModel):
    status: str
    source: str | None = None
    source_organization: str | None = None
    source_url: str | None = None
    unit: str | None = None
    price_grade: str | None = None
    model_scope: str | None = None
    latest_reference_date: str | None = None
    latest_reference_price: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    latest_price_interpretation: str | None = None
    previous_reference_price: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    latest_observed_return: float | None = Field(default=None, allow_inf_nan=False)
    forecast_target_date: str | None = None
    forecast_log_return: float | None = Field(default=None, allow_inf_nan=False)
    forecast_return: float | None = Field(default=None, allow_inf_nan=False)
    forecast_price: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    forecast_direction: str | None = None
    forecast_interval: Phase7ForecastInterval | None = None
    persistence_price: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    model_vs_persistence: str | None = None
    forecast_signal: str | None = None
    evidence_partition: str | None = None


class Phase7DecisionSupport(BaseModel):
    category: Phase7DecisionCategory
    summary: str
    limitations: list[str]


class Phase7Runtime(BaseModel):
    grading: str
    price: str
    mobile: str
    tflite: str


class Phase7AnalyzeResponse(BaseModel):
    schema_version: Literal["phase6_decision_support_v1"]
    grading: Phase7GradingResult
    market: Phase7MarketResult
    decision_support: Phase7DecisionSupport
    trace: dict
    runtime: Phase7Runtime

    @model_validator(mode="after")
    def validate_rejection_first_contract(self) -> "Phase7AnalyzeResponse":
        """Enforce Phase 6 semantics at the API boundary.

        Rejected or uncertain grading stops before pricing, and accepted
        market evidence must use the exact Grade 1 or Grade 2 route selected by
        the frozen research workflow. This protects clients from accidental
        schema drift or a wrong-grade price response.
        """
        category = self.decision_support.category
        unavailable_values = (
            self.market.price_grade,
            self.market.latest_reference_price,
            self.market.forecast_price,
            self.market.forecast_direction,
            self.market.forecast_interval,
        )
        if self.grading.status in {
            Phase7GradingStatus.rejected,
            Phase7GradingStatus.uncertain,
        }:
            if self.market.status == "AVAILABLE" or any(value is not None for value in unavailable_values):
                raise ValueError("Rejected or uncertain grading cannot include market output")

        if category == Phase7DecisionCategory.reject and self.grading.status != Phase7GradingStatus.rejected:
            raise ValueError("REJECT requires rejected grading status")
        if category in {
            Phase7DecisionCategory.uncertain_grade,
            Phase7DecisionCategory.conflicting_sample_views,
        } and self.grading.status != Phase7GradingStatus.uncertain:
            raise ValueError("Uncertainty category requires uncertain grading status")

        if self.market.status == "AVAILABLE":
            if self.grading.status != Phase7GradingStatus.accepted:
                raise ValueError("Market output requires accepted grading")
            expected_route = {
                "V3 Grade 1": "Grade 1",
                "V3 Grade 2": "Grade 2",
            }.get(self.grading.grade)
            if expected_route is None or self.market.price_grade != expected_route:
                raise ValueError("Invalid grade-specific price route")
            if self.market.latest_reference_price is None or self.market.forecast_price is None:
                raise ValueError("Available market output requires reference and forecast prices")
        return self


class GradeEnum(str, Enum):
    """Legacy model vocabulary retained only for retired endpoints."""
    grade_1 = "Grade 1"
    grade_2 = "Grade 2"
    grade_3 = "Grade 3"


class TrendEnum(str, Enum):
    upward = "upward"
    downward = "downward"
    stable = "stable"


class DecisionEnum(str, Enum):
    wait_or_target_export_buyer = "WAIT_OR_TARGET_EXPORT_BUYER"
    sell_export = "SELL_EXPORT"
    sell_soon = "SELL_SOON"
    wait_shortly = "WAIT_SHORTLY"
    monitor = "MONITOR"
    sort_or_process = "SORT_OR_PROCESS"
    process_local = "PROCESS_LOCAL"
    process_or_sell_immediately = "PROCESS_OR_SELL_IMMEDIATELY"


class UrgencyLevelEnum(str, Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"


class ImageAnalysis(BaseModel):
    image_id: str
    processed: bool
    note: str


class VisualFeatures(BaseModel):
    color_uniformity_score: float = Field(..., ge=0.0, le=1.0)
    dark_berry_ratio: float = Field(..., ge=0.0, le=1.0)
    light_berry_ratio: float = Field(..., ge=0.0, le=1.0)
    texture_score: float = Field(..., ge=0.0, le=1.0)
    defect_ratio: float = Field(..., ge=0.0, le=1.0)
    cleanliness_score: float = Field(..., ge=0.0, le=1.0)


class SupportingLabels(BaseModel):
    size_quality: str = Field(..., description="good / medium / poor")
    color_quality: str = Field(..., description="good / medium / poor")
    texture_quality: str = Field(..., description="good / medium / poor")
    broken_level: str = Field(..., description="low / medium / high")
    light_berry_level: str = Field(..., description="low / medium / high")
    pinhead_level: str = Field(..., description="low / medium / high")
    foreign_matter_visible: bool
    mould_visible: bool
    insect_damage_visible: bool


class GradingResult(BaseModel):
    predicted_grade: GradeEnum
    quality_score: float = Field(..., ge=0.0, le=100.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    visual_features: VisualFeatures
    supporting_labels: SupportingLabels
    explanation: list[str]
    limitation: str


class ForecastMetrics(BaseModel):
    mae: float | None = None
    rmse: float | None = None


class ForecastResult(BaseModel):
    model: str
    current_price_lkr_per_kg: int = Field(..., ge=0)
    predicted_price_lkr_per_kg: int = Field(..., ge=0)
    trend: TrendEnum
    forecast_period: str
    metrics: ForecastMetrics


class RecommendationResult(BaseModel):
    decision: DecisionEnum
    message: str
    explanation: list[str]
    urgency_level: UrgencyLevelEnum
    suggested_action: str
    limitation_note: str


class StorageResult(BaseModel):
    saved_to_firebase: bool
    document_id: str | None = None


class AnalyzeResponse(BaseModel):
    status: str
    component: str
    image_analysis: ImageAnalysis
    grading: GradingResult
    forecast: ForecastResult
    recommendation: RecommendationResult
    storage: StorageResult


class GradeOnlyResponse(BaseModel):
    status: str
    component: str
    grading: GradingResult


class PriceForecastResponse(BaseModel):
    status: str
    component: str
    forecast: ForecastResult


class RecommendRequest(BaseModel):
    grade: GradeEnum
    trend: TrendEnum
    quality_score: float | None = Field(default=None, ge=0.0, le=100.0)
    current_price_lkr_per_kg: int | None = Field(default=None, ge=0)
    predicted_price_lkr_per_kg: int | None = Field(default=None, ge=0)


class RecommendResponse(BaseModel):
    status: str
    component: str
    recommendation: RecommendationResult
