from fastapi.testclient import TestClient
from app import main as main_module


def test_lifespan_initializes_complete_phase7_runtime(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(main_module, "load_dotenv", lambda: calls.append("load_dotenv"))
    monkeypatch.setattr(main_module, "initialize_phase7_runtime", lambda: calls.append("initialize_phase7_runtime"))
    with TestClient(main_module.create_app()):
        pass
    assert calls == ["load_dotenv", "initialize_phase7_runtime"]
