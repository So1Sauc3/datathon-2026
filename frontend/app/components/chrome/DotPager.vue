<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from 'cn'

defineProps<{
  count: number
  modelValue: number
  class?: HTMLAttributes['class']
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()
</script>

<template>
  <div :class="cn('flex items-center justify-center gap-2', $props.class)">
    <button
      v-for="index in count"
      :key="index"
      type="button"
      class="size-[10px] rounded-full"
      :class="modelValue === index - 1 ? 'bg-white' : 'bg-black'"
      :aria-label="`Option ${index}`"
      :aria-current="modelValue === index - 1 ? 'true' : undefined"
      @click="emit('update:modelValue', index - 1)"
    />
  </div>
</template>
