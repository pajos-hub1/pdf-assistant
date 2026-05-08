import { useState, useRef } from 'react'
import { Upload, Trash2, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import ChatList from './ChatList'
import DocumentPreview from '../Documents/DocumentPreview'
import { SkeletonDocument } from '../UI/Skeleton'

export default function Sidebar({
  documents,
  onUpload,
  onClearAll,
  uploading,
  onChatSwitch,
  loadingDocs
}) {
  const fileRef = useRef(null)
  const [showDocs, setShowDocs] = useState(true)

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'application/pdf') {
      onUpload(file)
    }
    e.target.value = ''
  }

  return (
    <aside className="w-64 border-r border-gray-200 dark:border-gray-800
                      bg-white dark:bg-gray-950 flex flex-col shrink-0">

      {/* Chat list */}
      <div className="flex-1 overflow-hidden flex flex-col min-h-0">
        <div className="px-3 pt-3 pb-1">
          <p className="text-xs font-semibold text-gray-400 dark:text-gray-500
                        uppercase tracking-wider">
            Chats
          </p>
        </div>
        <div className="flex-1 overflow-hidden">
          <ChatList onChatSwitch={onChatSwitch} />
        </div>
      </div>

      {/* Documents panel */}
      <div className="border-t border-gray-200 dark:border-gray-800 shrink-0">

        {/* Documents header */}
        <button
          onClick={() => setShowDocs(!showDocs)}
          className="w-full flex items-center justify-between
                     px-3 py-2 text-xs font-semibold
                     text-gray-400 dark:text-gray-500
                     uppercase tracking-wider
                     hover:text-gray-600 dark:hover:text-gray-300
                     transition-colors"
        >
          <span>Documents ({documents.length})</span>
          {showDocs
            ? <ChevronDown size={12} />
            : <ChevronUp size={12} />
          }
        </button>

        {showDocs && (
          <div className="px-3 pb-2 space-y-1.5 max-h-52 overflow-y-auto">
            {loadingDocs ? (
              // Skeleton loading state
              <>
                <SkeletonDocument />
                <SkeletonDocument />
              </>
            ) : documents.length === 0 ? (
              <p className="text-xs text-gray-400 dark:text-gray-600
                            text-center py-3">
                No documents in this chat.
              </p>
            ) : (
              documents.map((doc) => (
                <DocumentPreview key={doc.id} document={doc} />
              ))
            )}
          </div>
        )}

        {/* Upload + Clear */}
        <div className="px-3 pb-3 flex gap-2">
          <button
            onClick={() => fileRef.current.click()}
            disabled={uploading}
            className="flex-1 flex items-center justify-center gap-1
                       py-2 px-3 rounded-xl
                       bg-gray-950 dark:bg-white
                       text-white dark:text-gray-950
                       text-xs font-semibold
                       hover:bg-gray-800 dark:hover:bg-gray-100
                       disabled:opacity-50
                       transition-all duration-200"
          >
            {uploading
              ? <Loader2 size={12} className="animate-spin" />
              : <Upload size={12} />
            }
            {uploading ? 'Uploading...' : 'Upload PDF'}
          </button>

          {documents.length > 0 && (
            <button
              onClick={onClearAll}
              className="p-2 rounded-xl text-red-400
                         hover:bg-red-50 dark:hover:bg-red-950
                         hover:text-red-500 transition-all duration-200"
              title="Clear all documents"
            >
              <Trash2 size={12} />
            </button>
          )}
        </div>

        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>
    </aside>
  )
}