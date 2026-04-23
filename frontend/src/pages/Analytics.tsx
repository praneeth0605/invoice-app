import { useState, useEffect } from 'react'
import { get } from '../api'

export default function Analytics() {
  const [topCustomers, setTopCustomers] = useState<any[]>([])
  const [avgDays, setAvgDays] = useState<number>(0)
  const [outstanding, setOutstanding] = useState<number>(0)
  const [byStatus, setByStatus] = useState<any[]>([])
  const [monthly, setMonthly] = useState<any[]>([])
  const [aging, setAging] = useState<any[]>([])

  useEffect(() => {
    get('/analytics/top-customers').then((d) => setTopCustomers(d))
    get('/analytics/avg-days-to-pay').then((d) => setAvgDays(d.avg_days))
    get('/analytics/total-outstanding').then((d) => setOutstanding(d.total))
    get('/analytics/invoices-by-status').then((d) => setByStatus(d))
    get('/analytics/monthly-revenue').then((d) => setMonthly(d))
    get('/analytics/aging').then((d) => setAging(d))
  }, [])

  return (
    <div>
      <h1>Analytics</h1>

      <div className="stats">
        <div className="stat">
          <div className="stat-label">Total Outstanding</div>
          <div className="stat-value">${outstanding.toFixed(2)}</div>
        </div>
        <div className="stat">
          <div className="stat-label">Avg Days to Pay</div>
          <div className="stat-value">{avgDays.toFixed(1)}</div>
        </div>
      </div>

      <h2>Top Customers by Revenue</h2>
      <table>
        <thead>
          <tr>
            <th>Customer</th>
            <th>Revenue</th>
          </tr>
        </thead>
        <tbody>
          {topCustomers.map((c, i) => (
            <tr key={i}>
              <td>{c.name}</td>
              <td>${c.revenue.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Invoices by Status</h2>
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          {byStatus.map((s) => (
            <tr key={s.status}>
              <td>{s.status}</td>
              <td>{s.count}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Aging</h2>
      <table>
        <thead>
          <tr>
            <th>Bucket</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          {aging.map((a) => (
            <tr key={a.bucket}>
              <td>{a.bucket}</td>
              <td>{a.count}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Monthly Revenue</h2>
      <table>
        <thead>
          <tr>
            <th>Month</th>
            <th>Revenue</th>
          </tr>
        </thead>
        <tbody>
          {monthly.map((m) => (
            <tr key={m.month}>
              <td>{m.month}</td>
              <td>${m.revenue.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
