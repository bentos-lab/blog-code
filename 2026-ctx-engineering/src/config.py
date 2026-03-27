"""Multi-provider LLM configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    provider: str
    model: str
    api_key: str
    benchmark_runs: int
    max_turns: int
    log_llm_calls: bool
    # Raw API keys for non-default providers (needed for compactor)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    max_context_tokens: int = 10_000
    context_reduction_threshold: float = 0.80
    max_compactions: int = 2


_PROVIDER_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}

_PROVIDER_SUPPORT_MODEL_MAP = {
    "openai": "OPENAI_SUPPORT_MODEL",
    "anthropic": "ANTHROPIC_SUPPORT_MODEL",
    "google": "GEMINI_SUPPORT_MODEL",
}


def load_config() -> Config:
    """Load and validate configuration from environment variables.

    Raises:
        ValueError: If required env vars are missing or model is unsupported.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower().strip()
    model = os.getenv("LLM_MODEL", "").strip()

    if provider not in _PROVIDER_KEY_MAP:
        raise ValueError(
            f"Unsupported LLM_PROVIDER '{provider}'. "
            f"Must be one of: {', '.join(_PROVIDER_KEY_MAP.keys())}"
        )

    api_key_var = _PROVIDER_KEY_MAP[provider]
    api_key = os.getenv(api_key_var, "").strip()
    if not api_key:
        raise ValueError(
            f"LLM_PROVIDER is '{provider}' but {api_key_var} is not set."
        )

    support_model_var = _PROVIDER_SUPPORT_MODEL_MAP[provider]
    support_model_raw = os.getenv(support_model_var, "")
    supported_models = [m.strip() for m in support_model_raw.split(",") if m.strip()]

    if not model:
        raise ValueError("LLM_MODEL is not set.")

    if supported_models and model not in supported_models:
        raise ValueError(
            f"LLM_MODEL '{model}' is not in the supported list for '{provider}': "
            f"{supported_models}. Update {support_model_var} in .env to add it."
        )

    return Config(
        provider=provider,
        model=model,
        api_key=api_key,
        benchmark_runs=int(os.getenv("BENCHMARK_RUNS", "10")),
        max_turns=int(os.getenv("MAX_TURNS", "15")),
        log_llm_calls=os.getenv("LOG_LLM_CALLS", "true").lower() == "true",
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        google_api_key=os.getenv("GOOGLE_API_KEY", ""),
        max_context_tokens=int(os.getenv("MAX_CONTEXT_TOKENS", "10000")),
        context_reduction_threshold=float(os.getenv("CONTEXT_REDUCTION_THRESHOLD", "0.80")),
        max_compactions=int(os.getenv("MAX_COMPACTIONS", "2")),
    )
