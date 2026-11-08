<script setup lang="ts">
import { computed } from 'vue'
import { chartTheme } from '~/lib/d3/theme'
import type { ChartKind } from '~/lib/dashboard/layouts'

const props = defineProps<{
  kind: ChartKind
  width: number
  height: number
  seed: string
}>()

const GHOST = chartTheme.slate
const GRID = chartTheme.well

/** Seeded so server, client, and every resize draw the same skeleton. */
function generator() {
  let state = 0
  for (const char of props.seed) state = (state * 31 + char.charCodeAt(0)) >>> 0
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0
    return state / 2 ** 32
  }
}

function series(count: number) {
  const next = generator()
  return Array.from({ length: count }, () => 0.2 + 0.7 * next())
}

const gridLines = computed(() => [0, 0.25, 0.5, 0.75, 1].map(step => step * props.height))

const bars = computed(() => {
  const values = series(props.width > 520 ? 12 : 7)
  const band = props.width / values.length
  return values.map((value, index) => ({
    x: index * band + band * 0.18,
    y: props.height * (1 - value),
    width: band * 0.64,
    height: props.height * value,
  }))
})

const rows = computed(() => {
  const values = series(6).sort((a, b) => b - a)
  const band = props.height / values.length
  return values.map((value, index) => ({
    y: index * band + band * 0.2,
    width: props.width * value,
    height: band * 0.6,
  }))
})

const points = computed(() => {
  const values = series(16)
  return values.map((value, index) => [
    (index / (values.length - 1)) * props.width,
    props.height * (1 - value),
  ] as const)
})

const linePath = computed(() => points.value.map(([x, y], index) => `${index ? 'L' : 'M'}${x},${y}`).join(''))
const areaPath = computed(() => `${linePath.value}L${props.width},${props.height}L0,${props.height}Z`)

const dots = computed(() => {
  const next = generator()
  return Array.from({ length: 36 }, () => {
    const x = next()
    return { x: x * (props.width - 10), y: (1 - (0.15 + 0.6 * x + 0.25 * next())) * (props.height - 10) }
  })
})

const cells = computed(() => {
  const cols = props.width > 520 ? 12 : 8
  const rowCount = 7
  const next = generator()
  const cellWidth = props.width / cols
  const cellHeight = props.height / rowCount
  return Array.from({ length: cols * rowCount }, (_, index) => ({
    x: (index % cols) * cellWidth + 2,
    y: Math.floor(index / cols) * cellHeight + 2,
    width: cellWidth - 4,
    height: cellHeight - 4,
    opacity: 0.15 + 0.75 * next(),
  }))
})

const donut = computed(() => {
  const outer = Math.min(props.width, props.height) / 2
  const stroke = outer * 0.4
  const radius = Math.max(0, outer - stroke / 2)
  const circumference = 2 * Math.PI * radius
  const shares = series(4)
  const total = shares.reduce((sum, share) => sum + share, 0)
  let offset = 0
  return {
    radius,
    stroke,
    segments: shares.map((share, index) => {
      const length = (share / total) * circumference
      const segment = { dash: `${Math.max(0, length - 6)} ${circumference}`, offset: -offset, opacity: 0.85 - index * 0.2 }
      offset += length
      return segment
    }),
  }
})

const intervals = computed(() => {
  const values = series(5)
  const next = generator()
  const band = props.height / values.length
  return values.map((value, index) => {
    const center = props.width * (0.3 + 0.4 * value)
    const spread = props.width * (0.06 + 0.12 * next())
    return { y: index * band + band / 2, from: center - spread, to: center + spread, center }
  })
})
</script>

<template>
  <g v-if="width > 0 && height > 0" aria-hidden="true">
    <g v-if="kind !== 'donut' && kind !== 'heatmap'">
      <line
        v-for="y in gridLines"
        :key="y"
        :x1="0"
        :x2="width"
        :y1="y"
        :y2="y"
        :stroke="GRID"
        stroke-width="2"
      />
    </g>

    <g v-if="kind === 'bar'">
      <rect
        v-for="(bar, index) in bars"
        :key="index"
        v-bind="bar"
        :fill="GHOST"
        fill-opacity="0.55"
        rx="4"
      />
    </g>

    <g v-else-if="kind === 'hbar'">
      <rect
        v-for="(bar, index) in rows"
        :key="index"
        x="0"
        v-bind="bar"
        :fill="GHOST"
        fill-opacity="0.55"
        rx="4"
      />
    </g>

    <g v-else-if="kind === 'line' || kind === 'area'">
      <path v-if="kind === 'area'" :d="areaPath" :fill="GHOST" fill-opacity="0.3" />
      <path :d="linePath" fill="none" :stroke="GHOST" stroke-width="4" stroke-linejoin="miter" />
    </g>

    <g v-else-if="kind === 'scatter'">
      <rect
        v-for="(dot, index) in dots"
        :key="index"
        :x="dot.x"
        :y="dot.y"
        width="10"
        height="10"
        :fill="GHOST"
        fill-opacity="0.6"
      />
    </g>

    <g v-else-if="kind === 'heatmap'">
      <rect
        v-for="(cell, index) in cells"
        :key="index"
        :x="cell.x"
        :y="cell.y"
        :width="cell.width"
        :height="cell.height"
        :fill="GHOST"
        :fill-opacity="cell.opacity"
        rx="3"
      />
    </g>

    <g v-else-if="kind === 'donut'" :transform="`translate(${width / 2},${height / 2}) rotate(-90)`">
      <circle :r="donut.radius" fill="none" :stroke="GRID" :stroke-width="donut.stroke" />
      <circle
        v-for="(segment, index) in donut.segments"
        :key="index"
        :r="donut.radius"
        fill="none"
        :stroke="GHOST"
        :stroke-opacity="segment.opacity"
        :stroke-width="donut.stroke"
        :stroke-dasharray="segment.dash"
        :stroke-dashoffset="segment.offset"
      />
    </g>

    <g v-else-if="kind === 'interval'">
      <line :x1="width / 2" :x2="width / 2" y1="0" :y2="height" :stroke="GRID" stroke-width="2" stroke-dasharray="6 6" />
      <g v-for="(row, index) in intervals" :key="index">
        <line :x1="row.from" :x2="row.to" :y1="row.y" :y2="row.y" :stroke="GHOST" stroke-width="4" />
        <rect :x="row.center - 7" :y="row.y - 7" width="14" height="14" :fill="GHOST" />
      </g>
    </g>
  </g>
</template>
