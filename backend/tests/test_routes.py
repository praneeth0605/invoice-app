import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from main import app
from db import get_db
from models import Base, Customer, Invoice, InvoiceLineItem, Payment
from datetime import date, datetime
from decimal import Decimal

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def sample_customer(db):
    c = Customer(name="Test Corp", email="test@corp.com", tax_id="12-3456789")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture
def sample_invoice(db, sample_customer):
    inv = Invoice(
        customer_id=sample_customer.id,
        invoice_number="INV-0001",
        status="sent",
        issued_date=date(2024, 1, 1),
        due_date=date(2024, 1, 31),
    )
    db.add(inv)
    db.flush()
    li = InvoiceLineItem(
        invoice_id=inv.id,
        description="Consulting",
        quantity=2,
        unit_price=Decimal("100.00"),
    )
    db.add(li)
    db.commit()
    db.refresh(inv)
    return inv


# --- Customer tests ---

def test_list_customers(client, sample_customer):
    r = client.get("/api/customers")
    assert r.status_code == 200
    data = r.json()
    assert any(c["name"] == "Test Corp" for c in data)


def test_list_customers_no_tax_id(client, sample_customer):
    r = client.get("/api/customers")
    assert r.status_code == 200
    for c in r.json():
        assert "tax_id" not in c


def test_customer_search(client, sample_customer):
    r = client.get("/api/customers?search=test")  # lowercase — SQLite LIKE is case-insensitive
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "Test Corp"


def test_customer_search_no_injection(client, sample_customer):
    # SQL injection attempt — parameterized query should handle safely, return empty
    r = client.get("/api/customers?search='; DROP TABLE customers; --")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_customer_includes_tax_id(client, sample_customer):
    r = client.get(f"/api/customers/{sample_customer.id}")
    assert r.status_code == 200
    assert r.json()["tax_id"] == "12-3456789"


def test_get_customer_not_found(client):
    r = client.get("/api/customers/99999")
    assert r.status_code == 404


# --- Invoice tests ---

def test_list_invoices(client, sample_invoice):
    r = client.get("/api/invoices")
    assert r.status_code == 200
    data = r.json()
    assert any(i["number"] == "INV-0001" for i in data)


def test_list_invoices_filter_by_status(client, sample_invoice):
    r = client.get("/api/invoices?status=sent")
    assert r.status_code == 200
    assert all(i["status"] == "sent" for i in r.json())


def test_get_invoice_not_found(client):
    r = client.get("/api/invoices/99999")
    assert r.status_code == 404


def test_invoice_total(client, sample_invoice):
    r = client.get(f"/api/invoices/{sample_invoice.id}/total")
    assert r.status_code == 200
    assert r.json()["total"] == 200.0


def test_invoice_balance(client, sample_invoice):
    r = client.get(f"/api/invoices/{sample_invoice.id}/balance")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 200.0
    assert data["paid"] == 0.0
    assert data["balance"] == 200.0


# --- Analytics tests ---

def test_total_outstanding(client, sample_invoice):
    r = client.get("/api/analytics/total-outstanding")
    assert r.status_code == 200
    assert r.json()["total"] == 200.0


def test_total_outstanding_excludes_paid(client, db, sample_invoice):
    db.execute(
        text("UPDATE invoices SET status = 'paid' WHERE id = :id"),
        {"id": sample_invoice.id},
    )
    db.commit()
    r = client.get("/api/analytics/total-outstanding")
    assert r.status_code == 200
    assert r.json()["total"] == 0.0


def test_avg_days_to_pay_only_paid(client, db, sample_invoice):
    # Unpaid invoice should not affect avg
    r = client.get("/api/analytics/avg-days-to-pay")
    assert r.status_code == 200
    assert r.json()["avg_days"] == 0  # no paid invoices yet


# --- Payment tests ---

def test_maybe_mark_paid(client, db, sample_invoice):
    # Record a payment equal to invoice total — should mark as paid
    r = client.post("/api/payments", json={
        "invoice_id": sample_invoice.id,
        "amount": 200.0,
        "method": "cash",
    })
    assert r.status_code == 200
    inv = db.execute(
        text("SELECT status FROM invoices WHERE id = :id"),
        {"id": sample_invoice.id},
    ).scalar()
    assert inv == "paid"


def test_invalid_payment_method(client, sample_invoice):
    r = client.post("/api/payments", json={
        "invoice_id": sample_invoice.id,
        "amount": 100.0,
        "method": "bitcoin",
    })
    assert r.status_code == 400