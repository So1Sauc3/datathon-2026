<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from 'cn'

const props = defineProps<{
  options: string[]
  modelValue: number
  class?: HTMLAttributes['class']
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

function cycle() {
  if (props.options.length === 0) return
  emit('update:modelValue', (props.modelValue + 1) % props.options.length)
}
</script>

<template>
  <div :class="cn('inline-flex flex-col items-center gap-2', props.class)">
    <Button type="button" variant="action" size="row" @click="cycle">
      {{ options[modelValue] }}
    </Button>
    <div class="flex items-center justify-center gap-2">
      <span
        v-for="(_, index) in options"
        :key="index"
        class="size-[10px] rounded-full"
        :class="index === modelValue ? 'bg-white' : 'bg-black'"
      />
    </div>
  </div>
</template>
