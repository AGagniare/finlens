# Compare Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a third "⚖️ Compare" tab that accepts two financial PDFs and streams a structured competitor comparison (table + narrative + verdict) always in English.

**Architecture:** Single Gemini call with both PDFs uploaded via the existing `_get_or_upload` helper. A new `compare()` generator in `llm/gemini.py` mirrors the shape of `summarise()`. The Gradio tab accumulates streamed chunks into a growing Markdown string (same pattern as Tab 1).

**Tech Stack:** Python, Gradio, google-genai SDK (`genai.Client`, `types.Part.from_uri`, `generate_content_stream`), pytest + `unittest.mock`

---

## File Map

| File | Change |
|------|--------|
| `prompts.py` | Add `COMPARE_PROMPT` constant |
| `llm/gemini.py` | Add `compare(pdf_path_a, pdf_path_b, api_key)` generator; add `COMPARE_PROMPT` to import |
| `app.py` | Add `compare` to import; add `run_compare` handler; add `compare_tab` block; extend `TabbedInterface` |
| `tests/test_compare.py` | New file — 3 mocked tests |

---

### Task 1: COMPARE_PROMPT

**Files:**
- Modify: `prompts.py`

- [ ] **Step 1: Add COMPARE_PROMPT to prompts.py**

Append this constant after `QA_SYSTEM_PROMPT`:

```python
COMPARE_PROMPT = """\
You are a senior financial analyst. You have been given two financial reports.

Auto-detect the company name and reporting period from each document.

Respond ENTIRELY in English regardless of the source document languages.

Only use information present in the documents. If a metric is not disclosed, \
write "Not disclosed" in the table cell.

Return exactly this structure:

## 🏢 Companies Compared
[Company A] vs [Company B] | [Period A] · [Period B]

## 📊 Financial Snapshot
| Metric | [Company A] | [Company B] |
|--------|-------------|-------------|
| Revenue | | |
| Operating Profit | | |
| Net Profit | | |
| Operating Margin | | |
| YoY Revenue Growth | | |

## 📈 Performance Analysis
Compare strengths and weaknesses across financials, risk profile, and outlook.

## ⚖️ Verdict
One paragraph — which company is in a stronger financial position and why.
"""
```

- [ ] **Step 2: Commit**

```bash
git add prompts.py
git commit -m "feat: add COMPARE_PROMPT constant"
```

---

### Task 2: compare() function + tests (TDD)

**Files:**
- Create: `tests/test_compare.py`
- Modify: `llm/gemini.py` (add import + function)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_compare.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/arthur/finlens && python -m pytest tests/test_compare.py -v
```

Expected: `ImportError: cannot import name 'compare' from 'llm.gemini'`

- [ ] **Step 3: Add compare() to llm/gemini.py**

In `llm/gemini.py`, update the import line at the top:

```python
from prompts import SUMMARISE_PROMPT, QA_SYSTEM_PROMPT, COMPARE_PROMPT
```

Then append `compare()` after the `ask()` function:

```python
def compare(pdf_path_a: str, pdf_path_b: str, api_key: str) -> Generator[str, None, None]:
    """Upload two PDFs and stream a structured competitor comparison."""
    client = genai.Client(api_key=api_key)
    uri_a = _get_or_upload(client, pdf_path_a)
    uri_b = _get_or_upload(client, pdf_path_b)
    contents = [
        types.Part.from_uri(file_uri=uri_a, mime_type="application/pdf"),
        types.Part.from_uri(file_uri=uri_b, mime_type="application/pdf"),
        types.Part.from_text(text=COMPARE_PROMPT),
    ]
    config = types.GenerateContentConfig()
    response = client.models.generate_content_stream(
        model=_MODEL,
        contents=contents,
        config=config,
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/arthur/finlens && python -m pytest tests/test_compare.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Run the full test suite to check for regressions**

```bash
cd /Users/arthur/finlens && python -m pytest -v
```

Expected: all tests pass (10 total: 7 from test_gemini.py + 3 from test_compare.py)

- [ ] **Step 6: Commit**

```bash
git add llm/gemini.py tests/test_compare.py
git commit -m "feat: add compare() generator and tests"
```

---

### Task 3: Compare tab in app.py

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Update the import line**

In `app.py`, change line 8:

```python
from llm.gemini import summarise, ask, compare
```

- [ ] **Step 2: Add the run_compare handler and tab block**

Insert the following section between the Q&A section and the `# ── App entry point` comment:

```python
# ── Tab 3: Compare ───────────────────────────────────────────────────────────

def run_compare(pdf_a, pdf_b) -> Generator[str, None, None]:
    api_key = _get_api_key()
    if not api_key:
        gr.Warning(
            "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/ "
            "and add it to your .env file."
        )
        return

    if pdf_a is None or pdf_b is None:
        gr.Warning("Please upload both PDFs first.")
        return

    try:
        accumulated = []
        for chunk in compare(pdf_a.name, pdf_b.name, api_key=api_key):
            accumulated.append(chunk)
            yield "".join(accumulated)
    except Exception as exc:
        gr.Warning(f"Gemini API error: {exc}")


with gr.Blocks() as compare_tab:
    with gr.Row():
        with gr.Column():
            pdf_input_a = gr.File(label="Company A", file_types=[".pdf"])
        with gr.Column():
            pdf_input_b = gr.File(label="Company B", file_types=[".pdf"])
    compare_btn = gr.Button("Compare", variant="primary")
    compare_output = gr.Markdown(label="Comparison")

    compare_btn.click(
        fn=run_compare,
        inputs=[pdf_input_a, pdf_input_b],
        outputs=[compare_output],
    )
```

- [ ] **Step 3: Extend TabbedInterface**

Replace the existing `demo = gr.TabbedInterface(...)` block with:

```python
demo = gr.TabbedInterface(
    [summarise_tab, qa_tab, compare_tab],
    tab_names=["📊 Summarise", "💬 Q&A", "⚖️ Compare"],
    title="FinLens — Financial Report Analyst",
)
```

- [ ] **Step 4: Verify the app starts without errors**

```bash
cd /Users/arthur/finlens && python app.py
```

Expected: Gradio app starts, prints a local URL, no import errors or tracebacks.

Stop the server with Ctrl+C once it starts cleanly.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: add Compare tab to FinLens UI"
```
