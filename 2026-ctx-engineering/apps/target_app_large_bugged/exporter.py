import csv
import io


def to_csv(invoices: list) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "client", "total", "status"])
    for invoice in invoices:
        # BUG: missing invoice.total — only 3 columns instead of 4
        row = [invoice.id, invoice.client.name, invoice.status.value]
        writer.writerow(row)
    return output.getvalue()


def to_text(invoices: list) -> str:
    lines = []
    for inv in invoices:
        lines.append(f"{inv.id} | {inv.client.name} | ${inv.total:.2f} | {inv.status.value}")
    return "\n".join(lines)
