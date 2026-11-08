<script setup lang="ts">
import { computed } from 'vue'
import { cn } from 'cn'
import { claimById } from '~/lib/dashboard/catalog'
import { TILE_COL, TILE_ROW, layoutFor, type TileDef } from '~/lib/dashboard/layouts'

const props = withDefaults(defineProps<{
  claimId: string
  framed?: boolean
  tiles?: readonly TileDef[]
}>(), {
  framed: true,
})

const claim = computed(() => claimById(props.claimId))
const tiles = computed(() => props.tiles ?? layoutFor(props.claimId))

function span(tile: TileDef) {
  return [TILE_COL[tile.col], TILE_ROW[tile.row]]
}
</script>

<template>
  <section
    :class="cn(
      'flex min-w-0 flex-col gap-[15px]',
      framed && 'rounded-[28px] border-[5px] border-sidebar-line bg-sidebar p-[15px] shadow-panel',
    )"
    :data-board="claimId"
  >
    <header
      v-if="framed || claim"
      :class="cn('flex flex-wrap items-center gap-3 px-1', framed ? 'justify-between' : 'justify-end')"
    >
      <h2 v-if="framed" class="text-[40px] text-white [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
        {{ claim?.label ?? claimId }}
      </h2>
      <ul v-if="claim" class="flex flex-wrap gap-2" aria-label="Sources">
        <li
          v-for="file in claim.dataFiles"
          :key="file"
          class="rounded-[16px] bg-count px-3 py-1 text-[20px] text-back"
        >
          {{ file }}
        </li>
      </ul>
    </header>

    <div class="grid grid-flow-row-dense auto-rows-[128px] grid-cols-1 gap-[15px] md:grid-cols-6 lg:grid-cols-12">
      <template v-for="(tile, index) in tiles" :key="`${claimId}-${index}`">
        <StatTile
          v-if="tile.kind === 'stat'"
          :class="span(tile)"
          :title="tile.title"
          :tone="tile.tone"
          :value="tile.value"
          :caption="tile.caption"
          :fill="tile.fill"
        />
        <PairTile
          v-else-if="tile.kind === 'pair'"
          :class="span(tile)"
          :title="tile.title"
          :left="tile.left"
          :right="tile.right"
          :joiner="tile.joiner"
          :values="tile.values"
        />
        <ChartTile
          v-else-if="tile.kind === 'chart'"
          :class="span(tile)"
          :title="tile.title"
          :chart="tile.chart"
        />
        <RankTile
          v-else-if="tile.kind === 'rank'"
          :class="span(tile)"
          :title="tile.title"
          :columns="tile.columns"
          :row="tile.row"
        />
        <NoteTile
          v-else
          :class="span(tile)"
          :title="tile.title"
        />
      </template>
    </div>
  </section>
</template>
