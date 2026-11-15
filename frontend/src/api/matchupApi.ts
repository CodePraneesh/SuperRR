import { apiClient } from './client'
import type { MatchupResponse } from '../types/scouting'
import type { Scope } from '../types/common'

export async function getMatchup(
  scope: Scope,
  batter: string,
  bowler: string
): Promise<MatchupResponse> {
  const encBatter = encodeURIComponent(batter)
  const encBowler = encodeURIComponent(bowler)
  const { data } = await apiClient.get<MatchupResponse>(`/scouting/matchup/${scope}/${encBatter}/${encBowler}`)
  return data
}
