import { useState, useEffect, useRef } from 'react'
import { useAuth } from './context/AuthContext'
import Register from './components/Auth/Register'
import Header from './components/Layout/Header'
import Sidebar from './components/Layout/Sidebar'
import ChatWindow from './components/Chat/ChatWindow'
import ChatInput from './components/Chat/ChatInput'
import { useStream } from './hooks/useStream'
import {
  uploadPDF,
  checkStatus,
  getDocuments,
  clearDocuments,
  askQuestion,
  getHistory,
  clearHistory
} from './services/api'

export default function App() {
  const { isAuthenticated, updateSession } = useAuth()
  const { streaming, streamQuestion } = useStream()
  const isAskingRef = useRef(false) // ← prevents double calls

  const [messages, setMessages] = useState([])
  const [documents, setDocuments] = useState([])
  const [uploading, setUploading] = useState(false)
  const [hasReadyDoc, setHasReadyDoc] = useState(false)

  // Load documents and history ONCE on login
  useEffect(() => {
    if (isAuthenticated) {
      loadDocuments()
      loadHistory()
    } else {
      setMessages([])
      setDocuments([])
      setHasReadyDoc(false)
    }
  }, [isAuthenticated])

  // Check if any document is ready
  useEffect(() => {
    const ready = documents.some((d) => d.status === 'done')
    setHasReadyDoc(ready)
  }, [documents])

  // Poll ONLY when documents are processing
  useEffect(() => {
    const processing = documents.filter((d) => d.status === 'processing')
    if (processing.length === 0) return

    const interval = setInterval(() => {
      loadDocuments()
    }, 15000)

    return () => clearInterval(interval)
  }, [documents])

  const loadDocuments = async () => {
    try {
      const data = await getDocuments()
      setDocuments(data.documents || [])
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }

  const loadHistory = async () => {
    try {
      const data = await getHistory()
      const formatted = []
      for (const record of data.history || []) {
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
    } catch (err) {
      console.error('Failed to load history:', err)
    }
  }

  const handleUpload = async (file) => {
    setUploading(true)
    try {
      const data = await uploadPDF(file)
      if (data.session_id) updateSession(data.session_id)

      setDocuments((prev) => [
        ...prev,
        {
          id: data.doc_id,
          filename: file.name,
          status: 'processing',
          summary: ''
        }
      ])
      pollDocumentStatus(data.doc_id)
    } catch (err) {
      console.error('Upload failed:', err)
    } finally {
      setUploading(false)
    }
  }

  const pollDocumentStatus = (docId) => {
    const interval = setInterval(async () => {
      try {
        const data = await checkStatus(docId)
        if (data.status === 'done' || data.status === 'failed') {
          clearInterval(interval)
          loadDocuments()
        }
      } catch (err) {
        clearInterval(interval)
      }
    }, 10000)
  }

const handleAsk = async (question) => {
  if (!question.trim() || streaming || isAskingRef.current) return
  isAskingRef.current = true

  // Add user message only
  setMessages((prev) => [...prev, { role: 'user', content: question }])

  // Track if assistant message has been added yet
  let assistantAdded = false

  await streamQuestion(
    question,

    // onToken — add assistant message on FIRST token only
    (token) => {
      setMessages((prev) => {
        const updated = [...prev]
        const last = updated[updated.length - 1]

        // Only add assistant bubble on first token
        if (!assistantAdded || last?.role !== 'assistant') {
          assistantAdded = true
          return [...updated, {
            role: 'assistant',
            content: token,
            streaming: true
          }]
        }

        // Append token to existing assistant bubble
        updated[updated.length - 1] = {
          ...last,
          content: last.content + token
        }
        return updated
      })
    },

    // onDone — finalize assistant message
    (metadata) => {
      setMessages((prev) => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last?.role === 'assistant') {
          updated[updated.length - 1] = {
            ...last,
            streaming: false,
            confidence: metadata.confidence,
            sources: `Pages: ${metadata.sources}`,
            suggestions: metadata.suggestions,
            language_detected: metadata.language
          }
        }
        return updated
      })
      isAskingRef.current = false
    },

    // onError
    (error) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ ${error}`,
          streaming: false
        }
      ])
      isAskingRef.current = false
    }
  )
}

  const handleClearAll = async () => {
    try {
      await clearDocuments()
      await clearHistory()
      setDocuments([])
      setMessages([])
      setHasReadyDoc(false)
    } catch (err) {
      console.error('Clear failed:', err)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    if (!streaming && !isAskingRef.current) {
      handleAsk(suggestion)
    }
  }

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
        />
        <main className="flex-1 flex flex-col overflow-hidden">
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
        </main>
      </div>
    </div>
  )
}