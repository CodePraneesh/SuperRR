import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Trophy,
  Activity,
  Bot,
  Zap,
  ShieldCheck,
  TrendingUp,
  AlertCircle,
  Clock,
  Sparkles,
  ChevronRight,
  GitCompare,
  Crown,
  Flame,
  Info,
} from 'lucide-react'
import { getPlayerProfile, getPlayerSplits } from '../api/playerApi'
import { getScoutingReport, getPressureExplanation } from '../api/scoutingApi'
import { getOfficialPlayer } from '../api/officialApi'
import type { PlayerProfileResponse, ContextualSplitsResponse } from '../types/player'
import type { ScoutingReportResponse, PressureExplanationResponse } from '../types/scouting'
import type { OfficialPlayerItem } from '../types/official'
import type { Scope, Role } from '../types/common'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { StatMetric } from '../components/common/StatMetric'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorState } from '../components/common/ErrorState'
import { MarkdownView } from '../components/common/MarkdownView'
import { CPRIComponentRadar } from '../components/charts/CPRIComponentRadar'
import { PhaseSplitsBarChart } from '../components/charts/PhaseSplitsBarChart'
import { formatScore, formatDelta } from '../utils/formatters'
import { getErrorMessage } from '../api/client'

export const PlayerIntelligencePage: React.FC = () => {
  const { scope: rawScope, role: rawRole, name: rawName } = useParams<{
    scope?: string
    role?: string
    name?: string
  }>()
  const navigate = useNavigate()

  const scope: Scope = (rawScope?.toUpperCase() as Scope) || 'IPL'
  const safeRole = rawRole || 'Batter'
  const role: Role = (safeRole.charAt(0).toUpperCase() + safeRole.slice(1).toLowerCase() as Role) || 'Batter'
  const playerName = decodeURIComponent(rawName || 'Rinku Singh')

  const [profile, setProfile] = useState<PlayerProfileResponse | null>(null)
  const [splits, setSplits] = useState<ContextualSplitsResponse | null>(null)
  const [officialData, setOfficialData] = useState<OfficialPlayerItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // AI Report state
  const [aiReport, setAiReport] = useState<ScoutingReportResponse | null>(null)
  const [pressureReport, setPressureReport] = useState<PressureExplanationResponse | null>(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [pressureLoading, setPressureLoading] = useState(false)
  const [reportError, setReportError] = useState<string | null>(null)

  const loadPlayerData = async () => {
    setLoading(true)
    setError(null)
    setAiReport(null)
    setPressureReport(null)
    try {
      const [profileData, splitsData, offData] = await Promise.all([
        getPlayerProfile(scope, role, playerName),
        getPlayerSplits(scope, role, playerName),
        getOfficialPlayer(playerName).catch(() => null),
      ])
      setProfile(profileData)
      setSplits(splitsData)
      setOfficialData(offData)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPlayerData()
  }, [scope, role, playerName])

  const handleGenerateReport = async () => {
    setReportLoading(true)
    setReportError(null)
    try {
      const res = await getScoutingReport(scope, role, playerName)
      setAiReport(res)
    } catch (err) {
      setReportError(getErrorMessage(err))
    } finally {
      setReportLoading(false)
    }
  }

  const handleGeneratePressureReport = async () => {
    setPressureLoading(true)
    try {
      const res = await getPressureExplanation(scope, role, playerName)
      setPressureReport(res)
    } catch (err) {
      setReportError(getErrorMessage(err))
    } finally {
      setPressureLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner label={`Retrieving intelligence dossier for ${playerName}...`} />
  }

  if (error || !profile) {
    return (
      <ErrorState
        title="Player Dossier Not Found"
        message={error || `Player '${playerName}' could not be located in ${scope} ${role}s.`}
        onRetry={loadPlayerData}
      />
    )
  }

  const comps = profile.components
  const contrast = splits?.pressure_contrast || {}
  const isBatter = role === 'Batter'
  const tacticalClass = contrast.tactical_classification || 'Standard Execution'

  return (
    <div className="space-y-8">
      {/* Official Phase 8 Competition Standing Banner */}
      {officialData ? (
        <div className="bg-[#101F43] border border-[#EC008C]/40 rounded-2xl p-5 shadow-lg text-white">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <span className="text-[10px] font-mono uppercase tracking-wider bg-[#EC008C] text-white px-2 py-0.5 rounded font-black">
                  Official Phase 8 Submission
                </span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                  officialData.confidence_tier === 'High Confidence'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                }`}>
                  {officialData.confidence_tier}
                </span>
                <span className="text-xs text-slate-300 font-mono">
                  {officialData.competition_evidence} Evidence
                </span>
                {officialData.last_played && (
                  <span className="text-xs text-emerald-300 font-mono bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-600/40">
                    Last Played: {officialData.last_played}
                  </span>
                )}
              </div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                <span>{officialData.player_name}</span>
                <span className="text-slate-300 font-normal text-sm">
                  — {officialData.is_official_top10 ? `Official #${officialData.official_rank} ${officialData.role}` : 'not in Top 10'}
                </span>
              </h2>
              <div className="text-xs text-slate-300 mt-1 flex flex-wrap items-center gap-3">
                <span>
                  90% Bootstrap Rank CI: <span className="font-mono font-bold text-amber-300">[{officialData.rank_uncertainty.rank_p5}, {officialData.rank_uncertainty.rank_p95}]</span>
                </span>
                <span>•</span>
                <span>
                  Top-10 Inclusion: <span className="font-mono text-emerald-300">{(officialData.rank_uncertainty.top10_inclusion_freq * 100).toFixed(0)}%</span>
                </span>
                <span>•</span>
                <span className="font-mono text-white">
                  {officialData.pressure_stats?.pressure_deliveries || 0} Pressure Balls ({officialData.pressure_stats?.pressure_matches || 0} Matches)
                </span>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {/* Rank Interval Bar Visual */}
              <div className="hidden sm:flex flex-col gap-1 w-32 bg-[#070b18]/80 p-2.5 rounded-xl border border-pink-500/20">
                <span className="text-[10px] uppercase font-mono text-slate-400">90% Rank Interval</span>
                <span className="text-xs font-mono font-bold text-amber-300">[{officialData.rank_uncertainty.rank_p5}, {officialData.rank_uncertainty.rank_p95}]</span>
                <div className="w-full h-1.5 bg-slate-700 rounded-full overflow-hidden relative mt-1">
                  <div
                    className="h-full bg-gradient-to-r from-[#EC008C] to-indigo-400 rounded-full absolute"
                    style={{
                      left: `${Math.max(0, Math.min(100, ((officialData.rank_uncertainty.rank_p5 - 1) / 75) * 100))}%`,
                      width: `${Math.max(6, Math.min(100, ((officialData.rank_uncertainty.rank_p95 - officialData.rank_uncertainty.rank_p5) / 75) * 100))}%`
                    }}
                  />
                </div>
              </div>
              <div className="text-right bg-[#070b18]/80 px-4 py-2.5 rounded-xl border border-pink-500/20 min-w-[130px]">
                <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">Official CPRI</div>
                <div className="text-3xl font-black font-mono text-[#EC008C]">
                  {formatScore(officialData.cpri_score)}
                </div>
                <div className="text-[10px] font-mono text-amber-300">Phase 8 Baseline</div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-[#101F43]/5 border border-slate-200 rounded-xl p-4 text-slate-600 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Info className="w-5 h-5 text-slate-400 flex-shrink-0" />
            <div className="text-xs">
              <span className="font-semibold text-slate-800">Contextual League Profile ({scope}):</span> This dossier represents single-tournament {scope} play. Player official rank: <span className="font-bold text-amber-800">not in Top 10</span>.
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold bg-slate-200 text-slate-700 px-2.5 py-1 rounded">
            not in Top 10
          </span>
        </div>
      )}

      {/* Header Profile Hero Card */}
      <Card variant="royal" className="p-6 md:p-8 relative overflow-hidden border-slate-200">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200">
                {profile.competition_scope} {profile.role}
              </span>
              <Badge variant={profile.is_official_top10 ? 'official' : 'provisional'} size="md">
                {officialData?.is_official_top10 ? `Official #${officialData.official_rank}` : 'not in Top 10'}
              </Badge>
              <Badge variant="high" size="md">
                {profile.confidence_tier}
              </Badge>
              {(officialData?.last_played || (profile as any).last_played) && (
                <span className="text-xs font-mono text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-300">
                  Last Played: {officialData?.last_played || (profile as any).last_played}
                </span>
              )}
            </div>

            <h1 className="text-3xl md:text-4xl font-extrabold text-[#0F172A] tracking-tight mb-2 flex items-center gap-2">
              <span>{profile.player_name}</span>
              {officialData?.official_rank === 1 && (
                <Crown className="w-7 h-7 text-amber-500 inline" />
              )}
            </h1>

            <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-[#64748B]">
              <div className="flex items-center gap-1.5 text-amber-900 font-bold bg-amber-50 px-2 py-0.5 rounded border border-amber-300">
                <Trophy className="w-3.5 h-3.5 text-amber-600" />
                {officialData?.is_official_top10
                  ? `Official Rank #${officialData.official_rank} in ${profile.cohort}`
                  : 'Official Rank: not in Top 10'}
              </div>
              <div className="text-[#334155] font-medium">
                {officialData?.pressure_stats?.pressure_deliveries ?? profile.exposure.pressure_deliveries} Pressure Balls
              </div>
              <span className="text-slate-400">•</span>
              <div className="text-[#334155] font-medium">
                {officialData?.pressure_stats?.pressure_matches ?? profile.exposure.pressure_matches} Pressure Matches
              </div>
              <span className="text-slate-400">•</span>
              <div className="text-[#EC008C] font-semibold">{formatScore(profile.exposure.pos_pressure_match_ratio * 100, 1)}% Positive Match Ratio</div>
            </div>
          </div>

          {/* Master CPRI Score Display */}
          <div className="flex items-center gap-6 bg-slate-50 border border-pink-200 p-5 rounded-2xl shadow-xs">
            <div>
              <div className="text-[11px] font-mono uppercase tracking-wider text-[#EC008C] mb-0.5 font-bold">
                Official CPRI Score
              </div>
              <div className="text-4xl md:text-5xl font-black font-mono text-[#EC008C]">
                <span>{formatScore(officialData?.cpri_score ?? profile.cpri_score)}</span>
              </div>
              <div className="text-[10px] font-mono text-[#64748B] mt-1 flex items-center gap-1 font-medium">
                <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
                CPRI v1.0.0 Frozen Baseline
              </div>
            </div>

            {/* Quick action to compare */}
            <button
              onClick={() => navigate('/compare')}
              className="p-3 rounded-xl bg-slate-100 hover:bg-pink-50 border border-slate-300 hover:border-pink-300 text-[#334155] hover:text-[#EC008C] transition-colors focus:outline-none focus:ring-2 focus:ring-[#EC008C]"
              title="Compare with another player"
              aria-label="Compare with another player"
            >
              <GitCompare className="w-5 h-5" />
            </button>
          </div>
        </div>
      </Card>

      {/* 4 CPRI Components Grid */}
      <div>
        <h2 className="text-sm font-bold text-[#0F172A] uppercase tracking-wider font-mono mb-3 flex items-center gap-2">
          <Activity className="w-4 h-4 text-pink-600" />
          The Four Constituent CPRI Component Scores
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatMetric
            label="score_pressure_impact"
            value={formatScore(comps.pressure_impact, 2)}
            weight="40% Weight"
            subValue={`Percentile: ${formatScore(profile.peer_benchmarks?.cohort_percentiles.pressure_impact_percentile, 1)}%`}
          />
          <StatMetric
            label="score_adaptability"
            value={formatScore(comps.pressure_adaptability, 2)}
            weight="25% Weight"
            subValue={`Percentile: ${formatScore(profile.peer_benchmarks?.cohort_percentiles.adaptability_percentile, 1)}%`}
          />
          <StatMetric
            label="score_consistency"
            value={formatScore(comps.clutch_consistency, 2)}
            weight="20% Weight"
            subValue={`Percentile: ${formatScore(profile.peer_benchmarks?.cohort_percentiles.consistency_percentile, 1)}%`}
          />
          <StatMetric
            label="score_reliability"
            value={formatScore(comps.reliability_confidence, 2)}
            weight="15% Weight"
            subValue={`Percentile: ${formatScore(profile.peer_benchmarks?.cohort_percentiles.reliability_percentile, 1)}%`}
          />
        </div>
      </div>

      {/* Visual Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar of the 4 Components */}
        <Card variant="default" className="border-slate-200">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-bold text-[#0F172A] flex items-center gap-2">
                <Zap className="w-4 h-4 text-pink-600" />
                Component Distribution
              </h3>
              <p className="text-xs text-[#64748B]">
                Evaluation across the 4 CPRI dimensions
              </p>
            </div>
            <span className="text-xs font-mono text-[#EC008C] font-bold">
              CPRI {formatScore(profile.cpri_score)}
            </span>
          </div>
          <CPRIComponentRadar componentsA={profile.components} labelA={profile.player_name} height={260} />
        </Card>

        {/* Situational Phase Splits Bar Chart */}
        {splits && (
          <Card variant="default" className="border-slate-200">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-bold text-[#0F172A] flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                  Situational Phase Execution
                </h3>
                <p className="text-xs text-[#64748B]">
                  Performance across Powerplay, Middle, and Death overs
                </p>
              </div>
              <Badge variant="blue" size="sm">
                {isBatter ? 'Strike Rate' : 'Economy'}
              </Badge>
            </div>
            <PhaseSplitsBarChart splits={splits} height={260} />
          </Card>
        )}
      </div>

      {/* Pressure Contrast Section (High vs Low Pressure) */}
      <Card variant="default" className="p-6 border-slate-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
          <div>
            <div className="text-xs font-mono uppercase tracking-wider text-[#EC008C] font-semibold mb-1">
              Leverage State Contrast
            </div>
            <h3 className="text-lg font-bold text-[#0F172A]">
              High Pressure (PI ≥ 50) vs Low Pressure (PI &lt; 50)
            </h3>
            <p className="text-xs text-[#64748B]">
              Empirical metric shift when match outcome leverage spikes
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#64748B] font-medium">Tactical Classification:</span>
            <span className="px-3 py-1 rounded-full text-xs font-bold font-mono bg-pink-50 text-[#EC008C] border border-pink-200">
              {tacticalClass}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div className="text-xs text-[#64748B] uppercase font-mono mb-1 font-semibold">
              High Pressure ({isBatter ? 'Strike Rate' : 'Economy'})
            </div>
            <div className="text-2xl font-bold font-mono text-[#0F172A]">
              {isBatter
                ? formatScore(contrast.high_pressure?.strike_rate, 1)
                : formatScore(contrast.high_pressure?.economy_rate, 2)}
            </div>
            <div className="text-[11px] font-mono text-[#64748B] mt-1">
              {contrast.high_pressure?.balls_faced || contrast.high_pressure?.balls_bowled || 0} balls faced/bowled
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div className="text-xs text-[#64748B] uppercase font-mono mb-1 font-semibold">
              Low Pressure ({isBatter ? 'Strike Rate' : 'Economy'})
            </div>
            <div className="text-2xl font-bold font-mono text-[#334155]">
              {isBatter
                ? formatScore(contrast.low_pressure?.strike_rate, 1)
                : formatScore(contrast.low_pressure?.economy_rate, 2)}
            </div>
            <div className="text-[11px] font-mono text-[#64748B] mt-1">
              {contrast.low_pressure?.balls_faced || contrast.low_pressure?.balls_bowled || 0} balls faced/bowled
            </div>
          </div>

          <div className="p-4 rounded-xl bg-pink-50/70 border border-pink-200">
            <div className="text-xs text-[#EC008C] uppercase font-mono mb-1 font-bold">
              Net Pressure Delta
            </div>
            <div className="text-2xl font-bold font-mono text-[#EC008C]">
              {isBatter
                ? `${formatDelta(contrast.delta_strike_rate, 2)} SR`
                : `${formatDelta(contrast.delta_economy, 2)} Econ`}
            </div>
            <div className="text-[11px] font-mono text-pink-700 mt-1 font-semibold">
              {isBatter
                ? contrast.delta_strike_rate && contrast.delta_strike_rate > 0
                ? '⚡ Accelerates under pressure'
                : 'Decelerates under pressure'
              : contrast.delta_economy && contrast.delta_economy < 0
              ? '⚡ Tightens under pressure'
              : 'Concedes more under pressure'}
            </div>
          </div>
        </div>
      </Card>

      {/* Empirical Strengths & Weaknesses */}
      {profile.strengths_and_weaknesses && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card variant="default" className="border-slate-200">
            <div className="flex items-center gap-2 mb-3 text-emerald-800 text-sm font-bold">
              <Sparkles className="w-4 h-4 text-emerald-600" />
              Verified Empirical Strengths
            </div>
            <ul className="space-y-2.5">
              {profile.strengths_and_weaknesses.strengths.map((str, i) => (
                <li key={i} className="text-xs text-[#475569] flex items-start gap-2.5 leading-relaxed">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 mt-1.5 flex-shrink-0" />
                  <span className="text-[#334155] font-medium">{str}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card variant="default" className="border-slate-200">
            <div className="flex items-center gap-2 mb-3 text-amber-800 text-sm font-bold">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              Empirical Tactical Vulnerabilities
            </div>
            <ul className="space-y-2.5">
              {profile.strengths_and_weaknesses.weaknesses.map((w, i) => (
                <li key={i} className="text-xs text-[#475569] flex items-start gap-2.5 leading-relaxed">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-600 mt-1.5 flex-shrink-0" />
                  <span className="text-[#334155] font-medium">{w}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}

      {/* AI Scouting Report Generator Action Section */}
      <Card variant="royal" className="p-6 border-slate-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2 text-[#EC008C] text-xs font-mono font-semibold uppercase mb-1">
              <Bot className="w-4 h-4" />
              Three-Tier AI Scouting Intelligence
            </div>
            <h3 className="text-lg font-bold text-[#0F172A]">
              Evidence-Grounded AI Scouting Report
            </h3>
            <p className="text-xs text-[#64748B]">
              Generate a comprehensive tactical report audited by zero-hallucination verification
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleGeneratePressureReport}
              disabled={pressureLoading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-300 text-xs font-semibold text-[#334155] transition-colors disabled:opacity-50"
            >
              {pressureLoading ? <Clock className="w-3.5 h-3.5 animate-spin text-[#EC008C]" /> : <Clock className="w-3.5 h-3.5 text-[#64748B]" />}
              Explain Pressure
            </button>
            <button
              onClick={handleGenerateReport}
              disabled={reportLoading}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-xs font-bold text-white shadow-lg shadow-pink-600/30 transition-all disabled:opacity-50"
            >
              {reportLoading ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  Synthesizing Report...
                </>
              ) : (
                <>
                  <Bot className="w-4 h-4" />
                  Generate AI Scouting Report
                </>
              )}
            </button>
          </div>
        </div>

        {reportError && (
          <div className="mt-4 p-4 rounded-xl bg-rose-50 border border-rose-300 text-xs text-rose-800">
            {reportError}
          </div>
        )}

        {/* Display Pressure Dossier if requested */}
        {pressureReport && (
          <div className="mt-6 p-5 rounded-xl bg-slate-50 border border-blue-200">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-blue-200 text-xs font-mono text-blue-900 font-bold">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <span>Pressure Performance Dossier</span>
              </div>
              <Badge variant="blue" size="sm">
                {pressureReport.tier_used}
              </Badge>
            </div>
            <MarkdownView content={pressureReport.response} />
          </div>
        )}

        {/* Display Full AI Scouting Report */}
        {aiReport && (
          <div className="mt-6 p-6 rounded-xl bg-slate-50 border border-pink-200 shadow-xs">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-200 text-xs font-mono">
              <div className="flex items-center gap-2 text-pink-700 font-bold">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Verified AI Scouting Intelligence</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={aiReport.verified ? 'official' : 'warning'} size="sm">
                  {aiReport.verified ? 'Numerical Verification Passed' : 'Verification Fallback'}
                </Badge>
                <span className="text-[11px] text-[#64748B]">Model: {aiReport.model_name}</span>
              </div>
            </div>
            <MarkdownView content={aiReport.response} />
          </div>
        )}
      </Card>
    </div>
  )
}
