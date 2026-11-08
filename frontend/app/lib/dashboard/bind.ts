import { chartTheme } from '~/lib/d3/theme'
import {
  emptyBoard,
  type BoardBinding,
  type ChartSpec,
} from './charts'
import {
  compactMoney,
  dayKey,
  formatQ,
  monthName,
  multiple,
  pct,
  signedPct,
} from './format'

type Rec = Record<string, any>
type Pack = Record<string, any>

const play = chartTheme.play
const action = chartTheme.action
const back = chartTheme.back
const collection = chartTheme.collection
const slate = chartTheme.slate

const WEEK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const ZONE: Record<string, string> = {
  'Z-B40': 'Back Forty',
  'Z-GAR': 'Garage',
  'Z-HL': 'High limit',
  'Z-HTL': 'Hotel',
  'Z-BAR': 'Bar',
  'Z-PIT': 'Center Pit',
  'Z-ENT': 'Entrance',
}

const ACTION: Record<string, string> = {
  'A-INSPECT': 'Inspect',
  'A-MOVE-MACHINE': 'Move',
  'A-PROMO': 'Promo',
  'A-TECH-SHIFT': 'Technician',
  'A-PREVENTIVE': 'Preventive',
  'A-WAYFINDING': 'Signs',
  'A-COMP-PILOT': 'Comp pilot',
  'A-COMP-CHANGE': 'Comp change',
  'A-MOVE-BANK': 'Move bank',
  'A-SURVEY': 'Survey',
  'A-REPLACE-LEASE': 'Lease',
  'A-REPLACE-BUY': 'Buy',
}

function table(pack: Pack, file: string, key: string): Rec[] {
  return pack[file][key] as Rec[]
}

function columnRows(table: Record<string, unknown[]>): Rec[] {
  const keys = Object.keys(table)
  const count = (table[keys[0]!] ?? []).length
  return Array.from({ length: count }, (_, index) => {
    const row: Rec = {}
    for (const key of keys) row[key] = (table[key] as unknown[])[index]
    return row
  })
}

