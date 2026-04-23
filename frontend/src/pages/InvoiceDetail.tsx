import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { get } from '../api'

export default function InvoiceDetail() {
  const { id } = useParams()
  const [invoice, setInvoice] = useState<any>(null)

  useEffect(() => {
    get(`/invoices/${id}`).then(setInvoice)
  }, [id])

  if (!invoice) return <p>Loading...</p>

  return (
    <div>
      <h1>Invoice {invoice.number}</h1>
      <p>
        Customer: {invoice.customer.name} ({invoice.customer.email}) — TIN: {invoice.customer.tax_id}
      </p>
      <p>Status: {invoice.status}</p>
      <p>Issued: {invoice.issued_date}</p>
      <p>Due: {invoice.due_date}</p>
      {invoice.paid_date && <p>Paid: {invoice.paid_date}</p>}

      <h2>Line Items</h2>
      <table>
        <thead>
          <tr>
            <th>Description</th>
            <th>Qty</th>
            <th>Unit Price</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          {invoice.line_items.map((li: any) => (
            <tr key={li.id}>
              <td>{li.description}</td>
              <td>{li.quantity}</td>
              <td>${li.unit_price.toFixed(2)}</td>
              <td>${(li.quantity * li.unit_price).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Payments</h2>
      {invoice.payments.length === 0 ? (
        <p>No payments yet.</p>
      ) : (
        <ul>
          {invoice.payments.map((p: any) => (
            <li key={p.id}>
              ${p.amount.toFixed(2)} via {p.method} on {p.received_at}
              {p.bank_account_last4 && ` (acct ****${p.bank_account_last4})`}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
