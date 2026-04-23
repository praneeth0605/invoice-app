from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from db import get_db

router = APIRouter()


@router.get("")
def list_customers(search: str = "", db=Depends(get_db)):
    if search:
        rows = db.execute(
            text("SELECT id, name, email FROM customers WHERE name ILIKE :search ORDER BY name"),
            {"search": f"%{search}%"},
        ).fetchall()
    else:
        rows = db.execute(
            text("SELECT id, name, email FROM customers ORDER BY name")
        ).fetchall()
    return [{"id": r[0], "name": r[1], "email": r[2]} for r in rows]


@router.get("/{customer_id}")
def get_customer(customer_id: int, db=Depends(get_db)):
    customer = db.execute(
        text("SELECT id, name, email, tax_id FROM customers WHERE id = :id"),
        {"id": customer_id},
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    invoices = db.execute(
        text(
            "SELECT id, invoice_number, status, issued_date, due_date "
            "FROM invoices WHERE customer_id = :id ORDER BY issued_date DESC"
        ),
        {"id": customer_id},
    ).fetchall()

    return {
        "id": customer[0],
        "name": customer[1],
        "email": customer[2],
        "tax_id": customer[3],
        "invoices": [
            {
                "id": i[0],
                "number": i[1],
                "status": i[2],
                "issued": str(i[3]),
                "due": str(i[4]),
            }
            for i in invoices
        ],
    }


@router.get("/{customer_id}/total-billed")
def total_billed(customer_id: int, db=Depends(get_db)):
    q = """
    SELECT SUM(li.quantity * li.unit_price)
    FROM invoices i
    JOIN invoice_line_items li ON li.invoice_id = i.id
    WHERE i.customer_id = :id
    """
    result = db.execute(text(q), {"id": customer_id}).scalar()
    return {"total": float(result or 0)}


@router.get("/{customer_id}/recent-invoices")
def recent_invoices(customer_id: int, limit: int = 10, db=Depends(get_db)):
    rows = db.execute(
        text(
            "SELECT id, invoice_number, status, issued_date "
            "FROM invoices WHERE customer_id = :id "
            "ORDER BY issued_date DESC LIMIT :limit"
        ),
        {"id": customer_id, "limit": limit},
    ).fetchall()
    return [
        {"id": r[0], "number": r[1], "status": r[2], "issued": str(r[3])}
        for r in rows
    ]