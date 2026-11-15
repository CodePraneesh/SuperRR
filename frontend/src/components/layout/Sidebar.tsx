import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Trophy,
  Globe,
  UserCheck,
  GitCompare,
  Swords,
  Bot,
  BookOpen,
  X,
} from 'lucide-react'
import { cn } from '../../utils/cn'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const navItems = [
    { name: 'Overview', to: '/', icon: LayoutDashboard },
    { name: 'IPL Rankings', to: '/rankings/ipl', icon: Trophy },
    { name: 'T20I Rankings', to: '/rankings/t20i', icon: Globe },
    { name: 'Player Intelligence', to: '/players/IPL/Batter/Rinku%20Singh', icon: UserCheck },
    { name: 'Player Comparison', to: '/compare', icon: GitCompare },
    { name: 'Matchup Analysis', to: '/matchup', icon: Swords },
    { name: 'AI Scouting Assistant', to: '/assistant', icon: Bot, badge: 'AI' },
    { name: 'Methodology', to: '/methodology', icon: BookOpen },
  ]

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-[#101F43]/40 backdrop-blur-xs z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          'fixed top-0 bottom-0 left-0 z-50 w-64 bg-white border-r border-[#E5E7EB] flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Brand / Logo */}
        <div className="h-16 px-6 flex items-center justify-between border-b border-[#E5E7EB]">
          <NavLink to="/" className="flex items-center gap-2 group" onClick={onClose}>
            <div>
              <div className="text-lg font-black tracking-tight text-[#101F43] flex items-center">
                <span>Supe</span>
                <span className="text-[#EC008C]">RR</span>
                <span className="ml-1 text-[#101F43] font-bold">Selector</span>
              </div>
              <div className="text-[10px] uppercase tracking-wider text-[#EC008C] font-bold">
                Season 2 • Cricket Analytics
              </div>
            </div>
          </NavLink>

          <button
            onClick={onClose}
            className="p-1.5 rounded text-slate-400 hover:text-[#101F43] hover:bg-slate-100 lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tagline Banner */}
        <div className="px-6 py-2.5 border-b border-[#E5E7EB] bg-[#F5F7FA]">
          <p className="text-[11px] font-medium text-slate-600 leading-tight">
            Beyond Performance. <span className="text-[#EC008C] font-semibold">Measuring Pressure.</span>
          </p>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  'flex items-center justify-between px-3.5 py-2.5 rounded text-xs font-semibold tracking-wide transition-colors',
                  isActive
                    ? 'bg-[#FDF2F8] text-[#EC008C] border-l-4 border-[#EC008C] font-bold'
                    : 'text-[#101F43]/80 hover:text-[#101F43] hover:bg-[#F5F7FA]'
                )
              }
            >
              <div className="flex items-center gap-3">
                <item.icon className="w-4 h-4" />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#FDF2F8] text-[#EC008C] border border-[#FBCFE8]">
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* CPRI Specification Seal */}
        <div className="p-4 border-t border-[#E5E7EB] bg-[#F5F7FA]">
          <div className="p-3 rounded bg-white border border-[#E5E7EB]">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] uppercase tracking-wider text-[#EC008C] font-bold">
                Methodology Baseline
              </span>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            </div>
            <div className="text-xs font-bold text-[#101F43]">CPRI v1.0.0 Frozen</div>
            <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
              40% PI • 25% PA • 20% CC • 15% RC
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
