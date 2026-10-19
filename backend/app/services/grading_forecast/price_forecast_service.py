from __future__ import annotations

import csv
import datetime as dt
import hashlib
import math
import random
import re
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.schemas.grading_forecast import ForecastMetrics, ForecastResult, TrendEnum
from app.services.grading_forecast.artifact_service import get_runtime_artifacts

MOVING_AVG_WINDOW = 3
EVAL_MIN_RECORDS = 6
RUNTIME_FORECAST_MODEL_ID = "naive_persistence"
RUNTIME_FORECAST_TARGET_RELATIVE_PATH = (
    Path("data")
    / "processed"
    / "grading_forecast"
    / "price_v2"
    / "national_grade1_average_weekly.csv"
)
RUNTIME_NAIVE_METRICS_RELATIVE_PATH = (
    Path("ml")
    / "grading_forecast"
    / "price_forecasting"
    / "models"
    / "v2"
    / "naive_persistence_metrics.json"
)
GRADE_PRICE_GAP_SOURCE_RELATIVE_PATH = (
    Path("data")
    / "processed"
    / "grading_forecast"
    / "price_v2"
    / "cleaned_price_data_v2.csv"
)
GRADE_2_DEFAULT_DISCOUNT_LKR_PER_KG = 113
GRADE_2_ADJUSTED_FORECAST_MODEL_ID = "naive_persistence_grade2_gap_adjusted"
GRADE_3_UNAVAILABLE_FORECAST_MODEL_ID = "price_unavailable_grade3"


@dataclass(frozen=True)
class PricePoint:
    date: dt.date
    price_lkr_per_kg: int


def _repo_root() -> Path:
    # backend/app/services/grading_forecast/price_forecast_service.py -> repo root
    return Path(__file__).resolve().parents[4]


def _default_input_paths(*, repo_root: Path) -> tuple[Path, Path]:
    real = repo_root / "data" / "raw" / "market_prices" / "black_pepper_prices.csv"
    sample = repo_root / "data" / "raw" / "market_prices" / "sample_black_pepper_prices.csv"
    return real, sample


def _runtime_target_csv(*, repo_root: Path) -> Path:
    artifacts = get_runtime_artifacts()
    if artifacts is not None:
        return artifacts.forecast_data_path

    return repo_root / RUNTIME_FORECAST_TARGET_RELATIVE_PATH


def _runtime_naive_metrics_path(*, repo_root: Path) -> Path:
    artifacts = get_runtime_artifacts()
    if artifacts is not None:
        return artifacts.forecast_metrics_path

    return repo_root / RUNTIME_NAIVE_METRICS_RELATIVE_PATH


def _grade_price_gap_source_csv(*, repo_root: Path) -> Path:
    return repo_root / GRADE_PRICE_GAP_SOURCE_RELATIVE_PATH


def _default_output_path(*, repo_root: Path) -> Path:
    return repo_root / "data" / "processed" / "grading_forecast" / "cleaned_price_data.csv"


def _forecast_models_dir(*, repo_root: Path) -> Path:
    return repo_root / "ml" / "grading_forecast" / "price_forecasting" / "models"


def _default_forecast_series_csv(*, repo_root: Path) -> Path | None:
    """
    Preferred series for real-model forecasting:
    - forecast_training_data.csv (National + Grade 1 + average baseline series)
    - fallback: cleaned_price_data.csv (may contain multiple series)
    """

    p1 = repo_root / "data" / "processed" / "grading_forecast" / "forecast_training_data.csv"
    if p1.is_file():
        return p1
    p2 = repo_root / "data" / "processed" / "grading_forecast" / "cleaned_price_data.csv"
    if p2.is_file():
        return p2
    return None


