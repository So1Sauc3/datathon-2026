<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { MENU, type MenuEntry, type MenuVariant } from '~/lib/dashboard/catalog'
import type { ButtonVariants } from '~/components/ui/button'

useHead({ title: 'The Gilded Ace' })

const { top, openRoot, back } = useModalStack()
const creditsOpen = ref(false)

function buttonSize(variant: MenuVariant): ButtonVariants['size'] {
  if (variant === 'play') return 'splash'
  if (variant === 'collection') return 'menuWide'
  if (variant === 'slate') return 'chip'
  return 'menu'
}

const groups = computed(() => {
  const rows: { tray: boolean, items: MenuEntry[] }[] = []
  for (const item of MENU) {
    const tray = item.variant !== 'slate'
    const last = rows.at(-1)
    if (last && last.tray === tray) last.items.push(item)
    else rows.push({ tray, items: [item] })
  }
  return rows
})

function openQuestion(id: MenuEntry['id']) {
  if (id !== 'q1') return
  openRoot(id)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  if (creditsOpen.value) {
    event.preventDefault()
    creditsOpen.value = false
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
  <main class="relative flex min-h-screen flex-col px-6 pb-8">
    <Button
      variant="slate"
      size="chip"
      type="button"
      class="absolute top-6 right-6 z-10 uppercase"
      @click="creditsOpen = true"
    >
      Credits
    </Button>
    <div class="flex flex-1 items-center justify-center">
      <h1 class="text-center text-[140px]">
        The Gilded Ace
      </h1>
    </div>
    <nav class="menu-fit" aria-label="Questions">
      <div class="menu-row">
        <div
          v-for="(group, index) in groups"
          :key="index"
          :class="group.tray
            ? 'flex h-[169px] items-center gap-4 rounded-[18px] bg-panel px-[11px] shadow-[0_6px_4px_rgba(0,0,0,0.5)]'
            : 'flex h-[114px] items-center justify-center gap-4 rounded-[21px] bg-panel px-5 shadow-[0_6px_4px_rgba(0,0,0,0.5)]'"
        >
          <template v-for="item in group.items" :key="item.id">
            <Button v-if="item.to" as-child :variant="item.variant" :size="buttonSize(item.variant)" class="uppercase">
              <NuxtLink :to="item.to">
                {{ item.label }}
              </NuxtLink>
            </Button>
            <Button
              v-else
              :variant="item.variant"
              :size="buttonSize(item.variant)"
              class="uppercase"
              type="button"
              :data-menu="item.id"
              @click="openQuestion(item.id)"
            >
              {{ item.label }}
            </Button>
          </template>
        </div>
      </div>
    </nav>

    <Transition name="modal" mode="out-in">
      <MachinesModal v-if="top?.id === 'q1'" />
      <ClaimModal v-else-if="top?.id === 'q1-claim'" />
    </Transition>
    <Transition name="modal">
      <CreditsModal v-if="creditsOpen" @close="creditsOpen = false" />
    </Transition>
  </main>
</template>

<style scoped>
.menu-fit {
  container-type: inline-size;
  display: flex;
  justify-content: center;
  width: 100%;
}

.menu-row {
  display: flex;
  align-items: flex-end;
  gap: 64px;
  zoom: min(1, calc(100cqw / 1662px));
}
</style>
