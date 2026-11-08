import { chartTheme } from './theme'
import { bandScale, linearScale } from './scales'
import type { ChartSpec } from '~/lib/dashboard/charts'
import { formatValue, type ValueFormat } from '~/lib/dashboard/format'

const GRID = chartTheme.tick
const INK = chartTheme.level
const SHADE = chartTheme.back

export type Mark =
  | { type: 'rect', x: number, y: number, w: number, h: number, fill: string, opacity?: number, rx?: number }
  | { type: 'line', x1: number, y1: number, x2: number, y2: number, stroke: string, width?: number, dash?: string, opacity?: number }
  | { type: 'path', d: string, stroke?: string, fill?: string, width?: number, dash?: string, opacity?: number }
  | { type: 'text', x: number, y: number, text: string, anchor: 'start' | 'middle' | 'end', fill?: string }
  | { type: 'circle', cx: number, cy: number, r: number, fill: string }

function finite(values: readonly (number | null | undefined)[]): number[] {
  return values.filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
}

function domain(values: number[], zero: boolean): [number, number] {
  let min = Math.min(...values)
  let max = Math.max(...values)
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [0, 1]
  if (zero) {
    min = Math.min(0, min)
    max = Math.max(0, max)
  }
  if (min === max) {
    const pad = Math.abs(min) || 1
    return [min - pad * 0.5, max + pad * 0.5]
  }
  const pad = (max - min) * 0.08
  return [zero && min >= 0 ? 0 : min - pad, max + pad]
}

function niceTicks(min: number, max: number, count = 4): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) return [min]
  const step0 = (max - min) / count
  const mag = 10 ** Math.floor(Math.log10(Math.abs(step0)))
  const err = step0 / mag
  const step = (err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1) * mag
  const start = Math.ceil(min / step) * step
  const ticks: number[] = []
  for (let value = start; value <= max + step * 0.01 && ticks.length < 6; value += step) {
    ticks.push(Number(value.toFixed(8)))
  }
  return ticks.length ? ticks : [min, max]
}

function label(n: number, format: ValueFormat, digits?: number): string {
  return formatValue(n, format, digits)
}

function mix(from: string, to: string, t: number): string {
  const parse = (hex: string) => {
    const n = Number.parseInt(hex.slice(1), 16)
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
  }
  const a = parse(from)
  const b = parse(to)
  const channel = a.map((value, index) => Math.round(value + (b[index] - value) * t))
  return `rgb(${channel[0]},${channel[1]},${channel[2]})`
}

function linePath(points: readonly (readonly [number, number] | null)[]): string[] {
  const paths: string[] = []
  let current = ''
  for (const point of points) {
    if (!point) {
      if (current) paths.push(current)
      current = ''
      continue
    }
    current += `${current ? 'L' : 'M'}${point[0]},${point[1]}`
  }
  if (current) paths.push(current)
  return paths
}

export function layoutChart(spec: ChartSpec, width: number, height: number): Mark[] {
  if (width < 8 || height < 8) return []
  switch (spec.kind) {
    case 'bar':
      return layoutBar(spec, width, height)
    case 'hbar':
      return layoutHBar(spec, width, height)
    case 'line':
    case 'area':
      return layoutLine(spec, width, height)
    case 'scatter':
      return layoutScatter(spec, width, height)
    case 'heatmap':
      return layoutHeat(spec, width, height)
    case 'donut':
      return layoutDonut(spec, width, height)
    case 'interval':
      return layoutInterval(spec, width, height)
  }
}

