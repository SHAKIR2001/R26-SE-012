"""Run controlled leakage-safe Phase 5 pepper-price experiments."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import time
from datetime import date
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
import yaml
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import confusion_matrix, mean_absolute_error, mean_squared_error, precision_recall_fscore_support, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[5]
PHASE5 = ROOT / "ml/grading_forecast/price_forecasting/phase5"
CONFIG_PATH = PHASE5 / "phase5_config.yaml"


def load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_modeling_data(config: dict[str, Any]) -> pd.DataFrame:
    canonical = pd.read_csv(ROOT / config["experiment"]["dataset_path"], parse_dates=["date", "source_date"])
    series = canonical[
        canonical["market"].eq(config["series"]["market"])
        & canonical["price_type"].eq(config["series"]["price_type"])
        & canonical["grade"].isin(config["series"]["grades"])
    ].copy()
    if series.duplicated(["date", "grade"]).any():
        raise RuntimeError("Duplicate National average date/grade rows in canonical input")
    series = series[["date", "grade", "price_lkr_per_kg", "source_url", "source_date", "observation_status"]]
    series = series.rename(columns={"price_lkr_per_kg": "current_price", "date": "feature_date"})

    built: list[pd.DataFrame] = []
    for _, grade_rows in series.groupby("grade"):
        g = grade_rows.sort_values("feature_date").copy()
        price = g["current_price"]
        completed_return = price.pct_change(fill_method=None)
        for lag in range(1, 5):
            g[f"return_lag_{lag}"] = completed_return.shift(lag - 1)
        g["days_since_previous_observation"] = g["feature_date"].diff().dt.days
        g["rolling_return_mean_3"] = completed_return.rolling(3, min_periods=3).mean()
        g["rolling_return_mean_5"] = completed_return.rolling(5, min_periods=5).mean()
        g["rolling_return_mean_10"] = completed_return.rolling(10, min_periods=10).mean()
        g["rolling_return_std_5"] = completed_return.rolling(5, min_periods=5).std()
        g["rolling_return_std_10"] = completed_return.rolling(10, min_periods=10).std()
        g["momentum_3"] = price / price.shift(3) - 1.0
        g["momentum_5"] = price / price.shift(5) - 1.0
        g["trend_vs_mean_5"] = price / price.rolling(5, min_periods=5).mean() - 1.0
        g["trend_vs_mean_10"] = price / price.rolling(10, min_periods=10).mean() - 1.0
        day_of_year = g["feature_date"].dt.dayofyear
        month = g["feature_date"].dt.month
        g["day_of_year_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
        g["day_of_year_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)
        g["month_sin"] = np.sin(2 * np.pi * month / 12.0)
        g["month_cos"] = np.cos(2 * np.pi * month / 12.0)
        g["target_date"] = g["feature_date"].shift(-1)
        g["actual_price"] = price.shift(-1)
        g["target_simple_return"] = g["actual_price"] / price - 1.0
        g["target_log_return"] = np.log(g["actual_price"] / price)
        g["target_price_delta"] = g["actual_price"] - price
        g["days_ahead"] = (g["target_date"] - g["feature_date"]).dt.days
        g["actual_direction"] = np.select(
            [g["target_simple_return"].gt(0), g["target_simple_return"].lt(0), g["target_simple_return"].eq(0)],
            ["UP", "DOWN", "FLAT"], default=None,
        )
        built.append(g)
    frame = pd.concat(built, ignore_index=True)

    wide_price = frame.pivot(index="feature_date", columns="grade", values="current_price")
    wide_return = frame.pivot(index="feature_date", columns="grade", values="return_lag_1")
    relationship = pd.DataFrame(index=wide_price.index)
    relationship["same_date_spread"] = wide_price["Grade 1"] - wide_price["Grade 2"]
    relationship["same_date_ratio"] = wide_price["Grade 2"] / wide_price["Grade 1"]
    frame = frame.merge(relationship.reset_index(), on="feature_date", how="left")
    other = pd.concat(
        [wide_return["Grade 1"].rename("g1_return"), wide_return["Grade 2"].rename("g2_return")], axis=1,
    ).reset_index()
    frame = frame.merge(other, on="feature_date", how="left")
    frame["other_grade_return_lag_1"] = np.where(frame["grade"].eq("Grade 1"), frame["g2_return"], frame["g1_return"])
    frame = frame.drop(columns=["g1_return", "g2_return"])
    frame["grade_indicator"] = frame["grade"].eq("Grade 2").astype(int)

    splits = config["splits"]
    target_date = frame["target_date"]
    frame["partition"] = np.select(
        [
            target_date.isna(),
            target_date.gt(pd.Timestamp(splits["test_last_target_date"])),
            target_date.le(pd.Timestamp(splits["train_last_target_date"])),
            target_date.le(pd.Timestamp(splits["validation_last_target_date"])),
            target_date.le(pd.Timestamp(splits["test_last_target_date"])),
        ],
        ["NO_TARGET", "EXTERNAL_NEWEST", "TRAIN", "VALIDATION", "TEST"],
        default="UNASSIGNED",
    )
    return frame.sort_values(["feature_date", "grade"]).reset_index(drop=True)


def make_estimator(name: str, config: dict[str, Any]):
    settings = config["ml_models"][name]
    seed = config["experiment"]["seed"]
    if name == "ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=settings["alpha"]))
    if name == "random_forest":
        return RandomForestRegressor(
            n_estimators=settings["n_estimators"], max_depth=settings["max_depth"],
            min_samples_leaf=settings["min_samples_leaf"], random_state=seed, n_jobs=settings["n_jobs"],
        )
    if name == "gradient_boosting":
        return GradientBoostingRegressor(
            n_estimators=settings["n_estimators"], learning_rate=settings["learning_rate"],
            max_depth=settings["max_depth"], min_samples_leaf=settings["min_samples_leaf"], random_state=seed,
        )
    raise ValueError(name)


def target_to_forecast(target: str, prediction: float, current_price: float) -> tuple[float, float]:
    if target == "simple_return":
        return prediction, current_price * (1.0 + prediction)
    if target == "log_return":
        predicted_price = current_price * math.exp(prediction)
        return predicted_price / current_price - 1.0, predicted_price
    if target == "price_delta":
        predicted_price = current_price + prediction
        return prediction / current_price, predicted_price
    raise ValueError(target)


def prediction_record(row: pd.Series, experiment: str, method: str, target: str, prediction: float, training_rows: int, feature_group: str, formulation: str) -> dict[str, Any]:
    predicted_return, predicted_price = target_to_forecast(target, prediction, float(row["current_price"]))
    reference_rounded, prediction_rounded = round(float(row["current_price"]), 2), round(predicted_price, 2)
    direction = "UP" if prediction_rounded > reference_rounded else "DOWN" if prediction_rounded < reference_rounded else "FLAT"
    return {
        "experiment": experiment, "method": method, "target": target, "feature_group": feature_group,
        "formulation": formulation, "partition": row["partition"], "grade": row["grade"],
        "feature_date": row["feature_date"], "target_date": row["target_date"], "days_ahead": int(row["days_ahead"]),
        "current_price": float(row["current_price"]), "actual_price": float(row["actual_price"]),
        "predicted_price": predicted_price, "actual_return": float(row["target_simple_return"]),
        "predicted_return": predicted_return, "actual_target": float(row[f"target_{target}"]),
        "predicted_target": prediction, "actual_direction": row["actual_direction"], "predicted_direction": direction,
        "days_since_previous_observation": float(row["days_since_previous_observation"]), "training_rows": training_rows,
    }


def available_history(frame: pd.DataFrame, origin: pd.Timestamp, target_column: str, features: list[str], grade: str | None) -> pd.DataFrame:
    history = frame[frame["target_date"].le(origin)].copy()
    if grade is not None:
        history = history[history["grade"].eq(grade)]
    return history.dropna(subset=features + [target_column])


def walk_forward_ml(frame: pd.DataFrame, partition: str, model_name: str, target: str, feature_group: str, formulation: str, config: dict[str, Any], experiment: str, cohort_features: list[str] | None = None) -> pd.DataFrame:
    features = list(config["feature_groups"][feature_group])
    if formulation == "shared":
        features.append("grade_indicator")
    target_column = config["targets"][target]["column"]
    required = list(dict.fromkeys(features + (cohort_features or []))) + [target_column]
    evaluation = frame[frame["partition"].eq(partition)].dropna(subset=required)
    minimum = config["experiment"]["minimum_training_observations"]
    rows: list[dict[str, Any]] = []
    for _, row in evaluation.sort_values(["target_date", "grade"]).iterrows():
        grade_filter = row["grade"] if formulation == "separate" else None
        history = available_history(frame, pd.Timestamp(row["feature_date"]), target_column, features, grade_filter)
        if len(history) < minimum:
            continue
        model = make_estimator(model_name, config)
        model.fit(history[features], history[target_column])
        prediction = float(model.predict(pd.DataFrame([{feature: row[feature] for feature in features}]))[0])
        rows.append(prediction_record(row, experiment, model_name, target, prediction, len(history), feature_group, formulation))
    return pd.DataFrame(rows)


def walk_forward_baseline(frame: pd.DataFrame, partition: str, name: str, config: dict[str, Any]) -> pd.DataFrame:
    evaluation = frame[frame["partition"].eq(partition)].dropna(subset=["target_simple_return", "return_lag_1"])
    rows: list[dict[str, Any]] = []
    for _, row in evaluation.sort_values(["target_date", "grade"]).iterrows():
        history = available_history(frame, pd.Timestamp(row["feature_date"]), "target_simple_return", [], row["grade"])
        if name == "persistence_zero_return":
            prediction = 0.0
        elif name == "last_observed_return":
            prediction = float(row["return_lag_1"])
        elif name == "expanding_mean_return":
            prediction = float(history["target_simple_return"].mean())
        elif name == "historical_price_drift":
            ordered = history.sort_values("target_date")
            drift_delta = (float(row["current_price"]) - float(ordered.iloc[0]["current_price"])) / max(1, len(ordered))
            prediction = drift_delta / float(row["current_price"])
        else:
            raise ValueError(name)
        rows.append(prediction_record(row, "baseline", name, "simple_return", prediction, len(history), "none", "grade_specific"))
    return pd.DataFrame(rows)


def walk_forward_statistical(frame: pd.DataFrame, partition: str, name: str, parameter: float | int, config: dict[str, Any]) -> pd.DataFrame:
    evaluation = frame[frame["partition"].eq(partition)].dropna(subset=["target_simple_return"])
    minimum = config["experiment"]["minimum_training_observations"]
    rows: list[dict[str, Any]] = []
    for _, row in evaluation.sort_values(["target_date", "grade"]).iterrows():
        history = available_history(frame, pd.Timestamp(row["feature_date"]), "target_simple_return", [], row["grade"])
        values = history.sort_values("target_date")["target_simple_return"].to_numpy()
        if len(values) < minimum:
            continue
        if name == "simple_exponential_smoothing":
            alpha, level = float(parameter), float(values[0])
            for value in values[1:]:
                level = alpha * float(value) + (1.0 - alpha) * level
            prediction, method = level, f"ses_alpha_{alpha:g}"
        elif name == "autoregressive":
            order = int(parameter)
            x = np.array([[values[i - lag] for lag in range(1, order + 1)] for i in range(order, len(values))])
            ar = LinearRegression().fit(x, values[order:])
            prediction = float(ar.predict(np.array([[values[-lag] for lag in range(1, order + 1)]]))[0])
            method = f"arima_{order}_0_0_conditional_ols"
        else:
            raise ValueError(name)
        rows.append(prediction_record(row, "statistical", method, "simple_return", prediction, len(history), "target_history", "grade_specific"))
    return pd.DataFrame(rows)


def metric_block(predictions: pd.DataFrame) -> dict[str, Any]:
    labels = ["DOWN", "FLAT", "UP"]
    actual_return, predicted_return = predictions["actual_return"].to_numpy(), predictions["predicted_return"].to_numpy()
    actual_price, predicted_price = predictions["actual_price"].to_numpy(), predictions["predicted_price"].to_numpy()
    precision, recall, f1, support = precision_recall_fscore_support(
        predictions["actual_direction"], predictions["predicted_direction"], labels=labels, zero_division=0,
    )
    nonflat = predictions[predictions["actual_direction"].ne("FLAT")]
    return {
        "observations": int(len(predictions)),
        "return_mae": float(mean_absolute_error(actual_return, predicted_return)),
        "return_rmse": float(np.sqrt(mean_squared_error(actual_return, predicted_return))),
        "return_r2": float(r2_score(actual_return, predicted_return)) if len(predictions) > 1 else None,
        "return_mape": None, "return_mape_reason": "Omitted because returns include and approach zero.",
        "price_mae_lkr_per_kg": float(mean_absolute_error(actual_price, predicted_price)),
        "price_rmse_lkr_per_kg": float(np.sqrt(mean_squared_error(actual_price, predicted_price))),
        "price_mape_percent": float(np.mean(np.abs((actual_price - predicted_price) / actual_price)) * 100.0),
        "directional_accuracy": float((predictions["actual_direction"] == predictions["predicted_direction"]).mean()),
        "nonflat_directional_accuracy": None if nonflat.empty else float((nonflat["actual_direction"] == nonflat["predicted_direction"]).mean()),
        "direction_labels": labels,
        "direction_confusion_matrix": confusion_matrix(predictions["actual_direction"], predictions["predicted_direction"], labels=labels).tolist(),
        "direction_per_class": {
            label: {"precision": float(precision[i]), "recall": float(recall[i]), "f1": float(f1[i]), "support": int(support[i])}
            for i, label in enumerate(labels)
        },
    }


def summarize(predictions: pd.DataFrame) -> dict[str, Any]:
    by_grade = {grade: metric_block(rows) for grade, rows in predictions.groupby("grade")}
    return {
        "overall": metric_block(predictions), "by_grade": by_grade,
        "macro_grade_return_rmse": float(np.mean([m["return_rmse"] for m in by_grade.values()])),
        "macro_grade_return_mae": float(np.mean([m["return_mae"] for m in by_grade.values()])),
    }


def add_candidate_id(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["candidate_id"] = output[["experiment", "method", "target", "feature_group", "formulation"]].astype(str).agg("|".join, axis=1)
    return output


def experiment_summaries(predictions: pd.DataFrame) -> dict[str, Any]:
    return {str(key): summarize(rows) for key, rows in predictions.groupby("candidate_id")}


def choose(metrics: dict[str, Any], candidates: list[str]) -> str:
    return min(candidates, key=lambda key: (metrics[key]["macro_grade_return_rmse"], metrics[key]["macro_grade_return_mae"], key))


def calibrate_intervals(validation: pd.DataFrame, evaluation: pd.DataFrame, quantile: float) -> tuple[pd.DataFrame, dict[str, Any]]:
    calibrated = evaluation.copy()
    radii = {
        grade: float(np.quantile(np.abs(rows["actual_return"] - rows["predicted_return"]), quantile, method="higher"))
        for grade, rows in validation.groupby("grade")
    }
    calibrated["interval_return_radius"] = calibrated["grade"].map(radii)
    calibrated["interval_lower_price"] = calibrated["current_price"] * (1.0 + calibrated["predicted_return"] - calibrated["interval_return_radius"])
    calibrated["interval_upper_price"] = calibrated["current_price"] * (1.0 + calibrated["predicted_return"] + calibrated["interval_return_radius"])
    calibrated["interval_covered"] = calibrated["actual_price"].between(calibrated["interval_lower_price"], calibrated["interval_upper_price"])
    stats = {
        "calibration_quantile": quantile, "return_radius_by_grade": radii,
        "overall_coverage": float(calibrated["interval_covered"].mean()),
        "mean_width_lkr_per_kg": float((calibrated["interval_upper_price"] - calibrated["interval_lower_price"]).mean()),
        "by_grade": {
            grade: {"observations": int(len(rows)), "coverage": float(rows["interval_covered"].mean()), "mean_width_lkr_per_kg": float((rows["interval_upper_price"] - rows["interval_lower_price"]).mean())}
            for grade, rows in calibrated.groupby("grade")
        },
    }
    return calibrated, stats


def make_plots(frame: pd.DataFrame, final_test: pd.DataFrame, external: pd.DataFrame, validation_metrics: dict[str, Any], selected_id: str, output: Path) -> None:
    def segmented(ax, rows: pd.DataFrame, y: str, label: str, color: str) -> None:
        rows = rows.sort_values("feature_date")
        ax.scatter(rows["feature_date"], rows[y], s=7, color=color, alpha=0.75)
        segments = rows["feature_date"].diff().dt.days.gt(14).cumsum()
        for i, (_, part) in enumerate(rows.groupby(segments)):
            ax.plot(part["feature_date"], part[y], color=color, linewidth=1.1, label=label if i == 0 else None)

    colors = {"Grade 1": "#1f77b4", "Grade 2": "#ff7f0e"}
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for grade, rows in frame.groupby("grade"):
        segmented(ax, rows, "current_price", grade, colors[grade])
    ax.set(title="DEA/EAC National Average Pepper Prices", xlabel="Observation date", ylabel="LKR per kg"); ax.legend(); ax.grid(alpha=.25); fig.tight_layout(); fig.savefig(output / "01_historical_prices.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    for grade, rows in frame.groupby("grade"):
        segmented(ax, rows.assign(return_percent=rows["return_lag_1"] * 100), "return_percent", grade, colors[grade])
    ax.axhline(0, color="black", linewidth=.8); ax.set(title="Historical One-Observation Returns", xlabel="Observation date", ylabel="Return (%)"); ax.legend(); ax.grid(alpha=.25); fig.tight_layout(); fig.savefig(output / "02_historical_returns.png", dpi=160); plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=False)
    for ax, (grade, rows) in zip(axes, final_test.groupby("grade")):
        rows = rows.sort_values("target_date"); ax.plot(rows["target_date"], rows["actual_price"], label="Actual", linewidth=1.4); ax.plot(rows["target_date"], rows["predicted_price"], label="Forecast", linewidth=1.1)
        ax.set(title=f"{grade}: Selected Walk-Forward Final Test", ylabel="LKR per kg"); ax.legend(); ax.grid(alpha=.25)
    axes[-1].set_xlabel("Target observation date"); fig.tight_layout(); fig.savefig(output / "03_selected_actual_vs_forecast_price.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 6)); ax.scatter(final_test["actual_return"] * 100, final_test["predicted_return"] * 100, alpha=.7, c=final_test["grade"].map(colors)); limits = [min(ax.get_xlim()[0], ax.get_ylim()[0]), max(ax.get_xlim()[1], ax.get_ylim()[1])]; ax.plot(limits, limits, "--", color="black"); ax.set(xlabel="Actual return (%)", ylabel="Predicted return (%)", title="Selected Model: Predicted vs Actual Returns"); ax.grid(alpha=.25); fig.tight_layout(); fig.savefig(output / "04_predicted_vs_actual_returns.png", dpi=160); plt.close(fig)

    ranked = sorted(validation_metrics.items(), key=lambda item: item[1]["macro_grade_return_rmse"])
    labels = [item[0].split("|")[1] + "\n" + item[0].split("|")[2] + "\n" + item[0].split("|")[4] for item in ranked]
    values = [item[1]["macro_grade_return_rmse"] for item in ranked]
    fig, ax = plt.subplots(figsize=(max(10, len(labels) * .7), 5)); ax.bar(range(len(labels)), values, color=["#2ca02c" if key == selected_id else "#7f7f7f" for key, _ in ranked]); ax.set_xticks(range(len(labels)), labels, rotation=55, ha="right"); ax.set(ylabel="Macro grade return RMSE", title="Validation Candidate Comparison"); ax.grid(axis="y", alpha=.25); fig.tight_layout(); fig.savefig(output / "05_validation_model_comparison.png", dpi=160); plt.close(fig)

    matrix = confusion_matrix(final_test["actual_direction"], final_test["predicted_direction"], labels=["DOWN", "FLAT", "UP"])
    fig, ax = plt.subplots(figsize=(5.5, 4.8)); image = ax.imshow(matrix, cmap="Blues")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center")
    ax.set_xticks(range(3), ["DOWN", "FLAT", "UP"]); ax.set_yticks(range(3), ["DOWN", "FLAT", "UP"]); ax.set(xlabel="Predicted", ylabel="Actual", title="Selected Model Direction Confusion Matrix"); fig.colorbar(image, ax=ax); fig.tight_layout(); fig.savefig(output / "06_direction_confusion_matrix.png", dpi=160); plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True)
    for ax, (grade, rows) in zip(axes, external.groupby("grade")):
        rows = rows.sort_values("target_date"); ax.plot(rows["target_date"], rows["actual_price"], marker="o", label="Actual"); ax.plot(rows["target_date"], rows["predicted_price"], marker="o", label="Forecast"); ax.fill_between(rows["target_date"], rows["interval_lower_price"], rows["interval_upper_price"], alpha=.18, label="Validation-calibrated interval")
        ax.set(title=grade, ylabel="LKR per kg"); ax.grid(alpha=.25); ax.legend()
    axes[-1].set_xlabel("External target date"); fig.suptitle("External Later-Observation Reality Check"); fig.tight_layout(); fig.savefig(output / "07_external_reality_check.png", dpi=160); plt.close(fig)


def main() -> int:
    started = time.perf_counter()
    config = load_config()
    output = ROOT / config["experiment"]["output_dir"]
    output.mkdir(parents=True, exist_ok=True)
    frame = build_modeling_data(config)
    modeling_path = PHASE5 / "data" / "phase5_modeling_dataset.csv"
    frame.to_csv(modeling_path, index=False, date_format="%Y-%m-%d")

    validation_parts: list[pd.DataFrame] = []
    stage1_ids: list[str] = []
    for feature_group in config["selection"]["stage_1_feature_groups"]:
        predictions = add_candidate_id(walk_forward_ml(frame, "VALIDATION", "ridge", "simple_return", feature_group, "separate", config, "feature_ablation"))
        validation_parts.append(predictions); stage1_ids.append(predictions["candidate_id"].iloc[0])
    stage1_metrics = experiment_summaries(pd.concat(validation_parts, ignore_index=True))
    selected_feature_id = choose(stage1_metrics, stage1_ids)
    selected_feature_group = selected_feature_id.split("|")[3]

    relationship_common = list(config["feature_groups"]["D_relationship"])
    for feature_group in [selected_feature_group, "D_relationship"]:
        predictions = walk_forward_ml(frame, "VALIDATION", "ridge", "simple_return", feature_group, "separate", config, "relationship_ablation", cohort_features=relationship_common)
        validation_parts.append(add_candidate_id(predictions))

    stage2_ids: list[str] = []
    for target in config["targets"]:
        for formulation in ["separate", "shared"]:
            predictions = add_candidate_id(walk_forward_ml(frame, "VALIDATION", "ridge", target, selected_feature_group, formulation, config, "target_formulation"))
            validation_parts.append(predictions); stage2_ids.append(predictions["candidate_id"].iloc[0])
    stage2_metrics = experiment_summaries(pd.concat(validation_parts, ignore_index=True))
    selected_target_id = choose(stage2_metrics, stage2_ids)
    selected_target = selected_target_id.split("|")[2]

    stage3_ids: list[str] = []
    for model_name in config["ml_models"]:
        for formulation in ["separate", "shared"]:
            predictions = add_candidate_id(walk_forward_ml(frame, "VALIDATION", model_name, selected_target, selected_feature_group, formulation, config, "model_bakeoff"))
            validation_parts.append(predictions); stage3_ids.append(predictions["candidate_id"].iloc[0])
    for name in config["baselines"]:
        validation_parts.append(add_candidate_id(walk_forward_baseline(frame, "VALIDATION", name, config)))
    for alpha in config["statistical_models"]["simple_exponential_smoothing"]["alphas"]:
        validation_parts.append(add_candidate_id(walk_forward_statistical(frame, "VALIDATION", "simple_exponential_smoothing", alpha, config)))
    for order in config["statistical_models"]["autoregressive"]["orders"]:
        validation_parts.append(add_candidate_id(walk_forward_statistical(frame, "VALIDATION", "autoregressive", order, config)))

    validation_predictions = pd.concat(validation_parts, ignore_index=True)
    validation_metrics = experiment_summaries(validation_predictions)
    selected_ml_id = choose(validation_metrics, stage3_ids)
    selected_parts = selected_ml_id.split("|")
    selected_model, selected_formulation = selected_parts[1], selected_parts[4]
    comparison_ids = [key for key in validation_metrics if key.startswith("baseline|") or key.startswith("statistical|")] + [selected_ml_id]
    strongest_validation_id = choose(validation_metrics, comparison_ids)

    final_parts: list[pd.DataFrame] = []
    external_parts: list[pd.DataFrame] = []
    for partition, destination in [("TEST", final_parts), ("EXTERNAL_NEWEST", external_parts)]:
        destination.append(add_candidate_id(walk_forward_ml(frame, partition, selected_model, selected_target, selected_feature_group, selected_formulation, config, "selected_ml")))
        for name in config["baselines"]:
            destination.append(add_candidate_id(walk_forward_baseline(frame, partition, name, config)))
        for alpha in config["statistical_models"]["simple_exponential_smoothing"]["alphas"]:
            destination.append(add_candidate_id(walk_forward_statistical(frame, partition, "simple_exponential_smoothing", alpha, config)))
        for order in config["statistical_models"]["autoregressive"]["orders"]:
            destination.append(add_candidate_id(walk_forward_statistical(frame, partition, "autoregressive", order, config)))
    final_predictions, external_predictions = pd.concat(final_parts, ignore_index=True), pd.concat(external_parts, ignore_index=True)
    final_metrics, external_metrics = experiment_summaries(final_predictions), experiment_summaries(external_predictions)

    selected_validation = validation_predictions[validation_predictions["candidate_id"].eq(selected_ml_id)].copy()
    selected_final_id = final_predictions[final_predictions["experiment"].eq("selected_ml")]["candidate_id"].iloc[0]
    selected_external_id = external_predictions[external_predictions["experiment"].eq("selected_ml")]["candidate_id"].iloc[0]
    selected_final = final_predictions[final_predictions["candidate_id"].eq(selected_final_id)].copy()
    selected_external = external_predictions[external_predictions["candidate_id"].eq(selected_external_id)].copy()
    quantile = float(config["prediction_intervals"]["nominal_coverage"])
    selected_final, final_interval = calibrate_intervals(selected_validation, selected_final, quantile)
    selected_external, external_interval = calibrate_intervals(selected_validation, selected_external, quantile)
    final_predictions = pd.concat([final_predictions[~final_predictions["candidate_id"].eq(selected_final_id)], selected_final], ignore_index=True)
    external_predictions = pd.concat([external_predictions[~external_predictions["candidate_id"].eq(selected_external_id)], selected_external], ignore_index=True)
    pd.concat([validation_predictions, final_predictions, external_predictions], ignore_index=True).to_csv(output / "walk_forward_predictions.csv", index=False, date_format="%Y-%m-%d")
    selected_external.to_csv(output / "external_reality_check_selected.csv", index=False, date_format="%Y-%m-%d")
    error_analysis = pd.concat(
        [selected_final.assign(evaluation_scope="FINAL_TEST"), selected_external.assign(evaluation_scope="EXTERNAL_NEWEST")],
        ignore_index=True,
    )
    error_analysis["absolute_price_error"] = (error_analysis["predicted_price"] - error_analysis["actual_price"]).abs()
    error_analysis["absolute_return_error"] = (error_analysis["predicted_return"] - error_analysis["actual_return"]).abs()
    error_analysis["direction_correct"] = error_analysis["predicted_direction"].eq(error_analysis["actual_direction"])
    error_analysis.sort_values(["absolute_price_error", "target_date"], ascending=[False, True]).head(20).to_csv(
        output / "selected_error_analysis.csv", index=False, date_format="%Y-%m-%d",
    )

    persistence_validation_id = next(key for key in validation_metrics if key.startswith("baseline|persistence_zero_return|"))
    persistence_final_id = next(key for key in final_metrics if key.startswith("baseline|persistence_zero_return|"))
    persistence_external_id = next(key for key in external_metrics if key.startswith("baseline|persistence_zero_return|"))
    selected_test_metrics, persistence_test_metrics = final_metrics[selected_final_id], final_metrics[persistence_final_id]
    selected_external_metrics, persistence_external_metrics = external_metrics[selected_external_id], external_metrics[persistence_external_id]
    val_beats = validation_metrics[selected_ml_id]["macro_grade_return_rmse"] < validation_metrics[persistence_validation_id]["macro_grade_return_rmse"] and validation_metrics[selected_ml_id]["macro_grade_return_mae"] < validation_metrics[persistence_validation_id]["macro_grade_return_mae"]
    test_beats = selected_test_metrics["overall"]["return_rmse"] < persistence_test_metrics["overall"]["return_rmse"] and selected_test_metrics["overall"]["return_mae"] < persistence_test_metrics["overall"]["return_mae"]
    external_beats = selected_external_metrics["overall"]["return_rmse"] < persistence_external_metrics["overall"]["return_rmse"] and selected_external_metrics["overall"]["return_mae"] < persistence_external_metrics["overall"]["return_mae"]
    verdict = "YES" if val_beats and test_beats and external_beats else "NO" if not any([val_beats, test_beats, external_beats]) else "MIXED"

    gap_analysis: dict[str, Any] = {}
    for label, rows in [("validation", selected_validation), ("final_test", selected_final), ("external", selected_external)]:
        grade2 = rows[rows["grade"].eq("Grade 2")]
        long_gap, ordinary = grade2[grade2["days_since_previous_observation"].gt(14)], grade2[grade2["days_since_previous_observation"].le(14)]
        gap_analysis[label] = {"grade2_gap_over_14_days": summarize(long_gap) if len(long_gap) else None, "grade2_gap_at_most_14_days": summarize(ordinary) if len(ordinary) else None}

    results = {
        "experiment_id": config["experiment"]["id"], "created_on": date.today().isoformat(),
        "dataset": {
            "version": config["experiment"]["dataset_version"], "canonical_path": config["experiment"]["dataset_path"],
            "canonical_sha256": sha256(ROOT / config["experiment"]["dataset_path"]), "modeling_dataset_sha256": sha256(modeling_path),
            "coverage": {"start": str(frame["feature_date"].min().date()), "end": str(frame["feature_date"].max().date())},
            "observations_by_grade": {grade: int(len(rows)) for grade, rows in frame.groupby("grade")},
            "partition_rows_by_grade": {partition: {grade: int(len(rows)) for grade, rows in part.groupby("grade")} for partition, part in frame.groupby("partition")},
        },
        "selection_protocol": {
            "feature_group_selected_on_validation": selected_feature_group, "target_selected_on_validation": selected_target,
            "selected_ml_candidate_id": selected_ml_id, "strongest_validation_method_id_including_baselines": strongest_validation_id,
            "minimum_training_observations": config["experiment"]["minimum_training_observations"],
            "hierarchy": "macro grade return RMSE, then macro grade return MAE, deterministic ID tie-break",
            "test_used_for_selection": False, "external_used_for_selection": False,
        },
        "feature_ablation": {key: validation_metrics[key] for key in stage1_ids},
        "relationship_ablation": {key: value for key, value in validation_metrics.items() if key.startswith("relationship_ablation|")},
        "target_formulation_comparison": {key: validation_metrics[key] for key in stage2_ids},
        "model_bakeoff": {key: validation_metrics[key] for key in stage3_ids},
        "validation_all_candidates": validation_metrics, "final_test": final_metrics, "external_reality_check": external_metrics,
        "selected_final_test": selected_test_metrics, "selected_external": selected_external_metrics,
        "persistence_final_test": persistence_test_metrics, "persistence_external": persistence_external_metrics,
        "prediction_intervals": {"method": config["prediction_intervals"]["method"], "final_test": final_interval, "external": external_interval},
        "grade2_gap_analysis": gap_analysis,
        "persistence_comparison": {"validation_both_mae_rmse_better": val_beats, "final_test_both_mae_rmse_better": test_beats, "external_both_mae_rmse_better": external_beats, "verdict": verdict},
        "seasonal_naive": config["statistical_models"]["seasonal_naive"], "fixed_calendar_horizon": config["horizon"]["fixed_calendar_horizon"],
        "arima_note": "ARIMA(1,0,0) and ARIMA(2,0,0) were fitted as conditional OLS autoregressions. MA/ARMA variants were not added because statsmodels was unavailable and adding dependencies was outside the small-dependency design.",
        "runtime_seconds": float(time.perf_counter() - started),
        "environment": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "scikit_learn": sklearn.__version__, "pyyaml": yaml.__version__, "platform": platform.platform()},
    }
    (output / "phase5_forecasting_metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (PHASE5 / "models" / "selected_model_spec.json").write_text(json.dumps({
        "candidate_id": selected_ml_id, "model": selected_model, "target": selected_target,
        "feature_group": selected_feature_group, "formulation": selected_formulation,
        "configuration": config["ml_models"][selected_model],
        "serialization": "No single fitted checkpoint: the selected research method refits on each expanding window.",
    }, indent=2), encoding="utf-8")
    make_plots(frame, selected_final, selected_external, validation_metrics, selected_ml_id, output)
    print(json.dumps({
        "selected_feature_group": selected_feature_group, "selected_target": selected_target,
        "selected_ml_candidate": selected_ml_id, "strongest_validation_method": strongest_validation_id,
        "persistence_verdict": verdict, "selected_final_test": selected_test_metrics["overall"],
        "persistence_final_test": persistence_test_metrics["overall"], "selected_external": selected_external_metrics["overall"],
        "persistence_external": persistence_external_metrics["overall"], "runtime_seconds": results["runtime_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
