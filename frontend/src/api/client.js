import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Jobs ──────────────────────────────────────────────────────────────

export const getJobs = (params = {}) =>
  api.get('/jobs', { params }).then(r => r.data)

export const getJob = (id) =>
  api.get(`/jobs/${id}`).then(r => r.data)

export const retryJob = (id) =>
  api.post(`/jobs/${id}/retry`).then(r => r.data)

export const getDownloadUrl = (id) => `/api/jobs/${id}/download`

// ── Stats ─────────────────────────────────────────────────────────────

export const getStats = () =>
  api.get('/stats').then(r => r.data)

// ── Trigger ───────────────────────────────────────────────────────────

export const triggerPoll = () =>
  api.post('/trigger').then(r => r.data)

export default api
