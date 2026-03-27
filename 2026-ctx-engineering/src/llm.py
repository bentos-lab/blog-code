"""LLM factory — returns a LangChain chat model for the configured provider."""

from langchain_core.language_models import BaseChatModel

from .config import Config
from .logger import LLMLogger


def get_llm(config: Config, agent_type: str = "agent") -> BaseChatModel:
    """Build a LangChain chat model with LLM logging callbacks attached.

    Args:
        config: Loaded Config object.
        agent_type: Label used in log file names (e.g. "traditional", "analyzer").

    Returns:
        A LangChain BaseChatModel instance ready to invoke.
    """
    callbacks = [LLMLogger(agent_type=agent_type, enabled=config.log_llm_calls)]

    if config.provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=config.model,
            api_key=config.api_key,  # type: ignore[arg-type]
            callbacks=callbacks,
        )

    elif config.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=config.model,
            api_key=config.api_key,  # type: ignore[arg-type]
            callbacks=callbacks,
        )

    elif config.provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=config.model,
            google_api_key=config.api_key,
            callbacks=callbacks,
        )

    else:
        raise ValueError(f"Unknown provider: {config.provider}")


def get_cheap_llm(config: Config, agent_type: str = "compactor") -> BaseChatModel:
    """Return the cheapest/fastest model for summarization/compaction tasks.

    Uses gpt-4o-mini (OpenAI), claude-3-5-haiku (Anthropic), or gemini-flash (Google)
    regardless of the main model configured, to minimize compaction cost.
    """
    callbacks = [LLMLogger(agent_type=agent_type, enabled=config.log_llm_calls)]

    if config.provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=config.openai_api_key or config.api_key,  # type: ignore[arg-type]
            callbacks=callbacks,
        )

    elif config.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model="claude-3-5-haiku-20241022",
            api_key=config.anthropic_api_key or config.api_key,  # type: ignore[arg-type]
            callbacks=callbacks,
        )

    elif config.provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=config.google_api_key or config.api_key,
            callbacks=callbacks,
        )

    else:
        raise ValueError(f"Unknown provider: {config.provider}")
