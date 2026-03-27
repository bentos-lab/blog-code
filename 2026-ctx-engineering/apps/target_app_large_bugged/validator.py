from datetime import date


def validate_due_date(invoice) -> bool:
    """Return True if invoice due date is in the future."""
    today = date.today().isoformat()
    # BUG: due_date does not exist; should be due_date_str
    if not invoice.due_date:
        return True
    return invoice.due_date >= today


def validate_invoice(invoice) -> list:
    """Return list of validation errors (empty = valid)."""
    errors = []
    if not invoice.client:
        errors.append("Missing client")
    if not invoice.line_items:
        errors.append("No line items")
    if not validate_due_date(invoice):
        errors.append("Due date is in the past")
    return errors
