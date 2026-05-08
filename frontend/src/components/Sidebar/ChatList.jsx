import { useChat } from '../../context/ChatContext'
import ChatListItem from './ChatListItem'
import { Plus, Loader2 } from 'lucide-react'

export default function ChatList({ onChatSwitch }) {
  const { chats, activeChatId, createNewChat, switchChat, loading } = useChat()

  const handleNewChat = async () => {
    const newId = await createNewChat('New Chat')
    if (newId) onChatSwitch(newId)
  }

  const handleSwitch = (chatId) => {
    if (chatId === activeChatId) return
    switchChat(chatId)
    onChatSwitch(chatId)
  }

  return (
    <div className="flex flex-col h-full">
      {/* New chat button */}
      <div className="p-3 border-b border-gray-200 dark:border-gray-800">
        <button
          onClick={handleNewChat}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2
                     py-2 px-3 rounded-xl
                     bg-gray-950 dark:bg-white
                     text-white dark:text-gray-950
                     text-xs font-semibold
                     hover:bg-gray-800 dark:hover:bg-gray-100
                     disabled:opacity-50
                     transition-all duration-200"
        >
          {loading
            ? <Loader2 size={14} className="animate-spin" />
            : <Plus size={14} />
          }
          New Chat
        </button>
      </div>

      {/* Chat list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {chats.length === 0 && (
          <div className="text-center py-8">
            <p className="text-xs text-gray-400 dark:text-gray-600">
              No chats yet.
              <br />Click New Chat to start.
            </p>
          </div>
        )}

        {chats.map((chat) => (
          <ChatListItem
            key={chat.id}
            chat={chat}
            isActive={chat.id === activeChatId}
            onClick={() => handleSwitch(chat.id)}
          />
        ))}
      </div>
    </div>
  )
}