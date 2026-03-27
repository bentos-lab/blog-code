from datetime import datetime


def filter_by_status(invoices: list, status: str) -> list:
    return [inv for inv in invoices if inv.status.value == status]


def filter_by_client(invoices: list, client_name: str) -> list:
    return [inv for inv in invoices if inv.client.name.lower() == client_name.lower()]


def filter_by_date_range(invoices: list, start_date: str, end_date: str) -> list:
    # BUG: missing datetime.fromisoformat() parse — comparing str directly to datetime, causing TypeError
    return [
        inv for inv in invoices
        if inv.created_at >= start_date and inv.created_at <= end_date
    ]
