<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, ref } from 'vue'
import { cn } from 'cn'
import { useChartBox } from '~/composables/useChartBox'

export interface ChartMargin {
  top: number
  right: number
  bottom: number
  left: number
}

const props = withDefaults(defineProps<{
  margin?: ChartMargin
  height?: number
  fill?: boolean
  class?: HTMLAttributes['class']
  ariaLabel?: string
}>(), {
  margin: () => ({ top: 24, right: 24, bottom: 24, left: 24 }),
  height: 280,
})

const frame = ref<HTMLElement | null>(null)
const { width, height: measuredHeight } = useChartBox(frame)

const innerWidth = computed(() => Math.max(0, width.value - props.margin.left - props.margin.right))
const innerHeight = computed(() => Math.max(0, measuredHeight.value - props.margin.top - props.margin.bottom))
</script>

<template>
  <div
    ref="frame"
    :class="cn('w-full', fill && 'h-full', props.class)"
    :style="fill ? undefined : { height: `${height}px` }"
  >
    <svg
      :width="width"
      :height="measuredHeight"
      class="block"
      role="img"
      :aria-label="ariaLabel"
    >
      <g :transform="`translate(${margin.left},${margin.top})`">
        <slot
          :width="width"
          :height="measuredHeight"
          :inner-width="innerWidth"
          :inner-height="innerHeight"
        />
      </g>
    </svg>
  </div>
</template>
