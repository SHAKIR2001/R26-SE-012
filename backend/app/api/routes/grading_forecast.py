from __future__ import annotations

import io
import logging
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.schemas.grading_forecast import Phase7AnalyzeResponse
from app.services.grading_forecast.phase7_service import (
    ForecastRecordError,
    GradingRuntimeError,
    analyze as analyze_phase7,
    initialize_phase7_runtime,
)

router = APIRouter(prefix="/api/v1/grading-forecast", tags=["grading-forecast"])
LOGGER = logging.getLogger(__name__)
MAX_IMAGE_UPLOAD_BYTES = 10 * 1024 * 1024
SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


async def _read_valid_image_upload(image: UploadFile | None) -> tuple[bytes, str]:
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image upload is required.",
        )

    image_name = image.filename or "uploaded_image"
    try:
        image_bytes = await image.read()
    except Exception as exc:
        LOGGER.warning("Failed to read uploaded image: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image upload could not be read.",
        ) from exc

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image upload is empty.",
        )

    if len(image_bytes) > MAX_IMAGE_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image upload exceeds the 10 MB limit.",
        )

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.verify()
            if str(img.format).upper() not in SUPPORTED_IMAGE_FORMATS:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Unsupported image format. Use JPEG, PNG, or WEBP.",
                )
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        LOGGER.warning("Invalid uploaded image: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image is invalid or unreadable.",
        ) from exc

    return image_bytes, image_name


def _safe_analysis(image_bytes: bytes, analysis_id: str) -> dict:
    try:
        return analyze_phase7(image_bytes, analysis_id)
    except (GradingRuntimeError, ForecastRecordError) as exc:
        LOGGER.warning("Phase 7 runtime failed safely: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Frozen grading runtime is unavailable or failed safely.",
        ) from exc
    except Exception as exc:
        LOGGER.exception("Unexpected berry grading failure.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integrated analysis failed unexpectedly.",
        ) from exc


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "component": "phase7_grade_price_decision_support",
    }


@router.get("/ready")
def ready() -> dict[str, object]:
    try:
        initialize_phase7_runtime()
        readiness = "ready"
    except (GradingRuntimeError, ForecastRecordError):
        readiness = "not_ready"
    return {
        "status": readiness,
        "component": "phase7_grade_price_decision_support",
        "runtime": "backend_onnx_runtime",
        "price_strategy": "frozen_phase5_forecast_records",
    }


@router.post("/analyze", response_model=Phase7AnalyzeResponse)
async def analyze(image: UploadFile | None = None) -> Phase7AnalyzeResponse:
    image_bytes, _ = await _read_valid_image_upload(image)
    analysis_id = str(uuid.uuid4())
    result = _safe_analysis(image_bytes, analysis_id)
    LOGGER.info("phase7_analysis id=%s category=%s", analysis_id, result["decision_support"]["category"])
    return Phase7AnalyzeResponse.model_validate(result)


@router.api_route("/grade-only", methods=["POST"], status_code=status.HTTP_410_GONE)
@router.api_route("/price-forecast", methods=["GET"], status_code=status.HTTP_410_GONE)
@router.api_route("/recommend", methods=["POST"], status_code=status.HTTP_410_GONE)
def retired_legacy_endpoint() -> dict[str, str]:
    return {"detail": "Retired in Phase 7; use POST /api/v1/grading-forecast/analyze."}
