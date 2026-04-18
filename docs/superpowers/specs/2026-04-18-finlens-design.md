# FinLens — Design Spec

## Goal

A polished, deployable Gradio app that analyses financial reports using Google Gemini 1.5 Flash. Accepts any financial PDF (Japanese 決算短信, English 10-K, earnings releases, analyst reports), auto-detects the document language, and responds in kind. Two modes: structured summarisation and multi-turn Q&A. Demonstrates LLM API integration, multilingual document understanding, and financial domain knowledge for Arthur Gagniare's data analyst portfolio targeting Tokyo roles.

## Architecture

Three clean layers:

- **`prompts.py`** — system prompts for both modes; no I/O
- **`llm/gemini.py`** — Gemini API client: `summarise(pdf_path)` and `ask(pdf_path, history, question)`
- **`app.py`** — Gradio layout, two tabs, wires layers together; no LLM logic

```
finlens/
├── app.py
├── llm/
│   ├── __init__.py
│   └── gemini.py
├── prompts.py
├── tests/
│   ├── __init__.py
│   ├── test_prompts.py
│   └── test_gemini.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Tech Stack

Python 3.10+, Gradio ≥4.0, google-generativeai ≥0.7, python-dotenv ≥1.0, pytest ≥8.0

## LLM Backend — Google Gemini

- **Model:** `gemini-1.5-flash` (free tier: 1,500 req/day via Google AI Studio)
- **API key:** read from `.env` as `GEMINI_API_KEY`; on Hugging Face Spaces set as a Space secret
- **PDF handling:** uploaded directly to Gemini Files API (no local text extraction); files auto-deleted after 48h
- **Language:** Gemini auto-detects document language; system prompt instructs it to respond in the same language as the document

## Gradio Layout

- `gr.TabbedInterface` with two tabs, side-by-side layout (upload column left, output column right)
- No custom CSS beyond Gradio defaults

## Tab 1 — Summarise

**Left column:**
- `gr.File` — PDF upload, accepts `.pdf` only
- `gr.Button("Analyse")` — triggers summarisation

**Right column:**
- `gr.Markdown` — streams the structured summary

**Output format** (Gemini instructed to return this structure):
```
## 📌 Company & Report
## 💹 Key Financials
## ⚠️ Key Risks
## 🔭 Outlook
## 📝 Notable Items
```

Language of output matches language of the PDF.

## Tab 2 — Q&A

**Left column:**
- `gr.File` — PDF upload, accepts `.pdf` only (cleared on new upload resets chat)

**Right column:**
- `gr.Chatbot` — multi-turn chat display
- `gr.Textbox` — user question input with placeholder examples in both languages
- `gr.Button("Ask")` — submits question

Chat history maintained within the Gradio session state. Uploading a new PDF clears the history. System prompt instructs Gemini to answer only from the document and to say so if the answer is not found.

## `llm/gemini.py`

```python
def summarise(pdf_path: str, api_key: str) -> Generator[str, None, None]:
    """Upload PDF to Gemini Files API and stream a structured summary."""

def ask(pdf_path: str, history: list[dict], question: str, api_key: str) -> Generator[str, None, None]:
    """Upload PDF (or reuse cached file handle) and stream an answer."""
```

Both functions yield text chunks for Gradio streaming. `pdf_path` is the local temp path Gradio provides after upload.

## `prompts.py`

Two prompt constants:

- `SUMMARISE_PROMPT` — instructs Gemini to produce the five-section structured summary, detect language, respond in document language
- `QA_SYSTEM_PROMPT` — instructs Gemini to answer from the document only, cite sections where possible, respond in document language, and say "I couldn't find that in the document" if the answer is absent

## Error Handling

- No API key → `gr.Warning` shown with link to aistudio.google.com, no crash
- Gemini API error (rate limit, timeout, quota) → `gr.Warning` with the error message
- Non-PDF upload → Gradio's `file_types=[".pdf"]` rejects it before the API is called
- Unreadable / image-only scan → Gemini returns a graceful message, surfaced as-is in the output

## Testing

- `tests/test_prompts.py` — assert prompt strings contain required keywords and section headers
- `tests/test_gemini.py` — mock `google.generativeai` client; assert `summarise()` yields strings; assert `ask()` yields strings and accepts history

No real API calls in tests.

## Deployment

Hugging Face Spaces — free Gradio hosting. Push repo to GitHub, create a Space linked to the repo, add `GEMINI_API_KEY` as a Space secret. Entry point: `app.py`.

## README

Includes: title + description, live demo link placeholder, screenshot placeholder, shields.io badges (Python, Gradio, Gemini), setup instructions, usage guide, example queries in English and Japanese, project structure, author (Arthur Gagniare — linkedin.com/in/arthurgagniare).
