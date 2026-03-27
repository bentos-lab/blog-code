"""Run the traditional agent on the large codebase and print results."""

from .config import load_config
from .agent_traditional import run_traditional_agent
from .reset_large import reset_target_app_large
from rich.console import Console

TARGET_FILES_LARGE = [
    "apps/target_app_large/models.py",
    "apps/target_app_large/pricing.py",
    "apps/target_app_large/validator.py",
    "apps/target_app_large/storage.py",
    "apps/target_app_large/search.py",
    "apps/target_app_large/reports.py",
    "apps/target_app_large/exporter.py",
    "apps/target_app_large/notifier.py",
    "apps/target_app_large/scheduler.py",
    "apps/target_app_large/audit.py",
    "apps/target_app_large/permissions.py",
    "apps/target_app_large/processor.py",
    "apps/target_app_large/cli.py",
    "apps/target_app_large/manager.py",
    "apps/target_app_large/main.py",
]
TEST_DIR_LARGE = "apps/target_app_large/tests"


def main():
    console = Console(highlight=False)
    config = load_config()

    console.print("\n[bold red]Traditional Agent (Large — 15 files)[/bold red]")
    console.print(f"Provider: [green]{config.provider}[/green]  Model: [green]{config.model}[/green]  Max turns: [yellow]{config.max_turns}[/yellow]")

    # Reset the codebase to the buggy snapshot
    try:
        reset_target_app_large()
    except FileNotFoundError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        return

    from .logger import session_tokens
    session_tokens.reset()

    import time
    t0 = time.monotonic()
    result = run_traditional_agent(config, target_files=TARGET_FILES_LARGE, test_dir=TEST_DIR_LARGE)
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