@lru_cache(maxsize=4)
def _load_forecast_model_bundle(models_dir_override: Path | None = None) -> tuple[object, dict] | None:
    """
    Returns (model, feature_spec) or None if artifacts are missing/unloadable.

    Never raises: the service must fall back to the existing baseline behavior.
    """
    root = _repo_root()

    if os.getenv("GRADING_FORECAST_DISABLE_REAL_MODELS", "").strip().lower() in {"1", "true", "yes"}:
        return None

    artifacts = get_runtime_artifacts()
    if models_dir_override is not None:
        models_dir = models_dir_override
        model_path = models_dir / "forecast_model.joblib"
    elif artifacts is not None:
        models_dir = artifacts.forecast_model_path.parent
        model_path = artifacts.forecast_model_path
    else:
        models_dir = _forecast_models_dir(repo_root=root)
        model_path = models_dir / "forecast_model.joblib"

    spec_path = models_dir / "forecast_features.json"
    if not model_path.is_file() or not spec_path.is_file():
        return None

    try:
        import joblib  # type: ignore
    except Exception:
        return None

    try:
        model = joblib.load(model_path)
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        return model, spec
    except Exception:
        return None


def initialize_forecast_runtime() -> None:
    """Validate the runtime forecast data and metrics during application startup."""

    forecast = build_price_forecast(seed_hint="startup")
    if forecast.model == "forecast_unavailable":
        raise RuntimeError("Price forecast runtime artifacts are unavailable or invalid.")


def select_input_csv_path(*, repo_root: Path | None = None) -> Path | None:
    root = repo_root or _repo_root()
    target_csv = _runtime_target_csv(repo_root=root)
    if target_csv.is_file():
        return target_csv
    return None


def _parse_date(value: str | None) -> dt.date | None:
    if value is None:
        return None
    s = value.strip()
    if not s:
        return None

    # ISO date/datetime forms
    try:
        return dt.datetime.fromisoformat(s).date()
    except Exception:
        pass

    # Common separators
    if "/" in s:
        s = s.replace("/", "-")

    parts = s.split("-")
    if len(parts) < 3:
        return None

    p0, p1, p2 = parts[0].strip(), parts[1].strip(), parts[2].strip()
    try:
        if len(p0) == 4:
            year, month, day = int(p0), int(p1), int(p2)
        elif len(p2) == 4:
            day, month, year = int(p0), int(p1), int(p2)
        else:
            return None
        return dt.date(year, month, day)
    except Exception:
        return None


_PRICE_ALLOWED_RE = re.compile(r"[^\d.\-]+")


def _parse_price(value: str | None) -> float | None:
    if value is None:
        return None
    s = value.strip()
    if not s:
        return None
    # Remove commas, currency markers, etc. Keep digits, '.', and '-' only.
    s = _PRICE_ALLOWED_RE.sub("", s.replace(",", ""))
    if not s:
        return None
    try:
        price = float(s)
    except Exception:
        return None
    if not math.isfinite(price) or price <= 0:
        return None
    return price


def _load_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return []
        return [dict(row) for row in reader]


def _detect_columns(rows: list[dict[str, str]]) -> tuple[str, str] | None:
    if not rows:
        return None

    fieldnames = set(rows[0].keys())
    if "date" not in fieldnames:
        return None

    for price_col in ("price_lkr_per_kg", "price_lkr", "price"):
        if price_col in fieldnames:
            return "date", price_col
    return None


