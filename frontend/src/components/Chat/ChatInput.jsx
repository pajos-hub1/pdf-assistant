import { useState } from 'react'
import { Send, Loader2 } from 'lucide-react'

export default function ChatInput({ onSend, loading, disabled }) {
  const [input, setInput] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || loading || disabled) return
    onSend(input.trim())
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="p-4 border-t border-gray-200 dark:border-gray-800
                    bg-white dark:bg-gray-950">
      <form onSubmit={handleSubmit} className="flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              disabled
                ? 'Upload and process a PDF first...'
                : 'Ask a question about your document...'
            }
            disabled={disabled || loading}
            rows={1}
            className="w-full px-4 py-3 pr-4 rounded-2xl
                       border border-gray-200 dark:border-gray-700
                       bg-gray-50 dark:bg-gray-900
                       text-gray-900 dark:text-white
                       placeholder-gray-400 dark:placeholder-gray-600
                       focus:outline-none focus:ring-2 
                       focus:ring-gray-900 dark:focus:ring-white
                       disabled:opacity-50 disabled:cursor-not-allowed
                       text-sm resize-none transition-all"
            style={{ minHeight: '48px', maxHeight: '120px' }}
          />
        </div>

        <button
          type="submit"
          disabled={!input.trim() || loading || disabled}
          className="w-11 h-11 rounded-2xl flex items-center justify-center
                     bg-gray-950 dark:bg-white
                     text-white dark:text-gray-950
                     hover:bg-gray-800 dark:hover:bg-gray-100
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-all duration-200 shrink-0"
        >
          {loading
            ? <Loader2 size={16} className="animate-spin" />
            : <Send size={16} />
          }
        </button>
      </form>

      <p className="text-xs text-center text-gray-400 dark:text-gray-600 mt-2">
        Press Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}