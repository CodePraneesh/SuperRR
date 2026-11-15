import axios, { AxiosError } from 'axios'

// Prefer explicit environment variable, fallback to direct port 8000
const API_BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Extract clean human-friendly error messages
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{ detail?: string; error_type?: string }>
    if (axiosErr.response?.data?.detail) {
      return axiosErr.response.data.detail
    }
    if (axiosErr.message === 'Network Error') {
      return 'Unable to reach SupeRR backend at 127.0.0.1:8000. Please ensure the FastAPI server is running.'
    }
    return axiosErr.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred while communicating with the backend.'
}
