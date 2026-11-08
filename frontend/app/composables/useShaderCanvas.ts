import { onMounted, onUnmounted, watch, type Ref } from 'vue'
import { usePreferredReducedMotion } from '@vueuse/core'
import {
  Mesh,
  NoBlending,
  OrthographicCamera,
  PlaneGeometry,
  Scene,
  ShaderMaterial,
  Vector2,
  WebGLRenderer,
} from 'three'

const vertexShader = /* glsl */ `
void main() {
  gl_Position = vec4(position.xy, 0.0, 1.0);
}
`

export interface ShaderCanvasOptions {
  fragmentShader: string
  /** Output premultiplied alpha so the canvas composites over the page. */
  transparent?: boolean
  pixelRatio?: () => number
}

/**
 * Draws a full-screen fragment shader into `canvas`. The shader receives
 * `uTime` (seconds), `uResolution` (drawing-buffer px), and `uScale`
 * (device pixels per CSS px).
 */
export function useShaderCanvas(canvas: Ref<HTMLCanvasElement | null>, options: ShaderCanvasOptions) {
  const reducedMotion = usePreferredReducedMotion()
  let teardown: (() => void) | null = null

  onMounted(() => {
    const element = canvas.value
    if (!element) return

    let renderer: WebGLRenderer
    try {
      renderer = new WebGLRenderer({
        canvas: element,
        alpha: options.transparent ?? false,
        premultipliedAlpha: true,
        antialias: false,
        depth: false,
        stencil: false,
        powerPreference: 'low-power',
      })
    }
    catch {
      return
    }

    const scene = new Scene()
    const camera = new OrthographicCamera(-1, 1, 1, -1, 0, 1)
    const geometry = new PlaneGeometry(2, 2)
    const uniforms = {
      uTime: { value: 0 },
      uResolution: { value: new Vector2() },
      uScale: { value: 1 },
    }
    const material = new ShaderMaterial({
      vertexShader,
      fragmentShader: options.fragmentShader,
      uniforms,
      blending: NoBlending,
      depthTest: false,
      depthWrite: false,
    })
    scene.add(new Mesh(geometry, material))
    renderer.setClearColor(0x000000, 0)

    const start = performance.now()
    const render = () => {
      uniforms.uTime.value = (performance.now() - start) / 1000
      renderer.render(scene, camera)
    }

    const resize = () => {
      const width = element.clientWidth
      const height = element.clientHeight
      if (!width || !height) return
      renderer.setPixelRatio(options.pixelRatio?.() ?? window.devicePixelRatio)
      renderer.setSize(width, height, false)
      renderer.getDrawingBufferSize(uniforms.uResolution.value)
      uniforms.uScale.value = window.devicePixelRatio
      render()
    }

    const observer = new ResizeObserver(resize)
    observer.observe(element)
    resize()

    const stopMotion = watch(reducedMotion, (preference) => {
      renderer.setAnimationLoop(preference === 'reduce' ? null : render)
    }, { immediate: true })

    teardown = () => {
      stopMotion()
      observer.disconnect()
      renderer.setAnimationLoop(null)
      geometry.dispose()
      material.dispose()
      renderer.dispose()
      renderer.forceContextLoss()
    }
  })

  onUnmounted(() => {
    teardown?.()
    teardown = null
  })
}
