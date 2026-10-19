from __future__ import annotations

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main() -> int:
    repo_root = _repo_root()
    backend_path = repo_root / "backend"
    sys.path.insert(0, str(backend_path))

    from app.services.grading_forecast.price_forecast_service import (  # noqa: PLC0415
        build_price_forecast,
    )

    forecast = build_price_forecast(seed_hint="cli")
    print(json.dumps(forecast.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
