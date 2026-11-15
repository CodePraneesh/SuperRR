import React from 'react'
import { cn } from '../../utils/cn'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  variant?: 'default' | 'glow' | 'gold' | 'royal' | 'interactive' | 'subtle'
  className?: string
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  className,
  ...props
}) => {
  const variantStyles = {
    default: 'bg-white border border-[#E5E7EB] shadow-xs',
    glow: 'bg-white border border-[#E5E7EB] shadow-sm',
    gold: 'bg-white border border-[#E5E7EB] shadow-xs',
    royal: 'bg-white border border-[#E5E7EB] shadow-xs',
    interactive: 'bg-white border border-[#E5E7EB] hover:border-[#EC008C]/40 hover:shadow-sm transition-all duration-150 cursor-pointer',
    subtle: 'bg-[#F5F7FA] border border-[#E5E7EB]',
  }

  return (
    <div
      className={cn('rounded-lg p-5', variantStyles[variant], className)}
      {...props}
    >
      {children}
    </div>
  )
}
