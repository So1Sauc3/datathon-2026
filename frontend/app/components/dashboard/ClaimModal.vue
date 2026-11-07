<script setup lang="ts">
import { computed } from 'vue'
import { claimById } from '~/lib/dashboard/catalog'

const { top, back } = useModalStack()
const claim = computed(() => claimById(top.value?.payload ?? ''))
</script>

<template>
  <ModalShell :title="claim?.label ?? 'Claim'" @back="back">
    <div v-if="claim" class="flex flex-col gap-[15px]">
      <PlaceholderWell kind="chart" :claim-id="claim.id" :height="280" />
      <PlaceholderWell kind="finding" :claim-id="claim.id" />
    </div>
  </ModalShell>
</template>
