<script setup lang="ts">
import { claimsFor } from '~/lib/dashboard/catalog'

const { open, back } = useModalStack()
const packs = claimsFor('q1')
</script>

<template>
  <ModalShell title="Machines" @back="back">
    <div class="grid grid-cols-2 gap-[15px] sm:grid-cols-3">
      <ChoiceCard
        v-for="pack in packs"
        :key="pack.id"
        tone="collection"
        class="min-h-[140px]"
        :data-pack="pack.id"
        @click="open('q1-claim', pack.id)"
      >
        <span class="text-[35px]">{{ pack.label }}</span>
      </ChoiceCard>
    </div>
  </ModalShell>
</template>
