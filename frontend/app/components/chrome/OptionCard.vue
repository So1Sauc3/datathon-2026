<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from 'cn'

const props = defineProps<{
  title: string
  description?: string
  page: number
  pages: number
  class?: HTMLAttributes['class']
}>()

const emit = defineEmits<{
  'update:page': [value: number]
  next: []
}>()

function advance() {
  if (props.pages === 0) return
  emit('update:page', (props.page + 1) % props.pages)
  emit('next')
}
</script>

<template>
  <div :class="cn('rounded-[28px] bg-shell p-4 text-white shadow-panel', props.class)">
    <div class="flex items-stretch gap-4">
      <div class="flex w-[140px] shrink-0 items-center justify-center rounded-[19px] bg-well p-3 text-center text-[40px]">
        <slot />
      </div>
      <div class="flex min-w-0 flex-1 flex-col gap-2">
        <h3 class="text-[40px]">
          {{ title }}
        </h3>
        <Card>
          <p class="text-[25px] text-ink">
            <slot name="description">
              {{ description }}
            </slot>
          </p>
        </Card>
      </div>
      <Button
        type="button"
        variant="action"
        size="row"
        class="w-[72px] self-stretch"
        aria-label="Next"
        @click="advance"
      >
        &gt;
      </Button>
    </div>
    <DotPager
      class="mt-4"
      :count="pages"
      :model-value="page"
      @update:model-value="emit('update:page', $event)"
    />
  </div>
</template>
