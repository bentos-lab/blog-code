import os
import pytest
from unittest.mock import patch

from src.config import Config, load_config, ConfigError, get_supported_models, SUPPORTED_MODELS


class TestConfig:
    """Test configuration loading and validation."""

    def test_load_config_defaults(self, monkeypatch):
        """Config loads with defaults when minimal env vars are set."""
        monkeypatch.setattr("src.config.load_dotenv", lambda: None)
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.delenv("LLM_MODEL", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")
        monkeypatch.delenv("OPENAI_SUPPORT_MODEL", raising=False)

        config = load_config()

        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-5.4-mini"
        assert config.openai_api_key == "test-openai-key"
        assert config.tavily_api_key == "test-tavily-key"
        assert config.mem0_api_key == "test-mem0-key"
        assert config.user_id == "demo_user_2026"

    def test_load_config_custom_provider(self, monkeypatch):
        """Config respects custom provider and model."""
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("LLM_MODEL", "claude-sonnet-4-20250514")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")
        monkeypatch.delenv("ANTHROPIC_SUPPORT_MODEL", raising=False)

        config = load_config()

        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-sonnet-4-20250514"
        assert config.anthropic_api_key == "test-anthropic-key"

    def test_load_config_google_provider(self, monkeypatch):
        """Config works with Google provider."""
        monkeypatch.setenv("LLM_PROVIDER", "google")
        monkeypatch.setenv("LLM_MODEL", "gemini-2.0-flash")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")
        monkeypatch.delenv("GEMINI_SUPPORT_MODEL", raising=False)

        config = load_config()

        assert config.llm_provider == "google"
        assert config.llm_model == "gemini-2.0-flash"

    def test_missing_tavily_key_raises(self, monkeypatch):
        """Config raises when TAVILY_API_KEY is missing."""
        monkeypatch.setattr("src.config.load_dotenv", lambda: None)
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        with pytest.raises(ConfigError, match="TAVILY_API_KEY"):
            load_config()

    def test_missing_mem0_key_raises(self, monkeypatch):
        """Config raises when MEM0_API_KEY is missing."""
        monkeypatch.setattr("src.config.load_dotenv", lambda: None)
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.delenv("MEM0_API_KEY", raising=False)

        with pytest.raises(ConfigError, match="MEM0_API_KEY"):
            load_config()

    def test_missing_provider_key_raises(self, monkeypatch):
        """Config raises when the API key for the chosen provider is missing."""
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
            load_config()

    def test_invalid_provider_raises(self, monkeypatch):
        """Config raises for unsupported provider."""
        monkeypatch.setenv("LLM_PROVIDER", "invalid_provider")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")

        with pytest.raises(ConfigError, match="Unsupported"):
            load_config()

    def test_custom_user_id(self, monkeypatch):
        """Config respects custom USER_ID."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")
        monkeypatch.setenv("USER_ID", "my_custom_user")
        monkeypatch.delenv("OPENAI_SUPPORT_MODEL", raising=False)

        config = load_config()
        assert config.user_id == "my_custom_user"

    # --- Model validation tests ---

    def test_invalid_model_raises(self, monkeypatch):
        """Config raises when LLM_MODEL is not in the supported list."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("LLM_MODEL", "gpt-99-fake")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")
        monkeypatch.delenv("OPENAI_SUPPORT_MODEL", raising=False)

        with pytest.raises(ConfigError, match="Unsupported LLM_MODEL"):
            load_config()

    def test_invalid_model_error_mentions_env_var(self, monkeypatch):
        """Error message tells the user which env var to set to extend the list."""
        monkeypatch.setenv("LLM_PROVIDER", "google")
        monkeypatch.setenv("LLM_MODEL", "gemini-fake-model")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")
        monkeypatch.delenv("GEMINI_SUPPORT_MODEL", raising=False)

        with pytest.raises(ConfigError, match="GEMINI_SUPPORT_MODEL"):
            load_config()

    def test_custom_support_model_env_var_accepted(self, monkeypatch):
        """User can add a new model via the SUPPORT_MODEL env var."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("LLM_MODEL", "gpt-future-model")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")
        monkeypatch.setenv("OPENAI_SUPPORT_MODEL", "gpt-future-model,gpt-4o")

        config = load_config()
        assert config.llm_model == "gpt-future-model"

    def test_custom_support_model_overrides_defaults(self, monkeypatch):
        """When SUPPORT_MODEL env var is set, it fully replaces the hardcoded list."""
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("LLM_MODEL", "claude-4.6-opus")  # in hardcoded defaults
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")
        # Override with a list that does NOT include claude-4.6-opus
        monkeypatch.setenv("ANTHROPIC_SUPPORT_MODEL", "claude-restricted-only")

        with pytest.raises(ConfigError, match="Unsupported LLM_MODEL"):
            load_config()

    def test_gemini_support_model_env_var(self, monkeypatch):
        """GEMINI_SUPPORT_MODEL controls google provider validation."""
        monkeypatch.setenv("LLM_PROVIDER", "google")
        monkeypatch.setenv("LLM_MODEL", "gemini-3.1-flash-lite")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("MEM0_API_KEY", "test-mem0-key")
        monkeypatch.setenv("GEMINI_SUPPORT_MODEL", "gemini-3.1-flash-lite,gemini-3.1-pro")

        config = load_config()
        assert config.llm_model == "gemini-3.1-flash-lite"


class TestGetSupportedModels:
    """Test the get_supported_models helper."""

    def test_returns_hardcoded_defaults_when_no_env(self, monkeypatch):
        monkeypatch.delenv("OPENAI_SUPPORT_MODEL", raising=False)
        models = get_supported_models("openai")
        assert models == SUPPORTED_MODELS["openai"]

    def test_env_var_overrides_defaults(self, monkeypatch):
        monkeypatch.setenv("GEMINI_SUPPORT_MODEL", "gemini-3.1-pro,gemini-3.1-flash-lite")
        models = get_supported_models("google")
        assert models == ["gemini-3.1-pro", "gemini-3.1-flash-lite"]

    def test_env_var_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv("OPENAI_SUPPORT_MODEL", " gpt-4o , gpt-4o-mini ")
        models = get_supported_models("openai")
        assert models == ["gpt-4o", "gpt-4o-mini"]

    def test_unknown_provider_returns_empty(self, monkeypatch):
        models = get_supported_models("unknown_provider")
        assert models == []
