<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { cn } from "cn"
import { DialogClose } from "reka-ui"
import { Button } from '@/components/ui/button'

const props = withDefaults(defineProps<{
  class?: HTMLAttributes["class"]
  showCloseButton?: boolean
}>(), {
  showCloseButton: false,
})
</script>

<template>
  <div
    data-slot="dialog-footer"
    :class="cn('flex flex-col gap-[15px]', props.class)"
  >
    <slot />
    <DialogClose v-if="showCloseButton" as-child>
      <Button variant="back" size="row" class="w-full">
        Back
      </Button>
    </DialogClose>
  </div>
</template>
