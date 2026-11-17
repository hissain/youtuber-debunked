from unittest.mock import patch, MagicMock
import pytest
from ytdebunk.refiner import enhance_transcription
from ytdebunk.philosopher import detect_logical_faults

def test_enhance_transcription_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Gemini API key is required"):
        enhance_transcription("Some text", key=None)

def test_detect_logical_faults_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Gemini API key is required"):
        detect_logical_faults("Some text", key=None)

@patch("google.generativeai.configure")
@patch("google.generativeai.GenerativeModel")
def test_enhance_transcription_success(mock_model_cls, mock_configure):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Enhanced text"
    mock_model.generate_content.return_value = mock_response
    mock_model_cls.return_value = mock_model

    result = enhance_transcription("Some text.", key="TEST_KEY_ABC")
    mock_configure.assert_called_with(api_key="TEST_KEY_ABC")
    assert result == "Enhanced text"

@patch("google.generativeai.configure")
@patch("google.generativeai.GenerativeModel")
def test_detect_logical_faults_success(mock_model_cls, mock_configure):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Detected faults"
    mock_model.generate_content.return_value = mock_response
    mock_model_cls.return_value = mock_model

    result = detect_logical_faults("Some text.", key="TEST_KEY_XYZ")
    mock_configure.assert_called_with(api_key="TEST_KEY_XYZ")
    assert result == "Detected faults"
