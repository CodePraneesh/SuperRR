import { apiClient } from './client'
import type {
  UnifiedOfficialOverviewResponse,
  OfficialRoleRankingsResponse,
  OfficialPlayerItem
} from '../types/official'

export async function getOfficialUnifiedRankings(): Promise<UnifiedOfficialOverviewResponse> {
  const { data } = await apiClient.get<UnifiedOfficialOverviewResponse>('/official/rankings')
  return data
}

export async function getOfficialRoleRankings(role: 'Batter' | 'Bowler'): Promise<OfficialRoleRankingsResponse> {
  const { data } = await apiClient.get<OfficialRoleRankingsResponse>(`/official/${role}`)
  return data
}

export async function getOfficialPlayer(name: string): Promise<OfficialPlayerItem> {
  const encoded = encodeURIComponent(name)
  const { data } = await apiClient.get<OfficialPlayerItem>(`/official/player/${encoded}`)
  return data
}
