import { useRef } from 'react'
import { Upload, Trash2, FileText, Loader2, CheckCircle, XCircle } from 'lucide-react'

export default function Sidebar({ documents, onUpload, onClearAll, uploading }) {
  const fileRef = useRef(null)

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'application/pdf') {
      onUpload(file)
    }
    e.target.value = ''
  }

  const getStatusIcon = (status) => {
    if (status === 'done') return <CheckCircle size={14} className="text-green-500" />
    if (status === 'failed') return <XCircle size={14} className="text-red-500" />
    return <Loader2 size={14} className="text-blue-500 animate-spin" />
  }

  const getStatusText = (status) => {
    if (status === 'done') return 'Ready'
    if (status === 'failed') return 'Failed'
    return 'Processing...'
  }

  return (
    <aside className="w-64 border-r border-gray-200 dark:border-gray-800
                      bg-white dark:bg-gray-950 flex flex-col shrink-0">

      {/* Upload button */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-800">
        <button
          onClick={() => fileRef.current.click()}
          disabled={uploading}
          className="w-full flex items-center justify-center gap-2
                     py-2.5 px-4 rounded-xl
                     bg-gray-950 dark:bg-white
                     text-white dark:text-gray-950
                     text-sm font-semibold
                     hover:bg-gray-800 dark:hover:bg-gray-100
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-all duration-200"
        >
          {uploading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Upload size={16} />
          )}
          {uploading ? 'Uploading...' : 'Upload PDF'}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {/* Documents list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        <p className="text-xs font-semibold text-gray-400 dark:text-gray-500 
                      uppercase tracking-wider mb-3">
          Documents ({documents.length})
        </p>

        {documents.length === 0 && (
          <div className="text-center py-8">
            <FileText size={32} className="text-gray-300 dark:text-gray-700 mx-auto mb-2" />
            <p className="text-xs text-gray-400 dark:text-gray-600">
              No documents yet.
              <br />Upload a PDF to get started.
            </p>
          </div>
        )}

        {documents.map((doc) => (
          <div
            key={doc.id}
            className="p-3 rounded-xl bg-gray-50 dark:bg-gray-900
                       border border-gray-100 dark:border-gray-800"
          >
            <div className="flex items-start gap-2">
              <FileText size={14} className="text-gray-400 mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-gray-800 dark:text-gray-200 
                               truncate">
                  {doc.filename}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  {getStatusIcon(doc.status)}
                  <span className="text-xs text-gray-400 dark:text-gray-500">
                    {getStatusText(doc.status)}
                  </span>
                </div>
                {doc.summary && doc.status === 'done' && (
                  <p className="text-xs text-gray-400 dark:text-gray-500 
                                 mt-1 line-clamp-2">
                    {doc.summary}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Clear all */}
      {documents.length > 0 && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-800">
          <button
            onClick={onClearAll}
            className="w-full flex items-center justify-center gap-2
                       py-2 px-4 rounded-xl
                       text-red-500 dark:text-red-400
                       hover:bg-red-50 dark:hover:bg-red-950
                       text-xs font-medium
                       transition-all duration-200"
          >
            <Trash2 size={14} />
            Clear All Documents
          </button>
        </div>
      )}
    </aside>
  )
}