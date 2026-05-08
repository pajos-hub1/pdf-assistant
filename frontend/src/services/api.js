import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
})

api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('api_key')
  const sessionId = localStorage.getItem('session_id')
  if (apiKey) config.headers['X-API-Key'] = apiKey
  if (sessionId) config.headers['X-Session-Id'] = sessionId
  return config
})

// ─────────────────────────────────────────
// AUTH
// ─────────────────────────────────────────

export const register = async (ownerName) => {
  const response = await api.post('/auth/register', { owner_name: ownerName })
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
// CHAT / QA
// ─────────────────────────────────────────

export const askQuestion = async (question) => {
  const response = await api.post('/ask', { question })
  return response.data
}

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