from prompts import SUMMARISE_PROMPT, QA_SYSTEM_PROMPT


def test_summarise_prompt_has_section_headers():
    for header in ["Company", "Financials", "Risks", "Outlook", "Notable"]:
        assert header in SUMMARISE_PROMPT, f"Missing section: {header}"


def test_summarise_prompt_instructs_language_match():
    assert "language" in SUMMARISE_PROMPT.lower()


def test_summarise_prompt_has_emoji_markers():
    for emoji in ["📌", "💹", "⚠️", "🔭", "📝"]:
        assert emoji in SUMMARISE_PROMPT, f"Missing emoji: {emoji}"


def test_qa_prompt_instructs_document_only():
    text = QA_SYSTEM_PROMPT.lower()
    assert "document" in text


def test_qa_prompt_handles_missing_answer():
    # Must instruct model to explicitly say so when an answer is absent from the document
    assert "couldn't find" in QA_SYSTEM_PROMPT.lower() or "not found in the document" in QA_SYSTEM_PROMPT.lower()


def test_qa_prompt_instructs_language_match():
    assert "language" in QA_SYSTEM_PROMPT.lower()
