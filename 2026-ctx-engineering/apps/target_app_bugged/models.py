"""Expense data models."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


# BUG 1 (Logic Error): TAX_RATE is 17 (a percentage int) instead of 0.17 (a decimal).
# total_with_tax() multiplies by (1 + 17) = 18x instead of 1.17x → 1700% tax.
TAX_RATE = 17  # Should be: 0.17


class Category(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    OTHER = "other"

    @classmethod
    def from_string(cls, s: str) -> "Category":
        return cls(s.lower())


@dataclass
class Expense:
    id: int
    title: str
    amount: float
    category: str
    date: str            # ISO format: YYYY-MM-DD
    tags: List[str] = field(default_factory=list)

    def total_with_tax(self) -> float:
        """Return amount including tax."""
        return self.amount * (1 + TAX_RATE)

    def is_overdue(self, reference_date: str) -> bool:
        """Return True if this expense's date is before the reference date."""
        return self.date < reference_date
