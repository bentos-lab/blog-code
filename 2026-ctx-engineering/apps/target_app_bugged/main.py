"""Entry point for the Expense Tracker CLI."""

from __future__ import annotations
import sys

from .cli import build_parser
from .manager import ExpenseManager
from .formatter import format_expense_list
from .utils import parse_date, today_str


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    manager = ExpenseManager()

    if args.command == "add":
        date = args.date or today_str()
        exp = manager.add(
            title=args.title,
            amount=args.amount,
            category=args.category,
            date=date,
            tags=args.tags or [],
        )
        print(f"Added expense #{exp.id}: {exp.title} ({exp.amount})")

    elif args.command == "list":
        expenses = manager.get_all()
        if args.category:
            expenses = manager.filter_by_category(args.category)
        if args.from_date and args.to_date:
            start = parse_date(args.from_date)
            end = parse_date(args.to_date)
            expenses = manager.filter_by_date_range(start, end)
        print(format_expense_list(expenses))

    elif args.command == "summary":
        summary = manager.get_summary()
        print(f"Total expenses: {summary['count']}")
        print(f"Total amount:   ${summary['total']:.2f}")
        for cat, total in summary.get("by_category", {}).items():
            print(f"  {cat}: ${total:.2f}")

    elif args.command == "delete":
        if manager.delete(args.id):
            print(f"Deleted expense #{args.id}")
        else:
            print(f"No expense with id {args.id}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
