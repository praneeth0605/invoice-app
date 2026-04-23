import { useState, useEffect } from 'react'
import { get } from '../api'

export default function Customers() {
  const [customers, setCustomers] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    get(`/customers?search=${search}`).then((data) => {
      console.log('customers:', data)
      setCustomers(data)
      setLoading(false)
    })
  }, [search])

  return (
    <div>
      <h1>Customers</h1>
      <input
        type="text"
        placeholder="Search by name..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      {loading ? (
        <p>Loading...</p>
      ) : (
        <ul>
          {customers.map((c) => (
            <li>
              <strong>{c.name}</strong> — {c.email} — TIN: {c.tax_id}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
