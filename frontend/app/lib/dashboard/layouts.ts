export type TileTone = 'play' | 'action' | 'back' | 'collection'

export type ChartKind = 'bar' | 'hbar' | 'line' | 'area' | 'scatter' | 'heatmap' | 'donut' | 'interval'

/** Column spans on the 12-column grid. Small spans fold to half width on medium screens. */
export type TileCol = 3 | 4 | 5 | 6 | 7 | 8 | 12

export type TileRow = 1 | 2 | 3

interface TileBase {
  title: string
  col: TileCol
  row: TileRow
}

export interface StatTileDef extends TileBase {
  kind: 'stat'
  tone: TileTone
  value?: string
  caption?: string
  fill?: boolean
}

export interface PairTileDef extends TileBase {
  kind: 'pair'
  left: string
  right: string
  joiner?: string
  values?: readonly [string, string]
}

export interface ChartTileDef extends TileBase {
  kind: 'chart'
  chart: ChartKind
}

export interface RankTileDef extends TileBase {
  kind: 'rank'
  columns: readonly [string, string]
}

export interface NoteTileDef extends TileBase {
  kind: 'note'
}

export type TileDef = StatTileDef | PairTileDef | ChartTileDef | RankTileDef | NoteTileDef

export const TILE_COL: Record<TileCol, string> = {
  3: 'md:col-span-3 lg:col-span-3',
  4: 'md:col-span-3 lg:col-span-4',
  5: 'md:col-span-6 lg:col-span-5',
  6: 'md:col-span-6 lg:col-span-6',
  7: 'md:col-span-6 lg:col-span-7',
  8: 'md:col-span-6 lg:col-span-8',
  12: 'md:col-span-6 lg:col-span-12',
}

export const TILE_ROW: Record<TileRow, string> = {
  1: 'row-span-1',
  2: 'row-span-2',
  3: 'row-span-3',
}

type Extra<T> = Partial<Omit<T, 'kind' | 'title' | 'col' | 'row'>>

export function stat(title: string, tone: TileTone, col: TileCol, row: TileRow = 1, extra: Extra<StatTileDef> = {}): StatTileDef {
  return { kind: 'stat', title, tone, col, row, ...extra }
}

export function pair(title: string, left: string, right: string, col: TileCol, row: TileRow = 1, joiner = 'X'): PairTileDef {
  return { kind: 'pair', title, left, right, col, row, joiner }
}

function chart(title: string, kind: ChartKind, col: TileCol, row: TileRow): ChartTileDef {
  return { kind: 'chart', title, chart: kind, col, row }
}

function rank(title: string, columns: readonly [string, string], col: TileCol, row: TileRow): RankTileDef {
  return { kind: 'rank', title, columns, col, row }
}

function note(col: TileCol, row: TileRow, title = 'Finding'): NoteTileDef {
  return { kind: 'note', title, col, row }
}

