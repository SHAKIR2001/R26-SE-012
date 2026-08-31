import utils.transport
import utils.session
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.services.grading_forecast.artifact_service import download_runtime_artifacts
from app.services.grading_forecast.grading_service import initialize_grading_runtime
from app.services.grading_forecast.price_forecast_service import initialize_forecast_runtime


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    download_runtime_artifacts()
    initialize_grading_runtime()
    initialize_forecast_runtime()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Multimodal Pepper AI Decision Support - Backend",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
