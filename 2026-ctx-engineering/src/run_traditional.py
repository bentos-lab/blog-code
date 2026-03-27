"""Run the traditional agent interactively and print results."""

from .config import load_config
from .agent_traditional import run_traditional_agent
from .reset import reset_target_app
from rich.console import Console

def main():
    console = Console(highlight=False)
    config = load_config()

    console.print("\n[bold red]Traditional Agent (Monolithic)[/bold red]")
    console.print(f"Provider: [green]{config.provider}[/green]  Model: [green]{config.model}[/green]  Max turns: [yellow]{config.max_turns}[/yellow]")

    # Phase B: auto-reset the codebase to the buggy snapshot
    try:
        reset_target_app()
    except FileNotFoundError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        return

    from .logger import session_tokens
    session_tokens.reset()

    import time
    t0 = time.monotonic()
    result = run_traditional_agent(config)
    elapsed = time.monotonic() - t0

    console.rule("[bold]Finished[/bold]")
    status = "[green]✓ PASSED[/green]" if result["success"] else "[red]✗ FAILED[/red]"
    console.print(f"\nResult:  {status}")
    console.print(f"Time:    [cyan]{elapsed:.1f}s[/cyan]")
    console.print(f"Turns:   [yellow]{result['turns']}[/yellow]")
    console.print(f"Tokens:  [cyan]~{result.get('total_tokens', 0)}[/cyan]")
    console.print(f"Summary: [dim]{result['final_summary']}[/dim]\n")


if __name__ == "__main__":
    main()