function yAxis(min: number, max: number, height: number, format: ValueFormat, digits?: number): { marks: Mark[], scale: (n: number) => number } {
  const scale = linearScale([min, max], height, { vertical: true })
  const marks: Mark[] = []
  for (const tick of niceTicks(min, max)) {
    const y = scale(tick)
    if (y < -4 || y > height + 4) continue
    marks.push({ type: 'line', x1: 0, y1: y, x2: 0, y2: y, stroke: GRID, width: 2 })
    marks.push({ type: 'text', x: -8, y, text: label(tick, format, digits), anchor: 'end' })
  }
  if (min < 0 && max > 0) {
    const y = scale(0)
    marks.push({ type: 'line', x1: 0, y1: y, x2: 1, y2: y, stroke: INK, width: 2, opacity: 0.45 })
  }
  return { marks, scale }
}

function layoutBar(spec: Extract<ChartSpec, { kind: 'bar' }>, width: number, height: number): Mark[] {
  const marks: Mark[] = []
  const values = spec.waterfall
    ? spec.waterfall.y0.concat(spec.waterfall.y1)
    : spec.series.flatMap(series => series.values)
  const [min, max] = domain(finite(values), spec.zero !== false)
  const { marks: axis, scale } = yAxis(min, max, height, spec.format, spec.digits)
  for (const mark of axis) {
    if (mark.type === 'line' && mark.x2 === 1) marks.push({ ...mark, x2: width })
    else if (mark.type === 'line') marks.push({ ...mark, x2: width, opacity: 0.9 })
    else marks.push(mark)
  }
  const ids = spec.categories.map((_, index) => String(index))
  const band = bandScale(ids, width, 0.18)
  const every = spec.tickEvery ?? (spec.categories.length > 8 ? 2 : 1)
  spec.categories.forEach((category, index) => {
    if (!category) return
    if (index % every !== 0 && index !== spec.categories.length - 1) return
    marks.push({
      type: 'text',
      x: (band(String(index)) ?? 0) + band.bandwidth() / 2,
      y: height + 16,
      text: category,
      anchor: 'middle',
    })
  })
  if (spec.waterfall) {
    spec.categories.forEach((category, index) => {
      const y0 = spec.waterfall!.y0[index] ?? 0
      const y1 = spec.waterfall!.y1[index] ?? 0
      const top = scale(Math.max(y0, y1))
      const bottom = scale(Math.min(y0, y1))
      marks.push({
        type: 'rect',
        x: band(String(index)) ?? 0,
        y: top,
        w: band.bandwidth(),
        h: Math.max(2, bottom - top),
        fill: spec.waterfall!.color[index] ?? chartTheme.play,
        rx: 3,
      })
    })
    return marks
  }
  const groups = spec.series.length
  spec.series.forEach((series, seriesIndex) => {
    spec.categories.forEach((category, index) => {
      const value = series.values[index] ?? 0
      const top = scale(Math.max(value, 0))
      const bottom = scale(Math.min(value, 0))
      const slot = band.bandwidth() / groups
      marks.push({
        type: 'rect',
        x: (band(String(index)) ?? 0) + seriesIndex * slot,
        y: top,
        w: Math.max(2, slot - 3),
        h: Math.max(2, bottom - top),
        fill: series.colors?.[index] ?? series.color,
        rx: 3,
      })
    })
  })
  if (spec.series.length > 1) legend(marks, spec.series.map(series => ({ name: series.name, color: series.color })), width)
  return marks
}

function layoutHBar(spec: Extract<ChartSpec, { kind: 'hbar' }>, width: number, height: number): Mark[] {
  const marks: Mark[] = []
  const [min, max] = domain(spec.values, true)
  const scale = linearScale([min, max], width)
  const band = bandScale(spec.categories, height, 0.22)
  for (const tick of niceTicks(min, max, 3)) {
    const x = scale(tick)
    marks.push({ type: 'line', x1: x, y1: 0, x2: x, y2: height, stroke: GRID, width: 2 })
    marks.push({ type: 'text', x, y: height + 4, text: label(tick, spec.format, spec.digits), anchor: 'middle' })
  }
  if (min < 0 && max > 0) {
    marks.push({ type: 'line', x1: scale(0), y1: 0, x2: scale(0), y2: height, stroke: INK, width: 2, opacity: 0.45 })
  }
  spec.categories.forEach((category, index) => {
    const value = spec.values[index] ?? 0
    const x0 = scale(Math.min(value, 0))
    const x1 = scale(Math.max(value, 0))
    const y = band(category) ?? 0
    marks.push({
      type: 'text',
      x: -8,
      y: y + band.bandwidth() / 2,
      text: category,
      anchor: 'end',
    })
    marks.push({
      type: 'rect',
      x: x0,
      y,
      w: Math.max(2, x1 - x0),
      h: band.bandwidth(),
      fill: spec.colors[index] ?? chartTheme.play,
      rx: 3,
    })
  })
  return marks
}

