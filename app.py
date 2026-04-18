"""FinLens — Gradio app. UI wiring only; no LLM logic here."""
import os
from typing import Generator

import gradio as gr
from dotenv import load_dotenv

from llm.gemini import summarise, ask

load_dotenv()


def _get_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY")


# ── Tab 1: Summarise ──────────────────────────────────────────────────────────

def run_summarise(pdf_file) -> Generator[str, None, None]:
    api_key = _get_api_key()
    if not api_key:
        gr.Warning(
            "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/ "
            "and add it to your .env file."
        )
        return

    if pdf_file is None:
        gr.Warning("Please upload a PDF first.")
        return

    try:
        accumulated = []
        for chunk in summarise(pdf_file.name, api_key=api_key):
            accumulated.append(chunk)
            yield "".join(accumulated)
    except Exception as exc:
        gr.Warning(f"Gemini API error: {exc}")


with gr.Blocks() as summarise_tab:
    with gr.Row():
        with gr.Column(scale=1):
            pdf_input_sum = gr.File(label="Upload PDF", file_types=[".pdf"])
            analyse_btn = gr.Button("Analyse", variant="primary")
        with gr.Column(scale=2):
            summary_output = gr.Markdown(label="Summary")

    analyse_btn.click(
        fn=run_summarise,
        inputs=[pdf_input_sum],
        outputs=[summary_output],
    )


# ── Tab 2: Q&A ────────────────────────────────────────────────────────────────

def upload_pdf_qa(pdf_file, history):
    """Clear chat history and chatbot display when a new PDF is uploaded."""
    return [], []


def run_ask(pdf_file, history, question) -> Generator:
    api_key = _get_api_key()
    if not api_key:
        gr.Warning(
            "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/ "
            "and add it to your .env file."
        )
        return

    if pdf_file is None:
        gr.Warning("Please upload a PDF first.")
        return

    if not question.strip():
        return

    try:
        answer_chunks = []
        for chunk in ask(pdf_file.name, history=history, question=question, api_key=api_key):
            answer_chunks.append(chunk)
            partial = "".join(answer_chunks)
            new_history = history + [{"role": "user", "content": question}, {"role": "assistant", "content": partial}]
            yield new_history, "", new_history
    except Exception as exc:
        gr.Warning(f"Gemini API error: {exc}")


with gr.Blocks() as qa_tab:
    with gr.Row():
        with gr.Column(scale=1):
            pdf_input_qa = gr.File(label="Upload PDF", file_types=[".pdf"])
        with gr.Column(scale=2):
            chatbot = gr.Chatbot()
            question_input = gr.Textbox(
                placeholder="What was the operating profit? / 営業利益はいくらでしたか？",
                label="Question",
            )
            ask_btn = gr.Button("Ask", variant="primary")

    chat_state = gr.State([])

    pdf_input_qa.change(
        fn=upload_pdf_qa,
        inputs=[pdf_input_qa, chat_state],
        outputs=[chat_state, chatbot],
    )

    ask_btn.click(
        fn=run_ask,
        inputs=[pdf_input_qa, chat_state, question_input],
        outputs=[chatbot, question_input, chat_state],
    )

    question_input.submit(
        fn=run_ask,
        inputs=[pdf_input_qa, chat_state, question_input],
        outputs=[chatbot, question_input, chat_state],
    )


# ── App entry point ───────────────────────────────────────────────────────────

demo = gr.TabbedInterface(
    [summarise_tab, qa_tab],
    tab_names=["📊 Summarise", "💬 Q&A"],
    title="FinLens — Financial Report Analyst",
)

if __name__ == "__main__":
    demo.launch()
