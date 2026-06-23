import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { triggerPoll } from '../api/client'
import { useToast } from '../context/ToastContext'

export default function Navbar() {
  const toast = useToast()
  const [loading, setLoading] = React.useState(false)

  const handleTrigger = async () => {
    setLoading(true)
    try {
      const res = await triggerPoll()
      toast.success('Đang quét email', res.message)
    } catch {
      toast.error('Lỗi', 'Không thể kết nối tới server')
    } finally {
      setTimeout(() => setLoading(false), 2000)
    }
  }

  return (
    <nav className="navbar">
      <Link to="/" className="nav-brand" style={{ textDecoration: 'none' }}>
        <div className="nav-logo">🌐</div>
        <span className="nav-title">Email Translator</span>
        <span className="nav-badge">Ru → Vi</span>
      </Link>

      <div className="nav-actions">
        <button
          id="trigger-btn"
          className="btn btn-ghost"
          onClick={handleTrigger}
          disabled={loading}
        >
          <span className={loading ? 'spin' : ''}>🔄</span>
          {loading ? 'Đang quét...' : 'Quét ngay'}
        </button>
        <Link to="/" className="btn btn-primary">
          📊 Dashboard
        </Link>
      </div>
    </nav>
  )
}
