export const SkeletonLine = ({ width = 'w-full', height = 'h-3' }) => (
  <div className={`${width} ${height} rounded-full
                   bg-gray-200 dark:bg-gray-700
                   animate-pulse`} />
)

export const SkeletonMessage = ({ isUser = false }) => (
  <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
    <div className="max-w-[75%] flex flex-col gap-2">
      <SkeletonLine width="w-12" height="h-2" />
      <div className={`px-4 py-3 rounded-2xl
                       ${isUser
                         ? 'bg-gray-200 dark:bg-gray-700 rounded-tr-sm'
                         : 'bg-gray-100 dark:bg-gray-800 rounded-tl-sm'
                       }`}>
        <div className="space-y-2">
          <SkeletonLine />
          <SkeletonLine width="w-4/5" />
          <SkeletonLine width="w-3/5" />
        </div>
      </div>
    </div>
  </div>
)

export const SkeletonChatItem = () => (
  <div className="flex items-start gap-2 p-3 rounded-xl">
    <div className="w-7 h-7 rounded-lg bg-gray-200 dark:bg-gray-700
                    animate-pulse shrink-0" />
    <div className="flex-1 space-y-1.5">
      <SkeletonLine width="w-3/4" height="h-2.5" />
      <SkeletonLine width="w-1/2" height="h-2" />
    </div>
  </div>
)

export const SkeletonDocument = () => (
  <div className="flex items-center gap-2 p-2 rounded-lg
                  bg-gray-50 dark:bg-gray-900">
    <div className="w-4 h-4 rounded bg-gray-200 dark:bg-gray-700
                    animate-pulse shrink-0" />
    <div className="flex-1 space-y-1">
      <SkeletonLine width="w-3/4" height="h-2" />
      <SkeletonLine width="w-1/3" height="h-1.5" />
    </div>
  </div>
)