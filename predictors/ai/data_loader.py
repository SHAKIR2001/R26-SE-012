from __future__ import annotations

import io
import os

from PIL import Image

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    _HEIC_SUPPORT = True
except ImportError:
    _HEIC_SUPPORT = False

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}

# Lambdas for file discovery and conversion
_is_supported  = lambda f: os.path.splitext(f)[1].lower() in SUPPORTED
_list_images   = lambda folder: sorted(f for f in os.listdir(folder) if _is_supported(f))
_full_path     = lambda folder, fname: os.path.join(folder, fname)
_to_jpeg_bytes = lambda img: _encode(img)


def _encode(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def load_class_references(folder: str) -> list[bytes]:
    """Load all supported images from a class folder, return as JPEG bytes."""
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Reference folder not found: {folder}")

    filenames = _list_images(folder)
    if not filenames:
        raise FileNotFoundError(f"No supported images found in: {folder}")

    return [_to_jpeg_bytes(Image.open(_full_path(folder, f))) for f in filenames]


def load_all_references(data_map: dict[str, str]) -> dict[str, list[bytes]]:
    """Load reference images for all classes. Returns {class_label: [jpeg_bytes]}."""
    return {cls: load_class_references(folder) for cls, folder in data_map.items()}
