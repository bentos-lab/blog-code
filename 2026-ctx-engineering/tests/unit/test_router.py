"""Unit tests for src/router.py."""

import pytest
from src.router import route


def test_routes_to_analyzer_when_no_bug_report():
    state = {"bug_report": None, "proposed_fix": None, "fix_applied": False}
    assert route(state) == "analyzer"


def test_routes_to_researcher_after_analysis():
    state = {
        "bug_report": {"bug_file": "target_app/storage.py"},
        "proposed_fix": None,
        "fix_applied": False,
    }
    assert route(state) == "researcher"


def test_routes_to_executor_after_research():
    state = {
        "bug_report": {"bug_file": "target_app/storage.py"},
        "proposed_fix": "Wrap with try/except",
        "fix_applied": False,
    }
    assert route(state) == "executor"


def test_routes_to_tester_after_fix():
    state = {
        "bug_report": {"bug_file": "target_app/storage.py"},
        "proposed_fix": "Wrap with try/except",
        "fix_applied": True,
    }
    assert route(state) == "tester"
