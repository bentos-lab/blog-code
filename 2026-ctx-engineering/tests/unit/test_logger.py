"""Unit tests for src/logger.py."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.logger import LLMLogger


def test_logger_disabled_no_file(tmp_path):
    """When disabled, no log file should be created."""
    logger = LLMLogger(agent_type="test", enabled=False)
    with patch("src.logger.LOG_DIR", tmp_path):
        logger.on_chat_model_start({}, [[]])
        mock_result = MagicMock()
        mock_result.llm_output = {}
        mock_result.generations = []
        logger.on_llm_end(mock_result)
    assert list(tmp_path.iterdir()) == []


def test_logger_creates_file(tmp_path):
    """When enabled, on_llm_end should write a JSON file."""
    logger = LLMLogger(agent_type="traditional", enabled=True)
    with patch("src.logger.LOG_DIR", tmp_path):
        logger.on_chat_model_start({}, [[MagicMock(content="hello")]])
        mock_result = MagicMock()
        mock_result.llm_output = {"token_usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        mock_result.generations = [[MagicMock(text="response text", message=None)]]
        logger.on_llm_end(mock_result)
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data["agent_type"] == "traditional"
    assert data["turn"] == 1
    assert "prompt" in data
    assert "response" in data
    assert "latency_ms" in data


def test_logger_error_creates_error_file(tmp_path):
    """on_llm_error should create an error log file."""
    logger = LLMLogger(agent_type="analyzer", enabled=True)
    logger._turn = 2
    with patch("src.logger.LOG_DIR", tmp_path):
        logger.on_llm_error(RuntimeError("API timeout"))
    files = list(tmp_path.glob("*ERROR*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert "API timeout" in data["error"]
