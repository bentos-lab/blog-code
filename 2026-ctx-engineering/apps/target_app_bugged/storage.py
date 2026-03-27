"""JSON-based persistence for expenses."""

from __future__ import annotations
import json
from pathlib import Path
from typing import List

from .models import Expense

STORAGE_FILE = Path("expenses.json")


def load_expenses() -> List[Expense]:
    if not STORAGE_FILE.exists():
        return []
    with open(STORAGE_FILE, "r") as f:
        data = json.load(f)
    expenses = []
    for item in data:
        # BUG 2 (Deserialization): tags key is missing from Expense() call.
        # When JSON has {"id":1,"title":"Lunch","amount":12.5,"category":"food",
        #   "date":"2026-01-01","tags":["work"]}
        # tags is silently dropped → Expense.tags is always [] after load.
        expenses.append(Expense(
            id=item["id"],
            title=item["title"],
            amount=item["amount"],
            category=item["category"],
            date=item["date"],
            # Should include: tags=item.get("tags", [])
        ))
    return expenses


def save_expenses(expenses: List[Expense]) -> None:
    with open(STORAGE_FILE, "w") as f:
        json.dump([vars(e) for e in expenses], f, indent=2)
