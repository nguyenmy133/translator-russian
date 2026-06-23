import React from 'react'

export default function StatusBadge({ status }) {
  const labels = {
    PENDING:    'Chờ xử lý',
    PROCESSING: 'Đang dịch',
    DONE:       'Hoàn thành',
    FAILED:     'Thất bại',
  }

  return (
    <span className={`badge badge-${status}`}>
      <span className="badge-dot" />
      {labels[status] || status}
    </span>
  )
}
