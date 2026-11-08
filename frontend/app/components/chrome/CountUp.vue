<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { TransitionPresets, useTransition } from '@vueuse/core'

const props = defineProps<{
  value: string | number
}>()

const NUMBER = /((?:(?<!\w)-)?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)/

/** Odd indices hold the numeric tokens. */
const parts = computed(() => String(props.value).split(NUMBER))

const targets = computed(() =>
  parts.value.filter((_, index) => index % 2 === 1).map(token => Number(token.replace(/,/g, ''))),
)

const source = ref<number[]>(targets.value.map(() => 0))

const output = useTransition(source, {
  duration: 600,
  transition: TransitionPresets.easeOutCubic,
  interpolation: (from: number[], to: number[], alpha: number) =>
    to.map((target, index) => (from[index] ?? 0) + alpha * (target - (from[index] ?? 0))),
})

function format(amount: number, token: string) {
  const [whole = '', fraction = ''] = token.replace('-', '').split('.')
  return amount.toLocaleString('en-US', {
    minimumIntegerDigits: whole.startsWith('0') ? whole.length : 1,
    minimumFractionDigits: fraction.length,
    maximumFractionDigits: fraction.length,
    useGrouping: whole.includes(','),
  })
}

const text = computed(() => {
  let slot = 0
  return parts.value
    .map((part, index) => (index % 2 === 1 ? format(output.value[slot++] ?? 0, part) : part))
    .join('')
})

onMounted(() => {
  source.value = targets.value
})

watch(targets, (next) => {
  source.value = next
})
</script>

<template>
  {{ text }}
</template>
