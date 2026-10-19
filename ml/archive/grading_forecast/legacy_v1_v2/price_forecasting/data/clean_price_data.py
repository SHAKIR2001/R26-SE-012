from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _standardize_district(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text.title()


def _standardize_grade(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None

    match = re.search(r"(\d+)", text)
    if not match:
        return None
    number = match.group(1)
    return f"Grade {number}"


def _standardize_price_type(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    text = text.replace(" ", "_")
    text = re.sub(r"[^a-z_]", "", text)
    if text == "avg":
        text = "average"
    return text


def _parse_price(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def clean_price_data(input_csv: Path, output_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(input_csv)

    required_columns = {"date", "district", "grade", "price_type", "price_lkr_per_kg"}
    missing = sorted(required_columns.difference(df.columns))
    if missing:
        raise ValueError(f"Input CSV missing required columns: {missing}")

    df = df.copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["district"] = df["district"].map(_standardize_district)
    df["grade"] = df["grade"].map(_standardize_grade)
    df["price_type"] = df["price_type"].map(_standardize_price_type)
    df["price_lkr_per_kg"] = df["price_lkr_per_kg"].map(_parse_price)

    valid_grades = {"Grade 1", "Grade 2", "Grade 3"}
    valid_price_types = {"average", "highest", "lowest"}

    df = df.dropna(subset=["date", "district", "grade", "price_type", "price_lkr_per_kg"])
    df = df[df["grade"].isin(valid_grades)]
    df = df[df["price_type"].isin(valid_price_types)]

    df = df.drop_duplicates(subset=["date", "district", "grade", "price_type"], keep="first")
    df = df.sort_values(["date", "district", "grade", "price_type"], ascending=True)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    return df


def _default_input(repo_root: Path) -> Path:
    return repo_root / "data" / "raw" / "market_prices" / "dea_farmgate_weekly_prices_2016_2026.csv"


def _default_output(repo_root: Path) -> Path:
    return repo_root / "data" / "processed" / "grading_forecast" / "cleaned_price_data.csv"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean weekly DEA farm-gate pepper price data for forecasting.")
    parser.add_argument("--input", type=Path, default=None, help="Input price CSV path (defaults to project dataset).")
    parser.add_argument("--output", type=Path, default=None, help="Output cleaned CSV path.")
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    input_csv = args.input or _default_input(repo_root)
    output_csv = args.output or _default_output(repo_root)

    if not input_csv.exists():
        print(f"Missing input CSV: {input_csv}")
        return 2

    try:
        cleaned = clean_price_data(input_csv=input_csv, output_csv=output_csv)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to clean price data: {exc}")
        return 1

    print(f"Cleaned {len(cleaned)} rows -> {output_csv}")
    print(f"Date range: {cleaned['date'].min().date()} to {cleaned['date'].max().date()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

