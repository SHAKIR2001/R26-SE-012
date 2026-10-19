from __future__ import annotations

import os
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.services.grading_forecast.price_forecast_service import (
    EVAL_MIN_RECORDS,
    GRADE_2_ADJUSTED_FORECAST_MODEL_ID,
    GRADE_2_DEFAULT_DISCOUNT_LKR_PER_KG,
    GRADE_3_UNAVAILABLE_FORECAST_MODEL_ID,
    TrendEnum,
    build_price_forecast,
    clean_price_csv,
    evaluate_one_step_ahead_metrics,
)


def _write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@contextmanager
def _temp_dir() -> Iterator[Path]:
    base = Path(os.getenv("PYTEST_TMPDIR", r"C:\tmp")) / "pepper-tests"
    base.mkdir(parents=True, exist_ok=True)
    d = base / f"price-forecast-{uuid.uuid4().hex}"
    d.mkdir(parents=True, exist_ok=False)
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_clean_price_csv_sorts_dedupes_fills_and_writes() -> None:
    # Keep baseline behavior stable even if real model artifacts exist locally.
    os.environ["GRADING_FORECAST_DISABLE_REAL_MODELS"] = "1"
    with _temp_dir() as tmp_dir:
        raw = tmp_dir / "raw.csv"
        out = tmp_dir / "cleaned.csv"

        _write_csv(
            raw,
            "\n".join(
                [
                    "date,price_lkr_per_kg,market,grade,source",
                    "2024-01-02,1200,local,Grade 2,test",
                    "2024-01-01,1100,local,Grade 2,test",
                    '2024-01-03,"1,300",local,Grade 2,test',
                    "2024-01-04,,local,Grade 2,test",
                    "2024-01-02,1300,local,Grade 2,test",
                    "",
                ]
            ),
        )

        points = clean_price_csv(raw, output_csv_path=out)
        assert out.is_file()
        assert len(points) >= 4
        assert points[0].date.isoformat() == "2024-01-01"
        assert points[-1].date.isoformat() == "2024-01-04"

        # 2024-01-02 is duplicated (1200 & 1300) -> average 1250
        d_0102 = [p for p in points if p.date.isoformat() == "2024-01-02"]
        assert len(d_0102) == 1
        assert d_0102[0].price_lkr_per_kg == 1250

        # 2024-01-04 missing -> filled from prior (2024-01-03)
        assert points[-1].price_lkr_per_kg == points[-2].price_lkr_per_kg


def test_runtime_forecast_uses_grade_1_naive_persistence() -> None:
    os.environ["GRADING_FORECAST_DISABLE_REAL_MODELS"] = "1"
    with _temp_dir() as tmp_dir:
        raw = tmp_dir / "one.csv"
        _write_csv(
            raw,
            "\n".join(
                [
                    "date,price_lkr_per_kg",
                    "2024-01-01,1500",
                    "",
                ]
            ),
        )

        forecast = build_price_forecast(
            seed_hint="x",
            grade="Grade 1",
            csv_path_override=raw,
            cleaned_output_path_override=(tmp_dir / "cleaned.csv"),
        )
        assert forecast.model == "naive_persistence"
        assert forecast.predicted_price_lkr_per_kg == forecast.current_price_lkr_per_kg
        assert forecast.predicted_price_lkr_per_kg == 1500


def test_runtime_forecast_applies_grade_2_gap_adjustment() -> None:
    os.environ["GRADING_FORECAST_DISABLE_REAL_MODELS"] = "1"
    with _temp_dir() as tmp_dir:
        raw = tmp_dir / "multi.csv"
        _write_csv(
            raw,
            "\n".join(
                [
                    "date,price_lkr_per_kg",
                    "2024-01-01,1000",
                    "2024-01-08,1100",
                    "2024-01-15,1200",
                    "",
                ]
            ),
        )

        forecast = build_price_forecast(
            seed_hint="x",
            grade="Grade 2",
            csv_path_override=raw,
            cleaned_output_path_override=(tmp_dir / "cleaned.csv"),
        )
        assert forecast.model == GRADE_2_ADJUSTED_FORECAST_MODEL_ID
        assert forecast.current_price_lkr_per_kg == 1200 - GRADE_2_DEFAULT_DISCOUNT_LKR_PER_KG
        assert forecast.predicted_price_lkr_per_kg == forecast.current_price_lkr_per_kg
        assert forecast.trend == TrendEnum.stable


