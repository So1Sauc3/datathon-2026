<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from 'cn'

defineProps<{
  chips: string | number
  mult: string | number
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <span
    :class="cn('inline-flex items-center gap-2 rounded-full bg-capsule px-2 py-1', $props.class)"
  >
    <span class="rounded-[14px] bg-play px-3 py-1 text-[35px] text-white [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
      {{ chips }}
    </span>
    <span class="text-[35px] text-action">X</span>
    <span class="rounded-[14px] bg-action px-3 py-1 text-[35px] text-white [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
      {{ mult }}
    </span>
  </span>
</template>
