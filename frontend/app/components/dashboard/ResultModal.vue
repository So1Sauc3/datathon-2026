<script setup lang="ts">
import { useId } from 'vue'
import { formatDollars } from '~/lib/dashboard/catalog'

defineProps<{
  outcome: 'win' | 'lose'
  spent: number
  kept: number
  types: number
}>()

const emit = defineEmits<{
  menu: []
  again: []
}>()

const titleId = useId()
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
    <div
      role="dialog"
      aria-modal="true"
      :aria-labelledby="titleId"
      class="w-full max-w-[520px]"
      :data-result="outcome"
    >
      <Panel class="flex flex-col gap-[15px] p-6">
        <h2
          :id="titleId"
          class="text-center text-[65px]"
          :class="outcome === 'win' ? 'text-play' : 'text-action'"
        >
          {{ outcome === 'win' ? 'YOU WIN' : 'GAME OVER' }}
        </h2>
        <ul class="flex flex-col gap-2">
          <li class="flex items-center justify-between rounded-[14px] bg-white px-4 py-3 text-[25px] text-ink">
            <span>Spent</span>
            <span class="text-action">{{ formatDollars(spent) }}</span>
          </li>
          <li class="flex items-center justify-between rounded-[14px] bg-white px-4 py-3 text-[25px] text-ink">
            <span>Kept</span>
            <span class="text-action">{{ formatDollars(kept) }}</span>
          </li>
          <li class="flex items-center justify-between rounded-[14px] bg-white px-4 py-3 text-[25px] text-ink">
            <span>Types</span>
            <span class="text-action">{{ types }}</span>
          </li>
        </ul>
        <div class="flex flex-col gap-[15px]">
          <Button variant="action" size="row" type="button" class="w-full" @click="emit('again')">
            New run
          </Button>
          <Button variant="back" size="row" type="button" class="w-full" data-menu="leave" @click="emit('menu')">
            Main menu
          </Button>
        </div>
      </Panel>
    </div>
  </div>
</template>
