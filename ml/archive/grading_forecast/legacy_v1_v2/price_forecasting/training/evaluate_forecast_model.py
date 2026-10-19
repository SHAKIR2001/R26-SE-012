from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    mape = float(np.mean(np.abs((y_true - y_pred) / np.clip(np.abs(y_true), 1.0, None)))) * 100.0
    r2 = float(r2_score(y_true, y_pred))
    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "mape": round(mape, 4), "r2": round(r2, 4)}


def _is_v2_path(path: Path, marker: str) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return marker.lower() in normalized


def _date_range_payload(dates: pd.Series) -> dict[str, str | None]:
    clean = pd.to_datetime(dates, errors="coerce").dropna()
    if clean.empty:
        return {"start": None, "end": None}
    return {"start": str(clean.min().date()), "end": str(clean.max().date())}


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
    df = series_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "price_lkr_per_kg"]).sort_values("date", ascending=True)
    df["price_lkr_per_kg"] = pd.to_numeric(df["price_lkr_per_kg"], errors="coerce")
    df = df.dropna(subset=["price_lkr_per_kg"])

    df = _add_time_features(df)

    for lag in lags:
        df[f"lag_{lag}"] = df["price_lkr_per_kg"].shift(lag)

    shifted = df["price_lkr_per_kg"].shift(1)
    for w in rolling_windows:
        df[f"rolling_mean_{w}"] = shifted.rolling(window=w, min_periods=w).mean()
        df[f"rolling_std_{w}"] = shifted.rolling(window=w, min_periods=w).std()

    df["price_change_1w"] = df["price_lkr_per_kg"] - df["lag_1"]
    df["price_change_pct_1w"] = df["price_change_1w"] / df["lag_1"].clip(lower=eps)
    df["y_next_price"] = df["price_lkr_per_kg"].shift(-1)
    df["prediction_date"] = df["date"].shift(-1)
    return df


def build_test_prediction_frame(
    target_df: pd.DataFrame,
    test_df: pd.DataFrame,
    *,
    lags: list[int],
    rolling_windows: list[int],
    eps: float,
) -> pd.DataFrame:
    """
    Build one-step-ahead prediction rows for the test target dates.

    Row date is the feature timestamp t. prediction_date is the target timestamp t+1.
    This keeps lag/rolling features past-only while allowing the first test target
    to use the final validation observation as its immediate history.
    """
    test_dates = pd.to_datetime(test_df["date"], errors="coerce").dropna()
    feature_frame = build_features(target_df, lags=lags, rolling_windows=rolling_windows, eps=eps)
    feature_frame = feature_frame.dropna(subset=["prediction_date"])
    out = feature_frame[feature_frame["prediction_date"].isin(set(test_dates))].copy()
    out = out.sort_values("prediction_date", ascending=True).reset_index(drop=True)
    out["feature_date"] = out["date"]
    return out


