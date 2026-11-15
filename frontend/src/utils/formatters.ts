export function formatScore(val: number | null | undefined, decimals = 2): string {
  if (val === null || val === undefined || isNaN(val)) return '—'
  return Number(val).toFixed(decimals)
}

export function formatPercent(val: number | null | undefined, decimals = 1): string {
  if (val === null || val === undefined || isNaN(val)) return '—'
  return `${Number(val).toFixed(decimals)}%`
}

export function formatNumber(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return '—'
  return Number(val).toLocaleString()
}

export function formatDelta(val: number | null | undefined, decimals = 2): string {
  if (val === null || val === undefined || isNaN(val)) return '—'
  const sign = val > 0 ? '+' : ''
  return `${sign}${Number(val).toFixed(decimals)}`
}
