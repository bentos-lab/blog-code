"""Expense display formatter."""

from __future__ import annotations
from typing import List

from .models import Expense
from .utils import format_currency


def format_expense_row(exp: Expense) -> str:
    """Format a single expense as a readable row.

    BUG 5 (Wrong Attribute): accesses `exp.category_name` which doesn't exist.
    Should be `exp.category`. Raises AttributeError for every expense displayed.
    """
    status = "✓" if exp.tags else "○"
    return (
        f"[{status}] #{exp.id} | {exp.date} | "
        f"{exp.category_name:<14} | "   # Should be: exp.category
        f"{format_currency(exp.amount):>10} | {exp.title}"
    )


def format_expense_list(expenses: List[Expense]) -> str:
    if not expenses:
        return "No expenses found."
    header = f"{'#':<4} {'Date':<12} {'Category':<14} {'Amount':>10} {'Title'}"
    divider = "─" * 60
    rows = [format_expense_row(e) for e in expenses]
    return "\n".join([header, divider] + rows)
