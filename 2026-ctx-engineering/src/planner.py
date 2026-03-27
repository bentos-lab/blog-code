"""Central Planner — cycle-based parallel orchestrator.

Architecture upgrade: Parallel Sub-Agent Pattern
─────────────────────────────────────────────────
Each "logical turn" (cycle) runs:
  1. Analyzer    → identify ALL remaining bugs in one LLM pass
  2. Task Planner → build dependency-aware fix plan (groups same-file bugs)
  3. Parallel Dispatch → spawn N Executor workers concurrently (one per file)
  4. Tester      → verify; if still failing, repeat from step 1

Turn counting:
  - All parallel workers in a cycle count as 1 turn
  - Expected: 1–3 cycles for the 7-bug Expense Tracker

Context Engineering patterns applied:
  1. Progressive Disclosure — planner holds only signatures, not full files
  2. Context Routing        — Central Researcher builds the plan
  3. Context Isolation      — each Executor worker sees only its target file
  4. Context Reduction      — compaction after each cycle (not every turn)
  5. Layered Action Space   — workers receive descriptions, not code
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from langchain_core.language_models import BaseChatModel

from .config import Config
from .llm import get_llm, get_cheap_llm
from .compactor import compact_history
from .summarizer import summarize
from .subagents import tester
from .subagents.analyzer import analyze_all
from .subagents.task_planner import plan_tasks, FixTask
from .subagents.executor import execute_task
from .tools import read_file_signatures
from . import console_logger as log

TARGET_FILES = [
    "apps/target_app/models.py",
    "apps/target_app/storage.py",
    "apps/target_app/manager.py",
    "apps/target_app/formatter.py",
    "apps/target_app/utils.py",
    "apps/target_app/cli.py",
    "apps/target_app/main.py",
]

MAX_CYCLES = 5  # Fallback only — overridden by config.max_turns at runtime
FULL_HISTORY_KEEP = 2  # cycles kept verbatim in the ring buffer


def _execute_parallel(tasks: list[FixTask], llm: BaseChatModel) -> list[dict]:
    """Dispatch tasks using a thread pool. One worker per FixTask (= per file).

    Tasks with can_parallel=False wait for all parallel tasks to finish first.
    This prevents write-after-write conflicts since each worker owns a unique file.

    Args:
        tasks: List of FixTask objects from task_planner.
        llm: LLM to pass to each executor (one call per thread).

    Returns:
        List of execution result dicts.
    """
    parallel_tasks = [t for t in tasks if t.can_parallel]
    sequential_tasks = [t for t in tasks if not t.can_parallel]

    results = []

    # ── Phase 1: Run all parallel tasks concurrently ──────────────────────────
    if parallel_tasks:
        log._console.print(
            f"\n  [bold cyan]⚡ Spawning {len(parallel_tasks)} parallel workers[/bold cyan]  "
            f"[dim](each owns a unique file — no write conflicts)[/dim]"
        )
        with ThreadPoolExecutor(max_workers=len(parallel_tasks)) as pool:
            futures = {
                pool.submit(execute_task, llm, task): task
                for task in parallel_tasks
            }
            for future in as_completed(futures):
                task = futures[future]
                t0 = time.monotonic()
                try:
                    result = future.result()
                    elapsed_ms = round((time.monotonic() - t0) * 1000)
                    log.worker_done(task.task_id, result["patched"], elapsed_ms)
                    results.append(result)
                except Exception as e:
                    log._console.print(f"  [red]✗ Worker {task.task_id} crashed: {e}[/red]")
                    results.append({"patched": False, "task_id": task.task_id, "path": task.target_file, "message": str(e)})

    # ── Phase 2: Run sequential tasks one-by-one ──────────────────────────────
    if sequential_tasks:
        log._console.print(
            f"\n  [yellow]⟳ Sequential tasks[/yellow]  "
            f"[dim]{len(sequential_tasks)} task(s) with dependencies[/dim]"
        )
        for task in sequential_tasks:
            result = execute_task(llm, task)
            log.worker_done(task.task_id, result["patched"], 0)
            results.append(result)

    return results


def run_context_agent(config: Config, target_files: list[str] | None = None, test_dir: str = "apps/target_app/tests") -> dict:
    """Run the parallel context-engineered agent.

    Returns:
        Dict with: success (bool), turns/cycles (int), total_tokens (int)
    """
    log.agent_start("Context-Engineered Agent", "parallel orchestrator — cycle-based")

    llm: BaseChatModel = get_llm(config, agent_type="planner")
    cheap_llm: BaseChatModel = get_cheap_llm(config, agent_type="compactor")

    # Progressive Disclosure: planner holds only signatures
    files = target_files or TARGET_FILES
    file_signatures: dict[str, str] = {}
    total_sig_chars = 0
    for path in files:
        sigs = read_file_signatures(path)
        file_signatures[path] = sigs
        total_sig_chars += len(sigs)
    log.context_slice("Planner", f"signatures for {len(files)} files", total_sig_chars)

    # Quick early exit if already passing
    log.tool_call("tester.verify", "initial check")
    test_result = tester.verify(test_dir)
    if test_result["success"]:
        log.test_result(test_result["passed"], test_result["failed"], test_result["summary"], True)
        return {"success": True, "turns": 0, "total_tokens": 0, "final_summary": "Already passing"}

    compact_summary: dict | None = None
    full_history: list = []
    compaction_count: int = 0
    success = False
    cycle = 0
    max_cycles = config.max_turns  # 1 cycle == 1 turn; respects MAX_TURNS from .env

    for cycle in range(1, max_cycles + 1):
        log._console.print(
            f"\n  [bold white]── Cycle {cycle}/{max_cycles}[/bold white]  "
            f"{'─' * 40}"
        )

        # ── Step 1: Analyze ALL remaining bugs ────────────────────────────────
        analyzer_llm = get_llm(config, agent_type="analyzer")
        bug_list = analyze_all(analyzer_llm, test_result["output"], file_signatures)

        if not bug_list:
            log._console.print("  [yellow]⚠ Analyzer returned no bugs — stopping[/yellow]")
            break

        # ── Step 2: Central Researcher builds the task plan ──────────────────
        planner_llm = get_llm(config, agent_type="task_planner")
        fix_tasks = plan_tasks(planner_llm, bug_list, file_signatures)

        if not fix_tasks:
            log._console.print("  [yellow]⚠ Task planner returned empty plan — stopping[/yellow]")
            break

        # ── Step 3: Parallel + Sequential Executor dispatch ──────────────────
        executor_llm = get_llm(config, agent_type="executor")
        exec_results = _execute_parallel(fix_tasks, executor_llm)
        n_success = sum(1 for r in exec_results if r["patched"])
        n_failed = len(exec_results) - n_success
        log.parallel_done(n_success, n_failed)

        # ── Step 4: Threshold-aware context reduction ────────────────────────
        cycle_entry = {
            "cycle": cycle,
            "test_output": test_result.get("output", ""),
            "bugs_found": [vars(b) if hasattr(b, "__dict__") else b for b in bug_list],
            "tasks_planned": [vars(t) if hasattr(t, "__dict__") else t for t in fix_tasks],
            "exec_results": exec_results,
            "test_summary_after": test_result.get("summary", ""),
        }
        full_history.append(cycle_entry)

        max_chars = config.max_context_tokens * 4
        threshold_chars = int(max_chars * config.context_reduction_threshold)
        context_chars = (len(str(compact_summary)) if compact_summary else 0) + \
                        sum(len(str(e)) for e in full_history)
        free_pct = 1.0 - (context_chars / max_chars)
        log.context_budget(cycle, context_chars, free_pct)

        if context_chars > threshold_chars:
            before = context_chars
            if compaction_count < config.max_compactions:
                # Stage 1: Reversible compaction — pure Python, no LLM
                compact_summary = compact_history(full_history)
                full_history = full_history[-FULL_HISTORY_KEEP:]
                compaction_count += 1
                after = (len(str(compact_summary)) + sum(len(str(e)) for e in full_history))
                log.compaction_done_with_sizes(before, after)
            else:
                # Stage 2: Irreversible summarization — LLM, only after MAX_COMPACTIONS exhausted
                compact_summary = summarize(cheap_llm, compact_summary, full_history)
                full_history = full_history[-FULL_HISTORY_KEEP:]
                compaction_count = 0  # reset after summarization
                after = (len(str(compact_summary)) + sum(len(str(e)) for e in full_history))
                log.summarization_done(before, after)

        # ── Step 5: Verify ────────────────────────────────────────────────────
        log.tool_call("tester.verify", f"after cycle {cycle}")
        test_result = tester.verify(test_dir)
        log.test_result(
            test_result["passed"],
            test_result["failed"],
            test_result["summary"],
            test_result["success"],
        )
        if test_result.get("failed", 0) > 0:
            log.test_output_preview(test_result["output"])

        if test_result["success"]:
            success = True
            break

    from .logger import session_tokens
    log.agent_done("Context-Engineered Agent", success, cycle)

    return {
        "success": success,
        "turns": cycle,
        "total_tokens": session_tokens.total_tokens,
        "final_summary": test_result["summary"],
    }
