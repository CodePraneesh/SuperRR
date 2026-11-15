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
}

export interface OfficialRoleRankingsResponse {
  role: string
  title: string
  total_official: number
  total_candidates: number
  official_top10: OfficialPlayerItem[]
  candidates: OfficialPlayerItem[]
  metadata: Record<string, any>
}

export interface UnifiedOfficialOverviewResponse {
  version: string
  title: string
  batters: OfficialPlayerItem[]
  bowlers: OfficialPlayerItem[]
  metadata: Record<string, any>
}
