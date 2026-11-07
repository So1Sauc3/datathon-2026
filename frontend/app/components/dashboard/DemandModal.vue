<script setup lang="ts">
import { ref } from 'vue'
import { claimsFor } from '~/lib/dashboard/catalog'

const { back } = useModalStack()
const cards = claimsFor('q2')
const active = ref(cards[0]?.id ?? '')
</script>

<template>
  <ModalShell title="Demand" @back="back">
    <div class="flex flex-col gap-[15px]">
      <div class="grid grid-cols-2 gap-[15px] lg:grid-cols-5">
        <ChoiceCard
          v-for="card in cards"
          :key="card.id"
          tone="action"
          class="min-h-[88px]"
          :selected="active === card.id"
          :data-choice="card.id"
          @click="active = card.id"
        >
          {{ card.label }}
        </ChoiceCard>
      </div>
      <div class="grid gap-[15px] lg:grid-cols-2">
        <PlaceholderWell kind="chart" :claim-id="active" :height="240" />
        <PlaceholderWell kind="finding" :claim-id="active" />
      </div>
    </div>
  </ModalShell>
</template>
