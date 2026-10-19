from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

sys.dont_write_bytecode = True


PRIMARY_TARGET = {
    "commodity": "black_pepper",
    "country": "Sri Lanka",
    "district": "National",
    "grade": "Grade 1",
    "price_type": "average",
    "market_level": "farm_gate",
    "frequency": "weekly",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def standardize_district(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("_", " ")
    return re.sub(r"\s+", " ", text).title()


def standardize_grade(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    match = re.search(r"(\d+)", text)
    return f"Grade {match.group(1)}" if match else None


def standardize_token(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    return re.sub(r"\s+", "_", text).lower()


def standardize_country(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = re.sub(r"\s+", " ", str(value).strip())
    return text or None


def parse_price(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        price = float(text)
    except ValueError:
        return None
    return price if price > 0 else None


def date_range_payload(dates: pd.Series) -> dict[str, str | None]:
    clean = pd.to_datetime(dates, errors="coerce").dropna()
    if clean.empty:
        return {"start": None, "end": None}
    return {"start": str(clean.min().date()), "end": str(clean.max().date())}


def clean_raw_prices(raw_csv: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = pd.read_csv(raw_csv)
    required = {
        "date",
        "commodity",
        "country",
        "district",
        "grade",
        "price_type",
        "price_lkr_per_kg",
        "market_level",
        "frequency",
    }
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise ValueError(f"Raw price CSV missing required columns: {missing}")

    cleaned = raw.copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    cleaned["commodity"] = cleaned["commodity"].map(standardize_token)
    cleaned["country"] = cleaned["country"].map(standardize_country)
    cleaned["district"] = cleaned["district"].map(standardize_district)
    cleaned["grade"] = cleaned["grade"].map(standardize_grade)
    cleaned["price_type"] = cleaned["price_type"].map(standardize_token)
    cleaned["market_level"] = cleaned["market_level"].map(standardize_token)
    cleaned["frequency"] = cleaned["frequency"].map(standardize_token)
    cleaned["price_lkr_per_kg"] = cleaned["price_lkr_per_kg"].map(parse_price)

    before_drop = len(cleaned)
    cleaned = cleaned.dropna(
        subset=[
            "date",
            "commodity",
            "country",
            "district",
            "grade",
            "price_type",
            "market_level",
            "frequency",
            "price_lkr_per_kg",
        ]
    )
    invalid_rows_removed = before_drop - len(cleaned)

    duplicate_count = int(cleaned.duplicated(["date", "district", "grade", "price_type"]).sum())
    cleaned = cleaned.drop_duplicates(["date", "district", "grade", "price_type"], keep="first")
    cleaned = cleaned.sort_values(["date", "district", "grade", "price_type"]).reset_index(drop=True)

    audit = {
        "raw_rows": int(len(raw)),
        "cleaned_rows": int(len(cleaned)),
        "invalid_rows_removed": int(invalid_rows_removed),
        "duplicates_removed_by_date_district_grade_price_type": duplicate_count,
        "raw_date_range": date_range_payload(raw["date"]),
        "cleaned_date_range": date_range_payload(cleaned["date"]),
        "district_values_after_standardization": sorted(cleaned["district"].dropna().unique().tolist()),
        "grade_values_after_standardization": sorted(cleaned["grade"].dropna().unique().tolist()),
        "price_type_values_after_standardization": sorted(cleaned["price_type"].dropna().unique().tolist()),
    }
    return cleaned, audit


def target_series(cleaned: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    mask = (
        (cleaned["commodity"] == PRIMARY_TARGET["commodity"])
        & (cleaned["country"] == PRIMARY_TARGET["country"])
        & (cleaned["district"] == PRIMARY_TARGET["district"])
        & (cleaned["grade"] == PRIMARY_TARGET["grade"])
        & (cleaned["price_type"] == PRIMARY_TARGET["price_type"])
        & (cleaned["market_level"] == PRIMARY_TARGET["market_level"])
        & (cleaned["frequency"] == PRIMARY_TARGET["frequency"])
    )
    target = cleaned.loc[mask].copy().sort_values("date")
    duplicates = target[target.duplicated("date", keep=False)].copy()
    if not duplicates.empty:
        raise ValueError(
            "Primary target has duplicate dates after filtering; inspect before aggregating. "
            f"Duplicate dates: {duplicates['date'].dt.date.astype(str).unique().tolist()[:10]}"
        )
    out = target[["date", "price_lkr_per_kg"]].copy()
    summary = {
        "target_definition": PRIMARY_TARGET,
        "target_observations": int(len(out)),
        "target_date_range": date_range_payload(out["date"]),
        "duplicate_target_dates": int(out.duplicated("date").sum()),
        "national_representation_verified": "National",
    }
    return out, summary


def gap_summary(dates: pd.Series) -> dict[str, Any]:
    clean = pd.to_datetime(dates, errors="coerce").dropna().sort_values()
    if clean.empty:
        return {
            "observation_count": 0,
            "observed_intervals_days": {},
            "gaps_over_8_days": [],
            "gap_count_over_8_days": 0,
            "largest_gap_days": None,
        }
    unique_dates = sorted(clean.dt.date.unique())
    intervals = [
        (unique_dates[i] - unique_dates[i - 1]).days
        for i in range(1, len(unique_dates))
    ]
    gaps = [
        {
            "from": unique_dates[i - 1].isoformat(),
            "to": unique_dates[i].isoformat(),
            "days": (unique_dates[i] - unique_dates[i - 1]).days,
        }
        for i in range(1, len(unique_dates))
        if (unique_dates[i] - unique_dates[i - 1]).days > 8
    ]
    return {
        "observation_count": len(unique_dates),
        "date_range": {"start": unique_dates[0].isoformat(), "end": unique_dates[-1].isoformat()},
        "observed_intervals_days": dict(sorted(Counter(intervals).items())),
        "gaps_over_8_days": gaps,
        "gap_count_over_8_days": len(gaps),
        "largest_gap_days": max((g["days"] for g in gaps), default=None),
        "note": "Dates are analyzed as observed source dates; no complete weekly calendar was fabricated.",
    }


def coverage_by_year(df: pd.DataFrame, *, grade: str | None = None) -> dict[str, Any]:
    sub = df.copy()
    if grade is not None:
        sub = sub[sub["grade"] == grade].copy()
    if sub.empty:
        return {}
    sub["year"] = sub["date"].dt.year
    rows_by_year = {
        str(int(k)): int(v)
        for k, v in sub.groupby("year").size().to_dict().items()
    }
    observed_weeks_by_year = {
        str(int(k)): int(v)
        for k, v in sub.groupby("year")["date"].nunique().to_dict().items()
    }
    return {
        "rows_by_year": rows_by_year,
        "observed_dates_by_year": observed_weeks_by_year,
        "total_rows": int(len(sub)),
        "unique_dates": int(sub["date"].nunique()),
    }


def split_chronological(target: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    n = len(target)
    if n < 3:
        raise ValueError("Need at least 3 observations for train/validation/test split.")
    train_end = int(n * 0.70)
    val_end = train_end + int(n * 0.15)
    train_end = max(1, min(train_end, n - 2))
    val_end = max(train_end + 1, min(val_end, n - 1))

    train = target.iloc[:train_end].copy()
    val = target.iloc[train_end:val_end].copy()
    test = target.iloc[val_end:].copy()

    summary = {
        "split_policy": "chronological_70_15_15_by_observed_rows",
        "train": {"rows": int(len(train)), **date_range_payload(train["date"])},
        "validation": {"rows": int(len(val)), **date_range_payload(val["date"])},
        "test": {"rows": int(len(test)), **date_range_payload(test["date"])},
        "no_shuffle": True,
    }
    return train, val, test, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare V2 price dataset and chronological splits.")
    parser.add_argument("--input", type=Path, default=None)
    args = parser.parse_args(argv)

    root = repo_root()
    raw_csv = args.input or root / "data" / "raw" / "market_prices" / "dea_farmgate_weekly_prices_2016_2026.csv"
    out_dir = root / "data" / "processed" / "grading_forecast" / "price_v2"
    cleaned_csv = out_dir / "cleaned_price_data_v2.csv"
    target_csv = out_dir / "national_grade1_average_weekly.csv"
    train_csv = out_dir / "forecast_train.csv"
    val_csv = out_dir / "forecast_validation.csv"
    test_csv = out_dir / "forecast_test.csv"
    summary_json = out_dir / "price_v2_coverage_summary.json"

    if not raw_csv.exists():
        print(f"Missing raw CSV: {raw_csv}")
        return 2

    cleaned, clean_audit = clean_raw_prices(raw_csv)
    target, target_audit = target_series(cleaned)
    train, val, test, split_audit = split_chronological(target)

    out_dir.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(cleaned_csv, index=False)
    target.to_csv(target_csv, index=False)
    train.to_csv(train_csv, index=False)
    val.to_csv(val_csv, index=False)
    test.to_csv(test_csv, index=False)

    grade2 = cleaned[cleaned["grade"] == "Grade 2"].copy()
    grade2_national_average = cleaned[
        (cleaned["grade"] == "Grade 2")
        & (cleaned["district"] == "National")
        & (cleaned["price_type"] == "average")
    ].copy()
    summary = {
        "dataset_version": "price_v2",
        "created_at": utc_now_iso(),
        "input_csv": "data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv",
        "outputs": {
            "cleaned_csv": "data/processed/grading_forecast/price_v2/cleaned_price_data_v2.csv",
            "target_csv": "data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv",
            "forecast_train_csv": "data/processed/grading_forecast/price_v2/forecast_train.csv",
            "forecast_validation_csv": "data/processed/grading_forecast/price_v2/forecast_validation.csv",
            "forecast_test_csv": "data/processed/grading_forecast/price_v2/forecast_test.csv",
        },
        "cleaning": clean_audit,
        "primary_target": target_audit,
        "target_gap_analysis": gap_summary(target["date"]),
        "all_grade_coverage": {
            "Grade 1": coverage_by_year(cleaned, grade="Grade 1"),
            "Grade 2": coverage_by_year(cleaned, grade="Grade 2"),
        },
        "grade2_coverage": {
            "all_observed_grade2_records": coverage_by_year(grade2),
            "national_average_grade2_records": coverage_by_year(grade2_national_average),
            "districts_with_grade2": sorted(grade2["district"].dropna().unique().tolist()),
            "note": "Grade 2 records are preserved but not used as the primary PP2 forecasting target because early historical coverage is sparse.",
        },
        "split": split_audit,
        "validation": {
            "target_has_at_most_one_row_per_date": int(target.duplicated("date").sum()) == 0,
            "splits_are_chronological": bool(train["date"].max() < val["date"].min() < val["date"].max() < test["date"].min()),
            "no_missing_target_prices": int(target["price_lkr_per_kg"].isna().sum()) == 0,
            "no_fabricated_missing_weeks": True,
            "no_grade2_imputation": True,
        },
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    ok = all(summary["validation"].values())
    print(f"Wrote cleaned CSV: {cleaned_csv}")
    print(f"Wrote target CSV: {target_csv}")
    print(f"Wrote split CSVs: {train_csv}, {val_csv}, {test_csv}")
    print(f"Wrote summary: {summary_json}")
    print(f"Target observations: {len(target)}")
    print(f"Validation passed: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

