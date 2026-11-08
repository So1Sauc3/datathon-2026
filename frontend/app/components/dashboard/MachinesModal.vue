<script setup lang="ts">
import { claimsFor } from '~/lib/dashboard/catalog'
import { claimArt } from '~/lib/dashboard/art'

const { open, back } = useModalStack()
const packs = claimsFor('q1')
</script>

<template>
  <ModalShell title="Machines" @back="back">
    <div class="flex flex-wrap justify-center gap-[15px]">
      <SpriteButton
        v-for="pack in packs"
        :key="pack.id"
        :src="claimArt(pack.id).src"
        :label="pack.label"
        :data-pack="pack.id"
        @click="open('q1-claim', pack.id)"
      />
    </div>
  </ModalShell>
</template>
