import pytest
import ytdebunk.settings as settings

@pytest.fixture(autouse=True)
def isolate_output_directory(tmp_path, monkeypatch):
    """
    Ensures that file writes during tests go to an isolated temporary directory
    instead of the repository's output/ directory.
    """
    out_dir = str(tmp_path / "test_output")
    monkeypatch.setattr(settings, "OUTPUT_DIRECTORY", out_dir)
    monkeypatch.setattr(settings, "AUDIO_FILE", f"{out_dir}/audio.mp3")
    monkeypatch.setattr(settings, "VIDEO_FILE", f"{out_dir}/video.mp4")
    monkeypatch.setattr(settings, "TRANSCRIPTION_FILE", f"{out_dir}/transcription.txt")
    monkeypatch.setattr(settings, "REFINED_TRANSCRIPTION_FILE", f"{out_dir}/refined_transcription.txt")
    monkeypatch.setattr(settings, "LOGICAL_FAULTS_FILE", f"{out_dir}/logical_faults.txt")
    monkeypatch.setattr(settings, "SUBTITLES_JSON_FILE", f"{out_dir}/subtitles.json")
    monkeypatch.setattr(settings, "DEBUNK_REPORT_JSON", f"{out_dir}/debunk_report.json")
    monkeypatch.setattr(settings, "DEBUNK_REPORT_MD", f"{out_dir}/debunk_report.md")
    monkeypatch.setattr(settings, "DEBUNK_SCRIPT_JSON", f"{out_dir}/debunk_script.json")
    monkeypatch.setattr(settings, "DEBUNK_SCRIPT_MD", f"{out_dir}/debunk_script.md")
    monkeypatch.setattr(settings, "TIMELINE_JSON", f"{out_dir}/timeline.json")
    monkeypatch.setattr(settings, "TIMELINE_MD", f"{out_dir}/timeline.md")
    monkeypatch.setattr(settings, "AUDIO_SEGMENTS_DIR", f"{out_dir}/audio_segments")
    monkeypatch.setattr(settings, "FULL_DEBUNK_AUDIO", f"{out_dir}/debunk_voiceover.mp3")
    monkeypatch.setattr(settings, "DEBUNK_VIDEO_FILE", f"{out_dir}/debunk_video.mp4")
    monkeypatch.setattr(settings, "DEBUNK_SHORTS_FILE", f"{out_dir}/debunk_shorts.mp4")
    monkeypatch.setattr(settings, "GRAPHICS_DIR", f"{out_dir}/graphics")
