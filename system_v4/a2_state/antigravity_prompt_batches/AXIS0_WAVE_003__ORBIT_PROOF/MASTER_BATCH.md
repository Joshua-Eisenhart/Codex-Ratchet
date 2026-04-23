# Antigravity Axis 0 — Wave 003: ORBIT_PROOF
**Date:** 2026-03-31

## Context going in (from Codex session 9874474d)

**CLOSED this session:**
- Fi Lemma: algebraic proof closed. σ_x commutes with U_x(θ) → Fi leaves lr_asym exactly invariant. 1995/1995, zero failures.
- Attractor basin characterized. Three joint conditions.
- Te paradox resolved: Te anti-arises in isolation, co-arises in sequence because Fi follows and re-establishes forward cross-temporal alignment.
- lr_asym "constant 1.0" paradox resolved: varies on trajectory (mean 0.94, min 0.62). Only 1.0 on static Hopf snapshots.

**Orbit phase alignment probe results (`sim_axis0_orbit_phase_alignment.py`):**
- 32-step orbit: Ti/Fe/Te/Fi×8 outer, then Ti/Fe/Te/Fi×8 inner
- Inner half: failures concentrated here (all 4 failures in T1/inner, all in inner half)
- Clifford: Fi fails 4× in Clifford inner half (vs 1 failure in non-Clifford)
- Ti: 100% success across ALL configs (as predicted by attractor basin)
- n_total_failures: 31 across all configs

**OPEN: OPEN-1 — ga0=MI formal proof**
- Need full algebraic proof that Ti→Fe→Te→Fi 4-step periodic orbit produces co-arising
- Currently 87-90% forward per-step; the ~10% failures are at Fe/Te/Fi steps, inner-half concentrated
- Fi failure puzzle: Fi is algebraically lr_asym invariant, but fails 4× in Clifford inner half in the orbit probe. Requires resolution.

## Batch structure: 10 prompts

1. `AGW3-01` — Orbit failure anatomy (Sonnet) — what characterizes the failing steps exactly
2. `AGW3-02` — Fi inner half paradox (Opus) — why do Fi steps fail in Clifford inner when lemma says no
3. `AGW3-03` — Fe mechanism proof attempt (Gemini High) — algebraic analysis of Fe co-arising condition
4. `AGW3-04` — Te orbit proof attempt (Opus) — derive Te co-arising from attractor conditions
5. `AGW3-05` — Proof strategy doc (Sonnet) — write AXIS0_OPEN1_PROOF_STRATEGY.md
6. `AGW3-06` — i-scalar derivation from RC-1+RC-2 (Opus) — now that basin is characterized
7. `AGW3-07` — Clifford anomaly revisit (Sonnet) — Clifford as the Ti failure boundary case
8. `AGW3-08` — Orbit randomization falsifier (Codex) — probe that scrambles orbit order to kill the phase-alignment mechanism
9. `AGW3-09` — State card sync (Gemini Flash) — update all controller docs with Wave 003 findings
10. `AGW3-10` — Wave 003 controller closeout (Opus) — no smoothing collapse

## Model routing
- Opus: AGW3-02, AGW3-04, AGW3-06, AGW3-10
- Sonnet: AGW3-01, AGW3-05, AGW3-07
- Gemini High: AGW3-03
- Gemini Flash: AGW3-09
- Codex: AGW3-08

## Return directory
`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/antigravity_prompt_batches/AXIS0_WAVE_003__ORBIT_PROOF/returns/`
