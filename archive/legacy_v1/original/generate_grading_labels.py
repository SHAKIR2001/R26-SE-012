from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

GRADE_DIR_TO_LABEL = {
    "grade_1": "Grade 1",
    "grade_2": "Grade 2",
    "grade_3": "Grade 3",
}

CSV_COLUMNS = [
    "image_id",
    "image_path",
    "grade",
    "size_quality",
    "color_quality",
    "texture_quality",
    "broken_level",
    "light_berry_level",
    "pinhead_level",
    "foreign_matter_visible",
    "mould_visible",
    "insect_damage_visible",
]

DEFAULT_UNKNOWN_FIELDS = {
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


@dataclass(frozen=True)
class ImageRecord:
    image_path: Path
    grade_dir_name: str


def repo_root_from_script() -> Path:
    # scripts/ -> repo root
    return Path(__file__).resolve().parents[1]


def is_supported_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def validate_image_with_pillow(path: Path) -> bool:
    from PIL import Image  # type: ignore

    try:
        if path.stat().st_size <= 0:
            return False
    except Exception:
        return False

    try:
        with Image.open(path) as img:
            img.load()
        return True
    except Exception:
        return False


def ensure_pillow_available() -> bool:
    try:
        import PIL  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def gather_grade_images(grade_dir: Path) -> list[Path]:
    if not grade_dir.exists():
        return []

    image_paths: list[Path] = []
    for path in grade_dir.rglob("*"):
        if not is_supported_image(path):
            continue
        if validate_image_with_pillow(path):
            image_paths.append(path)

    image_paths.sort(key=lambda p: p.as_posix().lower())
    return image_paths


def iter_image_records(berry_images_root: Path) -> Iterable[ImageRecord]:
    for grade_dir_name in sorted(GRADE_DIR_TO_LABEL.keys()):
        grade_dir = berry_images_root / grade_dir_name
        for path in gather_grade_images(grade_dir):
            yield ImageRecord(image_path=path, grade_dir_name=grade_dir_name)


def to_repo_relative_posix_path(repo_root: Path, path: Path) -> str:
    try:
        relative = path.resolve().relative_to(repo_root.resolve())
    except Exception:
        relative = path
    return relative.as_posix()


def make_image_id(index: int) -> str:
    return f"IMG_{index:06d}"


def write_csv(output_csv_path: Path, rows: list[dict[str, str]]) -> None:
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_summary_json(output_json_path: Path, summary: dict[str, int]) -> None:
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> int:
    if not ensure_pillow_available():
        print("Error: Pillow is required. Install with: pip install Pillow")
        return 1

    repo_root = repo_root_from_script()
    berry_images_root = repo_root / "data" / "raw" / "berry_images"

    output_dir = repo_root / "data" / "annotations" / "grading_forecast"
    output_csv = output_dir / "berry_grading_labels.csv"
    output_summary = output_dir / "berry_dataset_summary.json"

    image_records = list(iter_image_records(berry_images_root))
    image_records.sort(key=lambda r: r.image_path.as_posix().lower())

    grade_counts = {grade_dir: 0 for grade_dir in GRADE_DIR_TO_LABEL.keys()}
    rows: list[dict[str, str]] = []
    for idx, record in enumerate(image_records, start=1):
        grade_counts[record.grade_dir_name] += 1
        rows.append(
            {
                "image_id": make_image_id(idx),
                "image_path": to_repo_relative_posix_path(repo_root, record.image_path),
                "grade": GRADE_DIR_TO_LABEL.get(record.grade_dir_name, "unknown"),
                **DEFAULT_UNKNOWN_FIELDS,
            }
        )

    write_csv(output_csv, rows)
    summary = {
        "total_images": len(rows),
        "grade_1_count": grade_counts.get("grade_1", 0),
        "grade_2_count": grade_counts.get("grade_2", 0),
        "grade_3_count": grade_counts.get("grade_3", 0),
    }
    write_summary_json(output_summary, summary)

    print(f"Total images found: {summary['total_images']}")
    print(f"Grade 1 images: {summary['grade_1_count']}")
    print(f"Grade 2 images: {summary['grade_2_count']}")
    print(f"Grade 3 images: {summary['grade_3_count']}")
    print(f"Output CSV: {to_repo_relative_posix_path(repo_root, output_csv)}")
    print(f"Summary JSON: {to_repo_relative_posix_path(repo_root, output_summary)}")

    if summary["total_images"] == 0:
        print(
            "Warning: No images were found. Check that your dataset exists under "
            "data/raw/berry_images/grade_1..grade_3 and that files are valid JPG/PNG."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
