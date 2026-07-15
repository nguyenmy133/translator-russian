import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import StatusBadge from '../components/StatusBadge'
import { getJob, retryJob, getDownloadUrl } from '../api/client'
import { useToast } from '../context/ToastContext'

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('vi-VN', {
    weekday: 'long', day: '2-digit', month: '2-digit',
    year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

export default function JobDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()

  const [job, setJob]         = useState(null)
  const [loading, setLoading] = useState(true)
  const [retrying, setRetrying] = useState(false)

  const fetchJob = async () => {
    try {
      const data = await getJob(Number(id))
      setJob(data)
    } catch {
      toast.error('Lỗi', 'Không tìm thấy job')
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchJob() }, [id])

  const handleRetry = async () => {
    setRetrying(true)
    try {
      const res = await retryJob(job.id)
      toast.success('Đang retry', res.message)
      setTimeout(fetchJob, 3000)
    } catch {
      toast.error('Lỗi', 'Không thể retry')
    } finally {
      setRetrying(false)
    }
  }

  if (loading) return (
    <div style={{ padding: 40 }}>
      {[1,2,3].map(i => (
        <div key={i} className="skeleton" style={{ height: 60, marginBottom: 12, borderRadius: 10 }} />
      ))}
    </div>
  )

  if (!job) return null

  return (
    <div>
      {/* Back */}
      <button className="back-link" onClick={() => navigate(-1)}>
        ← Quay lại Dashboard
      </button>

      <div className="page-header">
        <div>
          <h1 className="page-title">Chi tiết bài dịch #{job.id}</h1>
          <p className="page-subtitle">{job.original_filename}</p>
        </div>
        <StatusBadge status={job.status} />
      </div>

      <div className="detail-grid">
        {/* Left: Info */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <p className="section-title">Thông tin chi tiết</p>

          {[
            { label: '📄 File gốc',      value: job.original_filename },
            { label: '✅ File đã dịch',   value: job.translated_filename || '—' },
            { label: '👤 Người gửi',      value: job.sender_name || '—' },
            { label: '📧 Email',          value: job.sender_email },
            { label: '📨 Tiêu đề email', value: job.subject || '—' },
            { label: '📊 Số đoạn văn',   value: job.paragraph_count ? `${job.paragraph_count} đoạn` : '—' },
            { label: '🔤 Số ký tự',       value: job.char_count ? `${job.char_count.toLocaleString()} ký tự` : '—' },
            { label: '🕐 Tạo lúc',       value: formatDate(job.created_at) },
            { label: '✔️ Hoàn thành',    value: formatDate(job.completed_at) },
          ].map(row => (
            <div key={row.label} className="info-row">
              <span className="info-label">{row.label}</span>
              <span className="info-value" style={{ fontWeight: '500' }}>{row.value}</span>
            </div>
          ))}

          {job.error_message && (
            <div className="error-box">
              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>⚠️ LỖI HỆ THỐNG:</div>
              {job.error_message}
            </div>
          )}
        </div>

        {/* Right: Actions & Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Actions */}
          <div className="card">
            <p className="section-title">Thao tác</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {job.has_file && (
                <a
                  id="download-btn"
                  href={getDownloadUrl(job.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-success"
                  style={{ justifyContent: 'center' }}
                >
                  ⬇️ Download file đã dịch
                </a>
              )}

              {job.is_retryable && (
                <button
                  id="retry-btn"
                  className="btn btn-danger"
                  onClick={handleRetry}
                  disabled={retrying}
                  style={{ justifyContent: 'center' }}
                >
                  {retrying ? '⏳ Đang retry...' : '🔁 Thử lại ngay'}
                </button>
              )}

              <button
                className="btn btn-ghost"
                onClick={fetchJob}
                style={{ justifyContent: 'center' }}
              >
                🔄 Làm mới trạng thái
              </button>
            </div>
          </div>

          {/* Stepper Timeline */}
          <div className="card">
            <p className="section-title">Quy trình xử lý</p>
            <div className="timeline">
              {['PENDING', 'PROCESSING', 'DONE'].map((s, i) => {
                const statusOrder = { PENDING: 0, PROCESSING: 1, DONE: 2, FAILED: 2 }
                const currentOrder = statusOrder[job.status] ?? 0
                const isDone = currentOrder > i
                const isCurrent = job.status === s || (s === 'DONE' && job.status === 'FAILED')
                const isFailed = s === 'DONE' && job.status === 'FAILED'

                let itemClass = ""
                if (isDone) itemClass = "done"
                else if (isFailed) itemClass = "failed"
                else if (isCurrent) itemClass = "active"

                const title = isFailed 
                  ? 'Gặp lỗi khi dịch' 
                  : { PENDING: 'Chờ xử lý', PROCESSING: 'Đang dịch thuật', DONE: 'Hoàn thành' }[s]

                const desc = {
                  PENDING: 'Hệ thống đã nhận email và đưa file vào hàng đợi.',
                  PROCESSING: 'Đang tiến hành đọc file Word và dịch bằng Gemini AI.',
                  DONE: isFailed ? 'Xảy ra lỗi trong quá trình dịch thuật hoặc gửi mail.' : 'Đã dịch xong và gửi file dịch về mail người gửi.'
                }[s]

                return (
                  <div key={s} className={`timeline-item ${itemClass}`}>
                    <div className="timeline-dot" />
                    <div className="timeline-content">
                      <div className="timeline-title">{title}</div>
                      <div className="timeline-desc">{desc}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
