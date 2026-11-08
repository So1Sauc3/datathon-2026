<script setup lang="ts">
import { ref } from 'vue'
import { balatroFragment } from '~/lib/shaders/balatro'

const canvas = ref<HTMLCanvasElement | null>(null)

useShaderCanvas(canvas, { fragmentShader: balatroFragment, pixelRatio: () => 1 })
</script>

<template>
  <canvas
    ref="canvas"
    aria-hidden="true"
    class="pointer-events-none fixed inset-0 -z-10 h-full w-full [image-rendering:pixelated]"
  />
</template>
