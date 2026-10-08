from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = ROOT / "ml/grading_forecast/evaluation/phase7/phase7_config.yaml"


def load_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def repo_path(relative: str) -> Path:
    return ROOT / relative


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_text_sha256(path: Path) -> str:
    """Hash text content with platform line endings normalized to LF.

    Git can materialize the same tracked CSV with CRLF on Windows and LF on
    Linux. Normalizing only newline bytes keeps the content check strict while
    making the frozen text artifact portable across those checkouts.
    """
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def frozen_text_matches(
    path: Path,
    *,
    raw_sha256: str,
    canonical_sha256: str,
) -> bool:
    if not path.is_file():
        return False
    return sha256(path) == raw_sha256 or canonical_text_sha256(path) == canonical_sha256