function layoutLine(spec: Extract<ChartSpec, { kind: 'line' | 'area' }>, width: number, height: number): Mark[] {
  const marks: Mark[] = []
  const values = spec.series.flatMap(series => series.values)
  if (spec.guide != null) values.push(spec.guide)
  const [min, max] = domain(finite(values), spec.zero ?? false)
  const { marks: axis, scale } = yAxis(min, max, height, spec.format, spec.digits)
  for (const mark of axis) {
    if (mark.type === 'line' && mark.x2 === 1) marks.push({ ...mark, x2: width })
    else if (mark.type === 'line') marks.push({ ...mark, x2: width })
    else marks.push(mark)
  }
  const xScale = linearScale([0, Math.max(1, spec.labels.length - 1)], width)
  const every = spec.tickEvery ?? (spec.labels.length > 12 ? Math.ceil(spec.labels.length / 6) : 1)
  const sparse = spec.labels.filter(Boolean).length <= 8
  spec.labels.forEach((text, index) => {
    if (!text) return
    if (!sparse && spec.tickEvery == null && index % every !== 0 && index !== spec.labels.length - 1) return
    marks.push({ type: 'text', x: xScale(index), y: height + 16, text, anchor: 'middle' })
  })
  for (const shade of spec.shades ?? []) {
    const x0 = xScale(shade.from)
    const x1 = xScale(shade.to)
    marks.push({ type: 'rect', x: Math.min(x0, x1), y: 0, w: Math.abs(x1 - x0), h: height, fill: SHADE, opacity: 0.18 })
  }
  if (spec.rule != null) {
    const x = xScale(spec.rule)
    marks.push({ type: 'line', x1: x, y1: 0, x2: x, y2: height, stroke: chartTheme.action, width: 2, dash: '4 4' })
  }
  if (spec.guide != null) {
    const y = scale(spec.guide)
    marks.push({ type: 'line', x1: 0, y1: y, x2: width, y2: y, stroke: chartTheme.slate, width: 2, dash: '6 4' })
  }
  for (const series of spec.series) {
    const points = series.values.map((value, index) => (
      value == null || !Number.isFinite(value) ? null : [xScale(index), scale(value)] as const
    ))
    if (spec.kind === 'area') {
      let run: (readonly [number, number])[] = []
      const flush = () => {
        if (run.length < 2) {
          run = []
          return
        }
        const start = run[0]![0]
        const end = run[run.length - 1]![0]
        const d = `M${start},${scale(Math.max(min, 0))}` + run.map(point => `L${point[0]},${point[1]}`).join('') + `L${end},${scale(Math.max(min, 0))}Z`
        marks.push({ type: 'path', d, fill: series.color, opacity: 0.28 })
        run = []
      }
      for (const point of points) {
        if (!point) flush()
        else run.push(point)
      }
      flush()
    }
    for (const d of linePath(points)) {
      marks.push({
        type: 'path',
        d,
        stroke: series.color,
        fill: 'none',
        width: 3,
        dash: series.dash ? '6 4' : undefined,
      })
    }
  }
  if (spec.series.length > 1) legend(marks, spec.series.map(series => ({ name: series.name, color: series.color })), width)
  return marks
}

