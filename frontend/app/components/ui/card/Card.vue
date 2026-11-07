<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { cn } from "cn"

const props = defineProps<{
  class?: HTMLAttributes["class"]
}>()
</script>

<template>
  <div
    data-slot="card"
    :class="
      cn(
        'flex flex-col gap-2 rounded-[19px] bg-white p-4 text-ink',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>
