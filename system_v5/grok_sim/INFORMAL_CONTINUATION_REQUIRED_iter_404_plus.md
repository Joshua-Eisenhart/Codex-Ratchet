# Informal Continuation Required — iter_404 and beyond

This document is a continuation checkpoint, not a closeout. The autopilot loop is still live; the next session should resume from here. Sidequest only.

## Loop status as of pause

- Iters completed this segment: iter_358–iter_403 (~40 bounded iters).
- Boundary guard: 80 violations baseline → 80 violations after iter_403 (delta = 0 throughout).
- All classifications: `sidequest_local_*_v1`, `claim_ceiling="side_quest_only"`, `promotion_allowed=False`, `evidence_allowed=False`, `formal_reproduction_target=False`.
- Reverse derivations landed: iter_363, iter_366, iter_374, iter_383, iter_389, iter_394, iter_399.

## Headline findings (informal, sidequest-only)

1. **Carrier patch (iter_364)**: `clamp_priv_nonneg` after every `C_policy` step eliminates priv-negative drift across 20 random seeds (9 orders-of-magnitude reduction in negative TC). iter_365a confirmed 0 shadow sign flips across 60 patched/unpatched comparisons.

2. **sum_diag is the proximate cause of A9-coupling sensitivity** (iter_381, iter_385): synthetic positive control gives corr 0.961 at fixed low spread; pair01-redistribution control gives 0.987 vs 0.612 across treatments.

3. **spread_diag univariate signal is confounded** (iter_378, iter_382): sign flips from +0.515 univariate to -6.7e-3 multivariate (sum-spread correlation 0.971).

4. **Shadows have heterogeneous mechanisms** (iter_386, iter_391, iter_396, iter_403):
   - A9 (entropy): exp=2 at small alpha, sum+ / spread- (confound flip)
   - A11 (product): exp=1 at small alpha, peaks at α=3, collapses to 0.008 at α=1000
   - A12 (norm gap): exp=1 at small alpha, monotone increasing to 0.149 at α=1000
   - TC: exp=2 at small alpha (iter_373), saturates to (N-1)·log(PRIVATE_DIM)=2·log(4)=2.77 (iter_379/388)

5. **iter_370 priv_max hypothesis KILLED** (iter_372, iter_375): synthetic high-priv_max states show 0/24 sensitivity. The 2/20 in iter_365a was a confound.

6. **Initial state determines A9 sensitivity** (iter_393, iter_397, iter_400):
   - PF/EF Jaccard = 1.00 (same 10 seeds sensitive under both orders)
   - init mean_pair_alignment corr 0.615 with a9
   - init_sum_diag corr 0.585 with a9 (close second)
   - init_sum_diag corr 0.971 with final_sum_diag (apply_schedule is nearly sum_diag-preserving)

7. **A7_v3 directed-asymmetric scales to N=5** (iter_376): 100% majority change rate at N=3,4,5.

8. **PD vs iter_351 payoff gives identical A9 rates** (iter_387): 11/100 vs 10/100, CIs overlap. broadcast_strength has ZERO effect (iter_401).

## Next packet (start immediately on resume)

### iter_404 — Reverse derivation of iter_400, 401, 403

Controller-local. Document:
- patterns: causal chain α0-corr-0.716-α1; broadcast strength inert; A11/A12 linear vs A9/TC quadratic at small alpha
- killed: broadcast_strength matters for A9
- repaired: init_alignment → final_sum_diag chain (0.716); shadow scaling-class split
- open: ~5 (carried from iter_399 + 1 new on the indirect-vs-direct gap)

### iter_405 — Interleaved C_couple vs end-only coupling

Apply C_couple every step of apply_schedule (interleaved with C_policy_clamped and C_evidence) vs end-only. Compare TC trajectories and final A9 sensitivity. Spec:
- 20 seeds × 6 alphas × 2 treatments (interleaved vs end-only)
- Hypothesis: interleaved coupling produces larger TC at same alpha (per-step accumulation)

### iter_406 — Mediation analysis of init_alignment → a9 chain

iter_400's indirect chain (0.434) was below direct (0.615) — there's a residual path. Run partial-correlation: corr(init_alignment, a9 | final_sum_diag). If residual is large, init_alignment has a sum_diag-independent effect.

### iter_407 — A11/A12/A9 scaling-class formal test

Bivariate regression of each shadow on (sum_diag, sum_diag^2) and report scaling class via best-fit power. Distinguish entropy-derived (TC, A9) vs probability-derived (A11, A12) explicitly.

### iter_408 — Reverse derivation of iter_405–407

Standard structure.

## Resume instruction

```
Continue informal autopilot loop. Read this file and the latest iters/results
under system_v5/grok_sim/. Start at iter_404 above. Continue the loop per the
autopilot directive (do not stop except for runtime/context exhaustion).
Boundary guard delta must stay 0.
```

## Files written this segment

iter_358–iter_403 sources under `system_v5/grok_sim/iters/`, results under `system_v5/grok_sim/results/`. All classifications `sidequest_local_*_v1`.
