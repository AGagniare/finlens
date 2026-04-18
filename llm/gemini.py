"""Gemini API client for FinLens. No Gradio imports here."""
from __future__ import annotations

import io
from typing import Generator

from google import genai
from google.genai import types

from prompts import SUMMARISE_PROMPT, QA_SYSTEM_PROMPT

# Maps local file path → Gemini Files API URI to avoid re-uploading the same PDF
# during a single server session. Note: keyed by raw path string; assumes Gradio
# supplies a consistent absolute tmp path per uploaded file within a session.
_file_cache: dict[str, str] = {}

_MODEL = "gemini-1.5-flash-latest"


def _get_or_upload(client: genai.Client, pdf_path: str) -> str:
    """Return the Gemini Files API URI for pdf_path, uploading if not cached.

    Reads the file as bytes to avoid ASCII encoding errors on filenames
    that contain non-ASCII characters (e.g. Japanese filenames).
    """
    if pdf_path not in _file_cache:
        with open(pdf_path, "rb") as f:
            data = io.BytesIO(f.read())
        uploaded = client.files.upload(
            file=data,
            config=types.UploadFileConfig(mime_type="application/pdf"),
        )
        _file_cache[pdf_path] = uploaded.uri
    return _file_cache[pdf_path]


def summarise(pdf_path: str, api_key: str) -> Generator[str, None, None]:
    """Upload PDF to Gemini Files API and stream a structured summary."""
    client = genai.Client(api_key=api_key)
    file_uri = _get_or_upload(client, pdf_path)
    config = types.GenerateContentConfig(system_instruction=SUMMARISE_PROMPT)
    response = client.models.generate_content_stream(
        model=_MODEL,
        contents=[types.Part.from_uri(file_uri=file_uri, mime_type="application/pdf")],
        config=config,
    )
    for chunk in response:
        yield chunk.text


def ask(
    pdf_path: str,
    history: list[dict],
    question: str,
    api_key: str,
) -> Generator[str, None, None]:
    """Stream an answer to a question about the uploaded PDF."""
    client = genai.Client(api_key=api_key)
    file_uri = _get_or_upload(client, pdf_path)

    # Build conversation contents: history turns + current question with PDF attached
    contents: list[types.Content] = []
    for turn in history:
        role = "user" if turn["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=turn["content"])]))

    contents.append(types.Content(
        role="user",
        parts=[
            types.Part.from_uri(file_uri=file_uri, mime_type="application/pdf"),
            types.Part.from_text(text=question),
        ],
    ))

    config = types.GenerateContentConfig(system_instruction=QA_SYSTEM_PROMPT)
    response = client.models.generate_content_stream(
        model=_MODEL,
        contents=contents,
        config=config,
    )
    for chunk in response:
        yield chunk.text
