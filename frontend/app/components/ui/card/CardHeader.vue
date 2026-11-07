<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { cn } from "cn"

const props = defineProps<{
  class?: HTMLAttributes["class"]
}>()
</script>

<template>
  <div
    data-slot="card-header"
    :class="cn('grid auto-rows-min grid-rows-[auto_auto] items-start gap-2', props.class)"
  >
    <slot />
  </div>
</template>
