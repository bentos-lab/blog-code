import pytest
from unittest.mock import patch, MagicMock

from src.llm import create_llm
from src.config import Config


class TestCreateLLM:
    """Test LLM factory function."""

    @patch("src.llm.init_chat_model")
    def test_creates_openai_model(self, mock_init):
        """create_llm calls init_chat_model with openai params."""
        mock_init.return_value = MagicMock()

        config = Config(
            llm_provider="openai",
            llm_model="gpt-5.4-mini",
            openai_api_key="test-key",
            tavily_api_key="test-tavily",
            mem0_api_key="test-mem0",
        )
        result = create_llm(config)

        mock_init.assert_called_once_with(
            "gpt-5.4-mini",
            model_provider="openai",
            temperature=0.7,
            api_key="test-key",
        )
        assert result == mock_init.return_value

    @patch("src.llm.init_chat_model")
    def test_creates_anthropic_model(self, mock_init):
        """create_llm calls init_chat_model with anthropic params."""
        mock_init.return_value = MagicMock()

        config = Config(
            llm_provider="anthropic",
            llm_model="claude-sonnet-4-20250514",
            anthropic_api_key="test-key",
            tavily_api_key="test-tavily",
            mem0_api_key="test-mem0",
        )
        result = create_llm(config)

        mock_init.assert_called_once_with(
            "claude-sonnet-4-20250514",
            model_provider="anthropic",
            temperature=0.7,
            api_key="test-key",
        )

    @patch("src.llm.init_chat_model")
    def test_creates_google_model(self, mock_init):
        """create_llm calls init_chat_model with google params."""
        mock_init.return_value = MagicMock()

        config = Config(
            llm_provider="google",
            llm_model="gemini-2.0-flash",
            google_api_key="test-key",
            tavily_api_key="test-tavily",
            mem0_api_key="test-mem0",
        )
        result = create_llm(config)

        mock_init.assert_called_once_with(
            "gemini-2.0-flash",
            model_provider="google_genai",
            temperature=0.7,
            api_key="test-key",
        )

    def test_invalid_provider_raises(self):
        """create_llm raises for unsupported provider."""
        config = Config(
            llm_provider="invalid",
            llm_model="some-model",
            tavily_api_key="test-tavily",
            mem0_api_key="test-mem0",
        )
        with pytest.raises(ValueError, match="Unsupported"):
            create_llm(config)
