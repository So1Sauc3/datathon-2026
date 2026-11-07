<script setup lang="ts">
import { ref } from 'vue'
import { claimsFor } from '~/lib/dashboard/catalog'

const { back } = useModalStack()
const tokens = claimsFor('q4')
const active = ref(tokens[0]?.id ?? '')
</script>

<template>
  <ModalShell title="Players" @back="back">
    <div class="grid items-start gap-[15px] lg:grid-cols-[minmax(0,3fr)_220px]">
      <div class="flex min-w-0 flex-col gap-[15px]">
        <PlaceholderWell kind="chart" :claim-id="active" :height="300" />
        <PlaceholderWell kind="finding" :claim-id="active" />
      </div>
      <div class="flex flex-col gap-3">
        <ChoiceCard
          v-for="token in tokens"
          :key="token.id"
          tone="action"
          class="min-h-[72px]"
          :selected="active === token.id"
          :data-token="token.id"
          @click="active = token.id"
        >
          <span class="text-[22px]">{{ token.label }}</span>
        </ChoiceCard>
      </div>
    </div>
  </ModalShell>
</template>
