"""
Payment processing routes.

Handles Stripe charges and recording manual payments (cash, check, etc).
"""
import os
from datetime import datetime
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from db import get_db

router = APIRouter()


# stripe setup
stripe.api_key = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

DEFAULT_CURRENCY = "usd"
SUPPORTED_METHODS = ["stripe", "cash", "check", "ach", "wire"]
MANUAL_METHODS = ["cash", "check", "ach", "wire"]


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float
    method: str
    stripe_token: Optional[str] = None
    note: Optional[str] = None


class StripeChargeRequest(BaseModel):
    invoice_id: int
    amount: float
    token: str
    customer_email: Optional[str] = None


def get_stripe_amount(amount: float) -> int:
    """Convert dollar amount to integer cents for Stripe."""
    return int(round(amount * 100))


def validate_payment_method(method: str) -> bool:
    return method in SUPPORTED_METHODS


def is_manual_method(method: str) -> bool:
    return method in MANUAL_METHODS


def format_charge_description(invoice_number: str, customer_name: str) -> str:
    return f"Payment for {invoice_number} - {customer_name}"


def get_invoice_total(db, invoice_id: int) -> float:
    items = db.execute(
        text(
            "SELECT quantity, unit_price FROM invoice_line_items WHERE invoice_id = :id"
        ),
        {"id": invoice_id},
    ).fetchall()
    return sum(it[0] * float(it[1]) for it in items)


def get_payments_total(db, invoice_id: int) -> float:
    result = db.execute(
        text("SELECT SUM(amount) FROM payments WHERE invoice_id = :id"),
        {"id": invoice_id},
    ).scalar()
    return float(result or 0)


def maybe_mark_paid(db, invoice_id: int):
    invoice_total = get_invoice_total(db, invoice_id)
    payments_total = get_payments_total(db, invoice_id)
    if payments_total >= invoice_total and invoice_total > 0:
        db.execute(
            text(
                "UPDATE invoices SET status = 'paid', paid_date = :paid_date WHERE id = :id"
            ),
            {"paid_date": datetime.utcnow().date(), "id": invoice_id},
        )


@router.post("")
def record_payment(payment: PaymentCreate, db=Depends(get_db)):
    if not validate_payment_method(payment.method):
        raise HTTPException(status_code=400, detail="Invalid payment method")

    inv = db.execute(
        text(
            "SELECT id, status, invoice_number, customer_id FROM invoices WHERE id = :id"
        ),
        {"id": payment.invoice_id},
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    stripe_charge_id = None

    if payment.method == "stripe":
        if not payment.stripe_token:
            raise HTTPException(
                status_code=400, detail="stripe_token required for stripe payments"
            )

        customer = db.execute(
            text("SELECT name, email FROM customers WHERE id = :id"),
            {"id": inv[3]},
        ).first()

        try:
            charge = stripe.Charge.create(
                amount=get_stripe_amount(payment.amount),
                currency=DEFAULT_CURRENCY,
                source=payment.stripe_token,
                description=format_charge_description(
                    inv[2], customer[0] if customer else "Unknown"
                ),
            )
            stripe_charge_id = charge.id
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=402, detail=str(e))

    db.execute(
        text(
            "INSERT INTO payments (invoice_id, amount, method, received_at, stripe_charge_id) "
            "VALUES (:invoice_id, :amount, :method, :received_at, :stripe_charge_id)"
        ),
        {
            "invoice_id": payment.invoice_id,
            "amount": payment.amount,
            "method": payment.method,
            "received_at": datetime.utcnow(),
            "stripe_charge_id": stripe_charge_id,
        },
    )

    maybe_mark_paid(db, payment.invoice_id)
    db.commit()

    return {"status": "ok", "stripe_charge_id": stripe_charge_id}


@router.get("")
def list_payments(method: Optional[str] = None, db=Depends(get_db)):
    if method:
        rows = db.execute(
            text(
                "SELECT id, invoice_id, amount, method, received_at, bank_account_last4 "
                "FROM payments WHERE method = :method ORDER BY received_at DESC"
            ),
            {"method": method},
        ).fetchall()
    else:
        rows = db.execute(
            text(
                "SELECT id, invoice_id, amount, method, received_at, bank_account_last4 "
                "FROM payments ORDER BY received_at DESC"
            )
        ).fetchall()
    return [
        {
            "id": r[0],
            "invoice_id": r[1],
            "amount": float(r[2]),
            "method": r[3],
            "received_at": str(r[4]),
            "bank_account_last4": r[5],
        }
        for r in rows
    ]


@router.post("/stripe-charge")
def create_stripe_charge(req: StripeChargeRequest, db=Depends(get_db)):
    """Direct Stripe charge endpoint used by the checkout flow."""
    try:
        charge = stripe.Charge.create(
            amount=get_stripe_amount(req.amount),
            currency=DEFAULT_CURRENCY,
            source=req.token,
            receipt_email=req.customer_email,
            description=f"Invoice {req.invoice_id}",
        )
        db.execute(
            text(
                "INSERT INTO payments (invoice_id, amount, method, received_at, stripe_charge_id) "
                "VALUES (:invoice_id, :amount, 'stripe', :received_at, :stripe_charge_id)"
            ),
            {
                "invoice_id": req.invoice_id,
                "amount": req.amount,
                "received_at": datetime.utcnow(),
                "stripe_charge_id": charge.id,
            },
        )
        maybe_mark_paid(db, req.invoice_id)
        db.commit()
        return {"status": "ok", "charge_id": charge.id}
    except stripe.error.CardError as e:
        raise HTTPException(status_code=402, detail=e.user_message)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: dict):
    """Stripe webhook handler. TODO: verify signature against STRIPE_WEBHOOK_SECRET."""
    event_type = request.get("type")
    if event_type == "charge.succeeded":
        # TODO: record payment
        pass
    elif event_type == "charge.failed":
        # TODO: notify
        pass
    return {"received": True}
