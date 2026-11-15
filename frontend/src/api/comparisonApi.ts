import { apiClient } from './client'
import type { PlayerComparisonRequest, PlayerComparisonResponse } from '../types/scouting'

export async function comparePlayers(
  request: PlayerComparisonRequest
): Promise<PlayerComparisonResponse> {
  const { data } = await apiClient.post<PlayerComparisonResponse>('/scouting/compare', request)
  return data
}