def test_runtime_forecast_marks_grade_3_price_unavailable() -> None:
    os.environ["GRADING_FORECAST_DISABLE_REAL_MODELS"] = "1"
    with _temp_dir() as tmp_dir:
        raw = tmp_dir / "multi.csv"
        _write_csv(
            raw,
            "\n".join(
                [
                    "date,price_lkr_per_kg",
                    "2024-01-01,1000",
                    "2024-01-08,1100",
                    "2024-01-15,1200",
                    "",
                ]
            ),
        )

        forecast = build_price_forecast(
            seed_hint="x",
            grade="Grade 3",
            csv_path_override=raw,
            cleaned_output_path_override=(tmp_dir / "cleaned.csv"),
        )
        assert forecast.model == GRADE_3_UNAVAILABLE_FORECAST_MODEL_ID
        assert forecast.current_price_lkr_per_kg == 0
        assert forecast.predicted_price_lkr_per_kg == 0
        assert forecast.trend == TrendEnum.stable


def test_metrics_are_null_when_insufficient_records() -> None:
    os.environ["GRADING_FORECAST_DISABLE_REAL_MODELS"] = "1"
    with _temp_dir() as tmp_dir:
        raw = tmp_dir / "few.csv"
        rows = ["date,price_lkr_per_kg"]
        for i in range(EVAL_MIN_RECORDS - 1):
            rows.append(f"2024-01-{i+1:02d},{1000 + (i * 10)}")
        _write_csv(raw, "\n".join(rows) + "\n")

        points = clean_price_csv(raw, output_csv_path=(tmp_dir / "cleaned.csv"))
        metrics = evaluate_one_step_ahead_metrics(points)
        assert metrics.mae is None
        assert metrics.rmse is None


def test_metrics_are_floats_when_enough_records() -> None:
    os.environ["GRADING_FORECAST_DISABLE_REAL_MODELS"] = "1"
    with _temp_dir() as tmp_dir:
        raw = tmp_dir / "enough.csv"
        rows = ["date,price_lkr_per_kg"]
        for i in range(EVAL_MIN_RECORDS):
            rows.append(f"2024-01-{i+1:02d},{1000 + (i * 10)}")
        _write_csv(raw, "\n".join(rows) + "\n")

        points = clean_price_csv(raw, output_csv_path=(tmp_dir / "cleaned.csv"))
        metrics = evaluate_one_step_ahead_metrics(points)
        assert isinstance(metrics.mae, float)
        assert isinstance(metrics.rmse, float)
        assert metrics.mae >= 0.0
        assert metrics.rmse >= 0.0


def test_unavailable_when_override_path_missing() -> None:
    os.environ["GRADING_FORECAST_DISABLE_REAL_MODELS"] = "1"
    with _temp_dir() as tmp_dir:
        missing = tmp_dir / "does_not_exist.csv"
        forecast = build_price_forecast(
            seed_hint="seed",
            csv_path_override=missing,
            cleaned_output_path_override=(tmp_dir / "cleaned.csv"),
        )
        assert forecast.model == "forecast_unavailable"


def test_runtime_prefers_naive_persistence_even_when_model_override_is_provided() -> None:
    os.environ.pop("GRADING_FORECAST_DISABLE_REAL_MODELS", None)

    with _temp_dir() as tmp_dir:
        raw = tmp_dir / "series.csv"
        rows = ["date,price_lkr_per_kg"]
        base = 1000
        for i in range(20):
            rows.append(f"2024-01-{1+i:02d},{base + (i * 10)}")
        _write_csv(raw, "\n".join(rows) + "\n")

        points = clean_price_csv(raw, output_csv_path=(tmp_dir / "cleaned.csv"))
        assert len(points) >= 8

        models_dir = tmp_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        (models_dir / "forecast_model.joblib").write_text("unused", encoding="utf-8")
        (models_dir / "forecast_features.json").write_text("{}", encoding="utf-8")

        forecast = build_price_forecast(
            seed_hint="x",
            grade="Grade 1",
            csv_path_override=raw,
            cleaned_output_path_override=(tmp_dir / "cleaned2.csv"),
            models_dir_override=models_dir,
        )
        assert forecast.model == "naive_persistence"
        assert forecast.current_price_lkr_per_kg > 0
        assert forecast.predicted_price_lkr_per_kg > 0
        assert forecast.trend in {TrendEnum.upward, TrendEnum.downward, TrendEnum.stable}
