import React from 'react'
import { cn } from '../../utils/cn'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'official' | 'provisional' | 'high' | 'medium' | 'low' | 'neutral' | 'accent' | 'warning' | 'gold' | 'pink' | 'blue'
  size?: 'sm' | 'md'
  className?: string
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className,
}) => {
  const variantStyles = {
    official: 'bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]',
    provisional: 'bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]',
    gold: 'bg-[#FEF3C7] text-[#92400E] border-[#FDE68A]',
    pink: 'bg-[#FDF2F8] text-[#EC008C] border-[#FBCFE8]',
    blue: 'bg-[#EFF6FF] text-[#1E40AF] border-[#BFDBFE]',
    high: 'bg-[#EFF6FF] text-[#1E40AF] border-[#BFDBFE]',
    medium: 'bg-[#F0FDFA] text-[#0F766E] border-[#99F6E4]',
    low: 'bg-[#F8FAFC] text-[#64748B] border-[#E2E8F0]',
    neutral: 'bg-[#F1F5F9] text-[#101F43] border-[#CBD5E1]',
    accent: 'bg-[#FDF2F8] text-[#EC008C] border-[#FBCFE8]',
    warning: 'bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]',
  }

  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5',
    md: 'text-xs font-medium px-2.5 py-0.5',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded border font-sans font-semibold tracking-wide',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {children}
    </span>
  )
}
