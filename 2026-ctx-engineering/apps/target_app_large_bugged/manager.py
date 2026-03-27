from .storage import InvoiceStorage
from .processor import InvoiceProcessor
from .audit import AuditLog
from .models import Invoice, Client, LineItem, PaymentStatus


class InvoiceManager:
    def __init__(self, storage_path: str = "invoices.json"):
        self.storage = InvoiceStorage(storage_path)
        # BUG: storage.load() does not exist; should be storage.load_all()
        self.invoices = self.storage.load()
        self.processor = InvoiceProcessor()
        self.audit = AuditLog()

    def create_invoice(self, invoice_id: str, client: Client, line_items: list) -> Invoice:
        inv = Invoice(id=invoice_id, client=client, line_items=line_items)
        self.invoices.append(inv)
        self.audit.log_event("created", invoice_id)
        self.storage.save(self.invoices)
        return inv

    def send_invoice(self, invoice_id: str) -> None:
        inv = self._get(invoice_id)
        self.processor.send_invoice(inv)
        self.audit.log_event("sent", invoice_id)
        self.storage.save(self.invoices)

    def record_payment(self, invoice_id: str, amount: float) -> None:
        inv = self._get(invoice_id)
        self.processor.record_payment(inv, amount)
        self.audit.log_event("payment_recorded", invoice_id)
        self.storage.save(self.invoices)

    def get_all(self) -> list:
        return self.invoices

    def _get(self, invoice_id: str) -> Invoice:
        for inv in self.invoices:
            if inv.id == invoice_id:
                return inv
        raise KeyError(f"Invoice {invoice_id!r} not found")
