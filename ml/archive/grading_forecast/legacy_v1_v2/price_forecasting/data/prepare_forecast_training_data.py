from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _default_cleaned_prices(repo_root: Path) -> Path:
    return repo_root / "data" / "processed" / "grading_forecast" / "cleaned_price_data.csv"


def _default_output(repo_root: Path) -> Path:
    return repo_root / "data" / "processed" / "grading_forecast" / "forecast_training_data.csv"


def prepare_forecast_dataset(
    cleaned_prices_csv: Path,
    output_csv: Path,
    *,
    district: str = "National",
    grade: str = "Grade 1",
    price_type: str = "average",
) -> pd.DataFrame:
    df = pd.read_csv(cleaned_prices_csv)
    required = {"date", "district", "grade", "price_type", "price_lkr_per_kg"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Cleaned price CSV missing required columns: {missing}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "price_lkr_per_kg"])

    subset = df[
        (df["district"].astype(str) == district)
        & (df["grade"].astype(str) == grade)
        & (df["price_type"].astype(str) == price_type)
    ].copy()

    subset = subset.sort_values("date", ascending=True)
    out = subset[["date", "price_lkr_per_kg"]].rename(columns={"price_lkr_per_kg": "price_lkr_per_kg"})

    # Research note:
    # District-wise forecasting is identified as future work due to inconsistent district-level data availability
    # and grade sparsity.

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_csv, index=False)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create forecasting-ready dataset (National + Grade 1 + average price) from cleaned prices."
    )
    parser.add_argument("--input", type=Path, default=None, help="Input cleaned price CSV path.")
    parser.add_argument("--output", type=Path, default=None, help="Output forecast training CSV path.")
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    input_csv = args.input or _default_cleaned_prices(repo_root)
    output_csv = args.output or _default_output(repo_root)

    if not input_csv.exists():
        print(f"Missing cleaned prices CSV: {input_csv}")
        print("Run ml/grading_forecast/price_forecasting/data/clean_price_data.py first.")
        return 2

    try:
        out = prepare_forecast_dataset(cleaned_prices_csv=input_csv, output_csv=output_csv)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to prepare forecasting dataset: {exc}")
        return 1

    print(f"Wrote {len(out)} rows -> {output_csv}")
    if not out.empty:
        dates = pd.to_datetime(out["date"], errors="coerce").dropna()
        if not dates.empty:
            print(f"Date range: {dates.min().date()} to {dates.max().date()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

