"""CLI argument parser for the Expense Tracker."""

from __future__ import annotations
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Expense Tracker CLI")
    sub = parser.add_subparsers(dest="command")

    # add
    add_p = sub.add_parser("add", help="Add a new expense")
    add_p.add_argument("title", type=str, help="Expense title")
    # BUG 7 (Arg Parse): amount parsed as str instead of float.
    # Downstream arithmetic (total_with_tax, sum) fails with TypeError.
    add_p.add_argument("amount", type=str, help="Amount in dollars")  # Should be: type=float
    add_p.add_argument("category", type=str, help="Category (food/transport/etc)")
    add_p.add_argument("--date", type=str, default=None, help="Date YYYY-MM-DD")
    add_p.add_argument("--tags", type=str, nargs="*", default=[], help="Tags")

    # list
    list_p = sub.add_parser("list", help="List expenses")
    list_p.add_argument("--category", type=str, default=None)
    list_p.add_argument("--from-date", type=str, default=None)
    list_p.add_argument("--to-date", type=str, default=None)

    # summary
    sub.add_parser("summary", help="Show summary stats")

    # delete
    del_p = sub.add_parser("delete", help="Delete an expense")
    del_p.add_argument("id", type=int, help="Expense ID")

    return parser
