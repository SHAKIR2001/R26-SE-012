from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def _git_sha(repo_root: Path) -> str | None:
    head = repo_root / ".git" / "HEAD"
    if not head.exists():
        return None
    try:
        ref = head.read_text(encoding="utf-8").strip()
    except Exception:
        return None
    if ref.startswith("ref:"):
        ref_path = repo_root / ".git" / ref.replace("ref:", "").strip()
        try:
            return ref_path.read_text(encoding="utf-8").strip()
        except Exception:
            return None
    return ref


def main(argv: list[str] | None = None) -> int:
    repo_root = _repo_root()
    default_keras = (
        repo_root
        / "ml"
        / "grading_forecast"
        / "berry_grading"
        / "models"
        / "v2"
        / "berry_mobilenetv2_v2_best.keras"
    )
    default_out = (
        repo_root / "mobile" / "assets" / "models" / "berry_mobilenetv2_v2_best.tflite"
    )

    parser = argparse.ArgumentParser(
        description="Export the selected berry grading Keras model to TensorFlow Lite."
    )
    parser.add_argument("--model", type=Path, default=default_keras)
    parser.add_argument("--out", type=Path, default=default_out)
    parser.add_argument(
        "--metadata-out",
        type=Path,
        default=None,
        help="Defaults beside the TFLite output as berry_mobilenetv2_v2_best_tflite_metadata.json.",
    )
    parser.add_argument("--no-optimize", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    model_path = args.model.resolve()
    out_path = args.out.resolve()
    metadata_path = args.metadata_out or out_path.with_name(f"{out_path.stem}_metadata.json")

    if args.dry_run:
        payload = {
            "mode": "dry_run",
            "keras_model_path": str(model_path),
            "keras_model_exists": model_path.exists(),
            "tflite_model_path": str(out_path),
            "metadata_path": str(metadata_path),
            "optimize": not args.no_optimize,
        }
        print(json.dumps(payload, indent=2))
        return 0

    if not model_path.is_file():
        print(f"Missing .keras model: {model_path}")
        return 2

    try:
        import tensorflow as tf
    except Exception as exc:
        print(f"TensorFlow is required for TFLite export. Error: {exc}")
        return 3

    model = tf.keras.models.load_model(model_path)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    if not args.no_optimize:
        converter.optimizations = [tf.lite.Optimize.DEFAULT]

    tflite_model = converter.convert()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(tflite_model)

    payload: dict[str, Any] = {
        "exported_at": _utc_now_iso(),
        "git_sha": _git_sha(repo_root),
        "keras_model_path": str(model_path),
        "tflite_model_path": str(out_path),
        "optimize": not args.no_optimize,
        "inputs": [{"dtype": "float32", "shape": [1, 224, 224, 3]}],
        "outputs": [{"dtype": "float32", "shape": [1, 3]}],
        "classes": ["Grade 1", "Grade 2", "Grade 3"],
        "preprocessing": "RGB float32 pixels in the 0..255 range; MobileNetV2 preprocessing is inside the model.",
    }
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    model_meta_path = model_path.parent / "berry_model_metadata.json"
    if model_meta_path.exists():
        try:
            model_meta = json.loads(model_meta_path.read_text(encoding="utf-8"))
            export_flags = model_meta.get("export_formats_present") or {}
            export_flags["tflite"] = True
            model_meta["export_formats_present"] = export_flags
            model_meta_path.write_text(json.dumps(model_meta, indent=2), encoding="utf-8")
        except Exception:
            pass

    print(f"Wrote TFLite -> {out_path}")
    print(f"Wrote metadata -> {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