def clean_price_csv(
    input_csv_path: Path,
    *,
    output_csv_path: Path | None = None,
) -> list[PricePoint]:
    """
    Clean a raw market price CSV into a single, date-indexed series.

    - Parses dates into dt.date
    - Cleans prices into LKR/kg integers
    - Aggregates duplicate dates using average price
    - Forward-fill then backward-fill missing prices, then drops any remaining missing rows
    - Writes cleaned CSV if output_csv_path is provided
    """

    rows = _load_csv_rows(input_csv_path)
    detected = _detect_columns(rows)
    if detected is None:
        return []
    date_col, price_col = detected

    parsed: list[tuple[dt.date, float | None]] = []
    for row in rows:
        date = _parse_date(row.get(date_col))
        if date is None:
            continue
        price = _parse_price(row.get(price_col))
        parsed.append((date, price))

    if not parsed:
        return []

    by_date: dict[dt.date, list[float]] = defaultdict(list)
    all_dates: set[dt.date] = set()
    for date, price in parsed:
        all_dates.add(date)
        if price is not None:
            by_date[date].append(price)

    series: list[tuple[dt.date, float | None]] = []
    for date in sorted(all_dates):
        values = by_date.get(date) or []
        if values:
            series.append((date, sum(values) / float(len(values))))
        else:
            series.append((date, None))

    # Fill missing: forward-fill then back-fill.
    filled: list[tuple[dt.date, float | None]] = []
    last_price: float | None = None
    for date, price in series:
        if price is None and last_price is not None:
            price = last_price
        if price is not None:
            last_price = price
        filled.append((date, price))

    next_price: float | None = None
    backfilled: list[tuple[dt.date, float | None]] = []
    for date, price in reversed(filled):
        if price is None and next_price is not None:
            price = next_price
        if price is not None:
            next_price = price
        backfilled.append((date, price))
    backfilled.reverse()

    cleaned: list[PricePoint] = []
    for date, price in backfilled:
        if price is None:
            continue
        cleaned.append(PricePoint(date=date, price_lkr_per_kg=int(round(price))))

    if output_csv_path is not None:
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with output_csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "price_lkr_per_kg"])
            for point in cleaned:
                writer.writerow([point.date.isoformat(), point.price_lkr_per_kg])

    return cleaned


def load_observed_price_points(input_csv_path: Path) -> list[PricePoint]:
    """
    Load observed price points without filling, interpolation, or synthetic rows.
    """

    rows = _load_csv_rows(input_csv_path)
    detected = _detect_columns(rows)
    if detected is None:
        return []
    date_col, price_col = detected

    by_date: dict[dt.date, list[float]] = defaultdict(list)
    for row in rows:
        date = _parse_date(row.get(date_col))
        price = _parse_price(row.get(price_col))
        if date is None or price is None:
            continue
        by_date[date].append(price)

    points: list[PricePoint] = []
    for date in sorted(by_date):
        values = by_date[date]
        if values:
            points.append(PricePoint(date=date, price_lkr_per_kg=int(round(sum(values) / len(values)))))
    return points


def _load_runtime_naive_metrics(repo_root: Path) -> ForecastMetrics:
    metrics_path = _runtime_naive_metrics_path(repo_root=repo_root)
    if not metrics_path.is_file():
        return ForecastMetrics(mae=None, rmse=None)
    try:
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics = payload.get("metrics") or {}
        return ForecastMetrics(
            mae=round(float(metrics["mae"]), 4) if metrics.get("mae") is not None else None,
            rmse=round(float(metrics["rmse"]), 4) if metrics.get("rmse") is not None else None,
        )
    except Exception:
        return ForecastMetrics(mae=None, rmse=None)


def evaluate_one_step_ahead_metrics(points: list[PricePoint]) -> ForecastMetrics:
    if len(points) < EVAL_MIN_RECORDS:
        return ForecastMetrics(mae=None, rmse=None)

    y_true: list[float] = []
    y_pred: list[float] = []

    prices = [p.price_lkr_per_kg for p in points]
    for i in range(1, len(prices)):
        history = prices[:i]
        if len(history) == 1:
            pred = float(history[-1])
        else:
            window = history[-min(MOVING_AVG_WINDOW, len(history)) :]
            pred = float(sum(window) / len(window))
        y_true.append(float(prices[i]))
        y_pred.append(pred)

    if not y_true:
        return ForecastMetrics(mae=None, rmse=None)

    abs_errors = [abs(a - p) for a, p in zip(y_true, y_pred, strict=False)]
    sq_errors = [(a - p) ** 2 for a, p in zip(y_true, y_pred, strict=False)]
    mae = sum(abs_errors) / len(abs_errors)
    rmse = math.sqrt(sum(sq_errors) / len(sq_errors))
    return ForecastMetrics(mae=round(float(mae), 3), rmse=round(float(rmse), 3))


def _rng_for(seed_hint: str | None) -> random.Random:
    hasher = hashlib.sha256()
    hasher.update(b"price-forecast-demo-v1")
    if seed_hint:
        hasher.update(seed_hint.encode("utf-8", errors="ignore"))
    seed = int.from_bytes(hasher.digest()[:8], "big", signed=False)
    return random.Random(seed)


