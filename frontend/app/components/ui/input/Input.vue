<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { useVModel } from '@vueuse/core'
import { cn } from 'cn'

const props = defineProps<{
  defaultValue?: string | number
  modelValue?: string | number
  class?: HTMLAttributes['class']
}>()

const emits = defineEmits<{
  (e: 'update:modelValue', payload: string | number): void
}>()

const modelValue = useVModel(props, 'modelValue', emits, {
  passive: true,
  defaultValue: props.defaultValue,
})
</script>

<template>
  <input
    v-model="modelValue"
    data-slot="input"
    :class="cn(
      'h-[50px] w-full min-w-0 rounded-[14px] bg-play/75 px-4 text-center text-[25px] text-white/75 outline-none placeholder:text-white/75 hover:bg-play/90 focus:bg-play/90 disabled:pointer-events-none disabled:opacity-50',
      props.class,
    )"
  >
</template>
