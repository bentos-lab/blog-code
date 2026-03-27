from datetime import date
from .models import PaymentStatus


def days_until_due(invoice) -> int:
    if not invoice.due_date_str:
        return 999
    due = date.fromisoformat(invoice.due_date_str)
    return (due - date.today()).days


def flag_overdue(invoices: list) -> list:
    flagged = []
    for invoice in invoices:
        if invoice.status.value not in ("paid", "cancelled"):
            days_overdue = -days_until_due(invoice)
            # BUG: < 0 flags future invoices instead of past-due ones
            if days_overdue < 0:
                invoice.status = PaymentStatus.OVERDUE
                flagged.append(invoice)
    return flagged
