export interface CPRIComponents {
  pressure_impact: number
  pressure_adaptability: number
  clutch_consistency: number
  reliability_confidence: number
}

export interface PlayerSummaryItem {
  player_id?: number | null
  player_name: string
  competition_scope: 'IPL' | 'T20I'
  role: 'Batter' | 'Bowler'
  cohort: string
  official_rank?: number | null
  ranking_tier: string
  confidence_tier: string
  is_official_top10: boolean
  is_official_ranked?: boolean
  cpri_score: number
  components: CPRIComponents
  pressure_deliveries: number
  strike_rate?: number | null
  economy_rate?: number | null
}

export interface CohortListResponse {
  competition_scope: string
  role: string
  cohort: string
  total_players: number
  official_count: number
  limit: number
  offset: number
  players: PlayerSummaryItem[]
}

export interface PeerPercentiles {
  cpri_percentile: number
  pressure_impact_percentile: number
  adaptability_percentile: number
  consistency_percentile: number
  reliability_percentile: number
}

export interface PeerBenchmarks {
  player_name: string
  cohort: string
  competition_scope: string
  role: string
  official_rank?: number | null
  total_cohort_peers: number
  player_scores: CPRIComponents & { cpri_score: number }
  cohort_percentiles: PeerPercentiles
  cohort_benchmarks: {
    cohort_mean_cpri: number
    cohort_max_cpri: number
    top10_cutoff_cpri: number
    delta_to_rank_1: number
    delta_to_top10_cutoff: number
  }
}

export interface StrengthsAndWeaknesses {
  player_name: string
  competition_scope: string
  role: string
  cpri_score: number
  strengths: string[]
  weaknesses: string[]
  neutral_observations?: string[]
}

export interface PlayerProfileResponse {
  player_id?: number | null
  player_name: string
  competition_scope: 'IPL' | 'T20I'
  role: 'Batter' | 'Bowler'
  cohort: string
  official_rank?: number | null
  ranking_tier: string
  confidence_tier: string
  is_official_top10: boolean
  is_official_ranked?: boolean
  cpri_score: number
  components: CPRIComponents
  exposure: {
    total_deliveries: number
    pressure_deliveries: number
    pressure_matches: number
    total_matches?: number
    pos_pressure_match_ratio: number
    effective_pressure_sample_size?: number
    pressure_specific_uncertainty?: number
  }
  performance_stats: {
    balls_faced?: number
    balls_bowled?: number
    actual_runs?: number
    runs_conceded?: number
    strike_rate?: number
    economy_rate?: number
    batting_average?: number | null
    bowling_average?: number | null
    dismissals?: number
    credited_wickets?: number
    dot_percentage?: number
    boundary_percentage?: number
    pressure_stats?: Record<string, any>
    nonpressure_stats?: Record<string, any>
  }
  peer_benchmarks?: PeerBenchmarks
  strengths_and_weaknesses?: StrengthsAndWeaknesses
}

export interface ContextualSplitsResponse {
  player_name: string
  competition_scope: string
  role: string
  innings_phase_splits: {
    powerplay?: Record<string, any>
    middle?: Record<string, any>
    death?: Record<string, any>
  }
  pressure_contrast: {
    high_pressure?: Record<string, any>
    low_pressure?: Record<string, any>
    delta_strike_rate?: number
    delta_economy?: number
    tactical_classification?: string
  }
  bowling_type_splits?: {
    pace?: Record<string, any>
    spin?: Record<string, any>
  }
  batter_hand_splits?: {
    rhb?: Record<string, any>
    lhb?: Record<string, any>
  }
}
