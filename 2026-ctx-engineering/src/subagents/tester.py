"""Tester sub-agent — runs pytest and returns a structured result.

This sub-agent has no LLM calls — it's a pure tool call wrapper.
Provides a clean interface for the planner to check progress.
"""

from ..tools import run_tests as _run_tests


def verify(test_dir: str = "apps/target_app/tests") -> dict:
    """Run the target app test suite and return structured results.

    Returns:
        Dict with:
            success (bool): True if all tests passed
            summary (str): Short summary line (e.g. "4 passed" or "2 failed, 2 passed")
            output (str): Full pytest output
            passed (int): Count of passed tests
            failed (int): Count of failed tests
    """
    result = _run_tests(test_dir)

    # Parse counts from summary line
    summary = result.get("summary", "")
    passed = _count(summary, "passed")
    failed = _count(summary, "failed")

    return {
        "success": result["success"],
        "summary": summary,
        "output": result["output"],
        "passed": passed,
        "failed": failed,
    }


def _count(summary: str, keyword: str) -> int:
    """Extract count of keyword (passed/failed) from pytest summary line."""
    import re
    match = re.search(rf"(\d+)\s+{keyword}", summary)
    return int(match.group(1)) if match else 0
