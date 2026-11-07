<script setup lang="ts">
import { computed } from 'vue'
import { claimById } from '~/lib/dashboard/catalog'
import { chartTheme } from '~/lib/d3/theme'

const props = withDefaults(defineProps<{
  claimId: string
  kind: 'chart' | 'finding'
  height?: number
}>(), {
  height: 220,
})

const claim = computed(() => claimById(props.claimId))
const heading = computed(() => props.kind === 'chart' ? 'Chart' : 'Finding')
</script>

<template>
  <section class="flex min-w-0 flex-col gap-2" :data-claim="claimId" :data-kind="kind">
    <p class="text-[22px] text-white/75">
      {{ heading }} · {{ claim?.label ?? claimId }}
    </p>
    <ChartFrame
      v-if="kind === 'chart'"
      v-slot="{ innerWidth, innerHeight }"
      class="rounded-[19px] bg-shell"
      :height="height"
      :aria-label="`${heading} placeholder for ${claimId}`"
    >
      <rect
        :width="innerWidth"
        :height="innerHeight"
        :fill="chartTheme.well"
        rx="8"
      />
    </ChartFrame>
    <Card v-else class="min-h-[120px]">
      <p class="text-[25px] text-muted">
        Placeholder
      </p>
      <p v-if="claim" class="text-[20px] text-muted">
        {{ claim.dataFiles.join(', ') }}
      </p>
    </Card>
  </section>
</template>
