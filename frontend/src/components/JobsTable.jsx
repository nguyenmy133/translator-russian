import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import StatusBadge from './StatusBadge'
import DeleteConfirmModal from './DeleteConfirmModal'
import { retryJob, getDownloadUrl, deleteJobs } from '../api/client'
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
      <td colSpan={7}><div className="skeleton skeleton-row" /></td>
    </tr>
  ))
}

export default function JobsTable({ jobs, loading, onRefresh }) {
  const navigate = useNavigate()
  const toast = useToast()
  const [retrying, setRetrying] = useState(null)
  const [selected, setSelected] = useState(new Set())
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const allSelected = jobs.length > 0 && selected.size === jobs.length

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelected(new Set())
    } else {
      setSelected(new Set(jobs.map(j => j.id)))
    }
  }

  const toggleSelect = (id) => {
    const next = new Set(selected)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    setSelected(next)
  }

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

  const handleDelete = async () => {
    setDeleting(true)
    try {
      const ids = Array.from(selected)
      const res = await deleteJobs(ids)
      toast.success('Đã xóa', res.message)
      setSelected(new Set())
      setShowDeleteModal(false)
      onRefresh()
    } catch {
      toast.error('Lỗi', 'Không thể xóa bài dịch')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <>
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
              Gửi email với file <code style={{color:'var(--accent-light)'}}>.docx</code> tiếng Nga để bắt đầu
            </div>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th style={{width: 40}}>
                  <input
                    type="checkbox"
                    className="custom-checkbox"
                    checked={allSelected}
                    onChange={toggleSelectAll}
                  />
                </th>
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
                    className={selected.has(job.id) ? 'row-selected' : ''}
                  >
                    <td onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        className="custom-checkbox"
                        checked={selected.has(job.id)}
                        onChange={() => toggleSelect(job.id)}
                      />
                    </td>
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

      {/* Floating Action Bar */}
      {selected.size > 0 && (
        <div className="floating-bar">
          <span className="floating-bar-text">
            Đã chọn <strong>{selected.size}</strong> bài
          </span>
          <button
            className="btn btn-danger"
            onClick={() => setShowDeleteModal(true)}
            disabled={deleting}
          >
            🗑️ Xóa {selected.size} bài
          </button>
          <button
            className="btn btn-ghost"
            onClick={() => setSelected(new Set())}
          >
            ✕ Bỏ chọn
          </button>
        </div>
      )}

      {/* Delete Confirm Modal */}
      {showDeleteModal && (
        <DeleteConfirmModal
          count={selected.size}
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteModal(false)}
        />
      )}
    </>
  )
}
