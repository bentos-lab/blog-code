"""Tests for cli.py — Bug 7: amount parsed as str not float."""

import pytest
from target_app.cli import build_parser


def test_add_amount_is_float():
    """The 'add' command amount arg must be a float (Bug 7: it's str)."""
    parser = build_parser()
    args = parser.parse_args(["add", "Lunch", "12.50", "food"])
    # BUG 7: args.amount is "12.50" (str) not 12.5 (float) → breaks arithmetic
    assert isinstance(args.amount, float), (
        f"Expected float, got {type(args.amount).__name__}: {args.amount!r}"
    )
    assert args.amount == 12.5


def test_add_amount_arithmetic():
    """Amount must support arithmetic after parsing (fails if str)."""
    parser = build_parser()
    args = parser.parse_args(["add", "Coffee", "3.75", "food"])
    # This would raise TypeError if amount is str
    total = args.amount * 1.17
    assert abs(total - 4.3875) < 0.001


def test_add_command_title_and_category():
    parser = build_parser()
    args = parser.parse_args(["add", "Taxi", "8.0", "transport"])
    assert args.title == "Taxi"
    assert args.category == "transport"


def test_delete_id_is_int():
    parser = build_parser()
    args = parser.parse_args(["delete", "3"])
    assert isinstance(args.id, int)
    assert args.id == 3
