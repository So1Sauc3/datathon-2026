<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, ref, watch } from 'vue'
import { cn } from 'cn'

const props = withDefaults(defineProps<{
  src: string
  label: string
  selected?: boolean
  disabled?: boolean
  inert?: boolean
  hideLabel?: boolean
  size?: 'card' | 'pack' | 'token' | 'hand' | 'shelf'
  class?: HTMLAttributes['class']
}>(), {
  selected: false,
  disabled: false,
  inert: false,
  hideLabel: false,
  size: 'card',
})

const MAX_TILT = 14

const widthClass = computed(() => {
  if (props.size === 'pack') return 'w-[171px]'
  if (props.size === 'token') return 'w-[112px]'
  if (props.size === 'hand') return 'w-[142px]'
  if (props.size === 'shelf') return 'w-[124px]'
  return 'w-[162px]'
})

const imageClass = computed(() => {
  if (props.size === 'shelf') return 'w-[81px]'
  if (props.size === 'token') return 'w-full rounded-full'
  return 'w-full'
})

const ringClass = computed(() => {
  if (props.inert) return ''
  if (!props.selected) return 'hover:ring-4 hover:ring-white'
  if (props.size === 'token') return 'ring-4 ring-white'
  return 'shadow-stack ring-4 ring-white'
})

const tilt = ref<{ x: number, y: number } | null>(null)

const tiltStyle = computed(() => {
  if (!tilt.value) return undefined
  const { x, y } = tilt.value
  return { transform: `perspective(500px) rotateX(${-y * MAX_TILT}deg) rotateY(${x * MAX_TILT}deg) scale(1.06)` }
})

function onPointerMove(event: PointerEvent) {
  if (props.inert || props.disabled) return
  const box = (event.currentTarget as HTMLElement).getBoundingClientRect()
  tilt.value = {
    x: (event.clientX - box.left) / box.width - 0.5,
    y: (event.clientY - box.top) / box.height - 0.5,
  }
}

function onPointerLeave() {
  tilt.value = null
}

watch(() => props.disabled, onPointerLeave)
</script>

<template>
  <component
    :is="inert ? 'div' : 'button'"
    :type="inert ? undefined : 'button'"
    :disabled="inert ? undefined : disabled"
    :aria-pressed="inert ? undefined : selected"
    :class="cn(
      'flex shrink-0 flex-col items-center gap-2 text-center disabled:pointer-events-none disabled:opacity-50',
      widthClass,
      props.class,
    )"
    @pointermove="onPointerMove"
    @pointerleave="onPointerLeave"
  >
    <img
      :src="src"
      alt=""
      draggable="false"
      :class="cn('select-none transition-transform duration-150 ease-out [image-rendering:pixelated] drop-shadow-control', imageClass, ringClass)"
      :style="tiltStyle"
    >
    <span
      :class="hideLabel
        ? 'sr-only'
        : 'line-clamp-3 text-[22px] text-white [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]'"
    >
      {{ label }}
    </span>
    <slot />
  </component>
</template>
