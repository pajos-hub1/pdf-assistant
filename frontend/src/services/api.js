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

export const register = async (ownerName) => {
  const response = await api.post('/auth/register', { owner_name: ownerName })
  return response.data
}

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

export const healthCheck = async () => {
  const response = await api.get('/health')
  return response.data
}
export const getMe = async () => {
  const response = await api.get('/auth/me')
  return response.data
}