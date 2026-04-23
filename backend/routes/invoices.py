from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from db import get_db

router = APIRouter()


@router.get("")
def list_invoices(status: str = None, db=Depends(get_db)):
    if status:
        invoices = db.execute(
            text(
                "SELECT i.id, i.invoice_number, i.status, i.customer_id, "
                "i.issued_date, i.due_date, c.name as customer_name "
                "FROM invoices i "
                "JOIN customers c ON c.id = i.customer_id "
                "WHERE i.status = :status "
                "ORDER BY i.issued_date DESC"
            ),
            {"status": status},
        ).fetchall()
    else:
        invoices = db.execute(
            text(
                "SELECT i.id, i.invoice_number, i.status, i.customer_id, "
                "i.issued_date, i.due_date, c.name as customer_name "
                "FROM invoices i "
                "JOIN customers c ON c.id = i.customer_id "
                "ORDER BY i.issued_date DESC"
            )
        ).fetchall()

    return [
        {
            "id": inv[0],
            "number": inv[1],
            "status": inv[2],
            "customer_id": inv[3],
            "issued_date": str(inv[4]),
            "due_date": str(inv[5]),
            "customer_name": inv[6] if inv[6] else "(unknown)",
        }
        for inv in invoices
    ]


@router.get("/{invoice_id}")
def get_invoice(invoice_id: int, db=Depends(get_db)):
    inv = db.execute(
        text(
            "SELECT id, invoice_number, status, customer_id, issued_date, due_date, paid_date "
            "FROM invoices WHERE id = :id"
        ),
        {"id": invoice_id},
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    items = db.execute(
        text(
            "SELECT id, description, quantity, unit_price "
            "FROM invoice_line_items WHERE invoice_id = :id"
        ),
        {"id": invoice_id},
    ).fetchall()

    payments = db.execute(
        text(
            "SELECT id, amount, method, received_at, bank_account_last4 "
            "FROM payments WHERE invoice_id = :id ORDER BY received_at"
        ),
        {"id": invoice_id},
    ).fetchall()

    customer = db.execute(
        text("SELECT id, name, email FROM customers WHERE id = :id"),
        {"id": inv[3]},
    ).first()

    return {
        "id": inv[0],
        "number": inv[1],
        "status": inv[2],
        "customer": (
            {"id": customer[0], "name": customer[1], "email": customer[2]}
            if customer
            else None
        ),
        "issued_date": str(inv[4]),
        "due_date": str(inv[5]),
        "paid_date": str(inv[6]) if inv[6] else None,
        "line_items": [
            {
                "id": it[0],
                "description": it[1],
                "quantity": it[2],
                "unit_price": float(it[3]),
            }
            for it in items
        ],
        "payments": [
            {
                "id": p[0],
                "amount": float(p[1]),
                "method": p[2],
                "received_at": str(p[3]),
                "bank_account_last4": p[4],
            }
            for p in payments
        ],
    }


@router.get("/{invoice_id}/total")
def invoice_total(invoice_id: int, db=Depends(get_db)):
    items = db.execute(
        text(
            "SELECT quantity, unit_price FROM invoice_line_items WHERE invoice_id = :id"
        ),
        {"id": invoice_id},
    ).fetchall()
    total = sum(it[0] * float(it[1]) for it in items)
    return {"total": total}


@router.get("/{invoice_id}/balance")
def invoice_balance(invoice_id: int, db=Depends(get_db)):
    items = db.execute(
        text(
            "SELECT quantity, unit_price FROM invoice_line_items WHERE invoice_id = :id"
        ),
        {"id": invoice_id},
    ).fetchall()
    total = sum(it[0] * float(it[1]) for it in items)

    paid = db.execute(
        text("SELECT SUM(amount) FROM payments WHERE invoice_id = :id"),
        {"id": invoice_id},
    ).scalar()
    paid = float(paid or 0)

    return {"total": total, "paid": paid, "balance": total - paid}