function mean(values: number[]): number {
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

function pearson(xs: number[], ys: number[]): number {
  const n = xs.length
  const mx = mean(xs)
  const my = mean(ys)
  let num = 0
  let dx = 0
  let dy = 0
  for (let index = 0; index < n; index++) {
    const a = xs[index]! - mx
    const b = ys[index]! - my
    num += a * b
    dx += a * a
    dy += b * b
  }
  return num / Math.sqrt(dx * dy)
}

function claimNote(pack: Pack, id: string): string {
  const claim = (pack['claims.json'] as Rec[]).find(item => item.id === id)
  if (!claim) return ''
  return `${claim.result} ${claim.alternative} ${claim.limitation}`
}

function dollars(n: number): string {
  const sign = n < 0 ? '-' : ''
  return `${sign}$${Math.round(Math.abs(n)).toLocaleString('en-US')}`
}

function monthTicks(dates: string[]): string[] {
  let last = ''
  return dates.map((value) => {
    const month = dayKey(value).slice(0, 7)
    if (month === last) return ''
    last = month
    return monthName(value)
  })
}

function onOrAfter(dates: string[], day: string): number | undefined {
  const index = dates.findIndex(value => dayKey(value) >= day)
  return index < 0 ? undefined : index
}

function histogram(values: number[], start: number, step: number, bins: number): number[] {
  const counts = Array.from({ length: bins }, () => 0)
  for (const value of values) {
    let index = Math.floor((value - start) / step)
    if (index < 0) index = 0
    if (index >= bins) index = bins - 1
    counts[index]! += 1
  }
  return counts
}

function shortEvent(name: string): string {
  if (name.startsWith('Super Bowl')) return 'Super Bowl'
  if (name.startsWith('Gilded Ace Winter')) return 'Winter slots'
  if (name.startsWith('College')) return 'College hoops'
  if (name.startsWith('Gilded Ace Locals')) return 'Locals week'
  if (name.startsWith('EDC')) return 'EDC'
  if (name.startsWith('NAB')) return 'NAB'
  if (name.startsWith('Cinema')) return 'CinemaCon'
  return name
}

function stepSeries(daily: Rec[], row: Rec): number[] {
  const pre = daily.filter(item => item.post === 0)
  const middle = mean(pre.map(item => item.t))
  const slope = row.pre_trend_per_30d / 30
  return daily.map(item => row.pre_mean + slope * (item.t - middle) + (item.post ? row.level_change : 0))
}

export function bindBoard(claimId: string, pack: Pack): BoardBinding {
  switch (claimId) {
    case 'Q1-manager-list':
      return bindManager(pack)
    case 'Q1-payout-anomaly':
      return bindAnomaly(pack)
    case 'Q1-luck':
      return bindLuck(pack)
    case 'Q1-location':
      return bindLocation(pack)
    case 'Q1-persistence':
      return bindPersistence(pack)
    case 'Q2-weekday':
      return bindWeekday(pack)
    case 'Q2-events':
      return bindEvents(pack)
    case 'Q2-renovation':
      return bindRenovation(pack)
    case 'Q2-trend':
      return bindTrend(pack)
    case 'Q2-weather':
      return bindWeather(pack)
    case 'Q3-total':
      return bindDowntime(pack)
    case 'Q3-when':
      return bindWhen(pack)
    case 'Q3-manufacturer':
      return bindMaker(pack)
    case 'Q3-staffing':
      return bindStaff(pack)
    case 'Q4-outcomes':
      return bindOutcomes(pack)
    case 'Q4-concentration':
      return bindConcentration(pack)
    case 'Q4-locals':
      return bindLocals(pack)
    case 'Q4-heavy-loss':
      return bindTail(pack)
    case 'Q4-reconciliation':
      return bindReconcile(pack)
    case 'Q5-change':
      return bindChange(pack)
    case 'Q5-cost':
      return bindCost(pack)
    case 'Q5-liability':
      return bindLiability(pack)
    case 'Q6-portfolio':
      return bindPortfolio(pack)
    default:
      return emptyBoard()
  }
}

function bindManager(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const scorecard = table(pack, 'machines.json', 'scorecard')
  const manager = table(pack, 'machines.json', 'manager_list')
  const byId = new Map(scorecard.map(row => [row.machine_id, row]))
  const listed = manager.map(row => byId.get(row.machine_id)).filter(Boolean) as Rec[]
  const inBack = listed.filter(row => row.zone_id === 'Z-B40').length
  const lowHold = listed.filter(row => row.theo_hold <= 0.08).length
  const partial = listed.filter(row => row.days_on < 181).length
  const listAvail = mean(listed.map(row => row.availability))
  const floorAvail = mean(scorecard.map(row => row.availability))
  board.stat['In Back Forty'] = String(inBack)
  board.stat['Low-hold configs'] = String(lowHold)
  board.stat['Partial window'] = String(partial)
  board.stat.Availability = `${pct(listAvail)} vs ${pct(floorAvail)}`
  board.rank["Manager's bottom 10"] = manager.map((row) => {
    const machine = byId.get(row.machine_id)
    return { label: row.machine_id, left: compactMoney(machine.house_win), right: compactMoney(machine.theo) }
  })
  const parts = [
    ['Ref', 'wf_reference', slate],
    ['Window', 'wf_partial_window', action],
    ['Down', 'wf_downtime', slate],
    ['Games', 'wf_game_mix', action],
    ['Place', 'wf_location', action],
    ['Machine', 'wf_machine', collection],
    ['Luck', 'wf_luck', back],
  ] as const
  let run = 0
  const y0: number[] = []
  const y1: number[] = []
  const colors: string[] = []
  for (const [, key, color] of parts) {
    const delta = listed.reduce((sum, row) => sum + row[key], 0)
    y0.push(delta >= 0 ? run : run + delta)
    y1.push(delta >= 0 ? run + delta : run)
    colors.push(color)
    run += delta
  }
  const house = listed.reduce((sum, row) => sum + row.house_win, 0)
  y0.push(Math.min(0, house))
  y1.push(Math.max(0, house))
  colors.push(play)
  board.chart['House win waterfall'] = {
    kind: 'bar',
    categories: ['Ref', 'Window', 'Down', 'Games', 'Place', 'Machine', 'Luck', 'Won'],
    series: [],
    waterfall: { y0, y1, color: colors },
    format: 'money',
    aria: 'Waterfall of the bottom 10: game mix and location, not downtime, explain the shortfall versus a full-window floor-average machine.',
  }
  const drivers = new Map<string, number>()
  for (const row of manager) drivers.set(row.primary_driver, (drivers.get(row.primary_driver) ?? 0) + 1)
  const driverColor: Record<string, string> = { 'game mix': back, 'partial window': slate, 'payout anomaly': action }
  board.chart['Primary driver'] = {
    kind: 'donut',
    slices: [...drivers.entries()].map(([label, value]) => ({ label, value, color: driverColor[label] ?? play })),
    format: 'number',
    aria: 'Primary driver of the manager bottom 10. Game mix is the largest share. One machine is a payout anomaly.',
  }
  board.chart['Floor position'] = managerHeat(pack, listed)
  board.note.Finding = claimNote(pack, 'Q1-manager-list')
  return board
}

function managerHeat(pack: Pack, listed: Rec[]): ChartSpec {
  const floor = pack['floor_map.json'] as Rec[]
  const slots = floor.filter(node => node.node_type === 'slot')
  const xs = slots.map(slot => slot.x_m as number)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const bins = 6
  const zones = ['Z-B40', 'Z-GAR', 'Z-HL', 'Z-HTL', 'Z-BAR', 'Z-PIT', 'Z-ENT']
  const values = zones.map(() => Array.from({ length: bins }, () => 0))
  const at = new Map(slots.map(slot => [slot.location_id, slot]))
  for (const machine of listed) {
    const slot = at.get(machine.location_id)
    if (!slot) continue
    const row = zones.indexOf(slot.zone_id)
    const span = maxX - minX || 1
    const col = Math.min(bins - 1, Math.floor(((slot.x_m - minX) / span) * bins))
    if (row >= 0) values[row]![col]! += 1
  }
  return {
    kind: 'heatmap',
    rows: zones.map(zone => ZONE[zone] ?? zone),
    cols: Array.from({ length: bins }, (_, index) => `${Math.round(minX + (index / bins) * (maxX - minX))}m`),
    values,
    format: 'number',
    accent: 'action',
    aria: 'Where the bottom 10 sit on the floor. The mass is in the Back Forty.',
  }
}

function bindAnomaly(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const scorecard = table(pack, 'machines.json', 'scorecard')
  const monthly = table(pack, 'machines.json', 'anomaly_monthly')
  const machine = scorecard.find(row => row.payout_anomaly) ?? scorecard[0]
  board.pair['Hit rate'] = [pct(machine.hit_rate), pct(machine.hit_expected)]
  board.pair.Hold = [pct(machine.hold), pct(machine.theo_hold)]
  board.stat['Hit-rate z'] = String(Math.round(machine.hit_z))
  board.stat['Luck z'] = machine.luck_z.toFixed(1)
  board.stat['Below theo'] = compactMoney(-machine.luck)
  board.chart['Monthly hit rate vs configured'] = {
    kind: 'line',
    labels: monthly.map(row => monthName(row.month)),
    series: [
      { name: 'Hit rate', values: monthly.map(row => row.hit_rate), color: action },
      { name: 'Configured', values: monthly.map(row => row.hit_expected), color: slate, dash: true },
    ],
    format: 'pct',
    digits: 0,
    aria: `${machine.machine_id} hit rate stays near 39 percent in every month, against a configured 31 percent. A lead to inspect the paytable, not proof of wrongdoing.`,
  }
  const sorted = [...scorecard].sort((a, b) => a.hit_z - b.hit_z)
  board.chart['Hit-rate z across machines'] = {
    kind: 'scatter',
    points: sorted.map((row, index) => ({
      x: index,
      y: row.hit_z,
      color: row.payout_anomaly ? action : slate,
    })),
    formatX: 'number',
    formatY: 'number',
    digitsY: 0,
    xLabel: 'Machines, low to high',
    yLabel: 'Hit z',
    aria: `Hit-rate z for all ${scorecard.length} machines. ${machine.machine_id} is the point near 124. The rest sit near zero.`,
  }
  board.note.Finding = claimNote(pack, 'Q1-payout-anomaly')
  return board
}

function bindLuck(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const scorecard = table(pack, 'machines.json', 'scorecard')
  const summary = pack['machines.json'].summary
  const expected = Math.round(0.0455 * summary.machines)
  board.pair['Beyond |z| > 2'] = [String(summary.beyond_2sd), String(expected)]
  board.stat.Significant = String(summary.luck_sig)
  board.stat.Machines = String(summary.machines)
  const start = -5
  const step = 0.5
  const bins = 20
  const counts = histogram(scorecard.map(row => row.luck_z), start, step, bins)
  board.chart['Luck z distribution'] = {
    kind: 'bar',
    categories: counts.map((_, index) => (index % 4 === 0 ? String(start + index * step) : '')),
    series: [{
      name: 'Machines',
      values: counts,
      color: slate,
      colors: counts.map((_, index) => (Math.abs(start + (index + 0.5) * step) > 2 ? action : slate)),
    }],
    format: 'number',
    tickEvery: 4,
    aria: 'Luck z across machines. Red bars are beyond absolute value 2, about as many as chance predicts.',
  }
  const tail = [...scorecard].sort((a, b) => Math.abs(b.luck_z) - Math.abs(a.luck_z))
  board.rank['Largest |z|'] = tail.map(row => ({
    label: row.machine_id,
    left: row.luck_z.toFixed(1),
    right: formatQ(row.luck_q),
  }))
  board.chart['House win vs theo'] = {
    kind: 'scatter',
    points: scorecard.map(row => ({
      x: row.theo,
      y: row.house_win,
      color: row.payout_anomaly ? action : slate,
    })),
    formatX: 'money',
    formatY: 'money',
    xLabel: 'Theo',
    yLabel: 'House win',
    parity: true,
    aria: 'House win against theo. The slate line is parity. The red point is the payout anomaly.',
  }
  board.chart['Luck z by machine'] = {
    kind: 'interval',
    rows: tail.slice(0, 8).map(row => ({ label: row.machine_id, low: row.luck_z, mid: row.luck_z, high: row.luck_z })),
    format: 'number',
    digits: 1,
    guides: [-2, 2],
    aria: 'Largest luck z scores. Guides at -2 and 2. One machine remains significant after correction, and it is the hit-rate case.',
  }
  return board
}

function bindLocation(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const zones = [...table(pack, 'machines.json', 'zone_factors')].sort((a, b) => a.zone_factor - b.zone_factor)
  const scorecard = table(pack, 'machines.json', 'scorecard')
  const theo = new Map<string, number[]>()
  for (const row of scorecard) {
    const list = theo.get(row.zone_id) ?? []
    list.push(row.theo_per_hour)
    theo.set(row.zone_id, list)
  }
  const low = zones[0]
  const high = zones[zones.length - 1]
  board.stat['Lowest zone'] = `${ZONE[low.zone_id] ?? low.zone_id} ${low.zone_factor.toFixed(2)}`
  board.stat['Highest zone'] = `${ZONE[high.zone_id] ?? high.zone_id} ${high.zone_factor.toFixed(2)}`
  board.stat.Zones = String(zones.length)
  board.chart['Zone factor'] = {
    kind: 'hbar',
    categories: zones.map(zone => ZONE[zone.zone_id] ?? zone.zone_id),
    values: zones.map(zone => zone.zone_factor),
    colors: zones.map(zone => (zone.zone_id === 'Z-B40' ? action : play)),
    format: 'index',
    digits: 2,
    aria: 'Zone factor after game mix is divided out. Back Forty is 0.65. The entrance is 1.19.',
  }
  board.rank.Zones = zones.map(zone => ({
    label: ZONE[zone.zone_id] ?? zone.zone_id,
    left: zone.zone_factor.toFixed(2),
    right: compactMoney(mean(theo.get(zone.zone_id) ?? [0])),
  }))
  const banks = new Map<string, Map<string, number[]>>()
  for (const row of scorecard) {
    const zone = banks.get(row.zone_id) ?? new Map<string, number[]>()
    const list = zone.get(row.bank_id) ?? []
    list.push(row.theo_per_hour)
    zone.set(row.bank_id, list)
    banks.set(row.zone_id, zone)
  }
  const means = zones.map(zone => [...(banks.get(zone.zone_id)?.values() ?? [])].map(list => mean(list)).sort((a, b) => a - b))
  const width = Math.max(...means.map(list => list.length))
  board.chart['Floor map'] = {
    kind: 'heatmap',
    rows: zones.map(zone => ZONE[zone.zone_id] ?? zone.zone_id),
    cols: Array.from({ length: width }, (_, index) => (index % 2 === 0 ? String(index + 1) : '')),
    values: means.map(list => Array.from({ length: width }, (_, index) => list[index] ?? null)),
    format: 'money',
    accent: 'play',
    aria: 'Theo per available hour by bank within each zone. Banks are ordered low to high. Back Forty stays dark.',
  }
  board.note.Finding = claimNote(pack, 'Q1-location')
  return board
}

function bindPersistence(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const scorecard = table(pack, 'machines.json', 'scorecard')
  const weak = table(pack, 'machines.json', 'truly_weak')
  const summary = pack['machines.json'].summary
  const persistentIds = new Set(weak.filter(row => row.persistent_weak).map(row => row.machine_id))
  const paired = scorecard.filter(row => row.effect_h1 != null && row.effect_h2 != null)
  const persistent = paired.filter(row => persistentIds.has(row.machine_id))
  board.pair['Machine effect'] = [signedPct(mean(persistent.map(row => row.effect_h1))), signedPct(mean(persistent.map(row => row.effect_h2)))]
  board.stat.Correlation = summary.effect_corr.toFixed(2)
  board.stat.Persistent = String(persistent.length)
  board.chart['Jan-Mar vs Apr-Jun effect'] = {
    kind: 'scatter',
    points: paired.map(row => ({
      x: row.effect_h1,
      y: row.effect_h2,
      color: persistentIds.has(row.machine_id) ? action : slate,
    })),
    formatX: 'signedPct',
    formatY: 'signedPct',
    xLabel: 'Jan-Mar',
    yLabel: 'Apr-Jun',
    parity: true,
    aria: 'Machine effect in the first quarter against the second. Correlation is 0.79. Red points are the persistent bottom decile.',
  }
  const ordered = [...persistent].sort((a, b) => (a.effect_h1 + a.effect_h2) - (b.effect_h1 + b.effect_h2))
  board.rank['Persistent bottom decile'] = ordered.map(row => ({
    label: row.machine_id,
    left: signedPct(row.effect_h1, 0),
    right: signedPct(row.effect_h2, 0),
  }))
  board.chart['Effect by quarter'] = {
    kind: 'interval',
    rows: ordered.slice(0, 8).map(row => ({
      label: row.machine_id,
      low: row.effect_h1,
      mid: (row.effect_h1 + row.effect_h2) / 2,
      high: row.effect_h2,
    })),
    format: 'signedPct',
    guides: [0],
    aria: 'Persistent bottom-decile machines. The span runs from the Jan-Mar effect to the Apr-Jun effect.',
  }
  board.note.Finding = claimNote(pack, 'Q1-persistence')
  return board
}

function bindWeekday(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const weekday = table(pack, 'demand.json', 'weekday')
  const daily = table(pack, 'demand.json', 'daily')
  const byDay = new Map(weekday.map(row => [row.local_weekday, row]))
  const sat = byDay.get('Sat')
  const tue = byDay.get('Tue')
  board.pair['Peak vs trough'] = [compactMoney(sat.coin_in), compactMoney(tue.coin_in)]
  board.stat['Weekend lift'] = multiple(sat.coin_in / tue.coin_in)
  const days = weekday.map(row => row.days)
  board.stat['Ordinary days'] = `${Math.min(...days)}–${Math.max(...days)}`
  const ordered = WEEK.map(day => byDay.get(day))
  board.chart['Mean coin-in by weekday'] = {
    kind: 'bar',
    categories: WEEK,
    series: [{ name: 'Coin-in', values: ordered.map(row => row.coin_in), color: play }],
    format: 'money',
    aria: 'Mean coin-in by weekday on ordinary days. Saturday is 1.60 times Tuesday. Event and holiday days are excluded.',
  }
  board.rank['Weekday ranking'] = [...ordered].sort((a, b) => b.coin_in - a.coin_in).map(row => ({
    label: row.local_weekday,
    left: compactMoney(row.coin_in),
    right: row.index_vs_mean.toFixed(2),
  }))
  const months = [...new Set(daily.map(row => row.month as string))]
  board.chart['Weekday x hour'] = {
    kind: 'heatmap',
    rows: WEEK,
    cols: months.map(month => monthName(month)),
    values: WEEK.map(day => months.map((month) => {
      const rows = daily.filter(item => item.local_weekday === day && item.month === month)
      return rows.length ? mean(rows.map(item => item.coin_in)) : null
    })),
    format: 'money',
    accent: 'play',
    aria: 'Mean daily coin-in by weekday and month. The export has gaming days, not hours, so the columns are months.',
  }
  board.note.Finding = claimNote(pack, 'Q2-weekday')
  return board
}

function bindEvents(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const events = [...table(pack, 'demand.json', 'events')].sort((a, b) => b.lift_mean - a.lift_mean)
  const daily = table(pack, 'demand.json', 'daily')
  const dates = daily.map(row => dayKey(row.gaming_date))
  board.stat.Events = String(events.length)
  board.stat['Best lift'] = signedPct(events[0].lift_mean)
  board.stat['Extra coin-in'] = compactMoney(events.reduce((sum, row) => sum + row.extra_coin_in, 0))
  board.stat['Event days'] = String(events.reduce((sum, row) => sum + row.days, 0))
  board.rank['Lift by event'] = events.map(row => ({
    label: shortEvent(row.name),
    left: compactMoney(row.extra_coin_in),
    right: signedPct(row.lift_mean, 0),
  }))
  board.chart['Daily coin-in with event windows'] = {
    kind: 'line',
    labels: monthTicks(dates),
    series: [{ name: 'Coin-in', values: daily.map(row => row.coin_in), color: play }],
    format: 'money',
    shades: events.map(row => ({
      from: dates.findIndex(date => date >= dayKey(row.start_date)),
      to: dates.findIndex(date => date >= dayKey(row.end_date)),
    })).filter(shade => shade.from >= 0 && shade.to >= shade.from),
    tickEvery: 1,
    aria: 'Daily coin-in with each event window shaded. Lifts differ, and the property promotions are the ones used to price a promotion weekend.',
  }
  board.chart['Lift vs event length'] = {
    kind: 'scatter',
    points: events.map(row => ({
      x: row.days,
      y: row.lift_mean,
      color: row.event_type === 'property_promotion' ? back : play,
      label: shortEvent(row.name),
    })),
    formatX: 'number',
    formatY: 'signedPct',
    digitsY: 0,
    xLabel: 'Days',
    yLabel: 'Lift',
    aria: 'Event lift against length. Orange points are the property\'s own promotions. Each event happens once.',
  }
  board.note.Finding = claimNote(pack, 'Q2-events')
  return board
}

function bindRenovation(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const summary = pack['demand.json'].summary
  const daily = table(pack, 'demand.json', 'renovation_daily')
  const dates = daily.map(row => dayKey(row.gaming_date))
  const zone = columnRows(pack['zone_day.json'])
  board.pair['Coin-in change'] = [signedPct(summary.closure_effect), signedPct(summary.post_effect)]
  board.stat['Lost coin-in'] = compactMoney(summary.lost_coin_in_closure)
  board.stat['Lost theo'] = compactMoney(summary.lost_theo_closure)
  const closure = daily.findIndex(row => row.period === 'closure')
  const closureEnd = daily.findLastIndex(row => row.period === 'closure')
  board.chart['Back Forty vs control zones'] = {
    kind: 'area',
    labels: monthTicks(dates),
    series: [{ name: 'Back Forty / control', values: daily.map(row => row.ratio), color: action }],
    format: 'index',
    digits: 2,
    guide: 1,
    shades: closure >= 0 ? [{ from: closure, to: closureEnd }] : [],
    aria: 'Back Forty coin-in per machine divided by the control zones. The slate line is parity. The shaded span is the walkway closure.',
  }
  const periodOf = new Map(daily.map(row => [dayKey(row.gaming_date), row.period as string]))
  const entries = { pre: 0, closure: 0, post: 0 }
  for (const row of zone) {
    if (row.zone_id !== 'Z-B40' || row.entries_ok == null) continue
    const period = periodOf.get(dayKey(row.gaming_date)) as keyof typeof entries | undefined
    if (period) entries[period] += row.entries_ok
  }
  board.chart['Door-counter entries'] = {
    kind: 'bar',
    categories: ['Before', 'Closed', 'After'],
    series: [{ name: 'Entries', values: [entries.pre, entries.closure, entries.post], color: back, colors: [slate, action, back] }],
    format: 'count',
    aria: 'Back Forty door-counter entries before, during, and after the closure. Offline counters are already excluded.',
  }
  board.chart['Bootstrap intervals'] = {
    kind: 'interval',
    rows: [
      { label: 'Closed', low: summary.closure_lo, mid: summary.closure_effect, high: summary.closure_hi },
      { label: 'After', low: summary.post_lo, mid: summary.post_effect, high: summary.post_hi },
    ],
    format: 'signedPct',
    digits: 0,
    guides: [0],
    aria: 'Bootstrap 95 percent intervals for the Back Forty coin-in change versus the period before the closure.',
  }
  board.note.Finding = claimNote(pack, 'Q2-renovation')
  return board
}

function bindTrend(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const monthly = table(pack, 'demand.json', 'monthly')
  const peak = monthly.reduce((best, row) => (row.coin_in_per_day > best.coin_in_per_day ? row : best))
  const low = monthly.reduce((best, row) => (row.coin_in_per_day < best.coin_in_per_day ? row : best))
  const index = monthly.map(row => row.weekday_adjusted_index as number)
  const machines = monthly.map(row => row.active_machines as number)
  const yoy = monthly.map(row => row.visitor_yoy as number)
  board.stat['Peak month'] = `${monthName(peak.month)} ${compactMoney(peak.coin_in_per_day)}`
  board.stat['Low month'] = `${monthName(low.month)} ${compactMoney(low.coin_in_per_day)}`
  board.stat.Correlation = pearson(monthly.map(row => row.coin_in_per_day), monthly.map(row => row.visitors_per_day)).toFixed(2)
  board.chart['Coin-in per day by month'] = {
    kind: 'area',
    labels: monthly.map(row => monthName(row.month)),
    series: [{ name: 'Coin-in', values: monthly.map(row => row.coin_in_per_day), color: play }],
    format: 'money',
    aria: 'Coin-in per gaming day by month. February is the peak and June is the low. Six months only.',
  }
  board.stat['Adjusted index'] = `${Math.min(...index).toFixed(3)}–${Math.max(...index).toFixed(3)}`
  board.stat['Active machines'] = `${Math.round(Math.min(...machines))}–${Math.round(Math.max(...machines))}`
  board.stat['Visitors YoY'] = `${signedPct(Math.max(...yoy), 0)} to ${signedPct(Math.min(...yoy), 0)}`
  board.chart['Index vs LVCVA visitors'] = {
    kind: 'scatter',
    points: monthly.map(row => ({
      x: row.visitors_per_day,
      y: row.coin_in_per_day,
      color: play,
      label: monthName(row.month),
    })),
    formatX: 'count',
    formatY: 'money',
    xLabel: 'LVCVA visitors / day',
    yLabel: 'Coin-in / day',
    aria: 'Six months of coin-in per day against LVCVA visitors per day. Real city data, published after the window, and too few points to show a cause.',
  }
  board.chart['Convention attendance'] = {
    kind: 'bar',
    categories: monthly.map(row => monthName(row.month)),
    series: [{ name: 'Attendance', values: monthly.map(row => row.convention_attendance), color: back }],
    format: 'count',
    aria: 'LVCVA convention attendance by month. June is the low month for conventions as well as coin-in.',
  }
  return board
}

function bindWeather(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const summary = pack['demand.json'].summary
  const daily = table(pack, 'demand.json', 'daily')
  const weekday = table(pack, 'demand.json', 'weekday')
  const means = new Map(weekday.map(row => [row.local_weekday, row.coin_in as number]))
  const ordinary = daily.filter(row => !row.special && row.tmax_c != null)
  const residual = (row: Rec) => row.coin_in / (means.get(row.local_weekday) ?? row.coin_in) - 1
  const wet = ordinary.filter(row => row.prcp_mm > 0.5)
  const dry = ordinary.filter(row => row.prcp_mm <= 0.5)
  const jan = daily.filter(row => row.month === '2025-01' && row.tmax_c != null)
  const jun = daily.filter(row => row.month === '2025-06' && row.tmax_c != null)
  board.stat['Temp correlation'] = summary.corr_tmax.toFixed(2)
  board.stat['Rainy days'] = String(summary.wet_days)
  board.stat['Rain effect'] = signedPct(summary.wet_minus_dry)
  board.stat['Ordinary days'] = String(ordinary.length)
  board.stat['Seasonal trend'] = `${(mean(jun.map(row => row.tmax_c)) - mean(jan.map(row => row.tmax_c))).toFixed(0)} C`
  board.chart['Demand residual vs max temp'] = {
    kind: 'scatter',
    points: ordinary.map(row => ({
      x: row.tmax_c,
      y: residual(row),
      color: row.prcp_mm > 0.5 ? action : play,
    })),
    formatX: 'number',
    formatY: 'signedPct',
    digitsX: 0,
    digitsY: 0,
    xLabel: 'Max C',
    yLabel: 'Vs weekday',
    aria: 'Ordinary-day coin-in relative to that weekday mean, against max temperature. Correlation is about -0.08. Red points are rainy days.',
  }
  board.chart['Rainy vs dry days'] = {
    kind: 'bar',
    categories: ['Rain', 'Dry'],
    series: [{
      name: 'Residual',
      values: [mean(wet.map(residual)), mean(dry.map(residual))],
      color: play,
      colors: [action, slate],
    }],
    format: 'signedPct',
    digits: 0,
    aria: 'Mean coin-in residual on rainy days versus dry ordinary days.',
  }
  const dates = daily.map(row => dayKey(row.gaming_date))
  board.chart['Max temperature through the window'] = {
    kind: 'line',
    labels: monthTicks(dates),
    series: [{ name: 'Max C', values: daily.map(row => row.tmax_c), color: back }],
    format: 'number',
    digits: 0,
    aria: 'Daily max temperature rises from January to June, so a temperature correlation also carries the season.',
  }
  board.note.Finding = claimNote(pack, 'Q2-weather')
  return board
}

function bindDowntime(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const summary = pack['downtime.json'].summary
  const causes = table(pack, 'downtime.json', 'by_cause')
  const daily = table(pack, 'downtime.json', 'daily')
  const causeName: Record<string, string> = {
    fault_repair: 'Faults',
    install: 'Install',
    move: 'Moves',
    scheduled_maintenance: 'Upkeep',
  }
  const causeColor: Record<string, string> = {
    fault_repair: action,
    install: back,
    move: slate,
    scheduled_maintenance: collection,
  }
  board.stat['Machine-hours lost'] = Math.round(summary.down_hours).toLocaleString('en-US')
  board.stat['Share of schedule'] = pct(summary.down_share, 2)
  board.stat['Theo lost'] = compactMoney(summary.lost_theo)
  board.stat.Recovered = pct(summary.recovered_share, 0)
  board.chart['Downtime by cause'] = {
    kind: 'donut',
    slices: causes.map(row => ({ label: causeName[row.cause] ?? row.cause, value: row.down_hours, color: causeColor[row.cause] ?? slate })),
    format: 'number',
    aria: 'Downtime hours by cause. Fault repairs are almost the entire total.',
  }
  const weeks = new Map<string, { hours: number, day: string }>()
  for (const row of daily) {
    const day = dayKey(row.gaming_date)
    const date = new Date(`${day}T00:00:00Z`)
    const start = new Date(date)
    start.setUTCDate(date.getUTCDate() - date.getUTCDay())
    const key = start.toISOString().slice(0, 10)
    const bucket = weeks.get(key)
    if (bucket) bucket.hours += row.down_hours
    else weeks.set(key, { hours: row.down_hours, day })
  }
  const weekKeys = [...weeks.keys()].sort()
  board.chart['Machine-hours lost by week'] = {
    kind: 'bar',
    categories: weekKeys.map((key, index) => (index % 4 === 0 ? monthName(weeks.get(key)!.day) : '')),
    series: [{ name: 'Hours', values: weekKeys.map(key => weeks.get(key)!.hours), color: action }],
    format: 'number',
    tickEvery: 4,
    aria: 'Machine-hours lost by week.',
  }
  board.rank['Cause breakdown'] = causes.map(row => ({
    label: causeName[row.cause] ?? row.cause,
    left: Math.round(row.down_hours).toLocaleString('en-US'),
    right: compactMoney(row.lost_theo),
  }))
  const net = summary.lost_theo * (1 - summary.recovered_share)
  board.pair.Loss = [compactMoney(summary.lost_theo), compactMoney(net)]
  board.stat['Reconciliation gap'] = '$0'
  return board
}

function bindWhen(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const months = table(pack, 'downtime.json', 'by_month')
  const shifts = table(pack, 'downtime.json', 'by_shift')
  const hours = [...table(pack, 'downtime.json', 'by_hour')].sort((a, b) => a.local_hour - b.local_hour)
  const byShift = new Map(shifts.map(row => [row.shift, row]))
  const peak = months.reduce((best, row) => (row.lost_theo > best.lost_theo ? row : best))
  const low = months.reduce((best, row) => (row.lost_theo < best.lost_theo ? row : best))
  board.stat['Costliest month'] = `${monthName(peak.month)} ${compactMoney(peak.lost_theo)}`
  board.stat['Lowest month'] = `${monthName(low.month)} ${compactMoney(low.lost_theo)}`
  board.pair['Theo per downtime hour'] = [
    `$${byShift.get('swing').theo_per_down_hour.toFixed(2)}`,
    `$${byShift.get('grave').theo_per_down_hour.toFixed(2)}`,
  ]
  board.chart['Downtime cost by month'] = {
    kind: 'bar',
    categories: months.map(row => monthName(row.month)),
    series: [{ name: 'Theo', values: months.map(row => row.lost_theo), color: action }],
    format: 'money',
    aria: 'Theo lost to downtime by month. May is the costliest month and June is the lowest.',
  }
  const rate = new Map(hours.map(row => [row.local_hour as number, row.theo_per_down_hour as number]))
  const inShift = (name: string, hour: number) => {
    if (name === 'Day') return hour >= 6 && hour < 14
    if (name === 'Swing') return hour >= 14 && hour < 22
    return hour >= 22 || hour < 6
  }
  board.chart['Shift x weekday cost'] = {
    kind: 'heatmap',
    rows: ['Day', 'Swing', 'Grave'],
    cols: Array.from({ length: 24 }, (_, hour) => (hour % 3 === 0 ? String(hour) : '')),
    values: ['Day', 'Swing', 'Grave'].map(name => Array.from({ length: 24 }, (_, hour) => (inShift(name, hour) ? rate.get(hour) ?? null : null))),
    format: 'money',
    accent: 'action',
    aria: 'Theo per downtime hour by hour of day, split into the day, swing, and grave shifts. Swing hours are the expensive band. Columns are hours, not weekdays.',
  }
  board.chart['Hours vs theo per hour'] = {
    kind: 'scatter',
    points: months.map(row => ({
      x: row.down_hours,
      y: row.lost_theo / row.down_hours,
      color: play,
      label: monthName(row.month),
    })),
    formatX: 'number',
    formatY: 'money',
    digitsX: 0,
    xLabel: 'Hours',
    yLabel: '$ / hour',
    aria: 'Downtime hours against theo per downtime hour, one point per month.',
  }
  board.chart['Theo per downtime hour by hour of day'] = {
    kind: 'line',
    labels: hours.map(row => (row.local_hour % 3 === 0 ? String(row.local_hour) : '')),
    series: [{ name: '$ / hour', values: hours.map(row => row.theo_per_down_hour), color: action }],
    format: 'money',
    aria: 'Theo per downtime hour across the local hour of day. The swing shift, 14:00 to 22:00, is the high band.',
  }
  return board
}

function bindMaker(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const summary = pack['downtime.json'].summary
  const makers = table(pack, 'downtime.json', 'by_manufacturer')
  const monthly = table(pack, 'downtime.json', 'faults_month')
  const worst = makers.find(row => row.manufacturer === summary.worst_manufacturer) ?? makers[0]
  const machines = new Map(makers.map(row => [row.manufacturer, row.machines as number]))
  board.stat['Fault ratio'] = multiple(summary.excess_fault_ratio, 1)
  board.stat['Repair cost'] = dollars(worst.repair_cost / worst.machines)
  board.stat['Theo lost'] = dollars(worst.lost_theo_per_machine)
  board.rank.Manufacturers = makers.map(row => ({
    label: row.manufacturer,
    left: row.faults_per_machine_month.toFixed(2),
    right: row.down_hours_per_machine.toFixed(1),
  }))
  board.chart['Faults per machine-month'] = {
    kind: 'hbar',
    categories: makers.map(row => row.manufacturer),
    values: makers.map(row => row.faults_per_machine_month),
    colors: makers.map(row => (row.manufacturer === summary.worst_manufacturer ? action : play)),
    format: 'index',
    digits: 2,
    aria: `${summary.worst_manufacturer} fails about 2.9 times as often as the other manufacturers, per machine-month.`,
  }
  const months = [...new Set(monthly.map(row => row.month as string))]
  const names = makers.map(row => row.manufacturer as string)
  const colors = [action, play, collection]
  board.chart['Monthly fault rate by maker'] = {
    kind: 'line',
    labels: months.map(month => monthName(month)),
    series: names.map((name, index) => ({
      name,
      color: colors[index] ?? slate,
      values: months.map((month) => {
        const row = monthly.find(item => item.month === month && item.manufacturer === name)
        return row ? row.faults / (machines.get(name) ?? 1) : 0
      }),
    })),
    format: 'index',
    digits: 2,
    aria: 'Faults per machine by month and manufacturer. The gap is present in every month.',
  }
  const repeats = table(pack, 'downtime.json', 'by_machine').slice(0, 3).map(row => row.machine_id).join(', ')
  board.note.Finding = `${claimNote(pack, 'Q3-manufacturer')} Repeat-fault machines at the top of the list include ${repeats}.`
  return board
}

function bindStaff(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const summary = pack['downtime.json'].summary
  const faults = columnRows(pack['faults.json'])
  const staffing = table(pack, 'downtime.json', 'staffing')
  const short = faults.filter(row => row.understaffed)
  const full = faults.filter(row => !row.understaffed)
  const shortMean = mean(short.map(row => row.repair_hours))
  const fullMean = mean(full.map(row => row.repair_hours))
  const waitGap = mean(short.map(row => row.wait_hours)) - mean(full.map(row => row.wait_hours))
  board.pair['Mean repair time'] = [`${shortMean.toFixed(2)} h`, `${fullMean.toFixed(2)} h`]
  board.stat['Extra hours'] = `+${summary.staff_effect_h.toFixed(2)} h`
  board.stat['Short shifts'] = String(staffing.reduce((sum, row) => sum + row.short_days, 0))
  const bins = 12
  const shortShare = histogram(short.map(row => row.repair_hours), 0, 1, bins).map(count => count / short.length)
  const fullShare = histogram(full.map(row => row.repair_hours), 0, 1, bins).map(count => count / full.length)
  board.chart['Repair time distribution'] = {
    kind: 'area',
    labels: Array.from({ length: bins }, (_, index) => (index % 2 === 0 ? String(index) : '')),
    series: [
      { name: 'Full', values: fullShare, color: slate },
      { name: 'Short', values: shortShare, color: action },
    ],
    format: 'pct',
    zero: true,
    aria: 'Share of fault repairs by duration in hours. Short-staffed repairs, in red, sit to the right of fully staffed repairs.',
  }
  board.chart['Difference with 95% CI'] = {
    kind: 'interval',
    rows: [
      { label: 'Repair', low: summary.staff_lo, mid: summary.staff_effect_h, high: summary.staff_hi },
      { label: 'Wait', low: waitGap, mid: waitGap, high: waitGap },
    ],
    format: 'number',
    digits: 2,
    guides: [0],
    aria: 'Extra repair hours when the slot-tech shift is short-staffed, with the exported 95 percent interval. The wait gap is the observed difference in hours to start work.',
  }
  const months = [...new Set(staffing.map(row => row.month as string))]
  const shiftNames = ['day', 'swing', 'grave']
  board.chart['Short-staffed shift-days'] = {
    kind: 'heatmap',
    rows: ['Day', 'Swing', 'Grave'],
    cols: months.map(month => monthName(month)),
    values: shiftNames.map(shift => months.map((month) => {
      const row = staffing.find(item => item.month === month && item.shift === shift)
      return row ? row.short_days : 0
    })),
    format: 'number',
    accent: 'action',
    aria: 'Short-staffed slot-tech days by month and shift. The mass is the April day shift, the May day shift, and the May swing shift.',
  }
  board.note.Finding = claimNote(pack, 'Q3-staffing')
  return board
}

function bindOutcomes(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const summary = pack['players.json'].summary
  const deciles = table(pack, 'players.json', 'theo_deciles')
  const monthly = table(pack, 'players.json', 'monthly')
  const hold = -summary.net / summary.coin_in
  const theo = summary.theo / summary.coin_in
  board.stat['Card holders'] = Math.round(summary.players).toLocaleString('en-US')
  board.stat['Ahead share'] = pct(summary.ahead_share)
  board.pair.Hold = [pct(hold, 2), pct(theo, 2)]
  board.chart['Ahead share by theo decile'] = {
    kind: 'bar',
    categories: deciles.map(row => `D${row.theo_decile}`),
    series: [{
      name: 'Ahead',
      values: deciles.map(row => row.ahead),
      color: collection,
      colors: deciles.map((row, index) => (index === deciles.length - 1 ? action : collection)),
    }],
    format: 'pct',
    aria: 'Share of gamblers who finished ahead, by theo decile. It falls from about 34 percent in the lightest decile to about 10 percent in the heaviest.',
  }
  board.stat['Net result'] = compactMoney(summary.net)
  board.stat['Luck residual'] = compactMoney(summary.luck)
  board.stat['Card-only diners'] = Math.round(summary.players - summary.gamers).toLocaleString('en-US')
  board.chart['Wagered vs returned'] = {
    kind: 'area',
    labels: monthly.map(row => monthName(row.month)),
    series: [
      { name: 'Wagered', values: monthly.map(row => row.coin_in), color: play },
      { name: 'Returned', values: monthly.map(row => row.payout), color: back },
    ],
    format: 'money',
    zero: true,
    aria: 'Tracked coin-in and payout by month. Players get most of the wager back. The gap is the house hold.',
  }
  board.note.Finding = claimNote(pack, 'Q4-outcomes')
  return board
}

function lorenzSeries(rows: Rec[], metric: string): Rec[] {
  return rows.filter(row => row.metric === metric).sort((a, b) => a.population_share - b.population_share)
}

function bindConcentration(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const summary = pack['players.json'].summary
  const lorenz = table(pack, 'players.json', 'lorenz')
  const theo = lorenzSeries(lorenz, 'theo')
  const losses = lorenzSeries(lorenz, 'losses')
  const coin = lorenzSeries(lorenz, 'coin_in')
  const labels = theo.map((row, index) => (index === 0 || index === 50 || index === 100 ? `${Math.round(row.population_share * 100)}%` : ''))
  board.stat['Top 1% of theo'] = pct(summary.top1_theo, 0)
  board.stat['Top 10% of theo'] = pct(summary.top10_theo, 0)
  board.stat.Gini = summary.gini_theo.toFixed(2)
  board.chart['Lorenz curve'] = {
    kind: 'line',
    labels,
    series: [
      { name: 'Equality', values: theo.map(row => row.population_share), color: slate, dash: true },
      { name: 'Theo', values: theo.map(row => row.value_share), color: play },
      { name: 'Losses', values: losses.map(row => row.value_share), color: action },
      { name: 'Coin-in', values: coin.map(row => row.value_share), color: back },
    ],
    format: 'pct',
    zero: true,
    aria: 'Lorenz curves for tracked theo, losses, and coin-in. The slate diagonal is equality. Gini for theo is 0.75.',
  }
  const at = (share: number) => theo.reduce((best, row) => (
    Math.abs(row.population_share - share) < Math.abs(best.population_share - share) ? row : best
  )).value_share
  const shares = Array.from({ length: 10 }, (_, index) => at((index + 1) / 10) - at(index / 10))
  board.chart['Theo share by percentile'] = {
    kind: 'bar',
    categories: shares.map((_, index) => `D${index + 1}`),
    series: [{
      name: 'Theo',
      values: shares,
      color: play,
      colors: shares.map((_, index) => (index === shares.length - 1 ? action : play)),
    }],
    format: 'pct',
    aria: 'Share of tracked theo in each decile of players, from the lightest to the heaviest.',
  }
  board.rank['Gini by measure'] = [
    { label: 'Theo', left: summary.gini_theo.toFixed(2), right: pct(summary.top10_theo, 0) },
    { label: 'Losses', left: summary.gini_loss.toFixed(2), right: pct(summary.top10_loss, 0) },
    { label: 'Coin-in', left: summary.gini_coin_in.toFixed(2), right: pct(1 - coin.reduce((best, row) => (Math.abs(row.population_share - 0.9) < Math.abs(best.population_share - 0.9) ? row : best)).value_share, 0) },
  ]
  board.chart['Loss concentration'] = {
    kind: 'area',
    labels,
    series: [
      { name: 'Equality', values: losses.map(row => row.population_share), color: slate, dash: true },
      { name: 'Losses', values: losses.map(row => row.value_share), color: action },
    ],
    format: 'pct',
    zero: true,
    aria: 'Lorenz curve of tracked losses. The top 10 percent of losses are about 59 percent of the total.',
  }
  return board
}

function bindLocals(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const regions = table(pack, 'players.json', 'segments').filter(row => row.dimension === 'home_region')
  const local = regions.find(row => row.segment === 'Local')
  const ordered = [...regions].sort((a, b) => b.share_of_theo - a.share_of_theo)
  const colors = [action, play, back, slate]
  board.pair.Locals = [pct(local.share_of_players, 0), pct(local.share_of_theo, 0)]
  board.stat['Visits per local'] = local.visits_per_player.toFixed(1)
  board.stat['Net per local'] = dollars(local.net_per_player)
  board.chart['Theo share by home region'] = {
    kind: 'donut',
    slices: ordered.map((row, index) => ({ label: row.segment, value: row.share_of_theo, color: colors[index] ?? slate })),
    format: 'pct',
    aria: 'Share of tracked theo by home region. Locals are a small share of card holders and most of the theo.',
  }
  board.rank.Regions = ordered.map(row => ({
    label: `${row.segment} · ${row.visits_per_player.toFixed(1)} visits`,
    left: pct(row.share_of_players, 0),
    right: pct(row.share_of_theo, 0),
  }))
  board.chart['Visits per player by region'] = {
    kind: 'hbar',
    categories: ordered.map(row => row.segment),
    values: ordered.map(row => row.visits_per_player),
    colors: ordered.map(row => (row.segment === 'Local' ? action : play)),
    format: 'number',
    digits: 1,
    aria: 'Visits per card holder by home region. Locals visit about 28 times. Everyone else visits about once.',
  }
  const groups = columnRows(pack['player_groups.json'])
  const tiers = ['Base', 'Gold', 'Platinum']
  const homes = ['Local', 'Regional', 'Domestic', 'International']
  board.chart['Tier x residence'] = {
    kind: 'heatmap',
    rows: tiers,
    cols: homes,
    values: tiers.map(tier => homes.map(home => groups
      .filter(row => row.tier === tier && row.home_region === home)
      .reduce((sum, row) => sum + row.theo, 0))),
    format: 'money',
    accent: 'play',
    aria: 'Tracked theo by tier and home region. Theo adds across months. Player counts do not, because a person is one row per active month. Locals dominate every tier.',
  }
  return board
}

function bindTail(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const profile = table(pack, 'players.json', 'tail_profile')
  const histogramRows = table(pack, 'players.json', 'net_histogram')
  const tail = profile.find(row => row.group.startsWith('heaviest'))
  const rest = profile.find(row => !row.group.startsWith('heaviest'))
  board.stat['Players in tail'] = Math.round(tail.players).toLocaleString('en-US')
  board.pair['Net per player'] = [dollars(tail.net_mean), dollars(rest.net_mean)]
  board.stat.Visits = tail.visits_mean.toFixed(1)
  board.chart['Net result distribution'] = {
    kind: 'bar',
    categories: histogramRows.map(row => row.net_bin),
    series: [{
      name: 'Players',
      values: histogramRows.map(row => row.players),
      color: slate,
      colors: histogramRows.map(row => (/^(0|[1-9]|>)/.test(row.net_bin) ? collection : action)),
    }],
    format: 'count',
    tickEvery: 2,
    aria: 'Card holders by net result. Red bins finished behind. This is a group for protective outreach, not for more marketing.',
  }
  board.note.Finding = claimNote(pack, 'Q4-heavy-loss')
  board.chart['Luck vs volume'] = {
    kind: 'scatter',
    points: [
      { x: tail.theo_mean, y: tail.luck_mean, color: action, label: 'Heaviest 1%' },
      { x: rest.theo_mean, y: rest.luck_mean, color: slate, label: 'Other 99%' },
    ],
    formatX: 'money',
    formatY: 'money',
    xLabel: 'Mean theo',
    yLabel: 'Mean luck',
    aria: 'Mean luck against mean theo. The heaviest-loss 1 percent have far more theo than their luck residual, so volume of play drives the result.',
  }
  board.chart['Visits per player'] = {
    kind: 'hbar',
    categories: ['Heaviest 1%', 'Other 99%'],
    values: [tail.visits_mean, rest.visits_mean],
    colors: [action, slate],
    format: 'number',
    digits: 1,
    aria: 'Visits per player. The heaviest-loss group visits about 63 times. Everyone else visits about 2.5 times.',
  }
  return board
}

function bindReconcile(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const rows = table(pack, 'players.json', 'reconciliation')
  const shares = rows.map(row => row.carded_share as number)
  board.stat['Max monthly gap'] = '$0.00'
  board.stat['Carded share'] = `${pct(Math.min(...shares))}–${pct(Math.max(...shares))}`
  board.stat['Months matched'] = String(rows.length)
  board.chart['Carded vs tracked coin-in'] = {
    kind: 'line',
    labels: rows.map(row => monthName(row.month)),
    series: [
      { name: 'Carded', values: rows.map(row => row.carded_coin_in), color: play },
      { name: 'Tracked', values: rows.map(row => row.player_coin_in), color: action, dash: true },
    ],
    format: 'money',
    aria: 'Carded meter coin-in and player-table coin-in by month. The two series match. The maximum monthly gap is zero.',
  }
  board.rank['Monthly gap'] = rows.map(row => ({
    label: monthName(row.month),
    left: compactMoney(row.carded_coin_in),
    right: dollars(row.gap),
  }))
  board.chart['Carded share by month'] = {
    kind: 'bar',
    categories: rows.map(row => monthName(row.month)),
    series: [{ name: 'Carded share', values: shares, color: play }],
    format: 'pct',
    aria: 'Carded share of coin-in by month, about two thirds in every month.',
  }
  return board
}

function bindChange(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const daily = table(pack, 'comps.json', 'daily')
  const its = table(pack, 'comps.json', 'its')
  const rates = table(pack, 'comps.json', 'redemption_rates')
  const row = its.find(item => item.outcome === 'pts_per_usd')
  const dates = daily.map(item => dayKey(item.gaming_date))
  board.stat['Level change'] = row.level_change.toFixed(2)
  board.stat.Switch = 'May 1'
  board.stat['Tiers affected'] = String(rates.length)
  board.chart['Points per $ by redemption'] = {
    kind: 'scatter',
    points: daily.flatMap(item => (Number.isFinite(item.pts_per_usd)
      ? [{ x: item.t, y: item.pts_per_usd, color: item.post ? action : play }]
      : [])),
    formatX: 'number',
    formatY: 'number',
    digitsX: 0,
    digitsY: 1,
    xLabel: 'Day',
    yLabel: 'Points per $',
    aria: 'Points redeemed per comp dollar by gaming day. Blue is before May 1 and red is after. The rate falls by about half in one day.',
  }
  board.rank['Rate by tier'] = rates.map(item => ({
    label: item.tier,
    left: item.pts_per_usd_before.toFixed(1),
    right: item.pts_per_usd_after.toFixed(1),
  }))
  board.chart['Segmented regression'] = {
    kind: 'line',
    labels: monthTicks(dates),
    series: [
      { name: 'Observed', values: daily.map(item => item.pts_per_usd), color: play },
      { name: 'Step', values: stepSeries(daily, row), color: action, dash: true },
    ],
    format: 'number',
    digits: 1,
    rule: onOrAfter(dates, '2025-05-01'),
    aria: 'Daily points per comp dollar and the weekday-averaged step from the exported regression. The step uses the pre-period mean, the pre-period trend, and the level change. It is not a refit.',
  }
  board.note.Finding = claimNote(pack, 'Q5-change')
  return board
}

function bindCost(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const daily = table(pack, 'comps.json', 'daily')
  const monthly = table(pack, 'comps.json', 'monthly')
  const its = table(pack, 'comps.json', 'its')
  const cost = its.find(row => row.outcome === 'comp_cost')
  const reinvestment = its.find(row => row.outcome === 'reinvestment')
  const dates = daily.map(row => dayKey(row.gaming_date))
  const spent = monthly.reduce((sum, row) => sum + row.comp_cost, 0)
  const theo = monthly.reduce((sum, row) => sum + row.theo, 0)
  board.stat['Program cost'] = compactMoney(spent)
  board.stat['Of tracked theo'] = pct(spent / theo, 2)
  board.stat['Cost level change'] = compactMoney(cost.level_change)
  board.stat['Reinvestment change'] = `${reinvestment.level_change >= 0 ? '+' : ''}${(reinvestment.level_change * 100).toFixed(2)}`
  board.chart['Daily comp cost with fitted trend'] = {
    kind: 'line',
    labels: monthTicks(dates),
    series: [
      { name: 'Comp cost', values: daily.map(row => row.comp_cost), color: play },
      { name: 'Step', values: stepSeries(daily, cost), color: action, dash: true },
    ],
    format: 'money',
    rule: onOrAfter(dates, '2025-05-01'),
    aria: 'Daily comp cost and the exported interrupted-time-series step. The level change is about 8 dollars a day and is not distinguishable from the trend already underway.',
  }
  board.chart['Monthly reinvestment'] = {
    kind: 'bar',
    categories: monthly.map(row => monthName(row.month)),
    series: [{ name: 'Reinvestment', values: monthly.map(row => row.reinvestment), color: back }],
    format: 'pct',
    digits: 2,
    zero: false,
    aria: 'Comp cost as a share of tracked theo by month. It rises from 1.11 percent in January to 1.32 percent in June, through the May rate change.',
  }
  const names: Record<string, string> = {
    comp_cost: 'Comp cost',
    reinvestment: 'Reinvestment',
    redemptions: 'Redemptions',
    carded_coin_in: 'Carded play',
  }
  const effect = (row: Rec) => {
    if (row.outcome === 'comp_cost') return `${compactMoney(row.level_change)}/d`
    if (row.outcome === 'reinvestment') return `${(row.level_change * 100).toFixed(2)} pp`
    if (row.outcome === 'carded_coin_in') return signedPct(row.level_change_pct)
    return `${row.level_change.toFixed(1)}/d`
  }
  board.rank['Model terms'] = ['comp_cost', 'reinvestment', 'redemptions', 'carded_coin_in'].map((outcome) => {
    const row = its.find(item => item.outcome === outcome)
    return { label: names[outcome] ?? outcome, left: effect(row), right: row.level_p.toFixed(2) }
  })
  board.chart['Redemptions per day'] = {
    kind: 'area',
    labels: monthTicks(dates),
    series: [{ name: 'Redemptions', values: daily.map(row => row.redemptions), color: back }],
    format: 'number',
    zero: true,
    rule: onOrAfter(dates, '2025-05-01'),
    aria: 'Redemptions per gaming day. The May 1 rate change does not lift the count.',
  }
  return board
}

function bindLiability(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const summary = pack['comps.json'].summary
  const daily = table(pack, 'comps.json', 'daily')
  const tiers = table(pack, 'comps.json', 'by_tier')
  const dates = daily.map(row => dayKey(row.gaming_date))
  board.pair['Face value'] = [compactMoney(summary.face_at_old), compactMoney(summary.face_at_new)]
  board.pair['Economic cost'] = [compactMoney(summary.cost_at_old), compactMoney(summary.cost_at_new)]
  board.chart['Points awarded vs redeemed'] = {
    kind: 'area',
    labels: monthTicks(dates),
    series: [
      { name: 'Awarded', values: daily.map(row => row.points_awarded), color: play },
      { name: 'Redeemed', values: daily.map(row => row.points_redeemed), color: action },
    ],
    format: 'count',
    zero: true,
    rule: onOrAfter(dates, '2025-05-01'),
    aria: 'Points awarded and points redeemed by gaming day. Redemptions do not jump after May 1, so the cheaper rate is still mostly unredeemed.',
  }
  board.stat['Unredeemed points'] = `${(summary.balance_points / 1_000_000).toFixed(1)}M`
  board.stat['Exposure multiple'] = multiple(summary.face_at_new / summary.face_at_old, 1)
  board.stat['Cost to face'] = pct(summary.cost_ratio)
  const names = ['Base', 'Gold', 'Platinum']
  const before = names.map(tier => tiers.find(row => row.tier === tier && row.period === 'before'))
  const after = names.map(tier => tiers.find(row => row.tier === tier && row.period === 'after'))
  board.chart['Liability by tier'] = {
    kind: 'bar',
    categories: names,
    series: [
      { name: 'Before', values: before.map(row => row.pts_per_comp_usd), color: slate },
      { name: 'After', values: after.map(row => row.pts_per_comp_usd), color: action },
    ],
    format: 'number',
    digits: 1,
    aria: 'Points per comp dollar by tier before and after May 1. Every tier falls by about half.',
  }
  board.note.Finding = claimNote(pack, 'Q5-liability')
  return board
}

function bindPortfolio(pack: Pack): BoardBinding {
  const board = emptyBoard()
  const summary = pack['budget.json'].summary
  const actions = table(pack, 'budget.json', 'actions')
  const demand = pack['demand.json'].summary
  const forecast = pack['forecast.json']
  const july = table(pack, 'forecast.json', 'july')
  const metrics = new Map((forecast.metrics as Rec[]).map(row => [row.column, row]))
  board.pair.Recommended = [dollars(summary.spent), dollars(summary.kept)]
  board.pair['Net benefit range'] = [
    `$${(summary.net_low / 1000).toFixed(1)}k`,
    `$${(summary.net_high / 1000).toFixed(1)}k`,
  ]
  const bars = actions.filter(row => row.action_type_id !== 'A-HOLD' && row.action_type_id !== 'A-REPLACE-BUY')
  board.chart['Mid-case net by action'] = {
    kind: 'hbar',
    categories: bars.map(row => ACTION[row.action_type_id] ?? row.name),
    values: bars.map(row => row.net_mid),
    colors: bars.map(row => (row.funded ? collection : action)),
    format: 'money',
    aria: 'Mid-case net benefit by action. Green is funded. Buying the bottom 10 is omitted because its loss is 220 thousand dollars and would hide the rest. That cost is on the stat beside this chart.',
  }
  const funded = actions.filter(row => row.funded && row.action_type_id !== 'A-HOLD')
  board.rank['Funded actions'] = funded.map(row => ({
    label: fundLabel(row),
    left: dollars(row.cost),
    right: compactMoney(row.net_mid),
  }))
  board.stat['Replace bottom 10'] = '$220k vs $100k'
  board.stat['Net benefit'] = dollars(summary.net_mid)
  board.chart['Net benefit by scenario'] = {
    kind: 'interval',
    rows: funded.map(row => ({
      label: ACTION[row.action_type_id] ?? row.name,
      low: row.net_low,
      mid: row.net_mid,
      high: row.net_high,
    })),
    format: 'money',
    guides: [0],
    aria: 'Low, mid, and high net benefit for the three funded actions.',
  }
  board.chart['July coin-in forecast'] = {
    kind: 'line',
    labels: july.map((row, index) => (index === 0 || index === 14 || index === july.length - 1 ? `${monthName(row.gaming_date)} ${dayKey(row.gaming_date).slice(8)}` : '')),
    series: [
      { name: 'Forecast', values: july.map(row => row.forecast), color: play },
      { name: 'June level', values: july.map(row => row.scenario_low), color: slate, dash: true },
    ],
    format: 'money',
    aria: `July coin-in forecast, ${forecast.summary.method}, against the June-level low case. July totals ${compactMoney(forecast.summary.july_total)}, or ${compactMoney(forecast.summary.july_low_total)} if June's level persists.`,
  }
  const flat = metrics.get('flat')
  const weekday = metrics.get('weekday_mean')
  const winters = metrics.get('holt_winters')
  const measures = funded
    .map(row => `${ACTION[row.action_type_id]}: ${String(row.measurement).split('.')[0]}.`)
    .join(' ')
  board.note['Why this portfolio'] = [
    `Fund three action types for ${dollars(summary.spent)} and keep ${dollars(summary.kept)}. The mid-case net is ${dollars(summary.net_mid)}, from ${dollars(summary.net_low)} to ${dollars(summary.net_high)}.`,
    'Replacements are not funded. The bottom 10 lose to game mix and location, two are already retired, and buying all ten costs more than the budget. A technician and preventive maintenance do not pay back inside July, and June staffing is back to plan.',
    `The new Center Pit bank did not take play from the rest of the pit (${signedPct(demand.pit_rest_effect)}). B-51 earned ${multiple(demand.bank51_first4w)} the rest of the pit in its first four weeks and ${multiple(demand.bank51_last4w)} in its last four.`,
    `On the frozen May-June holdout the training-mean level has MAE ${dollars(flat.mae)}, against ${dollars(weekday.mae)} for the weekday-mean baseline and ${dollars(winters.mae)} for Holt-Winters. April preferred ${forecast.summary.april_choice}. Both windows together select ${forecast.summary.method}. The bands are ordinary-day spread and too narrow once the level moves.`,
    measures,
  ].join(' ')
  return board
}

function fundLabel(row: Rec): string {
  if (row.action_type_id === 'A-INSPECT') return `Inspect · ${row.targets}`
  if (row.action_type_id === 'A-MOVE-MACHINE') return 'Move · 2 to Center Pit'
  const weekend = String(row.targets).match(/Jul \d+-\d+/)
  if (row.action_type_id === 'A-PROMO') return `Promo · ${weekend?.[0] ?? 'weekend'}`
  return ACTION[row.action_type_id] ?? row.name
}
