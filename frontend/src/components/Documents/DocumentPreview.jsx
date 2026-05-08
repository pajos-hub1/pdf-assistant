import { useState } from 'react'
import { FileText, ChevronDown, ChevronUp, CheckCircle, Loader2, XCircle } from 'lucide-react'

export default function DocumentPreview({ document }) {
  const [expanded, setExpanded] = useState(false)

  const getStatusIcon = (status) => {
    if (status === 'done') return <CheckCircle size={12} className="text-green-500" />
    if (status === 'failed') return <XCircle size={12} className="text-red-500" />
    return <Loader2 size={12} className="text-blue-500 animate-spin" />
  }

  const getStatusText = (status) => {
    if (status === 'done') return 'Ready'
    if (status === 'failed') return 'Failed'
    return 'Processing...'
  }

  return (
    <div className="rounded-xl border border-gray-100 dark:border-gray-800
                    bg-gray-50 dark:bg-gray-900 overflow-hidden">

      {/* Header row */}
      <div
        className="flex items-center gap-2 p-2.5 cursor-pointer
                   hover:bg-gray-100 dark:hover:bg-gray-800
                   transition-colors"
        onClick={() => document.summary && setExpanded(!expanded)}
      >
        <FileText size={13} className="text-gray-400 shrink-0" />

        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">
            {document.filename}
          </p>
          <div className="flex items-center gap-1 mt-0.5">
            {getStatusIcon(document.status)}
            <span className="text-xs text-gray-400 dark:text-gray-500">
              {getStatusText(document.status)}
            </span>
          </div>
        </div>

        {/* Expand arrow — only if summary exists */}
        {document.summary && (
          <button className="text-gray-400 dark:text-gray-500 shrink-0">
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        )}
      </div>

      {/* Summary panel */}
      {expanded && document.summary && (
        <div className="px-3 pb-3 border-t border-gray-100 dark:border-gray-800">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400
                        mt-2 mb-1">
            Summary
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
            {document.summary}
          </p>
        </div>
      )}
    </div>
  )
}