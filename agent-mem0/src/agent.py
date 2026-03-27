"""LangChain agent builder with Tavily search tool."""

from langchain_tavily import TavilySearch
from langchain_core.language_models import BaseChatModel
from langchain.agents import create_agent as langchain_create_agent


SYSTEM_PROMPT_TEMPLATE = """You are a helpful, general-purpose AI assistant.
{user_context}
- Use the tavily_search tool whenever you need current info (hotels, flights, products, news, etc.).
- Always prioritize the user's stored preferences and past topics.
- Be friendly and conversational."""


def create_agent(
    llm: BaseChatModel,
    tavily_api_key: str,
    user_context: str,
):
    """Build a LangChain agent with Tavily search and memory context.

    Args:
        llm: The chat model to use.
        tavily_api_key: Tavily API key for web search.
        user_context: Formatted memory context to inject into system prompt.

    Returns:
        An AgentExecutor ready to invoke.
    """
    tavily_tool = TavilySearch(
        max_results=5,
        search_depth="advanced",
        api_key=tavily_api_key,
    )

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(user_context=user_context)

    # In langchain 1.2+, create_agent returns a CompiledStateGraph
    return langchain_create_agent(
        model=llm,
        tools=[tavily_tool],
        system_prompt=system_prompt,
    )
