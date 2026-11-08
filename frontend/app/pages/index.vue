<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { MENU, type MenuEntry, type MenuVariant } from '~/lib/dashboard/catalog'
import type { ButtonVariants } from '~/components/ui/button'

useHead({ title: 'The Gilded Ace' })

const { top, openRoot, back } = useModalStack()
const creditsSeen = useState('credits-intro', () => false)
const creditsOpen = ref(!creditsSeen.value)

function closeCredits() {
  creditsOpen.value = false
  creditsSeen.value = true
}

interface FanCard {
  key: string
  label: string
  variant: MenuVariant
  size: NonNullable<ButtonVariants['size']>
  rot: number
  x: number
  y: number
  z: number
  delay: number
  to?: string
  question?: MenuEntry['id']
  credits?: boolean
}

const menuById = new Map(MENU.map(item => [item.id, item]))

function fromMenu(
  id: MenuEntry['id'],
  place: Pick<FanCard, 'rot' | 'x' | 'y' | 'z' | 'delay'>,
  size: FanCard['size'] = 'menu',
): FanCard {
  const item = menuById.get(id)
  if (!item) throw new Error(`Missing menu ${id}`)
  return {
    key: id,
    label: item.label,
    variant: item.variant,
    size,
    ...place,
    to: item.to,
    question: item.to ? undefined : item.id,
  }
}

/** Play stays splash-sized and in front. Every other card is the Demand (menu) size. */
const fan: FanCard[] = [
  {
    key: 'credits',
    label: 'Credits',
    variant: 'slate',
    size: 'menu',
    rot: -22,
    x: -620,
    y: 54,
    z: 1,
    delay: 0.18,
    credits: true,
  },
  fromMenu('q4', { rot: -14, x: -430, y: 24, z: 2, delay: 0.12 }),
  fromMenu('q2', { rot: -7, x: -240, y: 4, z: 3, delay: 0.06 }),
  fromMenu('q6', { rot: 0, x: 0, y: -16, z: 8, delay: 0 }, 'splash'),
  fromMenu('q3', { rot: 7, x: 240, y: 4, z: 3, delay: 0.06 }),
  fromMenu('q1', { rot: 14, x: 430, y: 24, z: 2, delay: 0.12 }),
  fromMenu('q5', { rot: 22, x: 620, y: 54, z: 1, delay: 0.18 }),
]

function activate(card: FanCard) {
  if (card.credits) {
    creditsOpen.value = true
    return
  }
  if (card.question === 'q1') openRoot('q1')
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  if (creditsOpen.value) {
    event.preventDefault()
    closeCredits()
    return
  }
  if (!top.value) return
  event.preventDefault()
  back()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <main class="relative flex h-screen flex-col overflow-hidden px-6">
    <div class="flex flex-1 items-center justify-center">
      <h1 class="text-center text-[140px]">
        The Gilded Ace
      </h1>
    </div>
    <nav class="fan-fit" aria-label="Menu">
      <div class="fan">
        <div
          v-for="card in fan"
          :key="card.key"
          class="fan-card"
          :style="{
            '--x': `${card.x}px`,
            '--y': `${card.y}px`,
            '--rot': `${card.rot}deg`,
            '--z': card.z,
            '--delay': `${card.delay}s`,
            '--origin': card.size === 'splash' ? '69px' : '58px',
          }"
        >
          <Button
            v-if="card.to"
            as-child
            :variant="card.variant"
            :size="card.size"
            class="uppercase"
          >
            <NuxtLink :to="card.to">
              {{ card.label }}
            </NuxtLink>
          </Button>
          <Button
            v-else
            :variant="card.variant"
            :size="card.size"
            class="uppercase"
            type="button"
            :data-menu="card.question"
            @click="activate(card)"
          >
            {{ card.label }}
          </Button>
        </div>
      </div>
    </nav>

    <Transition name="modal" mode="out-in">
      <MachinesModal v-if="top?.id === 'q1'" />
      <ClaimModal v-else-if="top?.id === 'q1-claim'" />
    </Transition>
    <Transition name="modal">
      <CreditsModal v-if="creditsOpen" @close="closeCredits" />
    </Transition>
  </main>
</template>

<style scoped>
.fan-fit {
  container-type: inline-size;
  display: flex;
  justify-content: center;
  width: 100%;
}

.fan {
  position: relative;
  width: 1560px;
  height: 380px;
  flex: none;
  zoom: min(1, calc(100cqw / 1560px));
}

.fan-card {
  position: absolute;
  left: 50%;
  top: 46%;
  z-index: var(--z);
  transform-origin: center var(--origin);
  translate: calc(-50% + var(--x)) calc(var(--y) - var(--origin));
  rotate: var(--rot);
  animation: fan-rise 0.7s cubic-bezier(0.16, 0.84, 0.32, 1) both;
  animation-delay: var(--delay);
}

/* Keep the label on the original face and grow the body down past the screen. */
.fan-card :deep([data-slot="button"]) {
  height: 100vh;
  align-items: flex-start;
  padding-top: calc(var(--origin) - 0.5lh);
}

@keyframes fan-rise {
  from {
    opacity: 0;
    translate: calc(-50% + var(--x)) calc(var(--y) - var(--origin) + 180px);
  }

  to {
    opacity: 1;
    translate: calc(-50% + var(--x)) calc(var(--y) - var(--origin));
  }
}

@media (prefers-reduced-motion: reduce) {
  .fan-card {
    animation: none;
  }
}
</style>
