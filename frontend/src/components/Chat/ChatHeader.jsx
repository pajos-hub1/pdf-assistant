import { Trash2, FileText } from 'lucide-react'

export default function ChatHeader({ chatName, messageCount, onClearChat }) {
  return (
    <div className="h-12 border-b border-gray-200 dark:border-gray-800
                    bg-white dark:bg-gray-950
                    flex items-center justify-between px-4 shrink-0">

      {/* Chat name + stats */}
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded-lg bg-gray-100 dark:bg-gray-800
                        flex items-center justify-center">
          <FileText size={12} className="text-gray-500 dark:text-gray-400" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
            {chatName || 'Chat'}
          </p>
          {messageCount > 0 && (
            <p className="text-xs text-gray-400 dark:text-gray-500">
              {messageCount} messages
            </p>
          )}
        </div>
      </div>

      {/* Clear chat button */}
      {messageCount > 0 && (
        <button
          onClick={onClearChat}
          className="flex items-center gap-1.5 px-3 py-1.5
                     rounded-lg text-xs font-medium
                     text-red-500 dark:text-red-400
                     hover:bg-red-50 dark:hover:bg-red-950
                     transition-all duration-150"
          title="Clear chat history"
        >
          <Trash2 size={12} />
          Clear chat
        </button>
      )}
    </div>
  )
}