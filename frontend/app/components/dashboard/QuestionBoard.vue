<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { claimsFor, type QuestionId } from '~/lib/dashboard/catalog'
import { claimArt } from '~/lib/dashboard/art'

const props = defineProps<{
  question: Extract<QuestionId, 'q2' | 'q3' | 'q4' | 'q5'>
}>()

const TITLES = {
  q2: 'Demand',
  q3: 'Downtime',
  q4: 'Players',
  q5: 'Loyalty',
} as const

const title = computed(() => TITLES[props.question])
const claims = computed(() => claimsFor(props.question))
const active = ref(claims.value[0]?.id ?? '')
const claim = computed(() => claims.value.find(item => item.id === active.value) ?? claims.value[0])

function leave() {
  navigateTo('/')
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  event.preventDefault()
  leave()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <main class="flex min-h-screen flex-col gap-[15px] px-6 py-6">
    <header class="flex flex-wrap items-center gap-[15px]">
      <Button variant="back" size="row" type="button" @click="leave">
        Back
      </Button>
      <h1 class="text-[45px]">
        {{ title }}
      </h1>
    </header>

    <div
      v-if="question === 'q4'"
      class="grid items-start gap-[15px] md:grid-cols-[186px_minmax(0,1fr)]"
    >
      <nav
        class="flex gap-3 overflow-x-auto p-1 pb-4 md:sticky md:top-6 md:max-h-[calc(100vh-7rem)] md:flex-col md:overflow-y-auto"
        :aria-label="title"
      >
        <SpriteButton
          v-for="item in claims"
          :key="item.id"
          :src="claimArt(item.id).src"
          :label="item.label"
          :selected="active === item.id"
          :data-claim="item.id"
          @click="active = item.id"
        />
      </nav>
      <DashboardGrid v-if="claim" :claim-id="claim.id" />
    </div>

    <div v-else-if="question === 'q2'" class="flex min-w-0 flex-col gap-[15px]">
      <nav class="flex gap-3 overflow-x-auto p-1 pb-4" :aria-label="title">
        <SpriteButton
          v-for="item in claims"
          :key="item.id"
          :src="claimArt(item.id).src"
          :label="item.label"
          :selected="active === item.id"
          :data-claim="item.id"
          @click="active = item.id"
        />
      </nav>
      <DashboardGrid v-if="claim" :claim-id="claim.id" />
    </div>

    <div v-else-if="question === 'q3'" class="flex min-w-0 flex-col gap-[15px]">
      <nav class="flex flex-wrap justify-center gap-6 p-1" :aria-label="title">
        <SpriteButton
          v-for="item in claims"
          :key="item.id"
          size="token"
          :src="claimArt(item.id).src"
          :label="item.label"
          :selected="active === item.id"
          :data-claim="item.id"
          @click="active = item.id"
        />
      </nav>
      <DashboardGrid v-if="claim" :claim-id="claim.id" />
    </div>

    <div v-else class="flex min-w-0 flex-col gap-[15px]">
      <nav class="flex flex-wrap justify-center gap-[15px] p-1" :aria-label="title">
        <SpriteButton
          v-for="item in claims"
          :key="item.id"
          size="pack"
          :src="claimArt(item.id).src"
          :label="item.label"
          :selected="active === item.id"
          :data-claim="item.id"
          @click="active = item.id"
        />
      </nav>
      <DashboardGrid v-if="claim" :claim-id="claim.id" />
    </div>
  </main>
</template>
