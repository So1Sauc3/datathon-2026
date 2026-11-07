<script setup lang="ts">
import { claimsFor } from '~/lib/dashboard/catalog'

const { back } = useModalStack()
const cells = claimsFor('q3')
</script>

<template>
  <ModalShell title="Downtime" @back="back">
    <BentoGrid>
      <BentoCell
        v-for="cell in cells"
        :key="cell.id"
        :claim-id="cell.id"
        :class="cell.id === 'Q3-total' ? 'lg:col-span-2' : ''"
      />
    </BentoGrid>
  </ModalShell>
</template>
