import React from 'react'
import { useNavigate } from 'react-router-dom'
import StatusBadge from './StatusBadge'
import { retryJob, getDownloadUrl } from '../api/client'
import { useToast } from '../context/ToastContext'

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('vi-VN', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function SkeletonRows({ count = 5 }) {
  return Array.from({ length: count }).map((_, i) => (
    <tr key={i}>
      <td colSpan={6}><div className="skeleton skeleton-row" /></td>
    </tr>
  ))
}

export default function JobsTable({ jobs, loading, onRefresh }) {
  const navigate = useNavigate()
  const toast = useToast()
  const [retrying, setRetrying] = React.useState(null)

  const handleRetry = async (e, jobId) => {
    e.stopPropagation()
    setRetrying(jobId)
    try {
      const res = await retryJob(jobId)
      toast.success('Đang retry', res.message)
      setTimeout(onRefresh, 2000)
    } catch {
      toast.error('Lỗi', 'Không thể retry job này')
    } finally {
      setRetrying(null)
    }
  }

  const handleDownload = (e, jobId) => {
    e.stopPropagation()
    window.open(getDownloadUrl(jobId), '_blank')
  }

  return (
    <div className="table-container">
      <div className="table-header">
        <span className="table-title">📋 Danh sách bài dịch</span>
        <span className="table-count">{loading ? '...' : `${jobs.length} bài`}</span>
      </div>

      {!loading && jobs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📭</div>
          <div className="empty-title">Chưa có bài nào</div>
          <div className="empty-desc">
            Gửi email với file <code style={{color:'var(--accent-light)'}}>abc(ru).docx</code> để bắt đầu
          </div>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th style={{width:40}}>#</th>
              <th>File gốc</th>
              <th>Người gửi</th>
              <th>Trạng thái</th>
              <th>Thời gian</th>
              <th style={{width:140}}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <SkeletonRows count={5} />
            ) : (
              jobs.map(job => (
                <tr
                  key={job.id}
                  onClick={() => navigate(`/jobs/${job.id}`)}
                  style={{ cursor: 'pointer' }}
                >
                  <td className="text-muted font-mono">{job.id}</td>
                  <td>
                    <div className="td-filename" title={job.original_filename}>
                      📄 {job.original_filename}
                    </div>
                    {job.translated_filename && (
                      <div className="td-email" style={{ marginTop: 2 }}>
                        → {job.translated_filename}
                      </div>
                    )}
                  </td>
                  <td>
                    <div style={{ fontSize: 13 }}>{job.sender_name || '—'}</div>
                    <div className="td-email">{job.sender_email}</div>
                  </td>
                  <td><StatusBadge status={job.status} /></td>
                  <td className="text-muted" style={{ fontSize: 12 }}>
                    {formatDate(job.created_at)}
                  </td>
                  <td>
                    <div className="td-actions">
                      {job.is_retryable && (
                        <button
                          id={`retry-btn-${job.id}`}
                          className="btn btn-sm btn-danger"
                          onClick={(e) => handleRetry(e, job.id)}
                          disabled={retrying === job.id}
                        >
                          {retrying === job.id ? '⏳' : '🔁'}
                        </button>
                      )}
                      {job.has_file && (
                        <button
                          id={`dl-btn-${job.id}`}
                          className="btn btn-sm btn-success"
                          onClick={(e) => handleDownload(e, job.id)}
                          title="Download file đã dịch"
                        >
                          ⬇️
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}
