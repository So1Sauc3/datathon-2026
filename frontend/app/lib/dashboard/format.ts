export type ValueFormat = 'money' | 'pct' | 'signedPct' | 'number' | 'index' | 'count'

/** Compact dollars for a 50px stat: $1.61M, $36k, $1,259. */
export function compactMoney(n: number): string {
  const sign = n < 0 ? '-' : ''
  const amount = Math.abs(n)
  if (amount >= 1_000_000) {
    const millions = amount / 1_000_000
    const digits = millions >= 10 ? 1 : 2
    return `${sign}$${millions.toFixed(digits)}M`
  }
  if (amount >= 10_000) return `${sign}$${Math.round(amount / 1000)}k`
  if (amount >= 1000) return `${sign}$${Math.round(amount).toLocaleString('en-US')}`
  return `${sign}$${Math.round(amount)}`
}

export function compactCount(n: number): string {
  const sign = n < 0 ? '-' : ''
  const amount = Math.abs(n)
  if (amount >= 1_000_000) {
    const millions = amount / 1_000_000
    const digits = millions >= 100 ? 0 : 1
    return `${sign}${millions.toFixed(digits)}M`
  }
  if (amount >= 10_000) return `${sign}${Math.round(amount / 1000)}k`
  if (amount >= 1000) return `${sign}${Math.round(amount).toLocaleString('en-US')}`
  return `${sign}${Math.round(amount)}`
}

export function pct(n: number, digits = 1): string {
  return `${(n * 100).toFixed(digits)}%`
}

export function signedPct(n: number, digits = 1): string {
  const value = n * 100
  const body = value.toFixed(digits)
  return `${value > 0 ? '+' : ''}${body}%`
}

export function multiple(n: number, digits = 2): string {
  return `${n.toFixed(digits)}x`
}

export function formatValue(n: number, format: ValueFormat, digits?: number): string {
  if (!Number.isFinite(n)) return ''
  switch (format) {
    case 'money':
      return compactMoney(n)
    case 'pct':
      return pct(n, digits ?? 0)
    case 'signedPct':
      return signedPct(n, digits ?? 0)
    case 'index':
      return n.toFixed(digits ?? 2)
    case 'count':
      return compactCount(n)
    default:
      return n.toLocaleString('en-US', {
        minimumFractionDigits: digits ?? 0,
        maximumFractionDigits: digits ?? 0,
      })
  }
}

export function formatQ(q: number): string {
  if (q < 0.001) return '<0.001'
  if (q < 0.01) return q.toFixed(3)
  return q.toFixed(2)
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export function monthName(iso: string): string {
  const month = Number(String(iso).slice(5, 7))
  return MONTHS[month - 1] ?? String(iso)
}

export function dayKey(value: string): string {
  return String(value).slice(0, 10)
}
