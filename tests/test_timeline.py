import pytest
from ytdebunk.schema import (
    DebunkReport,
    ClaimVerification,
    DebunkScript,
    ScriptSegment,
    TimelineSheet,
    TimelineEvent
)
from ytdebunk.timeline import (
    parse_timestamp_to_seconds,
    format_seconds_to_timestamp,
    sync_timeline
)

def test_parse_timestamp_to_seconds():
    assert parse_timestamp_to_seconds("00:15") == 15.0
    assert parse_timestamp_to_seconds("01:30") == 90.0
    assert parse_timestamp_to_seconds("1:05") == 65.0
    assert parse_timestamp_to_seconds("01:05:20") == 3920.0
    assert parse_timestamp_to_seconds("45") == 45.0
    assert parse_timestamp_to_seconds(None) == 0.0
    assert parse_timestamp_to_seconds("") == 0.0
    assert parse_timestamp_to_seconds("invalid") == 0.0

def test_format_seconds_to_timestamp():
    assert format_seconds_to_timestamp(15.0) == "00:15"
    assert format_seconds_to_timestamp(90.0) == "01:30"
    assert format_seconds_to_timestamp(3920.0) == "01:05:20"
    assert format_seconds_to_timestamp(0.0) == "00:00"

def test_sync_timeline_interleaved(tmp_path):
    report = DebunkReport(
        video_url="https://youtube.com/watch?v=sample",
        video_title="Diet Myths Debunked",
        language="en",
        summary="Claims regarding extreme diets lack clinical evidence.",
        overall_veracity_score=20.0,
        claims=[
            ClaimVerification(
                id=1,
                timestamp_start="00:10",
                timestamp_end="00:25",
                original_quote="Eating lemons melts fat instantly.",
                claim_text="Lemons burn adipose tissue directly.",
                claim_type="Scientific",
                veracity="False",
                confidence_score=0.98,
                is_fallacious=False,
                evidence_summary="Caloric deficit is required for fat metabolism; citric acid does not melt lipids.",
                sources=["https://nutrition.org"],
                counter_argument="Fat loss requires caloric deficit; lemons do not burn fat."
            ),
            ClaimVerification(
                id=2,
                timestamp_start="00:40",
                timestamp_end="00:55",
                original_quote="Drinking alkaline water cures all metabolic diseases.",
                claim_text="Alkaline water cures metabolic disease.",
                claim_type="Scientific",
                veracity="False",
                confidence_score=0.95,
                is_fallacious=True,
                fallacy_type="Pseudoscience",
                evidence_summary="Stomach acid neutralizes ingested fluids immediately.",
                sources=["https://mayoclinic.org"],
                counter_argument="Stomach acid neutralizes alkaline water on contact."
            )
        ]
    )

    script = DebunkScript(
        video_url="https://youtube.com/watch?v=sample",
        video_title="Diet Myths Debunked",
        language="en",
        persona="skeptic",
        hook="Ready to uncover the truth behind trending nutrition myths? Let's dive in.",
        segments=[
            ScriptSegment(
                segment_id=1,
                claim_id=1,
                timestamp_start="00:10",
                timestamp_end="00:25",
                speaker_quote="Eating lemons melts fat instantly.",
                rebuttal_text="Lemons have vitamin C, but they don't dissolve adipose tissue. Only a calorie deficit does that.",
                visual_cue="Display 'FALSE' badge",
                duration_seconds=5.0
            ),
            ScriptSegment(
                segment_id=2,
                claim_id=2,
                timestamp_start="00:40",
                timestamp_end="00:55",
                speaker_quote="Drinking alkaline water cures all metabolic diseases.",
                rebuttal_text="Your stomach pH is between 1.5 and 3.5. Any alkaline water is neutralized the second it hits your stomach.",
                visual_cue="Display 'FALSE' badge with Stomach Acid graphic",
                duration_seconds=6.0
            )
        ],
        outro="Stick to evidence-based nutrition and don't fall for miracle shortcuts."
    )

    timeline = sync_timeline(report, script, mode="interleaved")

    assert isinstance(timeline, TimelineSheet)
    assert timeline.total_duration_seconds > 0
    # Expected events: 1 (intro) + 2 * 2 (claim clip + rebuttal) + 1 (outro) = 6 events
    assert len(timeline.events) == 6

    # Verify event types in order
    expected_types = [
        "intro",
        "original_claim", "debunk_rebuttal",
        "original_claim", "debunk_rebuttal",
        "outro"
    ]
    for ev, exp_type in zip(timeline.events, expected_types):
        assert ev.event_type == exp_type

    # Verify timeline continuity: start of each event matches end of previous event
    prev_end = 0.0
    for ev in timeline.events:
        assert abs(ev.start_seconds - prev_end) < 0.01
        assert ev.end_seconds > ev.start_seconds
        assert ev.duration_seconds > 0
        prev_end = ev.end_seconds

    assert abs(timeline.total_duration_seconds - prev_end) < 0.01

    # Verify Markdown export
    md = timeline.to_markdown()
    assert "# AI Debunker Studio: Synchronized Timeline Sheet" in md
    assert "Studio Hook & Introduction" in md
    assert "Original Claim #1" in md
    assert "Debunker Rebuttal: Claim #1 (False)" in md

    # Verify JSON export and roundtrip
    json_str = timeline.to_json()
    assert '"total_duration_seconds":' in json_str
    loaded = TimelineSheet.from_json_string(json_str)
    assert len(loaded.events) == 6

    # Verify saving to disk
    j_file = tmp_path / "timeline.json"
    m_file = tmp_path / "timeline.md"
    timeline.save(json_path=str(j_file), md_path=str(m_file))
    assert j_file.exists()
    assert m_file.exists()
