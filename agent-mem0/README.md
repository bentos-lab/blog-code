# Memory-Powered General Assistant Demo

A lightweight demonstration of building an AI assistant with **long-term memory** (Mem0), **web search** (Tavily), and **multi-provider LLM support** (OpenAI, Anthropic, Google) via LangChain.

This demo shows how to make a chatbot that feels like a real friend by persistently remembering user personas, preferences, and past facts across completely separate chat sessions.

## 🛠️ Setup Instructions

### 1. Requirements
- Python 3.12+
- `uv` (Fast Python package manager)

### 2. Installation
Clone the repository, then use `uv` to install dependencies and sync the project:
```bash
uv sync
```

### 3. API Keys
Get your free API keys for the services:
- **Mem0**: [app.mem0.ai](https://app.mem0.ai) (Free tier included)
- **Tavily**: [tavily.com](https://tavily.com) (Free tier included)
- **LLM Provider**: Get a key for OpenAI, Anthropic, or Google.

Copy the environment template and add your keys:
```bash
cp .env.example .env
```
Edit `.env` and set `LLM_PROVIDER`, `LLM_MODEL`, and your chosen provider's API key. Then add your Mem0 and Tavily keys.

#### Supported model validation

Each provider has a `*_SUPPORT_MODEL` variable that defines which model IDs are valid. `LLM_MODEL` is checked against this list before any API call is made — an invalid model raises a clear error immediately rather than failing mid-session.

```bash
OPENAI_SUPPORT_MODEL=gpt-5.4,gpt-5.4-mini,gpt-4o,...
ANTHROPIC_SUPPORT_MODEL=claude-opus-4-6,claude-sonnet-4-6,...
GEMINI_SUPPORT_MODEL=gemini-2.5-pro,gemini-2.5-flash,...
```

The `.env.example` ships with the full current model lists. To use a newly released model before this file is updated, just append it to the relevant variable:

```bash
# Example: add a hypothetical new release
GEMINI_SUPPORT_MODEL=gemini-2.5-pro,gemini-2.5-flash,...,gemini-4.0-ultra
```

Official model reference pages:
- **OpenAI**: [platform.openai.com/docs/models](https://platform.openai.com/docs/models)
- **Anthropic**: [docs.anthropic.com/en/docs/about-claude/models/overview](https://docs.anthropic.com/en/docs/about-claude/models/overview)
- **Google**: [ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models)

### 4. Running the Demo
Launch the interactive assistant:
```bash
uv run python src/main.py
```

## 🧪 How to Test It (The "Magic" Flow)

**Session 1:**
1. Run the app.
2. Say: `"I'm planning a vacation to Japan next month. I love the culture, Tokyo street food, and I'm on a budget — nothing fancy."`
3. Have a brief chat, then type `exit` to close the app completely.

**Session 2 (The Magic):**
1. Run the app again.
2. Say: `"Can you book a reasonable hotel?"` 
3. Watch as the agent automatically infers you need *budget* hotels in *Japan* near *Tokyo*, prioritizing your previous context.

**Try switching topics:**
Say: `"What laptop should I buy under $800?"` — It acts as a general assistant seamlessly, but remembers if you ever mentioned "I travel a lot so I need something lightweight."

**View your saved knowledge/memories in Mem0 Dashboard**
Go to `https://app.mem0.ai/dashboard/memories` for view your memories.

## 🏗️ Architecture
- `src/config.py`: Environment and multi-provider configuration.
- `src/llm.py`: Dynamic LLM instantiator supporting OpenAI, Anthropic, and Google via LangChain.
- `src/memory.py`: Mem0 client wrapper that handles custom extraction and retrieval.
- `src/agent.py`: LangChain tool-calling agent with a personalized system prompt injecting Mem0 context.
- `src/chat.py`: The core feedback loop connecting the user, Mem0, and the Agent.
