import pytest
from unittest.mock import MagicMock, patch, call
from io import StringIO

from src.chat import chat_loop
from src.config import Config


class TestChatLoop:
    """Test the main chat loop."""

    def _make_config(self):
        return Config(
            llm_provider="openai",
            llm_model="gpt-5.4-mini",
            openai_api_key="test-key",
            tavily_api_key="test-tavily",
            mem0_api_key="test-mem0",
            user_id="test_user",
        )

    @patch("src.chat.create_agent")
    @patch("src.chat.create_llm")
    @patch("src.chat.MemoryManager")
    @patch("builtins.input", side_effect=["exit"])
    def test_exit_command_stops_loop(self, mock_input, mock_mem_cls, mock_llm, mock_agent):
        """Chat loop exits cleanly on 'exit' command."""
        config = self._make_config()
        mock_mem = MagicMock()
        mock_mem_cls.return_value = mock_mem

        chat_loop(config)

        # Should not have called memory search (exited immediately)
        mock_mem.search.assert_not_called()

    @patch("src.chat.create_agent")
    @patch("src.chat.create_llm")
    @patch("src.chat.MemoryManager")
    @patch("builtins.input", side_effect=["Hello there!", "exit"])
    def test_full_flow(self, mock_input, mock_mem_cls, mock_llm, mock_agent):
        """Full chat flow: memory search → agent run → memory add."""
        config = self._make_config()
        mock_mem = MagicMock()
        mock_mem_cls.return_value = mock_mem
        mock_mem.search.return_value = "No prior context yet."

        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {"output": "Hi! How can I help?"}
        mock_agent.return_value = mock_executor

        chat_loop(config)

        # 1. Memory search was called for user input
        mock_mem.search.assert_called_once_with("Hello there!", user_id="test_user")

        # 2. Agent was invoked
        mock_executor.invoke.assert_called_once()

        # 3. Memory add was called with the exchange
        mock_mem.add.assert_called_once()
        add_args = mock_mem.add.call_args
        messages = add_args[0][0]
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    @patch("src.chat.create_agent")
    @patch("src.chat.create_llm")
    @patch("src.chat.MemoryManager")
    @patch("builtins.input", side_effect=["quit"])
    def test_quit_command_stops_loop(self, mock_input, mock_mem_cls, mock_llm, mock_agent):
        """Chat loop also exits on 'quit' command."""
        config = self._make_config()
        mock_mem_cls.return_value = MagicMock()

        chat_loop(config)
        # No error = success
