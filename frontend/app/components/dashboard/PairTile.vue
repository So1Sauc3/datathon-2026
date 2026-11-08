<script setup lang="ts">
withDefaults(defineProps<{
  title: string
  left: string
  right: string
  joiner?: string
  values?: readonly [string, string]
}>(), {
  joiner: 'X',
  values: () => ['--', '--'],
})
</script>

<template>
  <DashTile :title="title" data-tile="pair">
    <div class="flex min-h-0 flex-1 items-stretch gap-2 text-white [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
      <p class="flex flex-1 flex-col items-end justify-center gap-1 rounded-[16px] bg-play px-3 shadow-lift">
        <span class="text-[20px] text-white/75">{{ left }}</span>
        <span class="text-[45px]"><CountUp :value="values[0]" /></span>
      </p>
      <span class="flex items-center px-1 text-[45px] text-action">{{ joiner }}</span>
      <p class="flex flex-1 flex-col items-start justify-center gap-1 rounded-[16px] bg-action px-3 shadow-lift">
        <span class="text-[20px] text-white/75">{{ right }}</span>
        <span class="text-[45px]"><CountUp :value="values[1]" /></span>
      </p>
    </div>
  </DashTile>
</template>
