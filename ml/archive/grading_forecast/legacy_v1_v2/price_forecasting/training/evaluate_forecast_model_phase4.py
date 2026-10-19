"""Phase 4 Limited Improvement — Evaluate RandomForest with extended lag features.

Evaluates a Phase 4 forecast model against the same 36 V2 test timestamps.
Compares against both naive persistence and the Phase 3 RandomForest baseline.
Writes combined metrics, naive persistence metrics, and evaluation plots.

Usage:

    python ml/grading_forecast/price_forecasting/training/evaluate_forecast_model_phase4.py \
        --target-csv data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv \
        --test-csv data/processed/grading_forecast/price_v2/forecast_test.csv \
        --models-dir ml/grading_forecast/price_forecasting/models/v2_phase4 \
        --phase3-models-dir ml/grading_forecast/price_forecasting/models/v2 \
        --output-dir ml/grading_forecast/price_forecasting/evaluation/_outputs/v2_phase4 \
        --split-name test

Rules preserved:
- Evaluates on exactly the same 36 V2 test timestamps as Phase 3.
- Feature dates are strictly before prediction dates (past-only).
- No test-set tuning occurred.
- Phase 3 baseline artifacts are not modified.
"""

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
    """Build one-step-ahead prediction rows for the test target dates."""
    test_dates = pd.to_datetime(test_df["date"], errors="coerce").dropna()
    feature_frame = build_features(target_df, lags=lags, rolling_windows=rolling_windows, eps=eps)
    feature_frame = feature_frame.dropna(subset=["prediction_date"])
    out = feature_frame[feature_frame["prediction_date"].isin(set(test_dates))].copy()
    out = out.sort_values("prediction_date", ascending=True).reset_index(drop=True)
    out["feature_date"] = out["date"]
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 4: Evaluate extended-lag RandomForest on V2 test set."
    )
    parser.add_argument("--test-csv", type=Path, required=True, help="Test CSV path.")
    parser.add_argument("--target-csv", type=Path, required=True, help="Full target CSV.")
    parser.add_argument("--models-dir", type=Path, required=True, help="Phase 4 models dir.")
    parser.add_argument("--phase3-models-dir", type=Path, default=None, help="Phase 3 models dir for comparison.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for evaluation plots.")
    parser.add_argument("--split-name", default="test", help="Split name recorded in metrics.")
    args = parser.parse_args(argv)

    if not args.test_csv.exists():
        print(f"Missing test CSV: {args.test_csv}")
        return 2
    if not args.target_csv.exists():
        print(f"Missing target CSV: {args.target_csv}")
        return 2

    model_path = args.models_dir / "forecast_model.joblib"
    features_path = args.models_dir / "forecast_features.json"
    if not model_path.exists():
        print(f"Missing model: {model_path}")
        return 3
    if not features_path.exists():
        print(f"Missing features JSON: {features_path}")
        return 3

    spec = json.loads(features_path.read_text(encoding="utf-8"))
    feature_names: list[str] = list(spec["feature_names"])

    test_df = pd.read_csv(args.test_csv)
    target_df = pd.read_csv(args.target_csv)

    feats = build_test_prediction_frame(
        target_df,
        test_df,
        lags=list(spec["lags"]),
        rolling_windows=list(spec["rolling_windows"]),
        eps=float(spec["eps"]),
    )
    feats = feats.dropna(subset=feature_names + ["y_next_price"]).copy()
    if feats.empty:
        print("Not enough test rows after feature engineering.")
        return 4

    test_dates_set = set(pd.to_datetime(test_df["date"], errors="coerce").dropna().dt.date)
    prediction_dates = pd.to_datetime(feats.get("prediction_date", feats["date"]), errors="coerce")
    same_test_dates = set(prediction_dates.dt.date) == test_dates_set
    feature_before_prediction = bool(
        (pd.to_datetime(feats["feature_date"]) < prediction_dates).all()
    ) if "prediction_date" in feats.columns else None

    # Compute metrics
    naive_pred = feats["price_lkr_per_kg"].astype(float).to_numpy()
    y = feats["y_next_price"].astype(float).to_numpy()
    naive_metrics = _metrics(y, naive_pred)

    X = feats[feature_names].astype(float).to_numpy()
    model = joblib.load(model_path)
    pred = np.asarray(model.predict(X), dtype=float)
    test_metrics = _metrics(y, pred)

    # Load phase3 RF for comparison plot (optional)
    phase3_pred: np.ndarray | None = None
    phase3_metrics: dict[str, float] | None = None
    if args.phase3_models_dir is not None:
        p3_model_path = args.phase3_models_dir / "forecast_model.joblib"
        p3_features_path = args.phase3_models_dir / "forecast_features.json"
        if p3_model_path.exists() and p3_features_path.exists():
            p3_spec = json.loads(p3_features_path.read_text(encoding="utf-8"))
            p3_feature_names: list[str] = list(p3_spec["feature_names"])
            p3_feats = build_test_prediction_frame(
                target_df,
                test_df,
                lags=list(p3_spec["lags"]),
                rolling_windows=list(p3_spec["rolling_windows"]),
                eps=float(p3_spec["eps"]),
            )
            p3_feats = p3_feats.dropna(subset=p3_feature_names + ["y_next_price"]).copy()
            if not p3_feats.empty:
                p3_model = joblib.load(p3_model_path)
                X_p3 = p3_feats[p3_feature_names].astype(float).to_numpy()
                phase3_pred = np.asarray(p3_model.predict(X_p3), dtype=float)
                y_p3 = p3_feats["y_next_price"].astype(float).to_numpy()
                phase3_metrics = _metrics(y_p3, phase3_pred)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Actual vs predicted
    fig = plt.figure(figsize=(8.0, 4.2))
    ax = fig.add_subplot(1, 1, 1)
    x_dates = pd.to_datetime(feats.get("prediction_date", feats["date"]), errors="coerce")
    ax.plot(x_dates, y, label="actual")
    ax.plot(x_dates, naive_pred, label="naive persistence")
    ax.plot(x_dates, pred, label="RF phase4 (extended lags)")
    if phase3_pred is not None and len(phase3_pred) == len(y):
        ax.plot(x_dates, phase3_pred, label="RF phase3 baseline", linestyle="--", alpha=0.6)
    ax.set_title(f"Price Forecast: Actual vs Predicted ({args.split_name}) — Phase 4")
    ax.set_xlabel("Prediction date")
    ax.set_ylabel("Price (LKR/kg)")
    ax.legend()
    fig.tight_layout()
    avp_path = args.output_dir / "actual_vs_predicted.png"
    fig.savefig(avp_path, dpi=140)
    plt.close(fig)

    # Residuals
    residuals = y - pred
    fig2 = plt.figure(figsize=(8.0, 4.2))
    ax2 = fig2.add_subplot(1, 1, 1)
    ax2.plot(residuals, label="residuals")
    ax2.axhline(0.0, color="black", linewidth=1)
    ax2.set_title("Price Forecast: Residuals (Test) — Phase 4")
    ax2.set_xlabel("Test index (chronological)")
    ax2.set_ylabel("Actual - Predicted")
    fig2.tight_layout()
    res_path = args.output_dir / "residuals.png"
    fig2.savefig(res_path, dpi=140)
    plt.close(fig2)

    # Feature importances
    importances_payload: dict[str, Any] | None = None
    imp_path: Path | None = None
    if hasattr(model, "feature_importances_"):
        importances = np.asarray(getattr(model, "feature_importances_"), dtype=float)
        pairs = sorted(zip(feature_names, importances.tolist(), strict=False), key=lambda x: x[1], reverse=True)
        importances_payload = {
            "feature_importances": [{"feature": f, "importance": round(float(v), 6)} for f, v in pairs]
        }
        fig3 = plt.figure(figsize=(9.0, 4.6))
        ax3 = fig3.add_subplot(1, 1, 1)
        top = pairs[:15]
        ax3.bar([p[0] for p in top][::-1], [p[1] for p in top][::-1])
        ax3.set_title("Random Forest Feature Importances — Phase 4 (Top 15)")
        ax3.set_xlabel("Importance")
        fig3.tight_layout()
        imp_path = args.output_dir / "feature_importances.png"
        fig3.savefig(imp_path, dpi=140)
        plt.close(fig3)

    # Write combined metrics
    metrics_payload: dict[str, Any] = {
        "evaluated_at": _utc_now_iso(),
        "phase": "phase4",
        "improvement": "extended_lag_features",
        "model": f"random_forest_regressor_v2_phase4",
        "split_name": args.split_name,
        "evaluation_mode": "full_target_context_same_test_timestamps",
        "target_csv": str(args.target_csv),
        "test_csv": str(args.test_csv),
        "test_input_rows": int(len(test_df)),
        "prediction_rows": int(len(feats)),
        "same_test_timestamps": bool(same_test_dates),
        "feature_date_before_prediction_date": feature_before_prediction,
        "test_metrics": test_metrics,
        "naive_persistence_metrics": naive_metrics,
        "phase3_rf_test_metrics": phase3_metrics,
        "comparison": {
            "Naive Persistence": naive_metrics,
            "Phase3 RandomForest (lags 1-3)": phase3_metrics or {},
            "Phase4 RandomForest (lags 1-3-4-8-12)": test_metrics,
        },
        "prediction_dates": [str(pd.Timestamp(d).date()) for d in prediction_dates],
        "artifacts": {
            "actual_vs_predicted_png": str(avp_path),
            "residuals_png": str(res_path),
            "feature_importances_png": str(imp_path) if imp_path else None,
        },
    }
    if importances_payload:
        metrics_payload.update(importances_payload)

    metrics_path = args.models_dir / "forecast_metrics.json"
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    # Write naive persistence metrics
    (args.models_dir / "naive_persistence_metrics.json").write_text(
        json.dumps(
            {
                "evaluated_at": metrics_payload["evaluated_at"],
                "split_name": args.split_name,
                "definition": "prediction(t+1) = observed price(t)",
                "target_csv": str(args.target_csv),
                "test_csv": str(args.test_csv),
                "prediction_rows": int(len(feats)),
                "same_test_timestamps": bool(same_test_dates),
                "metrics": naive_metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Wrote metrics -> {metrics_path}")
    print(f"Prediction rows: {len(feats)}")
    print(f"Same test timestamps: {same_test_dates}")
    print(f"Feature date before prediction date: {feature_before_prediction}")
    print(f"Naive Persistence: {json.dumps(naive_metrics)}")
    print(f"Phase 4 RF: {json.dumps(test_metrics)}")
    if phase3_metrics:
        print(f"Phase 3 RF (comparison): {json.dumps(phase3_metrics)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
