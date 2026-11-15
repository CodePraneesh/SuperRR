import React, { useState, useEffect } from 'react'
import {
  Swords,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Zap,
  Target,
  Clock,
  Sparkles,
} from 'lucide-react'
import { getCohortPlayers } from '../api/playerApi'
import { getMatchup } from '../api/matchupApi'
import type { MatchupResponse } from '../types/scouting'
import type { PlayerSummaryItem } from '../types/player'
import type { Scope } from '../types/common'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { StatMetric } from '../components/common/StatMetric'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorState } from '../components/common/ErrorState'
import { MarkdownView } from '../components/common/MarkdownView'
import { formatScore, formatPercent } from '../utils/formatters'
import { getErrorMessage } from '../api/client'

export const MatchupAnalysisPage: React.FC = () => {
  const [scope, setScope] = useState<Scope>('IPL')
  const [batters, setBatters] = useState<PlayerSummaryItem[]>([])
  const [bowlers, setBowlers] = useState<PlayerSummaryItem[]>([])
  const [loadingCohorts, setLoadingCohorts] = useState(false)

  // Selected players
  const [selectedBatter, setSelectedBatter] = useState<string>('')
  const [selectedBowler, setSelectedBowler] = useState<string>('')

  // Matchup response
  const [matchup, setMatchup] = useState<MatchupResponse | null>(null)
  const [loadingMatchup, setLoadingMatchup] = useState(false)
  const [matchupError, setMatchupError] = useState<string | null>(null)

  // Load cohorts for dropdowns
  useEffect(() => {
    let mounted = true
    setLoadingCohorts(true)
    setMatchup(null)
    setMatchupError(null)

    Promise.all([
      getCohortPlayers(scope, 'Batter', { limit: 100 }),
      getCohortPlayers(scope, 'Bowler', { limit: 100 }),
    ])
      .then(([batterData, bowlerData]) => {
        if (mounted) {
          setBatters(batterData.players)
          setBowlers(bowlerData.players)
          if (batterData.players.length > 0) {
            // Default to famous encounter if available
            const virat = batterData.players.find((p) => p.player_name.includes('Kohli'))
            setSelectedBatter(virat ? virat.player_name : batterData.players[0].player_name)
          }
          if (bowlerData.players.length > 0) {
            const bumrah = bowlerData.players.find((p) => p.player_name.includes('Bumrah'))
            setSelectedBowler(bumrah ? bumrah.player_name : bowlerData.players[0].player_name)
          }
        }
      })
      .catch((err) => {
        if (mounted) setMatchupError(getErrorMessage(err))
      })
      .finally(() => {
        if (mounted) setLoadingCohorts(false)
      })

    return () => {
      mounted = false
    }
  }, [scope])

  const handleInspectMatchup = async () => {
    if (!selectedBatter || !selectedBowler) {
      setMatchupError('Please select both a batter and a bowler.')
      return
    }

    setLoadingMatchup(true)
    setMatchupError(null)
    try {
      const data = await getMatchup(scope, selectedBatter, selectedBowler)
      setMatchup(data)
    } catch (err) {
      setMatchupError(getErrorMessage(err))
    } finally {
      setLoadingMatchup(false)
    }
  }

  const h2h = matchup?.h2h_data

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2 text-xs font-mono font-medium text-pink-400 mb-1">
          <Swords className="w-4 h-4 text-pink-400" />
          <span>Tactical Head-to-Head Analytics</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <span>Batter vs Bowler</span>
          <span className="text-pink-500 font-black">Matchup Intelligence</span>
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Evaluate historical encounters between specific batters and bowlers with rigorous sample size certification.
        </p>
      </div>

      {/* Selection Form */}
      <Card variant="subtle" className="p-6 border-[#182752]">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          {/* Scope Selector */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-bold">
              Competition Scope
            </label>
            <div className="grid grid-cols-2 gap-1 p-1 rounded-lg bg-[#070b18] border border-[#182752] text-xs font-semibold">
              <button
                onClick={() => setScope('IPL')}
                className={`py-1.5 rounded-md transition-all ${
                  scope === 'IPL'
                    ? 'bg-gradient-to-r from-blue-700 to-indigo-700 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                IPL
              </button>
              <button
                onClick={() => setScope('T20I')}
                className={`py-1.5 rounded-md transition-all ${
                  scope === 'T20I'
                    ? 'bg-gradient-to-r from-blue-700 to-indigo-700 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                T20I
              </button>
            </div>
          </div>

          {/* Batter Dropdown */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-pink-400 mb-1.5 font-bold">
              Select Batter (Pink)
            </label>
            <select
              value={selectedBatter}
              onChange={(e) => setSelectedBatter(e.target.value)}
              disabled={loadingCohorts}
              className="w-full px-3 py-2 rounded-lg bg-[#070b18] border border-pink-500/40 text-xs text-white focus:outline-none focus:border-pink-400 font-medium"
            >
              {batters.map((b) => (
                <option key={b.player_name} value={b.player_name}>
                  {b.player_name} (CPRI {formatScore(b.cpri_score)})
                </option>
              ))}
            </select>
          </div>

          {/* Bowler Dropdown */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-blue-400 mb-1.5 font-bold">
              Select Bowler (Blue)
            </label>
            <select
              value={selectedBowler}
              onChange={(e) => setSelectedBowler(e.target.value)}
              disabled={loadingCohorts}
              className="w-full px-3 py-2 rounded-lg bg-[#070b18] border border-blue-500/40 text-xs text-white focus:outline-none focus:border-blue-400 font-medium"
            >
              {bowlers.map((bw) => (
                <option key={bw.player_name} value={bw.player_name}>
                  {bw.player_name} (CPRI {formatScore(bw.cpri_score)})
                </option>
              ))}
            </select>
          </div>

          {/* Submit Action */}
          <div>
            <button
              onClick={handleInspectMatchup}
              disabled={loadingMatchup || loadingCohorts || !selectedBatter || !selectedBowler}
              className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-pink-600 via-rose-600 to-blue-600 hover:from-pink-500 hover:to-blue-500 text-xs font-bold text-white shadow-lg shadow-pink-600/20 transition-all disabled:opacity-50"
            >
              <Swords className="w-4 h-4" />
              {loadingMatchup ? 'Analyzing...' : 'Analyze Matchup'}
            </button>
          </div>
        </div>
      </Card>

      {matchupError && <ErrorState message={matchupError} />}

      {loadingMatchup && <LoadingSpinner label={`Retrieving matchup metrics for ${selectedBatter} vs ${selectedBowler}...`} />}

      {/* Matchup Encounter Results */}
      {matchup && h2h && (
        <div className="space-y-6">
          {/* Small Sample Warning Alert Banner if exploratory (<18 balls) */}
          {matchup.is_small_sample && (
            <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/20 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-amber-200">
                  Exploratory Sample Size Notice ({h2h.balls_faced} balls)
                </h4>
                <p className="text-xs text-amber-300/80 mt-0.5">
                  {matchup.sample_warning ||
                    `This head-to-head encounter contains fewer than 18 legal deliveries. Tactical conclusions should be treated with caution, as high variance governs small sample sizes.`}
                </p>
              </div>
            </div>
          )}

          {/* Main Encounter Scoreboard */}
          <Card variant="royal" className="p-6 md:p-8 border-[#182752]">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-[#182752]">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-pink-500/20 border border-pink-500/40 flex items-center justify-center text-pink-400 shadow-md shadow-pink-500/20">
                  <Swords className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-0.5 font-bold">
                    {matchup.competition_scope} Head-to-Head
                  </div>
                  <h2 className="text-2xl md:text-3xl font-extrabold text-white">
                    <span className="text-pink-400">{matchup.batter_name}</span>{' '}
                    <span className="text-slate-500 font-light">vs</span>{' '}
                    <span className="text-blue-400">{matchup.bowler_name}</span>
                  </h2>
                </div>
              </div>

              {/* Sample Tier Badge */}
              <div className="flex items-center gap-2">
                <Badge
                  variant={matchup.is_small_sample ? 'warning' : 'official'}
                  size="md"
                >
                  {matchup.sample_tier}
                </Badge>
              </div>
            </div>

            {/* Core Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6">
              <StatMetric label="Balls Faced" value={h2h.balls_faced} />
              <StatMetric label="Runs Scored" value={h2h.runs_scored} />
              <StatMetric
                label="Dismissals"
                value={h2h.dismissals}
                subValue={h2h.balls_per_dismissal ? `${formatScore(h2h.balls_per_dismissal, 1)} balls/out` : undefined}
              />
              <StatMetric
                label="Strike Rate"
                value={formatScore(h2h.strike_rate, 1)}
                subValue={h2h.strike_rate >= 150 ? 'Dominant Striking' : undefined}
                trend={h2h.strike_rate >= 140 ? 'positive' : 'neutral'}
              />
              <StatMetric
                label="Dot Ball %"
                value={formatPercent(h2h.dot_percentage)}
                subValue={`${h2h.dot_balls} dots`}
              />
            </div>

            {/* Secondary Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-[#182752]/80 text-xs font-mono text-slate-400">
              <div>Boundaries: <span className="text-white font-semibold">{h2h.fours} fours, {h2h.sixes} sixes</span></div>
              <div>Boundary %: <span className="text-white font-semibold">{formatPercent(h2h.boundary_percentage)}</span></div>
              <div>Batting Average: <span className="text-white font-semibold">{formatScore(h2h.batting_average, 1)}</span></div>
              <div>Statistical Reliability: <span className={matchup.is_small_sample ? 'text-amber-400 font-bold' : 'text-emerald-400 font-bold'}>{matchup.is_small_sample ? 'Caution (Low Sample)' : 'Certified Reliable'}</span></div>
            </div>
          </Card>

          {/* AI Narrative Breakdown */}
          <Card variant="default" className="p-6 border-[#182752]">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#182752] text-xs font-mono">
              <div className="flex items-center gap-2 text-pink-300 font-bold">
                <Sparkles className="w-4 h-4 text-pink-400" />
                <span>Tactical Scouting Narrative & Caveats</span>
              </div>
              <Badge variant={matchup.verified ? 'official' : 'warning'} size="sm">
                {matchup.tier_used}
              </Badge>
            </div>
            <MarkdownView content={matchup.ai_narrative} />
          </Card>
        </div>
      )}
    </div>
  )
}
