import pytest
from datetime import datetime, timedelta, date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from target_app_large.models import Invoice, LineItem, Client, PaymentStatus
from target_app_large.pricing import apply_discount, calculate_total, round_currency
from target_app_large.validator import validate_due_date
from target_app_large.storage import InvoiceStorage
from target_app_large.search import filter_by_date_range
from target_app_large.reports import revenue_by_client
from target_app_large.exporter import to_csv
from target_app_large.scheduler import flag_overdue
from target_app_large.audit import AuditLog
from target_app_large.processor import InvoiceProcessor


def make_client(name="Acme", email="acme@example.com"):
    return Client(id="c1", name=name, email=email)


def make_invoice(inv_id="INV-001", paid=0.0, due_days=30):
    client = make_client()
    items = [LineItem("Widget", 2, 100.0)]  # subtotal = 200
    due = (date.today() + timedelta(days=due_days)).isoformat()
    inv = Invoice(id=inv_id, client=client, line_items=items, paid_amount=paid, due_date_str=due)
    return inv


# Bug 1: due_amount() uses subtraction not multiplication
def test_due_amount_subtraction():
    inv = make_invoice(paid=50.0)
    due = inv.due_amount()
    assert due < inv.total, "due_amount should be less than total when partially paid"
    assert abs(due - (inv.total - 50.0)) < 0.01


# Bug 2: discount applied before tax (on subtotal)
def test_discount_applied_before_tax():
    # subtotal=1100 qualifies for 5% discount
    # correct: discounted=1045, taxed=1045*1.1=1149.5
    # wrong (if discount after tax): total=1100*1.1=1210, then 1210*0.95=1149.5... same?
    # Let's use a clearer example: subtotal=2000
    # correct: 2000*0.95=1900, 1900*1.1=2090
    # wrong: 2000*1.1=2200, 2200*0.95=2090 — actually same in this formulation
    # We need to test apply_discount specifically acts on subtotal
    result = apply_discount(1000.0)
    assert result == 950.0, f"5% discount on 1000 should give 950, got {result}"
    result_no_discount = apply_discount(999.0)
    assert result_no_discount == 999.0


# Bug 3: round_currency uses int 2 not str "2"
def test_round_currency_returns_float():
    result = round_currency(12.3456)
    assert isinstance(result, float)
    assert result == 12.35


# Bug 4: validate_due_date uses due_date_str (correct field name)
def test_validate_due_date_uses_correct_field():
    inv = make_invoice(due_days=10)
    assert validate_due_date(inv) is True
    inv_past = make_invoice(due_days=-5)
    assert validate_due_date(inv_past) is False


# Bug 5: storage saves line_items as dicts (vars(li)), not strings
def test_storage_roundtrip_preserves_line_items(tmp_path):
    storage = InvoiceStorage(str(tmp_path / "test.json"))
    inv = make_invoice()
    storage.save([inv])
    loaded = storage.load_all()
    assert len(loaded) == 1
    assert len(loaded[0].line_items) == 1
    assert isinstance(loaded[0].line_items[0], type(inv.line_items[0]))
    assert loaded[0].line_items[0].unit_price == 100.0


# Bug 6: filter_by_date_range parses string dates before comparing with datetime
def test_filter_by_date_range():
    inv = make_invoice()
    inv.created_at = datetime(2024, 6, 15)
    result = filter_by_date_range([inv], "2024-06-01", "2024-06-30")
    assert len(result) == 1
    result_out = filter_by_date_range([inv], "2024-07-01", "2024-07-31")
    assert len(result_out) == 0


# Bug 7: revenue_by_client uses invoice.client.name (nested accessor)
def test_revenue_by_client_uses_nested_accessor():
    inv = make_invoice()
    inv.status = PaymentStatus.PAID
    result = revenue_by_client([inv])
    assert "Acme" in result
    assert result["Acme"] > 0


# Bug 8: to_csv includes total column
def test_csv_export_includes_total():
    inv = make_invoice()
    csv_output = to_csv([inv])
    header_line = csv_output.splitlines()[0]
    assert "total" in header_line.lower()
    data_line = csv_output.splitlines()[1]
    parts = data_line.split(",")
    assert len(parts) == 4, f"Expected 4 columns, got {len(parts)}: {data_line}"


# Bug 9: flag_overdue only flags past-due invoices (days_overdue > 0)
def test_flag_overdue_only_past_due():
    future_inv = make_invoice("INV-001", due_days=10)
    future_inv.status = PaymentStatus.SENT
    past_inv = make_invoice("INV-002", due_days=-5)
    past_inv.status = PaymentStatus.SENT

    flagged = flag_overdue([future_inv, past_inv])
    assert len(flagged) == 1
    assert flagged[0].id == "INV-002"
    assert future_inv.status == PaymentStatus.SENT  # not flagged


# Bug 10: audit.log_event appends dict not string
def test_audit_log_event_appends_dict():
    audit = AuditLog()
    audit.log_event("created", "INV-001")
    assert len(audit.log) == 1
    entry = audit.log[0]
    assert isinstance(entry, dict)
    assert entry["event"] == "created"
    assert entry["invoice_id"] == "INV-001"
    assert "ts" in entry


# Bug 11: processor.send_invoice sets status = SENT not PAID
def test_send_invoice_sets_sent_status():
    processor = InvoiceProcessor()
    inv = make_invoice()
    processor.send_invoice(inv)
    assert inv.status == PaymentStatus.SENT, f"Expected SENT, got {inv.status}"


# Bug 12: manager uses storage.load_all() not storage.load()
def test_manager_instantiation_uses_load_all(tmp_path):
    from target_app_large.manager import InvoiceManager
    # Should not raise AttributeError
    mgr = InvoiceManager(storage_path=str(tmp_path / "inv.json"))
    assert mgr.invoices == []
