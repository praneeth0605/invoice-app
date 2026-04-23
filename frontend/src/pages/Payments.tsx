import { useState, useEffect } from 'react'
import { get } from '../api'

export default function Payments() {
  const [payments, setPayments] = useState<any[]>([])
  const [method, setMethod] = useState('')

  useEffect(() => {
    get(`/payments${method ? `?method=${method}` : ''}`).then(setPayments)
  }, [method])

  return (
    <div>
      <h1>Payments</h1>
      <select value={method} onChange={(e) => setMethod(e.target.value)}>
        <option value="">All methods</option>
        <option value="stripe">Stripe</option>
        <option value="cash">Cash</option>
        <option value="check">Check</option>
      </select>
      <table>
        <thead>
          <tr>
            <th>Invoice ID</th>
            <th>Amount</th>
            <th>Method</th>
            <th>Account</th>
            <th>Received</th>
          </tr>
        </thead>
        <tbody>
          {payments.map((p) => (
            <tr key={p.id}>
              <td>{p.invoice_id}</td>
              <td>${p.amount.toFixed(2)}</td>
              <td>{p.method}</td>
              <td>{p.bank_account_last4 ? `****${p.bank_account_last4}` : '—'}</td>
              <td>{p.received_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
