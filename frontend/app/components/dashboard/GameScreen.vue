<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { TYPE_CAP, actionById, claimsFor, formatDollars } from '~/lib/dashboard/catalog'
import { actionCard, claimArt } from '~/lib/dashboard/art'

const {
  hand,
  played,
  result,
  returned,
  round,
  ready,
  spent,
  remaining,
  typeCount,
  playedCount,
  canPlay,
  play,
  unplay,
  playRecommended,
  commit,
  newRun,
} = usePortfolio()

const jokers = claimsFor('q4')

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
  <div class="flex h-screen overflow-hidden">
    <aside class="ml-[70px] flex w-[431px] shrink-0 flex-col overflow-y-auto border-[5px] border-sidebar-line bg-sidebar px-1 pb-[43px] pt-[27px]">
      <h1 class="mx-[15px] flex h-[67px] shrink-0 items-center justify-center rounded-[14px] border-[5px] border-blind-line bg-blind text-[60px] text-white drop-shadow-control [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
        Portfolio
      </h1>

      <div class="flex min-h-0 flex-1 items-center justify-center py-6">
        <img
          src="/assets/token/blind/big.png"
          alt=""
          draggable="false"
          class="aspect-square max-h-full w-[177px] select-none object-contain [image-rendering:pixelated]"
        >
      </div>

      <div class="flex h-[75px] shrink-0 items-stretch rounded-[16px] bg-sidebar-box py-[6px] pr-[11px] shadow-lift">
        <p class="flex w-[127px] shrink-0 flex-col items-center justify-center text-[32px] text-white [text-shadow:0_4px_4px_rgba(0,0,0,0.5)]">
          <span>Round</span>
          <span>score</span>
        </p>
        <div class="flex flex-1 items-center justify-center gap-3 rounded-[16px] bg-score-well shadow-lift">
          <img
            src="/assets/token/stake/white.png"
            alt=""
            draggable="false"
            class="size-[42px] select-none [image-rendering:pixelated]"
          >
          <span class="text-[45px] text-white [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]" data-spent>
            {{ formatDollars(spent) }}
          </span>
        </div>
      </div>

      <div class="mt-[10px] flex shrink-0 items-center rounded-[16px] bg-sidebar-box p-[15px] text-[70px] text-white shadow-lift [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
        <span class="flex h-[81px] w-[164px] items-center justify-end rounded-[16px] bg-play pr-2 shadow-lift">
          {{ played.length }}
        </span>
        <span class="flex-1 text-center text-action">X</span>
        <span class="flex h-[81px] w-[164px] items-center justify-start rounded-[16px] bg-action pl-2 shadow-lift">
          {{ typeCount }}
        </span>
      </div>

      <div class="mt-[17px] flex shrink-0 gap-[15px] pl-[15px]">
        <div class="flex w-[126px] shrink-0 flex-col gap-[30px]">
          <Button variant="action" size="tile" type="button" class="flex-1" data-new-run @click="newRun">
            New Run
          </Button>
          <Button variant="back" size="tile" type="button" class="flex-1" data-menu="leave" @click="leave">
            Menu
          </Button>
        </div>
        <div class="grid flex-1 grid-cols-2 grid-rows-[97px_97px_97px] gap-x-[7px] gap-y-[15px]">
          <SidebarStat label="Hands">
            <span class="text-play">{{ hand.length }}</span>
          </SidebarStat>
          <SidebarStat label="Discards">
            <span class="text-action">{{ returned }}</span>
          </SidebarStat>
          <div class="col-span-2 flex rounded-[16px] bg-sidebar-box px-3 py-[7px] shadow-lift">
            <p
              class="flex flex-1 items-center justify-center rounded-[16px] bg-sidebar-well text-[50px] text-back shadow-lift [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]"
              data-remaining
            >
              {{ formatDollars(remaining) }}
            </p>
          </div>
          <SidebarStat label="Ante">
            <span class="text-back">{{ typeCount }}</span>
            <span class="text-white">/</span>
            <span class="text-[40px] text-white">{{ TYPE_CAP }}</span>
          </SidebarStat>
          <SidebarStat label="Round">
            <span class="text-back">{{ round }}</span>
          </SidebarStat>
        </div>
      </div>
    </aside>

    <section class="flex min-h-0 min-w-0 flex-1 flex-col gap-4 p-6">
      <div class="flex shrink-0 items-start justify-center gap-3 overflow-x-auto p-1" data-jokers>
        <SpriteButton
          v-for="joker in jokers"
          :key="joker.id"
          inert
          hide-label
          size="hand"
          :src="claimArt(joker.id).src"
          :label="joker.label"
        />
      </div>

      <div class="flex min-h-0 flex-1 items-center justify-center overflow-hidden" data-played>
        <div class="flex max-h-full max-w-full items-start gap-3 overflow-x-auto overflow-y-hidden p-1 [justify-content:safe_center]">
          <SpriteButton
            v-for="(id, index) in played"
            :key="`${id}-${index}`"
            size="hand"
            :src="actionCard(id)"
            :label="actionById(id)?.name ?? id"
            :disabled="result !== null"
            data-played-card
            @click="unplay(index)"
          >
            <span class="text-[20px]">
              <span class="text-action">{{ formatDollars(actionById(id)?.unitCost ?? 0) }}</span>
              <span class="ml-2 text-white/75">{{ playedCount(id) }} / {{ actionById(id)?.limit }}</span>
            </span>
          </SpriteButton>
        </div>
      </div>

      <div class="mt-auto flex shrink-0 flex-col gap-[15px]">
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
        <div class="flex p-1 pb-2" data-hand>
          <div
            v-for="action in hand"
            :key="action.id"
            class="group relative min-w-0 flex-1 last:w-[142px] last:flex-none hover:z-10 focus-within:z-10"
          >
            <div class="relative w-[142px]">
              <SpriteButton
                size="hand"
                hide-label
                :src="actionCard(action.id)"
                :label="action.name"
                :disabled="!canPlay(action.id)"
                :data-action="action.id"
                @click="play(action.id)"
              />
              <div class="pointer-events-none absolute bottom-full left-1/2 mb-3 hidden w-[180px] -translate-x-1/2 flex-col gap-2 rounded-[14px] bg-white p-3 text-center text-[22px] text-ink shadow-panel group-hover:flex group-focus-within:flex">
                <p>{{ action.name }}</p>
                <p>
                  <span class="text-action">{{ formatDollars(action.unitCost) }}</span>
                  <span class="ml-2">{{ playedCount(action.id) }} / {{ action.limit }}</span>
                </p>
              </div>
            </div>
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
