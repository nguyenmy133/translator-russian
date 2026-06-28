import React, { useState, useEffect, useCallback } from 'react'
import StatsCards from '../components/StatsCards'
import JobsTable from '../components/JobsTable'
import { getJobs, getStats } from '../api/client'

export default function Dashboard() {
  const [jobs, setJobs]       = useState([])
  const [stats, setStats]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter]   = useState('ALL')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate]     = useState('')

  const fetchData = useCallback(async () => {
    try {
      const [jobsRes, statsRes] = await Promise.all([getJobs(), getStats()])
      setJobs(jobsRes.jobs)
      setStats(statsRes)
    } catch (err) {
      console.error('Lỗi tải dữ liệu:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    // Auto-refresh mỗi 30 giây
    const interval = setInterval(fetchData, 30_000)
    return () => clearInterval(interval)
  }, [fetchData])

  const filteredJobs = jobs.filter(j => {
    // 1. Lọc theo trạng thái tab
    if (filter !== 'ALL' && j.status !== filter) return false

    // 2. Lọc theo ngày bắt đầu
    if (startDate) {
      const jobDate = new Date(j.created_at)
      const filterStart = new Date(startDate)
      jobDate.setHours(0, 0, 0, 0)
      filterStart.setHours(0, 0, 0, 0)
      if (jobDate < filterStart) return false
    }

    // 3. Lọc theo ngày kết thúc
    if (endDate) {
      const jobDate = new Date(j.created_at)
      const filterEnd = new Date(endDate)
      jobDate.setHours(0, 0, 0, 0)
      filterEnd.setHours(0, 0, 0, 0)
      if (jobDate > filterEnd) return false
    }

    return true
  })

  const filters = [
    { key: 'ALL',        label: 'Tất cả' },
    { key: 'PENDING',    label: '⏳ Chờ' },
    { key: 'PROCESSING', label: '🔄 Đang dịch' },
    { key: 'DONE',       label: '✅ Xong' },
    { key: 'FAILED',     label: '❌ Lỗi' },
  ]

  return (
    <div>
      {/* Stats */}
      <StatsCards stats={stats} loading={loading} />

      {/* Header + Filter */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Danh sách bài dịch</h1>
          <p className="page-subtitle">
            Cập nhật tự động mỗi 30 giây · Tổng {stats?.total ?? '...'} bài
          </p>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-8">
          {filters.map(f => (
            <button
              key={f.key}
              className={`btn btn-sm ${filter === f.key ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Date Filter Panel */}
      <div className="date-filter-panel">
        <div className="date-filter-group">
          <span className="date-filter-label">Từ ngày:</span>
          <input
            type="date"
            className="date-input"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div className="date-filter-group">
          <span className="date-filter-label">Đến ngày:</span>
          <input
            type="date"
            className="date-input"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        {(startDate || endDate) && (
          <button
            className="btn btn-sm btn-ghost"
            style={{ color: '#ff7675' }}
            onClick={() => {
              setStartDate('')
              setEndDate('')
            }}
          >
            Clear lọc
          </button>
        )}
      </div>

      {/* Table */}
      <JobsTable
        jobs={filteredJobs}
        loading={loading}
        onRefresh={fetchData}
      />
    </div>
  )
}
