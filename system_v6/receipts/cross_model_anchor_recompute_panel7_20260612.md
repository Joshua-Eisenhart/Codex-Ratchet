# Cross-model blind recomputation, panel 7 — the basin-Landauer floor, the cycle-ledger closure, the alternation gap (2026-06-12)

Protocol as panels 1–6 (blind, temperature 0, no repo values). Routes: `grok-4.3` (API, raw
`/tmp/panel7_grok_resp.json`), `auto-gemini-3` (gemini TUI, raw `/tmp/panel7_gemini_resp.txt`).
Pre-registers the targets of the Carnot/Szilard-connection doctrine (24d03db89) BEFORE the
mapping mine reports or the connection packet builds.

| # | target | both routes AGREE |
|---|---|---|
| q1 | THE BASIN-LANDAUER FLOOR | relaxation merging m displaced states into one terminal orbit erases exactly ln(m) nats (counting); minimal dissipation = T_bath ln(m) |
| q2 | THE CYCLE-LEDGER CLOSURE | relaxation dissipation >= T_bath (ln(m) - r) for a record retaining r nats; dissipation-free iff r = ln(m) (perfect record); THE DEFERRED COST: resetting that record afterward costs T_bath ln(m) — the Szilard honesty clause (no free cycle by perfect recording) |
| q3 | THE ALTERNATION GAP | U,E commuting => D = I exactly (D=UEUE, I=EUEU); non-commuting leading order: D - I ~ 2ue[A,B] (second order in stroke sizes) — the within-engine N01 gap's exact form |
