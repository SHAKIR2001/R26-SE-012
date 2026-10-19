from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image

sys.dont_write_bytecode = True

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
GRADE_DIR_TO_LABEL = {
    "grade_1": "Grade 1",
    "grade_2": "Grade 2",
    "grade_3": "Grade 3",
}
UNKNOWN_LABEL_FIELDS = {
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
BERRY_MANIFEST_COLUMNS = [
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
    *UNKNOWN_LABEL_FIELDS.keys(),
]
SEED = 42


@dataclass(frozen=True)
class BerryRecord:
    image_id: str
    image_path: str
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


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def rel_posix(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def make_image_id(index: int) -> str:
    return f"IMGV2_{index:06d}"


def normalize_district(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"\s+", " ", text.replace("_", " "))
    return text.title()


def normalize_grade(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    match = re.search(r"(\d+)", text)
    if not match:
        return None
    return f"Grade {match.group(1)}"


def normalize_price_type(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().lower().replace(" ", "_")
    text = re.sub(r"[^a-z_]", "", text)
    if text == "avg":
        text = "average"
    return text or None


def parse_price(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        price = float(text)
    except ValueError:
        return None
    if price <= 0:
        return None
    return price


def image_metadata(path: Path) -> tuple[bool, int | None, int | None, float | None, str, str, str | None]:
    try:
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        with Image.open(path) as img:
            img.load()
            width, height = img.size
            exif = img.getexif()
            camera_model = str(exif.get(272, "unknown")).strip() if exif else "unknown"
            orientation = str(exif.get(274, "unknown")).strip() if exif else "unknown"
        aspect_ratio = round(width / height, 6) if height else None
        return True, width, height, aspect_ratio, camera_model or "unknown", orientation or "unknown", digest
    except Exception:
        return False, None, None, None, "unknown", "unknown", None


def discover_berry_records(root: Path, raw_root: Path) -> tuple[list[BerryRecord], dict[str, Any]]:
    records: list[BerryRecord] = []
    unreadable: list[str] = []
    missing_or_inconsistent: list[str] = []

    candidates: list[tuple[str, Path]] = []
    for grade_dir in sorted(GRADE_DIR_TO_LABEL):
        grade_root = raw_root / grade_dir
        if not grade_root.exists():
            continue
        for path in sorted(grade_root.rglob("*"), key=lambda p: p.as_posix().lower()):
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                candidates.append((grade_dir, path))

    for index, (grade_dir, path) in enumerate(candidates, start=1):
        rel_parts = path.relative_to(raw_root / grade_dir).parts
        if len(rel_parts) < 2:
            sample_id = "unassigned_root"
            missing_or_inconsistent.append(rel_posix(root, path))
        else:
            sample_id = rel_parts[0]

        readable, width, height, aspect, camera_model, orientation, digest = image_metadata(path)
        if not readable:
            unreadable.append(rel_posix(root, path))

        records.append(
            BerryRecord(
                image_id=make_image_id(index),
                image_path=rel_posix(root, path),
                grade_dir=grade_dir,
                grade=GRADE_DIR_TO_LABEL[grade_dir],
                sample_id=sample_id,
                camera_model=camera_model,
                orientation=orientation,
                width=width,
                height=height,
                aspect_ratio=aspect,
                image_readable=readable,
                content_hash=digest,
            )
        )

    summary = {
        "unreadable_images": unreadable,
        "inconsistent_structure_images": missing_or_inconsistent,
    }
    return records, summary


def write_berry_manifest(path: Path, records: list[BerryRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=BERRY_MANIFEST_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "image_id": record.image_id,
                    "image_path": record.image_path,
                    "grade": record.grade,
                    "sample_id": record.sample_id,
                    "camera_model": record.camera_model,
                    "orientation": record.orientation,
                    "width": "" if record.width is None else record.width,
                    "height": "" if record.height is None else record.height,
                    "aspect_ratio": "" if record.aspect_ratio is None else record.aspect_ratio,
                    "image_readable": str(record.image_readable).lower(),
                    **UNKNOWN_LABEL_FIELDS,
                }
            )


def split_samples(records: list[BerryRecord], seed: int) -> dict[tuple[str, str], str]:
    samples_by_grade: dict[str, list[str]] = defaultdict(list)
    for record in records:
        if not record.image_readable:
            continue
        key = record.sample_id
        if key not in samples_by_grade[record.grade_dir]:
            samples_by_grade[record.grade_dir].append(key)

    rng = random.Random(seed)
    split_map: dict[tuple[str, str], str] = {}
    for grade_dir, sample_ids in sorted(samples_by_grade.items()):
        sample_ids = sorted(sample_ids)
        rng.shuffle(sample_ids)
        total = len(sample_ids)
        test_count = max(1, round(total * 0.15))
        val_count = max(1, round(total * 0.15))
        train_count = total - val_count - test_count
        if train_count <= 0:
            raise ValueError(f"Not enough samples to split grade {grade_dir}: {total}")

        train_samples = sample_ids[:train_count]
        val_samples = sample_ids[train_count : train_count + val_count]
        test_samples = sample_ids[train_count + val_count :]

        for sample_id in train_samples:
            split_map[(grade_dir, sample_id)] = "train"
        for sample_id in val_samples:
            split_map[(grade_dir, sample_id)] = "val"
        for sample_id in test_samples:
            split_map[(grade_dir, sample_id)] = "test"

    return split_map


def reset_v2_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def create_berry_split(root: Path, split_root: Path, split_manifest: Path, records: list[BerryRecord], seed: int) -> dict[str, Any]:
    split_map = split_samples(records, seed=seed)
    reset_v2_directory(split_root)

    rows: list[dict[str, str]] = []
    for record in records:
        if not record.image_readable:
            continue
        split = split_map[(record.grade_dir, record.sample_id)]
        src = root / record.image_path
        dst = split_root / split / record.grade_dir / record.sample_id / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        rows.append(
            {
                "image_id": record.image_id,
                "source_image_path": record.image_path,
                "split_image_path": rel_posix(root, dst),
                "split": split,
                "grade": record.grade,
                "grade_dir": record.grade_dir,
                "sample_id": record.sample_id,
            }
        )

    split_manifest.parent.mkdir(parents=True, exist_ok=True)
    with split_manifest.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["image_id", "source_image_path", "split_image_path", "split", "grade", "grade_dir", "sample_id"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return validate_berry_split(records=records, split_rows=rows)


def validate_berry_split(records: list[BerryRecord], split_rows: list[dict[str, str]]) -> dict[str, Any]:
    readable_records = [r for r in records if r.image_readable]
    source_paths = [r.image_path for r in readable_records]
    split_source_paths = [row["source_image_path"] for row in split_rows]

    source_counter = Counter(split_source_paths)
    duplicate_split_sources = sorted([path for path, count in source_counter.items() if count > 1])
    missing_from_split = sorted(set(source_paths) - set(split_source_paths))
    extra_in_split = sorted(set(split_source_paths) - set(source_paths))

    split_grade_image_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    split_grade_sample_sets: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    sample_to_splits: dict[tuple[str, str], set[str]] = defaultdict(set)

    for row in split_rows:
        split = row["split"]
        grade_dir = row["grade_dir"]
        sample_id = row["sample_id"]
        split_grade_image_counts[split][grade_dir] += 1
        split_grade_sample_sets[split][grade_dir].add(sample_id)
        sample_to_splits[(grade_dir, sample_id)].add(split)

    crossing_samples = [
        {"grade_dir": grade_dir, "sample_id": sample_id, "splits": sorted(splits)}
        for (grade_dir, sample_id), splits in sorted(sample_to_splits.items())
        if len(splits) > 1
    ]

    split_sample_counts = {
        split: {grade: len(samples) for grade, samples in grades.items()}
        for split, grades in split_grade_sample_sets.items()
    }

    passed = (
        not duplicate_split_sources
        and not missing_from_split
        and not extra_in_split
        and not crossing_samples
        and all(grade in split_grade_image_counts.get(split, {}) for split in ["train", "val", "test"] for grade in GRADE_DIR_TO_LABEL)
    )

    return {
        "validation_passed": passed,
        "seed": SEED,
        "total_split_images": len(split_rows),
        "duplicate_source_paths_in_split": duplicate_split_sources,
        "missing_source_paths_from_split": missing_from_split,
        "extra_source_paths_in_split": extra_in_split,
        "sample_id_cross_split_violations": crossing_samples,
        "image_counts_by_split_and_grade": {
            split: dict(sorted(grades.items())) for split, grades in sorted(split_grade_image_counts.items())
        },
        "sample_counts_by_split_and_grade": {
            split: dict(sorted(grades.items())) for split, grades in sorted(split_sample_counts.items())
        },
    }


def summarize_berry(records: list[BerryRecord], discovery_summary: dict[str, Any], split_validation: dict[str, Any]) -> dict[str, Any]:
    readable = [r for r in records if r.image_readable]
    duplicate_paths = sorted([path for path, count in Counter(r.image_path for r in records).items() if count > 1])
    duplicate_hashes = {
        digest: [r.image_path for r in records if r.content_hash == digest]
        for digest, count in Counter(r.content_hash for r in records if r.content_hash).items()
        if count > 1
    }

    image_count_per_sample: dict[str, dict[str, int]] = defaultdict(dict)
    sample_counter: Counter[tuple[str, str]] = Counter((r.grade_dir, r.sample_id) for r in readable)
    for (grade_dir, sample_id), count in sorted(sample_counter.items()):
        image_count_per_sample[grade_dir][sample_id] = count

    samples_lt4 = [
        {"grade_dir": grade_dir, "sample_id": sample_id, "image_count": count}
        for (grade_dir, sample_id), count in sorted(sample_counter.items())
        if count < 4
    ]
    samples_gt4 = [
        {"grade_dir": grade_dir, "sample_id": sample_id, "image_count": count}
        for (grade_dir, sample_id), count in sorted(sample_counter.items())
        if count > 4
    ]

    return {
        "dataset_version": "berry_v2",
        "generated_at": utc_now_iso(),
        "raw_root": "data/raw/berry_images",
        "manifest": "data/annotations/grading_forecast/berry_grading_labels_v2.csv",
        "split_root": "data/processed/grading_forecast/berry_split_v2",
        "split_manifest": "data/processed/grading_forecast/berry_split_v2_manifest.csv",
        "total_images": len(records),
        "readable_images": len(readable),
        "images_per_grade": dict(sorted(Counter(r.grade for r in readable).items())),
        "samples_per_grade": {
            grade_dir: len({r.sample_id for r in readable if r.grade_dir == grade_dir})
            for grade_dir in sorted(GRADE_DIR_TO_LABEL)
        },
        "total_sample_count": len({(r.grade_dir, r.sample_id) for r in readable}),
        "image_count_per_sample": image_count_per_sample,
        "samples_with_fewer_than_4_images": samples_lt4,
        "samples_with_more_than_4_images": samples_gt4,
        "unreadable_images": discovery_summary["unreadable_images"],
        "missing_files": [],
        "duplicate_image_paths": duplicate_paths,
        "duplicate_image_content_groups": duplicate_hashes,
        "image_dimensions": {
            f"{r.width}x{r.height}": count
            for (r_width, r_height), count in sorted(Counter((r.width, r.height) for r in readable).items())
            for r in [type("Dimension", (), {"width": r_width, "height": r_height})]
        },
        "aspect_ratios": {str(k): v for k, v in sorted(Counter(r.aspect_ratio for r in readable).items())},
        "exif_camera_models": dict(sorted(Counter(r.camera_model for r in readable).items())),
        "exif_orientation_distribution": dict(sorted(Counter(r.orientation for r in readable).items())),
        "inconsistent_structure_images": discovery_summary["inconsistent_structure_images"],
        "split": split_validation,
        "notes": [
            "Detailed visual-quality columns are retained as unknown placeholders only.",
            "Sample-level split prevents images from the same physical sample crossing train/val/test.",
            "Readable unusual samples are retained and documented rather than silently discarded.",
        ],
    }


def clean_price_v2(input_csv: Path, output_csv: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = pd.read_csv(input_csv)
    required = {
        "date",
        "commodity",
        "country",
        "district",
        "grade",
        "price_type",
        "price_lkr_per_kg",
        "market_level",
        "frequency",
    }
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise ValueError(f"Raw price CSV missing required columns: {missing}")

    df = raw.copy()
    raw_count = len(df)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["district"] = df["district"].map(normalize_district)
    df["grade"] = df["grade"].map(normalize_grade)
    df["price_type"] = df["price_type"].map(normalize_price_type)
    df["price_lkr_per_kg"] = df["price_lkr_per_kg"].map(parse_price)
    df["commodity"] = df["commodity"].astype(str).str.strip().str.lower()
    df["country"] = df["country"].astype(str).str.strip()
    df["market_level"] = df["market_level"].astype(str).str.strip().str.lower()
    df["frequency"] = df["frequency"].astype(str).str.strip().str.lower()

    invalid_before_drop = {
        "invalid_dates": int(df["date"].isna().sum()),
        "invalid_districts": int(df["district"].isna().sum()),
        "invalid_grades": int(df["grade"].isna().sum()),
        "invalid_price_types": int(df["price_type"].isna().sum()),
        "invalid_prices": int(df["price_lkr_per_kg"].isna().sum()),
    }

    df = df.dropna(subset=["date", "district", "grade", "price_type", "price_lkr_per_kg"])
    df = df[df["grade"].isin({"Grade 1", "Grade 2", "Grade 3"})]
    df = df[df["price_type"].isin({"average", "highest", "lowest"})]
    duplicate_count = int(df.duplicated(["date", "district", "grade", "price_type"]).sum())
    df = df.drop_duplicates(["date", "district", "grade", "price_type"], keep="first")
    df = df.sort_values(["date", "district", "grade", "price_type"], ascending=True)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    summary = {
        "raw_row_count": raw_count,
        "cleaned_row_count": int(len(df)),
        "invalid_before_drop": invalid_before_drop,
        "duplicate_date_district_grade_price_type_rows_removed": duplicate_count,
        "cleaned_date_range": {
            "min": str(df["date"].min().date()) if not df.empty else None,
            "max": str(df["date"].max().date()) if not df.empty else None,
        },
    }
    return df, summary


def create_price_target(cleaned: pd.DataFrame, output_csv: Path) -> pd.DataFrame:
    subset = cleaned[
        (cleaned["commodity"] == "black_pepper")
        & (cleaned["country"] == "Sri Lanka")
        & (cleaned["district"] == "National")
        & (cleaned["grade"] == "Grade 1")
        & (cleaned["price_type"] == "average")
        & (cleaned["market_level"] == "farm_gate")
        & (cleaned["frequency"] == "weekly")
    ].copy()
    duplicate_dates = subset[subset.duplicated(["date"], keep=False)]
    if not duplicate_dates.empty:
        raise ValueError(f"Target filter produced duplicate dates: {duplicate_dates['date'].dt.date.astype(str).tolist()}")
    out = subset[["date", "price_lkr_per_kg"]].sort_values("date")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_csv, index=False)
    return out


def date_gap_summary(dates: list[pd.Timestamp]) -> dict[str, Any]:
    if not dates:
        return {
            "observation_count": 0,
            "min_date": None,
            "max_date": None,
            "observed_intervals_days": {},
            "gaps_gt_8_days": [],
            "gap_count_gt_8_days": 0,
            "largest_gap_days": None,
        }

    ordered = sorted(pd.Timestamp(d).date() for d in dates)
    intervals = [(ordered[i] - ordered[i - 1]).days for i in range(1, len(ordered))]
    gaps = [
        {
            "from": ordered[i - 1].isoformat(),
            "to": ordered[i].isoformat(),
            "days": (ordered[i] - ordered[i - 1]).days,
        }
        for i in range(1, len(ordered))
        if (ordered[i] - ordered[i - 1]).days > 8
    ]
    return {
        "observation_count": len(ordered),
        "min_date": ordered[0].isoformat(),
        "max_date": ordered[-1].isoformat(),
        "observed_intervals_days": {str(k): v for k, v in sorted(Counter(intervals).items())},
        "gaps_gt_8_days": gaps,
        "gap_count_gt_8_days": len(gaps),
        "largest_gap_days": max((gap["days"] for gap in gaps), default=None),
    }


def create_forecast_splits(target: pd.DataFrame, out_dir: Path) -> dict[str, Any]:
    df = target.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "price_lkr_per_kg"]).sort_values("date")
    n = len(df)
    if n < 3:
        raise ValueError("Need at least 3 target observations for train/validation/test split.")
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)
    train_end = max(1, min(train_end, n - 2))
    val_end = max(train_end + 1, min(val_end, n - 1))

    splits = {
        "train": df.iloc[:train_end].copy(),
        "validation": df.iloc[train_end:val_end].copy(),
        "test": df.iloc[val_end:].copy(),
    }
    for split_name, split_df in splits.items():
        split_df.to_csv(out_dir / f"forecast_{split_name}.csv", index=False)

    return {
        split_name: {
            "rows": int(len(split_df)),
            "percentage": round((len(split_df) / n) * 100.0, 2),
            "start_date": str(split_df["date"].min().date()) if not split_df.empty else None,
            "end_date": str(split_df["date"].max().date()) if not split_df.empty else None,
        }
        for split_name, split_df in splits.items()
    }


def coverage_summary(cleaned: pd.DataFrame, target: pd.DataFrame, clean_summary: dict[str, Any], split_summary: dict[str, Any]) -> dict[str, Any]:
    cleaned = cleaned.copy()
    cleaned["year"] = cleaned["date"].dt.year
    target_dates = list(pd.to_datetime(target["date"], errors="coerce").dropna())

    grade_year = (
        cleaned.pivot_table(index="year", columns="grade", values="date", aggfunc="count", fill_value=0)
        .astype(int)
        .to_dict()
    )
    national_grade2 = cleaned[
        (cleaned["district"] == "National") & (cleaned["grade"] == "Grade 2") & (cleaned["price_type"] == "average")
    ].copy()

    return {
        "dataset_version": "price_v2",
        "generated_at": utc_now_iso(),
        "raw_source": "data/raw/market_prices/dea_farmgate_weekly_prices_2016_2026.csv",
        "cleaned_output": "data/processed/grading_forecast/price_v2/cleaned_price_data_v2.csv",
        "target_output": "data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv",
        **clean_summary,
        "raw_unique_values": {
            "districts": sorted(cleaned["district"].dropna().unique().tolist()),
            "grades": sorted(cleaned["grade"].dropna().unique().tolist()),
            "price_types": sorted(cleaned["price_type"].dropna().unique().tolist()),
            "market_levels": sorted(cleaned["market_level"].dropna().unique().tolist()),
            "frequencies": sorted(cleaned["frequency"].dropna().unique().tolist()),
        },
        "primary_target": {
            "commodity": "black_pepper",
            "country": "Sri Lanka",
            "district": "National",
            "grade": "Grade 1",
            "price_type": "average",
            "market_level": "farm_gate",
            "frequency": "weekly",
            **date_gap_summary(target_dates),
        },
        "grade_coverage_by_year": {grade: {str(year): count for year, count in years.items()} for grade, years in grade_year.items()},
        "national_grade2_average": {
            **date_gap_summary(list(national_grade2["date"])),
            "coverage_by_year": {str(k): int(v) for k, v in national_grade2.groupby("year").size().to_dict().items()},
            "pp2_decision": "Document as sparse; not used as primary PP2 forecasting target.",
        },
        "forecast_split": split_summary,
        "notes": [
            "Missing prices were not fabricated.",
            "Grade 2 observations were preserved where available but not interpolated.",
            "Feature engineering is intentionally deferred to Phase 3.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare Phase 1 V2 dataset artifacts without touching V1 outputs.")
    parser.add_argument("--seed", type=int, default=SEED, help="Deterministic sample split seed.")
    args = parser.parse_args(argv)

    root = repo_root()
    annotations_dir = root / "data" / "annotations" / "grading_forecast"
    processed_dir = root / "data" / "processed" / "grading_forecast"
    berry_raw = root / "data" / "raw" / "berry_images"
    price_raw = root / "data" / "raw" / "market_prices" / "dea_farmgate_weekly_prices_2016_2026.csv"

    if not berry_raw.exists():
        print(f"Missing berry raw directory: {berry_raw}")
        return 2
    if not price_raw.exists():
        print(f"Missing price raw CSV: {price_raw}")
        return 2

    berry_manifest = annotations_dir / "berry_grading_labels_v2.csv"
    berry_summary_path = processed_dir / "berry_dataset_v2_summary.json"
    berry_split_root = processed_dir / "berry_split_v2"
    berry_split_manifest = processed_dir / "berry_split_v2_manifest.csv"

    records, discovery_summary = discover_berry_records(root, berry_raw)
    write_berry_manifest(berry_manifest, records)
    split_validation = create_berry_split(root, berry_split_root, berry_split_manifest, records, seed=int(args.seed))
    berry_summary = summarize_berry(records, discovery_summary, split_validation)
    write_json(berry_summary_path, berry_summary)

    price_v2_dir = processed_dir / "price_v2"
    price_v2_dir.mkdir(parents=True, exist_ok=True)
    cleaned_csv = price_v2_dir / "cleaned_price_data_v2.csv"
    target_csv = price_v2_dir / "national_grade1_average_weekly.csv"
    coverage_json = price_v2_dir / "price_v2_coverage_summary.json"

    cleaned, clean_summary = clean_price_v2(price_raw, cleaned_csv)
    target = create_price_target(cleaned, target_csv)
    split_summary = create_forecast_splits(target, price_v2_dir)
    price_summary = coverage_summary(cleaned, target, clean_summary, split_summary)
    write_json(coverage_json, price_summary)

    all_passed = bool(split_validation["validation_passed"]) and len(target) > 0
    print("Phase 1 V2 dataset preparation complete." if all_passed else "Phase 1 V2 dataset preparation finished with validation warnings.")
    print(f"Berry manifest: {rel_posix(root, berry_manifest)} ({len(records)} rows)")
    print(f"Berry summary: {rel_posix(root, berry_summary_path)}")
    print(f"Berry split manifest: {rel_posix(root, berry_split_manifest)}")
    print(f"Price cleaned: {rel_posix(root, cleaned_csv)} ({len(cleaned)} rows)")
    print(f"Price target: {rel_posix(root, target_csv)} ({len(target)} rows)")
    print(f"Price summary: {rel_posix(root, coverage_json)}")
    print(f"Berry split validation passed: {split_validation['validation_passed']}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
