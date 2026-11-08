const BGM_SRC = '/assets/sound/balatro-main.mp3'

let audio: HTMLAudioElement | null = null
let listening = false

function ensureAudio() {
  if (audio) return audio
  audio = new Audio(BGM_SRC)
  audio.loop = true
  audio.preload = 'auto'
  audio.volume = 0.45
  return audio
}

async function tryStart() {
  const el = ensureAudio()
  if (!el.paused) return true
  try {
    await el.play()
    return true
  }
  catch {
    return false
  }
}

export function useBgm() {
  const started = useState('bgm-started', () => false)

  onMounted(() => {
    if (!import.meta.client || started.value || listening) return

    ensureAudio()
    listening = true

    const start = async () => {
      if (started.value) return
      const ok = await tryStart()
      if (!ok) return
      started.value = true
      listening = false
      window.removeEventListener('pointerdown', start)
      window.removeEventListener('keydown', start)
    }

    window.addEventListener('pointerdown', start)
    window.addEventListener('keydown', start)
  })
}