function layoutScatter(spec: Extract<ChartSpec, { kind: 'scatter' }>, width: number, height: number): Mark[] {
  const marks: Mark[] = []
  const xs = spec.points.map(point => point.x)
  const ys = spec.points.map(point => point.y)
  let [xMin, xMax] = domain(xs, false)
  let [yMin, yMax] = domain(ys, false)
  if (spec.parity) {
    const min = Math.min(xMin, yMin)
    const max = Math.max(xMax, yMax)
    xMin = yMin = min
    xMax = yMax = max
  }
  const xScale = linearScale([xMin, xMax], width)
  const yScale = linearScale([yMin, yMax], height, { vertical: true })
  for (const tick of niceTicks(yMin, yMax)) {
    const y = yScale(tick)
    marks.push({ type: 'line', x1: 0, y1: y, x2: width, y2: y, stroke: GRID, width: 2 })
    marks.push({ type: 'text', x: -8, y, text: label(tick, spec.formatY, spec.digitsY), anchor: 'end' })
  }
  for (const tick of niceTicks(xMin, xMax, 3)) {
    marks.push({ type: 'text', x: xScale(tick), y: height + 16, text: label(tick, spec.formatX, spec.digitsX), anchor: 'middle' })
  }
  if (spec.yLabel) marks.push({ type: 'text', x: 0, y: 10, text: spec.yLabel, anchor: 'start', fill: chartTheme.hand })
  if (spec.parity) {
    marks.push({
      type: 'line',
      x1: xScale(xMin),
      y1: yScale(xMin),
      x2: xScale(xMax),
      y2: yScale(xMax),
      stroke: chartTheme.slate,
      width: 2,
      dash: '6 4',
    })
  }
  const size = spec.points.length > 40 ? 5 : 8
  for (const point of spec.points) {
    marks.push({ type: 'rect', x: xScale(point.x) - size / 2, y: yScale(point.y) - size / 2, w: size, h: size, fill: point.color, rx: 1 })
    if (point.label && spec.points.length <= 8) {
      marks.push({ type: 'text', x: xScale(point.x) + size, y: yScale(point.y) - 8, text: point.label, anchor: 'start' })
    }
  }
  return marks
}

function layoutHeat(spec: Extract<ChartSpec, { kind: 'heatmap' }>, width: number, height: number): Mark[] {
  const marks: Mark[] = []
  const flat = spec.values.flat().filter((value): value is number => value != null && Number.isFinite(value))
  const min = Math.min(...flat, 0)
  const max = Math.max(...flat, 1)
  const span = max - min || 1
  const accent = spec.accent === 'action' ? chartTheme.action : chartTheme.play
  const cellW = width / Math.max(1, spec.cols.length)
  const cellH = height / Math.max(1, spec.rows.length)
  spec.rows.forEach((row, rowIndex) => {
    marks.push({ type: 'text', x: -8, y: rowIndex * cellH + cellH / 2, text: row, anchor: 'end' })
    spec.cols.forEach((col, colIndex) => {
      const value = spec.values[rowIndex]?.[colIndex]
      if (rowIndex === 0 && (spec.cols.length <= 8 || colIndex % 2 === 0)) {
        marks.push({ type: 'text', x: colIndex * cellW + cellW / 2, y: height + 16, text: col, anchor: 'middle' })
      }
      if (value == null || !Number.isFinite(value)) return
      const t = (value - min) / span
      marks.push({
        type: 'rect',
        x: colIndex * cellW + 2,
        y: rowIndex * cellH + 2,
        w: Math.max(2, cellW - 4),
        h: Math.max(2, cellH - 4),
        fill: mix(chartTheme.track, accent, 0.15 + 0.85 * t),
        rx: 3,
      })
    })
  })
  return marks
}

