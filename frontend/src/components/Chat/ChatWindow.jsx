import { useEffect, useRef } from 'react'
import ChatMessage from './ChatMessage'
import { MessageSquare } from 'lucide-react'

export default function ChatWindow({ messages, loading, onSuggestionClick }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6">

      {/* Empty state */}
      {messages.length === 0 && (
        <div className="h-full flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-900
                          flex items-center justify-center mb-4">
            <MessageSquare size={28} className="text-gray-400 dark:text-gray-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">
            Ask anything about your document
          </h2>
          <p className="text-sm text-gray-400 dark:text-gray-600 max-w-sm">
            Upload a PDF from the sidebar, wait for processing to complete,
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
        />
      ))}

      {/* Loading indicator */}
      {loading && (
        <div className="flex justify-start mb-6">
          <div className="max-w-[75%] flex flex-col gap-1 items-start">
            <span className="text-xs text-gray-400 dark:text-gray-500 px-1">
              Assistant
            </span>
            <div className="px-4 py-3 rounded-2xl rounded-tl-sm
                            bg-gray-100 dark:bg-gray-900">
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-gray-400 
                                  dark:bg-gray-500 animate-bounce"
                      style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-gray-400 
                                  dark:bg-gray-500 animate-bounce"
                      style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-gray-400 
                                  dark:bg-gray-500 animate-bounce"
                      style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}