def _trend(current_price: int, predicted_price: int) -> TrendEnum:
    threshold = max(20, int(round(current_price * 0.02)))
    if predicted_price >= current_price + threshold:
        return TrendEnum.upward
    if predicted_price <= current_price - threshold:
        return TrendEnum.downward
    return TrendEnum.stable


def _demo_forecast(seed_hint: str | None) -> ForecastResult:
    rng = _rng_for(seed_hint=seed_hint)
    current_price = int(rng.uniform(1200, 1600))
    change_pct = rng.uniform(-0.06, 0.07)
    predicted_price = max(0, int(round(current_price * (1.0 + change_pct))))
    return ForecastResult(
        model="demo_baseline",
        current_price_lkr_per_kg=current_price,
        predicted_price_lkr_per_kg=predicted_price,
        trend=_trend(current_price, predicted_price),
        forecast_period="next_period",
        metrics=ForecastMetrics(mae=None, rmse=None),
    )


def _unavailable_forecast() -> ForecastResult:
    return ForecastResult(
        model="forecast_unavailable",
        current_price_lkr_per_kg=0,
        predicted_price_lkr_per_kg=0,
        trend=TrendEnum.stable,
        forecast_period="next_period",
        metrics=ForecastMetrics(mae=None, rmse=None),
    )


def _normalize_grade(grade: object | None) -> str:
    value = getattr(grade, "value", grade)
    return str(value or "Grade 1").strip()


def _round_to_nearest_50(value: float) -> int:
    return int(round(value / 50.0) * 50)


@lru_cache(maxsize=4)
def _grade_2_discount_lkr_per_kg(source_csv: Path) -> int:
    """
    Derive a simple Grade 2 discount from observed National average Grade 1 vs
    Grade 2 rows. The latest overlapping date is used, then rounded for display.
    """

    if not source_csv.is_file():
        return GRADE_2_DEFAULT_DISCOUNT_LKR_PER_KG

    try:
        rows = _load_csv_rows(source_csv)
    except Exception:
        return GRADE_2_DEFAULT_DISCOUNT_LKR_PER_KG

    grade_1: dict[dt.date, float] = {}
    grade_2: dict[dt.date, float] = {}
    for row in rows:
        if (row.get("district") or "").strip().lower() != "national":
            continue
        if (row.get("price_type") or "").strip().lower() != "average":
            continue

        date = _parse_date(row.get("date"))
        price = _parse_price(row.get("price_lkr_per_kg"))
        if date is None or price is None:
            continue

        grade_value = (row.get("grade") or "").strip()
        if grade_value == "Grade 1":
            grade_1[date] = price
        elif grade_value == "Grade 2":
            grade_2[date] = price

    for date in sorted(set(grade_1).intersection(grade_2), reverse=True):
        gap = grade_1[date] - grade_2[date]
        if math.isfinite(gap) and gap > 0:
            rounded = _round_to_nearest_50(gap)
            return max(50, rounded)

    return GRADE_2_DEFAULT_DISCOUNT_LKR_PER_KG


def _apply_grade_price_adjustment(
    *,
    base_price_lkr_per_kg: int,
    grade: object | None,
    repo_root: Path,
) -> tuple[str, int, ForecastMetrics]:
    normalized = _normalize_grade(grade)
    if normalized == "Grade 2":
        discount = _grade_2_discount_lkr_per_kg(_grade_price_gap_source_csv(repo_root=repo_root))
        return (
            GRADE_2_ADJUSTED_FORECAST_MODEL_ID,
            max(0, int(base_price_lkr_per_kg) - discount),
            ForecastMetrics(mae=None, rmse=None),
        )
    if normalized == "Grade 3":
        return (
            GRADE_3_UNAVAILABLE_FORECAST_MODEL_ID,
            0,
            ForecastMetrics(mae=None, rmse=None),
        )
    return (
        RUNTIME_FORECAST_MODEL_ID,
        int(base_price_lkr_per_kg),
        _load_runtime_naive_metrics(repo_root),
    )


