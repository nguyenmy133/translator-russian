import React, { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { postAuthGoogle } from '../api/client'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const googleBtnRef = useRef(null)
  const [error, setError] = React.useState('')

  useEffect(() => {
    // Load Google Identity Services script
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = () => {
      if (window.google && GOOGLE_CLIENT_ID) {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleCallback,
        })
        window.google.accounts.id.renderButton(googleBtnRef.current, {
          type: 'standard',
          theme: 'filled_black',
          size: 'large',
          width: 320,
          text: 'signin_with',
          shape: 'pill',
          logo_alignment: 'left',
        })
      }
    }
    document.body.appendChild(script)

    return () => {
      // Cleanup script on unmount
      const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]')
      if (existing) existing.remove()
    }
  }, [])

  const handleGoogleCallback = async (response) => {
    setError('')
    try {
      const data = await postAuthGoogle(response.credential)
      login(data.user)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err?.response?.data?.detail || 'Đăng nhập thất bại. Vui lòng thử lại.')
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">📬</div>
          <h1 className="login-title">Email Translator</h1>
          <p className="login-subtitle">Hệ thống dịch thuật tự động Tiếng Nga → Tiếng Việt</p>
        </div>

        <div className="login-body">
          <div className="login-features" style={{ margin: '0 0 24px 0', textAlign: 'left', width: '100%' }}>
            <div style={{ display: 'flex', gap: '10px', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              <span>⚡</span> <span>Dịch tức thời tài liệu MS Word (.docx)</span>
            </div>
            <div style={{ display: 'flex', gap: '10px', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              <span>🤖</span> <span>Bản dịch chuẩn xác tối ưu hóa bởi Gemini AI</span>
            </div>
            <div style={{ display: 'flex', gap: '10px', fontSize: '13px', color: 'var(--text-secondary)' }}>
              <span>📩</span> <span>Tự động quét và trả kết quả qua Email (IMAP/SMTP)</span>
            </div>
          </div>

          <p className="login-instruction">
            Đăng nhập bằng tài khoản Google được cấu hình để truy cập hệ thống
          </p>

          {!GOOGLE_CLIENT_ID ? (
            <div className="login-error">
              ⚠️ Chưa cấu hình VITE_GOOGLE_CLIENT_ID trong .env
            </div>
          ) : (
            <div className="login-google-btn" ref={googleBtnRef} />
          )}

          {error && <div className="login-error">{error}</div>}
        </div>

        <div className="login-footer">
          <p>Powered by Gemini AI & Google OAuth 2.0</p>
        </div>
      </div>
    </div>
  )
}
