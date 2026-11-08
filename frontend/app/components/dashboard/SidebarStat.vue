<script setup lang="ts">
defineProps<{
  label: string
}>()
</script>

<template>
  <div class="flex flex-col items-center rounded-[16px] bg-sidebar-box px-3 pb-[7px] shadow-lift">
    <p class="flex h-[35px] items-center text-[30px] text-white [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
      {{ label }}
    </p>
    <div class="flex w-full flex-1 items-baseline justify-center rounded-[16px] bg-sidebar-well pt-[5px] text-[60px] shadow-lift [text-shadow:0_4px_4px_rgba(0,0,0,0.25)]">
      <slot />
    </div>
  </div>
</template>
