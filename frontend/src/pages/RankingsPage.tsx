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
  Info
} from 'lucide-react'
import { getCohortPlayers } from '../api/playerApi'
import { getOfficialRoleRankings } from '../api/officialApi'
import type { PlayerSummaryItem } from '../types/player'
import type { OfficialPlayerItem } from '../types/official'
import type { Role } from '../types/common'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorState } from '../components/common/ErrorState'
import { formatScore } from '../utils/formatters'
import { getErrorMessage } from '../api/client'

type SortField = 'rank' | 'cpri' | 'pi' | 'pa' | 'cc' | 'rc' | 'balls'
type SortOrder = 'asc' | 'desc'

export const RankingsPage: React.FC = () => {
  const { scopeParam } = useParams<{ scopeParam?: string }>()
  const navigate = useNavigate()

  // Mode: 'official' by default, or 'ipl', 't20i'
  const mode = scopeParam?.toLowerCase() === 'ipl' ? 'ipl' : scopeParam?.toLowerCase() === 't20i' ? 't20i' : 'official'
  const isOfficial = mode === 'official'

  const [role, setRole] = useState<Role>('Batter')
  
  // Data stores
  const [officialTop10, setOfficialTop10] = useState<OfficialPlayerItem[]>([])
  const [officialCandidates, setOfficialCandidates] = useState<OfficialPlayerItem[]>([])
  const [cohortPlayers, setCohortPlayers] = useState<PlayerSummaryItem[]>([])
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCandidates, setShowCandidates] = useState(false)

  // Filtering & Sorting
  const [search, setSearch] = useState('')
  const [sortField, setSortField] = useState<SortField>('rank')
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc')

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      if (isOfficial) {
        const data = await getOfficialRoleRankings(role)
        setOfficialTop10(data.official_top10)
        setOfficialCandidates(data.candidates || [])
      } else {
        const data = await getCohortPlayers(mode.toUpperCase() as any, role, { limit: 100 })
        setCohortPlayers(data.players)
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [mode, role])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder(field === 'rank' ? 'asc' : 'desc')
    }
  }

  const baseList: any[] = isOfficial
    ? (showCandidates ? [...officialTop10, ...officialCandidates] : officialTop10)
    : cohortPlayers

  const filteredAndSortedPlayers = useMemo(() => {
    return baseList
      .filter((p) => {
        const matchesName = p.player_name.toLowerCase().includes(search.toLowerCase())
        return matchesName
      })
      .sort((a, b) => {
        let valA = 0
        let valB = 0
        switch (sortField) {
          case 'rank':
            valA = a.official_rank || 999
            valB = b.official_rank || 999
            break
          case 'cpri':
            valA = a.cpri_score
            valB = b.cpri_score
            break
          case 'pi':
            valA = a.components.pressure_impact
            valB = b.components.pressure_impact
            break
          case 'pa':
            valA = a.components.pressure_adaptability
            valB = b.components.pressure_adaptability
            break
          case 'cc':
            valA = a.components.clutch_consistency
            valB = b.components.clutch_consistency
            break
          case 'rc':
            valA = a.components.reliability_confidence
            valB = b.components.reliability_confidence
            break
          case 'balls':
            valA = a.pressure_stats?.pressure_deliveries || a.pressure_deliveries
            valB = b.pressure_stats?.pressure_deliveries || b.pressure_deliveries
            break
        }
        return sortOrder === 'desc' ? valB - valA : valA - valB
      })
  }, [baseList, search, sortField, sortOrder])

  const topThree = filteredAndSortedPlayers.slice(0, 3)

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-[#E5E7EB] rounded-lg p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-widest text-[#EC008C] font-bold mb-1">
            {isOfficial ? 'SupeRR Selector Season 2 • Official Competition Submission' : `${mode.toUpperCase()} Contextual League Slice`}
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-[#101F43] tracking-tight">
            {isOfficial ? `Official Top 10 ${role}s` : `${mode.toUpperCase()} ${role} Rankings`}
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            {isOfficial
              ? 'Authoritative frozen competition rankings evaluating high-pressure execution (PI ≥ 50.0) across all qualifying IPL and T20I match deliveries.'
              : `Contextual single-tournament slice isolating balls faced/bowled within ${mode.toUpperCase()} only.`}
          </p>
        </div>

        {/* Navigation Switchers */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Format / Mode Switcher */}
          <div className="inline-flex rounded-md p-1 bg-[#F5F7FA] border border-[#E5E7EB] text-xs font-semibold">
            <button
              onClick={() => navigate('/rankings')}
              className={`px-3 py-1.5 rounded transition-colors flex items-center gap-1.5 ${
                isOfficial
                  ? 'bg-[#101F43] text-white shadow-xs'
                  : 'text-slate-600 hover:text-[#101F43]'
              }`}
            >
              <Crown className="w-3.5 h-3.5 text-[#EC008C]" />
              <span>Official Unified</span>
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

      {/* Secondary View Warning Banner */}
      {!isOfficial && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg shadow-xs flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-900 leading-relaxed">
            <strong className="font-bold">Contextual League Notice: </strong>
            This view reflects single-tournament metrics within {mode.toUpperCase()}. 
            The <strong>Official Competition Ranking</strong> submitted for SupeRR Selector Season 2 is the{' '}
            <button
              onClick={() => navigate('/rankings')}
              className="font-bold underline text-[#101F43] hover:text-[#EC008C]"
            >
              Unified Phase 8 Ranking
            </button>.
          </div>
        </div>
      )}

      {/* Controls Bar: Search & Toggle */}
      <div className="bg-white border border-[#E5E7EB] rounded-lg p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="relative flex-1 min-w-[240px] max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by player name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-[#F5F7FA] border border-[#E5E7EB] rounded-md text-xs text-[#101F43] focus:outline-none focus:border-[#EC008C]"
          />
        </div>

        <div className="flex items-center gap-3">
          {isOfficial && (
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={showCandidates}
                onChange={(e) => setShowCandidates(e.target.checked)}
                className="rounded border-[#E5E7EB] text-[#EC008C] focus:ring-[#EC008C]"
              />
              <span>Include Contender Candidates (Ranks 11–25)</span>
            </label>
          )}

          <div className="text-xs font-mono text-slate-500">
            Showing {filteredAndSortedPlayers.length} players
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label={`Loading ${isOfficial ? 'Official' : mode.toUpperCase()} ${role} rankings...`} />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchData} />
      ) : (
        /* Leaderboard Table */
        <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-[#101F43] text-white border-b border-[#E5E7EB]">
                  <th
                    className="py-3 px-3 cursor-pointer hover:bg-white/10 transition-colors"
                    onClick={() => handleSort('rank')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Rank</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>
                  {isOfficial && <th className="py-3 px-3">90% CI</th>}
                  <th className="py-3 px-3">Player</th>
                  {isOfficial && <th className="py-3 px-3">Format Evidence</th>}
                  <th className="py-3 px-3">Confidence Tier</th>
                  <th
                    className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors"
                    onClick={() => handleSort('cpri')}
                  >
                    <div className="flex items-center justify-end gap-1">
                      <span>CPRI Score</span>
                      <ArrowUpDown className="w-3 h-3 text-[#EC008C]" />
                    </div>
                  </th>
                  <th
                    className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors"
                    onClick={() => handleSort('pi')}
                  >
                    PI (40%)
                  </th>
                  <th
                    className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors"
                    onClick={() => handleSort('pa')}
                  >
                    PA (25%)
                  </th>
                  <th
                    className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors"
                    onClick={() => handleSort('cc')}
                  >
                    CC (20%)
                  </th>
                  <th
                    className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors"
                    onClick={() => handleSort('rc')}
                  >
                    RC (15%)
                  </th>
                  <th
                    className="py-3 px-3 text-right cursor-pointer hover:bg-white/10 transition-colors"
                    onClick={() => handleSort('balls')}
                  >
                    Pressure Balls
                  </th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E7EB]">
                {filteredAndSortedPlayers.map((p, idx) => {
                  const rankNum = p.official_rank || idx + 1
                  const isTop3 = rankNum <= 3
                  const confTier = p.confidence_tier || 'High Confidence'
                  const isExploratory = confTier === 'Exploratory'
                  const pScope = isOfficial ? (p.competition_evidence === 'T20I-Only' ? 'T20I' : 'IPL') : mode.toUpperCase()

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
                              rankNum === 1
                                ? 'bg-[#EC008C] text-white font-extrabold'
                                : isTop3
                                ? 'bg-[#101F43] text-white'
                                : 'bg-[#F5F7FA] text-[#101F43] border border-[#E5E7EB]'
                            }`}
                          >
                            {rankNum}
                          </span>
                        </div>
                      </td>

                      {/* 90% Rank CI */}
                      {isOfficial && (
                        <td className="py-3 px-3 font-mono text-slate-600 font-semibold">
                          {p.rank_uncertainty?.ci_display || '—'}
                        </td>
                      )}

                      {/* Player Name */}
                      <td className="py-3 px-3">
                        <Link
                          to={`/players/${pScope}/${role}/${encodeURIComponent(p.player_name)}`}
                          className="font-bold text-[#101F43] hover:text-[#EC008C] transition-colors"
                        >
                          {p.player_name}
                        </Link>
                      </td>

                      {/* Format Evidence */}
                      {isOfficial && (
                        <td className="py-3 px-3">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                            {p.competition_evidence || 'Dual-Format'}
                          </span>
                        </td>
                      )}

                      {/* Confidence Tier */}
                      <td className="py-3 px-3">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            isExploratory
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {confTier}
                        </span>
                      </td>

                      {/* CPRI Score */}
                      <td className="py-3 px-3 text-right font-black text-sm text-[#EC008C] font-mono">
                        {formatScore(p.cpri_score)}
                      </td>

                      {/* PI */}
                      <td className="py-3 px-3 text-right font-mono text-slate-700">
                        {formatScore(p.components.pressure_impact)}
                      </td>

                      {/* PA */}
                      <td className="py-3 px-3 text-right font-mono text-slate-700">
                        {formatScore(p.components.pressure_adaptability)}
                      </td>

                      {/* CC */}
                      <td className="py-3 px-3 text-right font-mono text-slate-700">
                        {formatScore(p.components.clutch_consistency)}
                      </td>

                      {/* RC */}
                      <td className="py-3 px-3 text-right font-mono text-slate-700">
                        {formatScore(p.components.reliability_confidence)}
                      </td>

                      {/* Pressure Balls */}
                      <td className="py-3 px-3 text-right font-mono text-slate-600">
                        {p.pressure_stats?.pressure_deliveries || p.pressure_deliveries}
                      </td>

                      {/* Action */}
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
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
