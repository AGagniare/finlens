import pytest
from unittest.mock import MagicMock, patch, mock_open

import llm.gemini as gemini_module
from llm.gemini import compare


@pytest.fixture(autouse=True)
def clear_file_cache():
    gemini_module._file_cache.clear()
    yield
    gemini_module._file_cache.clear()


def _make_fake_file(uri: str = "files/fake-uri-123"):
    f = MagicMock()
    f.uri = uri
    return f


def _make_streaming_response(chunks: list[str]):
    return [MagicMock(text=c) for c in chunks]


def _patch_open():
    return patch("builtins.open", mock_open(read_data=b""))


@patch("llm.gemini.genai")
def test_compare_yields_strings(mock_genai):
    fake_file = _make_fake_file()
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.files.upload.return_value = fake_file
    mock_client.models.generate_content_stream.return_value = (
        _make_streaming_response(["## 🏢 Companies", " Compared\nA vs B"])
    )

    with _patch_open():
        result = list(compare("/tmp/a.pdf", "/tmp/b.pdf", api_key="test-key"))

    assert result == ["## 🏢 Companies", " Compared\nA vs B"]


@patch("llm.gemini.genai")
def test_compare_uploads_both_pdfs(mock_genai):
    fake_file_a = _make_fake_file(uri="files/uri-a")
    fake_file_b = _make_fake_file(uri="files/uri-b")
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.files.upload.side_effect = [fake_file_a, fake_file_b]
    mock_client.models.generate_content_stream.return_value = (
        _make_streaming_response(["ok"])
    )

    with _patch_open():
        list(compare("/tmp/a.pdf", "/tmp/b.pdf", api_key="test-key"))

    assert mock_client.files.upload.call_count == 2


@patch("llm.gemini.genai")
def test_compare_configures_api_key(mock_genai):
    fake_file = _make_fake_file()
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.files.upload.return_value = fake_file
    mock_client.models.generate_content_stream.return_value = (
        _make_streaming_response(["ok"])
    )

    with _patch_open():
        list(compare("/tmp/a.pdf", "/tmp/b.pdf", api_key="my-secret-key"))

    mock_genai.Client.assert_called_once_with(api_key="my-secret-key")
