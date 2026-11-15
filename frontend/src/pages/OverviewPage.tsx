import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Trophy,
  ArrowRight,
  TrendingUp,
  Activity,
  ShieldCheck,
  Target,
} from 'lucide-react'
import { getCohortPlayers } from '../api/playerApi'
import type { PlayerSummaryItem } from '../types/player'
import type { Scope, Role } from '../types/common'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorState } from '../components/common/ErrorState'
import { TopRankingsBarChart } from '../components/charts/TopRankingsBarChart'
import { CPRIComponentRadar } from '../components/charts/CPRIComponentRadar'
import { formatScore } from '../utils/formatters'
import { getErrorMessage } from '../api/client'

export const OverviewPage: React.FC = () => {
  const [scope, setScope] = useState<Scope>('IPL')
  const [role, setRole] = useState<Role>('Batter')
  const [players, setPlayers] = useState<PlayerSummaryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const loadData = async (s: Scope, r: Role) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getCohortPlayers(s, r, { limit: 50 })
      setPlayers(data.players)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData(scope, role)
  }, [scope, role])

  const champion = players[0]
  const topThree = players.slice(0, 3)

  return (
    <div className="space-y-8">
      {/* Official Editorial Hero Banner */}
      <div className="bg-white border border-[#E5E7EB] rounded-lg p-6 md:p-8 shadow-xs">
        <div className="max-w-4xl">
          <div className="text-xs uppercase tracking-widest text-[#EC008C] font-bold mb-2">
            SupeRR Selector Season 2 • Official Competition Analytics
          </div>

          <h1 className="text-3xl md:text-4xl font-extrabold text-[#101F43] tracking-tight mb-1">
            Supe<span className="text-[#EC008C]">RR</span> Intelligence
          </h1>

          <div className="text-base md:text-lg font-bold text-[#101F43] mb-4">
            Beyond Performance. <span className="text-[#EC008C]">Measuring Pressure.</span>
          </div>

          <p className="text-sm text-slate-600 leading-relaxed mb-6 max-w-3xl">
            Conventional cricket statistics collapse when match leverage peaks. SupeRR Intelligence isolates and quantifies player execution strictly when match outcome volatility spikes (Pressure Index ≥ 50.0). By synthesizing ball-by-ball Win Probability Added (WPA) residuals with Bayesian reliability shrinkage, the platform produces the frozen Clutch Performance &amp; Reliability Index (CPRI v1.0.0).
          </p>

          {/* Clean Editorial Switchers */}
          <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-[#E5E7EB]">
            {/* Scope Switcher */}
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mr-1">Competition:</span>
              <div className="inline-flex rounded-md p-1 bg-[#F5F7FA] border border-[#E5E7EB] text-xs font-semibold">
                <button
                  onClick={() => setScope('IPL')}
                  className={`px-3.5 py-1.5 rounded transition-colors ${
                    scope === 'IPL'
                      ? 'bg-[#101F43] text-white shadow-xs'
                      : 'text-slate-600 hover:text-[#101F43]'
                  }`}
                >
                  IPL
                </button>
                <button
                  onClick={() => setScope('T20I')}
                  className={`px-3.5 py-1.5 rounded transition-colors ${
                    scope === 'T20I'
                      ? 'bg-[#101F43] text-white shadow-xs'
                      : 'text-slate-600 hover:text-[#101F43]'
                  }`}
                >
                  T20I
                </button>
              </div>
            </div>

            {/* Role Switcher */}
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mr-1">Cohort:</span>
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

            {/* Methodology status tag */}
            <div className="ml-auto hidden md:flex items-center gap-1.5 text-xs text-slate-500 font-mono">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>CPRI-v1.0.0 Frozen Baseline</span>
            </div>
          </div>
        </div>
      </div>

      {/* The 4 CPRI Pillars (Editorial Grid) */}
      <div>
        <div className="text-xs font-bold uppercase tracking-wider text-[#EC008C] mb-2">
          Methodological Architecture
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs">
            <div className="text-[11px] font-bold uppercase tracking-wider text-[#EC008C] mb-1">
              Pillar 1 • 40% Weight
            </div>
            <div className="text-base font-bold text-[#101F43] mb-1">Pressure Impact</div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Expected run and dismissal residuals on high-pressure deliveries ($PI \ge 50.0$) against pre-ball baselines.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs">
            <div className="text-[11px] font-bold uppercase tracking-wider text-[#EC008C] mb-1">
              Pillar 2 • 25% Weight
            </div>
            <div className="text-base font-bold text-[#101F43] mb-1">Pressure Adaptability</div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Performance rate delta comparing high-pressure execution directly against low-pressure baseline rates.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs">
            <div className="text-[11px] font-bold uppercase tracking-wider text-[#EC008C] mb-1">
              Pillar 3 • 20% Weight
            </div>
            <div className="text-base font-bold text-[#101F43] mb-1">Clutch Consistency</div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Match-to-match stability and positive match ratio, penalizing volatile boom-or-bust performers.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs">
            <div className="text-[11px] font-bold uppercase tracking-wider text-[#EC008C] mb-1">
              Pillar 4 • 15% Weight
            </div>
            <div className="text-base font-bold text-[#101F43] mb-1">Reliability Confidence</div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Empirical Bayes shrinkage based on pressure ball sample depth ($\ge 100$ balls) and match dispersion.
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label={`Retrieving ${scope} ${role} rankings...`} />
      ) : error ? (
        <ErrorState message={error} onRetry={() => loadData(scope, role)} />
      ) : (
        <>
          {/* Top 3 Pressure Performers Spotlight */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-xs font-bold uppercase tracking-wider text-[#EC008C] mb-0.5">
                  Official Leaderboard Spotlight
                </div>
                <h2 className="text-lg font-bold text-[#101F43]">
                  {scope} {role} Leaders (Official Top 3)
                </h2>
              </div>
              <Link
                to={`/rankings/${scope.toLowerCase()}`}
                className="text-xs font-bold text-[#EC008C] hover:text-[#C70076] flex items-center gap-1 transition-colors"
              >
                View Full Cohort <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {topThree.map((player, idx) => (
                <div
                  key={player.player_name}
                  onClick={() => navigate(`/players/${scope}/${role}/${encodeURIComponent(player.player_name)}`)}
                  className="bg-white border border-[#E5E7EB] rounded-lg p-5 shadow-xs hover:border-[#EC008C]/40 transition-all cursor-pointer group"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-7 h-7 rounded flex items-center justify-center font-bold text-xs ${
                          idx === 0
                            ? 'bg-[#FDF2F8] text-[#EC008C] border border-[#FBCFE8]'
                            : 'bg-[#F1F5F9] text-[#101F43] border border-[#E2E8F0]'
                        }`}
                      >
                        #{player.official_rank || idx + 1}
                      </span>
                      <Badge variant={player.is_official_top10 ? 'official' : 'provisional'} size="sm">
                        {player.ranking_tier}
                      </Badge>
                    </div>
                    <Badge variant="neutral" size="sm">
                      {player.confidence_tier}
                    </Badge>
                  </div>

                  <h3 className="text-lg font-bold text-[#101F43] group-hover:text-[#EC008C] transition-colors mb-1 truncate">
                    {player.player_name}
                  </h3>
                  <div className="text-xs text-slate-500 mb-4 flex items-center gap-2 font-mono">
                    <span>{player.pressure_deliveries} Pressure Balls</span>
                    <span>•</span>
                    <span>
                      {role === 'Batter' ? `${player.strike_rate || '—'} SR` : `${player.economy_rate || '—'} Econ`}
                    </span>
                  </div>

                  <div className="pt-3 border-t border-[#E5E7EB] flex items-baseline justify-between">
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">
                        CPRI Score
                      </div>
                      <div className="text-2xl font-black font-sans text-[#101F43]">
                        {formatScore(player.cpri_score)}
                      </div>
                    </div>
                    <div className="text-right text-[11px] font-mono text-slate-500">
                      <div>PI: <span className="text-[#101F43] font-bold">{formatScore(player.components.pressure_impact, 1)}</span></div>
                      <div>CC: <span className="text-[#101F43] font-bold">{formatScore(player.components.clutch_consistency, 1)}</span></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Visualizations Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top 10 Chart */}
            <div className="bg-white border border-[#E5E7EB] rounded-lg p-5 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-[#EC008C] mb-0.5">
                    Benchmark Distribution
                  </div>
                  <h3 className="text-sm font-bold text-[#101F43] flex items-center gap-1.5">
                    <TrendingUp className="w-4 h-4 text-[#101F43]" />
                    Top 10 CPRI Ranking Curve
                  </h3>
                </div>
                <span className="text-xs font-mono text-slate-500">Scale: [60-100]</span>
              </div>
              <TopRankingsBarChart
                players={players}
                onSelectPlayer={(p) => navigate(`/players/${scope}/${role}/${encodeURIComponent(p.player_name)}`)}
                height={280}
              />
            </div>

            {/* Radar Comparison for #1 */}
            {champion && (
              <div className="bg-white border border-[#E5E7EB] rounded-lg p-5 shadow-xs">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-wider text-[#EC008C] mb-0.5">
                      Component Decomposition
                    </div>
                    <h3 className="text-sm font-bold text-[#101F43] flex items-center gap-1.5">
                      <Activity className="w-4 h-4 text-[#101F43]" />
                      #{champion.official_rank || 1} {champion.player_name}
                    </h3>
                  </div>
                  <span className="text-xs font-bold text-[#101F43] font-sans">
                    CPRI {formatScore(champion.cpri_score)}
                  </span>
                </div>
                <CPRIComponentRadar componentsA={champion.components} labelA={champion.player_name} height={260} />
              </div>
            )}
          </div>

          {/* Master Cohort Table */}
          <div className="bg-white border border-[#E5E7EB] rounded-lg overflow-hidden shadow-xs">
            <div className="p-4 border-b border-[#E5E7EB] flex items-center justify-between bg-white">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-[#EC008C] mb-0.5">
                  Complete Evaluation Roster
                </div>
                <h3 className="text-sm font-bold text-[#101F43]">
                  {scope} {role} CPRI Master Table
                </h3>
              </div>
              <Link
                to={`/rankings/${scope.toLowerCase()}`}
                className="text-xs font-bold text-[#EC008C] hover:text-[#C70076] flex items-center gap-1"
              >
                Detailed Rankings <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#F5F7FA] text-[#101F43] font-sans font-bold uppercase text-[10px] tracking-wider border-b border-[#E5E7EB]">
                  <tr>
                    <th className="py-3 px-4">Rank</th>
                    <th className="py-3 px-4">Player</th>
                    <th className="py-3 px-4">CPRI Score</th>
                    <th className="py-3 px-4">Pressure Impact (40%)</th>
                    <th className="py-3 px-4">Adaptability (25%)</th>
                    <th className="py-3 px-4">Consistency (20%)</th>
                    <th className="py-3 px-4">Reliability (15%)</th>
                    <th className="py-3 px-4">Confidence</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E7EB] font-sans">
                  {players.slice(0, 10).map((p, idx) => (
                    <tr
                      key={p.player_name}
                      className="hover:bg-[#F8FAFC] transition-colors cursor-pointer group"
                      onClick={() => navigate(`/players/${scope}/${role}/${encodeURIComponent(p.player_name)}`)}
                    >
                      <td className="py-3 px-4 font-mono font-bold text-slate-700">
                        {p.official_rank === 1 ? (
                          <span className="w-6 h-6 rounded bg-[#FDF2F8] text-[#EC008C] border border-[#FBCFE8] flex items-center justify-center font-bold">
                            #1
                          </span>
                        ) : p.official_rank ? (
                          <span className="w-6 h-6 rounded bg-[#F1F5F9] text-[#101F43] border border-[#E2E8F0] flex items-center justify-center font-bold">
                            #{p.official_rank}
                          </span>
                        ) : (
                          <span className="text-slate-400 pl-1 font-mono text-xs">#{idx + 1}*</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-bold text-[#101F43] group-hover:text-[#EC008C] transition-colors text-sm">
                          {p.player_name}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono">
                          {p.pressure_deliveries} balls under pressure
                        </div>
                      </td>
                      <td className="py-3 px-4 font-sans font-bold text-[#101F43] text-sm">
                        {formatScore(p.cpri_score)}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-700">
                        {formatScore(p.components.pressure_impact, 1)}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-700">
                        {formatScore(p.components.pressure_adaptability, 1)}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-700">
                        {formatScore(p.components.clutch_consistency, 1)}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-700">
                        {formatScore(p.components.reliability_confidence, 1)}
                      </td>
                      <td className="py-3 px-4">
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
                      <td className="py-3 px-4 text-right">
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#EC008C] group-hover:text-[#C70076]">
                          Inspect <ArrowRight className="w-3 h-3" />
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
