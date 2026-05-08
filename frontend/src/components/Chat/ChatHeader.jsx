import { useState } from 'react'
import { Trash2, FileText, Download, Loader2 } from 'lucide-react'
import { exportChat } from '../../services/api'
import { useToast } from '../../context/ToastContext'

export default function ChatHeader({
  chatName,
  messageCount,
  onClearChat,
  sessionId
}) {
  const { toast } = useToast()
  const [exporting, setExporting] = useState(false)
  const [showExportMenu, setShowExportMenu] = useState(false)

  const handleExport = async (format) => {
    setShowExportMenu(false)
    setExporting(true)
    try {
      const response = await exportChat(sessionId, format)

      // Get filename from response headers
      const disposition = response.headers.get('content-disposition')
      const filename = disposition
        ? disposition.split('filename=')[1]
        : `chat_export.${format}`

      // Download the file
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast.success(`✅ Chat exported as ${format.toUpperCase()}`)
    } catch (err) {
      toast.error('Export failed. Please try again.')
    } finally {
      setExporting(false)
    }
  }

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

      {/* Actions */}
      <div className="flex items-center gap-2">

        {/* Export button */}
        {messageCount > 0 && (
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              disabled={exporting}
              className="flex items-center gap-1.5 px-3 py-1.5
                         rounded-lg text-xs font-medium
                         text-gray-600 dark:text-gray-400
                         hover:bg-gray-100 dark:hover:bg-gray-800
                         disabled:opacity-50
                         transition-all duration-150"
            >
              {exporting
                ? <Loader2 size={12} className="animate-spin" />
                : <Download size={12} />
              }
              Export
            </button>

            {/* Export format menu */}
            {showExportMenu && (
              <div className="absolute right-0 top-full mt-1 z-20
                              bg-white dark:bg-gray-900
                              border border-gray-200 dark:border-gray-700
                              rounded-xl shadow-lg overflow-hidden
                              min-w-32">
                <button
                  onClick={() => handleExport('txt')}
                  className="w-full flex items-center gap-2 px-3 py-2
                             text-xs text-gray-700 dark:text-gray-300
                             hover:bg-gray-50 dark:hover:bg-gray-800
                             transition-colors"
                >
                  <span>📄</span>
                  Export as TXT
                </button>
                <button
                  onClick={() => handleExport('pdf')}
                  className="w-full flex items-center gap-2 px-3 py-2
                             text-xs text-gray-700 dark:text-gray-300
                             hover:bg-gray-50 dark:hover:bg-gray-800
                             transition-colors border-t
                             border-gray-100 dark:border-gray-800"
                >
                  <span>📕</span>
                  Export as PDF
                </button>
              </div>
            )}
          </div>
        )}

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
            Clear
          </button>
        )}
      </div>

      {/* Close export menu on outside click */}
      {showExportMenu && (
        <div
          className="fixed inset-0 z-10"
          onClick={() => setShowExportMenu(false)}
        />
      )}
    </div>
  )
}