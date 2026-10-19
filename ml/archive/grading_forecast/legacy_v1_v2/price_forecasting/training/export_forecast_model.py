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


def _is_v2_path(path: Path, marker: str) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return marker.lower() in normalized


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Finalize/validate forecast artifacts in models folder (no retrain).")
    parser.add_argument("--models-dir", type=Path, default=None, help="Models directory.")
    parser.add_argument("--require-v2-paths", action="store_true", help="Fail unless V2 models directory is used.")
    parser.add_argument("--dry-run", action="store_true", help="Validate artifact paths without writing export manifest.")
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    models_dir = args.models_dir or (repo_root / "ml" / "grading_forecast" / "price_forecasting" / "models")
    if args.require_v2_paths and not _is_v2_path(models_dir, "ml/grading_forecast/price_forecasting/models/v2"):
        print(f"Expected V2 models directory, got: {models_dir}")
        return 3

    required = ["forecast_model.joblib", "forecast_features.json", "forecast_metrics.json", "forecast_model_metadata.json"]
    missing = [name for name in required if not (models_dir / name).exists()]
    payload: dict[str, Any] = {
        "exported_at": _utc_now_iso(),
        "models_dir": str(models_dir),
        "artifacts": {name: str(models_dir / name) for name in required},
        "missing": missing,
        "manifest_path": str(models_dir / "forecast_export_manifest.json"),
    }
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0 if not missing else 2

    if missing:
        print(f"Missing required artifacts in {models_dir}: {missing}")
        return 2

    models_dir.mkdir(parents=True, exist_ok=True)
    out = models_dir / "forecast_export_manifest.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote manifest -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
