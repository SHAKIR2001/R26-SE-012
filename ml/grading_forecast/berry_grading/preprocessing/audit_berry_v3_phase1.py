from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev

from PIL import ExifTags, Image, ImageDraw, ImageFont, ImageOps, ImageStat


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
V3_CLASS_NAMES = {0: "V3 Grade 1", 1: "V3 Grade 2"}
SEED = 42


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_order(value: str, namespace: str) -> str:
    return hashlib.sha256(f"{SEED}|{namespace}|{value}".encode("utf-8")).hexdigest()


def image_files(root: Path) -> list[Path]:
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS),
        key=lambda path: path.as_posix().lower(),
    )


def parse_yolo_label(path: Path) -> tuple[int, float, float, float, float]:
    rows = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one V3 sample/batch box in {path}; found {len(rows)}")
    fields = rows[0].split()
    if len(fields) != 5:
        raise ValueError(f"Expected five YOLO fields in {path}: {rows[0]}")
    class_id = int(fields[0])
    coordinates = tuple(float(value) for value in fields[1:])
    if class_id not in V3_CLASS_NAMES:
        raise ValueError(f"Unsupported V3 class {class_id} in {path}")
    if any(value < 0.0 or value > 1.0 for value in coordinates):
        raise ValueError(f"Out-of-range normalized coordinate in {path}")
    return class_id, *coordinates


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def split_groups(group_rows: dict[str, list[dict[str, object]]]) -> dict[str, str]:
    groups_by_grade: dict[str, list[str]] = defaultdict(list)
    for group_id, rows in group_rows.items():
        grades = {str(row["v3_grade"]) for row in rows}
        if len(grades) != 1:
            raise ValueError(f"Physical sample has inconsistent V3 classes: {group_id}: {sorted(grades)}")
        groups_by_grade[next(iter(grades))].append(group_id)

    assignments: dict[str, str] = {}
    for grade, group_ids in sorted(groups_by_grade.items()):
        ordered = sorted(group_ids, key=lambda value: stable_order(value, f"split:{grade}"))
        train_count = round(len(ordered) * 0.70)
        validation_count = round(len(ordered) * 0.15)
        for index, group_id in enumerate(ordered):
            if index < train_count:
                partition = "TRAIN"
            elif index < train_count + validation_count:
                partition = "VALIDATION"
            else:
                partition = "TEST"
            assignments[group_id] = partition
    return assignments


def descriptive(values: list[float]) -> dict[str, float]:
    return {
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "mean": round(mean(values), 6),
        "std": round(pstdev(values), 6),
    }


