import { claimById } from './catalog'

const cache = new Map<string, Promise<unknown>>()

/** Fetch one public JSON file. Repeated calls share the same promise. */
export function loadJson(file: string): Promise<unknown> {
  const pending = cache.get(file)
  if (pending) return pending
  const next = $fetch(`/data/${file}`) as Promise<unknown>
  cache.set(file, next)
  return next
}

/** Files a board needs. The machine-day extract stays unloaded; the scorecard is the full-window aggregate. */
export function filesFor(claimId: string): string[] {
  const listed = claimById(claimId)?.dataFiles ?? []
  const extra = claimId === 'Q6-portfolio'
    ? ['budget.json', 'forecast.json', 'demand.json', 'claims.json']
    : ['claims.json']
  return [...new Set([...listed, ...extra])].filter(file => file !== 'machine_day_slim.json')
}
