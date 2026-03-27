"""Integration tests for context isolation contracts.

Verifies that each sub-agent receives ONLY its expected context slice —
the core guarantee of Context Isolation (CE Pattern 3).
"""

import pytest
from unittest.mock import MagicMock, patch, call
import json


def _make_llm_with_response(content: str) -> MagicMock:
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content=content)
    return mock


def test_analyzer_receives_signatures_not_full_content():
    """Analyzer sub-agent must NOT see full file content, only signatures."""
    from src.subagents.analyzer import analyze
    from src.tools import read_file_signatures

    mock_llm = _make_llm_with_response(json.dumps({
        "bug_file": "target_app/storage.py",
        "bug_function": "load_todos",
        "bug_type": "io_error",
        "description": "Missing FileNotFoundError handling",
    }))

    test_output = "FileNotFoundError: [Errno 2] No such file or directory: 'todos.json'"

    with patch("src.subagents.analyzer.read_file_signatures") as mock_sig:
        mock_sig.return_value = "def load_todos() -> List[Todo]:"
        analyze(mock_llm, test_output)

    # Verify: read_file_signatures was called (not read_file / full content)
    mock_sig.assert_called()
    # The prompt sent to LLM should NOT contain full file body
    call_args = mock_llm.invoke.call_args
    messages = call_args[0][0]
    full_content_markers = ["import json", "open(STORAGE_FILE"]
    for m in messages:
        for marker in full_content_markers:
            assert marker not in m.content, (
                f"Analyzer received full file content (found '{marker}') — "
                "Context Isolation violated!"
            )


def test_executor_receives_single_file_only():
    """Executor must only see the one file it needs to patch."""
    from src.subagents.executor import execute

    file_content = "def load_todos():\n    with open(STORAGE_FILE) as f:\n        return json.load(f)\n"
    mock_llm = _make_llm_with_response(file_content.replace("with open", "try:\n    with open"))

    with patch("src.subagents.executor.read_file", return_value=file_content):
        with patch("src.subagents.executor.write_file", return_value="[OK]"):
            result = execute(mock_llm, "target_app/storage.py", "Add try/except FileNotFoundError")

    # Verify: only one file's content was in the prompt
    call_args = mock_llm.invoke.call_args
    messages = call_args[0][0]
    combined = " ".join(m.content for m in messages)
    # Should NOT have content from other files (e.g. todo.py class definitions)
    assert "target_app/todo.py" not in combined
    assert "target_app/cli.py" not in combined
    assert result["patched"] is True


def test_researcher_receives_only_bug_report_not_full_files():
    """Researcher should not see full codebase, only bug description + test snippet."""
    from src.subagents.researcher import research

    mock_llm = _make_llm_with_response("Wrap the open() call with try/except FileNotFoundError")
    bug_report = {
        "bug_file": "target_app/storage.py",
        "bug_function": "load_todos",
        "bug_type": "io_error",
        "description": "No FileNotFoundError handling",
    }
    test_output = "FileNotFoundError at line 15"

    research(mock_llm, bug_report, test_output)

    call_args = mock_llm.invoke.call_args
    messages = call_args[0][0]
    combined = " ".join(m.content for m in messages)

    # Should NOT contain full file content from other files
    assert "def toggle_done" not in combined  # From todo.py
    assert "def build_parser" not in combined  # From cli.py
