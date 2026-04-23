"""Seed the database with sample data on startup. Idempotent."""
import random
import time
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from db import engine, SessionLocal
from models import Base, Customer, Invoice, InvoiceLineItem, Payment


def wait_for_db(retries=30, delay=2):
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            print(f"DB not ready, retry {i + 1}/{retries}...")
            time.sleep(delay)
    raise RuntimeError("Database never became available")


CUSTOMERS = [
    ("Acme Corp", "billing@acme.example", "12-3456701"),
    ("Globex Industries", "ap@globex.example", "12-3456702"),
    ("Initech LLC", "accounts@initech.example", "12-3456703"),
    ("Soylent Co", "finance@soylent.example", "12-3456704"),
    ("Umbrella Holdings", "billing@umbrella.example", "12-3456705"),
    ("Vandelay Imports", "george@vandelay.example", "12-3456706"),
    ("Wonka Industries", "candy@wonka.example", "12-3456707"),
    ("Stark Enterprises", "tony@stark.example", "12-3456708"),
]

LINE_DESCRIPTIONS = [
    "Consulting hours",
    "Software license — annual",
    "Implementation services",
    "Monthly retainer",
    "On-site training",
    "Support package",
    "Custom development",
    "Strategy session",
    "Audit services",
    "Onboarding setup",
]

STATUS_CHOICES = ["draft", "sent", "sent", "sent", "paid", "paid", "paid", "paid", "void"]


def seed():
    Base.metadata.create_all(engine)
    db = SessionLocal()

    if db.query(Customer).count() > 0:
        print("Already seeded, skipping")
        db.close()
        return

    rng = random.Random(42)

    customers = []
    for name, email, tax_id in CUSTOMERS:
        c = Customer(
            name=name,
            email=email,
            tax_id=tax_id,
            created_at=datetime.utcnow() - timedelta(days=rng.randint(60, 400)),
        )
        db.add(c)
        customers.append(c)
    db.commit()

    invoice_count = 0
    for c in customers:
        n_invoices = rng.randint(3, 9)
        for _ in range(n_invoices):
            invoice_count += 1
            issued = date.today() - timedelta(days=rng.randint(1, 240))
            due = issued + timedelta(days=30)
            status = rng.choice(STATUS_CHOICES)
            paid = None
            if status == "paid":
                paid = issued + timedelta(days=rng.randint(3, 75))

            inv = Invoice(
                customer_id=c.id,
                invoice_number=f"INV-{invoice_count:04d}",
                status=status,
                issued_date=issued,
                due_date=due,
                paid_date=paid,
                created_at=datetime.combine(issued, datetime.min.time()),
            )
            db.add(inv)
            db.flush()

            n_items = rng.randint(1, 4)
            invoice_total = Decimal("0")
            for _ in range(n_items):
                qty = rng.randint(1, 12)
                price = Decimal(str(round(rng.uniform(50, 500), 2)))
                li = InvoiceLineItem(
                    invoice_id=inv.id,
                    description=rng.choice(LINE_DESCRIPTIONS),
                    quantity=qty,
                    unit_price=price,
                )
                db.add(li)
                invoice_total += qty * price

            if status == "paid" and paid is not None:
                # mostly one payment, occasionally split into 2-3
                n_payments = rng.choices([1, 2, 3], weights=[7, 2, 1])[0]
                per_payment = invoice_total / n_payments
                for i in range(n_payments):
                    method = rng.choice(["stripe", "stripe", "cash", "check", "ach"])
                    bank_last4 = None
                    if method in ("ach", "check"):
                        bank_last4 = f"{rng.randint(0, 9999):04d}"
                    p = Payment(
                        invoice_id=inv.id,
                        amount=per_payment.quantize(Decimal("0.01")),
                        method=method,
                        received_at=datetime.combine(paid, datetime.min.time())
                        + timedelta(days=i * 2),
                        stripe_charge_id=(
                            f"ch_{rng.randint(100000000, 999999999)}"
                            if method == "stripe"
                            else None
                        ),
                        bank_account_last4=bank_last4,
                    )
                    db.add(p)

    db.commit()
    db.close()
    print(f"Seeded {len(customers)} customers, {invoice_count} invoices")


if __name__ == "__main__":
    wait_for_db()
    seed()
