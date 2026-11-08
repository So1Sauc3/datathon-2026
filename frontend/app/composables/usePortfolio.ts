import { computed, ref } from 'vue'
import {
  ACTIONS,
  BUDGET,
  GAME_DATA_FILE,
  TYPE_CAP,
  actionById,
  portfolioMatches,
  type BudgetFile,
} from '~/lib/dashboard/catalog'

export function usePortfolio() {
  const played = ref<string[]>([])
  const result = ref<'win' | 'lose' | null>(null)
  const returned = ref(0)
  const round = ref(1)
  const { data } = useFetch<BudgetFile>(`/data/${GAME_DATA_FILE}`, { server: false })

  const target = computed(() => {
    const next: Record<string, number> = {}
    for (const action of data.value?.actions ?? []) {
      if (action.funded && action.cost > 0)
        next[action.action_type_id] = action.quantity
    }
    return next
  })

  const ready = computed(() => Object.keys(target.value).length > 0)

  const spent = computed(() =>
    played.value.reduce((sum, id) => sum + (actionById(id)?.unitCost ?? 0), 0),
  )

  const remaining = computed(() => BUDGET - spent.value)

  const spendingTypeIds = computed(() => {
    const ids = new Set<string>()
    for (const id of played.value) {
      const action = actionById(id)
      if (action && action.unitCost > 0) ids.add(id)
    }
    return ids
  })

  const typeCount = computed(() => spendingTypeIds.value.size)

  function playedCount(id: string) {
    return played.value.filter(playedId => playedId === id).length
  }

  const hand = computed(() => ACTIONS.filter(action => playedCount(action.id) < action.limit))

  function canPlay(id: string) {
    if (result.value) return false
    const action = actionById(id)
    if (!action) return false
    if (playedCount(id) >= action.limit) return false
    if (spent.value + action.unitCost > BUDGET) return false
    if (action.excludes?.some(other => playedCount(other) > 0)) return false
    if (action.unitCost > 0 && !spendingTypeIds.value.has(id) && spendingTypeIds.value.size >= TYPE_CAP)
      return false
    return true
  }

  function play(id: string) {
    if (!canPlay(id)) return
    played.value = [...played.value, id]
  }

  function unplay(index: number) {
    if (result.value || index < 0 || index >= played.value.length) return
    played.value = played.value.filter((_, playedIndex) => playedIndex !== index)
    returned.value += 1
  }

  function playRecommended() {
    if (!ready.value || result.value) return
    const next: string[] = []
    for (const [id, quantity] of Object.entries(target.value)) {
      if (!actionById(id)) continue
      for (let index = 0; index < quantity; index += 1)
        next.push(id)
    }
    played.value = next
  }

  function commit() {
    if (!ready.value || result.value) return
    result.value = portfolioMatches(played.value, target.value) ? 'win' : 'lose'
  }

  function newRun() {
    played.value = []
    result.value = null
    returned.value = 0
    round.value += 1
  }

  return {
    actions: ACTIONS,
    hand,
    played,
    result,
    returned,
    round,
    ready,
    spent,
    remaining,
    typeCount,
    playedCount,
    canPlay,
    play,
    unplay,
    playRecommended,
    commit,
    newRun,
  }
}
