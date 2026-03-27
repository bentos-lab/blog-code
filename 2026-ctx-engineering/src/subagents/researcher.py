"""Researcher sub-agent — sees only the failing test output and one bug description.

Context isolation: receives only the specific error details, NOT other files or history.
Returns a proposed fix description (not code — that's the executor's job).
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ..tools import extract_text
from .. import console_logger as log


SYSTEM_PROMPT = """You are a Python debugging researcher.
You will receive a specific bug description and the relevant test failure.
Your job: describe EXACTLY what one-line or few-line fix is needed.
Be concise. No code blocks. Just plain English like:
"In storage.py, wrap the open() call in a try/except FileNotFoundError and return []"
"""


def research(llm: BaseChatModel, bug_report: dict, test_output: str) -> str:
    """Research the fix for a specific identified bug.

    Args:
        llm: The language model to use.
        bug_report: Structured dict from analyzer sub-agent.
        test_output: The failing pytest output for context.

    Returns:
        Plain English description of the required fix.
    """
    content = (
        f"Bug identified:\n"
        f"  File: {bug_report.get('bug_file')}\n"
        f"  Function: {bug_report.get('bug_function')}\n"
        f"  Type: {bug_report.get('bug_type')}\n"
        f"  Description: {bug_report.get('description')}\n\n"
        f"Relevant test failure:\n```\n{test_output[:2000]}\n```\n\n"
        f"Describe exactly what needs to change to fix this bug:"
    )

    log.context_slice("Researcher", "bug report & test snippet", len(content))
    log.llm_thinking("researcher", "Drafting fix description")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=content),
    ]
    response = llm.invoke(messages)
    fix_text = extract_text(response.content).strip()

    log.llm_response("researcher", fix_text)
    log.fix_description(fix_text)

    return fix_text
