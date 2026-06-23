import React, { useState, useEffect, useCallback } from 'react'
import StatsCards from '../components/StatsCards'
import JobsTable from '../components/JobsTable'
import { getJobs, getStats } from '../api/client'

export default function Dashboard() {
  const [jobs, setJobs]       = useState([])
  const [stats, setStats]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter]   = useState('ALL')

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

  const filteredJobs = filter === 'ALL'
    ? jobs
    : jobs.filter(j => j.status === filter)

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

      {/* Table */}
      <JobsTable
        jobs={filteredJobs}
        loading={loading}
        onRefresh={fetchData}
      />
    </div>
  )
}
