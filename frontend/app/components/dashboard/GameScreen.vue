<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { actionById, formatDollars } from '~/lib/dashboard/catalog'

const {
  actions,
  played,
  result,
  ready,
  spent,
  remaining,
  typeCount,
  playedCount,
  canPlay,
  play,
  playRecommended,
  commit,
  newRun,
} = usePortfolio()

function leave() {
  navigateTo('/')
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  event.preventDefault()
  if (result.value) leave()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="flex min-h-screen">
    <aside class="flex w-[300px] shrink-0 flex-col gap-4 bg-shell p-5">
      <p class="rounded-[14px] bg-back px-4 py-3 text-center text-[35px] text-white drop-shadow-control [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
        Portfolio
      </p>
      <div class="mt-auto rounded-[14px] bg-back px-4 py-4 text-center text-white drop-shadow-control [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
        <p class="text-[45px]" data-remaining>
          {{ formatDollars(remaining) }}
        </p>
        <p class="text-[22px]">
          {{ typeCount }} / 3 types
        </p>
      </div>
    </aside>

    <section class="flex min-w-0 flex-1 flex-col gap-4 p-6">
      <div class="min-h-[170px] rounded-[19px] bg-shell p-4" data-played>
        <div class="flex gap-3 overflow-x-auto">
          <div
            v-for="(id, index) in played"
            :key="`${id}-${index}`"
            class="w-[160px] shrink-0"
          >
            <ChoiceCard tone="paper" inert class="min-h-[120px]">
              <span class="text-[22px]">{{ actionById(id)?.name }}</span>
              <span class="text-[22px] text-action">{{ formatDollars(actionById(id)?.unitCost ?? 0) }}</span>
            </ChoiceCard>
          </div>
        </div>
      </div>

      <div class="mt-auto flex flex-col gap-[15px]">
        <div class="flex flex-wrap items-center justify-between gap-[15px]">
          <Button
            variant="action"
            size="row"
            type="button"
            :disabled="!ready || result !== null"
            @click="playRecommended"
          >
            Play Recommended
          </Button>
          <Button
            variant="play"
            size="row"
            type="button"
            :disabled="!ready || result !== null"
            data-commit
            @click="commit"
          >
            Results
          </Button>
        </div>
        <div class="flex gap-3 overflow-x-auto pb-2" data-hand>
          <div
            v-for="action in actions"
            :key="action.id"
            class="w-[200px] shrink-0"
          >
            <ChoiceCard
              tone="paper"
              class="min-h-[150px]"
              :disabled="!canPlay(action.id)"
              :data-action="action.id"
              @click="play(action.id)"
            >
              <span class="text-[22px]">{{ action.name }}</span>
              <span class="text-[25px] text-action">{{ formatDollars(action.unitCost) }}</span>
              <span class="text-[20px] text-muted">{{ playedCount(action.id) }} / {{ action.limit }}</span>
            </ChoiceCard>
          </div>
        </div>
      </div>
    </section>

    <ResultModal
      v-if="result"
      :outcome="result"
      :spent="spent"
      :kept="remaining"
      :types="typeCount"
      @menu="leave"
      @again="newRun"
    />
  </div>
</template>
