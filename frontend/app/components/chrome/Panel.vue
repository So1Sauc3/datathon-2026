<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from 'cn'

const props = defineProps<{
  caret?: boolean
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <div
    :class="cn(
      'relative rounded-[28px] border-8 border-panel-line bg-panel text-white shadow-panel',
      props.class,
    )"
  >
    <span
      v-if="caret"
      class="absolute top-0 left-1/2 h-0 w-0 -translate-x-1/2 -translate-y-full border-x-[10px] border-t-[12px] border-solid border-x-transparent border-t-action"
      aria-hidden="true"
    />
    <slot />
  </div>
</template>
