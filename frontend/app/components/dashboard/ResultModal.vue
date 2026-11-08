<script setup lang="ts">
import { computed, useId } from 'vue'
import { TYPE_CAP, formatDollars } from '~/lib/dashboard/catalog'
import { layoutFor, pair, stat, type TileDef } from '~/lib/dashboard/layouts'

const props = defineProps<{
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

const tiles = computed<TileDef[]>(() => [
  { ...pair('Your run', 'Spent', 'Kept', 6), values: [formatDollars(props.spent), formatDollars(props.kept)] },
  stat('Types', 'back', 3, 1, { value: `${props.types} / ${TYPE_CAP}` }),
  stat('Net benefit', 'collection', 3, 1, { fill: true, caption: 'recommended, mid case' }),
  ...layoutFor('Q6-portfolio'),
])
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
    <div
      role="dialog"
      aria-modal="true"
      :aria-labelledby="titleId"
      class="flex max-h-[calc(100vh-2rem)] w-full max-w-[1120px]"
      :data-result="outcome"
    >
      <Panel class="flex max-h-full w-full flex-col gap-[15px] p-6">
        <h2
          :id="titleId"
          class="shrink-0 text-center text-[65px]"
          :class="outcome === 'win' ? 'text-play' : 'text-action'"
        >
          {{ outcome === 'win' ? 'YOU WIN' : 'GAME OVER' }}
        </h2>
        <div class="min-h-0 flex-1 overflow-auto">
          <DashboardGrid claim-id="Q6-portfolio" :framed="false" :tiles="tiles" />
        </div>
        <div class="flex shrink-0 flex-col gap-[15px]">
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
