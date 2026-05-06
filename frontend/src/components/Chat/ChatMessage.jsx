import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

export default function ChatMessage({ message, onSuggestionClick }) {
  const [showSuggestions, setShowSuggestions] = useState(true)
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>

        {/* Role label */}
        <span className="text-xs text-gray-400 dark:text-gray-500 px-1">
          {isUser ? 'You' : 'Assistant'}
        </span>

        {/* Message bubble */}
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed
          ${isUser
            ? 'bg-gray-950 dark:bg-white text-white dark:text-gray-950 rounded-tr-sm'
            : 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200 rounded-tl-sm'
          }`}>
          {message.content}
        </div>

        {/* Metadata — only for assistant messages */}
        {!isUser && (
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
            {message.language_detected && message.language_detected !== 'English' && (
              <span className="text-xs text-gray-400 dark:text-gray-500">
                🌐 {message.language_detected}
              </span>
            )}
          </div>
        )}

        {/* Suggestions */}
        {!isUser && message.suggestions && message.suggestions.length > 0 && (
          <div className="mt-2 w-full">
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="flex items-center gap-1 text-xs text-gray-400 
                         dark:text-gray-500 hover:text-gray-600 
                         dark:hover:text-gray-300 transition-colors px-1 mb-2"
            >
              {showSuggestions ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
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