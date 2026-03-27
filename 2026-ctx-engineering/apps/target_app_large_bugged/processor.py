from .models import PaymentStatus


class InvoiceProcessor:
    def send_invoice(self, invoice) -> None:
        if invoice.status != PaymentStatus.DRAFT:
            raise ValueError(f"Can only send DRAFT invoices, got {invoice.status}")
        # BUG: sets PAID instead of SENT
        invoice.status = PaymentStatus.PAID

    def record_payment(self, invoice, amount: float) -> None:
        if invoice.status != PaymentStatus.SENT:
            raise ValueError(f"Can only pay SENT invoices, got {invoice.status}")
        invoice.paid_amount += amount
        if invoice.paid_amount >= invoice.total:
            invoice.status = PaymentStatus.PAID

    def cancel_invoice(self, invoice) -> None:
        if invoice.status == PaymentStatus.PAID:
            raise ValueError("Cannot cancel a paid invoice")
        invoice.status = PaymentStatus.CANCELLED
