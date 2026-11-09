# The Gilded Ace

A Balatro-styled analytics dashboard for [Dashboard Royale](https://github.com/tamu-datathon-org/dashboard-casino) (TAMU Datathon): six months at a fictional 300-machine casino, answering whether the ten lowest earners should be replaced—**luck, location, or a leak?**

## Verdict

**Don’t replace the manager’s bottom 10.** Nine sit in the weak Back Forty zone; most run soft game configs. Availability is normal. The data point to location and game mix, not broken cabinets.

**Spend $19,800 of the $100k ops budget; keep $80,200.** Expected mid-case net benefit ≈ **$56k**.

| Fund | Why |
| --- | --- |
| Inspect M-1158 ($1.2k) | Hit rate 38.6% vs configured 31.5% every month—paytable check, not a replacement |
| Relocate 2 machines ($3.6k) | Move underperformers into empty Center Pit slots (zone factor 0.65 → 1.13) |
| Promotion weekend ($15k) | Priced from the property’s own past lifts; July forecast as baseline |

## Accomplishments

**Analysis (`backend/analysis/`)** — reproducible pipeline for all six challenge questions plus a holdout-validated forecast:

- **Machines** — theo/luck decomposition, BH-corrected hit-rate tests, location standardization, quarter-to-quarter persistence
- **Demand** — weekday profile, event lifts, Back Forty walkway closure (−31% during, still −4.5% after), weather null
- **Downtime** — ~$101k theo lost; Ridgeline fails ~3× other makers; short-staffed shifts add ~1.25h repair time
- **Players / comps** — locals are 7% of cards but 58% of tracked theo; May 1 redemption cut roughly doubled latent points liability with no measurable play jump
- **Forecast** — weekday factors × training-mean level: **$53k MAE** on a frozen May–June holdout (**22%** below the weekday-mean baseline and prior Holt–Winters)

Claims, alternatives, limitations, and budget scenarios export to JSON consumed by the UI.

**Dashboard (`frontend/`)** — Nuxt + Vue app that presents the analysis as a Balatro run, not a spreadsheet.

- **Home** — fanned menu cards (Machines, Demand, Downtime, Players, Loyalty, Play) over a live WebGL Balatro shader, with CRT overlay and optional BGM
- **Claim boards** — each question opens a board of claim cards; selecting one drives a responsive tile grid (stats, pairs, ranks, notes) bound to the exported JSON
- **Charts** — custom D3 layer for bars, waterfalls, lines/areas, scatter, heatmaps, donuts, and forecast intervals, themed to the Balatro token set
- **Machines** — modal stack with floor map, manager’s bottom-10 ranking, and the M-1158 payout anomaly
- **Play** — budget as a hand of action cards: deal recommended moves, animate into the played row, enforce the 3-type / $100k caps, then commit for scored result
- **Chrome** — shadcn-vue restyled onto Balatro tokens (m6x11plus, 14px pills, role colors), GSAP card flights / page transitions, Lenis scrolling, pixel sprites for decks and stakes

## Quick start

```bash
# Analysis (from backend/)
python -m analysis.run

# Dashboard (from frontend/)
pnpm install && pnpm dev
```

Challenge data lives under `backend/data/`. Prebuilt dashboard payloads are in `frontend/public/data/`.

## Attribution

Code is MIT. Balatro art, shaders, and music belong to LocalThunk (from a purchased copy; not redistributed under MIT). Font **m6x11plus** by Daniel Linssen.
