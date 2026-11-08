<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { cn } from 'cn'

const props = withDefaults(defineProps<{
  selected?: boolean
  disabled?: boolean
  inert?: boolean
  tone?: 'action' | 'play' | 'back' | 'collection' | 'slate' | 'paper'
  class?: HTMLAttributes['class']
}>(), {
  selected: false,
  disabled: false,
  inert: false,
  tone: 'action',
})

const toneClass = computed(() => {
  const ink = 'text-white [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]'
  if (props.tone === 'paper') {
    return props.selected
      ? 'bg-level text-ink'
      : 'bg-white text-ink hover:bg-level'
  }
  const fills = {
    action: props.selected ? 'bg-action-press' : 'bg-action hover:bg-action-press',
    play: props.selected ? 'bg-play-press' : 'bg-play hover:bg-play-press',
    back: props.selected ? 'bg-back-press' : 'bg-back hover:bg-back-press',
    collection: props.selected ? 'bg-collection-press' : 'bg-collection hover:bg-collection-press',
    slate: props.selected ? 'bg-track' : 'bg-slate hover:bg-track',
  } as const
  return cn(fills[props.tone], ink)
})
</script>

<template>
  <component
    :is="inert ? 'div' : 'button'"
    :type="inert ? undefined : 'button'"
    :disabled="inert ? undefined : disabled"
    :aria-pressed="inert ? undefined : selected"
    :class="cn(
      'flex h-full w-full flex-col gap-2 rounded-[14px] px-4 py-3 text-[25px] drop-shadow-control transition-[background-color,transform] duration-75 active:translate-y-[3px] disabled:pointer-events-none disabled:opacity-50',
      tone === 'paper' ? 'items-start text-left' : 'items-center justify-center text-center',
      toneClass,
      props.class,
    )"
  >
    <slot />
  </component>
</template>
