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
        clean_price_csv,
        evaluate_one_step_ahead_metrics,
        select_input_csv_path,
    )

    input_csv = select_input_csv_path(repo_root=repo_root)
    if input_csv is None:
        print("No input CSV found; metrics are unavailable.")
        return 2

    output_csv = repo_root / "data" / "processed" / "grading_forecast" / "cleaned_price_data.csv"
    points = clean_price_csv(input_csv, output_csv_path=output_csv)
    metrics = evaluate_one_step_ahead_metrics(points)

    out_path = (
        repo_root
        / "ml"
        / "grading_forecast"
        / "price_forecasting"
        / "evaluation"
        / "forecast_metrics.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = metrics.model_dump()
    if payload["mae"] is None or payload["rmse"] is None:
        payload["message"] = "Not enough data for reliable evaluation"

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote metrics -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
