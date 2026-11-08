<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<template>
  <DashTile :title="title" data-tile="note">
    <Card class="min-h-0 flex-1 gap-3 overflow-hidden">
      <span
        v-for="width in [100, 92, 96, 78, 88, 54]"
        :key="width"
        class="h-[12px] shrink-0 rounded-full bg-hand/50"
        :style="{ width: `${width}%` }"
      />
    </Card>
  </DashTile>
</template>
