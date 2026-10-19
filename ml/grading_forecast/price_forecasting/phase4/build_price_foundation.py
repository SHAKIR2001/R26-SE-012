"""Build the canonical, analytical, and leakage-safe Phase 4 price datasets."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
RAW_DIR = ROOT / "data/raw/market_prices/eac_phase4"
OLD_RAW = ROOT / "data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv"
OUT = ROOT / "data/processed/grading_forecast/price/eac_reconstructed_v1"
PLOTS = ROOT / "ml/grading_forecast/price_forecasting/phase4/outputs"
OLD_CUTOFF = pd.Timestamp("2026-08-18")
SEED = 42


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def interval_stats(dates: pd.Series) -> dict:
    unique = pd.Series(pd.to_datetime(dates).dropna().sort_values().unique())
    gaps = unique.diff().dt.days.dropna()
    return {
        "observation_dates": int(len(unique)),
        "interval_count": int(len(gaps)),
        "minimum_days": None if gaps.empty else int(gaps.min()),
        "maximum_days": None if gaps.empty else int(gaps.max()),
        "mean_days": None if gaps.empty else float(gaps.mean()),
        "median_days": None if gaps.empty else float(gaps.median()),
        "gaps_over_14_days": [
            {"from": str(unique.iloc[i - 1].date()), "to": str(unique.iloc[i].date()), "days": int((unique.iloc[i] - unique.iloc[i - 1]).days)}
            for i in range(1, len(unique)) if (unique.iloc[i] - unique.iloc[i - 1]).days > 14
        ],
    }


def price_stats(series: pd.Series) -> dict:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return {
        "count": int(len(clean)), "minimum": float(clean.min()), "maximum": float(clean.max()),
        "mean": float(clean.mean()), "median": float(clean.median()),
    }


def add_grade_features(group: pd.DataFrame) -> pd.DataFrame:
    group = group.sort_values("date").copy()
    price = group["price_lkr_per_kg"]
    group["return"] = price.pct_change(fill_method=None)
    group["log_return"] = np.log(price / price.shift(1))
    group["direction"] = np.where(group["return"].isna(), None, np.where(group["return"] > 0, "UP", np.where(group["return"] < 0, "DOWN", "FLAT")))
    group["price_lag_1"] = price.shift(1)
    group["price_lag_2"] = price.shift(2)
    group["return_lag_1"] = group["return"].shift(1)
    group["days_since_previous_observation"] = group["date"].diff().dt.days
    group["rolling_price_mean_3"] = price.rolling(3, min_periods=3).mean()
    group["rolling_return_std_3"] = group["return"].rolling(3, min_periods=3).std()
    group["next_observation_date"] = group["date"].shift(-1)
    group["target_return_next"] = price.shift(-1) / price - 1.0
    group["target_log_return_next"] = np.log(price.shift(-1) / price)
    group["target_direction_next"] = np.where(
        group["target_return_next"].isna(), None,
        np.where(group["target_return_next"] > 0, "UP", np.where(group["target_return_next"] < 0, "DOWN", "FLAT")),
    )
    group["days_to_next_observation"] = (group["next_observation_date"] - group["date"]).dt.days
    return group


def temporal_partitions(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    eligible_dates = sorted(frame.loc[frame["next_observation_date"].le(OLD_CUTOFF), "next_observation_date"].dropna().unique())
    n = len(eligible_dates)
    train_end = max(1, int(n * 0.70))
    validation_end = max(train_end + 1, int(n * 0.85))
    train_last = pd.Timestamp(eligible_dates[train_end - 1])
    validation_last = pd.Timestamp(eligible_dates[validation_end - 1])
    output = frame.copy()
    output["partition"] = np.select(
        [
            output["next_observation_date"].isna(),
            output["next_observation_date"].gt(OLD_CUTOFF),
            output["next_observation_date"].le(train_last),
            output["next_observation_date"].le(validation_last),
            output["next_observation_date"].le(OLD_CUTOFF),
        ],
        ["NO_TARGET", "EXTERNAL_NEWEST", "TRAIN", "VALIDATION", "TEST"],
        default="UNASSIGNED",
    )
    summary = {
        "policy": "shared chronological target-date boundaries; newest dates after old local cutoff reserved externally",
        "old_local_cutoff": OLD_CUTOFF.date().isoformat(), "train_last_target_date": train_last.date().isoformat(),
        "validation_last_target_date": validation_last.date().isoformat(), "test_last_target_date": OLD_CUTOFF.date().isoformat(),
        "rows_by_partition_and_grade": {
            partition: {grade: int(count) for grade, count in sub.groupby("grade").size().items()}
            for partition, sub in output.groupby("partition")
        },
    }
    return output, summary


def plots(national: pd.DataFrame, relationship: pd.DataFrame, forecasting: pd.DataFrame) -> None:
    def observed_segments(ax, frame: pd.DataFrame, value: str, label: str, color: str) -> None:
        ordered = frame.sort_values("date")
        ax.scatter(ordered["date"], ordered[value], s=7, color=color, alpha=0.8)
        segment = ordered["date"].diff().dt.days.gt(14).cumsum()
        for index, (_, part) in enumerate(ordered.groupby(segment)):
            ax.plot(part["date"], part[value], color=color, linewidth=1.2, label=label if index == 0 else None)

    PLOTS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    colors = {"Grade 1": "#1f77b4", "Grade 2": "#ff7f0e"}
    for grade, group in national.groupby("grade"):
        observed_segments(ax, group, "price_lkr_per_kg", grade, colors[grade])
    ax.set(title="National Average Black Pepper Farm-Gate Prices", xlabel="DEA observation date", ylabel="LKR per kg")
    ax.legend(); ax.grid(alpha=0.25); fig.tight_layout(); fig.savefig(PLOTS / "01_g1_g2_prices.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.2)); observed_segments(ax, relationship, "g1_g2_spread_lkr_per_kg", "Observed spread", "#7b3294")
    ax.set(title="Observed Grade 1 - Grade 2 Price Spread", xlabel="DEA observation date", ylabel="Spread (LKR/kg)")
    ax.grid(alpha=0.25); fig.tight_layout(); fig.savefig(PLOTS / "02_grade_spread.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.2)); observed_segments(ax, relationship, "g2_g1_ratio", "Observed ratio", "#008837")
    ax.set(title="Observed Grade 2 / Grade 1 Price Ratio", xlabel="DEA observation date", ylabel="Ratio")
    ax.grid(alpha=0.25); fig.tight_layout(); fig.savefig(PLOTS / "03_grade_ratio.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    for grade, group in forecasting.groupby("grade"):
        plot_group = group.assign(return_percent=group["return"] * 100.0)
        observed_segments(ax, plot_group, "return_percent", grade, colors[grade])
    ax.axhline(0, color="black", linewidth=0.8); ax.set(title="Historical One-Observation Price Changes", xlabel="DEA observation date", ylabel="Observed change (%)")
    ax.legend(); ax.grid(alpha=0.25); fig.tight_layout(); fig.savefig(PLOTS / "04_historical_returns.png", dpi=160); plt.close(fig)


def main() -> int:
    raw_files = sorted(RAW_DIR.glob("dea_eac_pepper_observations_retrieved_*.csv"))
    if not raw_files:
        raise FileNotFoundError("Run reconstruct_eac_prices.py first")
    raw_path = raw_files[-1]
    raw = pd.read_csv(raw_path)
    raw["date"] = pd.to_datetime(raw["date"], errors="raise")
    raw["source_date"] = pd.to_datetime(raw["source_date"], errors="raise")
    raw["price_lkr_per_kg"] = pd.to_numeric(raw["price_lkr_per_kg"], errors="raise")
    raw["market"] = raw["market"].str.replace("_", " ", regex=False).str.strip().str.title()
    raw = raw.sort_values(["date", "market", "grade", "price_type"]).reset_index(drop=True)
    key = ["date", "market", "commodity", "grade", "price_type", "market_level"]
    if raw.duplicated(key).any():
        raise RuntimeError("Duplicate canonical observation keys found")
    if not set(raw["grade"]).issubset({"Grade 1", "Grade 2"}):
        raise RuntimeError("Unexpected grade in reconstruction")
    raw["observation_status"] = "observed_source_value"
    raw["observation_id"] = raw.apply(lambda r: hashlib.sha256("|".join(str(r[c]) for c in key).encode()).hexdigest()[:20], axis=1)
    OUT.mkdir(parents=True, exist_ok=True)
    canonical_path = OUT / "eac_pepper_price_canonical.csv"
    raw.to_csv(canonical_path, index=False, date_format="%Y-%m-%d")

    national = raw[(raw["market"] == "National") & (raw["price_type"] == "average")].copy()
    national = national.sort_values(["grade", "date"])
    national_path = OUT / "eac_national_average_prices.csv"
    national.to_csv(national_path, index=False, date_format="%Y-%m-%d")

    wide = national.pivot(index="date", columns="grade", values="price_lkr_per_kg").rename(columns={"Grade 1": "g1_price_lkr_per_kg", "Grade 2": "g2_price_lkr_per_kg"})
    relationship = wide.dropna(subset=["g1_price_lkr_per_kg", "g2_price_lkr_per_kg"]).reset_index()
    relationship["g1_g2_spread_lkr_per_kg"] = relationship["g1_price_lkr_per_kg"] - relationship["g2_price_lkr_per_kg"]
    relationship["g2_g1_ratio"] = relationship["g2_price_lkr_per_kg"] / relationship["g1_price_lkr_per_kg"]
    relationship.to_csv(OUT / "eac_grade_relationship.csv", index=False, date_format="%Y-%m-%d")

    forecasting = pd.concat([add_grade_features(group) for _, group in national.groupby("grade")], ignore_index=True)
    forecasting = forecasting.merge(relationship[["date", "g1_g2_spread_lkr_per_kg", "g2_g1_ratio"]], on="date", how="left")
    forecasting["grade_indicator"] = (forecasting["grade"] == "Grade 2").astype(int)
    forecasting, split_summary = temporal_partitions(forecasting)
    forecasting = forecasting.sort_values(["date", "grade"]).reset_index(drop=True)
    forecasting.to_csv(OUT / "eac_forecasting_dataset.csv", index=False, date_format="%Y-%m-%d")

    source_manifest = pd.read_csv(OUT / "eac_pepper_price_source_manifest.csv")
    g1_dates = set(national.loc[national.grade == "Grade 1", "date"])
    g2_dates = set(national.loc[national.grade == "Grade 2", "date"])
    all_national_dates = sorted(g1_dates | g2_dates)
    old_summary = {}
    if OLD_RAW.exists():
        old = pd.read_csv(OLD_RAW)
        old_summary = {"rows": int(len(old)), "start": str(old["date"].min()), "end": str(old["date"].max()), "sha256": sha256(OLD_RAW)}
    quality = {
        "dataset_version": "eac_reconstructed_v1", "created_on": date.today().isoformat(),
        "source": "DEA Sri Lanka Economic Research Unit - Producers' Prices (Farm Gate) of EAC",
        "source_index_url": "https://exagri.info/mkt/index.html", "raw_reconstruction_file": str(raw_path.relative_to(ROOT)).replace("\\", "/"),
        "raw_reconstruction_sha256": sha256(raw_path), "canonical_sha256": sha256(canonical_path),
        "date_range": {"start": str(raw.date.min().date()), "end": str(raw.date.max().date())},
        "observation_count": int(len(raw)), "source_dates": int(raw.date.nunique()),
        "grade_observation_rows": {k: int(v) for k, v in raw.groupby("grade").size().items()},
        "national_average": {
            "g1_observations": len(g1_dates), "g2_observations": len(g2_dates), "dates_with_both": len(g1_dates & g2_dates),
            "missing_g1_dates_relative_to_union": len(set(all_national_dates) - g1_dates),
            "missing_g2_dates_relative_to_union": len(set(all_national_dates) - g2_dates),
            "latest_g1_date": str(max(g1_dates).date()), "latest_g2_date": str(max(g2_dates).date()),
            "prices": {grade: price_stats(group["price_lkr_per_kg"]) for grade, group in national.groupby("grade")},
            "observations_by_year_and_grade": {
                str(year): {grade: int(count) for grade, count in group.groupby("grade").size().items()}
                for year, group in national.assign(year=national.date.dt.year).groupby("year")
            },
            "intervals_by_grade": {grade: interval_stats(group["date"]) for grade, group in national.groupby("grade")},
        },
        "duplicates": {
            "canonical_key_duplicates": int(raw.duplicated(key).sum()),
            "duplicate_source_urls": int(source_manifest.duplicated("source_url").sum()),
            "duplicate_page_hashes": int(source_manifest.loc[source_manifest["page_sha256"].notna() & source_manifest["page_sha256"].ne(""), "page_sha256"].duplicated().sum()),
        },
        "source_completeness": {
            "dated_index_links": int(len(source_manifest)),
            "parsed_pages": int((source_manifest.parse_status == "parsed").sum()),
            "broken_index_links": source_manifest.loc[source_manifest.parse_status == "broken_index_link", "source_date"].tolist(),
            "limitation": "The canonical dataset contains only observations present on successfully retrieved public pages. Broken index links remain missing and were not interpolated.",
        },
        "missing_data_policy": "No rows are created for source dashes or missing pages; no Grade 2 discount, fill, interpolation, or resampling is used.",
        "old_local_artifact": old_summary,
        "newer_than_old_cutoff": {
            "cutoff": OLD_CUTOFF.date().isoformat(),
            "source_dates": sorted(str(pd.Timestamp(d).date()) for d in national.loc[national.date > OLD_CUTOFF, "date"].unique()),
            "observations_by_grade": {grade: int(len(group)) for grade, group in national[national.date > OLD_CUTOFF].groupby("grade")},
        },
        "split": split_summary,
        "reproducibility": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "seed": SEED},
        "integrity": {"no_fabricated_grade2": True, "no_resampling": True, "no_interpolation": True, "no_random_split": True, "features_are_current_or_backward_looking": True},
    }
    (OUT / "eac_pepper_price_quality_report.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    (OUT / "temporal_split_definition.json").write_text(json.dumps(split_summary, indent=2), encoding="utf-8")
    plots(national, relationship, forecasting)
    print(json.dumps({"canonical_rows": len(raw), "national_rows": len(national), "relationship_rows": len(relationship), "forecast_rows": len(forecasting), "split": split_summary}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
