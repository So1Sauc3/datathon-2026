<script setup lang="ts">
import { computed } from 'vue'
import { claimById } from '~/lib/dashboard/catalog'

const { top, back } = useModalStack()
const claim = computed(() => claimById(top.value?.payload ?? ''))
</script>

<template>
  <ModalShell :title="claim?.label ?? 'Claim'" @back="back">
    <DashboardGrid v-if="claim" :claim-id="claim.id" :framed="false" />
  </ModalShell>
</template>
