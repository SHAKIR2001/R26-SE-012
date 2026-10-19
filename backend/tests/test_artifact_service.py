from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from app.services.grading_forecast import artifact_service
from app.services.grading_forecast.artifact_service import (
    ArtifactConfigurationError,
    ArtifactDownloadError,
    RuntimeArtifacts,
)


HF_ENV = {
    "HF_TOKEN": "test-token",
    "HF_MODEL_REPO": "example/private-runtime",
    "HF_MODEL_REVISION": "main",
    "HF_GRADING_MODEL_FILE": "grading/berry_mobilenetv2_v2_best.onnx",
    "HF_CLASS_NAMES_FILE": "grading/class_names.json",
    "HF_FORECAST_MODEL_FILE": "forecasting/forecast_model.joblib",
    "HF_FORECAST_METRICS_FILE": "forecasting/naive_persistence_metrics.json",
    "HF_FORECAST_DATA_FILE": "forecasting/national_grade1_average_weekly.csv",
}

URL_ENV = {
    "ARTIFACT_GRADING_MODEL_URL": "https://github.com/example/releases/download/v1/berry.onnx",
    "ARTIFACT_CLASS_NAMES_URL": "https://github.com/example/releases/download/v1/class_names.json",
    "ARTIFACT_FORECAST_MODEL_URL": "https://github.com/example/releases/download/v1/forecast.joblib",
    "ARTIFACT_FORECAST_METRICS_URL": "https://github.com/example/releases/download/v1/metrics.json",
    "ARTIFACT_FORECAST_DATA_URL": "https://github.com/example/releases/download/v1/series.csv",
}


def _set_hf_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in HF_ENV.items():
        monkeypatch.setenv(key, value)


def _set_url_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in URL_ENV.items():
        monkeypatch.setenv(key, value)


class _FakeUrlResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> "_FakeUrlResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_missing_hugging_face_configuration_fails_clearly() -> None:
    with pytest.raises(ArtifactConfigurationError, match="HF_TOKEN"):
        artifact_service.load_hugging_face_artifact_config()


def test_download_runtime_artifacts_uses_hf_hub_download(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_hf_env(monkeypatch)
    calls: list[dict[str, str]] = []

    def fake_hf_hub_download(*, repo_id: str, filename: str, revision: str, token: str) -> str:
        calls.append(
            {
                "repo_id": repo_id,
                "filename": filename,
                "revision": revision,
                "token": token,
            }
        )
        local = tmp_path / filename.replace("/", "_")
        local.write_text("artifact", encoding="utf-8")
        return str(local)

    fake_module = types.SimpleNamespace(hf_hub_download=fake_hf_hub_download)
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_module)

    artifacts = artifact_service.download_runtime_artifacts()

    assert artifacts.grading_model_path.is_file()
    assert artifacts.class_names_path.is_file()
    assert artifacts.forecast_model_path.is_file()
    assert artifacts.forecast_metrics_path.is_file()
    assert artifacts.forecast_data_path.is_file()
    assert artifact_service.runtime_artifacts_ready() is True
    assert [call["filename"] for call in calls] == [
        HF_ENV["HF_GRADING_MODEL_FILE"],
        HF_ENV["HF_CLASS_NAMES_FILE"],
        HF_ENV["HF_FORECAST_MODEL_FILE"],
        HF_ENV["HF_FORECAST_METRICS_FILE"],
        HF_ENV["HF_FORECAST_DATA_FILE"],
    ]
    assert all(call["repo_id"] == HF_ENV["HF_MODEL_REPO"] for call in calls)
    assert all(call["revision"] == HF_ENV["HF_MODEL_REVISION"] for call in calls)
    assert all(call["token"] == HF_ENV["HF_TOKEN"] for call in calls)


def test_failed_hugging_face_download_raises_without_token_leak(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_hf_env(monkeypatch)
    monkeypatch.setattr(artifact_service, "_repo_root", lambda: tmp_path / "empty_repo")

    def fake_hf_hub_download(**_kwargs) -> str:
        raise RuntimeError("private failure containing test-token")

    fake_module = types.SimpleNamespace(hf_hub_download=fake_hf_hub_download)
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_module)

    with pytest.raises(ArtifactDownloadError) as exc_info:
        artifact_service.download_runtime_artifacts()

    assert "test-token" not in str(exc_info.value)


