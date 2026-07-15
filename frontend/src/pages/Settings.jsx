import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import {
  getEmailAccountStatus,
  postEmailAccount,
  testEmailConnection,
  deleteEmailAccount,
} from '../api/client'

export default function Settings() {
  const { user } = useAuth()
  const toast = useToast()

  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const [appPassword, setAppPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [imapHost, setImapHost] = useState('imap.gmail.com')
  const [imapPort, setImapPort] = useState(993)
  const [smtpHost, setSmtpHost] = useState('smtp.gmail.com')
  const [smtpPort, setSmtpPort] = useState(587)
  const [testResult, setTestResult] = useState(null)

  const fetchStatus = async () => {
    try {
      const data = await getEmailAccountStatus()
      setStatus(data)
      setImapHost(data.imap_host || 'imap.gmail.com')
      setImapPort(data.imap_port || 993)
      setSmtpHost(data.smtp_host || 'smtp.gmail.com')
      setSmtpPort(data.smtp_port || 587)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchStatus() }, [])

  const handleTest = async () => {
    if (!appPassword.trim()) {
      toast.error('Lỗi', 'Vui lòng nhập App Password trước')
      return
    }
    setTesting(true)
    setTestResult(null)
    try {
      const data = await testEmailConnection({
        email_address: user.email,
        app_password: appPassword,
        imap_host: imapHost,
        imap_port: imapPort,
        smtp_host: smtpHost,
        smtp_port: smtpPort,
      })
      setTestResult(data.results)
      if (data.success) {
        toast.success('Thành công', 'Kết nối IMAP & SMTP đều OK!')
      } else {
        toast.error('Lỗi kết nối', 'Kiểm tra lại App Password hoặc cấu hình')
      }
    } catch {
      toast.error('Lỗi', 'Không thể kiểm tra kết nối')
    } finally {
      setTesting(false)
    }
  }

  const handleSave = async () => {
    if (!appPassword.trim()) {
      toast.error('Lỗi', 'Vui lòng nhập App Password')
      return
    }
    setSaving(true)
    try {
      await postEmailAccount({
        app_password: appPassword,
        imap_host: imapHost,
        imap_port: imapPort,
        smtp_host: smtpHost,
        smtp_port: smtpPort,
      })
      toast.success('Đã lưu', 'Cấu hình email đã được lưu thành công')
      setAppPassword('')
      fetchStatus()
    } catch {
      toast.error('Lỗi', 'Không thể lưu cấu hình')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Bạn có chắc muốn xóa cấu hình email? Hệ thống sẽ dùng lại cấu hình từ .env')) return
    setDeleting(true)
    try {
      await deleteEmailAccount()
      toast.success('Đã xóa', 'Cấu hình email đã được xóa')
      fetchStatus()
    } catch {
      toast.error('Lỗi', 'Không thể xóa cấu hình')
    } finally {
      setDeleting(false)
    }
  }

  if (loading) return (
    <div style={{ padding: 40 }}>
      {[1,2].map(i => (
        <div key={i} className="skeleton" style={{ height: 80, marginBottom: 16, borderRadius: 12 }} />
      ))}
    </div>
  )

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">⚙️ Cài đặt Email</h1>
          <p className="page-subtitle">
            Cấu hình tài khoản email để nhận và gửi bài dịch tự động
          </p>
        </div>
      </div>

      {/* Current Account Info */}
      <div className="settings-card">
        <div className="settings-card-header">
          <span className="settings-card-icon">👤</span>
          <span className="settings-card-title">Tài khoản quản trị</span>
        </div>
        <div className="settings-user-info">
          {user?.picture ? (
            <img src={user.picture} alt="Avatar" className="settings-avatar" referrerPolicy="no-referrer" />
          ) : (
            <div className="settings-avatar" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--accent)', color: '#fff', fontSize: '20px', fontWeight: 'bold' }}>
              {(user?.name || user?.email || '?')[0].toUpperCase()}
            </div>
          )}
          <div>
            <div className="settings-user-name">{user?.name}</div>
            <div className="settings-user-email">{user?.email}</div>
          </div>
          <div style={{ marginLeft: 'auto' }}>
            {status?.configured ? (
              <span className="badge badge-DONE">
                <span className="badge-dot" />
                Đã cấu hình
              </span>
            ) : (
              <span className="badge badge-PENDING">
                <span className="badge-dot" />
                Chưa cấu hình
              </span>
            )}
          </div>
        </div>
        {status?.last_verified_at && (
          <div className="settings-verified">
            ✅ Xác thực kết nối gần nhất: {new Date(status.last_verified_at).toLocaleString('vi-VN')}
          </div>
        )}
      </div>

      {/* App Password Form */}
      <div className="settings-card">
        <div className="settings-card-header">
          <span className="settings-card-icon">🔑</span>
          <span className="settings-card-title">Cấu hình kết nối Mailbox</span>
        </div>

        <div className="settings-help">
          <p style={{ fontWeight: '600', marginBottom: '8px', color: 'var(--text-primary)' }}>
            📌 Hướng dẫn lấy App Password của Gmail:
          </p>
          <ol style={{ paddingLeft: '20px', lineHeight: '1.6' }}>
            <li>Kích hoạt <a href="https://myaccount.google.com/security" target="_blank" rel="noreferrer" style={{ textDecoration: 'underline' }}>Xác minh 2 bước (2-Step Verification)</a> trên tài khoản Google.</li>
            <li>Truy cập mục tạo <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" style={{ textDecoration: 'underline' }}>Mật khẩu ứng dụng (App Passwords)</a>.</li>
            <li>Đặt tên gợi nhớ (Ví dụ: "Email Translator") → Nhấn **Tạo** → Copy chuỗi mật mã 16 chữ số.</li>
          </ol>
        </div>

        <div className="settings-form">
          <div className="form-group">
            <label className="form-label">Gmail App Password</label>
            <div className="password-input-wrap">
              <input
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                placeholder="Nhập 16 chữ số mật khẩu ứng dụng..."
                value={appPassword}
                onChange={(e) => setAppPassword(e.target.value)}
              />
              <button
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                type="button"
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          <details className="settings-advanced">
            <summary>⚙️ IMAP / SMTP nâng cao</summary>
            <div className="settings-grid-2">
              <div className="form-group">
                <label className="form-label">IMAP Host</label>
                <input className="form-input" value={imapHost} onChange={e => setImapHost(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">IMAP Port</label>
                <input className="form-input" type="number" value={imapPort} onChange={e => setImapPort(Number(e.target.value))} />
              </div>
              <div className="form-group">
                <label className="form-label">SMTP Host</label>
                <input className="form-input" value={smtpHost} onChange={e => setSmtpHost(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">SMTP Port</label>
                <input className="form-input" type="number" value={smtpPort} onChange={e => setSmtpPort(Number(e.target.value))} />
              </div>
            </div>
          </details>

          {/* Test Results */}
          {testResult && (
            <div className="test-results">
              <div className={`test-result-item ${testResult.imap.success ? 'success' : 'error'}`}>
                <span>{testResult.imap.success ? '✅' : '❌'}</span>
                <span>IMAP Connection: {testResult.imap.message}</span>
              </div>
              <div className={`test-result-item ${testResult.smtp.success ? 'success' : 'error'}`}>
                <span>{testResult.smtp.success ? '✅' : '❌'}</span>
                <span>SMTP Connection: {testResult.smtp.message}</span>
              </div>
            </div>
          )}

          <div className="settings-actions">
            <button className="btn btn-ghost" onClick={handleTest} disabled={testing || !appPassword.trim()}>
              {testing ? '🔌 Đang kết nối...' : '🔌 Kiểm tra kết nối'}
            </button>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving || !appPassword.trim()}>
              {saving ? '💾 Đang lưu...' : '💾 Lưu cấu hình'}
            </button>
          </div>
        </div>
      </div>

      {/* Delete Config */}
      {status?.configured && (
        <div className="settings-card" style={{ borderColor: 'rgba(239, 68, 68, 0.25)' }}>
          <div className="settings-card-header">
            <span className="settings-card-icon">⚠️</span>
            <span className="settings-card-title" style={{ color: 'var(--danger)' }}>Khu vực nguy hiểm</span>
          </div>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            Xóa cấu hình email đã lưu trong cơ sở dữ liệu. Sau khi xóa, hệ thống sẽ sử dụng lại cấu hình mặc định từ tệp môi trường `.env`.
          </p>
          <button className="btn btn-danger" onClick={handleDelete} disabled={deleting}>
            {deleting ? '🗑️ Đang xóa...' : '🗑️ Xóa cấu hình email'}
          </button>
        </div>
      )}
    </div>
  )
}
