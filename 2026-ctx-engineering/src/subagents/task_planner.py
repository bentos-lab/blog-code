"""Task Planner — Central Researcher that builds a dependency-aware fix plan.

This is the key architectural upgrade:
- Receives ALL bug reports (from analyzer) + file signatures
- Groups same-file bugs into ONE FixTask (prevents write conflicts)
- Determines which tasks are independent (safe to parallelise)
- Outputs FixTask objects with plain-English context — no code generated here
- Executors receive descriptions and autonomously implement the fixes

This mirrors how Anthropic's multi-agent research system works:
  Lead agent (planner) → understands dependencies → dispatches sub-agents
"""

import json
from dataclasses import dataclass, field
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ..tools import extract_text
from .. import console_logger as log


@dataclass
class FixTask:
    """A unit of work for one Executor worker."""
    task_id: str
    target_file: str
    bugs: list[dict]              # all bugs to fix in this file
    context_hint: str             # plain-English notes about what to change
    can_parallel: bool = True     # True = no cross-file dependency
    depends_on: list[str] = field(default_factory=list)  # task_ids to wait for


SYSTEM_PROMPT = """You are a senior engineering lead planning a bug-fix task graph.

You will receive a list of bug reports and file signatures.

Your job:
1. Group bugs that are in the SAME file into one task (they must be fixed together)
2. Identify cross-file dependencies (e.g. storage.py imports from models.py — if models changes, storage may need re-reading)
3. Determine which tasks are safe to run in parallel (no shared file, no dependency chain)
4. For each task, write a clear plain-English fix description that an Executor can act on autonomously

Respond ONLY with a JSON object (no prose):
{
  "tasks": [
    {
      "task_id": "fix-models",
      "target_file": "apps/target_app/models.py",
      "bugs": [
        {"bug_function": "total_with_tax", "description": "TAX_RATE is 17 (int %) not 0.17 (decimal)"}
      ],
      "context_hint": "Change TAX_RATE constant from 17 to 0.17. The total_with_tax method is already correct.",
      "can_parallel": true,
      "depends_on": []
    },
    ...
  ]
}

Rules:
- Two tasks CANNOT both have the same target_file
- If task B imports from / reads a file that task A modifies, B must depend on A
- can_parallel: true = this task can run concurrently with other can_parallel tasks
- context_hint must be actionable plain English — no code snippets"""


def plan_tasks(
    llm: BaseChatModel,
    bug_list: list[dict],
    file_signatures: dict[str, str],
) -> list[FixTask]:
    """Build a dependency-aware fix plan from a list of bug reports.

    Args:
        llm: The language model to use (use the main config LLM).
        bug_list: List of bug dicts from analyzer.analyze_all().
        file_signatures: filepath -> signatures content.

    Returns:
        List of FixTask objects ready for parallel dispatch.
    """
    sigs = ""
    for path, sig_content in file_signatures.items():
        sigs += f"\n## {path}\n{sig_content}\n"

    bug_json = json.dumps(bug_list, indent=2)
    ctx_size = len(bug_json) + len(sigs)

    log.context_slice("Task Planner", f"{len(bug_list)} bug reports + file signatures", ctx_size)
    log.llm_thinking("task_planner", "Building dependency-aware fix plan")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Bug reports to plan:\n```json\n{bug_json}\n```\n\n"
                f"File signatures (for dependency analysis):{sigs}"
            )
        ),
    ]
    response = llm.invoke(messages)
    text = extract_text(response.content).strip()
    log.llm_response("task_planner", text)

    try:
        if "```" in text:
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()
        data = json.loads(text)
        tasks_raw = data.get("tasks", [])
    except (json.JSONDecodeError, IndexError):
        log._console.print("  [red]✗ Task Planner[/red]  failed to parse plan JSON; falling back to sequential plan")
        tasks_raw = _fallback_plan(bug_list)

    tasks = [FixTask(**t) for t in tasks_raw]

    # Log the plan
    parallel = [t for t in tasks if t.can_parallel]
    sequential = [t for t in tasks if not t.can_parallel]
    log._console.print(
        f"\n  [bold magenta]🗺  Task Plan[/bold magenta]  "
        f"[yellow]{len(tasks)}[/yellow] tasks  "
        f"([green]{len(parallel)} parallel[/green]  "
        f"[yellow]{len(sequential)} sequential[/yellow])"
    )
    for t in tasks:
        tag = "[green][parallel][/green]" if t.can_parallel else "[yellow][sequential][/yellow]"
        bugs_str = ", ".join(b.get("bug_function", "?") for b in t.bugs)
        log._console.print(f"      {tag}  [white]{t.task_id}[/white]  ({t.target_file})  bugs=[dim]{bugs_str}[/dim]")

    return tasks


def _fallback_plan(bug_list: list[dict]) -> list[dict]:
    """Simple fallback: one task per file, all parallel."""
    by_file: dict[str, list] = {}
    for b in bug_list:
        f = b.get("bug_file", "unknown")
        by_file.setdefault(f, []).append(b)
    result = []
    for filepath, bugs in by_file.items():
        import os
        name = "fix-" + os.path.splitext(os.path.basename(filepath))[0]
        result.append({
            "task_id": name,
            "target_file": filepath,
            "bugs": [{"bug_function": b.get("bug_function"), "description": b.get("description")} for b in bugs],
            "context_hint": " | ".join(b.get("description", "") for b in bugs),
            "can_parallel": True,
            "depends_on": [],
        })
    return result
