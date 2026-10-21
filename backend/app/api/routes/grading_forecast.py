# =============================================================================
# File: grading and forecast API routes
# Purpose: Validates image uploads and exposes the safe Phase 7 HTTP endpoints.
# =============================================================================
from __future__ import annotations

import io
import logging
import uuid

from fastapi import APIRouter, HTTPException, Response, UploadFile, status
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from app.schemas.grading_forecast import Phase7AnalyzeResponse
from app.services.grading_forecast.phase7_service import (
    ForecastRecordError,
    GradingRuntimeError,
    analyze as analyze_phase7,
    initialize_phase7_runtime,
)

router = APIRouter(prefix="/api/v1/grading-forecast", tags=["grading-forecast"])
LOGGER = logging.getLogger(__name__)
# These limits protect the API before image decoding or model execution. They
# are validation safeguards, not changes to the frozen model preprocessing.
MAX_IMAGE_UPLOAD_BYTES = 10 * 1024 * 1024
UPLOAD_READ_CHUNK_BYTES = 1024 * 1024
MAX_DECODED_IMAGE_PIXELS = 50_000_000
MAX_IMAGE_DIMENSION = 12_000
SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


async def _read_valid_image_upload(
    image: UploadFile | None,
    analysis_id: str,
) -> tuple[bytes, str]:
    """Read and validate one bounded, single-frame image upload.

    The route verifies bytes and decoded dimensions before handing the original
    image to the frozen grading runtime. Uploaded contents and filenames are
    intentionally excluded from logs.
    """
    # Read one bounded upload and reject unsafe content before model execution.
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image upload is required.",
        )

    image_name = image.filename or "uploaded_image"
    try:
        chunks: list[bytes] = []
        total = 0
        while chunk := await image.read(UPLOAD_READ_CHUNK_BYTES):
            total += len(chunk)
            if total > MAX_IMAGE_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="Image upload exceeds the 10 MB limit.",
                )
            chunks.append(chunk)
        image_bytes = b"".join(chunks)
    except HTTPException:
        raise
    except Exception as exc:
        LOGGER.warning(
            "phase7_upload id=%s stage=read error=%s",
            analysis_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image upload could not be read.",
        ) from exc

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image upload is empty.",
        )

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            if str(img.format).upper() not in SUPPORTED_IMAGE_FORMATS:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Unsupported image format. Use JPEG, PNG, or WEBP.",
                )
            width, height = img.size
            if width <= 0 or height <= 0:
                raise ValueError("Image has invalid dimensions")
            if (
                width > MAX_IMAGE_DIMENSION
                or height > MAX_IMAGE_DIMENSION
                or width * height > MAX_DECODED_IMAGE_PIXELS
            ):
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="Decoded image dimensions exceed the safe processing limit.",
                )
            if getattr(img, "n_frames", 1) != 1:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Animated images are not supported.",
                )
            img.verify()
    except HTTPException:
        raise
    except (
        Image.DecompressionBombError,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as exc:
        LOGGER.warning(
            "phase7_upload id=%s stage=validate error=%s",
            analysis_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image is invalid or unreadable.",
        ) from exc

    return image_bytes, image_name


def _safe_analysis(image_bytes: bytes, analysis_id: str) -> dict:
    """Translate internal Phase 7 failures into safe HTTP responses.

    Runtime, forecast-integrity, routing, and unexpected failures are kept
    distinct for operations while avoiding model details or uploaded data in
    the client response.
    """
    # Run Phase 7 and convert each internal failure into a safe HTTP error.
    try:
        return analyze_phase7(image_bytes, analysis_id)
    except GradingRuntimeError as exc:
        LOGGER.warning(
            "phase7_analysis id=%s stage=grading error=%s",
            analysis_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Frozen grading runtime is unavailable or failed safely.",
        ) from exc
    except ForecastRecordError as exc:
        LOGGER.warning(
            "phase7_analysis id=%s stage=forecast error=%s",
            analysis_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Frozen grade-specific forecast evidence is unavailable or failed integrity validation.",
        ) from exc
    except ValueError as exc:
        LOGGER.warning(
            "phase7_analysis id=%s stage=decision error=%s",
            analysis_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The grade-to-price decision route failed closed.",
        ) from exc
    except Exception as exc:
        LOGGER.exception("Unexpected berry grading failure.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integrated analysis failed unexpectedly.",
        ) from exc


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness endpoint; it does not claim that artifacts are ready."""
    # Confirm only that the API process is alive.
    return {
        "status": "ok",
        "component": "phase7_grade_price_decision_support",
    }


@router.get("/ready")
def ready(response: Response) -> dict[str, object]:
    """Readiness endpoint for both ONNX grading and frozen price evidence."""
    # Recheck the complete frozen runtime and return 503 if any part is unavailable.
    try:
        initialize_phase7_runtime()
        readiness = "ready"
    except (GradingRuntimeError, ForecastRecordError):
        readiness = "not_ready"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": readiness,
        "component": "phase7_grade_price_decision_support",
        "runtime": "backend_onnx_runtime",
        "price_strategy": "frozen_phase5_forecast_records",
    }


@router.post("/analyze", response_model=Phase7AnalyzeResponse)
async def analyze(image: UploadFile | None = None) -> Phase7AnalyzeResponse:
    """Run the rejection-first grading → price-decision workflow.

    Response validation occurs after the integrated service returns. Invalid
    output is withheld with HTTP 500 rather than converted into a partial or
    fabricated forecast.
    """
    # Validate the upload, run Phase 7, and enforce the final response contract.
    analysis_id = str(uuid.uuid4())
    try:
        # Check the file size, format, dimensions, and readability before analysis.
        image_bytes, _ = await _read_valid_image_upload(image, analysis_id)
    finally:
        if image is not None:
            try:
                await image.close()
            except Exception as exc:
                LOGGER.warning(
                    "phase7_upload id=%s stage=close error=%s",
                    analysis_id,
                    type(exc).__name__,
                )
    # Run grading and apply the frozen image-quality rejection rules.
    result = _safe_analysis(image_bytes, analysis_id)
    try:
        validated = Phase7AnalyzeResponse.model_validate(result)
    except ValidationError as exc:
        LOGGER.error(
            "phase7_analysis id=%s stage=response_validation error=%s",
            analysis_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integrated analysis produced an invalid response and was withheld.",
        ) from exc
    LOGGER.info(
        "phase7_analysis id=%s category=%s",
        analysis_id,
        validated.decision_support.category.value,
    )
    # Send the validated analysis result to the frontend as the API response.
    return validated


@router.api_route("/grade-only", methods=["POST"], status_code=status.HTTP_410_GONE)
@router.api_route("/price-forecast", methods=["GET"], status_code=status.HTTP_410_GONE)
@router.api_route("/recommend", methods=["POST"], status_code=status.HTTP_410_GONE)
def retired_legacy_endpoint() -> dict[str, str]:
    """Keep pre-Phase-7 routes explicit and prevent accidental legacy use."""
    # Direct callers away from endpoints that the integrated Phase 7 flow replaced.
    return {"detail": "Retired in Phase 7; use POST /api/v1/grading-forecast/analyze."}
