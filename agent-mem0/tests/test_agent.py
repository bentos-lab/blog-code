import pytest
from unittest.mock import MagicMock, patch

from src.agent import create_agent


class TestCreateAgent:
    """Test agent builder."""

    @patch("src.agent.TavilySearch")
    @patch("src.agent.langchain_create_agent")
    def test_create_agent_calls_builder(self, mock_create_agent, mock_tavily_cls):
        """create_agent calls langchain_create_agent with context and tools."""
        mock_llm = MagicMock()
        mock_tavily_tool = MagicMock()
        mock_tavily_cls.return_value = mock_tavily_tool
        
        mock_executor = MagicMock()
        mock_create_agent.return_value = mock_executor

        executor = create_agent(
            llm=mock_llm,
            tavily_api_key="test-key",
            user_context="User likes beaches.",
        )

        assert executor is mock_executor
        
        # Verify TavilySearch was instantiated with the key
        mock_tavily_cls.assert_called_once()
        assert mock_tavily_cls.call_args.kwargs.get("api_key") == "test-key"
        
        # Verify create_agent was called with the model, tools, and injected context
        mock_create_agent.assert_called_once()
        kwargs = mock_create_agent.call_args.kwargs
        assert kwargs["model"] is mock_llm
        assert kwargs["tools"] == [mock_tavily_tool]
        assert "User likes beaches." in kwargs["system_prompt"]
