export const SEVERITY_COLOR = {
  none:     'text-gray-400',
  low:      'text-green-400',
  medium:   'text-yellow-400',
  high:     'text-orange-400',
  critical: 'text-red-500',
}

export const SEVERITY_BG = {
  none:     'bg-gray-800',
  low:      'bg-green-900/40 border border-green-700',
  medium:   'bg-yellow-900/40 border border-yellow-700',
  high:     'bg-orange-900/40 border border-orange-700',
  critical: 'bg-red-900/40 border border-red-600',
}

export const CREDIT_COLOR = {
  NORMAL:   'text-green-400',
  ELEVATED: 'text-yellow-400',
  HIGH:     'text-orange-400',
  CRITICAL: 'text-red-500',
}

export function fmtUSD(val) {
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`
  if (val >= 1_000)     return `$${(val / 1_000).toFixed(1)}K`
  return `$${val.toFixed(0)}`
}

export function fmtTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString()
}

export function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

export function scoreColor(score) {
  if (score >= 0.8) return '#ef4444'
  if (score >= 0.65) return '#f97316'
  if (score >= 0.4) return '#f59e0b'
  return '#22c55e'
}
