import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Menu, ShieldCheck, AlertCircle } from 'lucide-react'
import { getSystemHealth } from '../../api/systemApi'
import type { HealthResponse } from '../../types/common'

interface HeaderProps {
  onMenuClick: () => void
}

export const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [isOnline, setIsOnline] = useState<boolean | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    let mounted = true
    getSystemHealth()
      .then((data) => {
        if (mounted) {
          setHealth(data)
          setIsOnline(true)
        }
      })
      .catch(() => {
        if (mounted) {
          setIsOnline(false)
        }
      })

    const interval = setInterval(() => {
      getSystemHealth()
        .then((data) => {
          if (mounted) {
            setHealth(data)
            setIsOnline(true)
          }
        })
        .catch(() => {
          if (mounted) {
            setIsOnline(false)
          }
        })
    }, 30000)

    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    navigate(`/players/IPL/Batter/${encodeURIComponent(searchQuery.trim())}`)
    setSearchQuery('')
  }

  return (
    <header className="h-16 border-b border-[#E5E7EB] bg-white px-4 lg:px-8 flex items-center justify-between sticky top-0 z-30">
      {/* Left: Mobile hamburger & Search */}
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <button
          onClick={onMenuClick}
          className="p-2 rounded text-slate-500 hover:text-[#101F43] hover:bg-slate-100 lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search player dossier (e.g. Rinku Singh)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 rounded-md bg-[#F5F7FA] border border-[#E5E7EB] focus:border-[#EC008C] focus:bg-white focus:outline-none text-xs text-[#101F43] placeholder-slate-400 transition-colors"
          />
        </form>
      </div>

      {/* Right: Engine Status & CPRI Seal */}
      <div className="flex items-center gap-3">
        {/* Backend health status pill */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full border border-[#E5E7EB] bg-[#F5F7FA] text-xs">
          {isOnline === true ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-slate-600 font-medium text-[11px]">
                Engine Online <span className="text-slate-400">•</span> v{health?.version || '1.0.0'}
              </span>
            </>
          ) : isOnline === false ? (
            <>
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              <span className="text-rose-600 font-medium text-[11px] flex items-center gap-1">
                <AlertCircle className="w-3 h-3" /> Offline (Port 8000)
              </span>
            </>
          ) : (
            <span className="text-slate-400 text-[11px]">Connecting...</span>
          )}
        </div>

        {/* CPRI Baseline badge */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full border border-[#FBCFE8] bg-[#FDF2F8] text-[#EC008C] text-xs font-semibold">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>CPRI v1.0.0 Certified</span>
        </div>
      </div>
    </header>
  )
}