def test_download_runtime_artifacts_falls_back_to_urls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_hf_env(monkeypatch)
    _set_url_env(monkeypatch)
    monkeypatch.setenv("ARTIFACT_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(artifact_service, "_repo_root", lambda: tmp_path / "empty_repo")
    calls: list[str] = []

    def fake_hf_hub_download(**_kwargs) -> str:
        raise RuntimeError("hugging face unavailable")

    def fake_urlopen(request: object, timeout: int) -> _FakeUrlResponse:
        del timeout
        calls.append(request.full_url)  # type: ignore[attr-defined]
        return _FakeUrlResponse(b"artifact")

    fake_module = types.SimpleNamespace(hf_hub_download=fake_hf_hub_download)
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_module)
    monkeypatch.setattr(artifact_service, "urlopen", fake_urlopen)

    artifacts = artifact_service.download_runtime_artifacts()

    assert artifacts.grading_model_path.is_file()
    assert artifacts.class_names_path.is_file()
    assert artifacts.forecast_model_path.is_file()
    assert artifacts.forecast_metrics_path.is_file()
    assert artifacts.forecast_data_path.is_file()
    assert calls == [
        URL_ENV["ARTIFACT_GRADING_MODEL_URL"],
        URL_ENV["ARTIFACT_CLASS_NAMES_URL"],
        URL_ENV["ARTIFACT_FORECAST_MODEL_URL"],
        URL_ENV["ARTIFACT_FORECAST_METRICS_URL"],
        URL_ENV["ARTIFACT_FORECAST_DATA_URL"],
    ]
    assert artifact_service.runtime_artifacts_ready() is True


def test_download_runtime_artifacts_falls_back_to_bundled_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_hf_env(monkeypatch)

    root = tmp_path / "repo"
    bundled_files = [
        root
        / "ml"
        / "grading_forecast"
        / "berry_grading"
        / "models"
        / "v2"
        / "berry_mobilenetv2_v2_best.onnx",
        root
        / "ml"
        / "grading_forecast"
        / "berry_grading"
        / "models"
        / "v2"
        / "class_names.json",
        root
        / "ml"
        / "grading_forecast"
        / "price_forecasting"
        / "models"
        / "v2"
        / "forecast_model.joblib",
        root
        / "ml"
        / "grading_forecast"
        / "price_forecasting"
        / "models"
        / "v2"
        / "naive_persistence_metrics.json",
        root
        / "data"
        / "processed"
        / "grading_forecast"
        / "price_v2"
        / "national_grade1_average_weekly.csv",
    ]
    for path in bundled_files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("artifact", encoding="utf-8")

    def fake_hf_hub_download(**_kwargs) -> str:
        raise RuntimeError("hugging face unavailable")

    fake_module = types.SimpleNamespace(hf_hub_download=fake_hf_hub_download)
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_module)
    monkeypatch.setattr(artifact_service, "_repo_root", lambda: root)

    artifacts = artifact_service.download_runtime_artifacts()

    assert artifacts.grading_model_path == bundled_files[0]
    assert artifacts.class_names_path == bundled_files[1]
    assert artifacts.forecast_model_path == bundled_files[2]
    assert artifacts.forecast_metrics_path == bundled_files[3]
    assert artifacts.forecast_data_path == bundled_files[4]
    assert artifact_service.runtime_artifacts_ready() is True


def test_ready_status_reports_loaded_artifacts(tmp_path: Path) -> None:
    paths = []
    for name in (
        "model.onnx",
        "class_names.json",
        "forecast.joblib",
        "metrics.json",
        "series.csv",
    ):
        path = tmp_path / name
        path.write_text("artifact", encoding="utf-8")
        paths.append(path)

    artifact_service.set_runtime_artifacts_for_tests(
        RuntimeArtifacts(
            grading_model_path=paths[0],
            class_names_path=paths[1],
            forecast_model_path=paths[2],
            forecast_metrics_path=paths[3],
            forecast_data_path=paths[4],
        )
    )

    assert artifact_service.runtime_artifacts_ready() is True
