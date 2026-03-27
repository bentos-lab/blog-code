"""Business logic: ExpenseManager."""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from .models import Expense
from .storage import load_expenses, save_expenses


class ExpenseManager:
    def __init__(self) -> None:
        self.expenses: List[Expense] = load_expenses()

    def add(self, title: str, amount: float, category: str,
            date: str, tags: Optional[List[str]] = None) -> Expense:
        new_id = max((e.id for e in self.expenses), default=0) + 1
        exp = Expense(id=new_id, title=title, amount=amount,
                      category=category, date=date, tags=tags or [])
        self.expenses.append(exp)
        save_expenses(self.expenses)
        return exp

    def get_all(self) -> List[Expense]:
        return list(self.expenses)

    def filter_by_category(self, category: str) -> List[Expense]:
        return [e for e in self.expenses if e.category == category]

    def filter_by_date_range(self, start: str, end: str) -> List[Expense]:
        # BUG 3 (Type Mismatch): start and end are str "YYYY-MM-DD".
        # Comparison works for ISO strings (lexicographic == chronological),
        # BUT the docstring says datetime objects — and the tests pass datetime objects.
        # When called with datetime objects, `e.date <= end` (str <= datetime) raises TypeError.
        return [e for e in self.expenses if start <= e.date <= end]

    def get_summary(self) -> dict:
        if not self.expenses:
            return {"total": 0.0, "count": 0, "by_category": {}}

        # BUG 4 (Typo cross-file): sorts by `e.data` instead of `e.date`.
        # `e.data` doesn't exist → AttributeError at runtime.
        sorted_expenses = sorted(self.expenses, key=lambda e: e.data)  # Should be: e.date

        by_cat: dict = {}
        for e in self.expenses:
            by_cat[e.category] = by_cat.get(e.category, 0.0) + e.amount

        return {
            "total": sum(e.amount for e in self.expenses),
            "count": len(self.expenses),
            "by_category": by_cat,
            "most_recent": sorted_expenses[-1].title if sorted_expenses else None,
        }

    def delete(self, expense_id: int) -> bool:
        before = len(self.expenses)
        self.expenses = [e for e in self.expenses if e.id != expense_id]
        if len(self.expenses) < before:
            save_expenses(self.expenses)
            return True
        return False
