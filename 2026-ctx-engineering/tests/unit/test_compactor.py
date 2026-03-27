"""Unit tests for src/compactor.py."""

import json
import pytest
from unittest.mock import MagicMock

from src.compactor import should_compact, compact


def test_should_compact_false_below_interval():
    assert should_compact(0) is False
    assert should_compact(1) is False
    assert should_compact(3) is False


def test_should_compact_true_at_interval():
    assert should_compact(4) is True
    assert should_compact(8) is True
    assert should_compact(12) is True


def test_compact_returns_parsed_json():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content=json.dumps({
            "bugs_identified": ["storage.py: no FileNotFoundError handling"],
            "fixes_applied": [],
            "tests_status": "0 passed, 4 failed",
            "key_decisions": [],
            "remaining_bugs": ["all 4 bugs remain"],
        })
    )
    history = [{"type": "analysis", "turn": 1}, {"type": "research", "turn": 2}]
    result = compact(mock_llm, history)
    assert "bugs_identified" in result
    assert "fixes_applied" in result


def test_compact_handles_invalid_json():
    """If LLM returns non-JSON, raw_summary fallback is used."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="not json at all")
    result = compact(mock_llm, [{"turn": 1}])
    assert "raw_summary" in result
