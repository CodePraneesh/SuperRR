import React, { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  Trophy,
  Search,
  Filter,
  ArrowUpDown,
  ArrowRight,
  ShieldCheck,
  Crown,
  Flame,
  Target,
  AlertTriangle,
  Info,
  CheckCircle2,
  Sparkles,
  Layers,
  BarChart3,
  UserCheck
} from 'lucide-react'
import { getCohortPlayers } from '../api/playerApi'
import { getOfficialRoleRankings } from '../api/officialApi'
import { getActiveRankings, getActiveSensitivity, ActivePlayerItem, SensitivityWindowItem } from '../api/activeApi'
import type { PlayerSummaryItem } from '../types/player'
import type { OfficialPlayerItem } from '../types/official'
import type { ActiveRole } from '../types/common'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorState } from '../components/common/ErrorState'
import { formatScore } from '../utils/formatters'
import { getErrorMessage } from '../api/client'

type SortField = 'rank' | 'adj_cpri' | 'raw_cpri' | 'ppr' | 'success_rate' | 'balls' | 'pi' | 'pa' | 'cc' | 'rc'
type SortOrder = 'asc' | 'desc'
type ViewTab = 'main' | 'contenders' | 'active' | 'all' | 'official_phase8'

export const RankingsPage: React.FC = () => {
  const { scopeParam } = useParams<{ scopeParam?: string }>()
  const navigate = useNavigate()

  // Mode: 'official' by default, or 'ipl', 't20i', 'active'
  const mode = scopeParam?.toLowerCase() === 'ipl' 
    ? 'ipl' 
    : scopeParam?.toLowerCase() === 't20i' 
    ? 't20i' 
    : scopeParam?.toLowerCase() === 'active'
    ? 'active'
    : 'official'
  const isOfficial = mode === 'official'
  const isActiveMode = mode === 'active'

  const [role, setRole] = useState<ActiveRole>('Batter')
  const [activeTab, setActiveTab] = useState<ViewTab>(isActiveMode ? 'active' : 'main')
  
  // Data stores
  const [officialTop10, setOfficialTop10] = useState<OfficialPlayerItem[]>([])
  const [officialCandidates, setOfficialCandidates] = useState<OfficialPlayerItem[]>([])
  const [mainLeaderboard, setMainLeaderboard] = useState<OfficialPlayerItem[]>([])
  const [contenders, setContenders] = useState<OfficialPlayerItem[]>([])
  const [evidenceCounts, setEvidenceCounts] = useState<Record<string, number>>({})
  const [cohortPlayers, setCohortPlayers] = useState<PlayerSummaryItem[]>([])
  const [activePlayers, setActivePlayers] = useState<ActivePlayerItem[]>([])
  const [activeMetadata, setActiveMetadata] = useState<any>(null)
  const [sensitivityWindows, setSensitivityWindows] = useState<SensitivityWindowItem[]>([])
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getActiveSensitivity()
      .then(res => setSensitivityWindows(res.windows || []))
      .catch(() => {})
  }, [])

  // Filtering & Sorting
  const [search, setSearch] = useState('')
  const [minBallsFilter, setMinBallsFilter] = useState<number>(0)
  const [evidenceTierFilter, setEvidenceTierFilter] = useState<string>('ALL')
  const [formatFilter, setFormatFilter] = useState<string>('ALL')
  const [sortField, setSortField] = useState<SortField>('adj_cpri')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      if (isActiveMode || activeTab === 'active') {
        const actData = await getActiveRankings({ role: role as any, limit: 100 })
        const list = role === 'Batter'
          ? (actData.active_batters || [])
          : (actData.active_bowlers || [])
        setActivePlayers(list)
        setActiveMetadata(actData.metadata)
      }
      
      if (isOfficial) {
        if (role !== 'All-Rounder') {
          const data = await getOfficialRoleRankings(role as 'Batter' | 'Bowler')
          setOfficialTop10(data.official_top10 || [])
          setOfficialCandidates(data.candidates || [])
          setMainLeaderboard(data.main_leaderboard || [])
          setContenders(data.contenders || [])
          setEvidenceCounts(data.evidence_tier_counts || {})
        }
      } else if (!isActiveMode) {
        if (role !== 'All-Rounder') {
          const data = await getCohortPlayers(mode.toUpperCase() as any, role as 'Batter' | 'Bowler', { limit: 100 })
          setCohortPlayers(data.players)
        }
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [mode, role, activeTab])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder(field === 'rank' ? 'asc' : 'desc')
    }
  }

  // Determine current active pool of players based on selected tab
  const tabPool = useMemo(() => {
    if (isActiveMode || activeTab === 'active') {
      return activePlayers
    }
    if (!isOfficial) {
      return cohortPlayers
    }
    switch (activeTab) {
      case 'main':
        return mainLeaderboard
      case 'contenders':
        return contenders
      case 'official_phase8':
        return officialTop10
      case 'all':
      default: {
        // Union of main and contenders
        const combined = [...mainLeaderboard, ...contenders]
        return combined
      }
    }
  }, [isActiveMode, activeTab, isOfficial, activePlayers, cohortPlayers, mainLeaderboard, contenders, officialTop10])

  // Filter and sort players
  const filteredAndSortedPlayers = useMemo(() => {
    return tabPool
      .filter((p: any) => {
        // Search filter
        const matchesName = (p.player_name || '').toLowerCase().includes(search.toLowerCase())
        if (!matchesName) return false

        // Min balls filter
        const balls = p.pressure_stats?.pressure_deliveries || p.pressure_deliveries || p.total_pressure_balls || 0
        if (minBallsFilter > 0 && balls < minBallsFilter) return false

        // Evidence Tier filter
        if (evidenceTierFilter !== 'ALL') {
          const tier = p.evidence_tier || ''
          if (tier !== evidenceTierFilter) return false
        }

        // Format filter
        if (formatFilter !== 'ALL') {
          const fmt = p.competition_evidence || ''
          if (fmt !== formatFilter) return false
        }

        return true
      })
      .sort((a: any, b: any) => {
        let valA = 0
        let valB = 0
        switch (sortField) {
          case 'rank':
            valA = a.active_rank || a.active_ar_rank || (activeTab === 'main' ? a.adjusted_rank : a.official_rank) || 999
            valB = b.active_rank || b.active_ar_rank || (activeTab === 'main' ? b.adjusted_rank : b.official_rank) || 999
            break
          case 'adj_cpri':
            valA = a.composite_ar_cpri ?? a.adjusted_cpri ?? a.cpri_score ?? 0
            valB = b.composite_ar_cpri ?? b.adjusted_cpri ?? b.cpri_score ?? 0
            break
          case 'raw_cpri':
            valA = a.composite_ar_cpri ?? a.cpri_score ?? 0
            valB = b.composite_ar_cpri ?? b.cpri_score ?? 0
            break
          case 'ppr':
            valA = a.ppr_score ?? a.composite_ar_cpri ?? a.cpri_score ?? 0
            valB = b.ppr_score ?? b.composite_ar_cpri ?? b.cpri_score ?? 0
            break
          case 'success_rate':
            valA = a.success_rate_pct ?? a.pressure_strike_rate ?? 0
            valB = b.success_rate_pct ?? b.pressure_strike_rate ?? 0
            break
          case 'balls':
            valA = a.pressure_stats?.pressure_deliveries || a.pressure_deliveries || a.total_pressure_balls || 0
            valB = b.pressure_stats?.pressure_deliveries || b.pressure_deliveries || b.total_pressure_balls || 0
            break
          case 'pi':
            valA = a.components?.pressure_impact || a.score_pressure_impact || 0
            valB = b.components?.pressure_impact || b.score_pressure_impact || 0
            break
          case 'pa':
            valA = a.components?.pressure_adaptability || a.score_adaptability || 0
            valB = b.components?.pressure_adaptability || b.score_adaptability || 0
            break
          case 'cc':
            valA = a.components?.clutch_consistency || a.score_consistency || 0
            valB = b.components?.clutch_consistency || b.score_consistency || 0
            break
          case 'rc':
            valA = a.components?.reliability_confidence || a.score_reliability || 0
            valB = b.components?.reliability_confidence || b.score_reliability || 0
            break
        }
        return sortOrder === 'desc' ? valB - valA : valA - valB
      })
  }, [tabPool, search, minBallsFilter, evidenceTierFilter, formatFilter, sortField, sortOrder, activeTab])

  // Helper for evidence tier badge styling
  const getEvidenceTierBadge = (tier?: string) => {
    switch (tier) {
      case 'Elite Evidence':
        return 'bg-purple-50 text-purple-700 border border-purple-200'
      case 'Strong Evidence':
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
      case 'Moderate Evidence':
        return 'bg-sky-50 text-sky-700 border border-sky-200'
      case 'Limited Evidence':
        return 'bg-amber-50 text-amber-700 border border-amber-200'
      default:
        return 'bg-slate-100 text-slate-600 border border-slate-200'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-[#E5E7EB] rounded-lg p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-widest text-[#EC008C] font-bold mb-1 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-[#EC008C]" />
            <span>Clutch Performance Rankings (CPRI)</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-[#101F43] tracking-tight">
            {isOfficial ? `Clutch Leaderboard • ${role}s` : `${mode.toUpperCase()} ${role} Rankings`}
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
            <strong className="text-[#101F43]">Official Submission:</strong> The Frozen Phase 8 Top 10 tab shows the official Unstop submission lists.
            The "Adjusted CPRI" view is an <span className="font-semibold text-amber-700">Exploratory, post-hoc</span> analysis — not the official ranking.
            Raw Phase 8 CPRI scores are always shown alongside any adjusted scores for transparency.
          </p>
        </div>

        {/* Navigation Switchers */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Format / Mode Switcher */}
          <div className="inline-flex rounded-md p-1 bg-[#F5F7FA] border border-[#E5E7EB] text-xs font-semibold">
            <button
              onClick={() => {
                navigate('/rankings/official')
                setActiveTab('main')
              }}
              className={`px-3 py-1.5 rounded transition-colors flex items-center gap-1.5 ${
                isOfficial && activeTab !== 'active'
                  ? 'bg-[#101F43] text-white shadow-xs'
                  : 'text-slate-600 hover:text-[#101F43]'
              }`}
            >
              <Crown className="w-3.5 h-3.5 text-[#EC008C]" />
              <span>Official Unified (Phase 8)</span>
            </button>
            <button
              onClick={() => {
                navigate('/rankings/active')
                setActiveTab('active')
              }}
              className={`px-3 py-1.5 rounded transition-colors flex items-center gap-1.5 ${
                isActiveMode || activeTab === 'active'
                  ? 'bg-emerald-800 text-white shadow-xs'
                  : 'text-slate-600 hover:text-[#101F43]'
              }`}
            >
              <UserCheck className="w-3.5 h-3.5 text-emerald-300" />
              <span>Recently Active (12m)</span>
              <span className="text-[9px] bg-emerald-500 text-white px-1.5 py-0.2 rounded-full font-bold">SUPP</span>
            </button>
            <button
              onClick={() => navigate('/rankings/ipl')}
              className={`px-3 py-1.5 rounded transition-colors ${
                mode === 'ipl'
                  ? 'bg-[#101F43] text-white shadow-xs'
                  : 'text-slate-600 hover:text-[#101F43]'
              }`}
            >
              IPL Contextual
            </button>
            <button
              onClick={() => navigate('/rankings/t20i')}
              className={`px-3 py-1.5 rounded transition-colors ${
                mode === 't20i'
                  ? 'bg-[#101F43] text-white shadow-xs'
                  : 'text-slate-600 hover:text-[#101F43]'
              }`}
            >
              T20I Contextual
            </button>
          </div>

          {/* Role Switcher */}
          <div className="inline-flex rounded-md p-1 bg-[#F5F7FA] border border-[#E5E7EB] text-xs font-semibold">
            <button
              onClick={() => setRole('Batter')}
              className={`px-3.5 py-1.5 rounded transition-colors ${
                role === 'Batter'
                  ? 'bg-[#101F43] text-white shadow-xs'
                  : 'text-slate-600 hover:text-[#101F43]'
              }`}
            >
              Batters
            </button>
            <button
              onClick={() => setRole('Bowler')}
              className={`px-3.5 py-1.5 rounded transition-colors ${
                role === 'Bowler'
                  ? 'bg-[#101F43] text-white shadow-xs'
                  : 'text-slate-600 hover:text-[#101F43]'
              }`}
            >
              Bowlers
            </button>
          </div>
        </div>
      </div>

      {/* Supplementary Eligibility Banner when in active view */}
      {(isActiveMode || activeTab === 'active') && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-5 shadow-xs space-y-3">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-emerald-700 text-white flex items-center justify-center shrink-0 mt-0.5">
                <UserCheck className="w-4 h-4 text-emerald-200" />
              </div>
              <div className="text-xs text-emerald-950 leading-relaxed">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-bold text-emerald-900 text-sm">
                    Supplementary Eligibility View: Recently Active in Data (Last 12 Months)
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-200 text-emerald-900 border border-emerald-300">
                    POST-HOC RULE
                  </span>
                </div>
                <p className="text-emerald-900/90">
                  <strong>Eligibility Definition:</strong> Player has at least one ball in the supplied ball-by-ball dataset in the evaluated role (batting or bowling) in a match dated on or after <strong>2025-11-01</strong> (12 months prior to latest match <strong>2026-11-01</strong>). 
                  Evaluates in-scope IPL and Senior Men's T20Is. Applied uniformly with no player-name logic.
                </p>
                <p className="text-emerald-800 text-[11px] mt-1 italic">
                  Note: A player absent from this dataset may still play other leagues; the label is strictly "not recently active in the supplied data". The official competition submission remains the Frozen Phase 8 Rankings.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                12-Month Data Window
              </span>
              <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-blue-100 text-blue-800 border border-blue-200">
                Phase 8 Baseline Preserved
              </span>
            </div>
          </div>

          {/* Sensitivity Windows Table */}
          {sensitivityWindows.length > 0 && (
            <div className="mt-3 pt-3 border-t border-emerald-200/70">
              <div className="text-[11px] font-bold text-emerald-950 uppercase tracking-wider mb-2">
                Sensitivity Windows (6 vs 12 vs 18 Months)
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-[11px] border-collapse bg-white/80 rounded border border-emerald-200">
                  <thead>
                    <tr className="bg-emerald-100/80 text-emerald-950 font-bold border-b border-emerald-200">
                      <th className="py-1.5 px-3">Window</th>
                      <th className="py-1.5 px-3">Cutoff Date</th>
                      <th className="py-1.5 px-3">Active Batters</th>
                      <th className="py-1.5 px-3">Batters Dropped from Top 10</th>
                      <th className="py-1.5 px-3">Batters Entered Top 10</th>
                      <th className="py-1.5 px-3">Active Bowlers</th>
                      <th className="py-1.5 px-3">Bowlers Dropped / Entered</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-emerald-100 text-emerald-900">
                    {sensitivityWindows.map((w) => (
                      <tr key={w.window_label} className={w.window_months === 12 ? 'bg-emerald-100/50 font-semibold' : ''}>
                        <td className="py-1.5 px-3 font-medium">
                          {w.window_label} {w.window_months === 12 && '(Primary)'}
                        </td>
                        <td className="py-1.5 px-3 font-mono text-[10px]">{w.cutoff_date}</td>
                        <td className="py-1.5 px-3 font-mono">{w.batters_qualifying_count}</td>
                        <td className="py-1.5 px-3 text-rose-700">{w.batters_dropped_from_top10 || 'None'}</td>
                        <td className="py-1.5 px-3 text-emerald-800">{w.batters_entered_top10 || 'None'}</td>
                        <td className="py-1.5 px-3 font-mono">{w.bowlers_qualifying_count}</td>
                        <td className="py-1.5 px-3 text-slate-600">
                          {w.bowlers_dropped_from_top10 ? `Dropped: ${w.bowlers_dropped_from_top10}; Entered: ${w.bowlers_entered_top10}` : 'None (Top 10 Unchanged)'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Explanatory Methodology Card */}
      {isOfficial && activeTab !== 'active' && (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-[#101F43] text-white flex items-center justify-center shrink-0 mt-0.5">
                <BarChart3 className="w-4 h-4 text-[#EC008C]" />
              </div>
              <div className="text-xs text-slate-700 leading-relaxed">
                <strong className="font-bold text-[#101F43]">Statistical Volume & Reliability Adjustment: </strong>
                Players are classified by pressure deliveries: 
                <span className="font-semibold text-purple-700 ml-1">Elite (600+)</span>, 
                <span className="font-semibold text-emerald-700 ml-1">Strong (400–599)</span>, 
                <span className="font-semibold text-sky-700 ml-1">Moderate (250–399)</span>, and 
                <span className="font-semibold text-amber-700 ml-1">Limited (150–249)</span>.
                Low-volume rate outliers (e.g. Matthew Wade at 191 balls) are regressed toward population baseline and presented in the Contender section, while proven high-volume clutch pillars (e.g. Suryakumar Yadav at 749 balls and Rashid Khan at 970 balls) lead the Main Leaderboard.
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-purple-100 text-purple-800">
                {evidenceCounts['Elite Evidence'] || 0} Elite
              </span>
              <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
                {evidenceCounts['Strong Evidence'] || 0} Strong
              </span>
              <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-sky-100 text-sky-800">
                {evidenceCounts['Moderate Evidence'] || 0} Moderate
              </span>
              <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-amber-100 text-amber-800">
                {evidenceCounts['Limited Evidence'] || 0} Limited
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Section Tabs (Main Leaderboard vs Contenders vs Active vs All vs Official Phase 8) */}
      {(isOfficial || isActiveMode) && (
        <div className="flex flex-wrap items-center gap-2 border-b border-[#E5E7EB] pb-3">
          <button
            onClick={() => {
              setActiveTab('main')
              setSortField('adj_cpri')
              setSortOrder('desc')
            }}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'main'
                ? 'bg-[#101F43] text-white shadow-xs'
                : 'bg-white border border-[#E5E7EB] text-slate-700 hover:bg-[#F5F7FA]'
            }`}
          >
            <Crown className={`w-3.5 h-3.5 ${activeTab === 'main' ? 'text-[#EC008C]' : 'text-slate-400'}`} />
            <span>Main Leaderboard (≥ 400 Balls)</span>
            <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
              activeTab === 'main' ? 'bg-[#EC008C] text-white' : 'bg-slate-100 text-slate-600'
            }`}>
              {mainLeaderboard.length}
            </span>
          </button>

          <button
            onClick={() => {
              setActiveTab('contenders')
              setSortField('adj_cpri')
              setSortOrder('desc')
            }}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'contenders'
                ? 'bg-[#101F43] text-white shadow-xs'
                : 'bg-white border border-[#E5E7EB] text-slate-700 hover:bg-[#F5F7FA]'
            }`}
          >
            <Target className={`w-3.5 h-3.5 ${activeTab === 'contenders' ? 'text-[#EC008C]' : 'text-slate-400'}`} />
            <span>Contenders & Emerging (150–399 Balls)</span>
            <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
              activeTab === 'contenders' ? 'bg-[#EC008C] text-white' : 'bg-slate-100 text-slate-600'
            }`}>
              {contenders.length}
            </span>
          </button>

          <button
            onClick={() => {
              setActiveTab('active')
              setSortField('rank')
              setSortOrder('asc')
            }}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'active'
                ? 'bg-emerald-800 text-white shadow-xs'
                : 'bg-white border border-[#E5E7EB] text-slate-700 hover:bg-[#F5F7FA]'
            }`}
          >
            <UserCheck className={`w-3.5 h-3.5 ${activeTab === 'active' ? 'text-emerald-300' : 'text-slate-400'}`} />
            <span>Recently Active (12m Data)</span>
            <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
              activeTab === 'active' ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-600'
            }`}>
              {activePlayers.length || 'SUPP'}
            </span>
          </button>

          <button
            onClick={() => {
              setActiveTab('all')
              setSortField('adj_cpri')
              setSortOrder('desc')
            }}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'all'
                ? 'bg-[#101F43] text-white shadow-xs'
                : 'bg-white border border-[#E5E7EB] text-slate-700 hover:bg-[#F5F7FA]'
            }`}
          >
            <Layers className={`w-3.5 h-3.5 ${activeTab === 'all' ? 'text-[#EC008C]' : 'text-slate-400'}`} />
            <span>All Evaluated Players</span>
            <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
              activeTab === 'all' ? 'bg-[#EC008C] text-white' : 'bg-slate-100 text-slate-600'
            }`}>
              {mainLeaderboard.length + contenders.length}
            </span>
          </button>

          <button
            onClick={() => {
              setActiveTab('official_phase8')
              setSortField('rank')
              setSortOrder('asc')
            }}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'official_phase8'
                ? 'bg-[#101F43] text-white shadow-xs'
                : 'bg-white border border-[#E5E7EB] text-slate-700 hover:bg-[#F5F7FA]'
            }`}
          >
            <ShieldCheck className={`w-3.5 h-3.5 ${activeTab === 'official_phase8' ? 'text-[#EC008C]' : 'text-slate-400'}`} />
            <span>Frozen Phase 8 Top 10</span>
            <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
              activeTab === 'official_phase8' ? 'bg-[#EC008C] text-white' : 'bg-slate-100 text-slate-600'
            }`}>
              10
            </span>
          </button>
        </div>
      )}

      {/* Controls Bar: Search, Filters & Counters */}
      <div className="bg-white border border-[#E5E7EB] rounded-lg p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Search Input */}
          <div className="relative min-w-[200px] max-w-xs flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by player name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 bg-[#F5F7FA] border border-[#E5E7EB] rounded-md text-xs text-[#101F43] focus:outline-none focus:border-[#EC008C]"
            />
          </div>

          {/* Min Pressure Balls Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-semibold text-slate-500">Min Balls:</span>
            <select
              value={minBallsFilter}
              onChange={(e) => setMinBallsFilter(Number(e.target.value))}
              className="text-xs bg-[#F5F7FA] border border-[#E5E7EB] rounded-md px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:border-[#EC008C]"
            >
              <option value={0}>All Qualifying (150+)</option>
              <option value={250}>250+ Balls (Moderate+)</option>
              <option value={400}>400+ Balls (Main Only)</option>
              <option value={600}>600+ Balls (Elite Only)</option>
            </select>
          </div>

          {/* Evidence Tier Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-semibold text-slate-500">Evidence Tier:</span>
            <select
              value={evidenceTierFilter}
              onChange={(e) => setEvidenceTierFilter(e.target.value)}
              className="text-xs bg-[#F5F7FA] border border-[#E5E7EB] rounded-md px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:border-[#EC008C]"
            >
              <option value="ALL">All Tiers</option>
              <option value="Elite Evidence">Elite Evidence (600+)</option>
              <option value="Strong Evidence">Strong Evidence (400–599)</option>
              <option value="Moderate Evidence">Moderate Evidence (250–399)</option>
              <option value="Limited Evidence">Limited Evidence (150–249)</option>
            </select>
          </div>

          {/* Format Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-semibold text-slate-500">Format:</span>
            <select
              value={formatFilter}
              onChange={(e) => setFormatFilter(e.target.value)}
              className="text-xs bg-[#F5F7FA] border border-[#E5E7EB] rounded-md px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:border-[#EC008C]"
            >
              <option value="ALL">All Formats</option>
              <option value="Dual-Format">Dual-Format</option>
              <option value="IPL-Only">IPL-Only</option>
              <option value="T20I-Only">T20I-Only</option>
            </select>
          </div>
        </div>

        <div className="text-xs font-mono text-slate-500 shrink-0">
          Showing <strong>{filteredAndSortedPlayers.length}</strong> players
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label={`Loading ${isOfficial ? 'High-Volume' : mode.toUpperCase()} ${role} rankings...`} />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchData} />
      ) : (
        /* Leaderboard Table */
        <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            {isActiveMode || activeTab === 'active' ? (
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-[#064E3B] text-white border-b border-emerald-900">
                    <th className="py-3 px-3 w-14 cursor-pointer hover:bg-white/10 transition-colors" onClick={() => handleSort('rank')}>
                      <div className="flex items-center gap-1">
                        <span>Rank</span>
                        <ArrowUpDown className="w-3 h-3 text-emerald-200" />
                      </div>
                    </th>
                    <th className="py-3 px-3 w-20">
                      <span>90% CI</span>
                    </th>
                    <th className="py-3 px-3 min-w-[160px]">Player</th>
                    <th className="py-3 px-3 w-36">Evidence Tier</th>
                    <th className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors" onClick={() => handleSort('raw_cpri')}>
                      <div className="flex items-center justify-end gap-1">
                        <span className="text-amber-300 font-extrabold">Raw CPRI</span>
                        <ArrowUpDown className="w-3 h-3 text-amber-300" />
                      </div>
                    </th>
                    <th className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors" onClick={() => handleSort('balls')}>
                      <div className="flex items-center justify-end gap-1">
                        <span>Pressure Balls</span>
                        <ArrowUpDown className="w-3 h-3 text-emerald-200" />
                      </div>
                    </th>
                    <th className="py-3 px-3 text-center w-28">Last Played in Data</th>
                    <th className="py-3 px-3 text-center w-28">Phase 8 Rank</th>
                    <th className="py-3 px-3 text-center w-28">Status</th>
                    <th className="py-3 px-3 text-right w-20">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E7EB]">
                  {filteredAndSortedPlayers.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="py-12 text-center text-slate-400">
                        No active players match the selected filters.
                      </td>
                    </tr>
                  ) : (
                    filteredAndSortedPlayers.map((p: any, idx: number) => {
                      const displayRank = p.rank || idx + 1
                      const isTop3 = displayRank <= 3
                      const pBalls = p.pressure_deliveries || 0
                      const pScore = p.cpri_score || 0
                      const tierName = p.evidence_tier || 'Moderate Evidence'
                      const ciDisplay = p.rank_ci_90 || '—'

                      return (
                        <tr key={p.player_id || p.player_name} className="hover:bg-emerald-50/40 transition-colors">
                          <td className="py-3 px-3 font-mono font-bold">
                            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                              displayRank === 1
                                ? 'bg-[#EC008C] text-white font-extrabold shadow-xs'
                                : isTop3
                                ? 'bg-[#101F43] text-white font-bold'
                                : 'bg-[#F5F7FA] text-[#101F43] border border-[#E5E7EB]'
                            }`}>
                              {displayRank}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-mono text-slate-600 font-semibold text-[11px]">
                            {ciDisplay}
                          </td>
                          <td className="py-3 px-3">
                            <Link
                              to={`/players/IPL/${role}/${encodeURIComponent(p.player_name)}`}
                              className="font-bold text-[#101F43] hover:text-[#EC008C] transition-colors block text-xs"
                            >
                              {p.player_name}
                            </Link>
                          </td>
                          <td className="py-3 px-3">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded whitespace-nowrap ${getEvidenceTierBadge(p.evidence_tier)}`}>
                              {tierName}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right font-black text-sm text-[#EC008C] font-mono">
                            {formatScore(pScore)}
                          </td>
                          <td className="py-3 px-3 text-right font-mono text-slate-700 font-semibold text-xs">
                            {pBalls}
                          </td>
                          <td className="py-3 px-3 text-center font-mono text-xs text-emerald-800 font-semibold">
                            {p.last_played || '—'}
                          </td>
                          <td className="py-3 px-3 text-center font-mono text-xs text-slate-700 font-bold">
                            {p.official_rank ? `#${p.official_rank}` : '—'}
                          </td>
                          <td className="py-3 px-3 text-center">
                            {p.in_official_top10 ? (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 border border-blue-200">
                                Official Top 10
                              </span>
                            ) : (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                                New Entrant
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-3 text-right">
                            <Link
                              to={`/players/IPL/${role}/${encodeURIComponent(p.player_name)}`}
                              className="text-[11px] font-bold text-[#EC008C] hover:text-[#101F43] inline-flex items-center gap-1"
                            >
                              <span>Dossier</span>
                              <ArrowRight className="w-3 h-3" />
                            </Link>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            ) : (
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-[#101F43] text-white border-b border-[#E5E7EB]">
                  {/* Rank Header */}
                  <th
                    className="py-3 px-3 cursor-pointer hover:bg-white/10 transition-colors w-14"
                    onClick={() => handleSort('rank')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Rank</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>

                  {/* 90% Rank CI Header */}
                  {isOfficial && (
                    <th className="py-3 px-3 w-20">
                      <span>90% CI</span>
                    </th>
                  )}

                  {/* Player Header */}
                  <th className="py-3 px-3 min-w-[160px]">Player</th>

                  {/* Format Evidence Header */}
                  {isOfficial && <th className="py-3 px-3 w-28">Format Evidence</th>}

                  {/* Evidence Tier Header */}
                  {isOfficial && <th className="py-3 px-3 w-32">Evidence Tier</th>}

                  {/* Adjusted CPRI Header */}
                  <th
                    className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors"
                    onClick={() => handleSort('adj_cpri')}
                  >
                    <div className="flex items-center justify-end gap-1">
                      <span className="text-amber-300 font-extrabold">Adj. CPRI</span>
                      <span className="text-[9px] bg-amber-500 text-white px-1 py-0.5 rounded font-bold">Exploratory</span>
                      <ArrowUpDown className="w-3 h-3 text-amber-300" />
                    </div>
                  </th>

                  {/* Raw CPRI Header (Official Phase 8 Score) */}
                  <th
                    className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors"
                    onClick={() => handleSort('raw_cpri')}
                  >
                    <div className="flex items-center justify-end gap-1">
                      <span className="text-[#EC008C] font-extrabold">Raw CPRI</span>
                      <span className="text-[9px] bg-[#EC008C] text-white px-1 py-0.5 rounded font-bold">Official</span>
                      <ArrowUpDown className="w-3 h-3 text-[#EC008C]" />
                    </div>
                  </th>

                  {/* PPR Score Header */}
                  {isOfficial && (
                    <th
                      className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors"
                      onClick={() => handleSort('ppr')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        <span>PPR</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                  )}

                  {/* Clutch Success % Header */}
                  {isOfficial && (
                    <th
                      className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors"
                      onClick={() => handleSort('success_rate')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        <span>Success %</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                  )}

                  {/* Pressure Deliveries Header */}
                  <th
                    className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors"
                    onClick={() => handleSort('balls')}
                  >
                    <div className="flex items-center justify-end gap-1">
                      <span>Pressure Balls</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>

                  {/* Action Header */}
                  <th className="py-3 px-3 text-right w-20">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E7EB]">
                {filteredAndSortedPlayers.length === 0 ? (
                  <tr>
                    <td colSpan={11} className="py-12 text-center text-slate-400">
                      No players match the selected filters.
                    </td>
                  </tr>
                ) : (
                  filteredAndSortedPlayers.map((p: any, idx: number) => {
                    const displayRank = activeTab === 'official_phase8'
                      ? p.official_rank
                      : (activeTab === 'main' ? p.adjusted_rank : (p.adjusted_rank || p.official_rank)) || idx + 1
                    const isTop3 = displayRank <= 3
                    const pScope = isOfficial ? (p.competition_evidence === 'T20I-Only' ? 'T20I' : 'IPL') : mode.toUpperCase()
                    const pBalls = p.pressure_stats?.pressure_deliveries || p.pressure_deliveries || 0
                    const tierName = p.evidence_tier || 'Limited Evidence'
                    const ciDisplay = activeTab === 'official_phase8'
                      ? (p.rank_uncertainty?.ci_display || '—')
                      : (p.adjusted_rank_ci || p.rank_uncertainty?.ci_display || '—')

                    return (
                      <tr
                        key={p.player_id || p.player_name}
                        className="hover:bg-[#F5F7FA] transition-colors"
                      >
                        {/* Rank */}
                        <td className="py-3 px-3 font-mono font-bold">
                          <div className="flex items-center gap-1.5">
                            <span
                              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                                displayRank === 1
                                  ? 'bg-[#EC008C] text-white font-extrabold shadow-xs'
                                  : isTop3
                                  ? 'bg-[#101F43] text-white font-bold'
                                  : 'bg-[#F5F7FA] text-[#101F43] border border-[#E5E7EB]'
                              }`}
                            >
                              {displayRank}
                            </span>
                          </div>
                        </td>

                        {/* 90% Rank CI */}
                        {isOfficial && (
                          <td className="py-3 px-3 font-mono text-slate-600 font-semibold text-[11px]">
                            {ciDisplay}
                          </td>
                        )}

                        {/* Player Name & Tactical Tag */}
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <Link
                              to={`/players/${pScope}/${role}/${encodeURIComponent(p.player_name)}`}
                              className="font-bold text-[#101F43] hover:text-[#EC008C] transition-colors block text-xs"
                            >
                              {p.player_name}
                            </Link>
                          </div>
                          {p.tactical_classification && (
                            <span className="text-[10px] text-slate-400 font-medium">
                              {p.tactical_classification}
                            </span>
                          )}
                        </td>

                        {/* Format Evidence */}
                        {isOfficial && (
                          <td className="py-3 px-3">
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 whitespace-nowrap">
                              {p.competition_evidence || 'Dual-Format'}
                            </span>
                          </td>
                        )}

                        {/* Evidence Tier */}
                        {isOfficial && (
                          <td className="py-3 px-3">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded whitespace-nowrap ${getEvidenceTierBadge(p.evidence_tier)}`}>
                              {tierName}
                            </span>
                          </td>
                        )}

                        {/* Adjusted CPRI Score (Highlighted) */}
                        <td className="py-3 px-3 text-right font-black text-sm text-[#EC008C] font-mono">
                          {formatScore(p.adjusted_cpri ?? p.cpri_score)}
                        </td>

                        {/* Raw CPRI Score (Reference) */}
                        <td className="py-3 px-3 text-right font-mono text-slate-600 text-xs">
                          {formatScore(p.cpri_score)}
                        </td>

                        {/* PPR Score */}
                        {isOfficial && (
                          <td className="py-3 px-3 text-right font-mono font-semibold text-slate-800 text-xs">
                            {formatScore(p.ppr_score ?? 50.0)}
                          </td>
                        )}

                        {/* Clutch Success % */}
                        {isOfficial && (
                          <td className="py-3 px-3 text-right font-mono text-slate-700 text-xs">
                            {p.success_rate_pct != null ? `${Number(p.success_rate_pct).toFixed(1)}%` : '—'}
                          </td>
                        )}

                        {/* Pressure Deliveries */}
                        <td className="py-3 px-3 text-right font-mono text-slate-700 font-semibold text-xs">
                          {pBalls}
                        </td>

                        {/* Action Link */}
                        <td className="py-3 px-3 text-right">
                          <Link
                            to={`/players/${pScope}/${role}/${encodeURIComponent(p.player_name)}`}
                            className="text-[11px] font-bold text-[#EC008C] hover:text-[#101F43] inline-flex items-center gap-1"
                          >
                            <span>Dossier</span>
                            <ArrowRight className="w-3 h-3" />
                          </Link>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
