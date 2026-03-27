"""Mem0 memory manager for long-term user memory."""

from mem0 import MemoryClient


CUSTOM_INSTRUCTIONS = """
INFER THE MEMORIES FROM USER QUERIES EVEN IF IT'S A QUESTION.
Extract user persona, preferences, past topics (especially travel), budget style, and any facts.
Be concise and accurate.
"""


class MemoryManager:
    """Wrapper around Mem0 MemoryClient for search/add operations."""

    def __init__(self, api_key: str):
        self.client = MemoryClient(api_key=api_key)

    def search(self, query: str, user_id: str) -> str:
        """Search for relevant memories and format as context string.

        Args:
            query: The user's current query.
            user_id: Persistent user identifier.

        Returns:
            Formatted context string for system prompt injection.
        """
        memories = self.client.search(query=query, filters={"user_id": user_id})

        # Mem0 returns {'results': [...]} 
        results = memories.get("results", []) if isinstance(memories, dict) else memories

        if results:
            lines = [f"- {m['memory']}" for m in results]
            context = "\n".join(lines)
            return (
                f"USER CONTEXT & PREFERENCES (use this to personalize):\n"
                f"{context}\n"
            )
        return "No prior context yet."

    def add(self, messages: list[dict], user_id: str) -> None:
        """Store a conversation exchange in long-term memory.

        Args:
            messages: List of {"role": ..., "content": ...} dicts.
            user_id: Persistent user identifier.
        """
        self.client.add(messages, user_id=user_id)

    def setup_instructions(self) -> None:
        """Set custom extraction instructions on the Mem0 project."""
        self.client.project.update(custom_instructions=CUSTOM_INSTRUCTIONS)
