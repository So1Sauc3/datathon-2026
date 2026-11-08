<script setup lang="ts">
import { computed } from 'vue'
import type { ChartSpec } from '~/lib/dashboard/charts'
import type { ChartKind } from '~/lib/dashboard/layouts'
import type { ChartMargin } from '~/components/charts/ChartFrame.vue'

const props = defineProps<{
  title: string
  chart: ChartKind
  spec?: ChartSpec
}>()

const KIND_LABEL: Record<ChartKind, string> = {
  bar: 'Bar',
  hbar: 'Ranked bar',
  line: 'Line',
  area: 'Area',
  scatter: 'Scatter',
  heatmap: 'Heatmap',
  donut: 'Donut',
  interval: 'Interval',
}

const MARGIN: Record<ChartKind, ChartMargin> = {
  bar: { top: 22, right: 8, bottom: 36, left: 84 },
  hbar: { top: 8, right: 12, bottom: 28, left: 120 },
  line: { top: 22, right: 8, bottom: 36, left: 84 },
  area: { top: 22, right: 8, bottom: 36, left: 84 },
  scatter: { top: 22, right: 12, bottom: 36, left: 84 },
  heatmap: { top: 8, right: 8, bottom: 32, left: 120 },
  donut: { top: 8, right: 8, bottom: 8, left: 8 },
  interval: { top: 8, right: 16, bottom: 28, left: 96 },
}

const margin = computed(() => (props.spec ? MARGIN[props.chart] : { top: 16, right: 16, bottom: 16, left: 16 }))
</script>

<template>
  <DashTile :title="title" data-tile="chart" :data-chart="chart">
    <template #aside>
      <span class="shrink-0 text-[20px] text-white/50">{{ KIND_LABEL[chart] }}</span>
    </template>
    <div class="relative min-h-0 flex-1 rounded-[16px] bg-sidebar-well shadow-lift">
      <ChartFrame
        v-slot="{ innerWidth, innerHeight }"
        fill
        class="absolute inset-0"
        :margin="margin"
        :aria-label="spec?.aria ?? `${title} chart placeholder`"
      >
        <ChartMark v-if="spec" :spec="spec" :width="innerWidth" :height="innerHeight" />
        <ChartGhost v-else :kind="chart" :width="innerWidth" :height="innerHeight" :seed="title" />
      </ChartFrame>
    </div>
  </DashTile>
</template>
