<script setup lang="ts">
import { ref } from 'vue'
import { crtFragment } from '~/lib/shaders/crt'

const canvas = ref<HTMLCanvasElement | null>(null)

useShaderCanvas(canvas, { fragmentShader: crtFragment, transparent: true })
</script>

<template>
  <canvas
    ref="canvas"
    aria-hidden="true"
    class="pointer-events-none fixed inset-0 z-[100] h-full w-full"
  />
</template>
