"""Tests for storage.py — Bug 2: tags dropped during deserialization."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from target_app.models import Expense
from target_app.storage import load_expenses, save_expenses


def test_tags_survive_roundtrip(tmp_path):
    """Tags must be preserved when saved and re-loaded (Bug 2: they're dropped)."""
    storage_file = tmp_path / "expenses.json"
    exp = Expense(id=1, title="Coffee", amount=4.5, category="food",
                  date="2026-01-01", tags=["work", "morning"])
    with patch("target_app.storage.STORAGE_FILE", storage_file):
        save_expenses([exp])
        loaded = load_expenses()

    # BUG 2: tags is always [] after load
    assert loaded[0].tags == ["work", "morning"], (
        f"Expected tags=['work','morning'], got tags={loaded[0].tags}"
    )


def test_load_empty_when_no_file(tmp_path):
    missing = tmp_path / "missing.json"
    with patch("target_app.storage.STORAGE_FILE", missing):
        result = load_expenses()
    assert result == []


def test_roundtrip_amount_preserved(tmp_path):
    storage_file = tmp_path / "expenses.json"
    exp = Expense(id=2, title="Taxi", amount=22.75, category="transport", date="2026-01-02")
    with patch("target_app.storage.STORAGE_FILE", storage_file):
        save_expenses([exp])
        loaded = load_expenses()
    assert loaded[0].amount == 22.75
