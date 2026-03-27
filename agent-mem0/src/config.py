"""Configuration loader and validator."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv


class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass


SUPPORTED_PROVIDERS = {"openai", "anthropic", "google"}

PROVIDER_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}

DEFAULT_MODELS = {
    "openai": "gpt-5.4-mini",
    "anthropic": "claude-sonnet-4-6",
    "google": "gemini-2.5-flash",
}

# Supported models per provider (sourced from official docs, March 2026).
# Override via OPENAI_SUPPORT_MODEL, ANTHROPIC_SUPPORT_MODEL, or
# GEMINI_SUPPORT_MODEL env vars (comma-separated) to add new releases
# without changing this file.
SUPPORTED_MODELS: dict[str, list[str]] = {
    # https://platform.openai.com/docs/models
    "openai": [
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
        "gpt-4o",
        "gpt-4o-mini",
        "o1",
        "o1-mini",
        "o3",
        "o3-mini",
        "o4-mini",
    ],
    # https://docs.anthropic.com/en/docs/about-claude/models/overview
    "anthropic": [
        # Latest
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
        "claude-haiku-4-5",
        # Legacy (still available)
        "claude-sonnet-4-5-20250929",
        "claude-sonnet-4-5",
        "claude-opus-4-5-20251101",
        "claude-opus-4-5",
        "claude-opus-4-1-20250805",
        "claude-opus-4-1",
        "claude-sonnet-4-20250514",
        "claude-sonnet-4-0",
        "claude-opus-4-20250514",
        "claude-opus-4-0",
        "claude-3-haiku-20240307",  # deprecated, retires Apr 19 2026
    ],
    # https://ai.google.dev/gemini-api/docs/models
    "google": [
        # Preview / latest
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
        # Stable
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ],
}

PROVIDER_MODELS_ENV_MAP = {
    "openai": "OPENAI_SUPPORT_MODEL",
    "anthropic": "ANTHROPIC_SUPPORT_MODEL",
    "google": "GEMINI_SUPPORT_MODEL",
}


def get_supported_models(provider: str) -> list[str]:
    """Return the supported model list for a provider.

    Reads from *_SUPPORTED_MODELS env var first (comma-separated); falls back
    to the hardcoded SUPPORTED_MODELS defaults.
    """
    env_key = PROVIDER_MODELS_ENV_MAP.get(provider, "")
    env_value = os.getenv(env_key, "")
    if env_value:
        return [m.strip() for m in env_value.split(",") if m.strip()]
    return SUPPORTED_MODELS.get(provider, [])


@dataclass
class Config:
    """Application configuration."""
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    tavily_api_key: str = ""
    mem0_api_key: str = ""
    user_id: str = "demo_user_2026"

    def get_provider_api_key(self) -> str:
        """Return the API key for the current provider."""
        key_map = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "google": self.google_api_key,
        }
        return key_map.get(self.llm_provider, "")


def load_config() -> Config:
    """Load config from environment variables and validate."""
    load_dotenv()

    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise ConfigError(
            f"Unsupported LLM_PROVIDER: '{provider}'. "
            f"Supported: {', '.join(SUPPORTED_PROVIDERS)}"
        )

    config = Config(
        llm_provider=provider,
        llm_model=os.getenv("LLM_MODEL", DEFAULT_MODELS.get(provider, "gpt-4o-mini")),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        google_api_key=os.getenv("GOOGLE_API_KEY", ""),
        tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
        mem0_api_key=os.getenv("MEM0_API_KEY", ""),
        user_id=os.getenv("USER_ID", "demo_user_2026"),
    )

    # Validate required keys
    if not config.tavily_api_key:
        raise ConfigError("TAVILY_API_KEY is required. Get one at https://tavily.com")

    if not config.mem0_api_key:
        raise ConfigError("MEM0_API_KEY is required. Get one at https://app.mem0.ai")

    provider_env_key = PROVIDER_KEY_MAP[provider]
    if not config.get_provider_api_key():
        raise ConfigError(
            f"{provider_env_key} is required for provider '{provider}'"
        )

    # Validate model against the supported list for the active provider
    supported = get_supported_models(provider)
    if supported and config.llm_model not in supported:
        models_env_key = PROVIDER_MODELS_ENV_MAP[provider]
        raise ConfigError(
            f"Unsupported LLM_MODEL: '{config.llm_model}' for provider '{provider}'. "
            f"Supported: {', '.join(supported)}. "
            f"To add new models, set {models_env_key} as a comma-separated list."
        )

    return config
