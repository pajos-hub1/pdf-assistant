import { useState, useRef, useEffect } from 'react'
import { MessageSquare, Trash2, Pencil, Check, X } from 'lucide-react'
import { useChat } from '../../context/ChatContext'

export default function ChatListItem({ chat, isActive, onClick }) {
  const { renameChat, deleteChat } = useChat()
  const [isEditing, setIsEditing] = useState(false)
  const [editName, setEditName] = useState(chat.name)
  const [showDelete, setShowDelete] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    if (isEditing) inputRef.current?.focus()
  }, [isEditing])

  const handleRename = async () => {
    if (editName.trim() && editName !== chat.name) {
      await renameChat(chat.id, editName.trim())
    }
    setIsEditing(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleRename()
    if (e.key === 'Escape') {
      setEditName(chat.name)
      setIsEditing(false)
    }
  }

  const handleDelete = async (e) => {
    e.stopPropagation()
    await deleteChat(chat.id)
  }

  const formatTime = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const now = new Date()
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setShowDelete(true)}
      onMouseLeave={() => setShowDelete(false)}
      className={`group relative flex items-start gap-2 p-3 rounded-xl
                  cursor-pointer transition-all duration-150
                  ${isActive
                    ? 'bg-gray-100 dark:bg-gray-800'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-900'
                  }`}
    >
      {/* Icon */}
      <div className={`w-7 h-7 rounded-lg flex items-center justify-center
                       shrink-0 mt-0.5
                       ${isActive
                         ? 'bg-gray-950 dark:bg-white'
                         : 'bg-gray-200 dark:bg-gray-700'
                       }`}>
        <MessageSquare
          size={13}
          className={isActive
            ? 'text-white dark:text-gray-950'
            : 'text-gray-500 dark:text-gray-400'
          }
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {isEditing ? (
          <div className="flex items-center gap-1">
            <input
              ref={inputRef}
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              onKeyDown={handleKeyDown}
              onClick={(e) => e.stopPropagation()}
              className="flex-1 text-xs bg-white dark:bg-gray-700
                         border border-gray-300 dark:border-gray-600
                         rounded-lg px-2 py-1 text-gray-900 dark:text-white
                         focus:outline-none"
            />
            <button
              onClick={(e) => { e.stopPropagation(); handleRename() }}
              className="text-green-500 hover:text-green-600"
            >
              <Check size={12} />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                setEditName(chat.name)
                setIsEditing(false)
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              <X size={12} />
            </button>
          </div>
        ) : (
          <p className={`text-xs font-medium truncate
                         ${isActive
                           ? 'text-gray-900 dark:text-white'
                           : 'text-gray-700 dark:text-gray-300'
                         }`}>
            {chat.name}
          </p>
        )}

        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs text-gray-400 dark:text-gray-500">
            {formatTime(chat.last_active)}
          </span>
          {chat.message_count > 0 && (
            <span className="text-xs text-gray-400 dark:text-gray-500">
              · {chat.message_count} msgs
            </span>
          )}
          {chat.doc_count > 0 && (
            <span className="text-xs text-gray-400 dark:text-gray-500">
              · {chat.doc_count} docs
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      {showDelete && !isEditing && (
        <div
          className="absolute right-2 top-1/2 -translate-y-1/2
                     flex items-center gap-1"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={(e) => { e.stopPropagation(); setIsEditing(true) }}
            className="p-1 rounded-lg text-gray-400
                       hover:text-gray-600 dark:hover:text-gray-300
                       hover:bg-gray-200 dark:hover:bg-gray-700
                       transition-all"
            title="Rename"
          >
            <Pencil size={11} />
          </button>
          <button
            onClick={handleDelete}
            className="p-1 rounded-lg text-gray-400
                       hover:text-red-500
                       hover:bg-red-50 dark:hover:bg-red-950
                       transition-all"
            title="Delete"
          >
            <Trash2 size={11} />
          </button>
        </div>
      )}
    </div>
  )
}