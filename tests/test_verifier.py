import os
import sys
from unittest.mock import patch, MagicMock
import pytest
from ytdebunk.verifier import search_ddg, ground_evidence_for_text, verify_claims
from ytdebunk.schema import DebunkReport
from ytdebunk.ytdebunk import main

def test_verify_claims_missing_token(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Gemini API key is required"):
        verify_claims("Some transcription text", key=None)

@patch("ytdebunk.verifier.DDGS")
def test_search_ddg_mock(mock_ddgs_cls):
    mock_instance = MagicMock()
    mock_instance.text.return_value = [
        {"title": "Fact Check Title", "href": "https://factcheck.org/sample", "body": "Snippet text"}
    ]
    mock_ddgs_cls.return_value.__enter__.return_value = mock_instance

    results = search_ddg("Earth spherical shape")
    assert len(results) == 1
    assert results[0]["title"] == "Fact Check Title"
    assert results[0]["href"] == "https://factcheck.org/sample"

@patch("ytdebunk.verifier.search_ddg")
def test_ground_evidence_for_text(mock_search):
    mock_search.return_value = [
        {"title": "Evidence", "href": "https://example.com", "snippet": "Sample evidence snippet."}
    ]
    text = "The earth is stationary and flat. The sun circles above the disk. Gravity does not exist."
    evidence = ground_evidence_for_text(text, language="en", max_queries=2)
    assert len(evidence) >= 1
    assert mock_search.called

@patch("google.genai.Client")
def test_verify_claims_with_genai_client(mock_client_cls, tmp_path):
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = """```json
    {
      "language": "en",
      "summary": "The transcript makes unscientific claims about planetary physics.",
      "overall_veracity_score": 10.0,
      "claims": [
        {
          "id": 1,
          "timestamp_start": "00:05",
          "timestamp_end": "00:20",
          "original_quote": "Gravity is just buoyancy.",
          "claim_text": "Gravity does not exist and is merely buoyancy.",
          "claim_type": "Scientific",
          "veracity": "False",
          "confidence_score": 0.98,
          "is_fallacious": true,
          "fallacy_type": "False Equivalence",
          "fallacy_explanation": "Buoyancy requires gravitational acceleration to function.",
          "evidence_summary": "General relativity and Newtonian mechanics prove gravity is a fundamental interaction.",
          "sources": ["https://physics.nist.gov"],
          "counter_argument": "Buoyancy is itself caused by gravitational pressure gradients."
        }
      ],
      "fallacies_found": ["False Equivalence"],
      "created_at": "2026-11-16T12:00:00Z"
    }
    ```"""
    mock_client.models.generate_content.return_value = mock_resp
    mock_client_cls.return_value = mock_client

    report = verify_claims(
        transcription="Gravity is just buoyancy.",
        key="TEST_API_TOKEN",
        enable_web_search=False
    )
    assert isinstance(report, DebunkReport)
    assert report.overall_veracity_score == 10.0
    assert len(report.claims) == 1
    assert report.claims[0].veracity == "False"
    assert "False Equivalence" in report.fallacies_found

@patch("ytdebunk.ytdebunk.extract_subtitles")
@patch("ytdebunk.ytdebunk.verify_claims")
def test_cli_verify_flag_generates_report(mock_verify, mock_extract, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GENAI_API_KEY", raising=False)
    
    mock_extract.return_value = ([{"start": 0, "end": 5, "text": "Claim statement"}], "Claim statement")
    mock_report = MagicMock()
    mock_report.overall_veracity_score = 42.0
    mock_report.to_json.return_value = '{"overall_veracity_score": 42.0}'
    mock_report.to_markdown.return_value = '# Report\nScore: 42.0%'
    mock_verify.return_value = mock_report

    monkeypatch.setattr(sys, "argv", ["ytdebunk", "https://youtube.com/watch?v=123", "-c", "-t", "KEY_999"])
    res = main()
    
    assert mock_verify.called
    assert res.report == mock_report
    # Also verify backward-compatible 2-tuple unpacking
    t, f = res
    assert t == "Claim statement"
