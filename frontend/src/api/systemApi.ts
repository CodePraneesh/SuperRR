import { apiClient } from './client'
import type { HealthResponse } from '../types/common'

export async function getSystemHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}
