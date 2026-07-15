import React from 'react'

export default function StatsCards({ stats, loading }) {
  const cards = [
    { key: 'total',      label: 'Tổng số bài',  icon: '📚', type: 'total'   },
    { key: 'done',       label: 'Hoàn thành',   icon: '✅', type: 'done'    },
    { key: 'pending',    label: 'Đang chờ',     icon: '⏳', type: 'pending' },
    { key: 'failed',     label: 'Thất bại',     icon: '❌', type: 'failed'  },
  ]

  const getSubtext = (key) => {
    if (loading || !stats || !stats.total) return null
    if (key === 'done') {
      const percentage = Math.round((stats.done / stats.total) * 100)
      return `Đạt ${percentage}% tổng số`
    }
    if (key === 'failed') {
      const percentage = Math.round((stats.failed / stats.total) * 100)
      return `${percentage}% bị lỗi`
    }
    if (key === 'pending') {
      const active = (stats.pending || 0) + (stats.processing || 0)
      return `${active} bài đang xử lý`
    }
    return 'Dữ liệu thời gian thực'
  }

  return (
    <div className="stats-grid">
      {cards.map(card => (
        <div key={card.key} className="stat-card">
          <div className={`stat-icon ${card.type}`}>{card.icon}</div>
          <div className="stat-info">
            {loading ? (
              <div className="skeleton" style={{ height: 28, width: 48, marginBottom: 6 }} />
            ) : (
              <div className="stat-value">{stats?.[card.key] ?? '0'}</div>
            )}
            <div className="stat-label">{card.label}</div>
            {!loading && (
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px', fontWeight: '500' }}>
                {getSubtext(card.key)}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
