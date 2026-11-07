import { onMounted, onUnmounted, ref, type Ref } from 'vue'

export function useChartBox(target: Ref<HTMLElement | null>) {
  const width = ref(0)
  const height = ref(0)
  let observer: ResizeObserver | null = null

  onMounted(() => {
    const element = target.value
    if (!element) return

    observer = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (!entry) return
      width.value = entry.contentRect.width
      height.value = entry.contentRect.height
    })
    observer.observe(element)
  })

  onUnmounted(() => {
    observer?.disconnect()
    observer = null
  })

  return { width, height }
}
