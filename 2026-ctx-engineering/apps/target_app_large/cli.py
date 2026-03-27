import argparse
import sys


def build_parser():
    parser = argparse.ArgumentParser(prog="invoice", description="Invoice Management CLI")
    sub = parser.add_subparsers(dest="command")

    # create
    create_p = sub.add_parser("create", help="Create a new invoice")
    create_p.add_argument("id", type=str)
    create_p.add_argument("--client-id", required=True)
    create_p.add_argument("--client-name", required=True)
    create_p.add_argument("--client-email", required=True)

    # send
    send_p = sub.add_parser("send", help="Send an invoice")
    send_p.add_argument("id", type=str)

    # pay
    pay_p = sub.add_parser("pay", help="Record a payment")
    pay_p.add_argument("id", type=str)
    pay_p.add_argument("amount", type=float)

    # list
    sub.add_parser("list", help="List all invoices")

    # export
    export_p = sub.add_parser("export", help="Export to CSV")
    export_p.add_argument("--format", choices=["csv", "text"], default="csv")

    # report
    sub.add_parser("report", help="Revenue report")

    # overdue
    sub.add_parser("overdue", help="List overdue invoices")

    # audit
    audit_p = sub.add_parser("audit", help="Show audit log")
    audit_p.add_argument("id", type=str)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    print(f"Command: {args.command}")
