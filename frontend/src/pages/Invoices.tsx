import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { get } from '../api'

export default function Invoices() {
  const [invoices, setInvoices] = useState<any[]>([])
  const [status, setStatus] = useState('')

  useEffect(() => {
    get(`/invoices${status ? `?status=${status}` : ''}`).then((data) => {
      setInvoices(data)
    })
  }, [status])

  return (
    <div>
      <h1>Invoices</h1>
      <select value={status} onChange={(e) => setStatus(e.target.value)}>
        <option value="">All statuses</option>
        <option value="draft">Draft</option>
        <option value="sent">Sent</option>
        <option value="paid">Paid</option>
        <option value="void">Void</option>
      </select>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Customer</th>
            <th>Status</th>
            <th>Issued</th>
            <th>Due</th>
          </tr>
        </thead>
        <tbody>
          {invoices.map((inv) => (
            <tr key={inv.id}>
              <td>
                <Link to={`/invoices/${inv.id}`}>{inv.number}</Link>
              </td>
              <td>{inv.customer_name}</td>
              <td>{inv.status}</td>
              <td>{inv.issued_date}</td>
              <td>{inv.due_date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
