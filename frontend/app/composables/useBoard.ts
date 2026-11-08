import { computed, onMounted, ref, toValue, watch, type MaybeRefOrGetter } from 'vue'
import { bindBoard } from '~/lib/dashboard/bind'
import { filesFor, loadJson } from '~/lib/dashboard/load'

/** Load the JSON for one claim and bind it to that board's tile titles. */
export function useBoard(claimId: MaybeRefOrGetter<string>) {
  const pack = ref<Record<string, unknown> | null>(null)
  let token = 0

  async function pull(claim: string) {
    const current = ++token
    pack.value = null
    const pairs = await Promise.all(filesFor(claim).map(async file => [file, await loadJson(file)] as const))
    if (current !== token) return
    pack.value = Object.fromEntries(pairs)
  }

  onMounted(() => {
    watch(() => toValue(claimId), pull, { immediate: true })
  })

  const board = computed(() => (pack.value ? bindBoard(toValue(claimId), pack.value) : null))
  return { board }
}
