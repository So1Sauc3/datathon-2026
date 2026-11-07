<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from 'cn'

defineProps<{
  level: string | number
  name: string
  chips: string | number
  mult: string | number
  count: string | number
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <div
    :class="cn(
      'flex items-center gap-3 rounded-[19px] bg-hand px-3 py-2',
      $props.class,
    )"
  >
    <Badge variant="level">
      {{ level }}
    </Badge>
    <span class="min-w-0 flex-1 text-[40px] text-capsule">
      {{ name }}
    </span>
    <ScoreCapsule :chips="chips" :mult="mult" />
    <span class="text-[35px] text-capsule">#</span>
    <Badge variant="count">
      {{ count }}
    </Badge>
  </div>
</template>
