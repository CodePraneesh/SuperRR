import { CPRIComponents } from './player'

export interface RankUncertainty {
  rank_p5: number
  rank_p95: number
  median_rank: number
  rank_std: number
  top10_inclusion_freq: number
  ci_display: string
}

export interface OfficialPlayerItem {
  official_rank: number
  player_id: number
  player_name: string
  role: 'Batter' | 'Bowler'
  competition_evidence: string
  cpri_score: number
  components: CPRIComponents
  pressure_stats: {
    pressure_deliveries: number
    pressure_matches: number
    pressure_strike_rate?: number
    pressure_economy?: number
    pressure_run_res?: number
    pressure_runs_saved?: number
    pressure_surv_res?: number
    pressure_wkts_above_exp?: number
    pressure_wpa: number
    total_deliveries: number
    total_matches: number
  }
  rank_uncertainty: RankUncertainty
  confidence_tier: 'High Confidence' | 'Exploratory'
  tactical_classification: string
  is_official_top10: boolean
  contextual_splits?: Record<string, any>

  // High-Volume PPR Upgrade Extensions
  adjusted_cpri?: number
  adjusted_rank?: number
  ppr_score?: number
  evidence_tier?: 'Elite Evidence' | 'Strong Evidence' | 'Moderate Evidence' | 'Limited Evidence' | 'Insufficient Evidence' | string
  is_main_eligible?: boolean
  eligibility_status?: 'Main Leaderboard' | 'Contender / Emerging' | 'Insufficient Evidence' | string
  success_rate_pct?: number
  role_success_metrics?: {
    success_rate_pct?: number
    dot_pct?: number
    boundary_pct?: number
    frequency_metric_pct?: number
  }
  adjusted_rank_ci?: string
  last_played?: string
}

export interface OfficialRoleRankingsResponse {
  role: string
  title: string
  total_official: number
  total_candidates: number
  official_top10: OfficialPlayerItem[]
  pre_floor_baseline?: OfficialPlayerItem[]
  candidates: OfficialPlayerItem[]
  main_leaderboard?: OfficialPlayerItem[]
  contenders?: OfficialPlayerItem[]
  insufficient_evidence?: OfficialPlayerItem[]
  evidence_tier_counts?: Record<string, number>
  metadata: Record<string, any>
}

export interface UnifiedOfficialOverviewResponse {
  version: string
  title: string
  batters: OfficialPlayerItem[]
  bowlers: OfficialPlayerItem[]
  pre_floor_batters?: OfficialPlayerItem[]
  pre_floor_bowlers?: OfficialPlayerItem[]
  main_leaderboard_batters?: OfficialPlayerItem[]
  main_leaderboard_bowlers?: OfficialPlayerItem[]
  contender_batters?: OfficialPlayerItem[]
  contender_bowlers?: OfficialPlayerItem[]
  metadata: Record<string, any>
}
