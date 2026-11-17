import pytest
from ytdebunk.chunker import chunk_text

def test_chunk_empty_and_whitespace():
    assert chunk_text("") == []
    assert chunk_text("   ") == []

def test_chunk_short_text():
    text = "Hello world! This is a short statement."
    chunks = chunk_text(text, max_chars=100)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_chunk_bengali_sentences():
    text = "প্রথম বাক্য। দ্বিতীয় বাক্য। তৃতীয় বাক্য। চতুর্থ বাক্য।"
    chunks = chunk_text(text, max_chars=30)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 30
        assert "বাক্য" in c

def test_chunk_english_sentences():
    text = "First sentence. Second sentence! Third sentence? Fourth sentence."
    chunks = chunk_text(text, max_chars=35)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 35
    reconstructed = " ".join(chunks)
    assert "First sentence." in reconstructed
    assert "Fourth sentence." in reconstructed

def test_chunk_long_continuous_text_without_punctuation():
    # Long text with spaces but no punctuation
    words = ["word" + str(i) for i in range(100)]
    text = " ".join(words)
    chunks = chunk_text(text, max_chars=50)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 50

def test_chunk_giant_word():
    # Word larger than max_chars
    giant_word = "A" * 120
    chunks = chunk_text(giant_word, max_chars=50)
    assert len(chunks) == 3
    assert len(chunks[0]) == 50
    assert len(chunks[1]) == 50
    assert len(chunks[2]) == 20
