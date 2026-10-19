from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def _safe_float(x: object) -> float | None:
    try:
        return float(x)  # type: ignore[arg-type]
    except Exception:
        return None


def _load_class_names(models_dir: Path) -> list[str]:
    p = models_dir / "class_names.json"
    if not p.exists():
        return ["Grade 1", "Grade 2", "Grade 3"]
    return list(json.loads(p.read_text(encoding="utf-8")))


def _load_val_dir_from_metadata(models_dir: Path) -> Path | None:
    """
    If training used a deterministic directory split, reuse its validation directory for evaluation.
    """
    meta_path = models_dir / "berry_model_metadata.json"
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        split = meta.get("split") or {}
        used = split.get("dir_split_used") or None
        if not isinstance(used, dict):
            return None
        val = used.get("val")
        if not val:
            return None
        p = Path(str(val))
        return p if p.exists() else None
    except Exception:
        return None


def _iter_image_files(root: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    if not root.exists():
        return []
    return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts]


def _validate_class_dirs(root: Path, class_names: list[str], *, label: str) -> None:
    missing = [c for c in class_names if not (root / c).is_dir()]
    if missing:
        raise ValueError(f"{label} is missing class directories: {missing}. Root: {root}")
    empty = [c for c in class_names if not _iter_image_files(root / c)]
    if empty:
        raise ValueError(f"{label} has empty class directories: {empty}. Root: {root}")


def _model_size_mb(path: Path) -> float | None:
    try:
        return round(path.stat().st_size / (1024.0 * 1024.0), 3)
    except Exception:
        return None


def _memory_rss_bytes() -> int | None:
    try:
        import psutil

        return int(psutil.Process(os.getpid()).memory_info().rss)
    except Exception:
        return None


