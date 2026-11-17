import os
import subprocess
from unittest.mock import patch, MagicMock
import pytest
from PIL import Image
from ytdebunk.schema import (
    DebunkReport,
    ClaimVerification,
    DebunkScript,
    ScriptSegment,
    TimelineSheet,
    TimelineEvent
)
from ytdebunk.graphics import (
    get_dimensions,
    create_intro_card,
    create_claim_card,
    create_rebuttal_card,
    create_scorecard_card,
    generate_all_graphics
)
from ytdebunk.videomaker import (
    check_ffmpeg_available,
    render_image_audio_clip,
    concat_video_clips,
    compose_debunk_video
)
from ytdebunk.downloader import download_video

@pytest.fixture
def mock_studio_data():
    report = DebunkReport(
        video_url="https://youtube.com/watch?v=sample123",
        video_title="Flat Earth Claims Tested",
        language="en",
        summary="Empirical evidence from geodesy and spaceflight refutes planar earth hypotheses.",
        overall_veracity_score=10.0,
        claims=[
            ClaimVerification(
                id=1,
                timestamp_start="00:05",
                timestamp_end="00:20",
                original_quote="The horizon is always completely flat at any altitude.",
                claim_text="The curvature of the Earth is never visible from any altitude.",
                claim_type="Scientific",
                veracity="False",
                confidence_score=0.99,
                is_fallacious=True,
                fallacy_type="Cherry Picking",
                evidence_summary="Geometric horizon dips measurably and curvature is visible above 35,000 feet.",
                sources=["https://space.nasa.gov"],
                counter_argument="High-altitude flights and satellite geodesy directly photograph and measure terrestrial curvature."
            )
        ],
        fallacies_found=["Cherry Picking"]
    )

    script = DebunkScript(
        video_url=report.video_url,
        video_title=report.video_title,
        language="en",
        persona="skeptic",
        hook="Think the Earth is flat? Let's check the flight instruments.",
        segments=[
            ScriptSegment(
                segment_id=1,
                claim_id=1,
                timestamp_start="00:05",
                timestamp_end="00:20",
                speaker_quote="The horizon is always completely flat at any altitude.",
                rebuttal_text="Commercial pilots use artificial horizon gyroscopes that continuously calibrate for Earth's curvature.",
                visual_cue="Display 'FALSE' Badge with Horizon Dip Diagram",
                duration_seconds=3.0
            )
        ],
        outro="Gravity is real, geometry works, and our planet remains delightfully round."
    )

    timeline = TimelineSheet(
        video_url=report.video_url,
        language="en",
        total_duration_seconds=9.0,
        events=[
            TimelineEvent(
                event_id=1,
                claim_id=None,
                event_type="intro",
                title="Studio Hook",
                start_seconds=0.0,
                end_seconds=3.0,
                timestamp_start="00:00",
                timestamp_end="00:03",
                duration_seconds=3.0,
                text=script.hook,
                cue="Intro Card"
            ),
            TimelineEvent(
                event_id=2,
                claim_id=1,
                event_type="debunk_rebuttal",
                title="Debunker Rebuttal #1",
                start_seconds=3.0,
                end_seconds=6.0,
                timestamp_start="00:03",
                timestamp_end="00:06",
                duration_seconds=3.0,
                text=script.segments[0].rebuttal_text,
                veracity="False",
                cue="Show FALSE badge"
            ),
            TimelineEvent(
                event_id=3,
                claim_id=None,
                event_type="outro",
                title="Debunker Outro",
                start_seconds=6.0,
                end_seconds=9.0,
                timestamp_start="00:06",
                timestamp_end="00:09",
                duration_seconds=3.0,
                text=script.outro,
                cue="Show Scorecard"
            )
        ]
    )

    return report, script, timeline

def test_check_ffmpeg_available():
    assert check_ffmpeg_available() is True

def test_graphics_dimensions():
    w_l, h_l = get_dimensions("landscape")
    assert w_l == 1280
    assert h_l == 720

    w_v, h_v = get_dimensions("vertical")
    assert w_v == 720
    assert h_v == 1280

def test_generate_all_graphics(mock_studio_data, tmp_path):
    report, script, _ = mock_studio_data
    graphics_dir = str(tmp_path / "graphics")

    cards = generate_all_graphics(report, script, aspect_ratio="landscape", output_dir=graphics_dir)
    
    assert "intro" in cards
    assert "claim_1" in cards
    assert "rebuttal_1" in cards
    assert "outro" in cards

    for name, path in cards.items():
        assert os.path.exists(path)
        img = Image.open(path)
        assert img.size == (1280, 720)

def test_render_image_audio_clip_silent(tmp_path):
    card_path = str(tmp_path / "sample_card.png")
    img = Image.new("RGB", (640, 360), color=(15, 23, 42))
    img.save(card_path)

    clip_path = str(tmp_path / "rendered_clip.mp4")
    res = render_image_audio_clip(
        image_path=card_path,
        duration=1.0,
        output_clip_path=clip_path,
        audio_path=None,
        resolution=(640, 360)
    )

    assert res == clip_path
    assert os.path.exists(clip_path)
    assert os.path.getsize(clip_path) > 1000

def test_concat_video_clips(tmp_path):
    card_path = str(tmp_path / "card.png")
    img = Image.new("RGB", (640, 360), color=(15, 23, 42))
    img.save(card_path)

    clip1 = str(tmp_path / "clip1.mp4")
    clip2 = str(tmp_path / "clip2.mp4")
    render_image_audio_clip(card_path, duration=0.8, output_clip_path=clip1, resolution=(640, 360))
    render_image_audio_clip(card_path, duration=0.8, output_clip_path=clip2, resolution=(640, 360))

    final_video = str(tmp_path / "final_combined.mp4")
    res = concat_video_clips([clip1, clip2], final_video)

    assert res == final_video
    assert os.path.exists(final_video)
    assert os.path.getsize(final_video) > 2000

def test_compose_debunk_video_end_to_end(mock_studio_data, tmp_path):
    report, script, timeline = mock_studio_data
    out_video = str(tmp_path / "debunk_rendered.mp4")

    # Run complete composition pipeline
    res_path = compose_debunk_video(
        report=report,
        script=script,
        timeline=timeline,
        output_path=out_video,
        aspect_ratio="landscape"
    )

    assert res_path == out_video
    assert os.path.exists(out_video)
    assert os.path.getsize(out_video) > 5000

@patch("yt_dlp.YoutubeDL")
def test_download_video_mock(mock_ydl_cls, tmp_path):
    mock_ydl = MagicMock()
    mock_ydl.download.return_value = 0
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

    target_file = str(tmp_path / "test_download.mp4")
    # Simulate downloaded file
    with open(target_file, "w") as f:
        f.write("dummy video data")

    res = download_video("https://youtube.com/watch?v=123", output_path=target_file)
    assert res == target_file
    assert mock_ydl_cls.called
