"""Focused integrity validator for the completed Phase 3 Follow-up experiment."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
OUTPUT = ROOT / "ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup"
RESULT = OUTPUT / "integrity_validation.json"
EXPECTED = {
    "ml/grading_forecast/berry_grading/models/v3_yolo/best.pt": "c35cc40515adcb6130a4bc93e8ad3de161dcf46b263a9d7df8286a5b4239a9c4",
    "docs/research/V3_PHASE3_REJECTION_RESULTS.md": "95ee80c44902385abbaf773f2344224b10fd5e7ebf27ea270ebc521c287a726d",
    "data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv": "7ebf54b8ad0928015b06ee7d27fc2c93cb5df2663509e81bab740a7c21cef9fb",
    "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv": "f97702eaa7d62861abd8e8674e79e407f7f9eaf3d1f709a1f454bbe1aaa93044",
    "data/processed/grading_forecast/berry_v3/v3_group_split_manifest.csv": "fecebbaf4a0346ee2a6b286828c4c3ca131687c693ad89d4b7ff2a3359ace64a",
    "ml/grading_forecast/berry_grading/evaluation/v3_phase3/phase3_metrics.json": "f96e54f7ce9747a1d673dbe3a95818f84f0816051343dc0479d2f0d9ae323787",
    "ml/grading_forecast/berry_grading/evaluation/v3_phase3/decision_config_frozen.json": "1a1c987bb9011209440e761f9acd29ac7afd4e64ce0c22704ac4e12655203f47",
    "ml/grading_forecast/berry_grading/evaluation/v3_yolo/test/metrics.json": "e9f5c227e9667e8b3575c14ced0ab23c37440c1abeb4483cfa7cb95c444ed233",
    "ml/grading_forecast/berry_grading/models/v3_yolo/experiment_metadata.json": "d70a62f137e3537bf5bb4d49293236e2e3799b46397f456273821a8cc73cda9b",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def check(name: str, passed: bool, detail: str) -> dict:
    return {"check": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def main() -> int:
    checks = []
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        actual = sha256(path) if path.is_file() else "MISSING"
        checks.append(check(f"frozen:{relative}", actual == expected, f"expected={expected}; actual={actual}"))

    v3 = rows(ROOT / "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv")
    image_matches, label_matches = 0, 0
    partitions: dict[str, set[str]] = defaultdict(set)
    for row in v3:
        image = ROOT / row["v3_image_path"]
        if image.is_file() and sha256(image) == row["sha256"]:
            image_matches += 1
        label = ROOT / row["v3_label_path"]
        try:
            values = [float(v) for v in label.read_text(encoding="utf-8").split()]
            expected = [float(row["v3_class_id"]), float(row["box_x_center"]), float(row["box_y_center"]), float(row["box_width"]), float(row["box_height"])]
            if len(values) == 5 and all(abs(a - b) <= 1e-9 for a, b in zip(values, expected)):
                label_matches += 1
        except (OSError, ValueError):
            pass
        partitions[row["physical_sample_id"]].add(row["research_partition"])
    counts = Counter(r["research_partition"] for r in v3)
    checks.append(check("canonical_v3_images_unchanged", image_matches == 775, f"matches={image_matches}/775"))
    checks.append(check("canonical_v3_annotations_unchanged", label_matches == 775, f"matches={label_matches}/775"))
    checks.append(check("phase1_split_counts_unchanged", counts == Counter({"TRAIN": 539, "VALIDATION": 116, "TEST": 120}), str(dict(counts))))
    leaks = sum(len(value) != 1 for value in partitions.values())
    checks.append(check("no_physical_sample_leakage", leaks == 0 and len(partitions) == 194, f"groups={len(partitions)}; leaks={leaks}"))

    followup = rows(ROOT / "data/processed/grading_forecast/berry_v3/phase3_followup_negative_manifest.csv")
    hashes, group_splits = [], defaultdict(set)
    consistent = True
    for row in followup:
        path = ROOT / row["local_path"]
        actual = sha256(path) if path.is_file() else "MISSING"
        consistent &= actual == row["sha256"]
        hashes.append(row["sha256"])
        group_splits[row["source_group"]].add(row["split"])
    split_counts = Counter(r["split"] for r in followup)
    checks.append(check("negative_manifest_image_consistency", consistent, f"rows={len(followup)}"))
    checks.append(check("no_duplicate_sha256_across_negative_partitions", len(hashes) == len(set(hashes)), f"unique={len(set(hashes))}/{len(hashes)}"))
    source_leaks = sum(len(value) != 1 for value in group_splits.values())
    checks.append(check("source_aware_partitioning", source_leaks == 0, f"groups={len(group_splits)}; leaks={source_leaks}"))
    checks.append(check("all_negative_partitions_present", all(split_counts[name] > 0 for name in ("NEGATIVE_TRAIN", "NEGATIVE_VALIDATION", "NEGATIVE_FINAL_HOLDOUT")), str(dict(split_counts))))

    original_hashes = {r["sha256"] for r in rows(ROOT / "data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv")}
    final_hashes = {r["sha256"] for r in followup if r["split"] == "NEGATIVE_FINAL_HOLDOUT"}
    train_hashes = {r["sha256"] for r in followup if r["split"] == "NEGATIVE_TRAIN"}
    checks.append(check("original_phase3_holdout_not_in_training", not (original_hashes & train_hashes), f"overlap={len(original_hashes & train_hashes)}"))
    checks.append(check("new_final_holdout_isolated", not (final_hashes & train_hashes), f"overlap={len(final_hashes & train_hashes)}"))

    train_list = (ROOT / "data/processed/grading_forecast/berry_v3/phase3_followup_yolo/train.txt").read_text(encoding="utf-8")
    final_paths_in_train = sum(r["negative_id"] in train_list for r in followup if r["split"] == "NEGATIVE_FINAL_HOLDOUT")
    test_names_in_train = sum(Path(r["v3_image_path"]).name in train_list for r in v3 if r["research_partition"] == "TEST")
    checks.append(check("holdout_paths_absent_from_training_list", final_paths_in_train == 0 and test_names_in_train == 0, f"negative_final={final_paths_in_train}; positive_test={test_names_in_train}"))

    freeze_path, metrics_path = OUTPUT / "decision_config_frozen.json", OUTPUT / "phase3_followup_metrics.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8")) if freeze_path.exists() else {}
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    scan = rows(OUTPUT / "validation_threshold_scan.csv") if (OUTPUT / "validation_threshold_scan.csv").exists() else []
    selected = freeze.get("selected_threshold")
    checks.append(check("experiment_configuration_recorded", (ROOT / "ml/grading_forecast/berry_grading/quality/phase3_followup/experiment.yaml").is_file() and (ROOT / "ml/grading_forecast/berry_grading/models/v3_phase3_followup/experiment_metadata.json").is_file(), "config and training metadata"))
    checks.append(check("selected_threshold_from_validation", any(abs(float(r["threshold"]) - float(selected)) < 1e-12 for r in scan) if selected is not None else False, f"selected={selected}; scan_rows={len(scan)}"))
    checks.append(check("holdouts_accessed_only_after_freeze", freeze.get("status") == "FROZEN_AFTER_VALIDATION_BEFORE_ANY_FINAL_HOLDOUT_ACCESS" and metrics.get("integrity", {}).get("model_and_threshold_frozen_before_holdout") is True, "freeze status and final provenance"))
    checks.append(check("final_metrics_complete", metrics.get("status") == "COMPLETE" and metrics.get("decision", "").startswith("COMPLETE"), metrics.get("decision", "missing")))

    passed = all(item["status"] == "PASS" for item in checks)
    payload = {"phase": "3_followup", "status": "PASS" if passed else "FAIL", "checks": checks,
               "summary": {"passed": sum(c["status"] == "PASS" for c in checks), "failed": sum(c["status"] == "FAIL" for c in checks)}}
    RESULT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

