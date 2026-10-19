from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import pandas as pd

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _normalize_grade(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    lower = text.lower().replace("_", " ").strip()
    for n in ("1", "2", "3"):
        if n in lower:
            return f"Grade {n}"
    return None


def _is_readable_image(path: Path) -> tuple[bool, tuple[int, int] | None, str | None]:
    try:
        img = cv2.imread(str(path))
    except Exception as exc:  # noqa: BLE001
        return (False, None, f"cv2.imread error: {exc}")
    if img is None:
        return (False, None, "cv2.imread returned None")
    height, width = img.shape[:2]
    if height <= 0 or width <= 0:
        return (False, (width, height), "non-positive dimensions")
    return (True, (width, height), None)


def validate_labels_csv(labels_csv: Path, summary_json: Path, repo_root: Path) -> dict:
    df = pd.read_csv(labels_csv)
    if "image_path" not in df.columns or "grade" not in df.columns:
        raise ValueError("Labels CSV must contain 'image_path' and 'grade' columns.")

    total = len(df)
    valid = 0
    invalid = 0

    per_class = Counter()
    invalid_reasons = Counter()
    duplicates: list[str] = []

    seen_paths: set[str] = set()
    duplicate_counter = Counter(df["image_path"].astype(str))
    duplicates = [p for p, c in duplicate_counter.items() if c > 1]

    invalid_examples: dict[str, list[str]] = defaultdict(list)

    for _, row in df.iterrows():
        rel_path = str(row["image_path"]).strip()
        grade = _normalize_grade(row["grade"])
        if grade is None:
            invalid += 1
            invalid_reasons["invalid_grade"] += 1
            if len(invalid_examples["invalid_grade"]) < 10:
                invalid_examples["invalid_grade"].append(rel_path)
            continue

        image_path = (repo_root / rel_path).resolve()
        if not image_path.exists():
            invalid += 1
            invalid_reasons["missing_file"] += 1
            if len(invalid_examples["missing_file"]) < 10:
                invalid_examples["missing_file"].append(rel_path)
            continue

        ok, dims, reason = _is_readable_image(image_path)
        if not ok:
            invalid += 1
            invalid_reasons["unreadable_image"] += 1
            if len(invalid_examples["unreadable_image"]) < 10:
                invalid_examples["unreadable_image"].append(rel_path)
            continue

        if dims is None:
            invalid += 1
            invalid_reasons["invalid_dimensions"] += 1
            if len(invalid_examples["invalid_dimensions"]) < 10:
                invalid_examples["invalid_dimensions"].append(rel_path)
            continue

        valid += 1
        per_class[grade] += 1
        seen_paths.add(rel_path)

    summary = {
        "total_images": total,
        "valid_images": valid,
        "invalid_images": invalid,
        "images_per_class": dict(per_class),
        "invalid_reasons": dict(invalid_reasons),
        "duplicate_paths": duplicates,
        "invalid_examples": dict(invalid_examples),
    }

    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate berry grading dataset labels and images.")
    parser.add_argument(
        "--labels",
        type=Path,
        required=True,
        help="Explicit path to the labels CSV; no historical dataset is selected implicitly.",
    )
    parser.add_argument("--out", type=Path, default=None, help="Output summary JSON path.")
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    labels_csv = args.labels
    out_json = (
        args.out
        or (repo_root / "data" / "processed" / "grading_forecast" / "berry_dataset_validation_summary.json")
    )

    if not labels_csv.exists():
        print(f"Missing labels CSV: {labels_csv}")
        return 2

    try:
        summary = validate_labels_csv(labels_csv=labels_csv, summary_json=out_json, repo_root=repo_root)
    except Exception as exc:  # noqa: BLE001
        print(f"Validation failed: {exc}")
        return 1

    print(f"Wrote: {out_json}")
    print(
        f"Total: {summary['total_images']} | Valid: {summary['valid_images']} | Invalid: {summary['invalid_images']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

