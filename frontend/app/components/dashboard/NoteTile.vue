<script setup lang="ts">
defineProps<{
  title: string
  body?: string
}>()
</script>

<template>
  <DashTile :title="title" data-tile="note">
    <Card v-if="body" class="min-h-0 flex-1 overflow-hidden">
      <p class="min-h-0 flex-1 overflow-y-auto text-[20px] leading-[1.15]">
        {{ body }}
      </p>
    </Card>
    <Card v-else class="min-h-0 flex-1 gap-3 overflow-hidden">
      <span
        v-for="width in [100, 92, 96, 78, 88, 54]"
        :key="width"
        class="h-[12px] shrink-0 rounded-full bg-hand/50"
        :style="{ width: `${width}%` }"
      />
    </Card>
  </DashTile>
</template>
