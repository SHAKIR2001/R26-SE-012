from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def _git_sha(repo_root: Path) -> str | None:
    head = repo_root / ".git" / "HEAD"
    if not head.exists():
        return None
    try:
        ref = head.read_text(encoding="utf-8").strip()
    except Exception:
        return None
    if ref.startswith("ref:"):
        ref_path = repo_root / ".git" / ref.replace("ref:", "").strip()
        try:
            return ref_path.read_text(encoding="utf-8").strip()
        except Exception:
            return None
    return ref


def _set_seeds(seed: int) -> None:
    os.environ.setdefault("PYTHONHASHSEED", str(seed))
    random.seed(seed)
    np.random.seed(seed)


def _feature_spec(*, lags: list[int], rolling_windows: list[int], eps: float) -> dict[str, Any]:
    features: list[str] = []
    for lag in lags:
        features.append(f"lag_{lag}")
    for w in rolling_windows:
        features.append(f"rolling_mean_{w}")
        features.append(f"rolling_std_{w}")
    features.extend(["month", "week_of_year", "price_change_1w", "price_change_pct_1w"])
    return {"lags": lags, "rolling_windows": rolling_windows, "eps": eps, "feature_names": features}


TARGET_DEFINITION = {
    "commodity": "black_pepper",
    "country": "Sri Lanka",
    "district": "National",
    "grade": "Grade 1",
    "price_type": "average",
    "market_level": "farm_gate",
    "frequency": "weekly",
}


def _is_v2_path(path: Path, marker: str) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return marker.lower() in normalized


def _date_range_payload(df: pd.DataFrame) -> dict[str, str | None]:
    if df.empty or "date" not in df.columns:
        return {"start": None, "end": None}
    dates = pd.to_datetime(df["date"], errors="coerce").dropna()
    if dates.empty:
        return {"start": None, "end": None}
    return {"start": str(dates.min().date()), "end": str(dates.max().date())}


def _csv_summary(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    df = pd.read_csv(path)
    payload: dict[str, Any] = {"rows": int(len(df))}
    if "date" in df.columns:
        payload.update(_date_range_payload(df))
    return payload


def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["month"] = out["date"].dt.month.astype(int)
    out["week_of_year"] = out["date"].dt.isocalendar().week.astype(int)
    return out


def build_features(
    series_df: pd.DataFrame,
    *,
    lags: list[int],
    rolling_windows: list[int],
    eps: float,
) -> pd.DataFrame:
    """
    Build past-only features for next-step forecasting.

    Input: df with columns [date, price_lkr_per_kg] sorted ascending.
    Output: df with engineered features + target y_next_price.
    """
    df = series_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "price_lkr_per_kg"]).sort_values("date", ascending=True)
    df["price_lkr_per_kg"] = pd.to_numeric(df["price_lkr_per_kg"], errors="coerce")
    df = df.dropna(subset=["price_lkr_per_kg"])

    df = _add_time_features(df)

    # Lags
    for lag in lags:
        df[f"lag_{lag}"] = df["price_lkr_per_kg"].shift(lag)

    # Rolling stats: computed on shifted prices to avoid leaking current/future into feature window.
    shifted = df["price_lkr_per_kg"].shift(1)
    for w in rolling_windows:
        df[f"rolling_mean_{w}"] = shifted.rolling(window=w, min_periods=w).mean()
        df[f"rolling_std_{w}"] = shifted.rolling(window=w, min_periods=w).std()

    df["price_change_1w"] = df["price_lkr_per_kg"] - df["lag_1"]
    df["price_change_pct_1w"] = df["price_change_1w"] / df["lag_1"].clip(lower=eps)

    # Target: next week's price (one-step ahead)
    df["y_next_price"] = df["price_lkr_per_kg"].shift(-1)

    return df


