"""LLM provider factory using LangChain's init_chat_model."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from src.config import Config


# Map our provider names to LangChain's model_provider values
PROVIDER_MAP = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google_genai",
}


def create_llm(config: Config) -> BaseChatModel:
    """Create a chat model for the configured provider.

    Args:
        config: Application config with provider, model, and API key.

    Returns:
        A LangChain BaseChatModel instance.

    Raises:
        ValueError: If the provider is not supported.
    """
    lc_provider = PROVIDER_MAP.get(config.llm_provider)
    if lc_provider is None:
        raise ValueError(
            f"Unsupported LLM provider: '{config.llm_provider}'. "
            f"Supported: {', '.join(PROVIDER_MAP.keys())}"
        )

    return init_chat_model(
        config.llm_model,
        model_provider=lc_provider,
        temperature=0.7,
        api_key=config.get_provider_api_key(),
    )
