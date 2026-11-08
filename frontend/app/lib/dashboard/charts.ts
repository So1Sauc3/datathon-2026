import type { ValueFormat } from './format'

export interface BarSeries {
  name: string
  values: number[]
  color: string
  colors?: string[]
}

export interface BarSpec {
  kind: 'bar'
  categories: string[]
  series: BarSeries[]
  waterfall?: { y0: number[], y1: number[], color: string[] }
  format: ValueFormat
  aria: string
  digits?: number
  tickEvery?: number
  /** Include zero in the axis. Defaults to yes so bar lengths stay comparable. */
  zero?: boolean
}

export interface HBarSpec {
  kind: 'hbar'
  categories: string[]
  values: number[]
  colors: string[]
  format: ValueFormat
  aria: string
  digits?: number
}

export interface LineSpec {
  kind: 'line' | 'area'
  labels: string[]
  series: { name: string, values: (number | null)[], color: string, dash?: boolean }[]
  format: ValueFormat
  aria: string
  digits?: number
  zero?: boolean
  shades?: { from: number, to: number }[]
  rule?: number
  guide?: number
  tickEvery?: number
}

export interface ScatterSpec {
  kind: 'scatter'
  points: { x: number, y: number, color: string, label?: string }[]
  formatX: ValueFormat
  formatY: ValueFormat
  aria: string
  xLabel: string
  yLabel: string
  parity?: boolean
  digitsX?: number
  digitsY?: number
}

export interface HeatmapSpec {
  kind: 'heatmap'
  rows: string[]
  cols: string[]
  values: (number | null)[][]
  format: ValueFormat
  aria: string
  accent: 'play' | 'action'
  digits?: number
}

export interface DonutSpec {
  kind: 'donut'
  slices: { label: string, value: number, color: string }[]
  format: ValueFormat
  aria: string
  digits?: number
}

export interface IntervalSpec {
  kind: 'interval'
  rows: { label: string, low: number, mid: number, high: number }[]
  format: ValueFormat
  aria: string
  guides?: number[]
  digits?: number
}

export type ChartSpec = BarSpec | HBarSpec | LineSpec | ScatterSpec | HeatmapSpec | DonutSpec | IntervalSpec

export interface RankRow {
  label: string
  left: string
  right: string
}

export interface BoardBinding {
  stat: Record<string, string>
  pair: Record<string, readonly [string, string]>
  rank: Record<string, RankRow[]>
  note: Record<string, string>
  chart: Record<string, ChartSpec>
}

export function emptyBoard(): BoardBinding {
  return { stat: {}, pair: {}, rank: {}, note: {}, chart: {} }
}
