"""Gemini API client for FinLens. No Gradio imports here."""
from __future__ import annotations

from typing import Generator

import google.generativeai as genai

from prompts import SUMMARISE_PROMPT, QA_SYSTEM_PROMPT

# Maps local file path → Gemini Files API URI to avoid re-uploading the same PDF
# during a single server session.
_file_cache: dict[str, str] = {}

_MODEL = "gemini-1.5-flash"


def _get_or_upload(pdf_path: str) -> str:
    """Return the Gemini Files API URI for pdf_path, uploading if not cached."""
    if pdf_path not in _file_cache:
        uploaded = genai.upload_file(pdf_path, mime_type="application/pdf")
        _file_cache[pdf_path] = uploaded.uri
    return _file_cache[pdf_path]


def summarise(pdf_path: str, api_key: str) -> Generator[str, None, None]:
    """Upload PDF to Gemini Files API and stream a structured summary."""
    genai.configure(api_key=api_key)
    file_uri = _get_or_upload(pdf_path)
    model = genai.GenerativeModel(_MODEL, system_instruction=SUMMARISE_PROMPT)
    response = model.generate_content(
        [{"file_data": {"file_uri": file_uri, "mime_type": "application/pdf"}}],
        stream=True,
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
    genai.configure(api_key=api_key)
    file_uri = _get_or_upload(pdf_path)

    # Build conversation contents: history + current question with the PDF attached
    contents = []
    for turn in history:
        role = "user" if turn["role"] == "user" else "model"
        contents.append({"role": role, "parts": [turn["content"]]})

    contents.append({
        "role": "user",
        "parts": [
            {"file_data": {"file_uri": file_uri, "mime_type": "application/pdf"}},
            question,
        ],
    })

    model = genai.GenerativeModel(_MODEL, system_instruction=QA_SYSTEM_PROMPT)
    response = model.generate_content(contents, stream=True)
    for chunk in response:
        yield chunk.text
