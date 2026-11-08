<script setup lang="ts">
import { onMounted, ref, useId } from 'vue'

defineProps<{
  title: string
}>()

const emit = defineEmits<{
  back: []
}>()

const titleId = useId()
const root = ref<HTMLElement | null>(null)

onMounted(() => {
  root.value?.focus()
})
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
    <div
      ref="root"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="titleId"
      data-modal-panel
      class="flex max-h-[calc(100vh-2rem)] w-full max-w-[1120px] outline-none"
    >
      <Panel class="flex max-h-full w-full flex-col gap-[15px] p-6">
        <h2 :id="titleId" class="text-[40px]">
          {{ title }}
        </h2>
        <div class="min-h-0 flex-1 overflow-auto">
          <slot />
        </div>
        <Button
          variant="back"
          size="row"
          type="button"
          class="w-full shrink-0"
          @click="emit('back')"
        >
          Back
        </Button>
      </Panel>
    </div>
  </div>
</template>
