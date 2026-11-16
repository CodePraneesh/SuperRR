import { apiClient } from './client'

export interface ActiveQueryParams {
  role?: 'Batter' | 'Bowler' | 'All-Rounder' | 'All'
  min_balls?: number
  evidence_tier?: string
  limit?: number
}

export interface ActivePlayerItem {
  active_rank?: number
  active_ar_rank?: number
  player_id: number
  player_name: string
  role?: string
  competition_evidence: string
  cpri_score?: number
  composite_ar_cpri?: number
  batting_cpri?: number
  bowling_cpri?: number
  evidence_tier: string
  pressure_deliveries?: number
  total_pressure_balls?: number
  batting_pressure_balls?: number
  bowling_pressure_balls?: number
  pressure_matches?: number
  pressure_strike_rate?: number
  pressure_economy?: number
  sr_elevation?: number
  dot_pct?: number
  boundary_pct?: number
  score_pressure_impact?: number
  score_adaptability?: number
  score_consistency?: number
  score_reliability?: number
  [key: string]: any
}

export interface ActiveRankingsResponse {
  metadata: {
    title: string
    audit_date: string
    qualifying_criteria: string
    active_batters_count: number
    active_bowlers_count: number
    active_allrounders_count: number
  }
  filters_applied: {
    role: string
    min_balls: number
    evidence_tier?: string
    limit: number
  }
  active_batters?: ActivePlayerItem[]
  active_bowlers?: ActivePlayerItem[]
  active_allrounders?: ActivePlayerItem[]
}

export interface RetiredResponse {
  total_retired: number
  retired_players: any[]
  retired_names: string[]
}

export async function getActiveRankings(
  params?: ActiveQueryParams
): Promise<ActiveRankingsResponse> {
  const { data } = await apiClient.get<ActiveRankingsResponse>('/active/rankings', {
    params
  })
  return data
}

export async function getRetiredPlayers(): Promise<RetiredResponse> {
  const { data } = await apiClient.get<RetiredResponse>('/active/retired')
  return data
}
