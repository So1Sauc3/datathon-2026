<script setup lang="ts">
import { cn } from 'cn'
import type { TileTone } from '~/lib/dashboard/layouts'

defineProps<{
  title: string
  tone: TileTone
  value?: string
  caption?: string
  fill?: boolean
}>()

const TEXT: Record<TileTone, string> = {
  play: 'text-play',
  action: 'text-action',
  back: 'text-back',
  collection: 'text-collection',
}

const FILL: Record<TileTone, string> = {
  play: 'bg-play',
  action: 'bg-action',
  back: 'bg-back',
  collection: 'bg-collection',
}
</script>

<template>
  <DashTile :title="title" data-tile="stat">
    <div
      :class="cn(
        'flex min-h-0 flex-1 flex-col items-center justify-center gap-1 rounded-[16px] shadow-lift',
        fill ? FILL[tone] : 'bg-sidebar-well',
      )"
    >
      <span
        :class="cn(
          'text-[50px] [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]',
          fill ? 'text-white' : TEXT[tone],
        )"
      >
        {{ value ?? '--' }}
      </span>
      <span v-if="caption" class="text-[20px] text-white/75">
        {{ caption }}
      </span>
    </div>
  </DashTile>
</template>
