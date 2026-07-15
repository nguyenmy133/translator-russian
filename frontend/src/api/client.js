import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Interceptor: redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.includes('/auth/')) {
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────

export const postAuthGoogle = (idToken) =>
  api.post('/auth/google', { id_token: idToken }).then(r => r.data)

export const getAuthMe = () =>
  api.get('/auth/me').then(r => r.data)

export const postAuthLogout = () =>
  api.post('/auth/logout').then(r => r.data)

// ── Jobs ──────────────────────────────────────────────────────────────

export const getJobs = (params = {}) =>
  api.get('/jobs', { params }).then(r => r.data)

export const getJob = (id) =>
  api.get(`/jobs/${id}`).then(r => r.data)

export const retryJob = (id) =>
  api.post(`/jobs/${id}/retry`).then(r => r.data)

export const deleteJobs = (ids) =>
  api.delete('/jobs', { data: { ids } }).then(r => r.data)

export const getDownloadUrl = (id) => `/api/jobs/${id}/download`

// ── Stats ─────────────────────────────────────────────────────────────

export const getStats = () =>
  api.get('/stats').then(r => r.data)

// ── Trigger ───────────────────────────────────────────────────────────

export const triggerPoll = () =>
  api.post('/trigger').then(r => r.data)

// ── Email Accounts ────────────────────────────────────────────────────

export const getEmailAccountStatus = () =>
  api.get('/email-accounts/status').then(r => r.data)

export const postEmailAccount = (data) =>
  api.post('/email-accounts', data).then(r => r.data)

export const testEmailConnection = (data) =>
  api.post('/email-accounts/test', data).then(r => r.data)

export const deleteEmailAccount = () =>
  api.delete('/email-accounts').then(r => r.data)

export default api
