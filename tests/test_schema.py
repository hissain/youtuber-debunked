import pytest
from ytdebunk.schema import (
    ClaimType,
    VeracityRating,
    FallacyType,
    ClaimVerification,
    DebunkReport,
    PersonaType,
    ScriptSegment,
    DebunkScript,
    TimelineEvent,
    TimelineSheet
)

def test_claim_verification_model():
    claim = ClaimVerification(
        id=1,
        timestamp_start="01:20",
        timestamp_end="01:35",
        original_quote="The moon is made of green cheese.",
        claim_text="The moon consists of cheese.",
        claim_type=ClaimType.SCIENTIFIC.value,
        veracity=VeracityRating.FALSE.value,
        confidence_score=0.99,
        is_fallacious=False,
        evidence_summary="Apollo samples confirm rock and regolith composition.",
        sources=["https://nasa.gov/moon-rocks"],
        counter_argument="Physical samples from Apollo missions prove the moon is made of silicate rock."
    )
    assert claim.id == 1
    assert claim.veracity == "False"
    assert claim.confidence_score == 0.99
    assert len(claim.sources) == 1

def test_claim_verification_confidence_bounds():
    with pytest.raises(Exception):
        ClaimVerification(
            id=2,
            original_quote="Test",
            claim_text="Test",
            evidence_summary="Test",
            confidence_score=1.5  # must be <= 1.0
        )

def test_debunk_report_markdown_and_json(tmp_path):
    report = DebunkReport(
        video_url="https://youtube.com/watch?v=abc12345",
        video_title="Astrology vs Astronomy",
        language="en",
        summary="The video conflates astronomy with astrological claims without empirical grounding.",
        overall_veracity_score=25.0,
        claims=[
            ClaimVerification(
                id=1,
                timestamp_start="00:15",
                timestamp_end="00:45",
                original_quote="Planets dictate human personalities directly.",
                claim_text="Planetary positions determine personality traits.",
                claim_type=ClaimType.FACTUAL.value,
                veracity=VeracityRating.FALSE.value,
                confidence_score=0.95,
                is_fallacious=True,
                fallacy_type=FallacyType.POST_HOC.value,
                fallacy_explanation="Correlation assumed without causal mechanism.",
                evidence_summary="Extensive double-blind psychological trials show no correlation.",
                sources=["https://nature.com/articles/sample"],
                counter_argument="Double-blind tests consistently fail to show any astrological effects."
            )
        ],
        fallacies_found=["Post Hoc (False Cause)"]
    )

    # Test JSON serialization and deserialization
    json_str = report.to_json()
    assert '"overall_veracity_score": 25.0' in json_str
    assert '"Post Hoc (False Cause)"' in json_str

    loaded = DebunkReport.from_json_string(json_str)
    assert loaded.video_title == "Astrology vs Astronomy"
    assert len(loaded.claims) == 1
    assert loaded.claims[0].id == 1

    # Test Markdown generation
    md_str = report.to_markdown()
    assert "# AI Debunk Studio Report: Astrology vs Astronomy" in md_str
    assert "**25.0%**" in md_str
    assert "Claims & Veracity Breakdown" in md_str
    assert "https://nature.com/articles/sample" in md_str

    # Test saving to disk
    json_file = tmp_path / "report.json"
    md_file = tmp_path / "report.md"
    report.save(json_path=str(json_file), md_path=str(md_file))
    assert json_file.exists()
    assert md_file.exists()

def test_from_json_string_with_code_fences():
    raw_llm_output = """```json
    {
      "language": "en",
      "summary": "Sample summary",
      "overall_veracity_score": 50.0,
      "claims": [],
      "fallacies_found": [],
      "created_at": "2026-11-16T12:00:00Z"
    }
    ```"""
    report = DebunkReport.from_json_string(raw_llm_output)
    assert report.summary == "Sample summary"
    assert report.overall_veracity_score == 50.0

def test_debunk_script_schema_and_narration():
    script = DebunkScript(
        video_url="https://youtube.com/watch?v=sample",
        video_title="Sample Title",
        language="en",
        persona=PersonaType.SKEPTIC.value,
        hook="Opening hook.",
        segments=[
            ScriptSegment(
                segment_id=1,
                claim_id=1,
                rebuttal_text="Rebuttal point 1.",
                visual_cue="Visual cue 1"
            ),
            ScriptSegment(
                segment_id=2,
                claim_id=2,
                rebuttal_text="Rebuttal point 2.",
                visual_cue="Visual cue 2"
            )
        ],
        outro="Closing outro."
    )
    narration = script.get_full_narration()
    assert "Opening hook." in narration
    assert "Rebuttal point 1." in narration
    assert "Rebuttal point 2." in narration
    assert "Closing outro." in narration

def test_debunk_script_from_json_code_fences():
    raw_json = """```json
    {
      "language": "bn",
      "persona": "journalist",
      "hook": "অনুসন্ধানী প্রতিবেদন",
      "segments": [],
      "outro": "ধন্যবাদ"
    }
    ```"""
    script = DebunkScript.from_json_string(raw_json)
    assert script.language == "bn"
    assert script.persona == "journalist"
    assert script.hook == "অনুসন্ধানী প্রতিবেদন"

def test_timeline_sheet_schema():
    event = TimelineEvent(
        event_id=1,
        claim_id=1,
        event_type="debunk_rebuttal",
        title="Debunk Claim 1",
        start_seconds=0.0,
        end_seconds=10.5,
        timestamp_start="00:00",
        timestamp_end="00:10",
        duration_seconds=10.5,
        text="Sample rebuttal text",
        veracity="False"
    )
    sheet = TimelineSheet(
        video_url="https://youtube.com/watch?v=test",
        language="en",
        total_duration_seconds=10.5,
        events=[event]
    )
    md = sheet.to_markdown()
    assert "| 1 | 00:00 - 00:10 | `debunk_rebuttal` | Debunk Claim 1 | False | 10.5s |" in md
    
    js = sheet.to_json()
    loaded = TimelineSheet.from_json_string(js)
    assert len(loaded.events) == 1
    assert loaded.events[0].title == "Debunk Claim 1"
