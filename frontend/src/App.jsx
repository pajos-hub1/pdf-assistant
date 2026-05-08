import { useState, useEffect, useRef } from 'react'
import { useAuth } from './context/AuthContext'
import { useChat } from './context/ChatContext'
import Register from './components/Auth/Register'
import Header from './components/Layout/Header'
import Sidebar from './components/Sidebar/Sidebar'
import ChatWindow from './components/Chat/ChatWindow'
import ChatInput from './components/Chat/ChatInput'
import { useStream } from './hooks/useStream'
import {
  uploadPDF,
  checkStatus,
  getChatDocuments,
  getChatHistory,
  clearDocuments,
  clearHistory
} from './services/api'

export default function App() {
  const { isAuthenticated, updateSession } = useAuth()
  const {
    chats,
    activeChatId,
    setActiveChatId,
    loadChats,
    createNewChat,
    updateChatStats
  } = useChat()
  const { streaming, streamQuestion } = useStream()

  const isAskingRef = useRef(false)
  const messagesRef = useRef([])
  const assistantIndexRef = useRef(-1)
  const finalAssistantIndexRef = useRef(-1)
  const loadingChatRef = useRef(null)

  const [messages, setMessages] = useState([])
  const [documents, setDocuments] = useState([])
  const [uploading, setUploading] = useState(false)
  const [hasReadyDoc, setHasReadyDoc] = useState(false)

  // Keep messagesRef in sync
  useEffect(() => {
    messagesRef.current = messages
  }, [messages])

  // Auto reset when streaming stops
  useEffect(() => {
    if (!streaming) {
      isAskingRef.current = false
    }
  }, [streaming])

  // On login — load all chats
  useEffect(() => {
    if (isAuthenticated) {
      initializeChats()
    } else {
      setMessages([])
      messagesRef.current = []
      setDocuments([])
      setHasReadyDoc(false)
      loadingChatRef.current = null
    }
  }, [isAuthenticated])

  // When active chat changes — load its data
  useEffect(() => {
    if (activeChatId && activeChatId !== loadingChatRef.current) {
      loadingChatRef.current = activeChatId
      loadChatData(activeChatId)
    }
  }, [activeChatId])

  // Check if any doc is ready
  useEffect(() => {
    const ready = documents.some((d) => d.status === 'done')
    setHasReadyDoc(ready)
  }, [documents])

  // Poll only when processing
  useEffect(() => {
    const processing = documents.filter((d) => d.status === 'processing')
    if (processing.length === 0) return

    const currentChatId = activeChatId

    const interval = setInterval(async () => {
      if (activeChatId !== currentChatId) {
        clearInterval(interval)
        return
      }
      loadDocuments()
    }, 15000)

    return () => clearInterval(interval)
  }, [documents, activeChatId])

  // ─────────────────────────────────────────
  // INIT
  // ─────────────────────────────────────────

  const initializeChats = async () => {
    const allChats = await loadChats()
    if (allChats.length === 0) return

    const savedSessionId = localStorage.getItem('session_id')
    const savedExists = allChats.some((c) => c.id === savedSessionId)
    const chatToLoad = savedExists ? savedSessionId : allChats[0].id

    if (!savedExists) {
      localStorage.setItem('session_id', chatToLoad)
    }

    setActiveChatId(chatToLoad)
  }

  // ─────────────────────────────────────────
  // LOADERS
  // ─────────────────────────────────────────

  const loadChatData = async (chatId) => {
    setMessages([])
    messagesRef.current = []
    setDocuments([])

    try {
      const [histData, docData] = await Promise.all([
        getChatHistory(chatId),
        getChatDocuments(chatId)
      ])

      const formatted = []
      for (const record of histData.history || []) {
        formatted.push({ role: 'user', content: record.question })
        formatted.push({
          role: 'assistant',
          content: record.answer,
          confidence: record.confidence,
          sources: record.sources,
          suggestions: record.suggestions,
          language_detected: record.language,
          streaming: false
        })
      }
      setMessages(formatted)
      messagesRef.current = formatted
      setDocuments(docData.documents || [])
    } catch (err) {
      console.error('Failed to load chat data:', err)
    }
  }

  const loadDocuments = async () => {
    if (!activeChatId) return
    try {
      const data = await getChatDocuments(activeChatId)
      setDocuments(data.documents || [])
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }

  // ─────────────────────────────────────────
  // CHAT SWITCH
  // ─────────────────────────────────────────

  const handleChatSwitch = (chatId) => {
    setMessages([])
    messagesRef.current = []
    setDocuments([])
    setHasReadyDoc(false)
    assistantIndexRef.current = -1
    finalAssistantIndexRef.current = -1
    isAskingRef.current = false
    loadingChatRef.current = chatId
    loadChatData(chatId)
  }

  // ─────────────────────────────────────────
  // UPLOAD
  // ─────────────────────────────────────────

  const handleUpload = async (file) => {
    if (!activeChatId) {
      alert('Please select or create a chat first.')
      return
    }
    setUploading(true)
    try {
      const data = await uploadPDF(file)
      if (data.session_id) {
        updateSession(data.session_id)
      }
      setDocuments((prev) => [
        ...prev,
        { id: data.doc_id, filename: file.name, status: 'processing', summary: '' }
      ])
      pollDocumentStatus(data.doc_id)
    } catch (err) {
      console.error('Upload failed:', err)
    } finally {
      setUploading(false)
    }
  }

  const pollDocumentStatus = (docId) => {
    const currentChatId = activeChatId
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/status/${docId}`, {
          headers: {
            'X-API-Key': localStorage.getItem('api_key') || '',
            'X-Session-Id': localStorage.getItem('session_id') || ''
          }
        })
        const data = await res.json()
        if (data.status === 'done' || data.status === 'failed') {
          clearInterval(interval)
          if (activeChatId === currentChatId) {
            loadDocuments()
            updateChatStats(currentChatId, {
              doc_count: documents.length + 1
            })
          }
        }
      } catch (err) {
        clearInterval(interval)
      }
    }, 10000)
  }

  // ─────────────────────────────────────────
  // ASK
  // ─────────────────────────────────────────

  const handleAsk = async (question) => {
    if (!question.trim() || streaming) return

    isAskingRef.current = true
    assistantIndexRef.current = -1
    finalAssistantIndexRef.current = -1

    const snapshot = [...messagesRef.current]
    const withUser = [...snapshot, { role: 'user', content: question }]
    messagesRef.current = withUser
    setMessages(withUser)

    await streamQuestion(
      question,

      // onToken
      (token) => {
        if (assistantIndexRef.current === -1) {
          const base = [...messagesRef.current]
          const withAssistant = [
            ...base,
            { role: 'assistant', content: token, streaming: true }
          ]
          const newIdx = withAssistant.length - 1
          assistantIndexRef.current = newIdx
          finalAssistantIndexRef.current = newIdx
          messagesRef.current = withAssistant
          setMessages([...withAssistant])
        } else {
          const idx = assistantIndexRef.current
          const base = [...messagesRef.current]
          if (idx >= 0 && idx < base.length) {
            base[idx] = {
              ...base[idx],
              content: base[idx].content + token,
              streaming: true
            }
            messagesRef.current = base
            setMessages([...base])
          }
        }
      },

      // onDone
      (metadata) => {
        const idx = assistantIndexRef.current
        finalAssistantIndexRef.current = idx
        const base = [...messagesRef.current]

        if (idx >= 0 && idx < base.length) {
          base[idx] = {
            ...base[idx],
            streaming: false,
            confidence: metadata.confidence,
            sources: `Pages: ${metadata.sources}`,
            suggestions: metadata.suggestions || [],
            language_detected: metadata.language
          }
          messagesRef.current = base
          setMessages([...base])
        }

        if (activeChatId) {
          updateChatStats(activeChatId, {
            message_count: Math.floor(base.length / 2)
          })
        }

        assistantIndexRef.current = -1
        isAskingRef.current = false
      },

      // onError
      (error) => {
        const idx = assistantIndexRef.current
        const base = [...messagesRef.current]
        const msg = error.includes('500')
          ? '❌ Something went wrong. Please try again.'
          : `❌ ${error}`

        if (idx >= 0 && idx < base.length) {
          base[idx] = { role: 'assistant', content: msg, streaming: false }
        } else {
          base.push({ role: 'assistant', content: msg, streaming: false })
        }

        messagesRef.current = base
        setMessages([...base])
        assistantIndexRef.current = -1
        finalAssistantIndexRef.current = -1
        isAskingRef.current = false
      },

      // onSuggestions — find last assistant message
      (suggestions) => {
        const base = [...messagesRef.current]

        let targetIdx = -1
        for (let i = base.length - 1; i >= 0; i--) {
          if (base[i].role === 'assistant' && !base[i].streaming) {
            targetIdx = i
            break
          }
        }

        if (targetIdx >= 0 && suggestions && suggestions.length > 0) {
          base[targetIdx] = { ...base[targetIdx], suggestions }
          messagesRef.current = base
          setMessages([...base])
        }
      }
    )
  }

  // ─────────────────────────────────────────
  // CLEAR
  // ─────────────────────────────────────────

  const handleClearAll = async () => {
    try {
      await clearDocuments()
      await clearHistory()
      setMessages([])
      messagesRef.current = []
      setDocuments([])
      setHasReadyDoc(false)
    } catch (err) {
      console.error('Clear failed:', err)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    if (streaming || isAskingRef.current) return
    handleAsk(suggestion)
  }

  // ─────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────

  if (!isAuthenticated) return <Register />

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-gray-950 overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          documents={documents}
          onUpload={handleUpload}
          onClearAll={handleClearAll}
          uploading={uploading}
          onChatSwitch={handleChatSwitch}
        />
        <main className="flex-1 flex flex-col overflow-hidden">
          {!activeChatId ? (
            <div className="flex-1 flex flex-col items-center justify-center
                            text-center p-8">
              <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-900
                              flex items-center justify-center mb-4">
                <span className="text-3xl">💬</span>
              </div>
              <h2 className="text-lg font-semibold
                             text-gray-800 dark:text-gray-200 mb-2">
                Select or create a chat
              </h2>
              <p className="text-sm text-gray-400 dark:text-gray-600 max-w-sm">
                Choose an existing chat from the sidebar or
                create a new one to get started.
              </p>
            </div>
          ) : (
            <>
              <ChatWindow
                messages={messages}
                loading={streaming}
                onSuggestionClick={handleSuggestionClick}
              />
              <ChatInput
                onSend={handleAsk}
                loading={streaming}
                disabled={!hasReadyDoc || streaming}
              />
            </>
          )}
        </main>
      </div>
    </div>
  )
}