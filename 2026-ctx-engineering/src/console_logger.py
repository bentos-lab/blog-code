"""Console logger — rich step-by-step event logging for agents.

Emits structured, color-coded output to stdout so users can see exactly:
- Which agent / sub-agent is running
- What context slice was sent (size in tokens estimate)
- What tool was called
- What the LLM's thinking/decision was
- What change was applied
- What the test result was
"""

from __future__ import annotations

from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich import print as rprint

_console = Console(highlight=False)


# ─── Agent lifecycle ──────────────────────────────────────────────────────────

def agent_start(agent_name: str, mode: str = "") -> None:
    label = f"[bold cyan]{agent_name}[/bold cyan]"
    tag = f"  [dim]{mode}[/dim]" if mode else ""
    _console.print(Rule(f"{label}{tag}", style="cyan"))


def agent_turn(turn: int, max_turns: int, agent_name: str = "") -> None:
    prefix = f"[dim]{agent_name} › [/dim]" if agent_name else ""
    _console.print(f"\n{prefix}[bold yellow]Turn {turn}/{max_turns}[/bold yellow]")


def agent_done(agent_name: str, success: bool, turns: int) -> None:
    icon = "✓" if success else "✗"
    color = "green" if success else "red"
    _console.print(
        f"\n[{color}]{icon} {agent_name} finished[/{color}]  "
        f"[dim]turns={turns}  success={success}[/dim]"
    )


# ─── Routing & dispatch ───────────────────────────────────────────────────────

def routing_decision(next_agent: str, reason: str = "") -> None:
    _console.print(
        f"  [bold magenta]→ Router[/bold magenta]  dispatching to "
        f"[bold white]{next_agent}[/bold white]"
        + (f"  [dim]({reason})[/dim]" if reason else "")
    )


def compaction_start(turn: int, history_len: int) -> None:
    _console.print(
        f"  [yellow]⊛ Compactor[/yellow]  turn={turn}  "
        f"compressing {history_len} history entries → structured JSON"
    )


def compaction_done(keys: list[str]) -> None:
    _console.print(f"  [yellow]⊛ Compactor[/yellow]  summary keys: {keys}")


def compaction_done_with_sizes(before_chars: int, after_chars: int) -> None:
    """Show before/after token counts for compaction."""
    before_tokens = before_chars // 4
    after_tokens = after_chars // 4
    reduction_pct = int(100 * (1 - after_tokens / max(before_tokens, 1)))
    _console.print(
        f"  [yellow]⊛ Compactor[/yellow]  "
        f"~{before_tokens:,} → ~{after_tokens:,} tokens  "
        f"[green]▼ {reduction_pct}% reduction[/green]"
    )


def summarization_done(before_chars: int, after_chars: int) -> None:
    """Show before/after token counts for irreversible LLM summarization."""
    before_tokens = before_chars // 4
    after_tokens = after_chars // 4
    reduction_pct = int(100 * (1 - after_tokens / max(before_tokens, 1)))
    _console.print(
        f"  [magenta]📝 Summarizer[/magenta]  "
        f"~{before_tokens:,} → ~{after_tokens:,} tokens  "
        f"[green]▼ {reduction_pct}% reduction[/green]  [dim][irreversible][/dim]"
    )


# ─── Context slice visibility ─────────────────────────────────────────────────

def context_slice(agent_name: str, description: str, char_count: int) -> None:
    """Log what context slice was given to a sub-agent."""
    _console.print(
        f"  [dim]  context → {agent_name}:[/dim] {description}  "
    )


def context_size_warning(turn: int, char_count: int, delta_chars: int = 0) -> None:
    """Warn when traditional agent is dumping a huge context."""
    tokens = char_count // 4
    color = "red" if tokens > 20000 else "yellow"
    delta_str = ""
    if delta_chars > 0:
        delta_tokens = delta_chars // 4
        delta_str = f"  [dim]▲ +{delta_tokens:,} from last turn[/dim]"
    _console.print(
        f"  [{color}]⚠ Context dump[/{color}]  turn={turn}  "
        f"~{tokens:,} tokens{delta_str}  [dim](monolithic — dumps ALL files every turn)[/dim]"
    )


def history_size(cycle: int, char_count: int) -> None:
    """Show how large the accumulated history is entering a new cycle."""
    tokens = char_count // 4
    color = "cyan" if tokens < 5000 else "yellow"
    _console.print(
        f"  [{color}]📋 History[/{color}]  cycle={cycle}  "
        f"~{tokens:,} tokens  [dim](accumulated from prior cycles)[/dim]"
    )


