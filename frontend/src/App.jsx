import { useState, useEffect } from 'react'
import { useAuth } from './context/AuthContext'
import Register from './components/Auth/Register'
import Header from './components/Layout/Header'
import Sidebar from './components/Layout/Sidebar'
import ChatWindow from './components/Chat/ChatWindow'
import ChatInput from './components/Chat/ChatInput'
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

  const [messages, setMessages] = useState([])
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [hasReadyDoc, setHasReadyDoc] = useState(false)

  // Load documents and history ONCE on login
  useEffect(() => {
    if (isAuthenticated) {
      loadDocuments()
      loadHistory()
    } else {
      // Clear state on logout
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

  // Poll ONLY when documents are still processing
  useEffect(() => {
    const processing = documents.filter((d) => d.status === 'processing')
    if (processing.length === 0) return

    const interval = setInterval(() => {
      loadDocuments() // only poll documents, not history
    }, 15000) // every 15 seconds

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
        formatted.push({
          role: 'user',
          content: record.question
        })
        formatted.push({
          role: 'assistant',
          content: record.answer,
          confidence: record.confidence,
          sources: record.sources,
          suggestions: record.suggestions,
          language_detected: record.language
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

      // Save session_id from first upload
      if (data.session_id) {
        updateSession(data.session_id)
      }

      // Add document immediately with processing status
      setDocuments((prev) => [
        ...prev,
        {
          id: data.doc_id,
          filename: file.name,
          status: 'processing',
          summary: ''
        }
      ])

      // Poll this specific document until done
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
          loadDocuments() // refresh full list when done
        }
      } catch (err) {
        clearInterval(interval)
      }
    }, 10000) // check every 10 seconds
  }

  const handleAsk = async (question) => {
    if (!question.trim() || loading) return

    // Add user message immediately
    setMessages((prev) => [...prev, {
      role: 'user',
      content: question
    }])
    setLoading(true)

    try {
      const data = await askQuestion(question)

      // Add assistant response
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          confidence: data.confidence,
          sources: data.sources,
          suggestions: data.suggestions,
          language_detected: data.language_detected
        }
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '❌ Something went wrong. Please try again.',
        }
      ])
    } finally {
      setLoading(false)
    }
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
    handleAsk(suggestion)
  }

  // Show auth page if not logged in
  if (!isAuthenticated) {
    return <Register />
  }

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-gray-950 overflow-hidden">

      {/* Header */}
      <Header />

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">

        {/* Sidebar */}
        <Sidebar
          documents={documents}
          onUpload={handleUpload}
          onClearAll={handleClearAll}
          uploading={uploading}
        />

        {/* Chat area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <ChatWindow
            messages={messages}
            loading={loading}
            onSuggestionClick={handleSuggestionClick}
          />
          <ChatInput
            onSend={handleAsk}
            loading={loading}
            disabled={!hasReadyDoc}
          />
        </main>
      </div>
    </div>
  )
}