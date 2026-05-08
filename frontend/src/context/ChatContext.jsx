import { createContext, useContext, useState, useCallback } from 'react'
import axios from 'axios'

const ChatContext = createContext(null)

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('access_token')
  const sessionId = localStorage.getItem('session_id')
  if (accessToken) config.headers['Authorization'] = `Bearer ${accessToken}`
  if (sessionId) config.headers['X-Session-Id'] = sessionId
  return config
})

export const ChatProvider = ({ children }) => {
  const [chats, setChats] = useState([])
  const [activeChatId, setActiveChatId] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadChats = useCallback(async () => {
    try {
      const { data } = await api.get('/chats')
      setChats(data.chats || [])
      return data.chats || []
    } catch (err) {
      console.error('Failed to load chats:', err)
      return []
    }
  }, [])

  const createNewChat = useCallback(async (name = 'New Chat') => {
    try {
      const { data } = await api.post('/chats/new', { name })
      setChats((prev) => [
        {
          id: data.session_id,
          name: data.name,
          message_count: 0,
          doc_count: 0,
          created_at: data.created_at,
          last_active: data.created_at
        },
        ...prev
      ])
      setActiveChatId(data.session_id)

      // Save new session to localStorage
      localStorage.setItem('session_id', data.session_id)

      return data.session_id
    } catch (err) {
      console.error('Failed to create chat:', err)
      return null
    }
  }, [])

  const renameChat = useCallback(async (sessionId, name) => {
    try {
      await api.patch(`/chats/${sessionId}/rename`, { name })
      setChats((prev) =>
        prev.map((c) => c.id === sessionId ? { ...c, name } : c)
      )
    } catch (err) {
      console.error('Failed to rename chat:', err)
    }
  }, [])

  const deleteChat = useCallback(async (sessionId) => {
    try {
      await api.delete(`/chats/${sessionId}`)
      setChats((prev) => prev.filter((c) => c.id !== sessionId))

      // If deleted chat was active — switch to first remaining
      if (activeChatId === sessionId) {
        setActiveChatId(null)
        localStorage.removeItem('session_id')
      }
    } catch (err) {
      console.error('Failed to delete chat:', err)
    }
  }, [activeChatId])

  const switchChat = useCallback((sessionId) => {
    setActiveChatId(sessionId)
    localStorage.setItem('session_id', sessionId)
  }, [])

  const updateChatStats = useCallback((sessionId, stats) => {
    setChats((prev) =>
      prev.map((c) =>
        c.id === sessionId ? { ...c, ...stats } : c
      )
    )
  }, [])

  return (
    <ChatContext.Provider value={{
      chats,
      activeChatId,
      loading,
      setActiveChatId,
      loadChats,
      createNewChat,
      renameChat,
      deleteChat,
      switchChat,
      updateChatStats
    }}>
      {children}
    </ChatContext.Provider>
  )
}

export const useChat = () => useContext(ChatContext)