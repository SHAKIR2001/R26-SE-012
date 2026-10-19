"""Leakage-safe Phase 4 walk-forward evaluation for next-observation returns."""

from __future__ import annotations

import json
import platform
import time
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import confusion_matrix, mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = ROOT / "data/processed/grading_forecast/price/eac_reconstructed_v1"
OUT = ROOT / "ml/grading_forecast/price_forecasting/phase4/outputs"
SEED = 42
CORE_FEATURES = [
    "price_lkr_per_kg",
    "price_lag_1",
    "price_lag_2",
    "return",
    "return_lag_1",
    "rolling_price_mean_3",
    "rolling_return_std_3",
    "days_since_previous_observation",
]
MODEL_SPECS = {
    "separate_ridge": {"formulation": "separate", "algorithm": "ridge", "alpha": 1.0},
    "separate_random_forest": {
        "formulation": "separate", "algorithm": "random_forest", "n_estimators": 100,
        "max_depth": 5, "min_samples_leaf": 5,
    },
    "shared_ridge": {"formulation": "shared", "algorithm": "ridge", "alpha": 1.0},
    "shared_random_forest": {
        "formulation": "shared", "algorithm": "random_forest", "n_estimators": 100,
        "max_depth": 5, "min_samples_leaf": 5,
    },
}


def make_estimator(spec: dict):
    if spec["algorithm"] == "ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=spec["alpha"]))
    return RandomForestRegressor(
        n_estimators=spec["n_estimators"], max_depth=spec["max_depth"],
        min_samples_leaf=spec["min_samples_leaf"], random_state=SEED, n_jobs=-1,
    )


def available_history(frame: pd.DataFrame, origin: pd.Timestamp, grade: str | None) -> pd.DataFrame:
    # A past row is trainable only once its next-observation target was known.
    history = frame[frame["next_observation_date"].le(origin)].copy()
    if grade is not None:
        history = history[history["grade"].eq(grade)]
    return history


def model_walk_forward(frame: pd.DataFrame, partition: str, model_name: str) -> pd.DataFrame:
    spec = MODEL_SPECS[model_name]
    features = CORE_FEATURES + (["grade_indicator"] if spec["formulation"] == "shared" else [])
    targets = frame[frame["partition"].eq(partition)].dropna(subset=features + ["target_return_next"]).copy()
    records: list[dict] = []
    for _, row in targets.sort_values(["next_observation_date", "grade"]).iterrows():
        grade_filter = row["grade"] if spec["formulation"] == "separate" else None
        history = available_history(frame, pd.Timestamp(row["date"]), grade_filter)
        history = history.dropna(subset=features + ["target_return_next"])
        if len(history) < 20:
            raise RuntimeError(f"Insufficient history for {model_name} at {row['date']}: {len(history)} rows")
        estimator = make_estimator(spec)
        estimator.fit(history[features], history["target_return_next"])
        predicted_return = float(estimator.predict(pd.DataFrame([{f: row[f] for f in features}]))[0])
        records.append(prediction_record(row, model_name, predicted_return, len(history)))
    return pd.DataFrame(records)


def baseline_walk_forward(frame: pd.DataFrame, partition: str, baseline: str) -> pd.DataFrame:
    targets = frame[frame["partition"].eq(partition)].dropna(subset=CORE_FEATURES + ["target_return_next"]).copy()
    records: list[dict] = []
    for _, row in targets.sort_values(["next_observation_date", "grade"]).iterrows():
        history = available_history(frame, pd.Timestamp(row["date"]), row["grade"]).dropna(subset=["target_return_next"])
        if baseline == "zero_return_persistence":
            predicted_return = 0.0
        elif baseline == "last_observed_return":
            predicted_return = float(row["return"])
        elif baseline == "expanding_mean_return":
            predicted_return = float(history["target_return_next"].mean())
        else:
            raise ValueError(baseline)
        records.append(prediction_record(row, baseline, predicted_return, len(history)))
    return pd.DataFrame(records)


