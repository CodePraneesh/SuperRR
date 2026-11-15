import { apiClient } from './client'
import type { CohortListResponse, PlayerProfileResponse, ContextualSplitsResponse } from '../types/player'
import type { Scope, Role } from '../types/common'

export interface GetCohortOptions {
  official_only?: boolean
  confidence_tier?: string
  limit?: number
  offset?: number
}

export async function getCohortPlayers(
  scope: Scope,
  role: Role,
  options: GetCohortOptions = {}
): Promise<CohortListResponse> {
  const { data } = await apiClient.get<CohortListResponse>(`/players/${scope}/${role}`, {
    params: options,
  })
  return data
}

export async function getPlayerProfile(
  scope: Scope,
  role: Role,
  name: string
): Promise<PlayerProfileResponse> {
  const encodedName = encodeURIComponent(name)
  const { data } = await apiClient.get<PlayerProfileResponse>(`/players/${scope}/${role}/${encodedName}`)
  return data
}

export async function getPlayerSplits(
  scope: Scope,
  role: Role,
  name: string
): Promise<ContextualSplitsResponse> {
  const encodedName = encodeURIComponent(name)
  const { data } = await apiClient.get<ContextualSplitsResponse>(`/players/${scope}/${role}/${encodedName}/splits`)
  return data
}
