"""Benchmark harness — runs both agents N times and compares results.

Outputs:
- results/benchmark_YYYY-MM-DD.json (raw data)
- Rich pretty-printed comparison table
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .config import load_config
from .agent_traditional import run_traditional_agent
from .planner import run_context_agent
from .reset import reset_target_app


# Fixed token pricing (USD per 1k tokens) — update when pricing changes
PRICING = {
    "openai": {"input": 0.00015, "output": 0.0006},    # gpt-4o-mini
    "anthropic": {"input": 0.0008, "output": 0.0024},   # claude-3-5-haiku
    "google": {"input": 0.0001, "output": 0.0004},      # gemini-2.0-flash
}


def _estimate_cost(tokens: int, provider: str) -> float:
    """Rough cost estimate — assumes 75% input / 25% output split."""
    pricing = PRICING.get(provider, PRICING["openai"])
    input_tokens = int(tokens * 0.75)
    output_tokens = tokens - input_tokens
    return round(
        (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1000,
        4,
    )


def run_benchmark() -> None:
    config = load_config()
    console = Console()
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    n_runs = config.benchmark_runs
    console.print(f"\n[bold cyan]Context Engineering Benchmark[/bold cyan]")
    console.print(f"Provider: [green]{config.provider}[/green]  Model: [green]{config.model}[/green]")
    console.print(f"Runs per agent: [yellow]{n_runs}[/yellow]  Max turns: [yellow]{config.max_turns}[/yellow]\n")

    # Verify snapshot exists before starting
    try:
        reset_target_app(silent=True)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        return

    trad_results = []
    ctx_results = []

    for i in range(n_runs):
        console.rule(f"Run {i + 1}/{n_runs} — Traditional Agent")
        reset_target_app(silent=True)
        from .logger import session_tokens
        session_tokens.reset()
        t0 = time.monotonic()
        result = run_traditional_agent(config)
        result["elapsed_s"] = round(time.monotonic() - t0, 1)
        result["cost_usd"] = _estimate_cost(result.get("total_tokens", 0), config.provider)
        trad_results.append(result)
        console.print(
            f"  success={result['success']}  turns={result['turns']}  "
            f"tokens={result.get('total_tokens', '?')}  cost=${result['cost_usd']}"
        )

    for i in range(n_runs):
        console.rule(f"Run {i + 1}/{n_runs} — Context-Engineered Agent")
        reset_target_app(silent=True)
        from .logger import session_tokens
        session_tokens.reset()
        t0 = time.monotonic()
        result = run_context_agent(config)
        result["elapsed_s"] = round(time.monotonic() - t0, 1)
        result["cost_usd"] = _estimate_cost(result.get("total_tokens", 0), config.provider)
        ctx_results.append(result)
        console.print(
            f"  success={result['success']}  turns={result['turns']}  "
            f"tokens={result.get('total_tokens', '?')}  cost=${result['cost_usd']}"
        )

    # Aggregate
    def agg(results: list) -> dict:
        if not results: return {}
        successes = sum(1 for r in results if r["success"])
        return {
            "success_rate": f"{successes}/{len(results)} ({100 * successes // len(results)}%)",
            "avg_turns": round(sum(r["turns"] for r in results) / len(results), 1),
            "avg_tokens": round(sum(r.get("total_tokens", 0) for r in results) / len(results)),
            "avg_cost_usd": round(sum(r["cost_usd"] for r in results) / len(results), 4),
        }

    trad_agg = agg(trad_results)
    ctx_agg = agg(ctx_results)

    # Print comparison table
    console.print()
    table = Table(title="Benchmark Results", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="dim")
    table.add_column("Traditional", justify="right")
    table.add_column("Context-Engineered", justify="right")
    table.add_column("Δ", justify="right")

    def delta(a, b):
        try:
            diff = float(str(b).split("/")[0]) - float(str(a).split("/")[0])
            return f"+{diff:.0f}" if diff > 0 else f"{diff:.0f}"
        except Exception:
            return "—"

    table.add_row("Success Rate", trad_agg.get("success_rate", ""), ctx_agg.get("success_rate", ""), "")
    table.add_row("Avg Turns", str(trad_agg.get("avg_turns", "")), str(ctx_agg.get("avg_turns", "")),
                  delta(ctx_agg.get("avg_turns"), trad_agg.get("avg_turns")))
    table.add_row("Avg Tokens", str(trad_agg.get("avg_tokens", "")), str(ctx_agg.get("avg_tokens", "")),
                  delta(ctx_agg.get("avg_tokens"), trad_agg.get("avg_tokens")))
    table.add_row("Avg Cost (USD)", f"${trad_agg.get('avg_cost_usd', 0)}", f"${ctx_agg.get('avg_cost_usd', 0)}", "")
    console.print(table)

    # Save results
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {"provider": config.provider, "model": config.model, "n_runs": n_runs},
        "traditional": {"runs": trad_results, "aggregate": trad_agg},
        "context_engineered": {"runs": ctx_results, "aggregate": ctx_agg},
    }
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = results_dir / f"benchmark_{date_str}.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    console.print(f"\n[green]Results saved to {out_path}[/green]")


if __name__ == "__main__":
    run_benchmark()
