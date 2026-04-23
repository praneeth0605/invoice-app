from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200))
    tax_id = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    invoices = relationship("Invoice", back_populates="customer")


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    invoice_number = Column(String(50), nullable=False)
    status = Column(String(20), default="draft")
    issued_date = Column(Date)
    due_date = Column(Date)
    paid_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    customer = relationship("Customer", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice")
    payments = relationship("Payment", back_populates="invoice")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    description = Column(Text)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10, 2))
    invoice = relationship("Invoice", back_populates="line_items")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    amount = Column(Numeric(10, 2))
    method = Column(String(20))
    received_at = Column(DateTime, default=datetime.utcnow)
    stripe_charge_id = Column(String(100), nullable=True)
    bank_account_last4 = Column(String(4), nullable=True)
    invoice = relationship("Invoice", back_populates="payments")