export const LAYOUTS: Record<string, readonly TileDef[]> = {
  'Q1-manager-list': [
    stat('In Back Forty', 'action', 3, 1, { fill: true, caption: 'of the 10' }),
    stat('Low-hold configs', 'play', 3, 1, { caption: 'theo hold <= 8%' }),
    stat('Partial window', 'back', 3),
    stat('Availability', 'collection', 3, 1, { caption: 'list vs floor' }),
    rank("Manager's bottom 10", ['House win', 'Theo'], 5, 3),
    chart('House win waterfall', 'bar', 7, 3),
    chart('Primary driver', 'donut', 4, 2),
    chart('Floor position', 'heatmap', 4, 2),
    note(4, 2),
  ],
  'Q1-payout-anomaly': [
    pair('Hit rate', 'Observed', 'Configured', 6, 1, 'vs'),
    pair('Hold', 'Actual', 'Theo', 6, 1, 'vs'),
    chart('Monthly hit rate vs configured', 'line', 8, 3),
    stat('Hit-rate z', 'action', 4, 1, { fill: true }),
    stat('Luck z', 'play', 4),
    stat('Below theo', 'back', 4, 1, { caption: 'over 181 days' }),
    chart('Hit-rate z across machines', 'scatter', 7, 2),
    note(5, 2),
  ],
  'Q1-luck': [
    pair('Beyond |z| > 2', 'Observed', 'Expected', 6, 1, 'vs'),
    stat('Significant', 'action', 3, 1, { fill: true, caption: 'after BH correction' }),
    stat('Machines', 'play', 3),
    chart('Luck z distribution', 'bar', 8, 3),
    rank('Largest |z|', ['z', 'q'], 4, 3),
    chart('House win vs theo', 'scatter', 6, 2),
    chart('Luck z by machine', 'interval', 6, 2),
  ],
  'Q1-location': [
    stat('Lowest zone', 'action', 4, 1, { fill: true, caption: 'zone factor' }),
    stat('Highest zone', 'collection', 4, 1, { caption: 'zone factor' }),
    stat('Zones', 'play', 4),
    chart('Zone factor', 'hbar', 7, 3),
    rank('Zones', ['Factor', 'Theo/hr'], 5, 3),
    chart('Floor map', 'heatmap', 8, 2),
    note(4, 2),
  ],
  'Q1-persistence': [
    pair('Machine effect', 'Jan-Mar', 'Apr-Jun', 6),
    stat('Correlation', 'play', 3, 1, { fill: true, caption: 'quarter to quarter' }),
    stat('Persistent', 'action', 3, 1, { caption: 'bottom decile' }),
    chart('Jan-Mar vs Apr-Jun effect', 'scatter', 7, 3),
    rank('Persistent bottom decile', ['Jan-Mar', 'Apr-Jun'], 5, 3),
    chart('Effect by quarter', 'interval', 6, 2),
    note(6, 2),
  ],
  'Q2-weekday': [
    pair('Peak vs trough', 'Saturday', 'Tuesday', 6),
    stat('Weekend lift', 'play', 3, 1, { fill: true }),
    stat('Ordinary days', 'back', 3, 1, { caption: 'per weekday' }),
    chart('Mean coin-in by weekday', 'bar', 8, 3),
    rank('Weekday ranking', ['Coin-in', 'Index'], 4, 3),
    chart('Weekday x hour', 'heatmap', 8, 2),
    note(4, 2),
  ],
  'Q2-events': [
    stat('Events', 'play', 3, 1, { fill: true, caption: 'in window' }),
    stat('Best lift', 'action', 3, 1, { caption: 'vs same weekday' }),
    stat('Extra coin-in', 'back', 3),
    stat('Event days', 'collection', 3),
    rank('Lift by event', ['Coin-in', 'Lift'], 5, 3),
    chart('Daily coin-in with event windows', 'line', 7, 3),
    chart('Lift vs event length', 'scatter', 6, 2),
    note(6, 2),
  ],
  'Q2-renovation': [
    pair('Coin-in change', 'During', 'After', 6, 1, 'vs'),
    stat('Lost coin-in', 'back', 3, 1, { fill: true }),
    stat('Lost theo', 'action', 3),
    chart('Back Forty vs control zones', 'area', 12, 3),
    chart('Door-counter entries', 'bar', 4, 2),
    chart('Bootstrap intervals', 'interval', 4, 2),
    note(4, 2),
  ],
  'Q2-trend': [
    stat('Peak month', 'play', 4, 1, { caption: 'coin-in per day' }),
    stat('Low month', 'action', 4, 1, { caption: 'coin-in per day' }),
    stat('Correlation', 'collection', 4, 1, { caption: 'with LVCVA visitors' }),
    chart('Coin-in per day by month', 'area', 8, 3),
    stat('Adjusted index', 'back', 4, 1, { fill: true }),
    stat('Active machines', 'play', 4),
    stat('Visitors YoY', 'action', 4),
    chart('Index vs LVCVA visitors', 'scatter', 5, 2),
    chart('Convention attendance', 'bar', 7, 2),
  ],
  'Q2-weather': [
    stat('Temp correlation', 'play', 3, 1, { fill: true }),
    stat('Rainy days', 'collection', 3),
    stat('Rain effect', 'action', 3, 1, { caption: 'vs weekday mean' }),
    stat('Ordinary days', 'back', 3),
    chart('Demand residual vs max temp', 'scatter', 7, 3),
    chart('Rainy vs dry days', 'bar', 5, 2),
    stat('Seasonal trend', 'back', 5, 1, { caption: 'carried by temperature' }),
    chart('Max temperature through the window', 'line', 8, 2),
    note(4, 2),
  ],
  'Q3-total': [
    stat('Machine-hours lost', 'action', 3, 1, { fill: true }),
    stat('Share of schedule', 'play', 3),
    stat('Theo lost', 'back', 3, 1, { caption: 'before substitution' }),
    stat('Recovered', 'collection', 3, 1, { caption: 'by neighbours' }),
    chart('Downtime by cause', 'donut', 4, 3),
    chart('Machine-hours lost by week', 'bar', 8, 3),
    rank('Cause breakdown', ['Hours', 'Theo'], 6, 2),
    pair('Loss', 'Gross', 'Net', 6, 1, 'vs'),
    stat('Reconciliation gap', 'collection', 6, 1, { caption: 'vs machine_day' }),
  ],
  'Q3-when': [
    stat('Costliest month', 'action', 3),
    stat('Lowest month', 'collection', 3),
    pair('Theo per downtime hour', 'Swing', 'Grave', 6),
    chart('Downtime cost by month', 'bar', 7, 3),
    chart('Shift x weekday cost', 'heatmap', 5, 3),
    chart('Hours vs theo per hour', 'scatter', 4, 2),
    chart('Theo per downtime hour by hour of day', 'line', 8, 2),
  ],
  'Q3-manufacturer': [
    stat('Fault ratio', 'action', 4, 1, { fill: true, caption: 'Ridgeline vs others' }),
    stat('Repair cost', 'back', 4, 1, { caption: 'per machine' }),
    stat('Theo lost', 'play', 4, 1, { caption: 'per machine' }),
    rank('Manufacturers', ['Faults', 'Hours'], 6, 3),
    chart('Faults per machine-month', 'hbar', 6, 3),
    chart('Monthly fault rate by maker', 'line', 8, 2),
    note(4, 2),
  ],
  'Q3-staffing': [
    pair('Mean repair time', 'Short', 'Full', 6, 1, 'vs'),
    stat('Extra hours', 'action', 3, 1, { fill: true, caption: '95% CI' }),
    stat('Short shifts', 'back', 3),
    chart('Repair time distribution', 'area', 6, 3),
    chart('Difference with 95% CI', 'interval', 6, 3),
    chart('Short-staffed shift-days', 'heatmap', 8, 2),
    note(4, 2),
  ],
  'Q4-outcomes': [
    stat('Card holders', 'play', 3),
    stat('Ahead share', 'collection', 3, 1, { fill: true }),
    pair('Hold', 'Actual', 'Theo', 6, 1, 'vs'),
    chart('Ahead share by theo decile', 'bar', 8, 3),
    stat('Net result', 'back', 4),
    stat('Luck residual', 'action', 4),
    stat('Card-only diners', 'play', 4),
    chart('Wagered vs returned', 'area', 7, 2),
    note(5, 2),
  ],
  'Q4-concentration': [
    stat('Top 1% of theo', 'action', 4, 1, { fill: true }),
    stat('Top 10% of theo', 'play', 4, 1, { fill: true }),
    stat('Gini', 'back', 4, 1, { caption: 'theo' }),
    chart('Lorenz curve', 'line', 6, 3),
    chart('Theo share by percentile', 'bar', 6, 3),
    rank('Gini by measure', ['Gini', 'Top 10%'], 4, 2),
    chart('Loss concentration', 'area', 8, 2),
  ],
  'Q4-locals': [
    pair('Locals', 'Players', 'Theo', 6),
    stat('Visits per local', 'play', 3),
    stat('Net per local', 'back', 3),
    chart('Theo share by home region', 'donut', 4, 3),
    rank('Regions', ['Players', 'Theo'], 8, 3),
    chart('Visits per player by region', 'hbar', 6, 2),
    chart('Tier x residence', 'heatmap', 6, 2),
  ],
  'Q4-heavy-loss': [
    stat('Players in tail', 'action', 3, 1, { fill: true }),
    pair('Net per player', 'Tail', 'Others', 6, 1, 'vs'),
    stat('Visits', 'back', 3, 1, { caption: 'per tail player' }),
    chart('Net result distribution', 'bar', 8, 3),
    note(4, 3),
    chart('Luck vs volume', 'scatter', 6, 2),
    chart('Visits per player', 'hbar', 6, 2),
  ],
  'Q4-reconciliation': [
    stat('Max monthly gap', 'collection', 4, 1, { fill: true }),
    stat('Carded share', 'play', 4, 1, { caption: 'of coin-in' }),
    stat('Months matched', 'back', 4),
    chart('Carded vs tracked coin-in', 'line', 8, 3),
    rank('Monthly gap', ['Carded', 'Gap'], 4, 3),
    chart('Carded share by month', 'bar', 12, 2),
  ],
  'Q5-change': [
    stat('Level change', 'action', 4, 1, { fill: true, caption: 'points per $' }),
    stat('Switch', 'play', 4, 1, { caption: 'gaming day' }),
    stat('Tiers affected', 'back', 4),
    chart('Points per $ by redemption', 'scatter', 8, 3),
    rank('Rate by tier', ['Old', 'New'], 4, 3),
    chart('Segmented regression', 'line', 8, 2),
    note(4, 2),
  ],
  'Q5-cost': [
    stat('Program cost', 'back', 3, 1, { fill: true }),
    stat('Of tracked theo', 'play', 3),
    stat('Cost level change', 'action', 3, 1, { caption: 'per day' }),
    stat('Reinvestment change', 'collection', 3, 1, { caption: 'pp' }),
    chart('Daily comp cost with fitted trend', 'line', 8, 3),
    chart('Monthly reinvestment', 'bar', 4, 3),
    rank('Model terms', ['Effect', 'p'], 6, 2),
    chart('Redemptions per day', 'area', 6, 2),
  ],
  'Q5-liability': [
    pair('Face value', 'Old rate', 'New rate', 6, 1, 'vs'),
    pair('Economic cost', 'Old rate', 'New rate', 6, 1, 'vs'),
    chart('Points awarded vs redeemed', 'area', 8, 3),
    stat('Unredeemed points', 'play', 4, 1, { fill: true }),
    stat('Exposure multiple', 'action', 4, 1, { caption: 'new vs old' }),
    stat('Cost to face', 'back', 4),
    chart('Liability by tier', 'bar', 6, 2),
    note(6, 2),
  ],
  'Q6-portfolio': [
    pair('Recommended', 'Spend', 'Keep', 6, 1, 'vs'),
    pair('Net benefit range', 'Low', 'High', 6, 1, 'to'),
    chart('Mid-case net by action', 'hbar', 7, 3),
    rank('Funded actions', ['Cost', 'Net'], 5, 2),
    stat('Replace bottom 10', 'action', 5, 1, { caption: 'buy cost vs budget' }),
    chart('Net benefit by scenario', 'interval', 4, 2),
    chart('July coin-in forecast', 'line', 4, 2),
    note(4, 2, 'Why this portfolio'),
  ],
}

export function layoutFor(claimId: string): readonly TileDef[] {
  return LAYOUTS[claimId] ?? []
}
