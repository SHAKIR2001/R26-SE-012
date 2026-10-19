"""Generate a small, deterministic input-gradient saliency audit for frozen V2.

This is a diagnostic only. It does not train or modify the historical V2 model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


CLASS_DIRS = {"grade_1": "Grade 1", "grade_2": "Grade 2", "grade_3": "Grade 3"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def _stable_order(path: Path) -> str:
    return hashlib.sha256(path.as_posix().encode("utf-8")).hexdigest()


def _load_image(path: Path, size: tuple[int, int] = (224, 224)) -> tuple[Image.Image, np.ndarray]:
    with Image.open(path) as source:
        display = ImageOps.exif_transpose(source).convert("RGB")
    resized = display.resize(size, Image.Resampling.BILINEAR)
    return display, np.asarray(resized, dtype=np.float32)


def _saliency_overlay(display: Image.Image, saliency: np.ndarray) -> Image.Image:
    saliency = np.maximum(saliency, 0.0)
    scale = float(np.percentile(saliency, 99.0))
    if scale <= 0.0:
        scale = float(saliency.max()) or 1.0
    norm = np.clip(saliency / scale, 0.0, 1.0)
    heat = np.zeros((*norm.shape, 3), dtype=np.uint8)
    heat[..., 0] = (255 * norm).astype(np.uint8)
    heat[..., 1] = (160 * np.sqrt(norm)).astype(np.uint8)
    heat_image = Image.fromarray(heat, mode="RGB").resize(display.size, Image.Resampling.BILINEAR)
    alpha = Image.fromarray((180 * norm).astype(np.uint8), mode="L").resize(
        display.size, Image.Resampling.BILINEAR
    )
    return Image.composite(Image.blend(display, heat_image, 0.65), display, alpha)


def _fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.pad(image, size, method=Image.Resampling.LANCZOS, color="white")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--test-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    import tensorflow as tf

    class_names = ["Grade 1", "Grade 2", "Grade 3"]
    model = tf.keras.models.load_model(args.model, compile=False)

    candidates: list[dict[str, object]] = []
    for class_index, (class_dir, true_label) in enumerate(CLASS_DIRS.items()):
        paths = sorted(
            (p for p in (args.test_dir / class_dir).rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES),
            key=_stable_order,
        )
        for path in paths:
            _, array = _load_image(path)
            probabilities = model(np.expand_dims(array, axis=0), training=False).numpy()[0]
            predicted_index = int(np.argmax(probabilities))
            candidates.append(
                {
                    "path": path,
                    "true_index": class_index,
                    "true_label": true_label,
                    "predicted_index": predicted_index,
                    "predicted_label": class_names[predicted_index],
                    "confidence": float(probabilities[predicted_index]),
                    "correct": predicted_index == class_index,
                }
            )

    selected: list[dict[str, object]] = []
    for class_index in range(3):
        by_class = [c for c in candidates if c["true_index"] == class_index]
        correct = [c for c in by_class if c["correct"]]
        incorrect = [c for c in by_class if not c["correct"]]
        # One correct and two incorrect examples per historical class, chosen by
        # stable hash order. All three V2 classes contain at least two errors.
        selected.extend(correct[:1])
        selected.extend(incorrect[:2])

    if len(selected) != 9:
        raise RuntimeError(f"Expected 9 diagnostic examples; selected {len(selected)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    panels: list[Image.Image] = []
    font = ImageFont.load_default()
    for index, item in enumerate(selected, start=1):
        path = item["path"]
        display, array = _load_image(path)
        tensor = tf.convert_to_tensor(np.expand_dims(array, axis=0))
        with tf.GradientTape() as tape:
            tape.watch(tensor)
            predictions = model(tensor, training=False)
            score = predictions[0, int(item["predicted_index"])]
        gradient = tape.gradient(score, tensor)[0]
        saliency = tf.reduce_max(tf.abs(gradient), axis=-1).numpy()
        overlay = _saliency_overlay(display, saliency)

        diagnostic_id = f"v2_saliency_{index:02d}"
        left = _fit(display, (360, 270))
        right = _fit(overlay, (360, 270))
        panel = Image.new("RGB", (720, 306), "white")
        panel.paste(left, (0, 36))
        panel.paste(right, (360, 36))
        caption = (
            f"{diagnostic_id} | true: {item['true_label']} | pred: {item['predicted_label']} "
            f"({float(item['confidence']):.3f}) | {'correct' if item['correct'] else 'incorrect'}"
        )
        ImageDraw.Draw(panel).text((8, 11), caption, fill="black", font=font)
        panel.save(args.output_dir / f"{diagnostic_id}.jpg", quality=92)
        panels.append(panel)
        rows.append(
            {
                "diagnostic_id": diagnostic_id,
                "image": path.relative_to(args.test_dir).as_posix(),
                "true_label": item["true_label"],
                "v2_prediction": item["predicted_label"],
                "confidence": f"{float(item['confidence']):.6f}",
                "correct": str(bool(item["correct"])).lower(),
                "attention_classification": "",
                "qualitative_observation": "",
            }
        )

    sheet = Image.new("RGB", (720, len(panels) * 306), "white")
    for index, panel in enumerate(panels):
        sheet.paste(panel, (0, index * 306))
    sheet.save(args.output_dir / "v2_saliency_contact_sheet.jpg", quality=94)

    with (args.output_dir / "v2_saliency_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Screened {len(candidates)} historical V2 test images")
    print(f"Generated {len(rows)} saliency examples in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
