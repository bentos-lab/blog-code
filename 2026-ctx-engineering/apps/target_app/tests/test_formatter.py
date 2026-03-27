"""Tests for formatter.py — Bug 5: exp.category_name vs exp.category."""

import pytest
from target_app.models import Expense
from target_app.formatter import format_expense_row, format_expense_list


FOOD_EXP = Expense(id=1, title="Lunch", amount=12.5, category="food", date="2026-01-01")
TAGGED_EXP = Expense(id=2, title="Coffee", amount=3.0, category="food",
                     date="2026-01-02", tags=["work"])


def test_format_expense_row_no_crash():
    """format_expense_row must not raise AttributeError (Bug 5: exp.category_name)."""
    # BUG 5: raises AttributeError: 'Expense' object has no attribute 'category_name'
    result = format_expense_row(FOOD_EXP)
    assert isinstance(result, str)


def test_format_expense_row_contains_category():
    """Row must include the category name."""
    result = format_expense_row(FOOD_EXP)
    assert "food" in result, f"Expected 'food' in row, got: {result}"


def test_format_expense_row_tagged_vs_untagged():
    """Tagged expenses show ✓, untagged show ○."""
    untagged = format_expense_row(FOOD_EXP)
    tagged = format_expense_row(TAGGED_EXP)
    assert "○" in untagged
    assert "✓" in tagged


def test_format_expense_list_empty():
    assert "No expenses found" in format_expense_list([])