def read_image_metadata(path: Path) -> dict[str, object]:
    with Image.open(path) as image:
        width, height = image.size
        exif = image.getexif()
        model = str(exif.get(272, "unknown") or "unknown").strip()
        make = str(exif.get(271, "unknown") or "unknown").strip()
        orientation = str(exif.get(274, "unknown") or "unknown")
        upright = ImageOps.exif_transpose(image).convert("RGB")
        upright.thumbnail((256, 256), Image.Resampling.BILINEAR)
        brightness = float(ImageStat.Stat(upright.convert("L")).mean[0])
        hsv = upright.convert("HSV")
        saturation = float(ImageStat.Stat(hsv).mean[1])

        border = max(1, min(upright.size) // 10)
        mask = Image.new("L", upright.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle((0, 0, upright.width - 1, upright.height - 1), fill=255)
        if upright.width > border * 2 and upright.height > border * 2:
            draw.rectangle((border, border, upright.width - border - 1, upright.height - border - 1), fill=0)
        border_pixels = [value for value, selected in zip(upright.convert("L").getdata(), mask.getdata()) if selected]
        border_brightness = float(mean(border_pixels)) if border_pixels else brightness

    return {
        "width": width,
        "height": height,
        "aspect_ratio": width / height,
        "camera_make": make,
        "camera_model": model,
        "exif_orientation": orientation,
        "brightness_0_255": brightness,
        "saturation_0_255": saturation,
        "border_brightness_0_255": border_brightness,
    }


def make_contact_sheet(
    entries: list[tuple[str, Path]],
    output: Path,
    *,
    columns: int,
    cell_size: tuple[int, int] = (280, 240),
) -> None:
    cell_width, cell_height = cell_size
    rows = math.ceil(len(entries) / columns)
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, (caption, source) in enumerate(entries):
        with Image.open(source) as image:
            rendered = ImageOps.exif_transpose(image).convert("RGB")
            rendered.thumbnail((cell_width - 12, cell_height - 34), Image.Resampling.LANCZOS)
        x = (index % columns) * cell_width
        y = (index // columns) * cell_height
        image_x = x + (cell_width - rendered.width) // 2
        image_y = y + 24 + (cell_height - 30 - rendered.height) // 2
        sheet.paste(rendered, (image_x, image_y))
        draw.text((x + 6, y + 6), caption, fill="black", font=font)

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def save_blind_copy(source: Path, output: Path) -> None:
    with Image.open(source) as image:
        clean = ImageOps.exif_transpose(image).convert("RGB")
        output.parent.mkdir(parents=True, exist_ok=True)
        clean.save(output, format="JPEG", quality=95, optimize=True)


def choose_group_diverse(
    rows: list[dict[str, object]],
    count: int,
    namespace: str,
) -> list[dict[str, object]]:
    by_group: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_group[str(row["physical_sample_id"])].append(row)
    groups = sorted(by_group, key=lambda value: stable_order(value, f"{namespace}:groups"))
    for group_id in groups:
        by_group[group_id].sort(
            key=lambda row: stable_order(str(row["v3_image_path"]), f"{namespace}:images")
        )

    selected: list[dict[str, object]] = []
    offset = 0
    while len(selected) < count:
        added = False
        for group_id in groups:
            candidates = by_group[group_id]
            if offset < len(candidates):
                selected.append(candidates[offset])
                added = True
                if len(selected) == count:
                    break
        if not added:
            break
        offset += 1
    if len(selected) != count:
        raise ValueError(f"Unable to select {count} records for {namespace}; found {len(selected)}")
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and prepare V3 Phase 1 research manifests.")
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(r"D:\work\Year - 4\pepper\project\datset reorder"),
    )
    parser.add_argument(
        "--v3-root",
        type=Path,
        default=Path("data/raw/Pepper Berry Grading V3.yolov8"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/processed/grading_forecast/berry_v3"),
    )
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    v3_root = args.v3_root.resolve()
    output_root = args.output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty Phase 1 output directory: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    source_paths = image_files(source_root)
    source_hash_index: dict[str, list[Path]] = defaultdict(list)
    for source_path in source_paths:
        source_hash_index[sha256(source_path)].append(source_path)

    records: list[dict[str, object]] = []
    unmatched: list[str] = []
    ambiguous: list[dict[str, object]] = []
    for roboflow_split in ("train", "valid", "test"):
        image_dir = v3_root / roboflow_split / "images"
        label_dir = v3_root / roboflow_split / "labels"
        for v3_image in image_files(image_dir):
            image_hash = sha256(v3_image)
            matches = source_hash_index.get(image_hash, [])
            if not matches:
                unmatched.append(v3_image.as_posix())
                continue
            if len(matches) != 1:
                ambiguous.append(
                    {"v3_image": v3_image.as_posix(), "source_matches": [path.as_posix() for path in matches]}
                )
                continue

            source_image = matches[0]
            source_relative = source_image.relative_to(source_root)
            if len(source_relative.parts) < 3:
                raise ValueError(f"Expected source grade/sample/image hierarchy: {source_image}")
            source_grade, sample_id = source_relative.parts[:2]
            physical_sample_id = f"{source_grade}/{sample_id}"
            label_path = label_dir / f"{v3_image.stem}.txt"
            class_id, x_center, y_center, box_width, box_height = parse_yolo_label(label_path)
            metadata = read_image_metadata(v3_image)
            records.append(
                {
                    "v3_image_path": v3_image.relative_to(v3_root.parents[2]).as_posix(),
                    "v3_label_path": label_path.relative_to(v3_root.parents[2]).as_posix(),
                    "roboflow_split": roboflow_split,
                    "sha256": image_hash,
                    "source_image_path": source_image.as_posix(),
                    "source_grade": source_grade,
                    "sample_id": sample_id,
                    "physical_sample_id": physical_sample_id,
                    "v3_class_id": class_id,
                    "v3_grade": V3_CLASS_NAMES[class_id],
                    "box_x_center": x_center,
                    "box_y_center": y_center,
                    "box_width": box_width,
                    "box_height": box_height,
                    **metadata,
                }
            )

    if unmatched or ambiguous:
        raise ValueError(f"Exact mapping failed: unmatched={len(unmatched)}, ambiguous={len(ambiguous)}")
    if len(records) != 775:
        raise ValueError(f"Expected 775 mapped V3 images; found {len(records)}")

    group_rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        group_rows[str(record["physical_sample_id"])].append(record)
    assignments = split_groups(group_rows)
    for record in records:
        record["research_partition"] = assignments[str(record["physical_sample_id"])]

    source_to_v3 = Counter((str(row["source_grade"]), str(row["v3_grade"])) for row in records)
    if source_to_v3 != Counter({("grade_1", "V3 Grade 1"): 448, ("grade_2", "V3 Grade 2"): 327}):
        raise ValueError(f"Unexpected source/V3 mapping: {source_to_v3}")

    manifest_fields = [
        "v3_image_path",
        "v3_label_path",
        "roboflow_split",
        "sha256",
        "source_image_path",
        "source_grade",
        "sample_id",
        "physical_sample_id",
        "v3_class_id",
        "v3_grade",
        "box_x_center",
        "box_y_center",
        "box_width",
        "box_height",
        "width",
        "height",
        "aspect_ratio",
        "camera_make",
        "camera_model",
        "exif_orientation",
        "brightness_0_255",
        "saturation_0_255",
        "border_brightness_0_255",
        "research_partition",
    ]
    records.sort(key=lambda row: str(row["v3_image_path"]))
    write_csv(output_root / "v3_image_sample_manifest.csv", manifest_fields, records)

    split_rows: list[dict[str, object]] = []
    for group_id in sorted(group_rows):
        rows = group_rows[group_id]
        grades = {str(row["v3_grade"]) for row in rows}
        split_rows.append(
            {
                "physical_sample_id": group_id,
                "source_grade": rows[0]["source_grade"],
                "sample_id": rows[0]["sample_id"],
                "v3_grade": next(iter(grades)),
                "image_count": len(rows),
                "partition": assignments[group_id],
            }
        )
    write_csv(
        output_root / "v3_group_split_manifest.csv",
        ["physical_sample_id", "source_grade", "sample_id", "v3_grade", "image_count", "partition"],
        split_rows,
    )

    partition_sets = {
        partition: {group_id for group_id, assigned in assignments.items() if assigned == partition}
        for partition in ("TRAIN", "VALIDATION", "TEST")
    }
    intersections = {
        "train_validation": sorted(partition_sets["TRAIN"] & partition_sets["VALIDATION"]),
        "train_test": sorted(partition_sets["TRAIN"] & partition_sets["TEST"]),
        "validation_test": sorted(partition_sets["VALIDATION"] & partition_sets["TEST"]),
    }
    union = set().union(*partition_sets.values())
    every_image_once = len(records) == len({str(row["v3_image_path"]) for row in records})
    if any(intersections.values()) or union != set(group_rows) or not every_image_once:
        raise ValueError("Group-aware split validation failed")

    stats_by_grade: dict[str, object] = {}
    for grade in sorted(V3_CLASS_NAMES.values()):
        grade_rows = [row for row in records if row["v3_grade"] == grade]
        stats_by_grade[grade] = {
            "images": len(grade_rows),
            "physical_samples": len({str(row["physical_sample_id"]) for row in grade_rows}),
            "resolution_distribution": dict(
                sorted(Counter(f"{row['width']}x{row['height']}" for row in grade_rows).items())
            ),
            "width": descriptive([float(row["width"]) for row in grade_rows]),
            "height": descriptive([float(row["height"]) for row in grade_rows]),
            "aspect_ratio": descriptive([float(row["aspect_ratio"]) for row in grade_rows]),
            "brightness_0_255": descriptive([float(row["brightness_0_255"]) for row in grade_rows]),
            "saturation_0_255": descriptive([float(row["saturation_0_255"]) for row in grade_rows]),
            "border_brightness_0_255": descriptive(
                [float(row["border_brightness_0_255"]) for row in grade_rows]
            ),
            "camera_make": dict(sorted(Counter(str(row["camera_make"]) for row in grade_rows).items())),
            "camera_model": dict(sorted(Counter(str(row["camera_model"]) for row in grade_rows).items())),
            "exif_orientation": dict(
                sorted(Counter(str(row["exif_orientation"]) for row in grade_rows).items())
            ),
        }

    split_summary: dict[str, object] = {}
    for partition in ("TRAIN", "VALIDATION", "TEST"):
        partition_rows = [row for row in records if row["research_partition"] == partition]
        split_summary[partition] = {
            "groups": len(partition_sets[partition]),
            "images": len(partition_rows),
            "groups_by_v3_grade": dict(
                sorted(Counter(str(row["v3_grade"]) for row in split_rows if row["partition"] == partition).items())
            ),
            "images_by_v3_grade": dict(
                sorted(Counter(str(row["v3_grade"]) for row in partition_rows).items())
            ),
        }

    audit_summary = {
        "phase": "V3 Phase 1 audit preparation",
        "created_date": "2026-10-06",
        "seed": SEED,
        "source_root": source_root.as_posix(),
        "v3_root": v3_root.as_posix(),
        "mapping": {
            "source_images": len(source_paths),
            "v3_images": len(records),
            "exact_matches": len(records),
            "unmatched": len(unmatched),
            "ambiguous": len(ambiguous),
            "duplicate_source_hash_groups": sum(1 for values in source_hash_index.values() if len(values) > 1),
            "physical_samples": len(group_rows),
            "sample_size_distribution": dict(sorted(Counter(len(rows) for rows in group_rows.values()).items())),
            "source_grade_to_v3_grade": {
                f"{source_grade} -> {v3_grade}": count
                for (source_grade, v3_grade), count in sorted(source_to_v3.items())
            },
        },
        "group_aware_split": split_summary,
        "split_validation": {
            "intersections": intersections,
            "all_groups_in_union": union == set(group_rows),
            "every_v3_image_exactly_once": every_image_once,
        },
        "capture_statistics": stats_by_grade,
    }
    (output_root / "v3_phase1_audit_summary.json").write_text(
        json.dumps(audit_summary, indent=2), encoding="utf-8"
    )

    # The visual shortcut sheet is drawn only from the new VALIDATION groups, never TEST.
    shortcut_entries: list[tuple[str, Path]] = []
    for grade in sorted(V3_CLASS_NAMES.values()):
        candidates = [
            row for row in records if row["research_partition"] == "VALIDATION" and row["v3_grade"] == grade
        ]
        chosen = choose_group_diverse(candidates, 12, f"shortcut:{grade}")
        for index, row in enumerate(chosen, start=1):
            shortcut_entries.append((f"{grade} audit {index:02d}", Path(str(row["source_image_path"]))))
    make_contact_sheet(shortcut_entries, output_root / "v3_background_contact_sheet.jpg", columns=4)

    # The blind review also uses only VALIDATION groups and strips filenames/EXIF.
    blind_candidates: list[dict[str, object]] = []
    for grade in sorted(V3_CLASS_NAMES.values()):
        candidates = [
            row for row in records if row["research_partition"] == "VALIDATION" and row["v3_grade"] == grade
        ]
        blind_candidates.extend(choose_group_diverse(candidates, 20, f"blind:{grade}"))
    blind_candidates.sort(key=lambda row: stable_order(str(row["v3_image_path"]), "blind:combined"))

    review_root = output_root / "blind_review"
    review_images = review_root / "review_images"
    internal_root = review_root / "internal"
    researcher_rows: list[dict[str, object]] = []
    internal_rows: list[dict[str, object]] = []
    contact_entries: list[tuple[str, Path]] = []
    for index, row in enumerate(blind_candidates, start=1):
        blind_id = f"blind_{index:03d}"
        output_image = review_images / f"{blind_id}.jpg"
        save_blind_copy(Path(str(row["source_image_path"])), output_image)
        researcher_rows.append({"blind_id": blind_id, "researcher_label": ""})
        internal_rows.append(
            {
                "blind_id": blind_id,
                "true_v3_grade": row["v3_grade"],
                "physical_sample_id": row["physical_sample_id"],
                "v3_image_path": row["v3_image_path"],
                "research_partition": row["research_partition"],
                "sha256": row["sha256"],
            }
        )
        contact_entries.append((blind_id, output_image))

    write_csv(review_root / "researcher_labels.csv", ["blind_id", "researcher_label"], researcher_rows)
    write_csv(
        internal_root / "blind_review_key.csv",
        [
            "blind_id",
            "true_v3_grade",
            "physical_sample_id",
            "v3_image_path",
            "research_partition",
            "sha256",
        ],
        internal_rows,
    )
    make_contact_sheet(contact_entries, review_root / "blind_review_sheet.jpg", columns=5)
    (review_root / "README.md").write_text(
        """# V3 Phase 1 Blind Review

Review the images in `review_images/` or `blind_review_sheet.jpg`. The visible IDs are intentionally neutral.

Enter exactly one value beside every ID in `researcher_labels.csv`:

- `Grade 1`
- `Grade 2`
- `Uncertain`

Do not open `internal/blind_review_key.csv` before completing the review; it contains the hidden dataset labels. The 40 images were selected deterministically with seed 42 from the leakage-free VALIDATION partition only: 20 V3 Grade 1 and 20 V3 Grade 2 images, distributed across physical sample groups where possible.
""",
        encoding="utf-8",
    )

    print(json.dumps(audit_summary, indent=2))
    print(f"Wrote Phase 1 outputs to {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
