"""Unit tests for src/config.py."""

import os
import pytest
from unittest.mock import patch


def _make_env(**overrides):
    base = {
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": "gpt-4o-mini",
        "OPENAI_API_KEY": "sk-test",
        "OPENAI_SUPPORT_MODEL": "gpt-4o,gpt-4o-mini",
        "ANTHROPIC_SUPPORT_MODEL": "claude-3-5-haiku-20241022",
        "GEMINI_SUPPORT_MODEL": "gemini-2.0-flash",
        "BENCHMARK_RUNS": "5",
        "MAX_TURNS": "10",
        "LOG_LLM_CALLS": "true",
    }
    base.update(overrides)
    return base


def test_load_config_openai_valid():
    from src.config import load_config

    with patch.dict(os.environ, _make_env(), clear=True):
        config = load_config()
    assert config.provider == "openai"
    assert config.model == "gpt-4o-mini"
    assert config.api_key == "sk-test"
    assert config.benchmark_runs == 5
    assert config.max_turns == 10
    assert config.log_llm_calls is True


def test_load_config_unsupported_provider():
    from src.config import load_config

    with patch.dict(os.environ, _make_env(LLM_PROVIDER="cohere"), clear=True):
        with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
            load_config()


def test_load_config_missing_api_key():
    from src.config import load_config

    env = _make_env()
    env.pop("OPENAI_API_KEY")
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
            load_config()


def test_load_config_unsupported_model():
    from src.config import load_config

    with patch.dict(os.environ, _make_env(LLM_MODEL="gpt-99-ultra"), clear=True):
        with pytest.raises(ValueError, match="not in the supported list"):
            load_config()


def test_load_config_anthropic():
    from src.config import load_config

    with patch.dict(
        os.environ,
        _make_env(
            LLM_PROVIDER="anthropic",
            LLM_MODEL="claude-3-5-haiku-20241022",
            ANTHROPIC_API_KEY="sk-ant-test",
        ),
        clear=True,
    ):
        config = load_config()
    assert config.provider == "anthropic"
    assert config.model == "claude-3-5-haiku-20241022"


def test_load_config_log_llm_calls_false():
    from src.config import load_config

    with patch.dict(os.environ, _make_env(LOG_LLM_CALLS="false"), clear=True):
        config = load_config()
    assert config.log_llm_calls is False
