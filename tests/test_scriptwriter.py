import os
import pytest
from unittest.mock import patch, MagicMock
from ytdebunk.schema import (
    DebunkReport,
    ClaimVerification,
    DebunkScript,
    ScriptSegment,
    PersonaType,
    VeracityRating,
    ClaimType
)
from ytdebunk.scriptwriter import (
    generate_debunk_script,
    _generate_template_fallback_script,
    PERSONA_PROFILES
)

@pytest.fixture
def sample_report():
    return DebunkReport(
        video_url="https://youtube.com/watch?v=sample123",
        video_title="Perpetual Motion Machine Debunked",
        language="en",
        summary="The video claims a self-running magnet motor generates free energy violating thermodynamics.",
        overall_veracity_score=15.0,
        claims=[
            ClaimVerification(
                id=1,
                timestamp_start="00:15",
                timestamp_end="00:45",
                original_quote="This neodymium wheel runs forever without input power.",
                claim_text="Neodymium magnet arrangement creates perpetual mechanical energy.",
                claim_type=ClaimType.SCIENTIFIC.value,
                veracity=VeracityRating.FALSE.value,
                confidence_score=0.99,
                is_fallacious=True,
                fallacy_type="Violation of Conservation of Energy",
                evidence_summary="First and second laws of thermodynamics prove energy cannot be created from nothing.",
                sources=["https://physics.nist.gov"],
                counter_argument="Magnetic fields store potential energy but do not generate net work in a closed cycle."
            ),
            ClaimVerification(
                id=2,
                timestamp_start="01:10",
                timestamp_end="01:30",
                original_quote="Power companies are hiding this technology from the public.",
                claim_text="Energy utilities actively suppress free energy devices.",
                claim_type=ClaimType.LOGICAL.value,
                veracity=VeracityRating.UNSUBSTANTIATED.value,
                confidence_score=0.90,
                is_fallacious=True,
                fallacy_type="Conspiracy Fallacy",
                evidence_summary="No working prototype has ever survived third-party laboratory testing.",
                sources=["https://wikipedia.org/wiki/Free_energy_suppression"],
                counter_argument="Patents on viable energy generation are public; none show functional over-unity motors."
            )
        ],
        fallacies_found=["Violation of Conservation of Energy", "Conspiracy Fallacy"]
    )

def test_persona_profiles_structure():
    assert "skeptic" in PERSONA_PROFILES
    assert "journalist" in PERSONA_PROFILES
    assert "educator" in PERSONA_PROFILES
    for p in ["skeptic", "journalist", "educator"]:
        assert "en_style" in PERSONA_PROFILES[p]
        assert "bn_style" in PERSONA_PROFILES[p]
        assert "name" in PERSONA_PROFILES[p]

def test_template_fallback_skeptic_en(sample_report):
    script = _generate_template_fallback_script(sample_report, persona="skeptic", language="en")
    assert isinstance(script, DebunkScript)
    assert script.persona == "skeptic"
    assert "Hold on a second" in script.hook
    assert len(script.segments) == 2
    assert script.segments[0].claim_id == 1
    assert "boldly claims" in script.segments[0].rebuttal_text
    assert "extraordinary evidence" in script.outro
    assert script.full_narration is not None

def test_template_fallback_journalist_bn(sample_report):
    sample_report.language = "bn"
    script = _generate_template_fallback_script(sample_report, persona="journalist", language="bn")
    assert isinstance(script, DebunkScript)
    assert script.persona == "journalist"
    assert "বস্তুনিষ্ঠ" in script.hook or "প্রমাণের ভিত্তিতে" in script.hook
    assert len(script.segments) == 2
    assert "দাবি #" in script.segments[0].rebuttal_text

def test_template_fallback_educator_en(sample_report):
    script = _generate_template_fallback_script(sample_report, persona="educator", language="en")
    assert isinstance(script, DebunkScript)
    assert script.persona == "educator"
    assert "Welcome!" in script.hook
    assert "Critical thinking" in script.outro

def test_debunk_script_markdown_and_json(sample_report, tmp_path):
    script = _generate_template_fallback_script(sample_report, persona="skeptic", language="en")
    
    # Test JSON serialization and roundtrip
    json_data = script.to_json()
    assert '"persona": "skeptic"' in json_data
    
    loaded = DebunkScript.from_json_string(json_data)
    assert loaded.persona == "skeptic"
    assert len(loaded.segments) == 2

    # Test Markdown formatting
    md = script.to_markdown()
    assert "# Debunker Studio Script:" in md
    assert "## 🎙️ Hook (Opening)" in md
    assert "## 🎬 Rebuttal Segments" in md
    assert "## 🏁 Outro (Closing)" in md

    # Test saving to isolated directory
    json_file = tmp_path / "script.json"
    md_file = tmp_path / "script.md"
    script.save(json_path=str(json_file), md_path=str(md_file))
    assert json_file.exists()
    assert md_file.exists()

@patch("google.genai.Client")
def test_generate_debunk_script_with_gemini(mock_client_cls, sample_report):
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = """```json
    {
      "video_url": "https://youtube.com/watch?v=sample123",
      "video_title": "Perpetual Motion Machine Debunked",
      "language": "en",
      "persona": "skeptic",
      "hook": "Ever wondered why nobody has a free-energy motor in their garage? Let's talk physics.",
      "segments": [
        {
          "segment_id": 1,
          "claim_id": 1,
          "timestamp_start": "00:15",
          "timestamp_end": "00:45",
          "speaker_quote": "This neodymium wheel runs forever without input power.",
          "rebuttal_text": "If magnets alone created continuous free work, the universe's energy budget would be bankrupt.",
          "visual_cue": "Show 'FALSE' badge with Thermodynamics Citation"
        }
      ],
      "outro": "Don't invest your savings in magical motors. Science wins every single time."
    }
    ```"""
    mock_client.models.generate_content.return_value = mock_resp
    mock_client_cls.return_value = mock_client

    script = generate_debunk_script(
        report=sample_report,
        persona="skeptic",
        key="TEST_API_KEY",
        language="en"
    )

    assert isinstance(script, DebunkScript)
    assert script.persona == "skeptic"
    assert "Ever wondered" in script.hook
    assert len(script.segments) == 1
    assert "Show 'FALSE' badge" in script.segments[0].visual_cue

def test_generate_debunk_script_fallback_when_no_token(sample_report, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GENAI_API_KEY", raising=False)

    # Without token, automatically generates high-quality fallback script without errors
    script = generate_debunk_script(
        report=sample_report,
        persona="educator",
        key=None,
        language="en"
    )
    assert isinstance(script, DebunkScript)
    assert script.persona == "educator"
    assert len(script.segments) == 2
