import React, { useState, useEffect } from 'react'
import {
  GitCompare,
  ArrowRight,
  ShieldCheck,
  TrendingUp,
  Activity,
  Zap,
  Crown,
} from 'lucide-react'
import { getCohortPlayers } from '../api/playerApi'
import { comparePlayers } from '../api/comparisonApi'
import { getOfficialPlayer } from '../api/officialApi'
import type { PlayerSummaryItem } from '../types/player'
import type { PlayerComparisonResponse } from '../types/scouting'
import type { OfficialPlayerItem } from '../types/official'
import type { Scope, Role } from '../types/common'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorState } from '../components/common/ErrorState'
import { MarkdownView } from '../components/common/MarkdownView'
import { CPRIComponentRadar } from '../components/charts/CPRIComponentRadar'
import { formatScore, formatDelta } from '../utils/formatters'
import { getErrorMessage } from '../api/client'

export const PlayerComparisonPage: React.FC = () => {
  const [scope, setScope] = useState<Scope>('IPL')
  const [role, setRole] = useState<Role>('Batter')
  const [availablePlayers, setAvailablePlayers] = useState<PlayerSummaryItem[]>([])
  const [loadingPlayers, setLoadingPlayers] = useState(false)

  // Player selections
  const [playerA, setPlayerA] = useState<string>('')
  const [playerB, setPlayerB] = useState<string>('')

  // Comparison results
  const [comparison, setComparison] = useState<PlayerComparisonResponse | null>(null)
  const [officialA, setOfficialA] = useState<OfficialPlayerItem | null>(null)
  const [officialB, setOfficialB] = useState<OfficialPlayerItem | null>(null)
  const [loadingComparison, setLoadingComparison] = useState(false)
  const [comparisonError, setComparisonError] = useState<string | null>(null)

  // Load cohort players on scope or role change
  useEffect(() => {
    let mounted = true
    setLoadingPlayers(true)
    setComparison(null)
    setComparisonError(null)

    getCohortPlayers(scope, role, { limit: 100 })
      .then((data) => {
        if (mounted) {
          setAvailablePlayers(data.players)
          if (data.players.length >= 2) {
            setPlayerA(data.players[0].player_name)
            setPlayerB(data.players[1].player_name)
          } else if (data.players.length === 1) {
            setPlayerA(data.players[0].player_name)
            setPlayerB(data.players[0].player_name)
          }
        }
      })
      .catch((err) => {
        if (mounted) setComparisonError(getErrorMessage(err))
      })
      .finally(() => {
        if (mounted) setLoadingPlayers(false)
      })

    return () => {
      mounted = false
    }
  }, [scope, role])

  const handleRunComparison = async () => {
    if (!playerA || !playerB) {
      setComparisonError('Please select both players for comparison.')
      return
    }
    if (playerA === playerB) {
      setComparisonError('Please select two different players to compare.')
      return
    }

    setLoadingComparison(true)
    setComparisonError(null)
    try {
      const [res, offA, offB] = await Promise.all([
        comparePlayers({
          scope,
          role,
          player_a: playerA,
          player_b: playerB,
        }),
        getOfficialPlayer(playerA).catch(() => null),
        getOfficialPlayer(playerB).catch(() => null),
      ])
      setComparison(res)
      setOfficialA(offA)
      setOfficialB(offB)
    } catch (err) {
      setComparisonError(getErrorMessage(err))
    } finally {
      setLoadingComparison(false)
    }
  }

  // Find summary objects for radar charts
  const itemA = availablePlayers.find((p) => p.player_name === playerA)
  const itemB = availablePlayers.find((p) => p.player_name === playerB)
  const deltas = comparison?.structured_comparison.deltas_a_minus_b

  return (
    <div className="space-y-8">
      {/* Page Title */}
      <div>
        <div className="flex items-center gap-2 text-xs font-mono font-medium text-[#EC008C] mb-1">
          <GitCompare className="w-4 h-4 text-[#EC008C]" />
          <span>Role-Adjusted Head-to-Head</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-[#0F172A] flex items-center gap-2">
          <span>Player Comparison</span>
          <span className="text-pink-600 font-black">Matrix</span>
        </h1>
        <p className="text-xs text-[#64748B] mt-0.5">
          Evaluate two players side-by-side across CPRI components, situational phase execution, and tactical deltas.
        </p>
      </div>

      {/* Selector Controls Card */}
      <Card variant="subtle" className="p-6 border-slate-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          {/* Scope Selector */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-[#64748B] mb-1.5 font-bold">
              Competition Scope
            </label>
            <div className="grid grid-cols-2 gap-1 p-1 rounded-lg bg-[#070b18] border border-[#182752] text-xs font-semibold">
              <button
                onClick={() => setScope('IPL')}
                aria-label="Select IPL scope"
                className={`py-1.5 rounded-md transition-all focus:outline-none focus:ring-2 focus:ring-[#EC008C] ${
                  scope === 'IPL'
                    ? 'bg-gradient-to-r from-blue-700 to-indigo-700 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                IPL
              </button>
              <button
                onClick={() => setScope('T20I')}
                aria-label="Select T20I scope"
                className={`py-1.5 rounded-md transition-all focus:outline-none focus:ring-2 focus:ring-[#EC008C] ${
                  scope === 'T20I'
                    ? 'bg-gradient-to-r from-blue-700 to-indigo-700 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                T20I
              </button>
            </div>
          </div>

          {/* Role Selector */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-bold">
              Role
            </label>
            <div className="grid grid-cols-2 gap-1 p-1 rounded-lg bg-[#070b18] border border-[#182752] text-xs font-semibold">
              <button
                onClick={() => setRole('Batter')}
                aria-label="Select Batter role"
                className={`py-1.5 rounded-md transition-all focus:outline-none focus:ring-2 focus:ring-[#EC008C] ${
                  role === 'Batter'
                    ? 'bg-gradient-to-r from-pink-600 to-rose-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Batter
              </button>
              <button
                onClick={() => setRole('Bowler')}
                aria-label="Select Bowler role"
                className={`py-1.5 rounded-md transition-all focus:outline-none focus:ring-2 focus:ring-[#EC008C] ${
                  role === 'Bowler'
                    ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Bowler
              </button>
            </div>
          </div>

          {/* Player A Dropdown */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-pink-400 mb-1.5 font-bold">
              Player A (Royal Pink)
            </label>
            <select
              value={playerA}
              onChange={(e) => setPlayerA(e.target.value)}
              disabled={loadingPlayers}
              aria-label="Select Player A for comparison"
              className="w-full px-3 py-2 rounded-lg bg-[#070b18] border border-pink-500/40 text-xs text-white focus:outline-none focus:ring-2 focus:ring-[#EC008C] font-medium"
            >
              {availablePlayers.map((p) => (
                <option key={p.player_name} value={p.player_name}>
                  {p.player_name} (CPRI {formatScore(p.cpri_score)})
                </option>
              ))}
            </select>
          </div>

          {/* Player B Dropdown */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-blue-400 mb-1.5 font-bold">
              Player B (Royal Blue)
            </label>
            <select
              value={playerB}
              onChange={(e) => setPlayerB(e.target.value)}
              disabled={loadingPlayers}
              aria-label="Select Player B for comparison"
              className="w-full px-3 py-2 rounded-lg bg-[#070b18] border border-blue-500/40 text-xs text-white focus:outline-none focus:ring-2 focus:ring-[#EC008C] font-medium"
            >
              {availablePlayers.map((p) => (
                <option key={p.player_name} value={p.player_name}>
                  {p.player_name} (CPRI {formatScore(p.cpri_score)})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Action Button */}
        <div className="mt-5 flex justify-end">
          <button
            onClick={handleRunComparison}
            disabled={loadingComparison || loadingPlayers || !playerA || !playerB}
            aria-label="Run side-by-side player comparison"
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-pink-600 via-rose-600 to-blue-600 hover:from-pink-500 hover:to-blue-500 text-xs font-bold text-white shadow-lg shadow-pink-600/20 transition-all disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#EC008C]"
          >
            <GitCompare className="w-4 h-4" />
            {loadingComparison ? 'Computing Comparative Matrix...' : 'Compare Players'}
          </button>
        </div>
      </Card>

      {comparisonError && <ErrorState message={comparisonError} />}

      {loadingComparison && <LoadingSpinner label={`Generating comparison: ${playerA} vs ${playerB}...`} />}

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-6">
          {/* Side-by-Side CPRI Head-to-Head Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Player A Card */}
            <Card variant="royal" className="border-pink-300 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-pink-50 text-[#EC008C] border border-pink-200 font-bold">
                  Player A
                </span>
                <span className="text-xs font-mono text-[#64748B]">
                  {itemA?.official_rank ? `#${itemA.official_rank} in ${scope}` : 'Provisional'}
                </span>
              </div>
              <h2 className="text-2xl font-bold text-[#0F172A] mb-2">{comparison.player_a}</h2>
              <div className="text-4xl font-black font-mono text-[#EC008C] mb-4">
                {formatScore(itemA?.cpri_score)}
                <span className="text-xs text-[#64748B] font-normal font-sans ml-2">CPRI</span>
              </div>

              <div className="space-y-2 pt-3 border-t border-slate-200 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Pressure Impact (40%)</span>
                  <span className="text-[#0F172A] font-semibold">{formatScore(itemA?.components.pressure_impact, 1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Adaptability (25%)</span>
                  <span className="text-[#0F172A] font-semibold">{formatScore(itemA?.components.pressure_adaptability, 1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Consistency (20%)</span>
                  <span className="text-[#0F172A] font-semibold">{formatScore(itemA?.components.clutch_consistency, 1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Reliability (15%)</span>
                  <span className="text-[#0F172A] font-semibold">{formatScore(itemA?.components.reliability_confidence, 1)}</span>
                </div>
              </div>
            </Card>

            {/* Net Delta Matrix */}
            <Card variant="default" className="flex flex-col justify-between text-center p-6 border-slate-200 bg-slate-50">
              <div>
                <div className="text-xs font-mono uppercase tracking-wider text-[#64748B] mb-1 font-bold">
                  Net Variance (A minus B)
                </div>
                <div className="text-3xl font-black font-mono text-[#0F172A] mb-1">
                  {formatDelta(deltas?.cpri_delta, 2)}
                </div>
                <div className="text-xs text-[#64748B] mb-4 font-medium">
                  {deltas && deltas.cpri_delta > 0
                    ? `${comparison.player_a} leads by +${deltas.cpri_delta} CPRI`
                    : deltas && deltas.cpri_delta < 0
                    ? `${comparison.player_b} leads by +${Math.abs(deltas.cpri_delta)} CPRI`
                    : 'Equal CPRI rating'}
                </div>
              </div>

              <div className="space-y-2.5 text-xs font-mono text-left bg-white p-3 rounded-xl border border-slate-200">
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Δ Impact:</span>
                  <span className={deltas && deltas.pressure_impact_delta >= 0 ? 'text-[#EC008C] font-bold' : 'text-blue-700 font-bold'}>
                    {formatDelta(deltas?.pressure_impact_delta, 1)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Δ Adaptability:</span>
                  <span className={deltas && deltas.adaptability_delta >= 0 ? 'text-[#EC008C] font-bold' : 'text-blue-700 font-bold'}>
                    {formatDelta(deltas?.adaptability_delta, 1)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Δ Consistency:</span>
                  <span className={deltas && deltas.consistency_delta >= 0 ? 'text-[#EC008C] font-bold' : 'text-blue-700 font-bold'}>
                    {formatDelta(deltas?.consistency_delta, 1)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Δ Reliability:</span>
                  <span className={deltas && deltas.reliability_delta >= 0 ? 'text-[#EC008C] font-bold' : 'text-blue-700 font-bold'}>
                    {formatDelta(deltas?.reliability_delta, 1)}
                  </span>
                </div>
              </div>

              <div className="text-[10px] text-[#64748B] font-mono mt-3">
                Strict CPRI v1.0.0 Component Decomposition
              </div>
            </Card>

            {/* Player B Card */}
            <Card variant="royal" className="border-blue-300 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-bold">
                  Player B
                </span>
                <span className="text-xs font-mono text-[#64748B]">
                  {itemB?.official_rank ? `#${itemB.official_rank} in ${scope}` : 'Provisional'}
                </span>
              </div>
              <h2 className="text-2xl font-bold text-[#0F172A] mb-2">{comparison.player_b}</h2>
              <div className="text-4xl font-black font-mono text-blue-700 mb-4">
                {formatScore(itemB?.cpri_score)}
                <span className="text-xs text-[#64748B] font-normal font-sans ml-2">CPRI</span>
              </div>

              <div className="space-y-2 pt-3 border-t border-slate-200 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Pressure Impact (40%)</span>
                  <span className="text-[#0F172A] font-semibold">{formatScore(itemB?.components.pressure_impact, 1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Adaptability (25%)</span>
                  <span className="text-[#0F172A] font-semibold">{formatScore(itemB?.components.pressure_adaptability, 1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Consistency (20%)</span>
                  <span className="text-[#0F172A] font-semibold">{formatScore(itemB?.components.clutch_consistency, 1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Reliability (15%)</span>
                  <span className="text-[#0F172A] font-semibold">{formatScore(itemB?.components.reliability_confidence, 1)}</span>
                </div>
              </div>
            </Card>
          </div>

          {/* Detailed Side-by-Side Component Matrix Table */}
          <Card variant="default" className="border-slate-200 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-[#0F172A] flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-[#EC008C]" />
                  Direct Component & Standing Comparison Matrix
                </h3>
                <p className="text-xs text-[#64748B]">
                  Comprehensive audit across all official CPRI components, ranks, sample sizes, and last match dates.
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse" aria-label="Two-Player Component Comparison Table">
                <thead>
                  <tr className="bg-slate-100 text-[#0F172A] border-b border-slate-200">
                    <th className="py-2.5 px-3 font-semibold">Component / Metric</th>
                    <th className="py-2.5 px-3 text-[#EC008C] font-bold">{comparison.player_a}</th>
                    <th className="py-2.5 px-3 text-center text-[#64748B]">Variance (Δ)</th>
                    <th className="py-2.5 px-3 text-blue-700 font-bold">{comparison.player_b}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 text-[#334155] font-mono">
                  {/* CPRI */}
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-semibold text-[#0F172A]">Composite CPRI Score</td>
                    <td className="py-2.5 px-3 font-bold text-[#EC008C] text-sm">{formatScore(itemA?.cpri_score)}</td>
                    <td className="py-2.5 px-3 text-center font-bold text-[#0F172A]">{formatDelta(deltas?.cpri_delta, 2)}</td>
                    <td className="py-2.5 px-3 font-bold text-blue-700 text-sm">{formatScore(itemB?.cpri_score)}</td>
                  </tr>

                  {/* Official Rank */}
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-semibold text-[#0F172A]">Official Competition Rank</td>
                    <td className="py-2.5 px-3">
                      {officialA?.is_official_top10 ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-pink-50 text-[#EC008C] border border-pink-200">
                          #{officialA.official_rank} Official Top 10
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-[#64748B] border border-slate-200">
                          not in Top 10
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center text-[#64748B] text-[11px]">—</td>
                    <td className="py-2.5 px-3">
                      {officialB?.is_official_top10 ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200">
                          #{officialB.official_rank} Official Top 10
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-[#64748B] border border-slate-200">
                          not in Top 10
                        </span>
                      )}
                    </td>
                  </tr>

                  {/* 90% Rank Interval */}
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-semibold text-[#0F172A]">90% Bootstrap Rank CI</td>
                    <td className="py-2.5 px-3 text-amber-900 font-semibold">
                      {officialA?.rank_uncertainty ? `[${officialA.rank_uncertainty.rank_p5}, ${officialA.rank_uncertainty.rank_p95}]` : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-center text-[#64748B] text-[11px]">—</td>
                    <td className="py-2.5 px-3 text-amber-900 font-semibold">
                      {officialB?.rank_uncertainty ? `[${officialB.rank_uncertainty.rank_p5}, ${officialB.rank_uncertainty.rank_p95}]` : '—'}
                    </td>
                  </tr>

                  {/* score_pressure_impact */}
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-semibold text-[#0F172A]">
                      score_pressure_impact <span className="text-[#64748B] font-normal">(40%)</span>
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">{formatScore(itemA?.components.pressure_impact, 2)}</td>
                    <td className="py-2.5 px-3 text-center font-bold text-[#0F172A]">{formatDelta(deltas?.pressure_impact_delta, 2)}</td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">{formatScore(itemB?.components.pressure_impact, 2)}</td>
                  </tr>

                  {/* score_adaptability */}
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-semibold text-[#0F172A]">
                      score_adaptability <span className="text-[#64748B] font-normal">(25%)</span>
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">{formatScore(itemA?.components.pressure_adaptability, 2)}</td>
                    <td className="py-2.5 px-3 text-center font-bold text-[#0F172A]">{formatDelta(deltas?.adaptability_delta, 2)}</td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">{formatScore(itemB?.components.pressure_adaptability, 2)}</td>
                  </tr>

                  {/* score_consistency */}
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-semibold text-[#0F172A]">
                      score_consistency <span className="text-[#64748B] font-normal">(20%)</span>
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">{formatScore(itemA?.components.clutch_consistency, 2)}</td>
                    <td className="py-2.5 px-3 text-center font-bold text-[#0F172A]">{formatDelta(deltas?.consistency_delta, 2)}</td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">{formatScore(itemB?.components.clutch_consistency, 2)}</td>
                  </tr>

                  {/* score_reliability */}
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-semibold text-[#0F172A]">
                      score_reliability <span className="text-[#64748B] font-normal">(15%)</span>
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">{formatScore(itemA?.components.reliability_confidence, 2)}</td>
                    <td className="py-2.5 px-3 text-center font-bold text-[#0F172A]">{formatDelta(deltas?.reliability_delta, 2)}</td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">{formatScore(itemB?.components.reliability_confidence, 2)}</td>
                  </tr>

                  {/* Pressure Balls */}
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-semibold text-[#0F172A]">Pressure Deliveries</td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">
                      {officialA?.pressure_stats?.pressure_deliveries ?? itemA?.pressure_deliveries ?? 0}
                    </td>
                    <td className="py-2.5 px-3 text-center text-[#64748B] text-[11px]">—</td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">
                      {officialB?.pressure_stats?.pressure_deliveries ?? itemB?.pressure_deliveries ?? 0}
                    </td>
                  </tr>

                  {/* Pressure Matches */}
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-semibold text-[#0F172A]">Pressure Matches</td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">
                      {officialA?.pressure_stats?.pressure_matches ?? '—'}
                    </td>
                    <td className="py-2.5 px-3 text-center text-[#64748B] text-[11px]">—</td>
                    <td className="py-2.5 px-3 font-semibold text-[#334155]">
                      {officialB?.pressure_stats?.pressure_matches ?? '—'}
                    </td>
                  </tr>

                  {/* Last Played Date */}
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-semibold text-[#0F172A]">Last Played in Data</td>
                    <td className="py-2.5 px-3 text-emerald-800 font-semibold">
                      {officialA?.last_played || '—'}
                    </td>
                    <td className="py-2.5 px-3 text-center text-[#64748B] text-[11px]">—</td>
                    <td className="py-2.5 px-3 text-emerald-800 font-semibold">
                      {officialB?.last_played || '—'}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>

          {/* Dual Overlay Radar Visualization */}
          {itemA && itemB && (
            <Card variant="default" className="border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-bold text-[#0F172A] flex items-center gap-2">
                    <Activity className="w-4 h-4 text-pink-600" />
                    Overlay Radar Comparison
                  </h3>
                  <p className="text-xs text-[#64748B]">
                    Direct comparison of 4 CPRI dimensions: <span className="text-[#EC008C] font-semibold">{comparison.player_a}</span> (Royal Pink) vs <span className="text-blue-700 font-semibold">{comparison.player_b}</span> (Royal Blue)
                  </p>
                </div>
              </div>
              <CPRIComponentRadar
                componentsA={itemA.components}
                labelA={comparison.player_a}
                componentsB={itemB.components}
                labelB={comparison.player_b}
                height={300}
              />
            </Card>
          )}

          {/* AI Comparison Analysis / Verdict */}
          <Card variant="default" className="p-6 border-slate-200">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-200 text-xs font-mono">
              <div className="flex items-center gap-2 text-[#EC008C] font-bold">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>AI Comparative Verdict & Tactical Breakdown</span>
              </div>
              <Badge variant={comparison.verified ? 'official' : 'warning'} size="sm">
                {comparison.tier_used}
              </Badge>
            </div>
            <MarkdownView content={comparison.ai_analysis} />
          </Card>
        </div>
      )}
    </div>
  )
}
