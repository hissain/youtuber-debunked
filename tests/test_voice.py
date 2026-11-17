import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from ytdebunk.schema import DebunkScript, ScriptSegment
from ytdebunk.voice import (
    get_default_voice,
    list_available_voices,
    get_audio_duration,
    synthesize_speech,
    synthesize_script
)

def test_get_default_voice():
    assert get_default_voice("en", "male") == "en-US-GuyNeural"
    assert get_default_voice("en", "female") == "en-US-JennyNeural"
    assert get_default_voice("bn", "male") == "bn-BD-PradeepNeural"
    assert get_default_voice("bn", "female") == "bn-BD-NabanitaNeural"
    # Fallback on unknown
    assert get_default_voice("unknown", "male") == "en-US-GuyNeural"

def test_list_available_voices():
    all_voices = list_available_voices()
    assert len(all_voices) >= 6
    
    bn_voices = list_available_voices("bn")
    assert all(v["language"] == "bn" for v in bn_voices)
    assert any("Pradeep" in v["name"] for v in bn_voices)
    
    en_voices = list_available_voices("en")
    assert all(v["language"] == "en" for v in en_voices)
    assert any("Guy" in v["name"] for v in en_voices)

def test_get_audio_duration_fallback():
    # If file doesn't exist, estimates from text length (~2.5 words/s)
    dur = get_audio_duration("non_existent_file.mp3", fallback_text="This is a ten word test sentence for audio duration calculation.")
    assert dur >= 3.0
    assert dur <= 6.0

@patch("edge_tts.Communicate")
def test_synthesize_speech_mock(mock_communicate_cls, tmp_path):
    mock_instance = MagicMock()
    mock_instance.save = AsyncMock(return_value=None)
    mock_communicate_cls.return_value = mock_instance

    out_file = str(tmp_path / "test_synth.mp3")
    res = synthesize_speech("Hello world", out_file, voice="en-US-GuyNeural")
    
    assert res == out_file
    assert mock_communicate_cls.called
    call_kwargs = mock_communicate_cls.call_args.kwargs
    assert call_kwargs["text"] == "Hello world"
    assert call_kwargs["voice"] == "en-US-GuyNeural"
    assert mock_instance.save.called

@patch("edge_tts.Communicate")
def test_synthesize_speech_in_running_event_loop(mock_communicate_cls, tmp_path):
    """
    Ensures synthesize_speech does not raise RuntimeError when called inside an already running event loop.
    """
    mock_instance = MagicMock()
    mock_instance.save = AsyncMock(return_value=None)
    mock_communicate_cls.return_value = mock_instance

    out_file = str(tmp_path / "test_thread.mp3")

    async def runner():
        return synthesize_speech("Inner loop test", out_file, voice="en-US-JennyNeural")

    res = asyncio.run(runner())
    assert res == out_file

@patch("ytdebunk.voice.synthesize_speech")
def test_synthesize_script(mock_synth, tmp_path):
    mock_synth.return_value = "/fake/path/audio.mp3"

    script = DebunkScript(
        video_url="https://youtube.com/watch?v=123",
        video_title="Fact Check Video",
        language="en",
        persona="skeptic",
        hook="Welcome to the debunk studio!",
        segments=[
            ScriptSegment(
                segment_id=1,
                claim_id=1,
                timestamp_start="00:10",
                timestamp_end="00:25",
                speaker_quote="The moon is hollow.",
                rebuttal_text="Seismic data from Apollo proves the moon has a dense metallic core.",
                visual_cue="Show 'FALSE' badge"
            )
        ],
        outro="Stay curious and keep verifying."
    )

    out_dir = str(tmp_path / "segments")
    res_script = synthesize_script(
        script=script,
        voice="en-US-GuyNeural",
        output_dir=out_dir,
        combine_full=True
    )

    assert res_script.segments[0].audio_path is not None
    assert res_script.segments[0].duration_seconds is not None
    assert res_script.audio_path is not None
    assert res_script.total_duration_seconds is not None
    # Called for: intro, segment 1, outro, and full narration
    assert mock_synth.call_count == 4
