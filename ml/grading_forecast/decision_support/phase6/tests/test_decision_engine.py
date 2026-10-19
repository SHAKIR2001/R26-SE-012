from __future__ import annotations

import unittest

from ml.grading_forecast.decision_support.phase6.decision_engine import decide
from ml.grading_forecast.decision_support.phase6.grading_adapter import GradingResult, aggregate_sample
from ml.grading_forecast.decision_support.phase6.price_router import MarketForecast


def grading(decision: str, grade: str | None = None) -> GradingResult:
    return GradingResult("test", decision, grade, .8 if grade else None, .8 if grade else None, .5 if grade else None, "PASSED" if grade else "NOT_APPLICABLE", None)


def market(
    grade: str, *, reference: float | None = 100.0, forecast: float | None = 110.0,
    lower: float | None = 105.0, upper: float | None = 115.0,
    comparison: str = "RIDGE_BETTER",
) -> MarketForecast:
    return MarketForecast(
        grade, "2026-01-01", reference, 95.0, .01,
        None if forecast is None else .09531, None if forecast is None else forecast / reference - 1 if reference else None,
        forecast, lower, upper, reference, comparison, "2026-01-08", "logic-test", "LOGIC_TEST",
    )


class DecisionEngineTests(unittest.TestCase):
    def category(self, grade_result, price=None):
        return decide(grade_result, price)["decision_support"]["category"]

    def test_01_non_pepper(self):
        result = decide(grading("NO_PEPPER"), None)
        self.assertEqual(result["decision_support"]["category"], "REJECT")
        self.assertIsNone(result["market"]["forecast_price"])

    def test_02_quality_rejection(self):
        self.assertEqual(self.category(grading("POOR_IMAGE"), None), "REJECT")

    def test_03_uncertain_grade(self):
        self.assertEqual(self.category(grading("UNCERTAIN_GRADE"), None), "UNCERTAIN_GRADE")

    def test_04_grade1_upward(self):
        result = decide(grading("GRADE_1", "V3 Grade 1"), market("Grade 1"))
        self.assertEqual(result["decision_support"]["category"], "UPWARD_PRICE_OUTLOOK")
        self.assertEqual(result["market"]["price_grade"], "Grade 1")

    def test_05_grade1_downward(self):
        self.assertEqual(self.category(grading("GRADE_1", "V3 Grade 1"), market("Grade 1", forecast=90, lower=85, upper=95)), "DOWNWARD_PRICE_OUTLOOK")

    def test_06_grade2_upward(self):
        result = decide(grading("GRADE_2", "V3 Grade 2"), market("Grade 2"))
        self.assertEqual(result["decision_support"]["category"], "UPWARD_PRICE_OUTLOOK")
        self.assertEqual(result["market"]["price_grade"], "Grade 2")

    def test_07_grade2_downward(self):
        self.assertEqual(self.category(grading("GRADE_2", "V3 Grade 2"), market("Grade 2", forecast=90, lower=85, upper=95)), "DOWNWARD_PRICE_OUTLOOK")

    def test_08_flat_uses_phase5_rounding_rule(self):
        result = decide(grading("GRADE_1", "V3 Grade 1"), market("Grade 1", forecast=100.004, lower=100, upper=100, comparison="TIE"))
        self.assertEqual(result["market"]["forecast_direction"], "FLAT")
        self.assertEqual(result["decision_support"]["category"], "FLAT_PRICE_OUTLOOK")

    def test_09_conflicting_multi_image_grades(self):
        aggregate, detail = aggregate_sample([grading("GRADE_1", "V3 Grade 1"), grading("GRADE_2", "V3 Grade 2")], "sample")
        self.assertTrue(detail["conflict"])
        self.assertEqual(self.category(aggregate, None), "CONFLICTING_SAMPLE_VIEWS")

    def test_10_missing_price(self):
        self.assertEqual(self.category(grading("GRADE_1", "V3 Grade 1"), None), "PRICE_DATA_UNAVAILABLE")

    def test_11_missing_forecast(self):
        self.assertEqual(self.category(grading("GRADE_1", "V3 Grade 1"), market("Grade 1", forecast=None, lower=None, upper=None)), "FORECAST_UNAVAILABLE")

    def test_12_wide_interval(self):
        result = decide(grading("GRADE_1", "V3 Grade 1"), market("Grade 1", lower=80, upper=120))
        self.assertEqual(result["market"]["forecast_signal"], "HIGH_UNCERTAINTY")
        self.assertEqual(result["decision_support"]["category"], "HIGH_UNCERTAINTY_OUTLOOK")

    def test_13_persistence_better(self):
        result = decide(grading("GRADE_1", "V3 Grade 1"), market("Grade 1", comparison="PERSISTENCE_BETTER"))
        self.assertEqual(result["market"]["forecast_signal"], "LIMITED_SIGNAL")

    def test_14_ridge_better(self):
        result = decide(grading("GRADE_1", "V3 Grade 1"), market("Grade 1", comparison="RIDGE_BETTER"))
        self.assertEqual(result["market"]["forecast_signal"], "RELATIVE_SUPPORT")

    def test_15_invalid_grade_price_series_mismatch(self):
        with self.assertRaisesRegex(ValueError, "mismatch"):
            decide(grading("GRADE_1", "V3 Grade 1"), market("Grade 2"))


if __name__ == "__main__":
    unittest.main()
