"""LLM request/response logger — writes structured JSON to llm_logs/ directory."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Union

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

LOG_DIR = Path("llm_logs")


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(exist_ok=True)


def _safe_serialize(obj: Any) -> Any:
    """Recursively make an object JSON-serializable."""
    if hasattr(obj, "content"):
        return {"type": type(obj).__name__, "content": obj.content}
    if hasattr(obj, "__dict__"):
        return {k: _safe_serialize(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


class TokenCounter:
    """Simple accumulator for token usage across multiple LLM calls."""

    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0

    def reset(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


# Global session counter for simple tracking in run scripts
session_tokens = TokenCounter()


class LLMLogger(BaseCallbackHandler):
    """LangChain callback handler that logs every LLM call to llm_logs/."""

    def __init__(
        self,
        agent_type: str,
        enabled: bool = True,
        counter: Optional[TokenCounter] = None,
    ) -> None:
        super().__init__()
        self.agent_type = agent_type
        self.enabled = enabled
        self.counter = counter or session_tokens
        self._turn: int = 0
        self._start_time: float = 0.0
        self._pending_messages: list = []

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: Sequence[Sequence[BaseMessage]],
        **kwargs: Any,
    ) -> None:
        if not self.enabled:
            return
        self._turn += 1
        self._start_time = time.monotonic()
        self._pending_messages = _safe_serialize(messages)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        if not self.enabled:
            return
        latency_ms = round((time.monotonic() - self._start_time) * 1000)
        _ensure_log_dir()

        # Extract token usage if available
        in_tok, out_tok = 0, 0
        
        # 1. Try finding usage in llm_output
        if response.llm_output and isinstance(response.llm_output, dict):
            usage = response.llm_output.get("token_usage") or response.llm_output.get("usage_metadata", {})
            if usage:
                in_tok = usage.get("prompt_tokens") or usage.get("input_tokens", 0)
                out_tok = usage.get("completion_tokens") or usage.get("output_tokens", 0)

        # 2. Try finding usage in message.usage_metadata (LangChain 0.2 / Google GenAI)
        if in_tok == 0 and out_tok == 0:
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, "message") and hasattr(gen.message, "usage_metadata") and gen.message.usage_metadata:
                        in_tok += gen.message.usage_metadata.get("input_tokens", 0)
                        out_tok += gen.message.usage_metadata.get("output_tokens", 0)

        token_usage = {
            "input_tokens": in_tok,
            "output_tokens": out_tok,
        }
        if self.counter:
            self.counter.input_tokens += in_tok
            self.counter.output_tokens += out_tok

        # Print latency and token usage
        from .console_logger import _console
        _console.print(f"    [dim]time: {latency_ms}ms  |  tokens: in={in_tok} out={out_tok} total={in_tok+out_tok}[/dim]")

        # Extract response text
        completions = []
        for gen_list in response.generations:
            for gen in gen_list:
                completions.append(
                    getattr(gen, "text", None) or getattr(gen.message, "content", "")
                    if hasattr(gen, "message")
                    else getattr(gen, "text", str(gen))
                )

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"{timestamp}_{self.agent_type}_turn{self._turn}.json"

        log_entry = {
            "timestamp": timestamp,
            "agent_type": self.agent_type,
            "turn": self._turn,
            "latency_ms": latency_ms,
            "token_usage": token_usage,
            "prompt": self._pending_messages,
            "response": completions,
        }

        log_path = LOG_DIR / filename
        with open(log_path, "w") as f:
            json.dump(log_entry, f, indent=2, default=str)

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        if not self.enabled:
            return
        _ensure_log_dir()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"{timestamp}_{self.agent_type}_turn{self._turn}_ERROR.json"
        log_entry = {
            "timestamp": timestamp,
            "agent_type": self.agent_type,
            "turn": self._turn,
            "error": str(error),
        }
        with open(LOG_DIR / filename, "w") as f:
            json.dump(log_entry, f, indent=2)
