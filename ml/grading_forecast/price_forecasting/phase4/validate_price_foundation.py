"""Focused integrity checks for the reconstructed Phase 4 price foundation."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
RAW_DIR = ROOT / "data/raw/market_prices/eac_phase4"
DATA_DIR = ROOT / "data/processed/grading_forecast/price/eac_reconstructed_v1"
OUTPUT_DIR = ROOT / "ml/grading_forecast/price_forecasting/phase4/outputs"
KEY = ["date", "market", "commodity", "grade", "price_type", "market_level"]


def check(condition: bool, name: str, details: str = "") -> dict:
    return {"check": name, "passed": bool(condition), "details": details}


def main() -> int:
    raw_path = sorted(RAW_DIR.glob("dea_eac_pepper_observations_retrieved_*.csv"))[-1]
    raw = pd.read_csv(raw_path)
    canonical = pd.read_csv(DATA_DIR / "eac_pepper_price_canonical.csv")
    forecasting = pd.read_csv(DATA_DIR / "eac_forecasting_dataset.csv", parse_dates=["date", "next_observation_date"])
    manifest = pd.read_csv(DATA_DIR / "eac_pepper_price_source_manifest.csv")
    metrics = json.loads((OUTPUT_DIR / "phase4_forecasting_metrics.json").read_text(encoding="utf-8"))

    normalized_raw = raw.copy()
    normalized_raw["market"] = normalized_raw["market"].str.replace("_", " ", regex=False).str.strip().str.title()
    raw_values = normalized_raw[KEY + ["price_lkr_per_kg", "source_url"]].sort_values(KEY).reset_index(drop=True)
    canonical_values = canonical[KEY + ["price_lkr_per_kg", "source_url"]].sort_values(KEY).reset_index(drop=True)
    value_identity = raw_values.equals(canonical_values)

    ordered = forecasting.sort_values(["grade", "date"]).copy()
    target_formula = ordered["price_lkr_per_kg"].mul(1 + ordered["target_return_next"])
    next_prices = ordered.groupby("grade")["price_lkr_per_kg"].shift(-1)
    target_ok = np.allclose(target_formula.dropna().to_numpy(), next_prices[target_formula.notna()].to_numpy(), atol=1e-10)
    chronological_targets = forecasting.loc[forecasting["next_observation_date"].notna(), "next_observation_date"].gt(
        forecasting.loc[forecasting["next_observation_date"].notna(), "date"]
    ).all()
    feature_checks = {
        "price_lag_1": ordered.groupby("grade")["price_lkr_per_kg"].shift(1),
        "price_lag_2": ordered.groupby("grade")["price_lkr_per_kg"].shift(2),
        "return_lag_1": ordered.groupby("grade")["return"].shift(1),
    }
    backward_features_ok = all(
        np.allclose(ordered[column].fillna(-999999), expected.fillna(-999999), atol=1e-10)
        for column, expected in feature_checks.items()
    )
    checks = [
        check(not canonical.duplicated(KEY).any(), "no_duplicate_canonical_observations"),
        check(value_identity, "canonical_values_identical_to_normalized_raw_extraction", f"rows={len(canonical)}"),
        check(set(canonical["observation_status"]) == {"observed_source_value"}, "no_fabricated_observation_status"),
        check(set(canonical["grade"]) == {"Grade 1", "Grade 2"}, "expected_grades_only"),
        check(chronological_targets, "all_targets_strictly_after_feature_date"),
        check(target_ok, "target_return_matches_next_observed_price"),
        check(backward_features_ok, "lag_features_are_backward_looking"),
        check(not metrics["integrity"]["random_split"], "no_random_temporal_split"),
        check(not metrics["integrity"]["test_used_for_selection"], "test_not_used_for_selection"),
        check(not metrics["integrity"]["external_used_for_selection"], "external_not_used_for_selection"),
        check((forecasting.loc[forecasting.partition == "EXTERNAL_NEWEST", "next_observation_date"] > pd.Timestamp("2026-08-18")).all(), "newest_observations_isolated_after_old_cutoff"),
        check(int((manifest["parse_status"] == "broken_index_link").sum()) == 2, "broken_source_links_explicitly_recorded"),
    ]
    report = {
        "phase": 4, "validated_on": date.today().isoformat(), "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "latest_source_date": str(pd.to_datetime(canonical["date"]).max().date()),
        "latest_g1_date": str(pd.to_datetime(canonical.loc[canonical.grade == "Grade 1", "date"]).max().date()),
        "latest_g2_date": str(pd.to_datetime(canonical.loc[canonical.grade == "Grade 2", "date"]).max().date()),
        "scope": "Focused data, temporal, feature, and evaluation-protocol validation; no backend/mobile integration tests.",
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "phase4_integrity_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
