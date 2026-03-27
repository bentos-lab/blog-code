"""Entry point for the Memory-Powered General Assistant."""

import os
import sys

# Ensure the project root is in the Python path so "src.config" resolves
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import load_config, ConfigError
from src.chat import chat_loop


def main():
    print("=" * 50)
    print("  Memory-Powered General Assistant")
    print("  Mem0 + LangChain + Tavily")
    print("=" * 50)

    try:
        config = load_config()
    except ConfigError as e:
        print(f"\n❌ Configuration error: {e}")
        print("   Copy .env.example to .env and fill in your API keys.")
        return

    print(f"\n🧠 Provider: {config.llm_provider} ({config.llm_model})")
    print(f"👤 User ID:  {config.user_id}")
    print()

    chat_loop(config)


if __name__ == "__main__":
    main()