def _letterbox_pil(img, *, size: tuple[int, int] = (224, 224)):
    from PIL import Image

    target_w, target_h = size
    img = img.convert("RGB")
    w, h = img.size
    scale = min(target_w / w, target_h / h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    resized = img.resize((new_w, new_h), resample=Image.BILINEAR)
    canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
    canvas.paste(resized, ((target_w - new_w) // 2, (target_h - new_h) // 2))
    return canvas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate berry classifier and write metrics JSON + plots.")
    parser.add_argument("--data-dir", type=Path, default=None, help="Dataset root with grade_1/grade_2/grade_3 subfolders.")
    parser.add_argument("--model", type=Path, default=None, help="Path to .keras model.")
    parser.add_argument("--models-dir", type=Path, default=None, help="Directory containing class_names.json and output metrics.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for evaluation plots.")
    parser.add_argument(
        "--use-full-data-dir",
        action="store_true",
        help="Evaluate every image under --data-dir. Use this for the V2 test split.",
    )
    parser.add_argument("--split-name", type=str, default="validation", help="Split name recorded in metrics.")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size.")
    parser.add_argument("--seed", type=int, default=42, help="Seed.")
    parser.add_argument("--val-split", type=float, default=0.2, help="Validation split ratio.")
    parser.add_argument("--runs", type=int, default=80, help="Inference timing runs (after warmup).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate paths and print resolved configuration without importing TensorFlow or evaluating.",
    )
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    data_dir = args.data_dir or (
        repo_root / "data" / "processed" / "grading_forecast" / "berry_images_processed"
    )

    default_models_dir = repo_root / "ml" / "grading_forecast" / "berry_grading" / "models"
    model_path = args.model or (default_models_dir / "berry_mobilenetv2_best.keras")
    models_dir = args.models_dir or model_path.parent
    eval_out = args.output_dir or (repo_root / "ml" / "grading_forecast" / "berry_grading" / "evaluation" / "_outputs")

    class_names_dir = ["grade_1", "grade_2", "grade_3"]
    val_dir_override = _load_val_dir_from_metadata(models_dir)
    eval_data_dir = data_dir if args.use_full_data_dir or val_dir_override is None else val_dir_override
    try:
        _validate_class_dirs(eval_data_dir, class_names_dir, label="evaluation data")
    except ValueError as exc:
        print(str(exc))
        return 3

    metrics_path = models_dir / "berry_classifier_metrics.json"
    cm_path = eval_out / "confusion_matrix.png"
    curves_path = eval_out / "training_curves.png"

    if args.dry_run:
        payload = {
            "mode": "dry_run",
            "model_path": str(model_path),
            "model_exists": model_path.exists(),
            "models_dir": str(models_dir),
            "class_names_path": str(models_dir / "class_names.json"),
            "data_dir": str(data_dir),
            "evaluation_data_dir": str(eval_data_dir),
            "split_name": str(args.split_name),
            "use_full_data_dir": bool(args.use_full_data_dir),
            "metrics_path": str(metrics_path),
            "confusion_matrix_path": str(cm_path),
            "training_curves_path": str(curves_path),
            "class_dirs": class_names_dir,
        }
        print(json.dumps(payload, indent=2))
        return 0

    eval_out.mkdir(parents=True, exist_ok=True)

    if not model_path.exists():
        print(f"Missing trained model: {model_path}")
        return 2

    class_names = _load_class_names(models_dir)

    import matplotlib.pyplot as plt
    import numpy as np
    import tensorflow as tf
    from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support

    if args.use_full_data_dir:
        val_ds = tf.keras.utils.image_dataset_from_directory(
            data_dir,
            labels="inferred",
            label_mode="int",
            class_names=class_names_dir,
            image_size=(224, 224),
            batch_size=args.batch_size,
            shuffle=False,
        )
    elif val_dir_override is not None:
        val_ds = tf.keras.utils.image_dataset_from_directory(
            val_dir_override,
            labels="inferred",
            label_mode="int",
            class_names=class_names_dir,
            image_size=(224, 224),
            batch_size=args.batch_size,
            shuffle=False,
        )
    else:
        val_ds = tf.keras.utils.image_dataset_from_directory(
            data_dir,
            labels="inferred",
            label_mode="int",
            class_names=class_names_dir,
            image_size=(224, 224),
            batch_size=args.batch_size,
            shuffle=False,
            seed=args.seed,
            validation_split=args.val_split,
            subset="validation",
        )
    val_ds = val_ds.cache().prefetch(tf.data.AUTOTUNE)

    model = tf.keras.models.load_model(model_path)

    y_true: list[int] = []
    y_pred: list[int] = []
    y_prob: list[list[float]] = []

    for x, y in val_ds:
        probs = model.predict(x, verbose=0)
        preds = np.argmax(probs, axis=1)
        y_true.extend(np.asarray(y).reshape(-1).astype(int).tolist())
        y_pred.extend(preds.reshape(-1).astype(int).tolist())
        y_prob.extend(probs.tolist())

    if not y_true:
        print("Evaluation dataset is empty; cannot evaluate.")
        return 3

    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(len(class_names))), average="weighted", zero_division=0
    )
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(len(class_names))), average="macro", zero_division=0
    )
    accuracy = float(np.mean(np.asarray(y_true) == np.asarray(y_pred)))

    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(class_names))),
        target_names=class_names,
        zero_division=0,
        output_dict=True,
    )

    # Confusion matrix plot
    fig = plt.figure(figsize=(6.4, 5.2))
    ax = fig.add_subplot(1, 1, 1)
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    fig.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(len(class_names)),
        yticks=np.arange(len(class_names)),
        xticklabels=class_names,
        yticklabels=class_names,
        ylabel="True label",
        xlabel="Predicted label",
        title="Berry Grading Confusion Matrix",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    thresh = cm.max() / 2.0 if cm.size else 0.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], "d"), ha="center", va="center", color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    fig.savefig(cm_path, dpi=140)
    plt.close(fig)

    # Training curves plot (if history exists)
    history_path = models_dir / "training_history.json"
    if history_path.exists():
        try:
            payload = json.loads(history_path.read_text(encoding="utf-8"))
            stages = payload.get("stages") or []
            losses: list[float] = []
            val_losses: list[float] = []
            accs: list[float] = []
            val_accs: list[float] = []
            for s in stages:
                h = s.get("history") or {}
                losses.extend([float(v) for v in (h.get("loss") or [])])
                val_losses.extend([float(v) for v in (h.get("val_loss") or [])])
                accs.extend([float(v) for v in (h.get("accuracy") or [])])
                val_accs.extend([float(v) for v in (h.get("val_accuracy") or [])])
            if losses and val_losses:
                fig2 = plt.figure(figsize=(8.2, 3.6))
                ax1 = fig2.add_subplot(1, 2, 1)
                ax1.plot(losses, label="train_loss")
                ax1.plot(val_losses, label="val_loss")
                ax1.set_title("Loss")
                ax1.legend()
                ax2 = fig2.add_subplot(1, 2, 2)
                if accs:
                    ax2.plot(accs, label="train_acc")
                if val_accs:
                    ax2.plot(val_accs, label="val_acc")
                ax2.set_title("Accuracy")
                ax2.legend()
                fig2.tight_layout()
                fig2.savefig(curves_path, dpi=140)
                plt.close(fig2)
        except Exception:
            pass

    # Performance metrics (Keras model)
    warm_img = None
    try:
        for batch_x, _ in val_ds.take(1):
            warm_img = batch_x[:1]
            break
    except Exception:
        warm_img = None

    timing: dict[str, Any] = {"runs": int(args.runs), "avg_ms": None, "p95_ms": None}
    rss_before = _memory_rss_bytes()
    if warm_img is not None:
        # Warmup
        for _ in range(8):
            _ = model.predict(warm_img, verbose=0)
        times: list[float] = []
        for _ in range(max(1, int(args.runs))):
            t0 = time.perf_counter()
            _ = model.predict(warm_img, verbose=0)
            times.append((time.perf_counter() - t0) * 1000.0)
        if times:
            times_sorted = sorted(times)
            timing["avg_ms"] = round(float(sum(times) / len(times)), 3)
            timing["p95_ms"] = round(float(times_sorted[int(0.95 * (len(times_sorted) - 1))]), 3)
    rss_after = _memory_rss_bytes()

    metrics: dict[str, Any] = {
        "evaluated_at": _utc_now_iso(),
        "model_path": str(model_path),
        "data_dir": str(data_dir),
        "split_name": str(args.split_name),
        "use_full_data_dir": bool(args.use_full_data_dir),
        "accuracy": round(accuracy, 4),
        "precision_macro": round(float(precision_macro), 4),
        "recall_macro": round(float(recall_macro), 4),
        "f1_macro": round(float(f1_macro), 4),
        "precision_weighted": round(float(precision_weighted), 4),
        "recall_weighted": round(float(recall_weighted), 4),
        "f1_weighted": round(float(f1_weighted), 4),
        "grade_2_recall": _safe_float((report.get("Grade 2") or {}).get("recall")),
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "artifacts": {
            "confusion_matrix_png": str(cm_path),
            "training_curves_png": str(curves_path) if curves_path.exists() else None,
        },
        "performance": {
            "inference_timing_single_image": timing,
            "model_size_mb": _model_size_mb(model_path),
            "rss_before_bytes": rss_before,
            "rss_after_bytes": rss_after,
            "rss_delta_bytes": (rss_after - rss_before) if (rss_after is not None and rss_before is not None) else None,
        },
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Wrote metrics -> {metrics_path}")
    print(f"Wrote confusion matrix -> {cm_path}")
    if curves_path.exists():
        print(f"Wrote training curves -> {curves_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
