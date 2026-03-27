"""Executor sub-agent — now accepts a FixTask (one or many bugs, one file).

Context isolation: sees only the content of ONE file + plain-English descriptions.
The executor autonomously reads the file, reasons about all bug descriptions, and
writes a corrected version. No pre-generated code is injected — the executor
figures out the solution itself.

This matches how Anthropic's sub-agents work in their multi-agent research system:
sub-agents receive task descriptions and autonomously implement them.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ..tools import read_file, write_file, extract_text
from ..subagents.task_planner import FixTask
from .. import console_logger as log


SYSTEM_PROMPT = """You are an autonomous Python code fixer.
You will receive:
1. The FULL content of a single Python file
2. A list of bug descriptions to fix in that file

Your job: output the COMPLETE corrected file — no prose, no markdown, no explanations.
Apply ALL described fixes in one pass. Preserve all other code exactly."""


def execute_task(llm: BaseChatModel, task: FixTask) -> dict:
    """Apply all fixes described in a FixTask to a single target file.

    Args:
        llm: The language model to use.
        task: A FixTask containing target_file, bugs, and context_hint.

    Returns:
        Dict with: patched (bool), task_id (str), path (str), message (str)
    """
    log.tool_call("read_file", task.target_file)
    file_content = read_file(task.target_file)
    if "[ERROR]" in file_content:
        log.patch_applied(task.target_file, success=False)
        return {"patched": False, "task_id": task.task_id, "path": task.target_file, "message": file_content}

    # Build the bug description block
    bugs_block = "\n".join(
        f"  {i+1}. [{b.get('bug_function', '?')}]: {b.get('description', '')}"
        for i, b in enumerate(task.bugs)
    )

    prompt = (
        f"File to fix: {task.target_file}\n\n"
        f"Current content:\n```python\n{file_content}\n```\n\n"
        f"Bugs to fix ({len(task.bugs)} total):\n{bugs_block}\n\n"
        f"Additional context:\n{task.context_hint}\n\n"
        f"Output the complete corrected Python file:"
    )

    ctx_size = len(prompt)
    log.context_slice(
        f"Executor[{task.task_id}]",
        f"{task.target_file} + {len(task.bugs)} bug description(s)",
        ctx_size,
    )
    log.llm_thinking(f"executor[{task.task_id}]", f"Fixing {len(task.bugs)} bug(s) in {task.target_file}", max_chars=80)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    corrected = extract_text(response.content).strip()

    # Strip markdown fences if present
    if corrected.startswith("```"):
        lines = corrected.splitlines()
        corrected = "\n".join(l for l in lines if not l.startswith("```")).strip()

    log.tool_call("write_file", task.target_file)
    result = write_file(task.target_file, corrected)
    success = "[OK]" in result

    log.patch_applied(task.target_file, success=success)
    return {
        "patched": success,
        "task_id": task.task_id,
        "path": task.target_file,
        "message": f"Fixed {len(task.bugs)} bug(s) in {task.target_file}" if success else result,
    }