def _validate_v2_paths(*, target_csv: Path | None, test_csv: Path, models_dir: Path, output_dir: Path) -> None:
    if target_csv is None:
        raise ValueError("--target-csv is required for V2 same-row evaluation.")
    if not _is_v2_path(target_csv, "data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv"):
        raise ValueError(f"Expected V2 target CSV, got: {target_csv}")
    if not _is_v2_path(test_csv, "data/processed/grading_forecast/price_v2/forecast_test.csv"):
        raise ValueError(f"Expected V2 test CSV, got: {test_csv}")
    if not _is_v2_path(models_dir, "ml/grading_forecast/price_forecasting/models/v2"):
        raise ValueError(f"Expected V2 models directory, got: {models_dir}")
    if not _is_v2_path(output_dir, "ml/grading_forecast/price_forecasting/evaluation/_outputs/v2"):
        raise ValueError(f"Expected V2 output directory, got: {output_dir}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate RandomForest forecasting model on test set.")
    parser.add_argument("--test-csv", type=Path, default=None, help="Test CSV path (test_forecast_data.csv).")
    parser.add_argument("--target-csv", type=Path, default=None, help="Full target CSV used to build past-only test features.")
    parser.add_argument("--models-dir", type=Path, default=None, help="Models dir containing joblib + features json.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for evaluation plots.")
    parser.add_argument("--split-name", default="test", help="Split name recorded in metrics.")
    parser.add_argument("--require-v2-paths", action="store_true", help="Fail unless V2 input/output paths are used.")
    parser.add_argument("--dry-run", action="store_true", help="Validate evaluation plan without loading model or writing metrics/plots.")
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    test_csv = args.test_csv or (
        repo_root / "data" / "processed" / "grading_forecast" / "test_forecast_data.csv"
    )
    if not test_csv.exists():
        print(f"Missing test CSV: {test_csv}")
        return 2

    models_dir = args.models_dir or (repo_root / "ml" / "grading_forecast" / "price_forecasting" / "models")
    out_dir = args.output_dir or (
        repo_root / "ml" / "grading_forecast" / "price_forecasting" / "evaluation" / "_outputs"
    )

    if args.require_v2_paths:
        try:
            _validate_v2_paths(target_csv=args.target_csv, test_csv=test_csv, models_dir=models_dir, output_dir=out_dir)
        except ValueError as exc:
            print(str(exc))
            return 5

    model_path = models_dir / "forecast_model.joblib"
    features_path = models_dir / "forecast_features.json"
    if not args.dry_run and (not model_path.exists() or not features_path.exists()):
        print(f"Missing artifacts. Need: {model_path} and {features_path}")
        return 3

    if features_path.exists():
        spec = json.loads(features_path.read_text(encoding="utf-8"))
    else:
        spec = {
            "lags": [1, 2, 3],
            "rolling_windows": [3, 5],
            "eps": 1.0,
            "feature_names": [
                "lag_1",
                "lag_2",
                "lag_3",
                "rolling_mean_3",
                "rolling_std_3",
                "rolling_mean_5",
                "rolling_std_5",
                "month",
                "week_of_year",
                "price_change_1w",
                "price_change_pct_1w",
            ],
        }
    feature_names: list[str] = list(spec["feature_names"])

    test_df = pd.read_csv(test_csv)
    if args.target_csv:
        target_df = pd.read_csv(args.target_csv)
        feats = build_test_prediction_frame(
            target_df,
            test_df,
            lags=list(spec["lags"]),
            rolling_windows=list(spec["rolling_windows"]),
            eps=float(spec["eps"]),
        )
        evaluation_mode = "full_target_context_same_test_timestamps"
    else:
        feats = build_features(
            test_df,
            lags=list(spec["lags"]),
            rolling_windows=list(spec["rolling_windows"]),
            eps=float(spec["eps"]),
        )
        feats["feature_date"] = feats["date"]
        evaluation_mode = "test_csv_only_legacy"

    feats = feats.dropna(subset=feature_names + ["y_next_price"]).copy()
    if feats.empty:
        print("Not enough test rows after feature engineering.")
        return 4

    test_dates = pd.to_datetime(test_df["date"], errors="coerce").dropna()
    prediction_dates = pd.to_datetime(feats.get("prediction_date", feats["date"]), errors="coerce")
    same_test_dates = set(prediction_dates.dt.date) == set(test_dates.dt.date)
    feature_before_prediction = bool((pd.to_datetime(feats["feature_date"]) < prediction_dates).all()) if "prediction_date" in feats.columns else None
    dry_payload = {
        "split_name": args.split_name,
        "evaluation_mode": evaluation_mode,
        "target_csv": str(args.target_csv) if args.target_csv else None,
        "test_csv": str(test_csv),
        "models_dir": str(models_dir),
        "output_dir": str(out_dir),
        "model_path": str(model_path),
        "features_path": str(features_path),
        "feature_names": feature_names,
        "test_input_rows": int(len(test_df)),
        "prediction_rows": int(len(feats)),
        "test_date_range": _date_range_payload(test_df["date"]),
        "prediction_date_range": _date_range_payload(prediction_dates),
        "same_test_timestamps": bool(same_test_dates),
        "feature_date_before_prediction_date": feature_before_prediction,
        "naive_persistence_definition": "prediction(t+1) = observed price(t)",
        "metrics_would_write": {
            "combined_metrics": str(models_dir / "forecast_metrics.json"),
            "naive_metrics": str(models_dir / "naive_persistence_metrics.json"),
            "actual_vs_predicted": str(out_dir / "actual_vs_predicted.png"),
            "feature_importances": str(out_dir / "feature_importances.png"),
        },
    }
    if args.dry_run:
        print(json.dumps(dry_payload, indent=2))
        return 0

    naive_pred = feats["price_lkr_per_kg"].astype(float).to_numpy()
    y = feats["y_next_price"].astype(float).to_numpy()
    naive_metrics = _metrics(y, naive_pred)
    X = feats[feature_names].astype(float).to_numpy()

    model = joblib.load(model_path)
    pred = np.asarray(model.predict(X), dtype=float)

    test_metrics = _metrics(y, pred)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Actual vs predicted
    fig = plt.figure(figsize=(8.0, 4.2))
    ax = fig.add_subplot(1, 1, 1)
    x = pd.to_datetime(feats.get("prediction_date", feats["date"]), errors="coerce")
    ax.plot(x, y, label="actual")
    ax.plot(x, naive_pred, label="naive persistence")
    ax.plot(x, pred, label="random forest")
    ax.set_title(f"Price Forecast: Actual vs Predicted ({args.split_name})")
    ax.set_xlabel("Prediction date")
    ax.set_ylabel("Price (LKR/kg)")
    ax.legend()
    fig.tight_layout()
    avp_path = out_dir / "actual_vs_predicted.png"
    fig.savefig(avp_path, dpi=140)
    plt.close(fig)

    # Residuals
    residuals = y - pred
    fig2 = plt.figure(figsize=(8.0, 4.2))
    ax2 = fig2.add_subplot(1, 1, 1)
    ax2.plot(residuals, label="residuals")
    ax2.axhline(0.0, color="black", linewidth=1)
    ax2.set_title("Price Forecast: Residuals (Test)")
    ax2.set_xlabel("Test index (chronological)")
    ax2.set_ylabel("Actual - Predicted")
    fig2.tight_layout()
    res_path = out_dir / "residuals.png"
    fig2.savefig(res_path, dpi=140)
    plt.close(fig2)

    # Feature importances (if available)
    importances_payload: dict[str, Any] | None = None
    if hasattr(model, "feature_importances_"):
        importances = np.asarray(getattr(model, "feature_importances_"), dtype=float)
        pairs = sorted(zip(feature_names, importances.tolist(), strict=False), key=lambda x: x[1], reverse=True)
        importances_payload = {"feature_importances": [{"feature": f, "importance": round(float(v), 6)} for f, v in pairs]}

        fig3 = plt.figure(figsize=(8.2, 4.6))
        ax3 = fig3.add_subplot(1, 1, 1)
        top = pairs[:12]
        ax3.bar([p[0] for p in top][::-1], [p[1] for p in top][::-1])
        ax3.set_title("Random Forest Feature Importances (Top 12)")
        ax3.set_xlabel("Importance")
        fig3.tight_layout()
        imp_path = out_dir / "feature_importances.png"
        fig3.savefig(imp_path, dpi=140)
        plt.close(fig3)
    else:
        imp_path = None

    metrics_path = models_dir / "forecast_metrics.json"
    existing: dict[str, Any] = {}
    if metrics_path.exists():
        try:
            existing = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    existing["evaluated_at"] = _utc_now_iso()
    existing["split_name"] = args.split_name
    existing["evaluation_mode"] = evaluation_mode
    existing["target_csv"] = str(args.target_csv) if args.target_csv else None
    existing["test_csv"] = str(test_csv)
    existing["test_input_rows"] = int(len(test_df))
    existing["prediction_rows"] = int(len(feats))
    existing["same_test_timestamps"] = bool(same_test_dates)
    existing["feature_date_before_prediction_date"] = feature_before_prediction
    existing["test_metrics"] = test_metrics
    existing["naive_persistence_metrics"] = naive_metrics
    existing["comparison"] = {
        "Naive Persistence": naive_metrics,
        "RandomForest": test_metrics,
    }
    existing["prediction_dates"] = [str(pd.Timestamp(d).date()) for d in prediction_dates]
    existing["artifacts"] = {
        "actual_vs_predicted_png": str(avp_path),
        "residuals_png": str(res_path),
        "feature_importances_png": str(imp_path) if imp_path else None,
    }
    if importances_payload:
        existing.update(importances_payload)

    metrics_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    (models_dir / "naive_persistence_metrics.json").write_text(
        json.dumps(
            {
                "evaluated_at": existing["evaluated_at"],
                "split_name": args.split_name,
                "definition": "prediction(t+1) = observed price(t)",
                "target_csv": str(args.target_csv) if args.target_csv else None,
                "test_csv": str(test_csv),
                "prediction_rows": int(len(feats)),
                "same_test_timestamps": bool(same_test_dates),
                "metrics": naive_metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote updated metrics -> {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