def _validate_v2_paths(*, train_csv: Path, models_dir: Path) -> None:
    if not _is_v2_path(train_csv, "data/processed/grading_forecast/price_v2/forecast_train.csv"):
        raise ValueError(f"Expected V2 train CSV, got: {train_csv}")
    if not _is_v2_path(models_dir, "ml/grading_forecast/price_forecasting/models/v2"):
        raise ValueError(f"Expected V2 models directory, got: {models_dir}")


def _hash_feature_spec(spec: dict[str, Any]) -> str:
    b = json.dumps(spec, sort_keys=True).encode("utf-8")
    return hashlib.sha256(b).hexdigest()[:16]


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    # Avoid relying on sklearn's `squared=` kwarg (removed/changed in some versions).
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    mape = float(np.mean(np.abs((y_true - y_pred) / np.clip(np.abs(y_true), 1.0, None)))) * 100.0
    r2 = float(r2_score(y_true, y_pred))
    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "mape": round(mape, 4), "r2": round(r2, 4)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train RandomForest forecasting model (one-step weekly).")
    parser.add_argument("--train-csv", type=Path, default=None, help="Train CSV path (train_forecast_data.csv).")
    parser.add_argument("--models-dir", type=Path, default=None, help="Output models directory.")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed.")
    parser.add_argument("--n-estimators", type=int, default=400, help="RandomForest n_estimators.")
    parser.add_argument("--max-depth", type=int, default=None, help="RandomForest max_depth.")
    parser.add_argument("--min-samples-leaf", type=int, default=1, help="RandomForest min_samples_leaf.")
    parser.add_argument("--n-jobs", type=int, default=-1, help="RandomForest n_jobs.")
    parser.add_argument("--train-linear-baseline", action="store_true", help="Also train LinearRegression baseline.")
    parser.add_argument("--dataset-version", default="v1", help="Dataset version recorded in metadata.")
    parser.add_argument("--artifact-version", default="v1", help="Artifact/model version recorded in metadata.")
    parser.add_argument("--target-csv", type=Path, default=None, help="Full target series CSV for metadata/dry-run checks.")
    parser.add_argument("--validation-csv", type=Path, default=None, help="Validation CSV for metadata/dry-run checks.")
    parser.add_argument("--test-csv", type=Path, default=None, help="Test CSV for metadata/dry-run checks.")
    parser.add_argument("--require-v2-paths", action="store_true", help="Fail unless V2 input/output paths are used.")
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration and feature schema without training.")
    args = parser.parse_args(argv)

    _set_seeds(args.seed)

    repo_root = _repo_root()
    train_csv = args.train_csv or (
        repo_root / "data" / "processed" / "grading_forecast" / "train_forecast_data.csv"
    )
    if not train_csv.exists():
        print(f"Missing train CSV: {train_csv}")
        return 2

    models_dir = args.models_dir or (repo_root / "ml" / "grading_forecast" / "price_forecasting" / "models")
    if args.require_v2_paths:
        try:
            _validate_v2_paths(train_csv=train_csv, models_dir=models_dir)
        except ValueError as exc:
            print(str(exc))
            return 4

    spec = _feature_spec(lags=[1, 2, 3], rolling_windows=[3, 5], eps=1.0)
    feature_hash = _hash_feature_spec(spec)

    df = pd.read_csv(train_csv)
    feats = build_features(df, lags=spec["lags"], rolling_windows=spec["rolling_windows"], eps=float(spec["eps"]))

    # Drop rows with insufficient history or missing target.
    feats = feats.dropna(subset=spec["feature_names"] + ["y_next_price"]).copy()
    if feats.empty:
        print("Not enough training rows after feature engineering.")
        return 3

    metadata_paths = {
        "train_csv": str(train_csv),
        "validation_csv": str(args.validation_csv) if args.validation_csv else None,
        "test_csv": str(args.test_csv) if args.test_csv else None,
        "target_csv": str(args.target_csv) if args.target_csv else None,
        "models_dir": str(models_dir),
    }
    split_inputs = {
        "target": _csv_summary(args.target_csv),
        "train": _csv_summary(train_csv),
        "validation": _csv_summary(args.validation_csv),
        "test": _csv_summary(args.test_csv),
    }
    dry_payload = {
        "dataset_version": args.dataset_version,
        "artifact_version": args.artifact_version,
        "target_definition": TARGET_DEFINITION,
        "split_strategy": "chronological_train_validation_test",
        "train_input_rows": int(len(df)),
        "train_feature_rows": int(len(feats)),
        "train_feature_date_range": _date_range_payload(feats),
        "feature_spec_hash": feature_hash,
        "feature_spec": spec,
        "rf_config": {
            "n_estimators": int(args.n_estimators),
            "random_state": int(args.seed),
            "n_jobs": int(args.n_jobs),
            "max_depth": None if args.max_depth is None else int(args.max_depth),
            "min_samples_leaf": int(args.min_samples_leaf),
        },
        "paths": metadata_paths,
        "split_inputs": split_inputs,
        "training_would_write": {
            "model": str(models_dir / "forecast_model.joblib"),
            "features": str(models_dir / "forecast_features.json"),
            "metrics": str(models_dir / "forecast_metrics.json"),
            "metadata": str(models_dir / "forecast_model_metadata.json"),
        },
    }

    if args.dry_run:
        print(json.dumps(dry_payload, indent=2))
        return 0

    models_dir.mkdir(parents=True, exist_ok=True)
    features_path = models_dir / "forecast_features.json"
    features_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")

    X = feats[spec["feature_names"]].astype(float).to_numpy()
    y = feats["y_next_price"].astype(float).to_numpy()

    rf = RandomForestRegressor(
        n_estimators=int(args.n_estimators),
        random_state=int(args.seed),
        n_jobs=int(args.n_jobs),
        max_depth=None if args.max_depth is None else int(args.max_depth),
        min_samples_leaf=int(args.min_samples_leaf),
    )
    rf.fit(X, y)

    pred = rf.predict(X)
    train_metrics = _metrics(y, pred)

    model_path = models_dir / "forecast_model.joblib"
    joblib.dump(rf, model_path)

    baseline_metrics: dict[str, Any] | None = None
    if args.train_linear_baseline:
        lr = LinearRegression()
        lr.fit(X, y)
        pred_lr = lr.predict(X)
        baseline_metrics = {"linear_regression": _metrics(y, pred_lr)}

    meta = {
        "model_name": "random_forest_regressor",
        "version": args.artifact_version,
        "dataset_version": args.dataset_version,
        "trained_at": _utc_now_iso(),
        "seed": int(args.seed),
        "git_sha": _git_sha(repo_root),
        "train_csv": str(train_csv),
        "validation_csv": str(args.validation_csv) if args.validation_csv else None,
        "test_csv": str(args.test_csv) if args.test_csv else None,
        "target_csv": str(args.target_csv) if args.target_csv else None,
        "target_definition": TARGET_DEFINITION,
        "split_strategy": "chronological_train_validation_test",
        "split_inputs": split_inputs,
        "feature_spec_hash": feature_hash,
        "feature_spec": spec,
        "n_rows": int(len(feats)),
        "date_range": {
            "start": str(pd.to_datetime(feats["date"]).min().date()),
            "end": str(pd.to_datetime(feats["date"]).max().date()),
        },
        "rf_params": rf.get_params(),
    }

    metrics_out = {
        "evaluated_at": _utc_now_iso(),
        "model": f"random_forest_regressor_{args.artifact_version}",
        "train_metrics": train_metrics,
        "baseline_metrics": baseline_metrics,
    }

    (models_dir / "forecast_model_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (models_dir / "forecast_metrics.json").write_text(json.dumps(metrics_out, indent=2), encoding="utf-8")

    print(f"Wrote model -> {model_path}")
    print(f"Wrote features -> {features_path}")
    print(f"Wrote metrics -> {models_dir / 'forecast_metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
