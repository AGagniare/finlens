# FinLens Compare Tab — Design Spec

## Goal

Add a third tab to FinLens that accepts two financial PDFs, auto-detects both company names, and produces a structured competitor comparison in English — a financial snapshot table followed by a narrative analysis and a verdict. Demonstrates multi-document LLM reasoning for Arthur Gagniare's data analyst portfolio.

## Architecture

One new test file; three existing files each get one addition:

- **`prompts.py`** — add `COMPARE_PROMPT` constant
- **`llm/gemini.py`** — add `compare(pdf_path_a, pdf_path_b, api_key)` generator
- **`app.py`** — add "⚖️ Compare" tab
- **`tests/test_compare.py`** — 3 mocked tests for the new function

## LLM Approach

Single Gemini call with both PDFs. Both files are uploaded to the Gemini Files API (reusing the existing `_get_or_upload` helper and `_file_cache`), then passed together in one `generate_content_stream` call. Gemini reads both documents and produces the full comparison in one streaming response. Output is always in English regardless of the source document languages.

## `prompts.py` — COMPARE_PROMPT

Instructs Gemini to:
1. Auto-detect both company names and report periods from the documents
2. Produce the structured output below
3. Respond entirely in English
4. Only use information present in the documents; say "Not disclosed" for missing metrics

Output structure:
```
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
Narrative comparing strengths and weaknesses: financials, risk profile, outlook.

## ⚖️ Verdict
One paragraph — which company is in a stronger position and why.
```

## `llm/gemini.py` — compare()

```python
def compare(pdf_path_a: str, pdf_path_b: str, api_key: str) -> Generator[str, None, None]:
    """Upload two PDFs and stream a structured competitor comparison."""
```

- Creates one `genai.Client(api_key=api_key)`
- Calls `_get_or_upload(client, pdf_path_a)` and `_get_or_upload(client, pdf_path_b)` to get both URIs
- Builds `contents` with both `Part.from_uri(...)` parts plus the compare prompt
- Calls `client.models.generate_content_stream(model=_MODEL, contents=contents, config=config)`
- Yields non-None `chunk.text` values

## `app.py` — Compare Tab

Layout:
- **Top row**: two equal columns — left is "Company A" `gr.File`, right is "Company B" `gr.File`, both `file_types=[".pdf"]`
- **Compare button**: full-width `gr.Button("Compare", variant="primary")` below the uploads
- **Output**: `gr.Markdown` streaming the comparison below the button

Event handler `run_compare(pdf_a, pdf_b)`:
- `gr.Warning` if API key missing (with aistudio link)
- `gr.Warning("Please upload both PDFs first.")` if either file is None
- Accumulates chunks and yields growing string (same pattern as `run_summarise`)
- `gr.Warning(f"Gemini API error: {exc}")` on exception

## `tests/test_compare.py`

3 mocked tests using `@patch("llm.gemini.genai")` and `patch("builtins.open", mock_open(read_data=b""))`:

- `test_compare_yields_strings` — returns streamed chunks
- `test_compare_uploads_both_pdfs` — `files.upload` called twice for two different paths
- `test_compare_configures_api_key` — `genai.Client` called with correct key

## Error Handling

| Situation | Behaviour |
|-----------|-----------|
| API key missing | `gr.Warning` with aistudio.google.com link |
| One or both PDFs missing | `gr.Warning("Please upload both PDFs first.")` |
| Gemini API error | `gr.Warning(f"Gemini API error: {exc}")` |
| Metric not in document | Gemini instructed to write "Not disclosed" in table cell |

## Testing

No real API calls. All tests mock `google.genai` and `builtins.open`. The `autouse` `clear_file_cache` fixture from `test_gemini.py` is not shared — `test_compare.py` defines its own fixture.
