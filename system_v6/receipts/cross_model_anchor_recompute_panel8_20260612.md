# Cross-model blind recomputation, panel 8 — b6 falsifiability baselines + the open-chain QCA calibrations (2026-06-12)

Protocol as panels 1–7. Routes: `grok-4.3` (API, raw `/tmp/panel8_grok_resp.json`), `auto-gemini-3`
(TUI, raw `/tmp/panel8_gemini_resp.txt`). Pre-registers the targets of the lanes IN FLIGHT
(axis_triple_consistency_b6_v0; ring_checkerboard_qca_v2).

| # | target | the routes AGREE |
|---|---|---|
| q1 | the b6 controls' baselines | scrambled-c chance agreement = 1/2 exactly; the global b-convention flip turns the relation into c = +a*b (the convention-flip control's exact prediction) |
| q2 | the open-chain index calibrations | right-shift index +1, left-shift -1, onsite 0 (log_2) — BOTH routes; NOTE: the intermediate crossing-algebra dimension bookkeeping differs between routes (grok 4&2, gemini 1&4 — different conventions, same index) — the v2 builder must DECLARE its convention and the auditor must check the index, not the intermediate dims |
| q3 | the gauge check's fact | operator Schmidt rank invariant under local onsite-unitary multiplication (a one-sided invertible change of basis) — the inserted-unitary gauge check's exact expected outcome |

Ceiling: advisory pre-registration; promotion_allowed: false.
