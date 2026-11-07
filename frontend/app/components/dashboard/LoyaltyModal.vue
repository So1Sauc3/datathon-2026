<script setup lang="ts">
import { claimsFor } from '~/lib/dashboard/catalog'

const { back } = useModalStack()
const cells = claimsFor('q5')
</script>

<template>
  <ModalShell title="Loyalty" @back="back">
    <BentoGrid>
      <BentoCell
        v-for="cell in cells"
        :key="cell.id"
        :claim-id="cell.id"
        :class="cell.id === 'Q5-change' ? 'lg:col-span-2' : ''"
      />
    </BentoGrid>
  </ModalShell>
</template>
