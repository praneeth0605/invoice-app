# Invoice App

Built this for tracking invoices and customers. Mostly working.

## Running it

```
docker compose up
```

Then go to http://localhost:5173 for the frontend. Backend is on :8000.

DB seeds automatically on first startup with some test data (customers, invoices, payments).

## What it does

- Customers page — list/search customers
- Invoices page — list invoices, filter by status, click into one to see details
- Payments page — list of all payments
- Analytics page — top customers by revenue, average days to pay, etc.

## TODO / known stuff

- Stripe integration is set up but I haven't actually tested the webhooks
- Analytics "days to pay" number sometimes looks higher than expected, not sure why
- Total outstanding on the dashboard shows $0 but I'm pretty sure we have outstanding invoices, will look into it
- Need to add tests at some point
- Should probably add login but for now its just open
- The list of invoices on the invoices page is sometimes empty even when there are invoices, just refresh

## Notes

- DB is postgres in docker, connection string is in db.py for now will move to env later
- Payments table has both stripe and manual payments (cash/check/ach), method column says which
- For ACH/check payments we save the last 4 of the bank account (need it for the audit trail)
- Customers have a tax_id field for 1099 stuff at year end
- Invoice statuses: draft, sent, paid, void
