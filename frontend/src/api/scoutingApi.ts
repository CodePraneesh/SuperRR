import { apiClient } from './client'
import type {
  ScoutingReportResponse,
  PressureExplanationResponse,
  AnalyticsQueryRequest,
  AnalyticsQueryResponse,
} from '../types/scouting'
import type { Scope, Role } from '../types/common'

export async function getScoutingReport(
  scope: Scope,
  role: Role,
  name: string
): Promise<ScoutingReportResponse> {
  const encodedName = encodeURIComponent(name)
  const { data } = await apiClient.get<ScoutingReportResponse>(`/scouting/report/${scope}/${role}/${encodedName}`)
  return data
}

export async function getPressureExplanation(
  scope: Scope,
  role: Role,
  name: string
): Promise<PressureExplanationResponse> {
  const encodedName = encodeURIComponent(name)
  const { data } = await apiClient.get<PressureExplanationResponse>(`/scouting/pressure/${scope}/${role}/${encodedName}`)
  return data
}

export async function askAnalyticsQuestion(
  request: AnalyticsQueryRequest
): Promise<AnalyticsQueryResponse> {
  const { data } = await apiClient.post<AnalyticsQueryResponse>('/scouting/ask', request)
  return data
}
