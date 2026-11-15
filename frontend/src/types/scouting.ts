export interface ScoutingReportResponse {
  status: string
  player_name: string
  competition_scope: string
  role: string
  feature: string
  tier_used: string
  model_name: string
  verified: boolean
  verification_notes: string[]
  response: string
  sample_limitations: string[]
}

export interface PressureExplanationResponse {
  status: string
  player_name: string
  competition_scope: string
  role: string
  feature: string
  tier_used: string
  model_name: string
  verified: boolean
  verification_notes: string[]
  response: string
  sample_limitations: string[]
}

export interface PlayerComparisonRequest {
  scope: 'IPL' | 'T20I'
  role: 'Batter' | 'Bowler'
  player_a: string
  player_b: string
}

export interface StructuredComparisonDeltas {
  cpri_delta: number
  pressure_impact_delta: number
  adaptability_delta: number
  consistency_delta: number
  reliability_delta: number
}

export interface PlayerComparisonResponse {
  status: string
  comparison_scope: string
  role: string
  player_a: string
  player_b: string
  structured_comparison: {
    comparison_scope: string
    role?: string
    batter_a?: Record<string, any>
    batter_b?: Record<string, any>
    bowler_a?: Record<string, any>
    bowler_b?: Record<string, any>
    deltas_a_minus_b: StructuredComparisonDeltas
    phase_comparison?: Record<string, any>
  }
  ai_analysis: string
  tier_used: string
  model_name: string
  verified: boolean
  verification_notes: string[]
  sample_limitations: string[]
}

export interface MatchupRecord {
  matchup_id: string
  matchup_key: string
  competition_scope: string
  batter_id?: number | null
  batter_name: string
  bowler_id?: number | null
  bowler_name: string
  balls_faced: number
  runs_scored: number
  dismissals: number
  fours: number
  sixes: number
  dot_balls: number
  strike_rate: number
  batting_average?: number | null
  balls_per_dismissal?: number | null
  dot_percentage: number
  boundary_percentage: number
  avg_pressure_score?: number | null
  sample_tier: string
  is_statistically_reliable: boolean
  ranked_player_involved: boolean
  notes?: string
}

export interface MatchupResponse {
  status: string
  competition_scope: string
  batter_name: string
  bowler_name: string
  h2h_data: MatchupRecord
  ai_narrative: string
  tier_used: string
  model_name: string
  verified: boolean
  is_small_sample: boolean
  sample_tier: string
  sample_warning?: string | null
}

export interface AnalyticsQueryRequest {
  query: string
  scope?: string
  role?: string
  target_entities?: string[]
}

export interface AnalyticsQueryResponse {
  status: string
  query: string
  scope?: string
  answer: string
  tier_used: string
  model_name: string
  verified: boolean
  verification_notes: string[]
  evidence_summary?: Record<string, any>
}
