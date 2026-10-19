from __future__ import annotations

import json
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main() -> int:
    repo_root = _repo_root()
    out_path = (
        repo_root
        / "ml"
        / "grading_forecast"
        / "price_forecasting"
        / "training"
        / "baseline_config.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "model": "moving_average_baseline",
        "window": 3,
        "note": "Baseline config only (no ARIMA/LSTM training).",
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote baseline config -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
