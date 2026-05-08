import { useEffect, useRef } from 'react'
import ChatMessage from './ChatMessage'
import { SkeletonMessage } from '../UI/Skeleton'
import { MessageSquare } from 'lucide-react'

export default function ChatWindow({
  messages,
  loading,
  onSuggestionClick,
  initialLoading
}) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Show skeletons while chat history is loading
  if (initialLoading) {
    return (
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <SkeletonMessage />
        <SkeletonMessage isUser />
        <SkeletonMessage />
        <SkeletonMessage isUser />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6">

      {/* Empty state */}
      {messages.length === 0 && (
        <div className="h-full flex flex-col items-center
                        justify-center text-center">
          <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-900
                          flex items-center justify-center mb-4">
            <MessageSquare size={28}
                          className="text-gray-400 dark:text-gray-600" />
          </div>
          <h2 className="text-lg font-semibold
                         text-gray-800 dark:text-gray-200 mb-2">
            Ask anything about your document
          </h2>
          <p className="text-sm text-gray-400 dark:text-gray-600 max-w-sm">
            Upload a PDF from the sidebar, wait for processing,
            then start asking questions.
          </p>
        </div>
      )}

      {/* Messages */}
      {messages.map((message, i) => (
        <ChatMessage
          key={i}
          message={message}
          onSuggestionClick={onSuggestionClick}
          isStreaming={loading}
        />
      ))}

      <div ref={bottomRef} />
    </div>
  )
}