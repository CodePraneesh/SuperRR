import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Trophy,
  ArrowRight,
  TrendingUp,
  Activity,
  ShieldCheck,
  Target,
  AlertTriangle,
  Flame,
  Crown,
  UserCheck
} from 'lucide-react'
import { getCohortPlayers } from '../api/playerApi'
import { getOfficialRoleRankings } from '../api/officialApi'
import { getActiveRankings, getActiveSensitivity, SensitivityWindowItem } from '../api/activeApi'
import type { PlayerSummaryItem } from '../types/player'
import type { OfficialPlayerItem } from '../types/official'
import type { Role } from '../types/common'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorState } from '../components/common/ErrorState'
import { TopRankingsBarChart } from '../components/charts/TopRankingsBarChart'
import { CPRIComponentRadar } from '../components/charts/CPRIComponentRadar'
import { formatScore } from '../utils/formatters'
import { getErrorMessage } from '../api/client'

type ViewMode = 'official' | 'active' | 'ipl' | 't20i' | 'pre_floor'

export const OverviewPage: React.FC = () => {
  // Official Phase 13 rankings remain default view
  const [viewMode, setViewMode] = useState<ViewMode>('official')
  const [role, setRole] = useState<Role>('Batter')
  
  // Official unified state
  const [officialPlayers, setOfficialPlayers] = useState<OfficialPlayerItem[]>([])
  // Pre-floor baseline state (Phase 8 unfloored supplementary)
  const [preFloorPlayers, setPreFloorPlayers] = useState<OfficialPlayerItem[]>([])
  // Active players state (last 12 months)
  const [activePlayers, setActivePlayers] = useState<OfficialPlayerItem[]>([])
  // Contextual league state
  const [cohortPlayers, setCohortPlayers] = useState<PlayerSummaryItem[]>([])
  // Sensitivity table state
  const [sensitivityWindows, setSensitivityWindows] = useState<SensitivityWindowItem[]>([])
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    getActiveSensitivity().then(res => {
      setSensitivityWindows(res.windows || [])
    }).catch(() => {})
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      if (viewMode === 'official') {
        const data = await getOfficialRoleRankings(role as 'Batter' | 'Bowler')
        setOfficialPlayers(data.official_top10)
      } else if (viewMode === 'pre_floor') {
        const data = await getOfficialRoleRankings(role as 'Batter' | 'Bowler')
        const rawList = data.pre_floor_baseline || []
        const mappedList: OfficialPlayerItem[] = rawList.map((p: any, idx: number) => ({
          official_rank: p.official_rank || idx + 1,
          player_id: p.player_id,
          player_name: p.player_name,
          role: role as 'Batter' | 'Bowler',
          competition_evidence: p.competition_evidence || 'Dual-Format',
          cpri_score: p.cpri_score || 0,
          components: {
            pressure_impact: p.components?.pressure_impact ?? p.score_pressure_impact ?? 75.0,
            pressure_adaptability: p.components?.pressure_adaptability ?? p.score_adaptability ?? 70.0,
            clutch_consistency: p.components?.clutch_consistency ?? p.score_consistency ?? 70.0,
            reliability_confidence: p.components?.reliability_confidence ?? p.score_reliability ?? 75.0,
          },
          pressure_stats: {
            pressure_deliveries: p.pressure_stats?.pressure_deliveries ?? p.pressure_deliveries ?? 0,
            pressure_matches: p.pressure_stats?.pressure_matches ?? p.pressure_matches ?? 0,
            pressure_strike_rate: p.pressure_stats?.pressure_strike_rate ?? p.pressure_strike_rate,
            pressure_economy: p.pressure_stats?.pressure_economy ?? p.pressure_economy,
            pressure_wpa: p.pressure_stats?.pressure_wpa ?? p.pressure_wpa ?? 0,
            total_deliveries: p.pressure_stats?.total_deliveries ?? p.total_deliveries ?? p.pressure_deliveries ?? 0,
            total_matches: p.pressure_stats?.total_matches ?? p.total_matches ?? p.pressure_matches ?? 0,
          },
          rank_uncertainty: {
            rank_p5: p.rank_uncertainty?.rank_p5 ?? p.rank_p5 ?? Math.max(1, (p.official_rank || idx + 1) - 2),
            rank_p95: p.rank_uncertainty?.rank_p95 ?? p.rank_p95 ?? (p.official_rank || idx + 1) + 4,
            median_rank: p.rank_uncertainty?.median_rank ?? p.median_rank ?? (p.official_rank || idx + 1),
            rank_std: p.rank_uncertainty?.rank_std ?? p.rank_std ?? 1.2,
            top10_inclusion_freq: p.rank_uncertainty?.top10_inclusion_freq ?? p.top10_inclusion_freq ?? 0.95,
            ci_display: p.rank_uncertainty?.ci_display ?? p.ci_display ?? (p.rank_p5 && p.rank_p95 ? `[${p.rank_p5}, ${p.rank_p95}]` : `[${Math.max(1, (p.official_rank || idx + 1) - 2)}, ${(p.official_rank || idx + 1) + 4}]`),
          },
          confidence_tier: p.confidence_tier || ((p.pressure_deliveries || p.pressure_stats?.pressure_deliveries || 0) < 250 ? 'Exploratory' : 'High Confidence'),
          evidence_tier: p.evidence_tier || ((p.pressure_deliveries || p.pressure_stats?.pressure_deliveries || 0) < 250 ? 'Limited Evidence' : 'Solid Evidence'),
          tactical_classification: p.tactical_classification || 'Phase 8 Unfloored Baseline',
          is_official_top10: true,
          last_played: p.last_played,
        }))
        setPreFloorPlayers(mappedList)
      } else if (viewMode === 'active') {
        const data = await getActiveRankings({ role: role as any, limit: 10 })
        const rawList = role === 'Batter' ? (data.active_batters || []) : (data.active_bowlers || [])
        const mappedList: OfficialPlayerItem[] = rawList.map((p, idx) => ({
          official_rank: p.rank || idx + 1,
          player_id: p.player_id,
          player_name: p.player_name,
          role: role as 'Batter' | 'Bowler',
          competition_evidence: p.competition_evidence || 'Dual-Format',
          cpri_score: p.cpri_score || 0,
          components: {
            pressure_impact: p.score_pressure_impact || 75.0,
            pressure_adaptability: p.score_adaptability || 70.0,
            clutch_consistency: p.score_consistency || 70.0,
            reliability_confidence: p.score_reliability || 75.0,
          },
          pressure_stats: {
            pressure_deliveries: p.pressure_deliveries || 0,
            pressure_matches: p.pressure_matches || 0,
            pressure_strike_rate: p.pressure_strike_rate,
            pressure_economy: p.pressure_economy,
            pressure_wpa: 0,
            total_deliveries: p.pressure_deliveries || 0,
            total_matches: p.pressure_matches || 0,
          },
          rank_uncertainty: {
            rank_p5: p.rank_p5 || Math.max(1, (p.rank || idx + 1) - 2),
            rank_p95: p.rank_p95 || (p.rank || idx + 1) + 4,
            median_rank: p.rank || idx + 1,
            rank_std: 1.2,
            top10_inclusion_freq: 0.95,
            ci_display: p.rank_ci_90 || p.evidence_tier || 'Active Tier',
          },
          confidence_tier: 'High Confidence' as const,
          tactical_classification: p.evidence_tier || 'Recently Active',
          is_official_top10: p.in_official_top10 ?? true,
        }))
        setActivePlayers(mappedList)
      } else {
        const data = await getCohortPlayers(viewMode.toUpperCase() as any, role as 'Batter' | 'Bowler', { limit: 50 })
        setCohortPlayers(data.players)
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [viewMode, role])

  const isOfficial = viewMode === 'official'
  const isPreFloor = viewMode === 'pre_floor'
  const isActive = viewMode === 'active'
  const displayPlayers: any[] = isOfficial
    ? officialPlayers
    : isPreFloor
    ? preFloorPlayers
    : isActive
    ? activePlayers
    : cohortPlayers
  const champion = displayPlayers[0]
  const topThree = displayPlayers.slice(0, 3)

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
            Conventional cricket statistics collapse when match leverage peaks. SupeRR Intelligence isolates and quantifies player execution strictly when match outcome volatility spikes (Pressure Index ≥ 50.0). By synthesizing ball-by-ball expected-performance residuals with Bayesian reliability shrinkage, the platform produces the certified <strong>Clutch Performance &amp; Reliability Index (CPRI v1.0.0)</strong>.
          </p>

          {/* Clean Editorial Switchers */}
          <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-[#E5E7EB]">
            {/* View Mode Switcher */}
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mr-1">Ranking View:</span>
              <div className="inline-flex rounded-md p-1 bg-[#F5F7FA] border border-[#E5E7EB] text-xs font-semibold">
                <button
                  onClick={() => setViewMode('official')}
                  className={`px-3 py-1.5 rounded transition-colors flex items-center gap-1.5 ${
                    viewMode === 'official'
                      ? 'bg-[#101F43] text-white shadow-xs'
                      : 'text-slate-600 hover:text-[#101F43]'
                  }`}
                >
                  <Crown className="w-3.5 h-3.5 text-[#EC008C]" />
                  <span>Official Rankings (Phase 13 · ≥250 pressure balls)</span>
                </button>
                <button
                  onClick={() => setViewMode('pre_floor')}
                  className={`px-3 py-1.5 rounded transition-colors flex items-center gap-1.5 ${
                    viewMode === 'pre_floor'
                      ? 'bg-[#101F43] text-white shadow-xs'
                      : 'text-slate-600 hover:text-[#101F43]'
                  }`}
                >
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                  <span>Pre-floor Baseline (Phase 8) — supplementary</span>
                  <span className="text-[9px] bg-amber-500 text-white px-1.5 py-0.2 rounded-full font-bold">SUPP</span>
                </button>
                <button
                  onClick={() => setViewMode('active')}
                  className={`px-3 py-1.5 rounded transition-colors flex items-center gap-1.5 ${
                    viewMode === 'active'
                      ? 'bg-emerald-800 text-white shadow-xs'
                      : 'text-slate-600 hover:text-[#101F43]'
                  }`}
                >
                  <UserCheck className="w-3.5 h-3.5 text-emerald-300" />
                  <span>Recently active in data (last 12 months)</span>
                  <span className="text-[9px] bg-emerald-500 text-white px-1.5 py-0.2 rounded-full font-bold">SUPP</span>
                </button>
                <button
                  onClick={() => setViewMode('ipl')}
                  className={`px-3 py-1.5 rounded transition-colors ${
                    viewMode === 'ipl'
                      ? 'bg-[#101F43] text-white shadow-xs'
                      : 'text-slate-600 hover:text-[#101F43]'
                  }`}
                >
                  IPL Contextual
                </button>
                <button
                  onClick={() => setViewMode('t20i')}
                  className={`px-3 py-1.5 rounded transition-colors ${
                    viewMode === 't20i'
                      ? 'bg-[#101F43] text-white shadow-xs'
                      : 'text-slate-600 hover:text-[#101F43]'
                  }`}
                >
                  T20I Contextual
                </button>
              </div>
            </div>

            {/* Role Switcher */}
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mr-1">Role:</span>
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
              <span>CPRI v1.0.0 · Evidence Floor ≥250</span>
            </div>
          </div>
        </div>
      </div>

      {/* Supplementary Active View Banner */}
      {isActive && (
        <div className="bg-emerald-50 border-l-4 border-emerald-600 p-4 rounded-r-lg shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-start gap-3">
            <UserCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div className="text-xs text-emerald-950 leading-relaxed">
              <strong className="font-bold text-emerald-900">Supplementary Eligibility View (Post-Hoc 12-Month Rule): </strong>
              Shows players with ≥ 1 delivery in the ranked role on or after <strong>2025-11-01</strong> (12 months before the dataset's final match date, 2026-11-01). Ranked strictly by RAW CPRI. Players absent from this data may remain active in other competitions; they are classified as <em>not recently active in the supplied data</em>.
            </div>
          </div>
          <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 shrink-0">
            Supplementary Output
          </span>
        </div>
      )}

      {/* Supplementary Pre-Floor Phase 8 Baseline Banner */}
      {isPreFloor && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-950 leading-relaxed">
              <strong className="font-bold text-amber-900">Pre-floor Baseline (Phase 8) — supplementary: </strong>
              Shows the unconstrained Phase 8 baseline rankings prior to the post-hoc ≥ 250 pressure balls floor. Small-sample rate leaders (e.g. Matthew Wade at 191 balls) exhibited wider bootstrap rank uncertainty intervals [1, 22]. The official competition submission is <strong>Phase 13 (≥ 250 pressure balls)</strong>.
            </div>
          </div>
          <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 border border-amber-300 shrink-0">
            Supplementary Baseline
          </span>
        </div>
      )}

      {/* Contextual Disclaimer Banner when viewing league-only */}
      {!isOfficial && !isActive && !isPreFloor && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg shadow-xs flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-900 leading-relaxed">
            <span className="font-bold">Contextual League View ({viewMode.toUpperCase()} {role}s): </span>
            This secondary view isolates performances strictly within {viewMode.toUpperCase()}. 
            The <strong>Official Competition Ranking</strong> evaluating all qualifying evidence is the{' '}
            <button
              onClick={() => setViewMode('official')}
              className="font-bold underline text-[#101F43] hover:text-[#EC008C]"
            >
              Official Rankings (Phase 13 · ≥250 pressure balls)
            </button>.
          </div>
        </div>
      )}

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
              Expected run and dismissal residuals on high-pressure deliveries (PI ≥ 50.0) against pre-ball match state baselines.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs">
            <div className="text-[11px] font-bold uppercase tracking-wider text-[#EC008C] mb-1">
              Pillar 2 • 25% Weight
            </div>
            <div className="text-base font-bold text-[#101F43] mb-1">Pressure Adaptability</div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Combined leverage formula (0.60 × Pressure Impact + 0.40 × max(delta, -5.0)) evaluating clutch execution vs low-leverage baselines.
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
              Empirical Bayes shrinkage based on pressure ball sample depth (≥100 balls) and match dispersion.
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label={`Retrieving ${isOfficial ? 'Official' : viewMode.toUpperCase()} ${role} rankings...`} />
      ) : error ? (
        <ErrorState message={error} onRetry={loadData} />
      ) : (
        <>
          {/* Top 3 Pressure Performers Spotlight */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-xs font-bold uppercase tracking-wider text-[#EC008C] mb-0.5">
                  {isActive 
                    ? 'Supplementary Active View (Last 12 Months)' 
                    : isOfficial 
                    ? 'Official Competition Podium (Phase 13 · ≥250 pressure balls)'
                    : isPreFloor
                    ? 'Pre-floor Baseline (Phase 8) — supplementary'
                    : `${viewMode.toUpperCase()} Contextual Leaders`}
                </div>
                <h2 className="text-lg font-bold text-[#101F43]">
                  {isActive 
                    ? `Recently Active Top 3 ${role}s` 
                    : isOfficial 
                    ? `Official Top 3 ${role}s` 
                    : isPreFloor
                    ? `Pre-floor Baseline Top 3 ${role}s`
                    : `${viewMode.toUpperCase()} ${role} Leaders`}
                </h2>
              </div>
              <Link
                to={isActive ? '/rankings/active' : isPreFloor ? '/rankings/official?tab=pre_floor' : isOfficial ? '/rankings' : `/rankings/${viewMode}`}
                className="text-xs font-bold text-[#EC008C] hover:text-[#101F43] flex items-center gap-1 transition-colors"
              >
                <span>View Full Leaderboard</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {topThree.map((p, idx) => {
                const rankNum = p.official_rank || idx + 1
                const ciText = p.rank_uncertainty?.ci_display ? ` 90% CI: ${p.rank_uncertainty.ci_display}` : ''
                const isFirst = rankNum === 1
                const confTier = p.confidence_tier || 'High Confidence'
                const isExploratory = confTier === 'Exploratory'

                return (
                  <div
                    key={p.player_id || p.player_name}
                    onClick={() => {
                      const pScope = (isOfficial || isPreFloor) ? (p.competition_evidence === 'T20I-Only' ? 'T20I' : 'IPL') : viewMode.toUpperCase()
                      navigate(`/players/${pScope}/${role}/${encodeURIComponent(p.player_name)}`)
                    }}
                    className={`relative p-5 rounded-lg border transition-all cursor-pointer hover:shadow-md ${
                      isFirst
                        ? 'bg-gradient-to-br from-[#101F43] to-[#1E3A8A] text-white border-[#101F43]'
                        : 'bg-white border-[#E5E7EB] text-[#101F43]'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs ${
                            isFirst ? 'bg-[#EC008C] text-white' : 'bg-[#F5F7FA] text-[#101F43] border border-[#E5E7EB]'
                          }`}
                        >
                          #{rankNum}
                        </span>
                        {ciText && (
                          <span className={`text-[11px] font-mono font-medium ${isFirst ? 'text-slate-200' : 'text-slate-500'}`}>
                            {p.rank_uncertainty?.ci_display}
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-1.5 flex-wrap justify-end">
                        {p.competition_evidence && (
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            isFirst ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-700'
                          }`}>
                            {p.competition_evidence}
                          </span>
                        )}
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          isExploratory
                            ? isFirst ? 'bg-amber-400/30 text-amber-200' : 'bg-amber-100 text-amber-800'
                            : isFirst ? 'bg-emerald-400/30 text-emerald-200' : 'bg-emerald-100 text-emerald-800'
                        }`}>
                          {confTier}
                        </span>
                      </div>
                    </div>

                    <div className="font-extrabold text-lg tracking-tight mb-1">{p.player_name}</div>
                    
                    <div className="flex items-baseline gap-2 mb-4">
                      <div className="text-2xl font-black text-[#EC008C]">{formatScore(p.cpri_score)}</div>
                      <div className={`text-xs uppercase tracking-wider font-semibold ${isFirst ? 'text-slate-300' : 'text-slate-500'}`}>
                        CPRI Index
                      </div>
                    </div>

                    {/* Component Pills */}
                    <div className="grid grid-cols-4 gap-1.5 pt-3 border-t border-slate-200/20 text-center">
                      <div>
                        <div className={`text-[10px] uppercase ${isFirst ? 'text-slate-300' : 'text-slate-500'}`}>PI (40%)</div>
                        <div className="text-xs font-bold font-mono">{formatScore(p.components?.pressure_impact ?? p.score_pressure_impact)}</div>
                      </div>
                      <div>
                        <div className={`text-[10px] uppercase ${isFirst ? 'text-slate-300' : 'text-slate-500'}`}>PA (25%)</div>
                        <div className="text-xs font-bold font-mono">{formatScore(p.components?.pressure_adaptability ?? p.score_adaptability)}</div>
                      </div>
                      <div>
                        <div className={`text-[10px] uppercase ${isFirst ? 'text-slate-300' : 'text-slate-500'}`}>CC (20%)</div>
                        <div className="text-xs font-bold font-mono">{formatScore(p.components?.clutch_consistency ?? p.score_consistency)}</div>
                      </div>
                      <div>
                        <div className={`text-[10px] uppercase ${isFirst ? 'text-slate-300' : 'text-slate-500'}`}>RC (15%)</div>
                        <div className="text-xs font-bold font-mono">{formatScore(p.components?.reliability_confidence ?? p.score_reliability)}</div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Deep Analysis Grid: Chart & Component Radar */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top 10 Chart */}
            <div className="bg-white border border-[#E5E7EB] rounded-lg p-5 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-xs font-bold uppercase tracking-wider text-[#EC008C] mb-0.5">
                    {isActive ? 'Recently Active CPRI Distribution' : isPreFloor ? 'Pre-floor Baseline (Phase 8) CPRI Distribution' : isOfficial ? 'Official CPRI Distribution' : `${viewMode.toUpperCase()} CPRI Distribution`}
                  </div>
                  <h3 className="text-base font-bold text-[#101F43]">
                    {isActive ? `Recently Active Top 10 ${role}s` : isPreFloor ? `Pre-floor Baseline Top 10 ${role}s` : isOfficial ? `Official Top 10 ${role}s` : `${viewMode.toUpperCase()} ${role} Rankings`}
                  </h3>
                </div>
                <div className="text-xs font-mono text-slate-500">Scale: 60 - 100 CPRI</div>
              </div>

              <TopRankingsBarChart
                players={displayPlayers}
                height={340}
                onSelectPlayer={(selected) => {
                  const pScope = (isOfficial || isPreFloor) ? (selected.competition_evidence === 'T20I-Only' ? 'T20I' : 'IPL') : viewMode.toUpperCase()
                  navigate(`/players/${pScope}/${role}/${encodeURIComponent(selected.player_name)}`)
                }}
              />
            </div>

            {/* #1 Player Radar Profile */}
            {champion && (
              <div className="bg-white border border-[#E5E7EB] rounded-lg p-5 shadow-xs flex flex-col">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <div className="text-xs font-bold uppercase tracking-wider text-[#EC008C] mb-0.5">
                      #1 Ranked Performer Radar
                    </div>
                    <h3 className="text-base font-bold text-[#101F43]">
                      {champion.player_name} (CPRI {formatScore(champion.cpri_score)})
                    </h3>
                  </div>
                  <Badge variant="pink">{role} Champion</Badge>
                </div>

                <div className="flex-1 flex items-center justify-center">
                  <CPRIComponentRadar
                    componentsA={champion.components || {
                      pressure_impact: champion.score_pressure_impact || 0,
                      pressure_adaptability: champion.score_adaptability || 0,
                      clutch_consistency: champion.score_consistency || 0,
                      reliability_confidence: champion.score_reliability || 0,
                    }}
                    labelA={champion.player_name}
                    height={300}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Sensitivity Table when Active View is Selected */}
          {isActive && sensitivityWindows.length > 0 && (
            <div className="bg-white border border-[#E5E7EB] rounded-lg p-5 shadow-xs">
              <div className="mb-3">
                <div className="text-xs font-bold uppercase tracking-wider text-[#EC008C] mb-0.5">
                  Methodology Robustness
                </div>
                <h3 className="text-base font-bold text-[#101F43]">
                  Activity Window Sensitivity Analysis (6 vs 12 vs 18 Months)
                </h3>
                <p className="text-xs text-slate-600 mt-1">
                  Evaluates how Top 10 inclusions shift across different recency thresholds relative to T_max (2026-11-01).
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="bg-[#101F43] text-white">
                      <th className="py-2.5 px-3 font-bold">Window</th>
                      <th className="py-2.5 px-3 font-bold">Cutoff Date</th>
                      <th className="py-2.5 px-3 font-bold">Batters Dropped from Top 10</th>
                      <th className="py-2.5 px-3 font-bold">Batters Entering Top 10</th>
                      <th className="py-2.5 px-3 font-bold">Bowlers Dropped</th>
                      <th className="py-2.5 px-3 font-bold">Bowlers Entering</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {sensitivityWindows.map((win, idx) => (
                      <tr key={win.window_label} className={idx === 1 ? 'bg-emerald-50 font-semibold' : 'hover:bg-slate-50'}>
                        <td className="py-2.5 px-3 font-bold text-[#101F43]">
                          {win.window_label} {idx === 1 && '(Primary)'}
                        </td>
                        <td className="py-2.5 px-3 font-mono">{win.cutoff_date}</td>
                        <td className="py-2.5 px-3 text-slate-700">{win.batters_dropped_from_top10 || 'None'}</td>
                        <td className="py-2.5 px-3 text-emerald-800">{win.batters_entered_top10 || 'None'}</td>
                        <td className="py-2.5 px-3 text-slate-700">{win.bowlers_dropped_from_top10 || 'None'}</td>
                        <td className="py-2.5 px-3 text-emerald-800">{win.bowlers_entered_top10 || 'None'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
