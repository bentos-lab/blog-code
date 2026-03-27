"""Auto-reset: restores apps/target_app/ from the bugged snapshot before each run.

Usage:
    from src.reset import reset_target_app
    reset_target_app()   # call at start of any run script

The canonical buggy snapshot lives in apps/target_app_bugged/.
After a run (whether the agent fixed things or not), reset() puts
the bugs back so the next comparison starts from the same baseline.
"""

import shutil
from pathlib import Path

from . import console_logger as log

SNAPSHOT_DIR = Path("apps/target_app_bugged")
TARGET_DIR = Path("apps/target_app")


def reset_target_app(silent: bool = False) -> None:
    """Restore target_app/ from the buggy snapshot.

    Args:
        silent: If True, suppress console output (used in benchmark loops).

    Raises:
        FileNotFoundError: If the snapshot directory doesn't exist.
    """
    if not SNAPSHOT_DIR.exists():
        raise FileNotFoundError(
            f"Snapshot not found at '{SNAPSHOT_DIR}'. "
            "Run `uv run python -m src.init_snapshot` to create it."
        )

    if not silent:
        log._console.print(
            f"\n[bold yellow]⟳ Reset[/bold yellow]  "
            f"restoring [white]apps/target_app/[/white] from [dim]apps/target_app_bugged/[/dim] snapshot"
        )

    # Remove current (possibly patched) target_app
    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)

    # Restore from snapshot (exclude __pycache__)
    shutil.copytree(
        str(SNAPSHOT_DIR),
        str(TARGET_DIR),
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
    )

    if not silent:
        py_files = list(TARGET_DIR.rglob("*.py"))
        log._console.print(
            f"  [green]✓[/green] Restored {len(py_files)} Python files  "
            f"[dim](bugs are back)[/dim]\n"
        )


def create_snapshot() -> None:
    """Create the buggy snapshot from the current target_app/.

    Call this once to initialize the snapshot, before any agent runs.
    """
    if not TARGET_DIR.exists():
        raise FileNotFoundError("apps/target_app/ does not exist.")

    if SNAPSHOT_DIR.exists():
        shutil.rmtree(SNAPSHOT_DIR)

    shutil.copytree(
        str(TARGET_DIR),
        str(SNAPSHOT_DIR),
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
    )
    log._console.print(
        f"[green]✓ Snapshot created[/green]  "
        f"[dim]{SNAPSHOT_DIR}/ → {len(list(SNAPSHOT_DIR.rglob('*.py')))} Python files[/dim]"
    )
