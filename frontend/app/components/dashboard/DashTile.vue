<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from 'cn'

const props = defineProps<{
  title: string
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <section
    :class="cn(
      'flex min-h-0 min-w-0 flex-col gap-[6px] rounded-[16px] bg-sidebar-box px-3 pb-3 pt-[7px] shadow-lift',
      props.class,
    )"
  >
    <header class="flex min-w-0 items-baseline justify-between gap-3">
      <h3 class="min-w-0 text-[25px] text-white [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
        {{ title }}
      </h3>
      <slot name="aside" />
    </header>
    <slot />
  </section>
</template>