def build_price_forecast(
    seed_hint: str | None,
    *,
    grade: object | None = None,
    csv_path_override: Path | None = None,
    cleaned_output_path_override: Path | None = None,
    models_dir_override: Path | None = None,
) -> ForecastResult:
    """
    Build the runtime price forecast from the selected research-backed method.

    - Uses the V2 National Grade 1 average weekly target by default.
    - Applies a documented Grade 2 discount when the predicted grade is Grade 2.
    - Returns a grade-specific unavailable marker for Grade 3 because no Grade 3
      historical price series is available.
    - Uses Naive Persistence because it is the strongest validated V2 forecasting method.
    - Never raises; data/configuration problems return an explicit unavailable state.
    """

    try:
        root = _repo_root()
        input_csv = csv_path_override
        if input_csv is None:
            input_csv = select_input_csv_path(repo_root=root)

        if input_csv is None or not input_csv.is_file():
            return _unavailable_forecast()

        points = load_observed_price_points(input_csv)
        if not points:
            return _unavailable_forecast()

        base_price = int(points[-1].price_lkr_per_kg)
        model_id, predicted, metrics = _apply_grade_price_adjustment(
            base_price_lkr_per_kg=base_price,
            grade=grade,
            repo_root=root,
        )
        return ForecastResult(
            model=model_id,
            current_price_lkr_per_kg=int(max(0, predicted)),
            predicted_price_lkr_per_kg=int(max(0, predicted)),
            trend=TrendEnum.stable,
            forecast_period="next_period",
            metrics=metrics,
        )
    except Exception:
        return _unavailable_forecast()


def _std(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return float(math.sqrt(sum((v - mean) ** 2 for v in values) / len(values)))


def _build_latest_features(points: list[PricePoint], *, spec: dict) -> dict[str, float] | None:
    feature_names = list(spec.get("feature_names") or [])
    lags = [int(x) for x in (spec.get("lags") or [])]
    rolling_windows = [int(x) for x in (spec.get("rolling_windows") or [])]
    eps = float(spec.get("eps") or 1.0)

    if not points or not feature_names or not lags or not rolling_windows:
        return None

    prices = [float(p.price_lkr_per_kg) for p in points]
    dates = [p.date for p in points]
    t = len(prices) - 1

    # Need lag history plus rolling history on shifted series.
    max_lag = max(lags)
    max_roll = max(rolling_windows)
    if len(prices) < (max_lag + 1) or len(prices) < (max_roll + 2):
        return None

    current_price = prices[t]
    current_date = dates[t]

    feats: dict[str, float] = {}
    for lag in lags:
        feats[f"lag_{lag}"] = float(prices[t - lag])

    # Rolling on shifted series => use history up to t-1.
    hist = prices[:t]  # excludes current
    for w in rolling_windows:
        window = hist[-w:]
        if len(window) != w:
            return None
        feats[f"rolling_mean_{w}"] = float(sum(window) / len(window))
        feats[f"rolling_std_{w}"] = float(_std(window))

    lag1 = feats.get("lag_1")
    if lag1 is None:
        return None
    feats["price_change_1w"] = float(current_price - lag1)
    denom = max(float(lag1), float(eps))
    feats["price_change_pct_1w"] = float((current_price - lag1) / denom)

    feats["month"] = float(int(current_date.month))
    feats["week_of_year"] = float(int(current_date.isocalendar().week))

    # Ensure all expected features present.
    for name in feature_names:
        if name not in feats:
            return None
    return feats


def _predict_next_price(points: list[PricePoint], *, spec: dict, model: object) -> float | None:
    feats = _build_latest_features(points, spec=spec)
    if feats is None:
        return None

    feature_names = list(spec.get("feature_names") or [])
    x = [[float(feats[n]) for n in feature_names]]

    try:
        pred = model.predict(x)  # type: ignore[attr-defined]
    except Exception:
        return None

    try:
        return float(pred[0])
    except Exception:
        return None
