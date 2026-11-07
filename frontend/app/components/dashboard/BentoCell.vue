<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { cn } from 'cn'
import { claimById } from '~/lib/dashboard/catalog'

const props = defineProps<{
  claimId: string
  class?: HTMLAttributes['class']
}>()

const claim = computed(() => claimById(props.claimId))
</script>

<template>
  <section :class="cn('flex min-w-0 flex-col gap-3', props.class)">
    <h3 class="text-[35px]">
      {{ claim?.label ?? claimId }}
    </h3>
    <PlaceholderWell kind="chart" :claim-id="claimId" :height="160" />
    <PlaceholderWell kind="finding" :claim-id="claimId" />
  </section>
</template>
