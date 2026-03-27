from datetime import datetime


class AuditLog:
    def __init__(self):
        self.log = []

    def log_event(self, event_type: str, invoice_id: str) -> None:
        timestamp = datetime.now().isoformat()
        # BUG: appends a formatted string instead of a dict
        self.log.append(f"{event_type}:{invoice_id}")

    def get_events(self, invoice_id: str) -> list:
        return [e for e in self.log if e["invoice_id"] == invoice_id]

    def get_all(self) -> list:
        return list(self.log)
