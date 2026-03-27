"""Context Summarizer — LLM-based, irreversible history compression.

Summarization is IRREVERSIBLE: converts structured history into a narrative
paragraph. Structure and detail are permanently lost. Only fires after
MAX_COMPACTIONS passes of reversible compaction have already been exhausted.

Contrast with compactor.py (reversible): that is pure Python and free.
"""

import json
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from .tools import extract_text
from . import console_logger as log


_CYCLE_SYSTEM_PROMPT = """You are a summarizer for an AI bug-fixing agent session.
Compress the provided history into a single concise paragraph (3–5 sentences).
Cover: what bugs were found and fixed, current test status, what remains to fix.
Output plain text only — no JSON, no bullet points, no markdown headers."""

_CONVERSATION_SYSTEM_PROMPT = """You are a summarizer for a software debugging conversation.
Compress the provided conversation turns into a single concise paragraph (3–5 sentences).
Cover: what errors were found, what fixes were attempted, what the current state is.
Output plain text only — no JSON, no bullet points, no markdown headers."""


def summarize(cheap_llm: BaseChatModel, compact_summary: dict | None, full_history: list) -> dict:
    """Irreversible: compress history into a narrative paragraph via LLM.

    Uses full_history (real detailed data) as the source, not compact_summary.
    Returns a dict with type='narrative_summary' wrapping the paragraph.
    """
    # Build input from full_history (the real data), not compact_summary
    history_text = json.dumps(full_history, default=str, indent=2)
    if compact_summary:
        history_text = f"Prior summary:\n{json.dumps(compact_summary, default=str)}\n\nRecent cycles:\n{history_text}"

    log.llm_thinking("summarizer", f"Summarizing {len(full_history)} cycle(s) into narrative")

    messages = [
        SystemMessage(content=_CYCLE_SYSTEM_PROMPT),
        HumanMessage(content=f"Summarize this bug-fixing session history:\n\n{history_text}"),
    ]
    response = cheap_llm.invoke(messages)
    text = extract_text(response.content).strip()

    return {"type": "narrative_summary", "content": text}


def summarize_conversation(cheap_llm: BaseChatModel, messages: list) -> str:
    """Summarize a list of LangChain messages into a plain-text paragraph.

    Used by the traditional agent to reduce its growing conversation list.
    Returns a plain string (not a dict).
    """
    conversation_text = "\n\n".join(
        f"{type(m).__name__}: {str(m.content)[:500]}"
        for m in messages
    )

    log.llm_thinking("summarizer", f"Summarizing {len(messages)} conversation turns")

    summary_messages = [
        SystemMessage(content=_CONVERSATION_SYSTEM_PROMPT),
        HumanMessage(content=f"Summarize this conversation:\n\n{conversation_text}"),
    ]
    response = cheap_llm.invoke(summary_messages)
    return extract_text(response.content).strip()
