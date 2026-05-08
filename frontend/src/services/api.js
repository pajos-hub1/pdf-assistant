import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({ baseURL: API_BASE })

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('access_token')
  const sessionId = localStorage.getItem('session_id')
  if (accessToken) config.headers['Authorization'] = `Bearer ${accessToken}`
  if (sessionId) config.headers['X-Session-Id'] = sessionId
  return config
})

// Auto-refresh on 401 — but NOT for auth endpoints
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    // Skip refresh for auth endpoints — show original error
    const isAuthEndpoint = original.url?.includes('/auth/')
    if (isAuthEndpoint) {
      return Promise.reject(error)
    }

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) throw new Error('No refresh token')

        const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
          refresh_token: refreshToken
        })

        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)

        original.headers['Authorization'] = `Bearer ${data.access_token}`
        return api(original)
      } catch (refreshErr) {
        localStorage.clear()
        window.location.reload()
        return Promise.reject(refreshErr)
      }
    }

    return Promise.reject(error)
  }
)

// ─────────────────────────────────────────
// AUTH
// ─────────────────────────────────────────

export const registerUser = async (ownerName, email, password) => {
  const response = await api.post('/auth/register', {
    owner_name: ownerName,
    email,
    password
  })
  return response.data
}

export const loginUser = async (email, password) => {
  const response = await api.post('/auth/login', { email, password })
  return response.data
}

export const getMe = async () => {
  const response = await api.get('/auth/me')
  return response.data
}

// ─────────────────────────────────────────
// CHATS
// ─────────────────────────────────────────

export const getChats = async () => {
  const response = await api.get('/chats')
  return response.data
}

export const createChat = async (name = 'New Chat') => {
  const response = await api.post('/chats/new', { name })
  return response.data
}

export const renameChat = async (sessionId, name) => {
  const response = await api.patch(`/chats/${sessionId}/rename`, { name })
  return response.data
}

export const deleteChat = async (sessionId) => {
  const response = await api.delete(`/chats/${sessionId}`)
  return response.data
}

export const getChatHistory = async (sessionId) => {
  const response = await api.get(`/chats/${sessionId}/history`)
  return response.data
}

export const getChatDocuments = async (sessionId) => {
  const response = await api.get(`/chats/${sessionId}/documents`)
  return response.data
}

export const exportChat = async (sessionId, format = 'txt') => {
  const accessToken = localStorage.getItem('access_token')
  const response = await fetch(
    `/api/chats/${sessionId}/export?format=${format}`,
    {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }
  )
  if (!response.ok) throw new Error('Export failed')
  return response
}

// ─────────────────────────────────────────
// DOCUMENTS
// ─────────────────────────────────────────

export const uploadPDF = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export const checkStatus = async (docId) => {
  const response = await api.get(`/status/${docId}`)
  return response.data
}

export const getDocuments = async () => {
  const response = await api.get('/documents')
  return response.data
}

export const clearDocuments = async () => {
  const response = await api.delete('/documents')
  return response.data
}

// ─────────────────────────────────────────
// QA
// ─────────────────────────────────────────

export const getHistory = async () => {
  const response = await api.get('/history')
  return response.data
}

export const clearHistory = async () => {
  const response = await api.delete('/history')
  return response.data
}

// ─────────────────────────────────────────
// HEALTH
// ─────────────────────────────────────────

export const healthCheck = async () => {
  const response = await api.get('/health')
  return response.data
}