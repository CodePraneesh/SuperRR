import React, { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Trophy, Search, Filter, ArrowUpDown, ArrowRight, ShieldCheck, Crown, Flame, Target } from 'lucide-react'
import { getCohortPlayers } from '../api/playerApi'
import type { PlayerSummaryItem } from '../types/player'
import type { Scope, Role } from '../types/common'
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

  // Default scope from URL: /rankings/ipl -> 'IPL', /rankings/t20i -> 'T20I'
  const scope: Scope = scopeParam?.toLowerCase() === 't20i' ? 'T20I' : 'IPL'
  const [role, setRole] = useState<Role>('Batter')
  const [players, setPlayers] = useState<PlayerSummaryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filtering & Sorting
  const [search, setSearch] = useState('')
  const [filterOfficial, setFilterOfficial] = useState(false)
  const [sortField, setSortField] = useState<SortField>('cpri')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  const fetchCohort = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getCohortPlayers(scope, role, { limit: 100 })
      setPlayers(data.players)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCohort()
  }, [scope, role])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('desc')
    }
  }

  const filteredAndSortedPlayers = useMemo(() => {
    return players
      .filter((p) => {
        const matchesName = p.player_name.toLowerCase().includes(search.toLowerCase())
        const matchesOfficial = filterOfficial ? p.is_official_top10 : true
        return matchesName && matchesOfficial
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
            valA = a.pressure_deliveries
            valB = b.pressure_deliveries
            break
        }
        return sortOrder === 'desc' ? valB - valA : valA - valB
      })
  }, [players, search, filterOfficial, sortField, sortOrder])

  // Top 3 official leaders for spotlight cards
  const topThree = useMemo(() => {
    return [...players]
      .filter((p) => p.is_official_top10 && p.official_rank)
      .sort((a, b) => (a.official_rank || 999) - (b.official_rank || 999))
      .slice(0, 3)
  }, [players])

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#182752]">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-medium text-pink-400 mb-1">
            <Crown className="w-4 h-4 text-amber-400" />
            <span>Official CPRI Leaderboard</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400">{scope} Championship Cohort</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>{scope}</span>
            <span className="text-pink-500 font-black">CPRI</span>
            <span>Rankings</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Composite Pressure Resilience Index rankings frozen under CPRI-v1.0.0 methodology
          </p>
        </div>

        {/* Scope and Role Tabs */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Format Switcher */}
          <div className="inline-flex rounded-lg p-1 bg-[#0c132c] border border-[#182752] text-xs font-semibold shadow-inner">
            <button
              onClick={() => navigate('/rankings/ipl')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                scope === 'IPL'
                  ? 'bg-gradient-to-r from-blue-700 to-indigo-700 text-white shadow-md shadow-blue-900/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              IPL Cohort
            </button>
            <button
              onClick={() => navigate('/rankings/t20i')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                scope === 'T20I'
                  ? 'bg-gradient-to-r from-blue-700 to-indigo-700 text-white shadow-md shadow-blue-900/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              T20I Cohort
            </button>
          </div>

          {/* Role Switcher */}
          <div className="inline-flex rounded-lg p-1 bg-[#0c132c] border border-[#182752] text-xs font-semibold shadow-inner">
            <button
              onClick={() => setRole('Batter')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                role === 'Batter'
                  ? 'bg-gradient-to-r from-pink-600 to-rose-600 text-white shadow-md shadow-pink-600/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Batters
            </button>
            <button
              onClick={() => setRole('Bowler')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                role === 'Bowler'
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Bowlers
            </button>
          </div>
        </div>
      </div>

      {/* Top 3 Podium Cards */}
      {!loading && topThree.length >= 3 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {topThree.map((player) => {
            const isRank1 = player.official_rank === 1
            const isRank2 = player.official_rank === 2
            const borderColor = isRank1
              ? 'border-amber-400/50 shadow-lg shadow-amber-500/10'
              : isRank2
              ? 'border-pink-500/40 shadow-lg shadow-pink-500/10'
              : 'border-blue-500/40 shadow-lg shadow-blue-500/10'
            const badgeBg = isRank1
              ? 'bg-amber-400/20 text-amber-300 border-amber-400/40'
              : isRank2
              ? 'bg-pink-500/20 text-pink-300 border-pink-500/40'
              : 'bg-blue-500/20 text-blue-300 border-blue-500/40'

            return (
              <Card
                key={player.player_name}
                variant="interactive"
                className={`p-4 relative overflow-hidden ${borderColor}`}
                onClick={() => navigate(`/players/${scope}/${role}/${encodeURIComponent(player.player_name)}`)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold border ${badgeBg}`}>
                      {isRank1 && <Crown className="w-3 h-3 inline mr-1 text-amber-400" />}
                      #{player.official_rank}
                    </span>
                    <Badge variant="official" size="sm">Official Top 10</Badge>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">
                    {player.pressure_deliveries} Pressure Balls
                  </span>
                </div>
                <div className="text-base font-bold text-white mb-1 group-hover:text-pink-400 transition-colors">
                  {player.player_name}
                </div>
                <div className="flex items-baseline justify-between pt-2 border-t border-[#182752]/60">
                  <span className="text-xs text-slate-400">CPRI Score</span>
                  <span className="text-xl font-mono font-black text-pink-400">
                    {formatScore(player.cpri_score)}
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-1 pt-2 mt-2 border-t border-[#182752]/40 text-center font-mono text-[10px]">
                  <div>
                    <div className="text-slate-500">PI</div>
                    <div className="text-slate-200 font-semibold">{formatScore(player.components.pressure_impact, 0)}</div>
                  </div>
                  <div>
                    <div className="text-slate-500">PA</div>
                    <div className="text-slate-200 font-semibold">{formatScore(player.components.pressure_adaptability, 0)}</div>
                  </div>
                  <div>
                    <div className="text-slate-500">CC</div>
                    <div className="text-slate-200 font-semibold">{formatScore(player.components.clutch_consistency, 0)}</div>
                  </div>
                  <div>
                    <div className="text-slate-500">RC</div>
                    <div className="text-slate-200 font-semibold">{formatScore(player.components.reliability_confidence, 0)}</div>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* Filter and Search Controls */}
      <Card variant="subtle" className="p-4 flex flex-col md:flex-row items-center justify-between gap-4 border-[#182752]">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder={`Filter ${scope} ${role}s by name...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-[#070b18] border border-[#182752] text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-pink-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto justify-end">
          <button
            onClick={() => setFilterOfficial(!filterOfficial)}
            className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition-colors ${
              filterOfficial
                ? 'bg-pink-500/20 text-pink-300 border-pink-500/40 shadow-sm shadow-pink-500/20'
                : 'bg-[#070b18] text-slate-400 border-[#182752] hover:text-white'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Official Top 10 Only
          </button>
          <span className="text-xs text-slate-400 font-mono">
            Showing <strong className="text-pink-400">{filteredAndSortedPlayers.length}</strong> players
          </span>
        </div>
      </Card>

      {/* Main Table */}
      {loading ? (
        <LoadingSpinner label={`Loading ${scope} ${role} rankings...`} />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchCohort} />
      ) : (
        <Card variant="default" className="overflow-hidden p-0 border-[#182752]">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#070b18] text-slate-400 font-mono uppercase text-[10px] tracking-wider border-b border-[#182752]">
                <tr>
                  <th
                    className="py-3.5 px-4 cursor-pointer hover:text-white select-none"
                    onClick={() => handleSort('rank')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Rank</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-500" />
                    </div>
                  </th>
                  <th className="py-3.5 px-4">Player Details</th>
                  <th
                    className="py-3.5 px-4 cursor-pointer hover:text-pink-400 select-none text-pink-400"
                    onClick={() => handleSort('cpri')}
                  >
                    <div className="flex items-center gap-1">
                      <span>CPRI Score</span>
                      <ArrowUpDown className="w-3 h-3 text-pink-400" />
                    </div>
                  </th>
                  <th
                    className="py-3.5 px-4 cursor-pointer hover:text-white select-none"
                    onClick={() => handleSort('pi')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Pressure Impact (40%)</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-500" />
                    </div>
                  </th>
                  <th
                    className="py-3.5 px-4 cursor-pointer hover:text-white select-none"
                    onClick={() => handleSort('pa')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Adaptability (25%)</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-500" />
                    </div>
                  </th>
                  <th
                    className="py-3.5 px-4 cursor-pointer hover:text-white select-none"
                    onClick={() => handleSort('cc')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Consistency (20%)</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-500" />
                    </div>
                  </th>
                  <th
                    className="py-3.5 px-4 cursor-pointer hover:text-white select-none"
                    onClick={() => handleSort('rc')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Reliability (15%)</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-500" />
                    </div>
                  </th>
                  <th className="py-3.5 px-4">Confidence</th>
                  <th className="py-3.5 px-4 text-right">Dossier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#182752]/60 font-sans">
                {filteredAndSortedPlayers.map((p, idx) => (
                  <tr
                    key={p.player_name}
                    className="hover:bg-blue-950/20 transition-colors cursor-pointer group"
                    onClick={() => navigate(`/players/${scope}/${role}/${encodeURIComponent(p.player_name)}`)}
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-300">
                      {p.official_rank ? (
                        <span
                          className={`w-6 h-6 rounded-md flex items-center justify-center text-xs ${
                            p.official_rank === 1
                              ? 'bg-amber-400/20 text-amber-300 border border-amber-400/40 font-black'
                              : p.official_rank === 2
                              ? 'bg-pink-500/20 text-pink-300 border border-pink-500/40 font-bold'
                              : p.official_rank === 3
                              ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40 font-bold'
                              : 'bg-[#182752]/50 text-slate-400'
                          }`}
                        >
                          #{p.official_rank}
                        </span>
                      ) : (
                        <span className="text-slate-600 pl-1 font-mono text-xs">#{idx + 1}*</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white group-hover:text-pink-400 transition-colors text-sm">
                          {p.player_name}
                        </span>
                        <Badge variant={p.is_official_top10 ? 'official' : 'provisional'} size="sm">
                          {p.ranking_tier}
                        </Badge>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        {p.pressure_deliveries} Pressure Deliveries • {role === 'Batter' ? `${p.strike_rate || '—'} SR` : `${p.economy_rate || '—'} Econ`}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-pink-400 text-sm">
                      {formatScore(p.cpri_score)}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {formatScore(p.components.pressure_impact, 1)}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {formatScore(p.components.pressure_adaptability, 1)}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {formatScore(p.components.clutch_consistency, 1)}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {formatScore(p.components.reliability_confidence, 1)}
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge
                        variant={
                          p.confidence_tier.includes('High')
                            ? 'high'
                            : p.confidence_tier.includes('Medium')
                            ? 'medium'
                            : 'low'
                        }
                        size="sm"
                      >
                        {p.confidence_tier}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-pink-400 group-hover:text-pink-300">
                        View Dossier <ArrowRight className="w-3.5 h-3.5" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
