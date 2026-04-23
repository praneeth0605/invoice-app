import { useState, useEffect } from 'react'
import { get } from '../api'

export default function Payments() {
  const [payments, setPayments] = useState<any[]>([])
  const [method, setMethod] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    get(`/payments${method ? `?method=${method}` : ''}`)
      .then((data) => {
        if (!Array.isArray(data)) throw new Error('Unexpected response')
        setPayments(data)
      })
      .catch(() => setError('Failed to load payments.'))
      .finally(() => setLoading(false))
  }, [method])

  return (
    <div>
      <h1>Payments</h1>
      <select value={method} onChange={(e) => setMethod(e.target.value)}>
        <option value="">All methods</option>
        <option value="stripe">Stripe</option>
        <option value="cash">Cash</option>
        <option value="check">Check</option>
        <option value="ach">ACH</option>
        <option value="wire">Wire</option>
      </select>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {!loading && !error && (
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
      )}
    </div>
  )
}