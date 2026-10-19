from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

sys.dont_write_bytecode = True


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
GRADE_DIR_TO_LABEL = {
    "grade_1": "Grade 1",
    "grade_2": "Grade 2",
    "grade_3": "Grade 3",
}
UNKNOWN_FIELDS = {
    "size_quality": "unknown",
    "color_quality": "unknown",
    "texture_quality": "unknown",
    "broken_level": "unknown",
    "light_berry_level": "unknown",
    "pinhead_level": "unknown",
    "foreign_matter_visible": "unknown",
    "mould_visible": "unknown",
    "insect_damage_visible": "unknown",
}
MANIFEST_COLUMNS = [
    "image_id",
    "image_path",
    "grade",
    "sample_id",
    "camera_model",
    "orientation",
    "width",
    "height",
    "aspect_ratio",
    "image_readable",
    *UNKNOWN_FIELDS.keys(),
]
SPLIT_MANIFEST_COLUMNS = [
    "image_id",
    "image_path",
    "split_image_path",
    "grade",
    "sample_id",
    "split",
    "camera_model",
    "orientation",
    "width",
    "height",
    "aspect_ratio",
]


@dataclass(frozen=True)
class ImageRecord:
    image_id: str
    image_path: Path
    grade_dir: str
    grade: str
    sample_id: str
    camera_model: str
    orientation: str
    width: int | None
    height: int | None
    aspect_ratio: float | None
    image_readable: bool
    content_hash: str | None
    error: str | None = None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def repo_relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def image_id(index: int) -> str:
    return f"IMGV2_{index:06d}"


def iter_candidate_images(raw_root: Path) -> list[Path]:
    paths: list[Path] = []
    for grade_dir in sorted(GRADE_DIR_TO_LABEL):
        grade_root = raw_root / grade_dir
        if not grade_root.exists():
            continue
        paths.extend(
            p
            for p in grade_root.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        )
    return sorted(paths, key=lambda p: p.as_posix().lower())


def sample_id_from_path(raw_root: Path, image_path: Path) -> tuple[str, str]:
    rel = image_path.relative_to(raw_root)
    if len(rel.parts) < 3:
        return rel.parts[0], "__root_level__"
    return rel.parts[0], rel.parts[1]


def inspect_image(path: Path) -> tuple[int | None, int | None, str, str, str | None]:
    try:
        with Image.open(path) as img:
            img.load()
            width, height = img.size
            exif = img.getexif()
            make = str(exif.get(271, "")).strip()
            model = str(exif.get(272, "")).strip()
            orientation = str(exif.get(274, "")).strip()
            camera_model = " ".join(x for x in [make, model] if x).strip()
            return width, height, camera_model or "unknown", orientation or "unknown", None
    except Exception as exc:  # noqa: BLE001
        return None, None, "unknown", "unknown", str(exc)