def context_budget(turn_or_cycle: int, char_count: int, free_pct: float) -> None:
    """Show occupied vs free context budget. Fires before every reduction decision."""
    tokens = char_count // 4
    # Clamp to [0, 100] — context can exceed the cap when file dump alone is large
    free_clamped = max(0.0, min(1.0, free_pct))
    occupied_pct = int((1.0 - free_clamped) * 100)
    free_display = int(free_clamped * 100)
    if free_clamped > 0.40:
        color = "green"
        note = "safe"
    elif free_clamped > 0.20:
        color = "yellow"
        note = "watch"
    else:
        color = "red"
        note = "fires"
    label = f"turn={turn_or_cycle}" if turn_or_cycle else ""
    _console.print(
        f"  [{color}]📊 Context[/{color}]  {label}  ~{tokens:,} tokens  "
        f"occupied: {occupied_pct}%  free: {free_display}%  "
        f"[dim]← {note}[/dim]"
    )


# ─── Tool calls ───────────────────────────────────────────────────────────────

def tool_call(tool_name: str, args: str) -> None:
    _console.print(f"  [bold blue]⚙ Tool[/bold blue]  {tool_name}({args})")


def tool_result(result_summary: str, success: bool = True) -> None:
    icon = "✓" if success else "✗"
    color = "green" if success else "red"
    _console.print(f"    [{color}]{icon}[/{color}] {result_summary}")


# ─── LLM thinking ─────────────────────────────────────────────────────────────

def llm_thinking(agent_name: str, prompt_preview: str, max_chars: int = 200) -> None:
    """Log a preview of what's being sent to the LLM."""
    preview = prompt_preview[:max_chars].replace("\n", " ").strip()
    if len(prompt_preview) > max_chars:
        preview += "…"
    _console.print(
        f"  [bold green]🤔 LLM[/bold green]  [dim]{agent_name}[/dim]  "
        f"[italic dim]\"{preview}\"[/italic dim]"
    )


def llm_response(agent_name: str, response_preview: str, max_chars: int = 300) -> None:
    """Log a preview of the LLM's response."""
    preview = response_preview[:max_chars].replace("\n", " ").strip()
    if len(response_preview) > max_chars:
        preview += "…"
    _console.print(
        f"  [bold green]💬 Response[/bold green]  [dim]{agent_name}[/dim]  "
        f"[italic dim]\"{preview}\"[/italic dim]"
    )


# ─── Analysis output ──────────────────────────────────────────────────────────

def bug_report(report: dict) -> None:
    if not report or not report.get("bug_file"):
        _console.print("  [red]✗ Analyzer[/red]  could not identify bug file")
        return
    _console.print(
        f"  [bold red]🐛 Bug found[/bold red]  "
        f"file=[white]{report.get('bug_file')}[/white]  "
        f"fn=[white]{report.get('bug_function')}[/white]  "
        f"type=[yellow]{report.get('bug_type')}[/yellow]\n"
        f"    [dim]{report.get('description', '')}[/dim]"
    )


def fix_description(fix: str) -> None:
    preview = fix[:250].replace("\n", " ")
    _console.print(f"  [bold cyan]💡 Fix plan[/bold cyan]  [italic]{preview}[/italic]")


def patch_applied(file_path: str, success: bool) -> None:
    icon = "✓" if success else "✗"
    color = "green" if success else "red"
    _console.print(f"  [{color}]{icon} Patch[/{color}]  [white]{file_path}[/white]")


# ─── Test results ─────────────────────────────────────────────────────────────

def test_result(passed: int, failed: int, summary: str, success: bool) -> None:
    if success:
        _console.print(
            f"  [bold green]✓ Tests[/bold green]  {summary}"
        )
    else:
        _console.print(
            f"  [bold red]✗ Tests[/bold red]  "
            f"passed={passed}  failed=[red]{failed}[/red]  {summary}"
        )


def test_output_preview(output: str, max_lines: int = 8) -> None:
    """Show first few lines of pytest output."""
    lines = [l for l in output.splitlines() if l.strip()][:max_lines]
    for line in lines:
        _console.print(f"    [dim]{line}[/dim]")


# ─── Parallel dispatch events ─────────────────────────────────────────────────

def worker_done(task_id: str, success: bool, elapsed_ms: int) -> None:
    """Log when a parallel worker completes its task."""
    icon = "✓" if success else "✗"
    color = "green" if success else "red"
    elapsed = f"  [dim]{elapsed_ms}ms[/dim]" if elapsed_ms > 0 else ""
    _console.print(
        f"      [{color}]{icon} Worker[/{color}]  [white]{task_id}[/white]{elapsed}"
    )


def parallel_done(n_success: int, n_failed: int) -> None:
    """Log the aggregate result of all parallel workers."""
    if n_failed == 0:
        _console.print(
            f"\n  [bold green]✓ All {n_success} workers completed successfully[/bold green]"
        )
    else:
        _console.print(
            f"\n  [yellow]⚠ Parallel batch done[/yellow]  "
            f"[green]{n_success} ok[/green]  [red]{n_failed} failed[/red]"
        )
