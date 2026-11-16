import { apiClient } from './client'

export interface ActiveQueryParams {
  role?: 'Batter' | 'Bowler' | 'All'
  min_balls?: number
  evidence_tier?: string
  limit?: number
}

export interface ActivePlayerItem {
  rank: number
  player_id: number
  player_name: string
  cpri_score: number
  pressure_deliveries: number
  last_played: string
  evidence_tier: string
  official_rank: number | null
  in_official_top10: boolean
  rank_p5?: number | null
  rank_p95?: number | null
  rank_ci_90?: string
  rank_uncertainty_source?: string
  [key: string]: any
}

export interface SensitivityWindowItem {
  window_label: string
  window_months: number
  cutoff_date: string
  batters_qualifying_count: number
  batters_dropped_from_top10: string
  batters_entered_top10: string
  bowlers_qualifying_count: number
  bowlers_dropped_from_top10: string
  bowlers_entered_top10: string
}

export interface ActiveRankingsResponse {
  metadata: {
    title: string
    rule_reference: string
    rule_type: string
    last_match_date: string
    primary_window_months: number
    primary_cutoff_date: string
    competitions_scope: string
    qualifying_active_batters_count: number
    qualifying_active_bowlers_count: number
    bootstrap_rank_uncertainty_note: string
  }
  filters_applied: {
    role: string
    min_balls: number
    evidence_tier?: string
    limit: number
  }
  active_batters?: ActivePlayerItem[]
  active_bowlers?: ActivePlayerItem[]
}

export interface ActiveSensitivityResponse {
  windows: SensitivityWindowItem[]
}

export async function getActiveRankings(
  params?: ActiveQueryParams
): Promise<ActiveRankingsResponse> {
  const { data } = await apiClient.get<ActiveRankingsResponse>('/active/rankings', {
    params
  })
  return data
}

export async function getActiveSensitivity(): Promise<ActiveSensitivityResponse> {
  const { data } = await apiClient.get<ActiveSensitivityResponse>('/active/sensitivity')
  return data
}
