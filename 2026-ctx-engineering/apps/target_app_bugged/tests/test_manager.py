"""Tests for manager.py — Bug 3 (date filter type mismatch) and Bug 4 (sort typo)."""

import pytest
from unittest.mock import patch, MagicMock

from target_app.models import Expense
from target_app.manager import ExpenseManager


def _make_manager(expenses):
    mgr = ExpenseManager.__new__(ExpenseManager)
    mgr.expenses = expenses
    return mgr


EXPENSES = [
    Expense(id=1, title="Coffee",    amount=4.5,  category="food",      date="2026-01-10"),
    Expense(id=2, title="Bus",       amount=2.0,  category="transport", date="2026-01-15"),
    Expense(id=3, title="Cinema",    amount=15.0, category="entertainment", date="2026-01-20"),
    Expense(id=4, title="Groceries", amount=45.0, category="food",      date="2026-02-01"),
]


def test_filter_by_date_range_returns_correct_items():
    """filter_by_date_range with ISO string bounds should work (Bug 3: TypeError when datetime passed)."""
    mgr = _make_manager(list(EXPENSES))
    result = mgr.filter_by_date_range("2026-01-10", "2026-01-20")
    ids = [e.id for e in result]
    assert ids == [1, 2, 3], f"Expected [1,2,3] got {ids}"


def test_filter_by_date_range_with_datetime_objects():
    """filter_by_date_range must handle datetime objects passed as start/end (Bug 3)."""
    from datetime import datetime
    mgr = _make_manager(list(EXPENSES))
    start = datetime(2026, 1, 10)
    end = datetime(2026, 1, 20)
    # BUG 3: comparing str <= datetime raises TypeError
    result = mgr.filter_by_date_range(start, end)
    assert len(result) == 3


def test_get_summary_does_not_crash():
    """get_summary() must not raise AttributeError (Bug 4: e.data typo)."""
    mgr = _make_manager(list(EXPENSES))
    # BUG 4: AttributeError: 'Expense' object has no attribute 'data'
    summary = mgr.get_summary()
    assert summary["count"] == 4
    assert "by_category" in summary


def test_get_summary_totals():
    mgr = _make_manager(list(EXPENSES))
    summary = mgr.get_summary()
    assert abs(summary["total"] - 66.5) < 0.01


def test_filter_by_category():
    mgr = _make_manager(list(EXPENSES))
    food = mgr.filter_by_category("food")
    assert len(food) == 2
