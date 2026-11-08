<script setup lang="ts">
import type { ChartKind } from '~/lib/dashboard/layouts'

defineProps<{
  title: string
  chart: ChartKind
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
        :margin="{ top: 16, right: 16, bottom: 16, left: 16 }"
        :aria-label="`${title} chart placeholder`"
      >
        <ChartGhost :kind="chart" :width="innerWidth" :height="innerHeight" :seed="title" />
      </ChartFrame>
    </div>
  </DashTile>
</template>
