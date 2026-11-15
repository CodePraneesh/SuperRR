import React from 'react'
import { cn } from '../../utils/cn'

interface StatMetricProps {
  label: string
  value: string | number
  subValue?: string
  trend?: 'positive' | 'negative' | 'neutral'
  weight?: string
  className?: string
}

export const StatMetric: React.FC<StatMetricProps> = ({
  label,
  value,
  subValue,
  trend,
  weight,
  className,
}) => {
  const trendColor = {
    positive: 'text-emerald-700',
    negative: 'text-rose-700',
    neutral: 'text-slate-500',
  }

  return (
    <div className={cn('p-4 rounded-lg bg-white border border-[#E5E7EB]', className)}>
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</span>
        {weight && (
          <span className="text-[10px] font-semibold text-[#EC008C] bg-[#FDF2F8] px-2 py-0.5 rounded border border-[#FBCFE8]">
            {weight}
          </span>
        )}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold font-sans tracking-tight text-[#101F43]">{value}</span>
        {subValue && (
          <span className={cn('text-xs font-medium', trend ? trendColor[trend] : 'text-slate-500')}>
            {subValue}
          </span>
        )}
      </div>
    </div>
  )
}
