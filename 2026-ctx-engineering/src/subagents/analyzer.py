"""Analyzer sub-agent — now returns ALL bugs found in a single pass.

Context isolation: receives file signatures only (not full content).
Returns a structured list of all bug reports found in the test output.
"""

import json
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ..tools import extract_text
from .. import console_logger as log


SYSTEM_PROMPT = """You are a bug analysis specialist for Python codebases.
You will receive:
1. A pytest failure report (showing ALL failing tests)
2. File signatures (function/class names — NOT full file content)

Your job: identify ALL distinct bugs across ALL files causing failures.
Group by bug location.

Respond ONLY with a JSON object (no prose, no markdown fences):
{
  "bugs": [
    {
      "bug_file": "apps/target_app/xxx.py",
      "bug_function": "function_name",
      "bug_type": "logic_error|io_error|arg_parse|attribute_error|type_error",
      "description": "one concise sentence describing the specific bug"
    },
    ...
  ]
}

Rules:
- Include ALL bugs visible from the test failures, even if in the same file
- If two tests fail about the same function, report it only ONCE
- Do NOT report the same (file, function) pair twice"""


def analyze_all(
    llm: BaseChatModel,
    test_output: str,
    file_signatures: dict[str, str],
) -> list[dict]:
    """Analyze failing tests and return ALL structured bug reports in one pass.

    Args:
        llm: The language model to use.
        test_output: Full pytest output.
        file_signatures: Pre-computed filepath -> signatures mapping.

    Returns:
        List of bug report dicts. Empty list on parse error.
    """
    sigs = ""
    for path, sig_content in file_signatures.items():
        sigs += f"\n## {path}\n{sig_content}\n"

    total_ctx = len(sigs) + len(test_output)
    log.context_slice("Analyzer", "ALL file signatures + full test payload", total_ctx)
    log.llm_thinking("analyzer", "Identifying ALL bugs across all failing tests")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Full pytest failure output:\n```\n{test_output}\n```\n\n"
                f"File signatures:{sigs}"
            )
        ),
    ]
    response = llm.invoke(messages)
    text = extract_text(response.content).strip()
    log.llm_response("analyzer", text)

    try:
        if "```" in text:
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()
        data = json.loads(text)
        bugs = data.get("bugs", [])
        log._console.print(
            f"  [bold red]🔍 Analyzer[/bold red]  "
            f"found [yellow]{len(bugs)}[/yellow] bug(s) across "
            f"[yellow]{len({b.get('bug_file') for b in bugs})}[/yellow] file(s)"
        )
        for b in bugs:
            log.bug_report(b)
        return bugs
    except (json.JSONDecodeError, IndexError, AttributeError):
        log._console.print("  [red]✗ Analyzer[/red]  failed to parse response as JSON")
        return []
