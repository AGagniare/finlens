import types
from unittest.mock import MagicMock, patch, call
import pytest

import llm.gemini as gemini_module
from llm.gemini import summarise, ask


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_fake_file(uri: str = "files/fake-uri-123"):
    f = MagicMock()
    f.uri = uri
    return f


def _make_streaming_response(chunks: list[str]):
    """Return an iterable of mock chunk objects."""
    return [MagicMock(text=c) for c in chunks]


# ── summarise() ───────────────────────────────────────────────────────────────

@patch("llm.gemini.genai")
def test_summarise_yields_strings(mock_genai):
    fake_file = _make_fake_file()
    mock_genai.upload_file.return_value = fake_file
    mock_genai.GenerativeModel.return_value.generate_content.return_value = (
        _make_streaming_response(["Hello", " world"])
    )

    result = list(summarise("/tmp/fake.pdf", api_key="test-key"))

    assert result == ["Hello", " world"]


@patch("llm.gemini.genai")
def test_summarise_uploads_pdf(mock_genai):
    fake_file = _make_fake_file()
    mock_genai.upload_file.return_value = fake_file
    mock_genai.GenerativeModel.return_value.generate_content.return_value = (
        _make_streaming_response(["ok"])
    )

    list(summarise("/tmp/report.pdf", api_key="test-key"))

    mock_genai.upload_file.assert_called_once_with("/tmp/report.pdf", mime_type="application/pdf")


@patch("llm.gemini.genai")
def test_summarise_configures_api_key(mock_genai):
    fake_file = _make_fake_file()
    mock_genai.upload_file.return_value = fake_file
    mock_genai.GenerativeModel.return_value.generate_content.return_value = (
        _make_streaming_response(["ok"])
    )

    list(summarise("/tmp/report.pdf", api_key="my-secret-key"))

    mock_genai.configure.assert_called_once_with(api_key="my-secret-key")


# ── ask() ─────────────────────────────────────────────────────────────────────

@patch("llm.gemini.genai")
def test_ask_yields_strings(mock_genai):
    fake_file = _make_fake_file()
    mock_genai.upload_file.return_value = fake_file
    mock_genai.GenerativeModel.return_value.generate_content.return_value = (
        _make_streaming_response(["Answer"])
    )

    result = list(ask("/tmp/fake.pdf", history=[], question="What is revenue?", api_key="test-key"))

    assert result == ["Answer"]


@patch("llm.gemini.genai")
def test_ask_accepts_history(mock_genai):
    fake_file = _make_fake_file()
    mock_genai.upload_file.return_value = fake_file
    mock_genai.GenerativeModel.return_value.generate_content.return_value = (
        _make_streaming_response(["42"])
    )

    history = [
        {"role": "user", "content": "What is revenue?"},
        {"role": "assistant", "content": "¥1T"},
    ]
    result = list(ask("/tmp/fake.pdf", history=history, question="And profit?", api_key="test-key"))

    assert result == ["42"]


@patch("llm.gemini.genai")
def test_ask_caches_uploaded_file(mock_genai):
    """Same pdf_path should only be uploaded once across two ask() calls."""
    # Clear module-level cache before test
    gemini_module._file_cache.clear()

    fake_file = _make_fake_file(uri="files/cached-uri")
    mock_genai.upload_file.return_value = fake_file
    mock_genai.GenerativeModel.return_value.generate_content.return_value = (
        _make_streaming_response(["ok"])
    )

    list(ask("/tmp/same.pdf", history=[], question="Q1", api_key="test-key"))
    list(ask("/tmp/same.pdf", history=[], question="Q2", api_key="test-key"))

    assert mock_genai.upload_file.call_count == 1


@patch("llm.gemini.genai")
def test_ask_different_pdfs_uploaded_separately(mock_genai):
    gemini_module._file_cache.clear()

    fake_file = _make_fake_file()
    mock_genai.upload_file.return_value = fake_file
    mock_genai.GenerativeModel.return_value.generate_content.return_value = (
        _make_streaming_response(["ok"])
    )

    list(ask("/tmp/a.pdf", history=[], question="Q", api_key="test-key"))
    list(ask("/tmp/b.pdf", history=[], question="Q", api_key="test-key"))

    assert mock_genai.upload_file.call_count == 2
