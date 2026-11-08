export type ArtKind = 'joker' | 'planet' | 'token' | 'booster' | 'tarot' | 'deck'

export interface ClaimArt {
  src: string
  kind: Exclude<ArtKind, 'deck'>
}

const CLAIM_ART: Record<string, ClaimArt> = {
  'Q1-manager-list': { src: '/assets/card/tarot/manager.png', kind: 'tarot' },
  'Q1-payout-anomaly': { src: '/assets/card/tarot/anomaly.png', kind: 'tarot' },
  'Q1-luck': { src: '/assets/card/tarot/luck.png', kind: 'tarot' },
  'Q1-location': { src: '/assets/card/tarot/location.png', kind: 'tarot' },
  'Q1-persistence': { src: '/assets/card/tarot/persistence.png', kind: 'tarot' },
  'Q2-weekday': { src: '/assets/card/planet/weekdays.png', kind: 'planet' },
  'Q2-events': { src: '/assets/card/planet/events.png', kind: 'planet' },
  'Q2-renovation': { src: '/assets/card/planet/walkway.png', kind: 'planet' },
  'Q2-trend': { src: '/assets/card/planet/visitors.png', kind: 'planet' },
  'Q2-weather': { src: '/assets/card/planet/weather.png', kind: 'planet' },
  'Q3-total': { src: '/assets/token/blind/total.png', kind: 'token' },
  'Q3-when': { src: '/assets/token/blind/when.png', kind: 'token' },
  'Q3-manufacturer': { src: '/assets/token/blind/manufacturer.png', kind: 'token' },
  'Q3-staffing': { src: '/assets/token/blind/staffing.png', kind: 'token' },
  'Q4-outcomes': { src: '/assets/card/joker/outcomes.png', kind: 'joker' },
  'Q4-concentration': { src: '/assets/card/joker/concentration.png', kind: 'joker' },
  'Q4-locals': { src: '/assets/card/joker/locals.png', kind: 'joker' },
  'Q4-heavy-loss': { src: '/assets/card/joker/heavy-losses.png', kind: 'joker' },
  'Q4-reconciliation': { src: '/assets/card/joker/reconciliation.png', kind: 'joker' },
  'Q5-change': { src: '/assets/card/booster/change.png', kind: 'booster' },
  'Q5-cost': { src: '/assets/card/booster/cost.png', kind: 'booster' },
  'Q5-liability': { src: '/assets/card/booster/liability.png', kind: 'booster' },
}

/** Catalog order, ace down to two. One spade stands for each action. */
const ACTION_CARDS: Record<string, string> = {
  'A-MOVE-MACHINE': 'spades_A',
  'A-MOVE-BANK': 'spades_K',
  'A-REPLACE-LEASE': 'spades_Q',
  'A-REPLACE-BUY': 'spades_J',
  'A-TECH-SHIFT': 'spades_10',
  'A-PREVENTIVE': 'spades_9',
  'A-INSPECT': 'spades_8',
  'A-WAYFINDING': 'spades_7',
  'A-COMP-PILOT': 'spades_6',
  'A-COMP-CHANGE': 'spades_5',
  'A-PROMO': 'spades_4',
  'A-SURVEY': 'spades_3',
  'A-HOLD': 'spades_2',
}

export function claimArt(id: string): ClaimArt {
  return CLAIM_ART[id] ?? { src: '', kind: 'tarot' }
}

export function actionCard(id: string) {
  const file = ACTION_CARDS[id] ?? 'spades_A'
  return `/assets/card/deck/${file}.png`
}