def prediction_record(row, method: str, predicted_return: float, training_rows: int) -> dict:
    reference = float(row["price_lkr_per_kg"])
    actual_return = float(row["target_return_next"])
    actual_price = reference * (1.0 + actual_return)
    predicted_price = reference * (1.0 + predicted_return)
    # Source prices are published to 0.01 LKR; equality after source-resolution
    # rounding is the documented FLAT rule for predictions.
    rounded_reference = round(reference, 2)
    rounded_prediction = round(predicted_price, 2)
    predicted_direction = "UP" if rounded_prediction > rounded_reference else "DOWN" if rounded_prediction < rounded_reference else "FLAT"
    return {
        "method": method, "partition": row["partition"], "grade": row["grade"],
        "reference_date": pd.Timestamp(row["date"]), "target_date": pd.Timestamp(row["next_observation_date"]),
        "reference_price_lkr_per_kg": reference, "actual_return": actual_return,
        "predicted_return": predicted_return, "actual_price_lkr_per_kg": actual_price,
        "predicted_price_lkr_per_kg": predicted_price, "actual_direction": row["target_direction_next"],
        "predicted_direction": predicted_direction, "training_rows": training_rows,
    }


def metric_block(predictions: pd.DataFrame) -> dict:
    actual_return = predictions["actual_return"].to_numpy()
    predicted_return = predictions["predicted_return"].to_numpy()
    actual_price = predictions["actual_price_lkr_per_kg"].to_numpy()
    predicted_price = predictions["predicted_price_lkr_per_kg"].to_numpy()
    labels = ["DOWN", "FLAT", "UP"]
    matrix = confusion_matrix(predictions["actual_direction"], predictions["predicted_direction"], labels=labels)
    nonflat = predictions[predictions["actual_direction"].ne("FLAT")]
    return {
        "observations": int(len(predictions)),
        "return_mae": float(mean_absolute_error(actual_return, predicted_return)),
        "return_rmse": float(np.sqrt(mean_squared_error(actual_return, predicted_return))),
        "return_r2": float(r2_score(actual_return, predicted_return)) if len(predictions) > 1 else None,
        "return_mape": None,
        "return_mape_reason": "Omitted because observed returns include and approach zero.",
        "directional_accuracy": float((predictions["actual_direction"] == predictions["predicted_direction"]).mean()),
        "nonflat_up_down_directional_accuracy": None if nonflat.empty else float((nonflat["actual_direction"] == nonflat["predicted_direction"]).mean()),
        "direction_labels": labels,
        "direction_confusion_matrix": matrix.tolist(),
        "derived_price_mae_lkr_per_kg": float(mean_absolute_error(actual_price, predicted_price)),
        "derived_price_rmse_lkr_per_kg": float(np.sqrt(mean_squared_error(actual_price, predicted_price))),
        "derived_price_mape_percent": float(np.mean(np.abs((actual_price - predicted_price) / actual_price)) * 100.0),
    }


def evaluate_methods(predictions: pd.DataFrame) -> dict:
    result = {}
    for method, method_rows in predictions.groupby("method"):
        by_grade = {grade: metric_block(rows) for grade, rows in method_rows.groupby("grade")}
        grade_rmses = [metrics["return_rmse"] for metrics in by_grade.values()]
        result[method] = {
            "overall": metric_block(method_rows), "by_grade": by_grade,
            "selection_score_macro_grade_return_rmse": float(np.mean(grade_rmses)),
        }
    return result


def forecast_plot(predictions: pd.DataFrame, selected: str) -> None:
    selected_rows = predictions[predictions["method"].eq(selected)]
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=False)
    for ax, (grade, rows) in zip(axes, selected_rows.groupby("grade")):
        rows = rows.sort_values("target_date")
        ax.plot(rows["target_date"], rows["actual_price_lkr_per_kg"], label="Actual EAC price", linewidth=1.5)
        ax.plot(rows["target_date"], rows["predicted_price_lkr_per_kg"], label="Walk-forward forecast", linewidth=1.2)
        ax.set_title(f"{grade}: Frozen Final Temporal Test")
        ax.set_ylabel("LKR per kg"); ax.grid(alpha=0.25); ax.legend()
    axes[-1].set_xlabel("Target observation date")
    fig.tight_layout(); fig.savefig(OUT / "05_walk_forward_forecast_vs_actual.png", dpi=160); plt.close(fig)


