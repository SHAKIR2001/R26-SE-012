"""Build manifest-driven Ultralytics image lists without copying V3 data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

import yaml


EXPECTED = {
    "TRAIN": {"images": 539, "groups": 135, "V3 Grade 1": 312, "V3 Grade 2": 227},
    "VALIDATION": {"images": 116, "groups": 29, "V3 Grade 1": 68, "V3 Grade 2": 48},
    "TEST": {"images": 120, "groups": 30, "V3 Grade 1": 68, "V3 Grade 2": 52},
}
LIST_NAMES = {"TRAIN": "train.txt", "VALIDATION": "validation.txt", "TEST": "test.txt"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv"))
    parser.add_argument("--group-manifest", type=Path, default=Path("data/processed/grading_forecast/berry_v3/v3_group_split_manifest.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/grading_forecast/berry_v3/yolo_phase2"))
    parser.add_argument("--skip-hash-check", action="store_true")
    args = parser.parse_args()

    repo = Path.cwd().resolve()
    with args.manifest.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with args.group_manifest.open(encoding="utf-8", newline="") as handle:
        group_rows = list(csv.DictReader(handle))
    if len(rows) != 775 or len(group_rows) != 194:
        raise RuntimeError(f"Unexpected manifest sizes: {len(rows)} images, {len(group_rows)} groups")

    group_partition = {row["physical_sample_id"]: row["partition"] for row in group_rows}
    if len(group_partition) != 194:
        raise RuntimeError("Duplicate physical_sample_id in group manifest")
    groups_by_partition: dict[str, set[str]] = {name: set() for name in EXPECTED}
    for group, partition in group_partition.items():
        if partition not in EXPECTED:
            raise RuntimeError(f"Unknown group partition: {partition}")
        groups_by_partition[partition].add(group)
    names = list(EXPECTED)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            overlap = groups_by_partition[left] & groups_by_partition[right]
            if overlap:
                raise RuntimeError(f"Group leakage between {left} and {right}: {sorted(overlap)}")

    output_rows: dict[str, list[tuple[Path, Path]]] = {name: [] for name in EXPECTED}
    image_paths: set[Path] = set()
    class_counts: dict[str, Counter[str]] = {name: Counter() for name in EXPECTED}
    errors: list[str] = []
    for row in rows:
        partition = row["research_partition"]
        if partition not in EXPECTED:
            errors.append(f"Unknown image partition for {row['v3_image_path']}: {partition}")
            continue
        if group_partition.get(row["physical_sample_id"]) != partition:
            errors.append(f"Image/group partition mismatch: {row['v3_image_path']}")
        image = (repo / Path(row["v3_image_path"])).resolve()
        label = (repo / Path(row["v3_label_path"])).resolve()
        if not image.is_file() or not label.is_file():
            errors.append(f"Missing image or label: {image} / {label}")
            continue
        if image in image_paths:
            errors.append(f"Duplicate image path: {image}")
        image_paths.add(image)
        if not args.skip_hash_check and sha256(image) != row["sha256"]:
            errors.append(f"SHA-256 mismatch: {image}")
        label_lines = [line.strip() for line in label.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(label_lines) != 1:
            errors.append(f"Expected exactly one annotation: {label}")
        else:
            parts = label_lines[0].split()
            if len(parts) != 5 or parts[0] not in {"0", "1"}:
                errors.append(f"Invalid YOLO annotation: {label}")
            if parts[0] != row["v3_class_id"]:
                errors.append(f"Manifest/annotation class mismatch: {label}")
        output_rows[partition].append((image, label))
        class_counts[partition][row["v3_grade"]] += 1

    for partition, expected in EXPECTED.items():
        if len(output_rows[partition]) != expected["images"]:
            errors.append(f"{partition} image count mismatch")
        if len(groups_by_partition[partition]) != expected["groups"]:
            errors.append(f"{partition} group count mismatch")
        for grade in ("V3 Grade 1", "V3 Grade 2"):
            if class_counts[partition][grade] != expected[grade]:
                errors.append(f"{partition} {grade} count mismatch")
    if len(image_paths) != 775:
        errors.append(f"Expected 775 unique image paths, found {len(image_paths)}")
    if errors:
        raise RuntimeError("Dataset validation failed:\n" + "\n".join(errors[:30]))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    materialized = args.output_dir / "materialized"
    for partition, filename in LIST_NAMES.items():
        split_name = {"TRAIN": "train", "VALIDATION": "validation", "TEST": "test"}[partition]
        images_dir = materialized / split_name / "images"
        labels_dir = materialized / split_name / "labels"
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)
        paths: list[str] = []
        seen_names: set[str] = set()
        for source_image, source_label in sorted(output_rows[partition], key=lambda pair: pair[0].as_posix()):
            if source_image.name in seen_names:
                raise RuntimeError(f"Duplicate filename in derived {partition} split: {source_image.name}")
            seen_names.add(source_image.name)
            derived_image = images_dir / source_image.name
            derived_label = labels_dir / source_label.name
            if not derived_image.exists() or sha256(derived_image) != sha256(source_image):
                shutil.copyfile(source_image, derived_image)
            if not derived_label.exists() or derived_label.read_bytes() != source_label.read_bytes():
                shutil.copyfile(source_label, derived_label)
            paths.append(derived_image.resolve().as_posix())
        (args.output_dir / filename).write_text("\n".join(paths) + "\n", encoding="utf-8")
    dataset_yaml = {
        "path": materialized.resolve().as_posix(),
        "train": "train/images",
        "val": "validation/images",
        "test": "test/images",
        "names": {0: "V3 Grade 1", 1: "V3 Grade 2"},
        "nc": 2,
    }
    (args.output_dir / "data.yaml").write_text(yaml.safe_dump(dataset_yaml, sort_keys=False), encoding="utf-8")
    integrity = {
        "canonical_dataset": "data/raw/Pepper Berry Grading V3.yolov8",
        "image_manifest": args.manifest.as_posix(),
        "group_manifest": args.group_manifest.as_posix(),
        "identity": "SHA-256 exact match",
        "images_copied": True,
        "annotations_copied": True,
        "copy_reason": "Ultralytics may repair JPEG end markers during scanning; materialization prevents writes to the canonical Roboflow export.",
        "materialized_root": materialized.as_posix(),
        "classes": {"0": "V3 Grade 1", "1": "V3 Grade 2"},
        "partitions": {partition: {"images": len(output_rows[partition]), "groups": len(groups_by_partition[partition]), "images_by_grade": dict(class_counts[partition])} for partition in EXPECTED},
        "checks": {"all_current_hashes_match": not args.skip_hash_check, "one_annotation_per_image": True, "class_ids_match_manifest": True, "pairwise_group_intersections_empty": True, "all_775_images_exactly_once": True},
    }
    (args.output_dir / "dataset_integrity.json").write_text(json.dumps(integrity, indent=2), encoding="utf-8")
    print(json.dumps(integrity, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
