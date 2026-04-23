# AGM-02 Matched-Marginal Attack — Return

**Date:** 2026-03-30  
**Source files read:**
- `AXIS0_ACTIVE_PACKET_INDEX.md`
- `sim_axis0_phase4_final_bridge.py`
- `sim_axis0_phase5a_marginal_preserving.py`
- `axis0_phase4_results.json`
- `axis0_phase5a_results.json`

---

## Verdict

The matched-marginal lane is closed on the current carrier. Phase 4 ran 69 candidates across all cross-temporal strides (1/2/4/8), directions (forward/backward/symmetric), and weighting schemes (uniform/retro/compress/retro-compress/cooling), plus same-time chiral and hybrid variants. Every single candidate failed the matched-marginal filter at tolerance `1e-3`: `matched_marginal_ranking_top10` is empty and `matched_marginal_winner` is null. Marginal deviation for all tested states ranges from 0.655 to 0.784 — one to two orders of magnitude above the filter threshold. Phase 5A independently certifies the same result from the other direction: the Nelder-Mead optimizer found the maximum-MI state compatible with the engine's marginals and it is the product state in every configuration. `mean_preserving = 6.35e-16` (machine-zero); `mean_chiral = 1.69`; ratio preserving/chiral ≈ 0 across all 12 certified blocks (6 engine/torus configs × final_state + history_averaged). Not a single per-step sample across all 48 sampled steps shows a non-zero preserving MI. The carrier — the two-engine, eight-stage, four-operator engine running across inner/clifford/outer torus configurations — produces marginals that are locally product states. There is no room in the marginal-compatible family for nonzero MI. The ~1.5 bits of MI in the winning constructive candidate is entirely Bell-injected by the `make_bell_mixed` construction.

---

## Proposed Test

**No-next-test statement:** There is no plausible matched-marginal variant worth testing on the current carrier. The block is not a gap in the sweep — Phase 4 exhausted direction, stride, and weighting degrees of freedom, and Phase 5A independently confirmed from the optimization side that the marginal-compatible set collapses to the product state. Adding more restarts to the Phase 5A optimizer would not change this: `best_source = "product_seed"` across all 12 blocks means the optimizer never left the product-state basin, which is the correct answer. A variant with different Bell states (e.g., Φ+, tested in Phase 4 as `30_cross_s1_forward_PhiPlus_uniform`, `max_marginal_dev = 0.678`) does not help — neither the Bell state choice nor the weighting moves the marginal deviation toward zero. The matched-marginal lane requires a different carrier (different engine marginals), not a different construction over the existing marginals.

---

## Risk List

- **Reintroduction risk:** The Phase 4 raw MI winner (1.54 bits) looks strong in absolute terms. A future probe that reports MI without simultaneously reporting `max_marginal_dev` or Phase 5A `ratio_preserving_to_chiral` could silently re-promote this as earned closure. Both numbers must travel together.
- **Carrier-swap confusion:** The matched-marginal lane could become live if the engine marginals change (e.g., different torus, different initial condition, or different stage parameters). Any new sim run must re-run Phase 5A before claiming the matched-marginal lane is open.
- **Optimizer false-confidence risk:** Phase 5A uses Nelder-Mead with 15 restarts seeded from the product state. If a future sim uses fewer restarts or a different seed without verifying `feasible_candidates > 1`, a `product_seed`-only optimum could be misread as a thorough search. The current data is honest only because all 12 blocks converged identically to the product state from the seed — this is strong, but the code structure does not enforce a multi-basin check.
