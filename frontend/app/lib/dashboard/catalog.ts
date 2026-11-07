export type QuestionId = 'q1' | 'q2' | 'q3' | 'q4' | 'q5'

export type MenuVariant = 'slate' | 'play' | 'back' | 'action' | 'collection'

export interface ClaimSlot {
  id: string
  label: string
  question: QuestionId
  dataFiles: readonly string[]
}

export interface MenuEntry {
  id: QuestionId | 'q6'
  label: string
  variant: MenuVariant
  to?: string
}

export interface ActionDef {
  id: string
  name: string
  unitCost: number
  limit: number
  excludes?: readonly string[]
}

export interface BudgetAction {
  action_type_id: string
  quantity: number
  cost: number
  funded: boolean
}

export interface BudgetFile {
  actions: BudgetAction[]
}

export const BUDGET = 100_000
export const TYPE_CAP = 3
export const GAME_DATA_FILE = 'budget.json'

export const MENU: readonly MenuEntry[] = [
  { id: 'q4', label: 'Players', variant: 'slate' },
  { id: 'q6', label: 'Play', variant: 'play', to: '/play' },
  { id: 'q2', label: 'Demand', variant: 'back' },
  { id: 'q3', label: 'Downtime', variant: 'action' },
  { id: 'q1', label: 'Machines', variant: 'collection' },
  { id: 'q5', label: 'Loyalty', variant: 'slate' },
]

export const CLAIMS: readonly ClaimSlot[] = [
  { id: 'Q1-manager-list', label: "Manager's 10", question: 'q1', dataFiles: ['machines.json', 'machine_day_slim.json', 'floor_map.json'] },
  { id: 'Q1-payout-anomaly', label: 'Anomaly M-1158', question: 'q1', dataFiles: ['machines.json', 'machine_day_slim.json'] },
  { id: 'Q1-luck', label: 'Luck', question: 'q1', dataFiles: ['machines.json', 'machine_day_slim.json'] },
  { id: 'Q1-location', label: 'Location', question: 'q1', dataFiles: ['machines.json', 'floor_map.json'] },
  { id: 'Q1-persistence', label: 'Persistence', question: 'q1', dataFiles: ['machines.json', 'machine_day_slim.json'] },
  { id: 'Q2-weekday', label: 'Weekdays', question: 'q2', dataFiles: ['demand.json'] },
  { id: 'Q2-events', label: 'Events', question: 'q2', dataFiles: ['demand.json'] },
  { id: 'Q2-renovation', label: 'Walkway', question: 'q2', dataFiles: ['zone_day.json', 'demand.json'] },
  { id: 'Q2-trend', label: 'Visitors', question: 'q2', dataFiles: ['demand.json'] },
  { id: 'Q2-weather', label: 'Weather', question: 'q2', dataFiles: ['demand.json'] },
  { id: 'Q3-total', label: 'Total', question: 'q3', dataFiles: ['downtime.json'] },
  { id: 'Q3-when', label: 'When', question: 'q3', dataFiles: ['downtime.json'] },
  { id: 'Q3-manufacturer', label: 'Manufacturer', question: 'q3', dataFiles: ['faults.json', 'downtime.json'] },
  { id: 'Q3-staffing', label: 'Staffing', question: 'q3', dataFiles: ['faults.json', 'downtime.json'] },
  { id: 'Q4-outcomes', label: 'Outcomes', question: 'q4', dataFiles: ['players.json', 'player_groups.json'] },
  { id: 'Q4-concentration', label: 'Concentration', question: 'q4', dataFiles: ['players.json', 'player_groups.json'] },
  { id: 'Q4-locals', label: 'Locals', question: 'q4', dataFiles: ['players.json', 'player_groups.json'] },
  { id: 'Q4-heavy-loss', label: 'Heavy Losses', question: 'q4', dataFiles: ['players.json', 'player_groups.json'] },
  { id: 'Q4-reconciliation', label: 'Reconciliation', question: 'q4', dataFiles: ['players.json'] },
  { id: 'Q5-change', label: 'Change', question: 'q5', dataFiles: ['comps.json'] },
  { id: 'Q5-cost', label: 'Cost', question: 'q5', dataFiles: ['comps.json'] },
  { id: 'Q5-liability', label: 'Liability', question: 'q5', dataFiles: ['comps.json'] },
]

/** Guide catalogue. Lease price is $2,500 plus $55 for each of 16 operating days. */
export const ACTIONS: readonly ActionDef[] = [
  { id: 'A-MOVE-MACHINE', name: 'Move one machine', unitCost: 1800, limit: 24 },
  { id: 'A-MOVE-BANK', name: 'Move a whole bank', unitCost: 9500, limit: 3 },
  { id: 'A-REPLACE-LEASE', name: 'Replace with a leased machine', unitCost: 3380, limit: 20 },
  { id: 'A-REPLACE-BUY', name: 'Replace with a purchased machine', unitCost: 22000, limit: 10 },
  { id: 'A-TECH-SHIFT', name: 'Add a technician to a shift', unitCost: 11520, limit: 3 },
  { id: 'A-PREVENTIVE', name: 'Preventive maintenance, one manufacturer', unitCost: 9000, limit: 3 },
  { id: 'A-INSPECT', name: 'Inspect a machine and verify its payout', unitCost: 1200, limit: 15 },
  { id: 'A-WAYFINDING', name: 'New signs for a zone', unitCost: 7500, limit: 2 },
  { id: 'A-COMP-PILOT', name: 'Comp policy pilot with a control group', unitCost: 4000, limit: 1, excludes: ['A-COMP-CHANGE'] },
  { id: 'A-COMP-CHANGE', name: 'Change the comp rate floor-wide', unitCost: 1500, limit: 1, excludes: ['A-COMP-PILOT'] },
  { id: 'A-PROMO', name: 'Promotion weekend', unitCost: 15000, limit: 2 },
  { id: 'A-SURVEY', name: 'Bigger guest survey', unitCost: 3500, limit: 1 },
  { id: 'A-HOLD', name: 'Keep the budget', unitCost: 0, limit: 1 },
]

const actionsById = new Map(ACTIONS.map(action => [action.id, action]))

export function claimsFor(question: QuestionId) {
  return CLAIMS.filter(claim => claim.question === question)
}

export function claimById(id: string) {
  return CLAIMS.find(claim => claim.id === id)
}

export function actionById(id: string) {
  return actionsById.get(id)
}

export function formatDollars(amount: number) {
  return `$${Math.round(amount).toLocaleString('en-US')}`
}

/** Spending cards match the funded rows in budget.json. A $0 keep card does not count. */
export function portfolioMatches(playedIds: readonly string[], target: Readonly<Record<string, number>>) {
  const counts = new Map<string, number>()
  for (const id of playedIds) {
    const action = actionById(id)
    if (!action || action.unitCost <= 0) continue
    counts.set(id, (counts.get(id) ?? 0) + 1)
  }
  const targetIds = Object.keys(target)
  if (counts.size !== targetIds.length) return false
  return targetIds.every(id => counts.get(id) === target[id])
}
