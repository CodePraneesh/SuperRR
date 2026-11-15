import { apiClient } from './client'
import type {
  UnifiedOfficialOverviewResponse,
  OfficialRoleRankingsResponse,
  OfficialPlayerItem
} from '../types/official'

export interface OfficialQueryParams {
  min_balls?: number
  evidence_tier?: string
  format_evidence?: string
}

export async function getOfficialUnifiedRankings(): Promise<UnifiedOfficialOverviewResponse> {
  const { data } = await apiClient.get<UnifiedOfficialOverviewResponse>('/official/rankings')
  return data
}

export async function getOfficialRoleRankings(
  role: 'Batter' | 'Bowler',
  params?: OfficialQueryParams
): Promise<OfficialRoleRankingsResponse> {
  const { data } = await apiClient.get<OfficialRoleRankingsResponse>(`/official/${role}`, {
    params
  })
  return data
}

export async function getOfficialPlayer(name: string): Promise<OfficialPlayerItem> {
  const encoded = encodeURIComponent(name)
  const { data } = await apiClient.get<OfficialPlayerItem>(`/official/player/${encoded}`)
  return data
}
