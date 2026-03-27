"""Auto-reset: restores apps/target_app_large/ from the bugged snapshot before each run.

Usage:
    from src.reset_large import reset_target_app_large
    reset_target_app_large()   # call at start of any large-app run script

The canonical buggy snapshot lives in apps/target_app_large_bugged/.
After a run (whether the agent fixed things or not), reset() puts
the bugs back so the next comparison starts from the same baseline.
"""

import shutil
from pathlib import Path

from . import console_logger as log

SNAPSHOT_DIR = Path("apps/target_app_large_bugged")
TARGET_DIR = Path("apps/target_app_large")


def reset_target_app_large(silent: bool = False) -> None:
    """Restore apps/target_app_large/ from the buggy snapshot.

    Args:
        silent: If True, suppress console output (used in benchmark loops).

    Raises:
        FileNotFoundError: If the snapshot directory doesn't exist.
    """
    if not SNAPSHOT_DIR.exists():
        raise FileNotFoundError(
            f"Snapshot not found at '{SNAPSHOT_DIR}'. "
            "Ensure apps/target_app_large_bugged/ exists."
        )

    if not silent:
        log._console.print(
            f"\n[bold yellow]⟳ Reset[/bold yellow]  "
            f"restoring [white]apps/target_app_large/[/white] from [dim]apps/target_app_large_bugged/[/dim] snapshot"
        )

    # Remove current (possibly patched) target_app_large
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


def create_snapshot_large() -> None:
    """Create the buggy snapshot from the current apps/target_app_large/.

    Call this once to initialize the snapshot, before any agent runs.
    """
    if not TARGET_DIR.exists():
        raise FileNotFoundError("apps/target_app_large/ does not exist.")

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
