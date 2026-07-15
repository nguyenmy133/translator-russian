import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { triggerPoll } from '../api/client'
import { useToast } from '../context/ToastContext'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const toast = useToast()
  const { user, logout } = useAuth()
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

  const handleLogout = async () => {
    await logout()
  }

  return (
    <nav className="navbar">
      <Link to="/" className="nav-brand" style={{ textDecoration: 'none' }}>
        <div className="nav-logo">📬</div>
        <span className="nav-title">Email Translator</span>
        <span className="nav-badge">Ru → Vi</span>
      </Link>

      <div className="nav-actions">
        <button
          id="trigger-btn"
          className="btn btn-ghost"
          onClick={handleTrigger}
          disabled={loading}
          style={{ gap: '8px' }}
        >
          <span className={loading ? 'spin' : ''} style={{ display: 'inline-block' }}>🔄</span>
          <span>{loading ? 'Đang quét...' : 'Quét email'}</span>
        </button>
        
        <Link to="/" className="btn btn-primary" style={{ gap: '6px' }}>
          <span>📊</span> Dashboard
        </Link>
        
        <Link to="/settings" className="btn btn-ghost" title="Cài đặt" style={{ padding: '10px 14px' }}>
          ⚙️
        </Link>

        {/* User Info */}
        {user && (
          <div className="nav-user">
            <span style={{ color: 'var(--text-secondary)', marginRight: '4px' }}>
              {user.name ? user.name.split(' ')[0] : 'User'}
            </span>
            {user.picture ? (
              <img src={user.picture} alt="" className="nav-avatar" referrerPolicy="no-referrer" />
            ) : (
              <div className="nav-avatar-placeholder">
                {(user.name || user.email || '?')[0].toUpperCase()}
              </div>
            )}
            <button 
              className="btn btn-ghost" 
              onClick={handleLogout} 
              title="Đăng xuất" 
              style={{ 
                padding: '4px 6px', 
                borderRadius: '50%',
                marginLeft: '4px',
                fontSize: '12px'
              }}
            >
              🚪
            </button>
          </div>
        )}
      </div>
    </nav>
  )
}
