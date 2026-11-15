import React from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { cn } from '../../utils/cn'

interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Data Retrieval Error',
  message,
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        'rounded-xl border border-rose-500/30 bg-rose-950/20 p-6 flex flex-col items-center text-center max-w-lg mx-auto',
        className
      )}
    >
      <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 mb-3">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-rose-200 mb-1">{title}</h3>
      <p className="text-sm text-rose-300/80 mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-sm font-medium text-rose-200 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Retry Request
        </button>
      )}
    </div>
  )
}
