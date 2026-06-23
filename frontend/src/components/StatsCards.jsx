import React from 'react'

export default function StatsCards({ stats, loading }) {
  const cards = [
    { key: 'total',      label: 'Tổng số bài',  icon: '📚', type: 'total'   },
    { key: 'done',       label: 'Hoàn thành',   icon: '✅', type: 'done'    },
    { key: 'pending',    label: 'Đang chờ',     icon: '⏳', type: 'pending' },
    { key: 'failed',     label: 'Thất bại',     icon: '❌', type: 'failed'  },
  ]

  return (
    <div className="stats-grid">
      {cards.map(card => (
        <div key={card.key} className="stat-card">
          <div className={`stat-icon ${card.type}`}>{card.icon}</div>
          <div className="stat-info">
            {loading ? (
              <div className="skeleton" style={{ height: 28, width: 48, marginBottom: 6 }} />
            ) : (
              <div className="stat-value">{stats?.[card.key] ?? '—'}</div>
            )}
            <div className="stat-label">{card.label}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
