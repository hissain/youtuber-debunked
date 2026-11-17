from unittest.mock import patch, MagicMock
import pytest
from app import get_video_preview, run_ytdebunk
from ytdebunk.ytdebunk import DebunkResult

def test_get_video_preview_standard_url():
    url = "https://www.youtube.com/watch?v=w4sJoZ9D1YM"
    preview = get_video_preview(url)
    assert preview == "https://img.youtube.com/vi/w4sJoZ9D1YM/hqdefault.jpg"

def test_get_video_preview_short_url():
    url = "https://youtu.be/w4sJoZ9D1YM"
    preview = get_video_preview(url)
    assert preview == "https://img.youtube.com/vi/w4sJoZ9D1YM/hqdefault.jpg"

def test_get_video_preview_shorts_url():
    url = "https://www.youtube.com/shorts/l8UDM4bOhpU"
    preview = get_video_preview(url)
    assert preview == "https://img.youtube.com/vi/l8UDM4bOhpU/hqdefault.jpg"

def test_get_video_preview_empty_or_invalid():
    assert get_video_preview("") is None
    assert get_video_preview(None) is None

@patch("app.ytdebunk_main")
def test_run_ytdebunk_with_verify(mock_main):
    mock_report = MagicMock()
    mock_script = MagicMock()
    mock_timeline = MagicMock()
    mock_main.return_value = DebunkResult(
        "Sample transcript",
        "Sample fallacies",
        report=mock_report,
        script=mock_script,
        timeline=mock_timeline,
        video_path="/path/to/debunk_video.mp4"
    )
    log_mock = MagicMock()

    t, f, r, s, tm, vp = run_ytdebunk(
        video_url="https://youtube.com/watch?v=123",
        st_time=10,
        et_time=20,
        language="English",
        enhance=True,
        detect=True,
        verbose=True,
        token="FAKE_KEY",
        log_placeholder=log_mock,
        verify=True,
        script=True,
        persona="journalist",
        voice=True,
        voice_name="en-US-GuyNeural",
        sync=True,
        make_video=True,
        aspect_ratio="landscape",
        force_asr=True
    )

    assert t == "Sample transcript"
    assert f == "Sample fallacies"
    assert r == mock_report
    assert s == mock_script
    assert tm == mock_timeline
    assert vp == "/path/to/debunk_video.mp4"
