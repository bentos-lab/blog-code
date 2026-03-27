"""Interactive chat loop with memory-powered agent."""

from langchain_core.messages import HumanMessage, AIMessage

from src.config import Config
from src.llm import create_llm
from src.memory import MemoryManager
from src.agent import create_agent


def chat_loop(config: Config) -> None:
    """Run the interactive chat loop.

    Flow per turn:
    1. Get user input
    2. Search Mem0 for relevant memories
    3. Create agent with memory context injected
    4. Run agent
    5. Store exchange back to Mem0
    6. Repeat

    Args:
        config: Application configuration.
    """
    llm = create_llm(config)
    memory = MemoryManager(api_key=config.mem0_api_key)
    memory.setup_instructions()

    print("Chat started (type 'exit' or 'quit' to end session)\n")
    messages: list[HumanMessage | AIMessage] = []

    while True:
        user_input = input("You: ")
        if user_input.lower().strip() in ("exit", "quit"):
            print("Session ended. Your memories are saved for next time!")
            break

        # 1. Get long-term context from Mem0
        context = memory.search(user_input, user_id=config.user_id)

        # 2. Create fresh agent with latest context
        agent_executor = create_agent(
            llm=llm,
            tavily_api_key=config.tavily_api_key,
            user_context=context,
        )

        # 3. Run agent with session history
        response = agent_executor.invoke({
            "messages": messages + [HumanMessage(content=user_input)],
            "user_context": context,
        })

        reply_content = response["messages"][-1].content
        if isinstance(reply_content, list):
            assistant_reply = " ".join(
                str(part.get("text", "")) for part in reply_content if isinstance(part, dict) and "text" in part
            )
        else:
            assistant_reply = str(reply_content)
        print(f"\nAssistant: {assistant_reply}\n")

        # 4. Store exchange in Mem0 for next session
        interaction = [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": assistant_reply},
        ]
        memory.add(interaction, user_id=config.user_id)

        # 5. Keep short-term session history
        messages.append(HumanMessage(content=user_input))
        messages.append(AIMessage(content=assistant_reply))
