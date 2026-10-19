"""Focused data, leakage, preservation, and artifact checks for Phase 5."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[5]
PHASE5 = ROOT / "ml/grading_forecast/price_forecasting/phase5"
OUTPUT = PHASE5 / "outputs"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def result(name: str, passed: bool, details: str = "") -> dict:
    return {"check": name, "passed": bool(passed), "details": details}


def git_changed_paths() -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT,
        text=True, capture_output=True, check=True,
    )
    return [line[3:].replace("\\", "/") for line in completed.stdout.splitlines() if len(line) >= 4]


def verify_v3_images_and_labels() -> tuple[bool, bool, int]:
    manifest = pd.read_csv(ROOT / "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv")
    image_ok, label_ok = True, True
    for row in manifest.itertuples(index=False):
        image = ROOT / row.v3_image_path
        label = ROOT / row.v3_label_path
        image_ok = image_ok and image.is_file() and sha256(image) == row.sha256
        if not label.is_file():
            label_ok = False
            continue
        lines = [line.strip().split() for line in label.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(lines) != 1 or len(lines[0]) != 5:
            label_ok = False
            continue
        values = [float(value) for value in lines[0]]
        expected = [float(row.v3_class_id), row.box_x_center, row.box_y_center, row.box_width, row.box_height]
        label_ok = label_ok and bool(np.allclose(values, expected, atol=1e-6))
    return image_ok, label_ok, len(manifest)


def main() -> int:
    config = yaml.safe_load((PHASE5 / "phase5_config.yaml").read_text(encoding="utf-8"))
    metrics = json.loads((OUTPUT / "phase5_forecasting_metrics.json").read_text(encoding="utf-8"))
    canonical = pd.read_csv(ROOT / config["experiment"]["dataset_path"])
    modeling = pd.read_csv(PHASE5 / "data/phase5_modeling_dataset.csv", parse_dates=["feature_date", "target_date"])
    predictions = pd.read_csv(OUTPUT / "walk_forward_predictions.csv", parse_dates=["feature_date", "target_date"])

    ordered = modeling.sort_values(["grade", "feature_date"]).copy()
    grouped = ordered.groupby("grade")
    completed_return = grouped["current_price"].pct_change(fill_method=None)
    feature_formula_ok = np.allclose(ordered["return_lag_1"].fillna(-999999), completed_return.fillna(-999999), atol=1e-10)
    for lag in range(2, 5):
        expected = completed_return.groupby(ordered["grade"]).shift(lag - 1)
        feature_formula_ok = feature_formula_ok and np.allclose(ordered[f"return_lag_{lag}"].fillna(-999999), expected.fillna(-999999), atol=1e-10)
    expected_next = grouped["current_price"].shift(-1)
    target_ok = np.allclose(ordered["actual_price"].fillna(-999999), expected_next.fillna(-999999), atol=1e-10)
    target_ok = target_ok and np.allclose(
        ordered["target_simple_return"].fillna(-999999), (expected_next / ordered["current_price"] - 1).fillna(-999999), atol=1e-10,
    )
    target_dates_ok = modeling.loc[modeling["target_date"].notna(), "target_date"].gt(modeling.loc[modeling["target_date"].notna(), "feature_date"]).all()

    changed = git_changed_paths()
    allowed_prefixes = (
        "ml/grading_forecast/price_forecasting/phase5/", "docs/research/PHASE5_PRICE_FORECASTING_RESULTS.md",
        "docs/research/EXPERIMENT_LOG.md",
    )
    out_of_scope_changes = [path for path in changed if not path.startswith(allowed_prefixes)]
    v3_images_ok, v3_labels_ok, v3_count = verify_v3_images_and_labels()

    selected = metrics["selection_protocol"]["selected_ml_candidate_id"]
    selected_validation = predictions[predictions["candidate_id"].eq(selected)]
    selected_test = predictions[(predictions["experiment"].eq("selected_ml")) & predictions["partition"].eq("TEST")]
    selected_external = predictions[(predictions["experiment"].eq("selected_ml")) & predictions["partition"].eq("EXTERNAL_NEWEST")]
    selection_partitions_ok = set(selected_validation["partition"]) == {"VALIDATION"}
    minimum_rows_ok = predictions.loc[predictions["experiment"].isin(["feature_ablation", "target_formulation", "model_bakeoff", "selected_ml"]), "training_rows"].ge(config["experiment"]["minimum_training_observations"]).all()
    persistence_partitions = set(predictions.loc[predictions["method"].eq("persistence_zero_return"), "partition"])

    required_artifacts = [
        ROOT / "docs/research/PHASE5_PRICE_FORECASTING_RESULTS.md",
        PHASE5 / "phase5_config.yaml", PHASE5 / "data/phase5_modeling_dataset.csv",
        OUTPUT / "phase5_forecasting_metrics.json", OUTPUT / "walk_forward_predictions.csv",
        OUTPUT / "external_reality_check_selected.csv", OUTPUT / "selected_error_analysis.csv",
        PHASE5 / "models/selected_model_spec.json",
    ] + [OUTPUT / f"{index:02d}_{name}.png" for index, name in [
        (1, "historical_prices"), (2, "historical_returns"), (3, "selected_actual_vs_forecast_price"),
        (4, "predicted_vs_actual_returns"), (5, "validation_model_comparison"),
        (6, "direction_confusion_matrix"), (7, "external_reality_check"),
    ]]
    checks = [
        result("phase4_canonical_unchanged", sha256(ROOT / config["experiment"]["dataset_path"]) == config["protected_phase4"]["canonical_sha256"]),
        result("phase4_results_report_unchanged", sha256(ROOT / "docs/research/PHASE4_PRICE_FOUNDATION_RESULTS.md") == config["protected_phase4"]["results_report_sha256"]),
        result("phase4_audit_report_unchanged", sha256(ROOT / "docs/research/PHASE4_PRICE_DATA_AUDIT.md") == config["protected_phase4"]["audit_report_sha256"]),
        result("no_out_of_scope_worktree_changes", not out_of_scope_changes, ", ".join(out_of_scope_changes)),
        result("v3_images_match_phase1_sha256", v3_images_ok, f"images_checked={v3_count}"),
        result("v3_annotations_match_phase1_manifest", v3_labels_ok, f"labels_checked={v3_count}"),
        result("canonical_has_no_duplicate_national_grade_rows", not canonical[(canonical.market == "National") & (canonical.price_type == "average")].duplicated(["date", "grade"]).any()),
        result("canonical_grade2_not_fabricated", set(canonical["observation_status"]) == {"observed_source_value"}),
        result("target_dates_strictly_future", target_dates_ok),
        result("targets_match_next_observed_price", target_ok),
        result("return_lags_are_backward_looking", feature_formula_ok),
        result("no_random_split", not metrics["selection_protocol"].get("random_split", False)),
        result("no_full_dataset_scaling", config["ml_models"]["ridge"]["scaling"].endswith("each expanding training window")),
        result("validation_only_model_selection", selection_partitions_ok and not metrics["selection_protocol"]["test_used_for_selection"] and not metrics["selection_protocol"]["external_used_for_selection"]),
        result("minimum_training_window_respected", minimum_rows_ok),
        result("selected_test_and_external_present", len(selected_test) == 147 and len(selected_external) == 10),
        result("persistence_in_all_evaluation_partitions", persistence_partitions == {"VALIDATION", "TEST", "EXTERNAL_NEWEST"}),
        result("required_artifacts_present", all(path.is_file() for path in required_artifacts), ", ".join(str(path.relative_to(ROOT)) for path in required_artifacts if not path.is_file())),
        result("phase6_not_implemented", not any(path.startswith(("backend/", "mobile/")) for path in changed)),
    ]
    report = {
        "phase": 5, "validated_on": date.today().isoformat(), "passed": all(check["passed"] for check in checks),
        "checks": checks, "changed_paths": changed,
        "verification_boundary": "Content hashes protect Phase 4 reports/canonical data; Phase 1 hashes and annotation values protect all 775 V3 images/labels; Git worktree scope protects tracked V2, berry, backend, and mobile files.",
    }
    (OUTPUT / "phase5_integrity_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
