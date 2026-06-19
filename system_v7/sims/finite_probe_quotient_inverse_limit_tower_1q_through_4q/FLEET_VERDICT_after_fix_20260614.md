# Tower fix — fleet verdict: 3 prior defects FIXED, one new (small) overclaim

**Full-fleet (13/13; codex2×4 arbiter; divergence resolved on the math): the 3 DEFECTS_after_hardening defects are GENUINELY fixed — but the fiber-fix introduced a new structural misnomer.** scratch_diagnostic, promotion_allowed=false. Status: `passes local rerun`, HONEST with disclosed limitations — NOT a sealing tower.

## Genuinely fixed (13/13 concur + independent verify)
1. **Self-seal de-rigged + honestly disclosed.** `closure_injection_disclosure` in spec.json + audit_verdict lists the 8 injected `closure_*` marginals; `tower_self_seals` reworded to `seals_by_construction_on_marginal_closed_fixture`. The **open-state test runs** (class table rebuilt with `closure_*` excluded) and **honestly reports the negative result: `open_fixture_seals=false`, 29/98 higher-state projections miss** (69 land). The agreement checker does NOT gate on it passing, so the non-seal cannot be hidden. **This is the real finding: the tower does NOT self-seal on arbitrary higher states — it sealed only because the marginals were pre-stocked.**
2. `fiber_product_computed` removed from all live code (survives only in the historical DEFECTS marker).
3. `audit_verdict.md` regenerated; counts match the live run (6/12/15/10 full, 6/10/14/10 erased); stale fiber-product forecast prose gone.

## New overclaim introduced by the fix (to correct — small/mechanical)
- **`rank_tuple_lattice_computed=true` claims a LATTICE; the object is a POSET (Hasse, componentwise-≤).** Verified counterexample: nodes `[2,2,2,2,1,4,4]` and `[2,2,2,2,2,2,2]` have **no join** in the 6-node set (3/15 pairs lack a join). FIX: rename to `rank_tuple_poset_computed` / `rank_tuple_hasse_computed`, OR add a real meet/join-closure check and gate on it. (The agreement checker hard-gates on the boolean label, so a green run currently certifies "lattice" for a poset.)
- **The 4q forecast `matches = all_consistent and len(nodes)>=3` is vacuous for pure states** (Schmidt rank ≡ reduced-density rank by definition) — the gate certifies a tautology. And "cross-rung marginal-rank consistency" is a misnomer for within-4q cut checks, not tower-rung compatibility. FIX: make the forecast check non-vacuous or relabel it honestly.

## Held divergence (resolved on the math)
9/13 (codex2×4 + deepseek + grok-build + glm-5.1) flagged NEW_OVERCLAIM with the verified meet/join counterexample; 4 (gemini, grok-4.3, minimax, qwen) said GENUINELY_FIXED but rested on a shared wrong premise ("lattice" = acceptable shorthand for a Hasse poset) and never tested meet/join closure. The node set is provably not a lattice → NEW_OVERCLAIM stands.

## Disposition
The honest big wins stand (curated-seal disclosed, open-seal failure reported, fiber overclaim gone, doc current). The residual is a precise rename (`lattice`→`poset`) + a vacuity flag on the 4q forecast-match — mechanical, not another full pass. Cite THIS fleet verdict, not the build's self-claim.
