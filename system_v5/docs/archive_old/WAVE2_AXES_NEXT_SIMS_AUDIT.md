# Wave-2 AXIS Next-Sims Audit

**Date:** 2026-04-04
**Grounded in:** `a0_kernel_discriminator_results.json`, `hopf_pointwise_pullback_results.json`, `history_vs_pointwise_ax0_results.json`, `xi_bridge_bakeoff_results.json`

---

## Strongest Primitive

**K1_Ic = −S(A|B) = I_c(A⟩B)** — coherent information.

- Kernel discriminator score: **5/6** (vs MI 4/6, shell_Ic 4/6)
- Passes: signed (R1), Bell ceiling (R3), Werner monotone (R4), Schmidt sensitive (R5), CQ honest (R6)
- Fails only: R2_sep_anchor (separable states land at 0, not a distinguished anchor value)
- This is the strongest simple Ax0 kernel primitive. MI cannot go negative; shell_Ic loses Bell ceiling and CQ honesty.

## Strongest Bridge Family

**Chiral** — least-arbitrary bridge in the Xi bakeoff.

- Only family with **positive I_c on all 6 engine configs** (both engine types, all 3 tori)
- Composite score: chiral **0.80** > shell 0.46 > point_ref 0.29 > hist 0.20
- Lowest perturbation sensitivity on inner/outer tori
- Nonzero fiber/base loop MI (not geometry-blind)
- History bridges dominate pointwise by +0.93 MI gap in the history-vs-pointwise probe, but the bakeoff's chiral family is evaluated pointwise and still leads — it captures inter-chirality correlation that the other pointwise families miss

## Hopf Pullback Confirmation

- Fiber loops: constant pullback (density-stationary) — **confirmed**
- Base loops: varying Bloch trajectory (density-traversing) — **confirmed**
- Product-state I(A:B) and I_c identically zero — the pointwise product pullback is honest but **trivial**
- This confirms: a nontrivial bridge construction is required for Ax0. Bare pullback cannot do it alone.

## Open Issues

1. **No tier-5 Xi sim exists.** Chiral is the bakeoff winner but has not been tested under a dedicated bridge-layer sim with explicit cut construction on the live Weyl engine cycle.
2. **Type2 Weyl inversion still open** (tier 3/4). Type2 fiber/base grammar is inverted vs canonical.
3. **C1 MI-based negative controls not killed** (tier 6). Only concurrence/negativity kill fake coupling. MI is not sufficient.
4. **History family split**: hist_retro_exp wins Type1, hist_fe_indexed wins Type2 — no single history bridge is universal yet.

## Next Bounded Follow-Up

**One sim: Chiral bridge Xi under full engine cycle.**

- Input: 8-step Type1 + Type2 engine trajectories on all 3 tori
- Bridge: chiral (L⊗R inter-chirality cut)
- Observables: I_c sign across cycle, monotonicity over stages, fiber/base discrimination, comparison to hist_retro_exp and hist_fe_indexed at same sample points
- Goal: determine if the chiral bridge can serve as tier-5 Xi, or if it must be composed with a history weighting to reach nontrivial I_c on the full cycle
- Scope: bounded to the existing engine_core infrastructure; no new geometry required

This is the single highest-value next move because it connects the winning kernel (K1_Ic) to the winning bridge family (chiral) on the live engine, closing the gap between tiers 5 and 7.
