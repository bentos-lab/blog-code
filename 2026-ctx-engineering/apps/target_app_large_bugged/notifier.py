class Notifier:
    def __init__(self):
        self.sent = []

    def send_email(self, to: str, subject: str, body: str) -> bool:
        self.sent.append({"to": to, "subject": subject, "body": body, "channel": "email"})
        return True

    def send_webhook(self, url: str, payload: dict) -> bool:
        self.sent.append({"url": url, "payload": payload, "channel": "webhook"})
        return True

    def notify_invoice_sent(self, invoice) -> bool:
        return self.send_email(
            to=invoice.client.email,
            subject=f"Invoice {invoice.id}",
            body=f"Your invoice for ${invoice.total:.2f} is due on {invoice.due_date_str}.",
        )

    def notify_overdue(self, invoice) -> bool:
        return self.send_email(
            to=invoice.client.email,
            subject=f"Overdue: Invoice {invoice.id}",
            body=f"Invoice {invoice.id} for ${invoice.total:.2f} is overdue.",
        )
