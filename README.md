# FinLens — Financial Report Analyst

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Gradio](https://img.shields.io/badge/Gradio-4.0%2B-orange)
![Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash-green)

Analyse financial PDFs in seconds. Upload any Japanese 決算短信, English 10-K, earnings release, or analyst report — FinLens auto-detects the language and responds in kind.

**Live demo:** _(Hugging Face Spaces link — coming soon)_

## Features

- **Summarise tab** — structured five-section summary (Company, Financials, Risks, Outlook, Notable Items)
- **Q&A tab** — multi-turn chat grounded in the document; will not hallucinate outside it
- **Multilingual** — Japanese and English PDFs supported; response language matches document language
- **Free tier** — powered by Google Gemini 1.5 Flash (1,500 requests/day via Google AI Studio)

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/arthurgagniare/finlens.git
   cd finlens
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com/) and add it to `.env`:
   ```bash
   cp .env.example .env
   # edit .env and paste your key
   ```

4. Run:
   ```bash
   python app.py
   ```

## Usage

### Summarise tab
1. Upload a financial PDF (`.pdf` only)
2. Click **Analyse**
3. Read the structured summary streamed on the right

### Q&A tab
1. Upload a PDF
2. Type a question in the box — examples:
   - `What was the net profit margin?`
   - `純利益はいくらですか？`
   - `What risks does management highlight?`
3. Click **Ask** or press Enter; upload a new PDF to reset the chat

## Project Structure

```
finlens/
├── app.py            # Gradio UI
├── llm/
│   └── gemini.py     # Gemini API client
├── prompts.py        # System prompt constants
├── tests/
│   ├── test_prompts.py
│   └── test_gemini.py
├── requirements.txt
└── .env.example
```

## Author

Arthur Gagniare — [linkedin.com/in/arthurgagniare](https://linkedin.com/in/arthurgagniare)
