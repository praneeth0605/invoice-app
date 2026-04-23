from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from db import get_db
from routes import customers, invoices, payments, analytics

app = FastAPI(title="Invoice App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["invoices"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.get("/")
def root():
    return {"status": "ok"}


# stuck this here for the dashboard, will move later
@app.get("/api/stats")
def stats(db=Depends(get_db)):
    customer_count = db.execute(text("SELECT COUNT(*) FROM customers")).scalar()
    invoice_count = db.execute(text("SELECT COUNT(*) FROM invoices")).scalar()
    payment_count = db.execute(text("SELECT COUNT(*) FROM payments")).scalar()
    return {
        "customers": customer_count,
        "invoices": invoice_count,
        "payments": payment_count,
    }
