from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from core.self_test import create_synthetic_video, probe_video
from server import app


def test_self_test_routes_are_registered():
    text = (ROOT / "server.py").read_text()
    assert "self_test_routes" in text
    assert "app.include_router(self_test_routes.router)" in text


def test_synthetic_video_is_real_mp4(tmp_path):
    result = create_synthetic_video(str(tmp_path / "smoke.mp4"), duration=1)
    assert result["ok"] is True
    assert result["codec"] == "h264"
    assert result["width"] == 640
    assert result["height"] == 360
    assert result["duration_seconds"] > 0


def test_probe_rejects_missing_file(tmp_path):
    result = probe_video(str(tmp_path / "missing.mp4"))
    assert result["ok"] is False


def test_health_is_actionable():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert "checks" in body
        assert "fully_ready" in body
        assert "tts_dependency" in body["checks"]


def test_live_self_test_refuses_without_provider_key(monkeypatch):
    monkeypatch.delenv("AGNES_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.post("/api/self-test/live")
        assert response.status_code == 412
        body = response.json()
        assert body["error_code"] == "AGNES_API_KEY_MISSING"
