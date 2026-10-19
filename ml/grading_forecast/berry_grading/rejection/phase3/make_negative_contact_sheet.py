"""Create a review contact sheet for the fixed Phase 3 external negatives."""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[5]
MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv"
OUTPUT = ROOT / "ml/grading_forecast/berry_grading/evaluation/v3_phase3/external_negative_contact_sheet.png"


def main() -> int:
    with MANIFEST.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 80:
        raise RuntimeError(f"Expected 80 negative images, found {len(rows)}")
    cell_w, cell_h, columns = 230, 190, 8
    rows_count = (len(rows) + columns - 1) // columns
    canvas = Image.new("RGB", (cell_w * columns, cell_h * rows_count), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for index, row in enumerate(rows):
        image = Image.open(ROOT / row["local_path"]).convert("RGB")
        image.thumbnail((cell_w - 10, cell_h - 35), Image.Resampling.LANCZOS)
        x = (index % columns) * cell_w
        y = (index // columns) * cell_h
        canvas.paste(image, (x + (cell_w - image.width) // 2, y + 3))
        draw.text((x + 4, y + cell_h - 28), row["image_id"], fill="black", font=font)
        draw.text((x + 4, y + cell_h - 15), row["phase3_partition"], fill="black", font=font)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, optimize=True)
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
