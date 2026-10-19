from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _default_input(repo_root: Path) -> Path:
    return repo_root / "data" / "processed" / "grading_forecast" / "forecast_training_data.csv"


def _default_train(repo_root: Path) -> Path:
    return repo_root / "data" / "processed" / "grading_forecast" / "train_forecast_data.csv"


def _default_test(repo_root: Path) -> Path:
    return repo_root / "data" / "processed" / "grading_forecast" / "test_forecast_data.csv"


def _date_range(df: pd.DataFrame) -> str:
    if df.empty:
        return "(empty)"
    start = df["date"].min().date()
    end = df["date"].max().date()
    return f"{start} -> {end}"


def create_split(input_csv: Path, train_csv: Path, test_csv: Path, train_ratio: float = 0.8) -> tuple[int, int]:
    df = pd.read_csv(input_csv)
    if "date" not in df.columns:
        raise ValueError("Input CSV must contain a 'date' column.")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date", ascending=True)

    if df.empty:
        train_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(train_csv, index=False)
        df.to_csv(test_csv, index=False)
        return (0, 0)

    split_index = int(len(df) * train_ratio)
    split_index = max(1, min(split_index, len(df) - 1))

    train_df = df.iloc[:split_index].copy()
    test_df = df.iloc[split_index:].copy()

    train_csv.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(train_csv, index=False)
    test_df.to_csv(test_csv, index=False)
    return (len(train_df), len(test_df))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a chronological train/test split for forecasting data.")
    parser.add_argument("--input", type=Path, default=None, help="Input forecasting CSV path.")
    parser.add_argument("--train-out", type=Path, default=None, help="Train CSV output path.")
    parser.add_argument("--test-out", type=Path, default=None, help="Test CSV output path.")
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    input_csv = args.input or _default_input(repo_root)
    train_out = args.train_out or _default_train(repo_root)
    test_out = args.test_out or _default_test(repo_root)

    if not input_csv.exists():
        print(f"Missing input CSV: {input_csv}")
        return 2

    df = pd.read_csv(input_csv)
    df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date", ascending=True)

    total = len(df)
    try:
        train_count, test_count = create_split(
            input_csv=input_csv, train_csv=train_out, test_csv=test_out, train_ratio=0.8
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to create split: {exc}")
        return 1

    train_df = pd.read_csv(train_out)
    test_df = pd.read_csv(test_out)
    train_df["date"] = pd.to_datetime(train_df.get("date"), errors="coerce")
    test_df["date"] = pd.to_datetime(test_df.get("date"), errors="coerce")

    print(f"Total records: {total}")
    print(f"Train count: {train_count} | Date range: {_date_range(train_df.dropna(subset=['date']))}")
    print(f"Test  count: {test_count} | Date range: {_date_range(test_df.dropna(subset=['date']))}")
    print(f"Wrote: {train_out}")
    print(f"Wrote: {test_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

