<script setup lang="ts">
import { computed } from 'vue'
import type { TileRow } from '~/lib/dashboard/layouts'

const props = defineProps<{
  title: string
  columns: readonly [string, string]
  row: TileRow
}>()

const count = computed(() => props.row * 3 - 2)
</script>

<template>
  <DashTile :title="title" data-tile="rank">
    <template #aside>
      <span class="shrink-0 text-[20px]">
        <span class="text-play">{{ columns[0] }}</span>
        <span class="mx-1 text-action">X</span>
        <span class="text-action">{{ columns[1] }}</span>
      </span>
    </template>
    <ol class="flex min-h-0 flex-1 flex-col gap-[5px]">
      <li
        v-for="index in count"
        :key="index"
        class="flex min-h-0 flex-1 items-center gap-2 rounded-[19px] bg-hand px-2"
      >
        <span class="rounded-[31px] bg-level px-3 py-[2px] text-[20px] text-muted">{{ index }}</span>
        <span class="flex min-w-0 flex-1">
          <span class="h-[12px] rounded-full bg-capsule/25" :style="{ width: `${90 - ((index * 17) % 45)}%` }" />
        </span>
        <span class="flex items-center gap-1 rounded-full bg-capsule p-1 text-[20px] text-white [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
          <span class="rounded-[14px] bg-play px-2">--</span>
          <span class="text-action">X</span>
          <span class="rounded-[14px] bg-action px-2">--</span>
        </span>
      </li>
    </ol>
  </DashTile>
</template>
