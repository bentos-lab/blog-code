def revenue_by_client(invoices: list) -> dict:
    totals = {}
    for invoice in invoices:
        if invoice.status.value == "paid":
            # BUG: invoice.client_name does not exist; should be invoice.client.name
            key = invoice.client_name
            totals[key] = totals.get(key, 0.0) + invoice.total
    return totals


def overdue_invoices(invoices: list) -> list:
    return [inv for inv in invoices if inv.status.value == "overdue"]


def revenue_summary(invoices: list) -> dict:
    paid = [inv for inv in invoices if inv.status.value == "paid"]
    return {
        "total_invoices": len(invoices),
        "paid_count": len(paid),
        "total_revenue": sum(inv.total for inv in paid),
    }
