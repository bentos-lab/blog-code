"""Tests for models.py — Bug 1: TAX_RATE is int % not decimal."""

import pytest
from target_app.models import Expense, TAX_RATE


def test_tax_rate_is_decimal():
    """TAX_RATE should be a decimal like 0.17, not an integer like 17."""
    # BUG 1: TAX_RATE = 17 (an int percentage), should be 0.17
    assert isinstance(TAX_RATE, float), f"TAX_RATE should be float, got {type(TAX_RATE).__name__}"
    assert TAX_RATE < 1.0, f"TAX_RATE should be < 1.0 (decimal), got {TAX_RATE}"


def test_total_with_tax_reasonable():
    """$100 at 17% tax should be ~$117, not $1800."""
    e = Expense(id=1, title="Lunch", amount=100.0, category="food", date="2026-01-01")
    result = e.total_with_tax()
    # BUG 1: returns 100 * 18 = 1800 instead of 100 * 1.17 = 117
    assert 115 < result < 120, f"Expected ~$117, got ${result}"


def test_expense_defaults():
    e = Expense(id=1, title="Test", amount=10.0, category="other", date="2026-01-01")
    assert e.tags == []
    assert e.id == 1
