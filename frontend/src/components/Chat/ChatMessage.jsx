import { useState } from 'react'
import { ChevronDown, ChevronUp, Copy, Check } from 'lucide-react'

export default function ChatMessage({ message, onSuggestionClick }) {
  const [showSuggestions, setShowSuggestions] = useState(true)
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Don't render empty assistant messages — show typing indicator instead
  if (!isUser && message.streaming && !message.content) {
    return (
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
    )
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>

        {/* Role label */}
        <span className="text-xs text-gray-400 dark:text-gray-500 px-1">
          {isUser ? 'You' : 'Assistant'}
        </span>

        {/* Message bubble */}
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed relative group
          ${isUser
            ? 'bg-gray-950 dark:bg-white text-white dark:text-gray-950 rounded-tr-sm'
            : 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200 rounded-tl-sm'
          }`}>
          {message.content}

          {/* Streaming cursor */}
          {message.streaming && (
            <span className="inline-block w-1.5 h-4 bg-gray-400 dark:bg-gray-500
                             ml-0.5 align-middle animate-pulse rounded-sm" />
          )}

          {/* Copy button — only for assistant when not streaming */}
          {!isUser && !message.streaming && message.content && (
            <button
              onClick={handleCopy}
              className="absolute top-2 right-2 p-1 rounded-lg
                         opacity-0 group-hover:opacity-100
                         bg-gray-200 dark:bg-gray-700
                         text-gray-500 dark:text-gray-400
                         hover:text-gray-700 dark:hover:text-gray-200
                         transition-all duration-150"
              title="Copy response"
            >
              {copied
                ? <Check size={12} className="text-green-500" />
                : <Copy size={12} />
              }
            </button>
          )}
        </div>

        {/* Metadata — only for completed assistant messages */}
        {!isUser && !message.streaming && (
          <div className="flex items-center gap-3 px-1 flex-wrap">
            {message.confidence && (
              <span className="text-xs text-gray-400 dark:text-gray-500">
                🎯 {parseFloat(message.confidence).toFixed(1)}% confidence
              </span>
            )}
            {message.sources && (
              <span className="text-xs text-gray-400 dark:text-gray-500">
                📄 {message.sources}
              </span>
            )}
            {message.language_detected &&
             message.language_detected !== 'English' &&
             message.language_detected !== 'Mathematical' && (
              <span className="text-xs text-gray-400 dark:text-gray-500">
                🌐 {message.language_detected}
              </span>
            )}
          </div>
        )}

        {/* Suggestions — only show if answer is NOT a refusal */}
        {!isUser &&
         !message.streaming &&
         message.suggestions &&
         message.suggestions.length > 0 &&
         !message.content.toLowerCase().includes("don't have enough information") &&
         !message.content.toLowerCase().includes("cannot answer") &&
         !message.content.toLowerCase().includes("not in this document") && (
          <div className="mt-2 w-full">
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="flex items-center gap-1 text-xs text-gray-400
                         dark:text-gray-500 hover:text-gray-600
                         dark:hover:text-gray-300 transition-colors px-1 mb-2"
            >
              {showSuggestions
                ? <ChevronUp size={12} />
                : <ChevronDown size={12} />
              }
              Suggested follow-ups
            </button>

            {showSuggestions && (
              <div className="flex flex-col gap-1">
                {message.suggestions.map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => onSuggestionClick(suggestion)}
                    className="text-left text-xs px-3 py-2 rounded-xl
                               border border-gray-200 dark:border-gray-700
                               text-gray-600 dark:text-gray-400
                               hover:bg-gray-50 dark:hover:bg-gray-800
                               hover:border-gray-300 dark:hover:border-gray-600
                               transition-all duration-150"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}