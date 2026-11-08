<script setup lang="ts">
import { computed } from 'vue'
import type { ChartSpec } from '~/lib/dashboard/charts'
import { layoutChart } from '~/lib/d3/layoutChart'
import { chartTheme } from '~/lib/d3/theme'

const props = defineProps<{
  spec: ChartSpec
  width: number
  height: number
}>()

const marks = computed(() => layoutChart(props.spec, props.width, props.height))
</script>

<template>
  <g v-if="width > 0 && height > 0" aria-hidden="true" style="font-family: m6x11plus, monospace">
    <template v-for="(mark, index) in marks" :key="index">
      <rect
        v-if="mark.type === 'rect'"
        :x="mark.x"
        :y="mark.y"
        :width="Math.max(0, mark.w)"
        :height="Math.max(0, mark.h)"
        :fill="mark.fill"
        :fill-opacity="mark.opacity ?? 1"
        :rx="mark.rx ?? 0"
      />
      <line
        v-else-if="mark.type === 'line'"
        :x1="mark.x1"
        :y1="mark.y1"
        :x2="mark.x2"
        :y2="mark.y2"
        :stroke="mark.stroke"
        :stroke-width="mark.width ?? 2"
        :stroke-dasharray="mark.dash"
        :stroke-opacity="mark.opacity ?? 1"
      />
      <path
        v-else-if="mark.type === 'path'"
        :d="mark.d"
        :stroke="mark.stroke ?? 'none'"
        :fill="mark.fill ?? 'none'"
        :stroke-width="mark.width ?? 3"
        :stroke-dasharray="mark.dash"
        :fill-opacity="mark.fill ? (mark.opacity ?? 1) : 0"
        :stroke-opacity="mark.opacity ?? 1"
        stroke-linejoin="miter"
      />
      <text
        v-else-if="mark.type === 'text'"
        :x="mark.x"
        :y="mark.y"
        :text-anchor="mark.anchor"
        dominant-baseline="middle"
        :fill="mark.fill ?? chartTheme.level"
        font-size="20"
      >
        {{ mark.text }}
      </text>
    </template>
  </g>
</template>
