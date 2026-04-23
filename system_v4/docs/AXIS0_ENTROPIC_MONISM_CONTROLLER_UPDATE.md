# Axis 0 — Entropic Monism Context: Controller Update

**Date:** 2026-03-30
**Status:** CONTEXT — proposal-facing interpretations. Probe-backed findings
  are marked with ✓. Open doctrine items are marked OPEN.
**Routing:** Controller-facing summary of the entropic monism / EC-3 /
  FEP exploration pass. See individual docs for full derivations.
**Sources:** AXIS0_EC3_OPERATOR_COARISING_NOTE.md,
  AXIS0_ENTROPIC_MONISM_DOCTRINE_BRIDGE.md,
  AXIS0_ENTROPIC_MONISM_AXIS_MAP.md,
  sim_axis0_fep_compression_framing.py,
  sim_axis0_fe_indexed_xi_hist.py

---

## 1. What Was Found (Probe-Backed)

### 1.1 EC-3 Co-arising: ga0 and MI move together every step ✓

At every single trajectory step, sign(Δga0) = sign(ΔMI). The entropy field
and the information structure are not correlated — they co-arise. Neither leads
nor lags the other (T3 peak cross-correlation at lag=0, all 6 configurations).

The period-4 pattern maps exactly onto Ti/Fe/Te/Fi:

| Operator | Δga0 | ΔMI | EC-3 role |
|---|---|---|---|
| Ti | ↓ (−0.111 mean) | ↓ | Identity assertion: `a=a` |
| Fe | ↑ (+0.038 mean) | ↑ large | Contrast generation: `a~b` |
| Te | ↑ (+0.094 mean) | ↑ small | Contrast exploration |
| Fi | ↓ (−0.052 mean) | ↓ | Identity refinement |

One Ti→Fe→Te→Fi subcycle = one EC-3 execution.
Eight EC-3 cycles per engine cycle.

### 1.2 Compression horizon: 7 steps ✓

T1 backward MI asymmetry by lag (1/inner, confirmed on outer):

| Lag | Asymmetry |
|---|---|
| 1 | +0.0044 |
| 4 | +0.0025 ← dip (full EC-3 cycle, state partially resets) |
| 7 | +0.0203 ← peak (1.75 cycles, max compression-to-expansion span) |
| 8 | +0.0140 ← falls |

The lag=4 dip confirms one EC-3 cycle = 4 steps.
The lag=7 peak is 1 full cycle + 3 steps (Ti→Fe→Te) of the next —
this is the maximum compression-to-expansion arc.

### 1.3 FEP framing: compression-from-future is confirmed, 6/6 ✓

T1 6/6: backward MI ≥ forward MI (future predicts past better, all configs)
T3 6/6: ga0 changes lag or are simultaneous with MI (entropy follows structure)
T4 4/6: MI trends upward on inner/outer (attractor convergence)

Overall: 6/6 COMPRESSION-FROM-FUTURE verdict across all engine/torus configs.

The Fe step is NOT the sensory correction in a FEP sense. Phase5A certified
marginal-preserving MI ≈ 0 — the predictive prior (Bell bridge) dominates.
Fe is where the prior is INSTANTIATED (marginals expand). The entire 4-step
cycle is prediction unfolding; there is no dedicated sensory operator.
Ratio: 25% instantiation peaks (Fe), 75% exploration/consolidation — all prior.

### 1.4 Fe-indexed Xi_hist: Phase 4 winner holds for inner/outer ✓

| Bridge | mean MI | gain vs Phase4 |
|---|---|---|
| A Phase4 winner (baseline) | 1.532 | — |
| B Fe-indexed 7-step window | 1.449 | −0.083 |
| C Fe pairs only | 1.371 | −0.161 |
| D lag=7 pairs | 1.489 | −0.043 |

The Phase 4 full-trajectory exponential weighting already implicitly captures
the Fe structure — it is not improved by explicit Fe indexing on inner/outer.

**Exception: Clifford torus.**
Fe-indexed beats Phase 4 winner on both engine types for Clifford
(+0.108 gain for Type 1, +0.012 for Type 2). When attractor convergence is
weak (Clifford anomaly — low chirality, high variance), time-position weighting
degrades and operator-type indexing is more robust.

---

## 2. Renamings

| Old term | New term | Reason |
|---|---|---|
| "Retrocausal weighting" | "Attractor-proximity weighting" | Later steps are closer to the attractor, not causal backward. Classical past→future causation is not fundamental in this model. |

---

## 3. What This Context Opens (Proposal-facing)

These are not canon claims. They are direction-setting based on the probe findings.

| Item | Proposal |
|---|---|
| The cut is sharpest at Fe-transition events | The shell/interior-boundary cut is not static at a fixed η level — it is sharpest when Ti releases into Fe. Exact constraint form: OPEN. |
| ga0 = MI up to a gauge | The co-arising is total; in entropic monism, entropy and information are the same thing. Formal proof: OPEN. |
| Fe-indexed bridge for Clifford | When chirality is weak, Fe-indexed construction outperforms time-position weighting. May be the right construction for the doctrine-facing shell bridge. |
| 7-step window as Xi_hist window | Current Xi_hist uses full 32-step trajectory. A 7-step rolling window may be cleaner. Phase4 winner holds overall — test specifically with Fe-anchor. |

---

## 4. Axis 0 Open Item Status (Unchanged)

| Item | Status |
|---|---|
| Final canon Xi | OPEN — Xi_hist strongest executable; this pass adds Fe-transition insight |
| Final cut A\|B | OPEN — shell strongest doctrine-facing; cut sharpest at Fe event (new) |
| Shell algebra A_r\|B_r | OPEN — EC-3 constraint form at Fe transition unknown |
| i-scalar derivation | OPEN — named; not yet derived from RC-1 + RC-2 |
| Bridge/cut unification | OPEN — Xi_hist emits; shell locates; one theorem pending |
| ga0 = MI formal proof | OPEN — empirically confirmed; algebraic form unknown |

---

## 5. Anti-Smoothing

- Fe-indexed Xi_hist does NOT beat Phase 4 winner on inner/outer
- Clifford exception is not a general win; it confirms the Clifford anomaly
- The 7-step compression horizon is empirical; formal derivation pending
- The "co-arising" finding says ga0 and MI move together — it does not prove they
  are algebraically identical; proof requires RC-1 + RC-2 derivation
- FEP framing is a reading of the probe results; it is not a derivation of FEP from
  the engine axioms
