from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _iter_image_files(root: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    if not root.exists():
        return []
    return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts]


def _resize_with_letterbox(img: Image.Image, size: tuple[int, int] = (224, 224), fill: tuple[int, int, int] = (0, 0, 0)) -> Image.Image:
    target_w, target_h = size
    img = img.convert("RGB")
    w, h = img.size
    if w <= 0 or h <= 0:
        raise ValueError("Invalid image dimensions.")

    scale = min(target_w / w, target_h / h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    resized = img.resize((new_w, new_h), resample=Image.BILINEAR)

    canvas = Image.new("RGB", (target_w, target_h), fill)
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y))
    return canvas


def prepare_images(
    raw_root: Path,
    processed_root: Path,
    summary_json: Path,
    *,
    size: tuple[int, int] = (224, 224),
) -> dict:
    files = _iter_image_files(raw_root)
    processed_root.mkdir(parents=True, exist_ok=True)

    processed = 0
    failed = 0
    per_grade = Counter()
    failures: list[dict] = []

    pixel_means: list[np.ndarray] = []
    pixel_stds: list[np.ndarray] = []

    for src in files:
        try:
            rel = src.relative_to(raw_root)
        except ValueError:
            rel = Path(src.name)

        grade_folder = rel.parts[0] if rel.parts else ""
        if grade_folder in {"grade_1", "grade_2", "grade_3"}:
            per_grade[grade_folder] += 1

        dst = processed_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(src) as img:
                out_img = _resize_with_letterbox(img, size=size)

                # "Normalize pixel values" for training: compute per-image mean/std in [0, 1] space.
                arr = np.asarray(out_img, dtype=np.float32) / 255.0
                pixel_means.append(arr.mean(axis=(0, 1)))
                pixel_stds.append(arr.std(axis=(0, 1)))

                out_img.save(dst, format="JPEG", quality=95, optimize=True)
            processed += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            if len(failures) < 25:
                failures.append({"path": str(src), "error": str(exc)})

    mean_rgb = np.mean(pixel_means, axis=0).tolist() if pixel_means else None
    std_rgb = np.mean(pixel_stds, axis=0).tolist() if pixel_stds else None

    summary = {
        "raw_root": str(raw_root),
        "processed_root": str(processed_root),
        "target_size": list(size),
        "total_found": len(files),
        "processed": processed,
        "failed": failed,
        "images_per_grade_folder": dict(per_grade),
        "dataset_mean_rgb_0_1": mean_rgb,
        "dataset_std_rgb_0_1": std_rgb,
        "failure_examples": failures,
    }

    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare resized (224x224) berry images for training.")
    parser.add_argument("--raw", type=Path, default=None, help="Raw images root folder.")
    parser.add_argument("--out-dir", type=Path, default=None, help="Processed output root folder.")
    parser.add_argument("--summary", type=Path, default=None, help="Output summary JSON path.")
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    raw_root = args.raw or (repo_root / "data" / "raw" / "berry_images")
    out_dir = args.out_dir or (repo_root / "data" / "processed" / "grading_forecast" / "berry_images_processed")
    summary_json = args.summary or (repo_root / "data" / "processed" / "grading_forecast" / "berry_preprocessing_summary.json")

    if not raw_root.exists():
        print(f"Missing raw image folder: {raw_root}")
        return 2

    try:
        summary = prepare_images(raw_root=raw_root, processed_root=out_dir, summary_json=summary_json)
    except Exception as exc:  # noqa: BLE001
        print(f"Preprocessing failed: {exc}")
        return 1

    print(f"Wrote: {summary_json}")
    print(f"Processed: {summary['processed']} | Failed: {summary['failed']} | Out: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