function layoutDonut(spec: Extract<ChartSpec, { kind: 'donut' }>, width: number, height: number): Mark[] {
  const marks: Mark[] = []
  const total = spec.slices.reduce((sum, slice) => sum + Math.max(0, slice.value), 0) || 1
  const legend = width >= 180
  const plot = legend ? Math.min(height, width * 0.58) : Math.min(width, height * 0.62)
  const cx = legend ? plot / 2 : width / 2
  const cy = legend ? height / 2 : plot / 2
  const radius = plot * 0.34
  const stroke = radius * 0.55
  let angle = -Math.PI / 2
  const gap = 0.04
  for (const slice of spec.slices) {
    const sweep = (Math.max(0, slice.value) / total) * Math.PI * 2
    const start = angle + gap / 2
    const end = angle + sweep - gap / 2
    angle += sweep
    if (end <= start) continue
    const r = radius
    const large = end - start > Math.PI ? 1 : 0
    const x0 = cx + r * Math.cos(start)
    const y0 = cy + r * Math.sin(start)
    const x1 = cx + r * Math.cos(end)
    const y1 = cy + r * Math.sin(end)
    marks.push({
      type: 'path',
      d: `M${x0},${y0}A${r},${r} 0 ${large} 1 ${x1},${y1}`,
      stroke: slice.color,
      fill: 'none',
      width: stroke,
    })
  }
  const legendX = legend ? plot + 8 : 8
  spec.slices.forEach((slice, index) => {
    const y = legend ? 16 + index * 26 : plot + 18 + index * 22
    const x = legendX
    marks.push({ type: 'rect', x, y: y - 8, w: 14, h: 14, fill: slice.color, rx: 2 })
    const share = formatValue(slice.value / total, 'pct', 0)
    marks.push({
      type: 'text',
      x: x + 20,
      y,
      text: `${slice.label} ${share}`,
      anchor: 'start',
    })
  })
  return marks
}

function layoutInterval(spec: Extract<ChartSpec, { kind: 'interval' }>, width: number, height: number): Mark[] {
  const marks: Mark[] = []
  const values = spec.rows.flatMap(row => [row.low, row.mid, row.high]).concat(spec.guides ?? [])
  const [min, max] = domain(finite(values), false)
  const scale = linearScale([min, max], width)
  const band = bandScale(spec.rows.map(row => row.label), height, 0.28)
  for (const tick of niceTicks(min, max, 3)) {
    const x = scale(tick)
    marks.push({ type: 'line', x1: x, y1: 0, x2: x, y2: height, stroke: GRID, width: 2 })
    marks.push({ type: 'text', x, y: height + 4, text: label(tick, spec.format, spec.digits), anchor: 'middle' })
  }
  for (const guide of spec.guides ?? []) {
    const x = scale(guide)
    marks.push({ type: 'line', x1: x, y1: 0, x2: x, y2: height, stroke: chartTheme.slate, width: 2, dash: '4 4' })
  }
  for (const row of spec.rows) {
    const y = (band(row.label) ?? 0) + band.bandwidth() / 2
    marks.push({ type: 'text', x: -8, y, text: row.label, anchor: 'end' })
    const left = scale(Math.min(row.low, row.high))
    const right = scale(Math.max(row.low, row.high))
    if (Math.abs(row.low - row.high) > (max - min) * 0.01) {
      marks.push({ type: 'line', x1: left, y1: y, x2: right, y2: y, stroke: chartTheme.play, width: 4 })
    }
    marks.push({ type: 'rect', x: scale(row.mid) - 6, y: y - 6, w: 12, h: 12, fill: chartTheme.action, rx: 2 })
  }
  return marks
}

function legend(marks: Mark[], items: { name: string, color: string }[], width: number) {
  let x = width
  for (const item of [...items].reverse()) {
    const textW = item.name.length * 11 + 22
    x -= textW
    if (x < 0) break
    marks.push({ type: 'rect', x, y: 2, w: 12, h: 12, fill: item.color, rx: 2 })
    marks.push({ type: 'text', x: x + 16, y: 8, text: item.name, anchor: 'start' })
  }
}