def content_hash(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        return h.hexdigest()
    except Exception:
        return None


def build_records(raw_root: Path) -> list[ImageRecord]:
    records: list[ImageRecord] = []
    for idx, path in enumerate(iter_candidate_images(raw_root), start=1):
        grade_dir, sample_id = sample_id_from_path(raw_root, path)
        width, height, camera_model, orientation, error = inspect_image(path)
        aspect_ratio = round(width / height, 6) if width and height else None
        records.append(
            ImageRecord(
                image_id=image_id(idx),
                image_path=path,
                grade_dir=grade_dir,
                grade=GRADE_DIR_TO_LABEL.get(grade_dir, "unknown"),
                sample_id=sample_id,
                camera_model=camera_model,
                orientation=orientation,
                width=width,
                height=height,
                aspect_ratio=aspect_ratio,
                image_readable=error is None,
                content_hash=content_hash(path) if error is None else None,
                error=error,
            )
        )
    return records


def manifest_row(root: Path, record: ImageRecord) -> dict[str, Any]:
    return {
        "image_id": record.image_id,
        "image_path": repo_relative(root, record.image_path),
        "grade": record.grade,
        "sample_id": record.sample_id,
        "camera_model": record.camera_model,
        "orientation": record.orientation,
        "width": record.width if record.width is not None else "",
        "height": record.height if record.height is not None else "",
        "aspect_ratio": record.aspect_ratio if record.aspect_ratio is not None else "",
        "image_readable": str(record.image_readable).lower(),
        **UNKNOWN_FIELDS,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def split_samples(records: list[ImageRecord], seed: int) -> dict[tuple[str, str], str]:
    rng = random.Random(seed)
    split_by_sample: dict[tuple[str, str], str] = {}
    for grade_dir in sorted(GRADE_DIR_TO_LABEL):
        sample_ids = sorted({r.sample_id for r in records if r.grade_dir == grade_dir and r.image_readable})
        rng.shuffle(sample_ids)
        total = len(sample_ids)
        train_n = int(total * 0.70)
        val_n = int(total * 0.15)
        if total and train_n == 0:
            train_n = 1
        if total >= 3 and val_n == 0:
            val_n = 1
        if train_n + val_n >= total and total >= 3:
            val_n = max(1, total - train_n - 1)
        for i, sample_id in enumerate(sample_ids):
            if i < train_n:
                split = "train"
            elif i < train_n + val_n:
                split = "val"
            else:
                split = "test"
            split_by_sample[(grade_dir, sample_id)] = split
    return split_by_sample


def copy_split_images(
    root: Path,
    raw_root: Path,
    split_root: Path,
    records: list[ImageRecord],
    split_by_sample: dict[tuple[str, str], str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        if not record.image_readable:
            continue
        split = split_by_sample[(record.grade_dir, record.sample_id)]
        rel_from_raw = record.image_path.relative_to(raw_root)
        dst = split_root / split / rel_from_raw
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(record.image_path, dst)
        rows.append(
            {
                "image_id": record.image_id,
                "image_path": repo_relative(root, record.image_path),
                "split_image_path": repo_relative(root, dst),
                "grade": record.grade,
                "sample_id": record.sample_id,
                "split": split,
                "camera_model": record.camera_model,
                "orientation": record.orientation,
                "width": record.width,
                "height": record.height,
                "aspect_ratio": record.aspect_ratio,
            }
        )
    return rows


def build_summary(
    root: Path,
    records: list[ImageRecord],
    split_rows: list[dict[str, Any]],
    seed: int,
) -> dict[str, Any]:
    readable = [r for r in records if r.image_readable]
    image_paths = [repo_relative(root, r.image_path) for r in readable]
    path_counts = Counter(image_paths)
    hash_counts = Counter(r.content_hash for r in readable if r.content_hash)

    sample_counts: dict[str, dict[str, int]] = defaultdict(dict)
    fewer: list[dict[str, Any]] = []
    more: list[dict[str, Any]] = []
    for grade_dir in sorted(GRADE_DIR_TO_LABEL):
        grade_records = [r for r in readable if r.grade_dir == grade_dir]
        by_sample = Counter(r.sample_id for r in grade_records)
        for sample_id, count in sorted(by_sample.items()):
            sample_counts[grade_dir][sample_id] = count
            item = {"grade": GRADE_DIR_TO_LABEL[grade_dir], "sample_id": sample_id, "image_count": count}
            if count < 4:
                fewer.append(item)
            elif count > 4:
                more.append(item)

    split_sample_map: dict[str, dict[str, set[str]]] = {
        "train": defaultdict(set),
        "val": defaultdict(set),
        "test": defaultdict(set),
    }
    split_image_counts: dict[str, Counter[str]] = {
        "train": Counter(),
        "val": Counter(),
        "test": Counter(),
    }
    sample_to_splits: dict[str, set[str]] = defaultdict(set)
    split_path_counts = Counter()
    for row in split_rows:
        split = str(row["split"])
        grade = str(row["grade"])
        sample_key = f"{grade}::{row['sample_id']}"
        split_sample_map[split][grade].add(str(row["sample_id"]))
        split_image_counts[split][grade] += 1
        sample_to_splits[sample_key].add(split)
        split_path_counts[str(row["image_path"])] += 1

    samples_crossing = {
        sample: sorted(splits)
        for sample, splits in sample_to_splits.items()
        if len(splits) > 1
    }

    split_summary: dict[str, Any] = {}
    for split in ["train", "val", "test"]:
        split_summary[split] = {
            "samples_per_grade": {
                grade: len(split_sample_map[split].get(grade, set()))
                for grade in sorted(GRADE_DIR_TO_LABEL.values())
            },
            "images_per_grade": dict(split_image_counts[split]),
            "total_samples": sum(len(v) for v in split_sample_map[split].values()),
            "total_images": sum(split_image_counts[split].values()),
        }

    validation = {
        "every_readable_image_in_split_once": all(c == 1 for c in split_path_counts.values())
        and len(split_path_counts) == len(readable),
        "no_sample_id_crosses_splits": len(samples_crossing) == 0,
        "all_grades_in_each_split": all(
            set(split_summary[split]["images_per_grade"]) == set(GRADE_DIR_TO_LABEL.values())
            for split in ["train", "val", "test"]
        ),
        "duplicate_manifest_paths": [p for p, c in path_counts.items() if c > 1],
        "duplicate_split_manifest_paths": [p for p, c in split_path_counts.items() if c > 1],
        "samples_crossing_splits": samples_crossing,
    }

    return {
        "dataset_version": "berry_v2",
        "created_at": utc_now_iso(),
        "seed": seed,
        "raw_total_candidates": len(records),
        "total_images": len(readable),
        "images_per_grade": dict(Counter(r.grade for r in readable)),
        "number_of_samples_per_grade": {
            GRADE_DIR_TO_LABEL[grade_dir]: len(sample_counts[grade_dir])
            for grade_dir in sorted(GRADE_DIR_TO_LABEL)
        },
        "total_sample_count": sum(len(v) for v in sample_counts.values()),
        "image_count_per_sample": sample_counts,
        "samples_with_fewer_than_4_images": fewer,
        "samples_with_more_than_4_images": more,
        "unreadable_images": [
            {"image_path": repo_relative(root, r.image_path), "error": r.error}
            for r in records
            if not r.image_readable
        ],
        "missing_files": [],
        "duplicate_image_paths": [p for p, c in path_counts.items() if c > 1],
        "duplicate_image_content_groups": [
            {"sha256": h, "count": c}
            for h, c in hash_counts.items()
            if c > 1
        ],
        "image_dimensions": {
            f"{r.width}x{r.height}": count
            for (r_width, r_height), count in Counter((r.width, r.height) for r in readable).items()
            for r in [type("Dims", (), {"width": r_width, "height": r_height})]
        },
        "aspect_ratios": {
            str(k): v for k, v in sorted(Counter(r.aspect_ratio for r in readable).items())
        },
        "exif_camera_models": dict(Counter(r.camera_model for r in readable)),
        "exif_orientation_distribution": dict(Counter(r.orientation for r in readable)),
        "split_root": "data/processed/grading_forecast/berry_split_v2",
        "split_manifest": "data/processed/grading_forecast/berry_split_v2_manifest.csv",
        "split_summary": split_summary,
        "validation": validation,
        "notes": [
            "Detailed visual-quality metadata is unavailable and kept as unknown in the V2 manifest.",
            "Readable unusual samples are retained and documented instead of silently discarded.",
            "Split is deterministic and performed at grade+sample_id level to prevent leakage.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare berry dataset V2 manifest, audit, and sample split.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    root = repo_root()
    raw_root = root / "data" / "raw" / "berry_images"
    manifest_csv = root / "data" / "annotations" / "grading_forecast" / "berry_grading_labels_v2.csv"
    split_root = root / "data" / "processed" / "grading_forecast" / "berry_split_v2"
    split_manifest_csv = root / "data" / "processed" / "grading_forecast" / "berry_split_v2_manifest.csv"
    summary_json = root / "data" / "processed" / "grading_forecast" / "berry_dataset_v2_summary.json"

    if not raw_root.exists():
        print(f"Missing raw image root: {raw_root}")
        return 2

    records = build_records(raw_root)
    if not records:
        print(f"No supported images found under: {raw_root}")
        return 3

    write_csv(manifest_csv, [manifest_row(root, r) for r in records], MANIFEST_COLUMNS)

    split_by_sample = split_samples(records, seed=int(args.seed))
    split_rows = copy_split_images(root, raw_root, split_root, records, split_by_sample)
    write_csv(split_manifest_csv, split_rows, SPLIT_MANIFEST_COLUMNS)

    summary = build_summary(root, records, split_rows, seed=int(args.seed))
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    validation = summary["validation"]
    ok = (
        validation["every_readable_image_in_split_once"]
        and validation["no_sample_id_crosses_splits"]
        and validation["all_grades_in_each_split"]
        and not validation["duplicate_manifest_paths"]
        and not validation["duplicate_split_manifest_paths"]
    )

    print(f"Wrote manifest: {repo_relative(root, manifest_csv)}")
    print(f"Wrote split manifest: {repo_relative(root, split_manifest_csv)}")
    print(f"Wrote summary: {repo_relative(root, summary_json)}")
    print(f"Readable images: {summary['total_images']}")
    print(f"Split validation passed: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

