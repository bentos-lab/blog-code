"""Atomic tools for agents: file I/O, grep, and test running."""

import subprocess
from pathlib import Path
from typing import Any, Optional


def extract_text(content: Any) -> str:
    """Safely extract a plain string from an LLM response.content.

    LangChain returns response.content as:
    - str for OpenAI / Anthropic
    - list of dicts for Google Gemini (multipart content blocks)

    Args:
        content: The value of response.content from any LangChain chat model.

    Returns:
        A plain string suitable for parsing / regex operations.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text", ""))
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content)


def read_file(path: str) -> str:
    """Read entire file content.

    Args:
        path: Path to file relative to project root.

    Returns:
        File content as string, or error message if not found.
    """
    p = Path(path)
    if not p.exists():
        return f"[ERROR] File not found: {path}"
    return p.read_text(encoding="utf-8")


def read_file_signatures(path: str) -> str:
    """Read only function/class signatures from a Python file (no body).

    Used by the Context-Engineered agent for Progressive Disclosure —
    sends only signatures to the planner, not full file content.

    Args:
        path: Path to Python file.

    Returns:
        String of class/function signature lines only.
    """
    p = Path(path)
    if not p.exists():
        return f"[ERROR] File not found: {path}"
    lines = p.read_text(encoding="utf-8").splitlines()
    sig_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("def ", "class ", "async def ")):
            sig_lines.append(line)
    return "\n".join(sig_lines) if sig_lines else "(no functions/classes found)"


def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories as needed.

    Args:
        path: Target file path.
        content: Content to write.

    Returns:
        Success or error message.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"[OK] Written to {path} ({len(content)} chars)"


def run_grep(pattern: str, path: str) -> str:
    """Run grep search within a file or directory.

    Args:
        pattern: Search string.
        path: File or directory to search.

    Returns:
        Grep output or error.
    """
    try:
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", pattern, path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout or result.stderr or "(no matches)"
    except subprocess.TimeoutExpired:
        return "[ERROR] grep timed out"
    except FileNotFoundError:
        return "[ERROR] grep not available"


def run_tests(target_dir: str = "apps/target_app/tests") -> dict:
    """Run pytest on the target app test suite.

    Args:
        target_dir: Directory containing the tests.

    Returns:
        Dict with keys: success (bool), summary (str), output (str), returncode (int).
    """
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", target_dir, "--tb=short", "-q"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        # Extract summary line (last non-empty line)
        lines = [l for l in output.splitlines() if l.strip()]
        summary = lines[-1] if lines else "(no output)"
        return {
            "success": success,
            "summary": summary,
            "output": output,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "summary": "Tests timed out",
            "output": "",
            "returncode": -1,
        }
