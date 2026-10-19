from __future__ import annotations

from app.schemas.grading_forecast import (
    DecisionEnum,
    GradeEnum,
    RecommendationResult,
    TrendEnum,
    UrgencyLevelEnum,
)

LIMITATION_NOTE = (
    "Camera-based visual estimate only. Laboratory tests are required for full official quality certification."
)

_RULE_TABLE: dict[tuple[GradeEnum, TrendEnum], DecisionEnum] = {
    (GradeEnum.grade_1, TrendEnum.upward): DecisionEnum.wait_or_target_export_buyer,
    (GradeEnum.grade_1, TrendEnum.stable): DecisionEnum.sell_export,
    (GradeEnum.grade_1, TrendEnum.downward): DecisionEnum.sell_soon,
    (GradeEnum.grade_2, TrendEnum.upward): DecisionEnum.wait_shortly,
    (GradeEnum.grade_2, TrendEnum.stable): DecisionEnum.monitor,
    (GradeEnum.grade_2, TrendEnum.downward): DecisionEnum.sell_soon,
    (GradeEnum.grade_3, TrendEnum.upward): DecisionEnum.sort_or_process,
    (GradeEnum.grade_3, TrendEnum.stable): DecisionEnum.process_local,
    (GradeEnum.grade_3, TrendEnum.downward): DecisionEnum.process_or_sell_immediately,
}

_MESSAGE_BY_DECISION: dict[DecisionEnum, str] = {
    DecisionEnum.wait_or_target_export_buyer: (
        "Grade 1 and prices are rising. If storage is safe, wait a bit or target an export buyer."
    ),
    DecisionEnum.sell_export: (
        "Grade 1 and the price is stable. You can sell to an export buyer after lab checks."
    ),
    DecisionEnum.sell_soon: (
        "The price trend is going down. Sell soon to reduce the risk of a lower price."
    ),
    DecisionEnum.wait_shortly: (
        "Prices are rising. Wait a short time if storage conditions are good."
    ),
    DecisionEnum.monitor: (
        "The price is stable. Monitor the market and decide based on your storage capacity."
    ),
    DecisionEnum.sort_or_process: (
        "Grade 3 is not ideal for export. Sort/clean the batch or process it before selling."
    ),
    DecisionEnum.process_local: (
        "Grade 3 is not ideal for export. Consider processing and selling in the local market."
    ),
    DecisionEnum.process_or_sell_immediately: (
        "Grade 3 and prices are falling. Process or sell immediately to avoid further loss."
    ),
}

_SUGGESTED_ACTION_BY_DECISION: dict[DecisionEnum, str] = {
    DecisionEnum.wait_or_target_export_buyer: "Wait if storage is safe; contact an export buyer.",
    DecisionEnum.sell_export: "Prepare for export sale and confirm required lab tests.",
    DecisionEnum.sell_soon: "Sell soon, especially if storage is limited.",
    DecisionEnum.wait_shortly: "Wait briefly and recheck the price trend soon.",
    DecisionEnum.monitor: "Monitor prices (e.g., weekly) and decide based on storage.",
    DecisionEnum.sort_or_process: "Sort/clean and remove defects, then consider processing.",
    DecisionEnum.process_local: "Process and sell locally for better value than raw selling.",
    DecisionEnum.process_or_sell_immediately: "Process or sell immediately to reduce losses.",
}

_URGENCY_BY_DECISION: dict[DecisionEnum, UrgencyLevelEnum] = {
    DecisionEnum.sell_soon: UrgencyLevelEnum.high,
    DecisionEnum.process_or_sell_immediately: UrgencyLevelEnum.high,
    DecisionEnum.sort_or_process: UrgencyLevelEnum.medium,
    DecisionEnum.process_local: UrgencyLevelEnum.medium,
    DecisionEnum.sell_export: UrgencyLevelEnum.medium,
    DecisionEnum.wait_or_target_export_buyer: UrgencyLevelEnum.low,
    DecisionEnum.wait_shortly: UrgencyLevelEnum.low,
    DecisionEnum.monitor: UrgencyLevelEnum.low,
}


def build_recommendation(
    *,
    grade: GradeEnum,
    trend: TrendEnum,
    quality_score: float | None = None,
    current_price_lkr_per_kg: int | None = None,
    predicted_price_lkr_per_kg: int | None = None,
) -> RecommendationResult:
    decision = _RULE_TABLE.get((grade, trend), DecisionEnum.monitor)
    message = _MESSAGE_BY_DECISION.get(decision, "Monitor the market and decide based on storage.")
    suggested_action = _SUGGESTED_ACTION_BY_DECISION.get(decision, "Monitor the market.")
    urgency_level = _URGENCY_BY_DECISION.get(decision, UrgencyLevelEnum.low)

    explanation: list[str] = [
        f"Predicted grade: {grade.value}. Forecast trend: {trend.value}.",
    ]

    if quality_score is not None:
        explanation.append(f"Quality score: {float(quality_score):.1f}/100.")
    else:
        explanation.append("Quality score not provided; using grade and trend only.")

    if (
        current_price_lkr_per_kg is not None
        and predicted_price_lkr_per_kg is not None
        and len(explanation) < 4
    ):
        delta = int(predicted_price_lkr_per_kg) - int(current_price_lkr_per_kg)
        if delta == 0:
            explanation.append(f"Predicted market price: {int(predicted_price_lkr_per_kg)} LKR/kg.")
        else:
            explanation.append(
                "Current: "
                f"{int(current_price_lkr_per_kg)} LKR/kg -> "
                f"Predicted market price: {int(predicted_price_lkr_per_kg)} LKR/kg "
                f"({delta:+d})."
            )

    return RecommendationResult(
        decision=decision,
        message=message,
        explanation=explanation[:4],
        urgency_level=urgency_level,
        suggested_action=suggested_action,
        limitation_note=LIMITATION_NOTE,
    )
