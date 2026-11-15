import React from 'react'
import { FolderSearch } from 'lucide-react'
import { cn } from '../../utils/cn'

interface EmptyStateProps {
  title?: string
  description?: string
  icon?: React.ReactNode
  action?: React.ReactNode
  className?: string
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Records Found',
  description = 'No matching players or tactical data match your active filters.',
  icon,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        'rounded-xl border border-slate-800 bg-slate-900/30 p-8 flex flex-col items-center text-center',
        className
      )}
    >
      <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-400 mb-3">
        {icon || <FolderSearch className="w-6 h-6" />}
      </div>
      <h3 className="text-base font-semibold text-slate-200 mb-1">{title}</h3>
      <p className="text-sm text-slate-400 max-w-sm mb-4">{description}</p>
      {action && <div>{action}</div>}
    </div>
  )
}
