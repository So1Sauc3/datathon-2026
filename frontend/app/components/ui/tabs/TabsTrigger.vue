<script setup lang="ts">
import type { TabsTriggerProps } from "reka-ui"
import type { HTMLAttributes } from "vue"
import { reactiveOmit } from "@vueuse/core"
import { cn } from "cn"
import { TabsTrigger, useForwardProps } from "reka-ui"

const props = defineProps<TabsTriggerProps & { class?: HTMLAttributes["class"] }>()

const delegatedProps = reactiveOmit(props, "class")

const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <TabsTrigger
    data-slot="tabs-trigger"
    :class="cn(
      'group relative inline-flex items-center justify-center rounded-[14px] bg-action px-5 py-2 text-[35px] whitespace-nowrap text-white drop-shadow-control [text-shadow:0_4px_4px_rgba(0,0,0,0.25)] hover:bg-action-press active:bg-action-press disabled:pointer-events-none disabled:opacity-50',
      props.class,
    )"
    v-bind="forwardedProps"
  >
    <slot />
    <span
      class="absolute top-full left-1/2 hidden h-0 w-0 -translate-x-1/2 border-x-8 border-t-[12px] border-solid border-x-transparent border-t-action group-data-[state=active]:block"
      aria-hidden="true"
    />
  </TabsTrigger>
</template>
