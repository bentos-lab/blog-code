"""Utility functions for dates and currency."""

from __future__ import annotations
from datetime import datetime


def parse_date(date_str: str) -> datetime:
    """Parse a date string into a datetime object.

    Expected format: YYYY-MM-DD (ISO 8601)

    BUG 6 (Wrong Format String): uses day/month/year format instead of ISO.
    `strptime("2026-01-15", "%d/%m/%Y")` → ValueError always.
    Should be: strptime(date_str, "%Y-%m-%d")
    """
    return datetime.strptime(date_str, "%d/%m/%Y")  # Should be: "%Y-%m-%d"


def format_currency(amount: float, symbol: str = "$") -> str:
    """Format a float as a currency string."""
    return f"{symbol}{amount:,.2f}"


def today_str() -> str:
    """Return today's date as YYYY-MM-DD string."""
    return datetime.now().strftime("%Y-%m-%d")
