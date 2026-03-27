"""Traditional Agent — monolithic prompt-engineering baseline.

Every turn: full content of all target files + full conversation history → one prompt.
Demonstrates context drift and hallucinations after turn 5.
"""

import time
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from .config import Config
from .llm import get_llm, get_cheap_llm
from .summarizer import summarize_conversation
from .tools import read_file, write_file, run_tests, extract_text
from . import console_logger as log

_prev_turn_chars: int = 0

TRADITIONAL_KEEP_TURNS = 3  # recent turns kept verbatim after summarization

TARGET_FILES = [
    "apps/target_app/models.py",
    "apps/target_app/storage.py",
    "apps/target_app/manager.py",
    "apps/target_app/formatter.py",
    "apps/target_app/utils.py",
    "apps/target_app/cli.py",
    "apps/target_app/main.py",
]

SYSTEM_PROMPT = """You are a senior Python engineer. Your job is to fix all bugs in the target codebase \
so that `pytest apps/target_app/tests/` passes completely.

For each response:
1. Identify which file(s) need changes.
2. Output the COMPLETE corrected file content in a fenced code block with the filename as a comment:
   ```python
   # FILE: apps/target_app/xxx.py
   <full corrected content>
   ```
3. Only output files that need changes. Do not repeat unchanged files.
4. Think step by step."""


def _build_full_context(files: list[str] | None = None) -> str:
    """Dumps ALL file contents — the monolithic traditional agent's problem."""
    file_dump = ""
    for path in (files or TARGET_FILES):
        content = read_file(path)
        file_dump += f"\n\n### {path}\n```python\n{content}\n```"
    return file_dump


def _parse_file_patches(response_text: str) -> dict:
    """Extract filename → content patches from fenced code blocks."""
    import re
    patches = {}
    pattern = r"```python\s*\n# FILE: (.+?)\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    for filename, content in matches:
        patches[filename.strip()] = content
    return patches


def run_traditional_agent(config: Config, target_files: list[str] | None = None, test_dir: str = "apps/target_app/tests") -> dict:
    """Run the traditional monolithic agent against the seeded buggy codebase.

    Returns:
        Dict with: success (bool), turns (int), total_tokens (int)
    """
    log.agent_start("Traditional Agent", "monolithic — dumps ALL files every turn")

    files = target_files or TARGET_FILES
    llm = get_llm(config, agent_type="traditional")
    cheap_llm = get_cheap_llm(config, agent_type="compactor")
    conversation: List = []
    total_tokens = 0
    success = False
    turn = 1

    for turn in range(1, config.max_turns + 1):
        log.agent_turn(turn, config.max_turns, "Traditional")

        # Run tests first
        log.tool_call("run_tests", test_dir)
        test_result = run_tests(test_dir)
        log.test_result(
            passed=test_result.get("passed", 0),
            failed=test_result.get("failed", 0),
            summary=test_result["summary"],
            success=test_result["success"],
        )
        if test_result.get("failed", 0) > 0:
            log.test_output_preview(test_result["output"])

        if test_result["success"]:
            success = True
            break

        # CONTEXT PROBLEM: dump everything every single turn
        file_context = _build_full_context(files)
        total_chars = len(file_context) + sum(
            len(str(m.content)) for m in conversation
        )
        max_chars = config.max_context_tokens * 4
        threshold_chars = int(max_chars * config.context_reduction_threshold)
        free_pct = 1.0 - (total_chars / max_chars)
        log.context_budget(turn, total_chars, free_pct)

        if total_chars > threshold_chars:
            keep = conversation[-TRADITIONAL_KEEP_TURNS:]
            to_summarize = conversation[:-TRADITIONAL_KEEP_TURNS]
            if to_summarize:
                before = total_chars
                summary_text = summarize_conversation(cheap_llm, to_summarize)
                conversation = [SystemMessage(content=f"[Conversation summary]\n{summary_text}")] + keep
                total_chars = len(file_context) + sum(len(str(m.content)) for m in conversation)
                log.summarization_done(before, total_chars)

        global _prev_turn_chars
        delta = total_chars - _prev_turn_chars if _prev_turn_chars > 0 else 0
        log.context_size_warning(turn, total_chars, delta)
        _prev_turn_chars = total_chars

        turn_msg = (
            f"Test run output:\n```\n{test_result['output']}\n```\n\n"
            f"Current file contents:{file_context}\n\n"
            f"Fix all failing tests. Output complete corrected file(s)."
        )
        conversation.append(HumanMessage(content=turn_msg))

        log.llm_thinking("traditional", f"Fix tests: {test_result['summary']}")
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + conversation
        response = llm.invoke(messages)
        response_text = extract_text(response.content)
        log.llm_response("traditional", response_text)

        conversation.append(AIMessage(content=response_text))

        # Apply patches
        patches = _parse_file_patches(response_text)
        if patches:
            for filepath, content in patches.items():
                log.tool_call("write_file", filepath)
                write_file(filepath, content)
                log.patch_applied(filepath, success=True)
        else:
            log._console.print("  [yellow]⚠ No file patches found in response[/yellow]")

    final_test = run_tests(test_dir)
    from .logger import session_tokens
    log.agent_done("Traditional Agent", final_test["success"], turn)
    return {
        "success": final_test["success"],
        "turns": turn,
        "total_tokens": session_tokens.total_tokens,
        "final_summary": final_test["summary"],
    }
