from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def _maybe_enable_determinism() -> None:
    # Best-effort determinism. Not all TF ops are deterministic on all platforms.
    os.environ.setdefault("PYTHONHASHSEED", "42")
    os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")


def _set_seeds(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except Exception:
        pass

    try:
        import tensorflow as tf

        tf.keras.utils.set_random_seed(seed)
    except Exception:
        pass


def _iter_image_files(root: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    if not root.exists():
        return []
    return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts]


def _count_per_class(root: Path, class_names: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in class_names:
        counts[c] = len(_iter_image_files(root / c))
    return counts


def _validate_class_dirs(root: Path, class_names: list[str], *, label: str) -> None:
    missing = [c for c in class_names if not (root / c).is_dir()]
    if missing:
        raise ValueError(f"{label} is missing class directories: {missing}. Root: {root}")
    empty = [c for c in class_names if not _iter_image_files(root / c)]
    if empty:
        raise ValueError(f"{label} has empty class directories: {empty}. Root: {root}")


def _ensure_stratified_split_dir(
    dataset_root: Path,
    split_root: Path,
    *,
    class_names: list[str],
    val_ratio: float,
    seed: int,
    tolerance: int = 1,
) -> tuple[Path, Path] | None:
    """
    Ensure a deterministic, stratified directory split exists.

    Returns (train_dir, val_dir) when a split is created/used, otherwise None.
    """
    if not dataset_root.exists():
        return None

    train_dir = split_root / "train"
    val_dir = split_root / "val"
    marker = split_root / "_SPLIT_COMPLETE.json"
    if marker.exists() and train_dir.exists() and val_dir.exists():
        return train_dir, val_dir

    per_class_files: dict[str, list[Path]] = {}
    for c in class_names:
        files = _iter_image_files(dataset_root / c)
        if not files:
            return None
        per_class_files[c] = sorted(files)

    rng = random.Random(seed)
    split_plan: dict[str, dict[str, int]] = {}
    for c, files in per_class_files.items():
        idxs = list(range(len(files)))
        rng.shuffle(idxs)
        val_count = int(round(len(files) * val_ratio))
        val_count = max(1, min(val_count, len(files) - 1))
        split_plan[c] = {"total": len(files), "val": val_count, "train": len(files) - val_count}

    # Validate balance: expects near-perfect balance given current dataset (360 / 120 each).
    # This is a safeguard: only used when original split is not balanced within tolerance.
    expected_val = None
    for c in class_names:
        if expected_val is None:
            expected_val = split_plan[c]["val"]
        else:
            if abs(split_plan[c]["val"] - expected_val) > tolerance:
                # If some class is too different, prefer deterministic floor-based split.
                split_plan[c]["val"] = max(1, int(len(per_class_files[c]) * val_ratio))
                split_plan[c]["train"] = len(per_class_files[c]) - split_plan[c]["val"]

    # Create/copy.
    for base in (train_dir, val_dir):
        (base).mkdir(parents=True, exist_ok=True)
        for c in class_names:
            (base / c).mkdir(parents=True, exist_ok=True)

    for c, files in per_class_files.items():
        idxs = list(range(len(files)))
        rng.shuffle(idxs)
        val_n = split_plan[c]["val"]
        val_idxs = set(idxs[:val_n])

        for i, src in enumerate(files):
            rel_name = src.name
            dst = (val_dir / c / rel_name) if i in val_idxs else (train_dir / c / rel_name)
            if dst.exists():
                continue
            dst.write_bytes(src.read_bytes())

    marker.write_text(
        json.dumps(
            {
                "created_at": _utc_now_iso(),
                "seed": seed,
                "val_ratio": val_ratio,
                "class_names": class_names,
                "plan": split_plan,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return train_dir, val_dir


def _dataset_label_counts(ds) -> dict[int, int]:
    import numpy as np

    counts: dict[int, int] = {}
    for _, y in ds:
        y_np = np.asarray(y)
        for cls in y_np.reshape(-1).tolist():
            counts[int(cls)] = counts.get(int(cls), 0) + 1
    return counts


def _compute_class_weight_from_counts(counts: dict[int, int]) -> dict[int, float]:
    total = sum(counts.values())
    if total <= 0:
        return {}
    num_classes = len(counts) if counts else 0
    if num_classes == 0:
        return {}
    weights: dict[int, float] = {}
    for cls, n in counts.items():
        # Inverse-frequency weighting.
        weights[int(cls)] = float(total) / float(num_classes * max(1, n))
    return weights


@dataclass(frozen=True)
class StageConfig:
    name: str
    epochs: int
    learning_rate: float
    patience: int


def _build_model(*, num_classes: int, dropout: float):
    import tensorflow as tf

    base = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    inputs = tf.keras.Input(shape=(224, 224, 3), dtype=tf.float32, name="image")
    x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(dropout)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="probs")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="berry_mobilenetv2")
    return model, base


def _augmentation_layers(*, seed: int):
    import tensorflow as tf

    return tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal", seed=seed),
            tf.keras.layers.RandomRotation(0.06, seed=seed),
            tf.keras.layers.RandomZoom(0.10, seed=seed),
            tf.keras.layers.RandomBrightness(factor=0.12, value_range=(0.0, 255.0), seed=seed),
        ],
        name="light_augmentation",
    )


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
    _maybe_enable_determinism()

    parser = argparse.ArgumentParser(description="Train MobileNetV2 berry grading classifier (Grade 1/2/3).")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Legacy dataset root with class subfolders; uses Keras validation_split unless --train-dir/--val-dir are provided.",
    )
    parser.add_argument(
        "--train-dir",
        type=Path,
        default=None,
        help="Explicit training directory with grade_1/grade_2/grade_3 subfolders. Use for V2.",
    )
    parser.add_argument(
        "--val-dir",
        type=Path,
        default=None,
        help="Explicit validation directory with grade_1/grade_2/grade_3 subfolders. Use for V2.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for model artifacts. Use models/v2 for V2 to avoid overwriting V1.",
    )
    parser.add_argument(
        "--model-filename",
        type=str,
        default="berry_mobilenetv2_best.keras",
        help="Keras model filename inside output directory.",
    )
    parser.add_argument(
        "--metadata-version",
        type=str,
        default="v1",
        help="Dataset/model version recorded in metadata.",
    )
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size.")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed.")
    parser.add_argument("--val-split", type=float, default=0.2, help="Validation split ratio.")
    parser.add_argument("--dropout", type=float, default=0.25, help="Dropout rate.")
    parser.add_argument("--stage1-epochs", type=int, default=25, help="Stage 1 epochs (frozen backbone).")
    parser.add_argument("--stage2-epochs", type=int, default=8, help="Stage 2 epochs (fine-tune).")
    parser.add_argument("--stage1-lr", type=float, default=1e-3, help="Stage 1 learning rate.")
    parser.add_argument("--stage2-lr", type=float, default=1e-5, help="Stage 2 learning rate.")
    parser.add_argument("--patience", type=int, default=6, help="Early stopping patience.")
    parser.add_argument(
        "--force-stratified-dir-split",
        action="store_true",
        help="Always create and use a deterministic stratified directory split.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate paths and print resolved configuration without importing TensorFlow or training.",
    )
    args = parser.parse_args(argv)

    _set_seeds(args.seed)

    repo_root = _repo_root()
    if (args.train_dir is None) != (args.val_dir is None):
        print("Both --train-dir and --val-dir must be provided together.")
        return 2

    explicit_split = args.train_dir is not None and args.val_dir is not None
    data_dir = args.data_dir or (
        repo_root / "data" / "processed" / "grading_forecast" / "berry_images_processed"
    )
    train_dir_arg = args.train_dir
    val_dir_arg = args.val_dir

    if explicit_split:
        assert train_dir_arg is not None and val_dir_arg is not None
        if not train_dir_arg.exists():
            print(f"Missing training directory: {train_dir_arg}")
            return 2
        if not val_dir_arg.exists():
            print(f"Missing validation directory: {val_dir_arg}")
            return 2
    elif not data_dir.exists():
        print(f"Missing dataset directory: {data_dir}")
        return 2

    models_dir = args.output_dir or (repo_root / "ml" / "grading_forecast" / "berry_grading" / "models")

    class_names = ["grade_1", "grade_2", "grade_3"]
    if explicit_split:
        _validate_class_dirs(train_dir_arg, class_names, label="--train-dir")
        _validate_class_dirs(val_dir_arg, class_names, label="--val-dir")
    else:
        _validate_class_dirs(data_dir, class_names, label="--data-dir")

    best_path = models_dir / args.model_filename
    history_path = models_dir / "training_history.json"
    meta_path = models_dir / "berry_model_metadata.json"

    if args.dry_run:
        payload = {
            "mode": "dry_run",
            "explicit_split": bool(explicit_split),
            "dataset_dir": None if explicit_split else str(data_dir),
            "legacy_data_dir": str(data_dir) if explicit_split else None,
            "train_dir": str(train_dir_arg) if train_dir_arg is not None else None,
            "val_dir": str(val_dir_arg) if val_dir_arg is not None else None,
            "output_dir": str(models_dir),
            "model_path": str(best_path),
            "history_path": str(history_path),
            "metadata_path": str(meta_path),
            "metadata_version": str(args.metadata_version),
            "class_dirs": class_names,
            "train_counts": _count_per_class(train_dir_arg, class_names) if train_dir_arg is not None else None,
            "val_counts": _count_per_class(val_dir_arg, class_names) if val_dir_arg is not None else None,
            "uses_v1_default_data_dir": not explicit_split and data_dir.name == "berry_images_processed",
        }
        print(json.dumps(payload, indent=2))
        return 0

    models_dir.mkdir(parents=True, exist_ok=True)
    class_names_path = models_dir / "class_names.json"
    class_names_path.write_text(json.dumps([c.replace("_", " ").title() for c in class_names], indent=2), encoding="utf-8")

    # Create initial split using the required Keras API.
    import tensorflow as tf

    if explicit_split:
        assert train_dir_arg is not None and val_dir_arg is not None
        train_ds = tf.keras.utils.image_dataset_from_directory(
            train_dir_arg,
            labels="inferred",
            label_mode="int",
            class_names=class_names,
            image_size=(224, 224),
            batch_size=args.batch_size,
            shuffle=True,
            seed=args.seed,
        )
        val_ds = tf.keras.utils.image_dataset_from_directory(
            val_dir_arg,
            labels="inferred",
            label_mode="int",
            class_names=class_names,
            image_size=(224, 224),
            batch_size=args.batch_size,
            shuffle=False,
        )
    else:
        train_ds = tf.keras.utils.image_dataset_from_directory(
            data_dir,
            labels="inferred",
            label_mode="int",
            class_names=class_names,
            image_size=(224, 224),
            batch_size=args.batch_size,
            shuffle=True,
            seed=args.seed,
            validation_split=args.val_split,
            subset="training",
        )
        val_ds = tf.keras.utils.image_dataset_from_directory(
            data_dir,
            labels="inferred",
            label_mode="int",
            class_names=class_names,
            image_size=(224, 224),
            batch_size=args.batch_size,
            shuffle=False,
            seed=args.seed,
            validation_split=args.val_split,
            subset="validation",
        )

    # Compute label distribution; if it drifts, enforce stratified directory split.
    train_counts = _dataset_label_counts(train_ds)
    val_counts = _dataset_label_counts(val_ds)

    def _balanced_enough(counts: dict[int, int], tol: int = 1) -> bool:
        if not counts:
            return False
        values = list(counts.values())
        return (max(values) - min(values)) <= tol

    use_dir_split = (not explicit_split) and (
        bool(args.force_stratified_dir_split) or not (_balanced_enough(train_counts) and _balanced_enough(val_counts))
    )
    split_dir_used: dict[str, str] | None = None
    if use_dir_split:
        split_root = repo_root / "data" / "processed" / "grading_forecast" / "_berry_split_v1"
        out = _ensure_stratified_split_dir(
            dataset_root=data_dir,
            split_root=split_root,
            class_names=class_names,
            val_ratio=args.val_split,
            seed=args.seed,
            tolerance=1,
        )
        if out is not None:
            train_dir, val_dir = out
            split_dir_used = {"train": str(train_dir), "val": str(val_dir)}
            train_ds = tf.keras.utils.image_dataset_from_directory(
                train_dir,
                labels="inferred",
                label_mode="int",
                class_names=class_names,
                image_size=(224, 224),
                batch_size=args.batch_size,
                shuffle=True,
                seed=args.seed,
            )
            val_ds = tf.keras.utils.image_dataset_from_directory(
                val_dir,
                labels="inferred",
                label_mode="int",
                class_names=class_names,
                image_size=(224, 224),
                batch_size=args.batch_size,
                shuffle=False,
            )
            train_counts = _dataset_label_counts(train_ds)
            val_counts = _dataset_label_counts(val_ds)

    # Cache/prefetch; apply augmentation to training only.
    aug = _augmentation_layers(seed=args.seed)

    def _with_aug(ds):
        return ds.map(lambda x, y: (aug(x, training=True), y), num_parallel_calls=tf.data.AUTOTUNE)

    train_ds = _with_aug(train_ds).cache().prefetch(tf.data.AUTOTUNE)
    val_ds = val_ds.cache().prefetch(tf.data.AUTOTUNE)

    class_weight = _compute_class_weight_from_counts(train_counts)

    model, backbone = _build_model(num_classes=len(class_names), dropout=args.dropout)

    stage1 = StageConfig(name="stage1_frozen", epochs=args.stage1_epochs, learning_rate=args.stage1_lr, patience=args.patience)
    stage2 = StageConfig(name="stage2_finetune", epochs=args.stage2_epochs, learning_rate=args.stage2_lr, patience=max(2, args.patience // 2))

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=stage1.patience, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=max(2, stage1.patience // 2)),
        tf.keras.callbacks.ModelCheckpoint(filepath=str(best_path), monitor="val_loss", save_best_only=True),
    ]

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=stage1.learning_rate),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy")],
    )
    hist_all: dict[str, Any] = {"stages": []}

    print(f"Training stage 1 (frozen backbone) -> epochs={stage1.epochs}")
    h1 = model.fit(train_ds, validation_data=val_ds, epochs=stage1.epochs, class_weight=class_weight, callbacks=callbacks)
    hist_all["stages"].append({"config": asdict(stage1), "history": {k: list(v) for k, v in h1.history.items()}})

    # Stage 2: fine-tune last ~20 layers.
    for layer in backbone.layers[:-20]:
        layer.trainable = False
    for layer in backbone.layers[-20:]:
        layer.trainable = True

    callbacks2 = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=stage2.patience, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=max(1, stage2.patience // 2)),
        tf.keras.callbacks.ModelCheckpoint(filepath=str(best_path), monitor="val_loss", save_best_only=True),
    ]
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=stage2.learning_rate),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy")],
    )
    print(f"Training stage 2 (fine-tune top layers) -> epochs={stage2.epochs}")
    h2 = model.fit(train_ds, validation_data=val_ds, epochs=stage2.epochs, class_weight=class_weight, callbacks=callbacks2)
    hist_all["stages"].append({"config": asdict(stage2), "history": {k: list(v) for k, v in h2.history.items()}})

    history_path.write_text(json.dumps(hist_all, indent=2), encoding="utf-8")

    # Model metadata (versioning + reproducibility).
    meta: dict[str, Any] = {
        "model_name": "berry_mobilenetv2",
        "version": str(args.metadata_version),
        "trained_at": _utc_now_iso(),
        "seed": int(args.seed),
        "image_size": [224, 224],
        "classes": json.loads(class_names_path.read_text(encoding="utf-8")),
        "dataset_dir": None if explicit_split else str(data_dir),
        "split": {
            "strategy": "explicit_train_val_directories" if explicit_split else "keras_validation_split_or_v1_dir_split",
            "train_dir": str(train_dir_arg) if train_dir_arg is not None else None,
            "val_dir": str(val_dir_arg) if val_dir_arg is not None else None,
            "val_ratio": None if explicit_split else float(args.val_split),
            "train_counts": {str(k): int(v) for k, v in train_counts.items()},
            "val_counts": {str(k): int(v) for k, v in val_counts.items()},
            "dir_split_used": split_dir_used,
        },
        "augmentation": {
            "flip": True,
            "rotation": 0.06,
            "zoom": 0.10,
            "brightness_factor": 0.12,
        },
        "stage1": asdict(stage1),
        "stage2": asdict(stage2),
        "export_formats_present": {"keras": best_path.exists(), "onnx": False, "tflite": False},
        "git_sha": _git_sha(repo_root),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Wrote: {best_path}")
    print(f"Wrote: {history_path}")
    print(f"Wrote: {meta_path}")
    print(f"Class weight: {json.dumps({str(k): round(v, 4) for k, v in class_weight.items()}, indent=2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
