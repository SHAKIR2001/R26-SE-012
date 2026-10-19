"""Validate the Phase 0-5 freeze and optional Phase 6 field-data independence.

This script is read-only except for its Phase 6 integrity JSON output. It does
not train a model, tune a threshold, alter a historical artifact, or open an
unlabelled image with the model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
PHASE6 = ROOT / "ml/grading_forecast/berry_grading/evaluation/phase6"
DEFAULT_MANIFEST = PHASE6 / "phase6_field_manifest.csv"
TEMPLATE_MANIFEST = PHASE6 / "phase6_field_manifest_template.csv"
DEFAULT_OUTPUT = PHASE6 / "phase6_integrity.json"

FROZEN_FILES = {
    "docs/research/V3_DECISION_RECORD.md": "02acbeb682857ebf5564893a057572a348fc6a264b6b1b0e6b890da13dbb23f7",
    "docs/research/V3_PHASE1_AUDIT.md": "f6afc3e4aa218aa79a28d8acefb3e0739b4711916f53a707d7fa3f238f0f6f76",
    "docs/research/V3_PHASE2_YOLO_RESULTS.md": "53ca99022325094e2ef4d6babfe6d78d50a9557858963e2fceada8bafefc7a22",
    "docs/research/V3_PHASE3_REJECTION_RESULTS.md": "95ee80c44902385abbaf773f2344224b10fd5e7ebf27ea270ebc521c287a726d",
    "docs/research/V3_PHASE3_FOLLOWUP_REJECTION_RESULTS.md": "7e5cb116f05c9bc741655d318e47d72eaead10b1d08f8f71275188824696ab28",
    "docs/research/PHASE4_PRICE_FOUNDATION_RESULTS.md": "1ff3db4bb51736cbf708b6bc7940c839f51e7cc94efe2afcbb84da3e555b69e0",
    "docs/research/PHASE5_PRICE_FORECASTING_RESULTS.md": "6b9de251bffb8f3493c700ff949c398317c1fe18d5a98d434af7ceab5235eb70",
    "ml/grading_forecast/berry_grading/models/v3_yolo/best.pt": "c35cc40515adcb6130a4bc93e8ad3de161dcf46b263a9d7df8286a5b4239a9c4",
    "ml/grading_forecast/berry_grading/models/v3_phase3_followup/best.pt": "e825278e0cf8eaff64cd05a2941cf96794e573027823a0ccd308bbc3f1a418ca",
    "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv": "f97702eaa7d62861abd8e8674e79e407f7f9eaf3d1f709a1f454bbe1aaa93044",
    "data/processed/grading_forecast/berry_v3/v3_group_split_manifest.csv": "fecebbaf4a0346ee2a6b286828c4c3ca131687c693ad89d4b7ff2a3359ace64a",
    "data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv": "7ebf54b8ad0928015b06ee7d27fc2c93cb5df2663509e81bab740a7c21cef9fb",
    "data/processed/grading_forecast/berry_v3/phase3_followup_negative_manifest.csv": "a98ed3f16b7d78e8cd896690dbf5db377c5b983602c5d5291bac83883d8adb14",
    "data/processed/grading_forecast/price/eac_reconstructed_v1/eac_pepper_price_canonical.csv": "ea800ea576817f07ad54d50317dbd68254fc5dc824447380e58688b6b711c0f6",
    "ml/grading_forecast/price_forecasting/phase5/models/selected_model_spec.json": "e98277d6ced450d47ee67e987217a45a1b2a717b0f467c3ac70b1607677e14f9",
    "ml/grading_forecast/price_forecasting/phase5/outputs/phase5_forecasting_metrics.json": "aa25b60f75d3b5bdfbfcdf37f126d3d826e77818241a68f16d00ed6292ed5e2c",
    "ml/grading_forecast/price_forecasting/phase5/outputs/walk_forward_predictions.csv": "d06f8c195a475e30eb78b5aeede55658dcfaaa0f5d09fecfda6de0f435b19e93",
    "ml/grading_forecast/price_forecasting/phase5/outputs/external_reality_check_selected.csv": "0b3e5a4ede8f6839f831f008a4655114413c6369a1b9549dca240cc685288c4a",
}

ALLOWED_PHASE6_CHANGES = (
    "docs/research/PHASE6_",
    "docs/research/EXPERIMENT_LOG.md",
    "docs/research/PROGRESS_REPORT_FROM_14A39C9.md",
    "ml/grading_forecast/berry_grading/evaluation/phase6/",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def check(name: str, passed: bool | None, detail: str, required: bool = True) -> dict:
    status = "UNAVAILABLE" if passed is None else "PASS" if passed else "FAIL"
    return {"check": name, "status": status, "required": required, "detail": detail}


def git_state() -> dict:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    entries = [line for line in status.stdout.splitlines() if line]
    paths = [line[3:].replace("\\", "/") for line in entries if len(line) >= 4]
    return {
        "commit": commit,
        "porcelain_entries": entries,
        "changed_paths": paths,
        "stderr_warnings": status.stderr.strip().splitlines(),
    }


def safe_repo_path(relative: str) -> Path | None:
    candidate = (ROOT / relative).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


def validate_field_manifest(path: Path, prior_hashes: set[str]) -> tuple[list[dict], dict]:
    field_rows = rows(path)
    if not field_rows:
        return [], {
            "status": "BLOCKED_PENDING_FIELD_DATA",
            "manifest": str(path.relative_to(ROOT)).replace("\\", "/") if path.is_relative_to(ROOT) else str(path),
            "images": 0,
            "physical_samples": 0,
            "devices": 0,
            "independent": None,
            "hash_overlap_with_prior": None,
            "physical_sample_leakage": None,
        }

    required = {
        "image_id", "relative_path", "sha256", "physical_sample_id", "partition",
        "reference_type", "reference_grade", "label_source", "device_model",
        "lighting", "background", "framing", "provenance_note", "consent_or_authorization",
    }
    missing_columns = sorted(required - set(field_rows[0]))
    actual_hashes: list[str] = []
    missing_files, bad_hashes, unsafe_paths = [], [], []
    group_partitions: dict[str, set[str]] = defaultdict(set)
    for row in field_rows:
        candidate = safe_repo_path(row.get("relative_path", ""))
        if candidate is None:
            unsafe_paths.append(row.get("relative_path", ""))
            continue
        if not candidate.is_file():
            missing_files.append(row.get("image_id", ""))
            continue
        actual = sha256(candidate)
        actual_hashes.append(actual)
        if actual.lower() != row.get("sha256", "").lower():
            bad_hashes.append(row.get("image_id", ""))
        group_partitions[row.get("physical_sample_id", "")].add(row.get("partition", ""))
    overlaps = set(actual_hashes) & prior_hashes
    leaks = {key: sorted(value) for key, value in group_partitions.items() if len(value) != 1}
    valid_partitions = {row.get("partition") for row in field_rows} <= {"CALIBRATION", "FINAL_EVALUATION"}
    labels_independent = all(row.get("label_source", "").strip() for row in field_rows)
    metadata_complete = all(
        all(row.get(field, "").strip() for field in ("device_model", "lighting", "background", "framing", "provenance_note", "consent_or_authorization"))
        for row in field_rows
    )
    final_rows_sealed = all(row.get("sealed_at_utc", "").strip() for row in field_rows if row.get("partition") == "FINAL_EVALUATION")
    independent = not (missing_columns or missing_files or bad_hashes or unsafe_paths or overlaps or leaks) and valid_partitions and labels_independent and metadata_complete and final_rows_sealed
    return field_rows, {
        "status": "READY_FOR_FROZEN_EVALUATION" if independent else "INVALID_OR_INDEPENDENCE_NOT_PROVEN",
        "manifest": str(path.relative_to(ROOT)).replace("\\", "/") if path.is_relative_to(ROOT) else str(path),
        "images": len(field_rows),
        "physical_samples": len(group_partitions),
        "devices": len({(r.get("device_make", ""), r.get("device_model", "")) for r in field_rows}),
        "independent": independent,
        "missing_columns": missing_columns,
        "missing_files": missing_files,
        "hash_mismatches": bad_hashes,
        "unsafe_paths": unsafe_paths,
        "hash_overlap_with_prior": len(overlaps),
        "physical_sample_leakage": leaks,
        "valid_partitions": valid_partitions,
        "independent_label_source_recorded": labels_independent,
        "acquisition_metadata_complete": metadata_complete,
        "final_rows_sealed": final_rows_sealed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    output = args.output if args.output.is_absolute() else ROOT / args.output

    checks: list[dict] = []
    frozen_observed = {}
    for relative, expected in FROZEN_FILES.items():
        path = ROOT / relative
        actual = sha256(path) if path.is_file() else None
        frozen_observed[relative] = {"expected_sha256": expected, "actual_sha256": actual}
        checks.append(check(f"frozen_file:{relative}", actual == expected, f"expected={expected}; actual={actual}"))

    v3 = rows(ROOT / "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv")
    image_matches = 0
    annotation_matches = 0
    annotation_digest = hashlib.sha256()
    sample_partitions: dict[str, set[str]] = defaultdict(set)
    for row in v3:
        image = ROOT / row["v3_image_path"]
        label = ROOT / row["v3_label_path"]
        if image.is_file() and sha256(image) == row["sha256"].lower():
            image_matches += 1
        try:
            content = label.read_bytes()
            values = [float(value) for value in content.decode("utf-8").split()]
            expected = [float(row[key]) for key in ("v3_class_id", "box_x_center", "box_y_center", "box_width", "box_height")]
            if len(values) == 5 and all(abs(left - right) <= 1e-9 for left, right in zip(values, expected)):
                annotation_matches += 1
            annotation_digest.update(row["v3_label_path"].encode("utf-8"))
            annotation_digest.update(b"\0")
            annotation_digest.update(content)
        except (OSError, UnicodeDecodeError, ValueError):
            pass
        sample_partitions[row["physical_sample_id"]].add(row["research_partition"])
    split_counts = Counter(row["research_partition"] for row in v3)
    split_leaks = sum(len(value) != 1 for value in sample_partitions.values())
    checks.extend([
        check("v3_image_count_and_hashes", len(v3) == 775 and image_matches == 775, f"rows={len(v3)}; hash_matches={image_matches}"),
        check("v3_annotation_count_and_values", annotation_matches == 775, f"matches={annotation_matches}/775; aggregate_sha256={annotation_digest.hexdigest()}"),
        check("phase1_group_split", split_counts == Counter({"TRAIN": 539, "VALIDATION": 116, "TEST": 120}) and len(sample_partitions) == 194 and split_leaks == 0, f"counts={dict(split_counts)}; groups={len(sample_partitions)}; leaks={split_leaks}"),
        check("phase2_test_historically_identifiable", split_counts.get("TEST") == 120, "The Phase 2 TEST has 120 rows; it was intentionally reused only for frozen follow-up regression analysis."),
    ])

    original = rows(ROOT / "data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv")
    original_counts = Counter(row["phase3_partition"] for row in original)
    original_file_matches = sum((ROOT / row["local_path"]).is_file() and sha256(ROOT / row["local_path"]) == row["sha256"].lower() for row in original)
    followup = rows(ROOT / "data/processed/grading_forecast/berry_v3/phase3_followup_negative_manifest.csv")
    followup_counts = Counter(row["split"] for row in followup)
    followup_hashes = [row["sha256"].lower() for row in followup]
    followup_file_matches = sum((ROOT / row["local_path"]).is_file() and sha256(ROOT / row["local_path"]) == row["sha256"].lower() for row in followup)
    source_splits: dict[str, set[str]] = defaultdict(set)
    for row in followup:
        source_splits[row["source_group"]].add(row["split"])
    checks.extend([
        check("phase3_original_negative_set", len(original) == 80 and original_counts == Counter({"CALIBRATION": 40, "EVALUATION": 40}) and original_file_matches == 80, f"rows={len(original)}; partitions={dict(original_counts)}; hash_matches={original_file_matches}"),
        check("phase3_followup_negative_set", len(followup) == 250 and followup_counts == Counter({"NEGATIVE_TRAIN": 152, "NEGATIVE_VALIDATION": 49, "NEGATIVE_FINAL_HOLDOUT": 49}) and followup_file_matches == 250, f"rows={len(followup)}; partitions={dict(followup_counts)}; hash_matches={followup_file_matches}"),
        check("phase3_followup_negative_isolation", len(followup_hashes) == len(set(followup_hashes)) and all(len(value) == 1 for value in source_splits.values()), f"unique_hashes={len(set(followup_hashes))}; source_groups={len(source_splits)}"),
    ])

    prior_hashes = {row["sha256"].lower() for row in v3 + original + followup}
    field_rows, field = validate_field_manifest(manifest, prior_hashes)
    if field_rows:
        checks.append(check("phase6_field_independence", field["independent"], json.dumps(field, sort_keys=True)))
    else:
        checks.append(check("phase6_field_independence", None, "No populated Phase 6 field manifest is present.", required=False))

    canonical = rows(ROOT / "data/processed/grading_forecast/price/eac_reconstructed_v1/eac_pepper_price_canonical.csv")
    latest_date = max((row.get("date", "") for row in canonical), default=None)
    checks.append(check("phase4_canonical_price_data", len(canonical) == 16903 and latest_date == "2026-09-29", f"rows={len(canonical)}; latest_date={latest_date}"))
    external = rows(ROOT / "ml/grading_forecast/price_forecasting/phase5/outputs/external_reality_check_selected.csv")
    checks.append(check("phase5_external_period_identifiable", len(external) == 10, f"rows={len(external)}; frozen cutoff=2026-09-29"))

    state = git_state()
    unexpected = [path for path in state["changed_paths"] if not path.startswith(ALLOWED_PHASE6_CHANGES)]
    checks.append(check("no_accidental_out_of_scope_overwrite", not unexpected, f"unexpected_changed_paths={unexpected}"))

    baseline = ROOT / "ml/grading_forecast/berry_grading/models/v3_yolo/best.pt"
    treatment = ROOT / "ml/grading_forecast/berry_grading/models/v3_phase3_followup/best.pt"
    model_separation = {
        "phase2": {"path": str(baseline.relative_to(ROOT)).replace("\\", "/"), "bytes": baseline.stat().st_size, "modified_utc": datetime.fromtimestamp(baseline.stat().st_mtime, timezone.utc).isoformat(), "sha256": sha256(baseline)},
        "phase3_followup": {"path": str(treatment.relative_to(ROOT)).replace("\\", "/"), "bytes": treatment.stat().st_size, "modified_utc": datetime.fromtimestamp(treatment.stat().st_mtime, timezone.utc).isoformat(), "sha256": sha256(treatment)},
        "identical": sha256(baseline) == sha256(treatment),
    }
    checks.append(check("phase2_and_followup_models_separate", not model_separation["identical"] and baseline.resolve() != treatment.resolve(), json.dumps(model_separation, sort_keys=True)))

    required_failures = [item for item in checks if item["required"] and item["status"] == "FAIL"]
    freeze_status = "PASS" if not required_failures else "FAIL"
    payload = {
        "phase": 6,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "freeze_status": freeze_status,
        "phase6_status": "BLOCKED_PENDING_FIELD_DATA" if not field_rows and freeze_status == "PASS" else "READY_FOR_EVALUATION" if field.get("independent") and freeze_status == "PASS" else "BLOCKED_INTEGRITY_REVIEW",
        "git": state,
        "model_separation": model_separation,
        "frozen_files": frozen_observed,
        "v3": {"images": len(v3), "image_hash_matches": image_matches, "annotation_matches": annotation_matches, "annotation_aggregate_sha256": annotation_digest.hexdigest(), "physical_samples": len(sample_partitions), "split_counts": dict(split_counts)},
        "phase3_original_negatives": {"images": len(original), "split_counts": dict(original_counts), "file_hash_matches": original_file_matches, "historical_reuse": "The 40-image evaluation subset was intentionally reused for frozen-model comparison; original metrics remain preserved."},
        "phase3_followup_negatives": {"images": len(followup), "split_counts": dict(followup_counts), "source_groups": len(source_splits), "file_hash_matches": followup_file_matches},
        "field_dataset": field,
        "price": {"canonical_rows": len(canonical), "frozen_cutoff": latest_date, "phase5_external_rows": len(external), "new_temporal_evaluation": "NO NEW TEMPORAL PRICE EVALUATION AVAILABLE"},
        "checks": checks,
        "summary": {"passed": sum(item["status"] == "PASS" for item in checks), "failed": sum(item["status"] == "FAIL" for item in checks), "unavailable": sum(item["status"] == "UNAVAILABLE" for item in checks)},
        "historical_test_reuse_note": "The original Phase 2 test was frozen as historical baseline evidence, then intentionally re-evaluated under the frozen Phase 3 follow-up decision pipeline for regression analysis. Its original Phase 2 metrics remain preserved.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0 if freeze_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
