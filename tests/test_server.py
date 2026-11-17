import os
from unittest.mock import patch, MagicMock
import pytest
from starlette.testclient import TestClient
from ytdebunk.server import app
from ytdebunk.ytdebunk import DebunkResult
import ytdebunk.settings as settings

client = TestClient(app)

def test_serve_studio_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Debunker" in response.text
    # Verify Infomity color tokens present
    assert "#07090e" in response.text
    assert "#10b981" in response.text

def test_get_voices():
    response = client.get("/api/voices")
    assert response.status_code == 200
    voices = response.json()
    assert len(voices) >= 4
    
    # Filter by Bengali
    res_bn = client.get("/api/voices?language=bn")
    assert res_bn.status_code == 200
    bn_voices = res_bn.json()
    assert all(v["language"] == "bn" for v in bn_voices)

def test_download_directory_traversal_protection():
    response = client.get("/api/download/..%2Fsecret.txt")
    assert response.status_code == 400

def test_download_file_not_found():
    response = client.get("/api/download/non_existent_file.json")
    assert response.status_code == 404

def test_download_existing_file(tmp_path, monkeypatch):
    test_file = tmp_path / "test_report.json"
    with open(test_file, "w") as f:
        f.write('{"test": true}')

    monkeypatch.setattr(settings, "OUTPUT_DIRECTORY", str(tmp_path))

    response = client.get("/api/download/test_report.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"test": True}

def test_get_config():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "has_gemini_key" in data
    assert "version" in data
    assert data["status"] == "ready"

def test_get_logs():
    response = client.get("/api/logs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert isinstance(data["logs"], list)

def test_save_key(tmp_path, monkeypatch):
    dummy_env = str(tmp_path / ".env")
    monkeypatch.setattr("ytdebunk.server.os.path.join", lambda *args: dummy_env if args[-1] == ".env" else os.path.join(*args))
    response = client.post("/api/save_key", json={"key": "test-api-key-12345"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert os.environ.get("GEMINI_API_KEY") == "test-api-key-12345"
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

def test_analyze_missing_token_returns_400(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GENAI_API_KEY", raising=False)
    req_payload = {
        "video_url": "https://www.youtube.com/watch?v=123",
        "verify": True,
        "script": True
    }
    response = client.post("/api/analyze", json=req_payload)
    assert response.status_code == 400
    assert "Gemini API Key is required" in response.json()["detail"]

@patch("ytdebunk.server.ytdebunk_main")
def test_analyze_video_endpoint(mock_main):
    mock_report = MagicMock()
    mock_report.model_dump.return_value = {"overall_veracity_score": 75.0}
    mock_script = MagicMock()
    mock_script.model_dump.return_value = {"persona": "skeptic"}
    mock_timeline = MagicMock()
    mock_timeline.model_dump.return_value = {"total_duration_seconds": 15.0}

    mock_main.return_value = DebunkResult(
        "Sample transcribed text",
        "Sample logical faults",
        report=mock_report,
        script=mock_script,
        timeline=mock_timeline,
        video_path="/path/to/video.mp4"
    )

    req_payload = {
        "video_url": "https://www.youtube.com/watch?v=123",
        "language": "en",
        "persona": "skeptic",
        "token": "mock-test-key",
        "verify": True,
        "script": True,
        "voice": True,
        "sync": True,
        "make_video": False
    }

    response = client.post("/api/analyze", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["transcription"] == "Sample transcribed text"
    assert data["logical_faults"] == "Sample logical faults"
    assert data["report"]["overall_veracity_score"] == 75.0
    assert data["script"]["persona"] == "skeptic"
    assert data["video_path"] == "/path/to/video.mp4"
    assert "logs" in data
