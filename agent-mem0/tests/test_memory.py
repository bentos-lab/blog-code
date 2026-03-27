import pytest
from unittest.mock import MagicMock, patch

from src.memory import MemoryManager


class TestMemoryManager:
    """Test Mem0 memory wrapper."""

    def setup_method(self):
        """Create a MemoryManager with mocked client."""
        with patch("src.memory.MemoryClient") as mock_client_cls:
            self.mock_client = MagicMock()
            mock_client_cls.return_value = self.mock_client
            self.manager = MemoryManager(api_key="test-key")

    def test_search_returns_formatted_context(self):
        """search() formats memories into a context string."""
        self.mock_client.search.return_value = {
            "results": [
                {"memory": "User planning Japan vacation"},
                {"memory": "Budget traveler"},
                {"memory": "Likes beaches & street food"},
            ]
        }

        result = self.manager.search("hotel in japan", user_id="test_user")

        self.mock_client.search.assert_called_once_with(
            query="hotel in japan",
            filters={"user_id": "test_user"},
        )
        assert "Japan vacation" in result
        assert "Budget traveler" in result
        assert "street food" in result

    def test_search_returns_fallback_when_empty(self):
        """search() returns fallback message when no memories found."""
        self.mock_client.search.return_value = []

        result = self.manager.search("random query", user_id="test_user")

        assert "No prior context" in result

    def test_add_stores_messages(self):
        """add() calls MemoryClient.add with correct params."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        self.manager.add(messages, user_id="test_user")

        self.mock_client.add.assert_called_once_with(
            messages, user_id="test_user"
        )

    def test_setup_instructions(self):
        """setup_instructions() updates project custom instructions."""
        self.manager.setup_instructions()

        self.mock_client.project.update.assert_called_once()
        call_kwargs = self.mock_client.project.update.call_args
        assert "custom_instructions" in call_kwargs.kwargs or len(call_kwargs.args) > 0