def main() -> int:
    started = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(DATA_DIR / "eac_forecasting_dataset.csv", parse_dates=["date", "source_date", "next_observation_date"])
    required = CORE_FEATURES + ["target_return_next", "grade_indicator"]
    if any(column not in frame for column in required):
        raise RuntimeError("Forecasting dataset is missing required columns")
    if not frame["partition"].isin(["TRAIN", "VALIDATION", "TEST", "EXTERNAL_NEWEST", "NO_TARGET"]).all():
        raise RuntimeError("Unexpected temporal partition")

    baselines = ["zero_return_persistence", "last_observed_return", "expanding_mean_return"]
    validation_parts = [baseline_walk_forward(frame, "VALIDATION", name) for name in baselines]
    validation_parts.extend(model_walk_forward(frame, "VALIDATION", name) for name in MODEL_SPECS)
    validation_predictions = pd.concat(validation_parts, ignore_index=True)
    validation_metrics = evaluate_methods(validation_predictions)
    selected = min(MODEL_SPECS, key=lambda name: validation_metrics[name]["selection_score_macro_grade_return_rmse"])
    persistence_validation_score = validation_metrics["zero_return_persistence"]["selection_score_macro_grade_return_rmse"]
    selected_beats_persistence_validation = validation_metrics[selected]["selection_score_macro_grade_return_rmse"] < persistence_validation_score

    final_methods = baselines + [selected]
    test_parts = [baseline_walk_forward(frame, "TEST", name) for name in baselines]
    test_parts.append(model_walk_forward(frame, "TEST", selected))
    test_predictions = pd.concat(test_parts, ignore_index=True)
    test_metrics = evaluate_methods(test_predictions)

    external_parts = [baseline_walk_forward(frame, "EXTERNAL_NEWEST", name) for name in baselines]
    external_parts.append(model_walk_forward(frame, "EXTERNAL_NEWEST", selected))
    external_predictions = pd.concat(external_parts, ignore_index=True)
    external_metrics = evaluate_methods(external_predictions)

    for name, table in [
        ("validation_walk_forward_predictions.csv", validation_predictions),
        ("final_test_walk_forward_predictions.csv", test_predictions),
        ("external_newest_reality_check.csv", external_predictions),
    ]:
        table.to_csv(OUT / name, index=False, date_format="%Y-%m-%d")
    forecast_plot(test_predictions, selected)

    results = {
        "phase": 4, "created_on": date.today().isoformat(), "seed": SEED,
        "primary_target": "next-observation percentage return",
        "forecast_horizon": "next observed DEA/EAC market observation; intervals retained as observed",
        "flat_rule": "Actual FLAT means exact equality in published source prices; predicted FLAT means derived price equals reference after rounding both to the source precision of 0.01 LKR.",
        "feature_set": CORE_FEATURES,
        "feature_timing": "All features are current or backward-looking at the reference date.",
        "walk_forward_rule": "For each forecast origin, fit only rows whose target observation date is on or before that origin.",
        "model_candidates": MODEL_SPECS, "baselines": baselines,
        "selection_metric": "lowest validation macro-average of per-grade return RMSE",
        "selected_ml_candidate": selected, "selected_ml_candidate_configuration": MODEL_SPECS[selected],
        "selected_ml_beats_persistence_on_validation": selected_beats_persistence_validation,
        "forecasting_decision": "No tested ML model demonstrated validation improvement over persistence; the best ML candidate is retained for transparent final comparison, not adopted as a superior final forecaster." if not selected_beats_persistence_validation else "The best ML candidate improved the validation selection score over persistence and was frozen for final comparison.",
        "validation": validation_metrics, "final_test": test_metrics,
        "external_newest_reality_check": external_metrics,
        "external_observation_policy": "Excluded from model/feature/hyperparameter selection; evaluated after final test using the frozen selected formulation.",
        "runtime_seconds": float(time.perf_counter() - started),
        "environment": {
            "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__,
            "scikit_learn": sklearn.__version__, "platform": platform.platform(),
        },
        "integrity": {
            "random_split": False, "test_used_for_selection": False, "external_used_for_selection": False,
            "full_dataset_scaling": False, "persistence_is_baseline_only": True,
        },
    }
    (OUT / "phase4_forecasting_metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    config = {key: results[key] for key in ["seed", "primary_target", "forecast_horizon", "flat_rule", "feature_set", "feature_timing", "walk_forward_rule", "model_candidates", "baselines", "selection_metric", "selected_ml_candidate", "selected_ml_candidate_configuration", "selected_ml_beats_persistence_on_validation", "forecasting_decision", "environment"]}
    (OUT / "phase4_experiment_configuration.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(json.dumps({
        "selected_ml_candidate": selected,
        "selected_ml_beats_persistence_on_validation": selected_beats_persistence_validation,
        "validation_selection_score": validation_metrics[selected]["selection_score_macro_grade_return_rmse"],
        "test_selected": test_metrics[selected],
        "test_persistence": test_metrics["zero_return_persistence"],
        "external_selected": external_metrics[selected],
        "external_persistence": external_metrics["zero_return_persistence"],
        "runtime_seconds": results["runtime_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
