from fastapi import APIRouter, Depends
from sqlalchemy import text

from db import get_db

router = APIRouter()


@router.get("/top-customers")
def top_customers(limit: int = 5, db=Depends(get_db)):
    """Top N customers by total revenue from paid invoices."""
    q = """
    SELECT c.name, SUM(li.quantity * li.unit_price) as revenue
    FROM customers c
    JOIN invoices i ON i.customer_id = c.id
    JOIN invoice_line_items li ON li.invoice_id = i.id
    WHERE i.status = 'paid'
    GROUP BY c.id, c.name
    ORDER BY revenue DESC
    LIMIT :limit
    """
    rows = db.execute(text(q), {"limit": limit}).fetchall()
    return [{"name": r[0], "revenue": float(r[1])} for r in rows]


@router.get("/avg-days-to-pay")
def avg_days_to_pay(db=Depends(get_db)):
    """Average number of days from invoice issue to full payment (paid invoices only)."""
    q = """
    SELECT AVG(paid_date - issued_date) as avg_days
    FROM invoices
    WHERE status = 'paid' AND paid_date IS NOT NULL
    """
    result = db.execute(text(q)).scalar()
    return {"avg_days": float(result) if result is not None else 0}


@router.get("/total-outstanding")
def total_outstanding(db=Depends(get_db)):
    """Total dollar amount across all unpaid invoices."""
    q = """
    SELECT COALESCE(SUM(li.quantity * li.unit_price), 0)
    FROM invoices i
    JOIN invoice_line_items li ON li.invoice_id = i.id
    WHERE i.status NOT IN ('paid', 'void')
    """
    result = db.execute(text(q)).scalar()
    return {"total": float(result or 0)}


@router.get("/invoices-by-status")
def invoices_by_status(db=Depends(get_db)):
    rows = db.execute(
        text("SELECT status, COUNT(*) as count FROM invoices GROUP BY status")
    ).fetchall()
    return [{"status": r[0], "count": r[1]} for r in rows]


@router.get("/monthly-revenue")
def monthly_revenue(db=Depends(get_db)):
    """Revenue collected per month (from payments)."""
    q = """
    SELECT
        TO_CHAR(received_at, 'YYYY-MM') as month,
        SUM(amount) as revenue
    FROM payments
    GROUP BY month
    ORDER BY month
    """
    rows = db.execute(text(q)).fetchall()
    return [{"month": r[0], "revenue": float(r[1])} for r in rows]


@router.get("/aging")
def aging(db=Depends(get_db)):
    """Aging buckets for outstanding invoices (days past due)."""
    q = """
    SELECT
        CASE
            WHEN CURRENT_DATE - due_date <= 0 THEN 'current'
            WHEN CURRENT_DATE - due_date <= 30 THEN '1-30'
            WHEN CURRENT_DATE - due_date <= 60 THEN '31-60'
            WHEN CURRENT_DATE - due_date <= 90 THEN '61-90'
            ELSE '90+'
        END as bucket,
        COUNT(*) as count
    FROM invoices
    WHERE status NOT IN ('paid', 'void')
    GROUP BY bucket
    """
    rows = db.execute(text(q)).fetchall()
    return [{"bucket": r[0], "count": r[1]} for r in rows]