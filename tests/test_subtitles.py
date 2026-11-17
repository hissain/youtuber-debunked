import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from ytdebunk.subtitles import (
    parse_vtt_timestamp,
    format_seconds,
    clean_vtt,
    get_target_languages,
    extract_subtitles
)
from ytdebunk.ytdebunk import main

SAMPLE_VTT = """WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:03.500
The earth revolves around the sun.

00:00:03.500 --> 00:00:06.000
This has been proven for centuries.
"""

ROLLING_VTT = """WEBVTT
Kind: captions
Language: en

00:00:00.100 --> 00:00:01.000 align:start position:0%
hello<00:00:00.300><c> world</c>

00:00:01.000 --> 00:00:01.010 align:start position:0%
hello world

00:00:01.010 --> 00:00:02.500 align:start position:0%
hello world
welcome<00:00:01.500><c> back</c>
"""

def test_parse_vtt_timestamp():
    assert parse_vtt_timestamp("00:01:23.456") == 83.456
    assert parse_vtt_timestamp("01:23.456") == 83.456
    assert parse_vtt_timestamp("45.5") == 45.5
    assert parse_vtt_timestamp("invalid") == 0.0

def test_format_seconds():
    assert format_seconds(83) == "01:23"
    assert format_seconds(3665) == "01:01:05"

def test_clean_vtt_basic():
    segs, text = clean_vtt(SAMPLE_VTT)
    assert len(segs) == 2
    assert segs[0]["text"] == "The earth revolves around the sun."
    assert segs[1]["text"] == "This has been proven for centuries."
    assert "The earth revolves around the sun. This has been proven for centuries." == text

def test_clean_vtt_rolling_auto_captions():
    segs, text = clean_vtt(ROLLING_VTT)
    # Deduplication should eliminate repeated 'hello world'
    assert "hello world" in text
    assert "welcome back" in text
    assert text.count("hello world") == 1

def test_clean_vtt_time_bounds():
    segs, text = clean_vtt(SAMPLE_VTT, start_time=3.0, end_time=5.0)
    # First cue ends at 3.5 (>= 3.0), second cue starts at 3.5 (<= 5.0)
    assert len(segs) == 2

    # Restrict bounds strictly
    segs_late, _ = clean_vtt(SAMPLE_VTT, start_time=4.0)
    assert len(segs_late) == 1
    assert segs_late[0]["text"] == "This has been proven for centuries."

def test_get_target_languages():
    assert "en" in get_target_languages("en")
    assert "bn" in get_target_languages("bn")
    assert "fr" in get_target_languages("fr")

@patch("ytdebunk.subtitles.yt_dlp.YoutubeDL")
def test_extract_subtitles_found(mock_ydl_cls, tmp_path):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

    # Side effect creates a simulated .vtt in the temp directory yt-dlp was called with
    def fake_download(urls):
        ydl_call_opts = mock_ydl_cls.call_args[0][0]
        outtmpl = ydl_call_opts["outtmpl"]
        vtt_path = f"{outtmpl}.en.vtt"
        with open(vtt_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_VTT)

    mock_ydl.download.side_effect = fake_download

    res = extract_subtitles("https://youtube.com/watch?v=sample", language="en")
    assert res is not None
    segments, text = res
    assert len(segments) == 2
    assert "The earth revolves around the sun." in text

@patch("ytdebunk.subtitles.yt_dlp.YoutubeDL")
def test_extract_subtitles_none_found(mock_ydl_cls):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    # Download produces no files
    res = extract_subtitles("https://youtube.com/watch?v=sample", language="en")
    assert res is None

@patch("ytdebunk.ytdebunk.extract_subtitles")
@patch("ytdebunk.ytdebunk.download_audio")
@patch("ytdebunk.ytdebunk.transcribe_audio")
def test_cli_bypasses_whisper_when_subtitles_exist(mock_transcribe, mock_download, mock_extract, monkeypatch):
    mock_extract.return_value = ([{"start": 0, "end": 2, "text": "Instant sub"}], "Instant sub")
    monkeypatch.setattr(sys, "argv", ["ytdebunk", "https://youtube.com/watch?v=123"])
    
    transcription, faults = main()
    assert mock_extract.called
    assert not mock_download.called
    assert not mock_transcribe.called
    assert transcription == "Instant sub"

@patch("ytdebunk.ytdebunk.extract_subtitles")
@patch("ytdebunk.ytdebunk.download_audio")
@patch("ytdebunk.ytdebunk.transcribe_audio")
def test_cli_force_asr_ignores_subtitles(mock_transcribe, mock_download, mock_extract, monkeypatch):
    mock_transcribe.return_value = "Whisper generated text"
    monkeypatch.setattr(sys, "argv", ["ytdebunk", "https://youtube.com/watch?v=123", "--force_asr"])

    transcription, faults = main()
    assert not mock_extract.called
    assert mock_download.called
    assert mock_transcribe.called
    assert transcription == "Whisper generated text"
