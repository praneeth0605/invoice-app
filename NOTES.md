# NOTES.md

## What I did

**Secrets / credentials**
- Moved hardcoded DB credentials out of `docker-compose.yml` into environment variables via `.env` (gitignored). Updated `.env.example` with safe placeholder values.

**Data hygiene (NPPI)**
- Removed `tax_id` from the customer list endpoint and frontend — it now only appears on the customer detail view where it's actually needed.
- Removed `tax_id` from the invoice detail customer object for the same reason.
- `bank_account_last4` and `stripe_charge_id` are kept in the DB and detail views (legitimate audit trail use) but no longer surfaced unnecessarily.

**Database queries**
- Fixed SQL injection in customer search — replaced f-string interpolation with a parameterized query using `LOWER(name) LIKE :search`.
- Fixed `total_outstanding` — was querying a nonexistent `amount_due` column (silently returning 0). Now correctly sums from `invoice_line_items`.
- Fixed `avg_days_to_pay` — was including unpaid invoices via `COALESCE(paid_date, CURRENT_DATE)`, inflating the average. Now filters to `status = 'paid'` only.
- Fixed `top_customers` — was joining to `payments`, so customers with no payments were excluded. Now sums line items directly.
- Fixed N+1 query in `list_invoices` — replaced per-invoice customer lookup with a single JOIN.
- Removed `try/except Exception: return []` in `list_invoices` that was silently hiding real errors.
- Changed `{"error": "not found"}` with HTTP 200 to proper `404` responses in customers and invoices.

**Frontend**
- Added loading and error states to Invoices, Payments, and InvoiceDetail pages.
- Fixed missing `key` prop on customer list items.
- Removed `console.log` left in Customers.tsx.
- Added ACH and Wire to the payments method filter dropdown.
- Guarded against null customer crash in InvoiceDetail.

**Tests**
- Added 16 tests covering customer search, NPPI exposure, invoice totals, analytics queries, payment recording, and the `maybe_mark_paid` logic.

## What I'd do next with more time

- Add authentication — the app is completely open, every route is public.
- Lock down CORS — currently `allow_origins=["*"]`.
- Implement or remove the Stripe webhook — currently a stub that accepts anything without verifying the signature.
- Move `datetime.utcnow()` to `datetime.now(UTC)` — deprecated in Python 3.12.
- Add the orphaned `/api/stats` endpoint to the frontend dashboard.
- Consider pagination on list endpoints — no limit on customers/invoices/payments.

## What I decided not to fix

- **Stripe integration** — the webhook stub and checkout flow are incomplete, but touching them without real Stripe test credentials risks breaking something I can't verify. Noted it instead.
- **No login/auth** — out of scope for this task, noted above as next step.
- **`docker-compose.yml` DB password** — kept it simple (`invoice_user` / `changeme_strong_password`). A real deployment would use a secrets manager.

