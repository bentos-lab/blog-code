from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class PaymentStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


@dataclass
class Client:
    id: str
    name: str
    email: str


@dataclass
class LineItem:
    description: str
    quantity: float
    unit_price: float

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Invoice:
    id: str
    client: Client
    line_items: list = field(default_factory=list)
    status: PaymentStatus = PaymentStatus.DRAFT
    due_date_str: str = ""          # ISO date string e.g. "2024-12-31"
    paid_amount: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    notes: str = ""

    @property
    def subtotal(self) -> float:
        return sum(item.subtotal for item in self.line_items)

    @property
    def total(self) -> float:
        from .pricing import calculate_total
        return calculate_total(self.subtotal)

    def due_amount(self) -> float:
        # BUG: should be subtraction, not multiplication
        return self.total * self.paid_amount
