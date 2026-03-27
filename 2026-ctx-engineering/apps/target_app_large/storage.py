import json
import os
from .models import Invoice, LineItem, Client, PaymentStatus
from datetime import datetime


DATA_FILE = "invoices.json"


class InvoiceStorage:
    def __init__(self, path: str = DATA_FILE):
        self.path = path

    def save(self, invoices: list) -> None:
        data = []
        for inv in invoices:
            d = {
                "id": inv.id,
                "client": vars(inv.client),
                "status": inv.status.value,
                "due_date_str": inv.due_date_str,
                "paid_amount": inv.paid_amount,
                "created_at": inv.created_at.isoformat(),
                "notes": inv.notes,
                # BUG: str(li) instead of vars(li)
                "line_items": [str(li) for li in inv.line_items],
            }
            data.append(d)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

    def load_all(self) -> list:
        if not os.path.exists(self.path):
            return []
        with open(self.path) as f:
            data = json.load(f)
        invoices = []
        for d in data:
            client = Client(**d["client"])
            line_items = [LineItem(**li) for li in d["line_items"]]
            inv = Invoice(
                id=d["id"],
                client=client,
                line_items=line_items,
                status=PaymentStatus(d["status"]),
                due_date_str=d.get("due_date_str", ""),
                paid_amount=d.get("paid_amount", 0.0),
                created_at=datetime.fromisoformat(d.get("created_at", datetime.now().isoformat())),
                notes=d.get("notes", ""),
            )
            invoices.append(inv)
        return invoices
