<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { MENU, type MenuEntry } from '~/lib/dashboard/catalog'

useHead({ title: 'The Gilded Ace' })

const { top, openRoot, back } = useModalStack()

function openQuestion(id: MenuEntry['id']) {
  if (id === 'q6') return
  openRoot(id)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape' || !top.value) return
  event.preventDefault()
  back()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <main class="flex min-h-screen flex-col px-6 pb-8">
    <div class="flex flex-1 items-center justify-center">
      <h1 class="text-center text-[72px]">
        The Gilded Ace
      </h1>
    </div>
    <nav class="flex flex-wrap items-center justify-center gap-3" aria-label="Questions">
      <template v-for="item in MENU" :key="item.id">
        <Button v-if="item.to" as-child :variant="item.variant" size="row">
          <NuxtLink :to="item.to">
            {{ item.label }}
          </NuxtLink>
        </Button>
        <Button
          v-else
          :variant="item.variant"
          size="row"
          type="button"
          :data-menu="item.id"
          @click="openQuestion(item.id)"
        >
          {{ item.label }}
        </Button>
      </template>
    </nav>

    <MachinesModal v-if="top?.id === 'q1'" />
    <ClaimModal v-else-if="top?.id === 'q1-claim'" />
    <DemandModal v-else-if="top?.id === 'q2'" />
    <DowntimeModal v-else-if="top?.id === 'q3'" />
    <PlayersModal v-else-if="top?.id === 'q4'" />
    <LoyaltyModal v-else-if="top?.id === 'q5'" />
  </main>
</template>
