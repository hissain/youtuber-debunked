import sys
import os
from unittest.mock import patch, MagicMock
import pytest
from ytdebunk.ytdebunk import main

def test_invalid_language(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ytdebunk", "https://youtube.com/watch?v=123", "-l", "fr"])
    res = main()
    assert res == (None, None)

def test_start_time_greater_than_end_time(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ytdebunk", "https://youtube.com/watch?v=123", "-st", "50", "-et", "20"])
    res = main()
    assert res == (None, None)

def test_enhance_without_token_fails(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GENAI_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["ytdebunk", "https://youtube.com/watch?v=123", "-e"])
    res = main()
    assert res == (None, None)

def test_detect_without_token_fails(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GENAI_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["ytdebunk", "https://youtube.com/watch?v=123", "-d"])
    res = main()
    assert res == (None, None)

@patch("ytdebunk.ytdebunk.download_audio")
@patch("ytdebunk.ytdebunk.transcribe_audio")
def test_plain_transcription_without_token_succeeds(mock_transcribe, mock_download, monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GENAI_API_KEY", raising=False)
    mock_transcribe.return_value = "Sample transcription"
    
    # Run plain transcription
    monkeypatch.setattr(sys, "argv", ["ytdebunk", "https://youtube.com/watch?v=123"])
    transcription, faults = main()
    assert mock_download.called
    assert mock_transcribe.called
    assert transcription == "Sample transcription"
    assert faults is None

@patch("ytdebunk.ytdebunk.download_audio")
@patch("ytdebunk.ytdebunk.transcribe_audio")
@patch("ytdebunk.ytdebunk.detect_logical_faults")
def test_token_passed_to_detect(mock_detect, mock_transcribe, mock_download, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GENAI_API_KEY", raising=False)
    mock_transcribe.return_value = "Sample text"
    mock_detect.return_value = "Detected fallacy"
    
    monkeypatch.setattr(sys, "argv", ["ytdebunk", "https://youtube.com/watch?v=123", "-d", "-t", "TEST_KEY_123"])
    transcription, faults = main()
    
    assert mock_detect.called
    # Verify key='TEST_KEY_123' was passed
    call_kwargs = mock_detect.call_args.kwargs
    assert call_kwargs.get("key") == "TEST_KEY_123"
    assert faults == "Detected fallacy"

@patch("ytdebunk.ytdebunk.extract_subtitles")
@patch("ytdebunk.ytdebunk.verify_claims")
@patch("ytdebunk.ytdebunk.generate_debunk_script")
@patch("ytdebunk.ytdebunk.synthesize_script")
@patch("ytdebunk.ytdebunk.sync_timeline")
def test_cli_phase3_full_pipeline(
    mock_sync,
    mock_synth,
    mock_script,
    mock_verify,
    mock_subs,
    monkeypatch
):
    mock_subs.return_value = ([{"start": 0, "end": 10, "text": "Claim quote"}], "Claim quote")
    mock_report = MagicMock()
    mock_report.overall_veracity_score = 45.0
    mock_report.claims = [MagicMock()]
    mock_report.to_json.return_value = '{"overall_veracity_score": 45.0}'
    mock_report.to_markdown.return_value = '# Report'
    mock_verify.return_value = mock_report

    mock_debunk_script = MagicMock()
    mock_debunk_script.persona = "journalist"
    mock_debunk_script.audio_path = "/path/to/voiceover.mp3"
    mock_debunk_script.to_markdown.return_value = '# Script'
    mock_script.return_value = mock_debunk_script
    mock_synth.return_value = mock_debunk_script

    mock_timeline_sheet = MagicMock()
    mock_timeline_sheet.events = [MagicMock()]
    mock_timeline_sheet.total_duration_seconds = 45.0
    mock_timeline_sheet.to_markdown.return_value = '# Timeline'
    mock_sync.return_value = mock_timeline_sheet

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ytdebunk",
            "https://youtube.com/watch?v=123",
            "-c",
            "-s",
            "-w",
            "--sync",
            "--persona", "journalist",
            "-t", "SAMPLE_KEY"
        ]
    )

    result = main()

    assert mock_verify.called
    assert mock_script.called
    assert mock_synth.called
    assert mock_sync.called

    assert result.report == mock_report
    assert result.script == mock_debunk_script
    assert result.timeline == mock_timeline_sheet

    # Backward compatible 2-tuple unpacking
    transcription, faults = result
    assert transcription == "Claim quote"
    assert faults is None

@patch("ytdebunk.ytdebunk.extract_subtitles")
@patch("ytdebunk.ytdebunk.verify_claims")
@patch("ytdebunk.ytdebunk.generate_debunk_script")
@patch("ytdebunk.ytdebunk.synthesize_script")
@patch("ytdebunk.ytdebunk.sync_timeline")
@patch("ytdebunk.ytdebunk.compose_debunk_video")
def test_cli_phase4_make_video(
    mock_compose,
    mock_sync,
    mock_synth,
    mock_script,
    mock_verify,
    mock_subs,
    monkeypatch
):
    mock_subs.return_value = ([{"start": 0, "end": 10, "text": "Claim quote"}], "Claim quote")
    mock_report = MagicMock()
    mock_report.claims = [MagicMock()]
    mock_report.to_json.return_value = '{"overall_veracity_score": 50.0}'
    mock_report.to_markdown.return_value = '# Report'
    mock_verify.return_value = mock_report

    mock_debunk_script = MagicMock()
    mock_debunk_script.to_markdown.return_value = '# Script'
    mock_script.return_value = mock_debunk_script
    mock_synth.return_value = mock_debunk_script

    mock_timeline = MagicMock()
    mock_timeline.events = [MagicMock()]
    mock_timeline.total_duration_seconds = 10.0
    mock_timeline.to_markdown.return_value = '# Timeline'
    mock_sync.return_value = mock_timeline
    mock_compose.return_value = "/path/to/rendered_video.mp4"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ytdebunk",
            "https://youtube.com/watch?v=123",
            "-m",
            "--aspect_ratio", "vertical",
            "-t", "SAMPLE_KEY"
        ]
    )

    result = main()

    assert mock_verify.called
    assert mock_script.called
    assert mock_synth.called
    assert mock_sync.called
    assert mock_compose.called
    assert mock_compose.call_args.kwargs["aspect_ratio"] == "vertical"

    assert result.video_path == "/path/to/rendered_video.mp4"
    transcription, faults = result
    assert transcription == "Claim quote"
