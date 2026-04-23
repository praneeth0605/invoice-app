import { Routes, Route, Link } from 'react-router-dom'
import Customers from './pages/Customers'
import Invoices from './pages/Invoices'
import InvoiceDetail from './pages/InvoiceDetail'
import Payments from './pages/Payments'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <div className="app">
      <nav className="nav">
        <Link to="/">Customers</Link>
        <Link to="/invoices">Invoices</Link>
        <Link to="/payments">Payments</Link>
        <Link to="/analytics">Analytics</Link>
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<Customers />} />
          <Route path="/invoices" element={<Invoices />} />
          <Route path="/invoices/:id" element={<InvoiceDetail />} />
          <Route path="/payments" element={<Payments />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </main>
    </div>
  )
}
