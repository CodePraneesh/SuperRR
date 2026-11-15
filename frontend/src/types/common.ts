export type Scope = 'IPL' | 'T20I'
export type Role = 'Batter' | 'Bowler'

export interface HealthResponse {
  status: string
  version: string
  stores_loaded: boolean
  offline_mode: boolean
  tier_available: string
  data_dir: string
  timestamp: string
}

export interface ApiError {
  detail: string
  error_type?: string
  status_code?: number
}
