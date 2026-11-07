import { computed } from 'vue'

export type ModalId = 'q1' | 'q1-claim' | 'q2' | 'q3' | 'q4' | 'q5'

export interface ModalFrame {
  id: ModalId
  payload?: string
}

export function useModalStack() {
  const stack = useState<ModalFrame[]>('modal-stack', () => [])
  const top = computed(() => stack.value.at(-1) ?? null)

  function openRoot(id: Exclude<ModalId, 'q1-claim'>) {
    stack.value = [{ id }]
  }

  function open(id: ModalId, payload?: string) {
    stack.value = [...stack.value, { id, payload }]
  }

  function back() {
    stack.value = stack.value.slice(0, -1)
  }

  return { stack, top, openRoot, open, back }
}
