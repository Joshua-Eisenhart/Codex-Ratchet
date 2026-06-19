# Tower hardening — 3 real defects (full-fleet 13/13 + fresh audit, 2026-06-14)

The WF-C hardening pass improved this tower but did NOT make it DONE. This marker supersedes the stale `audit_verdict.md`. Status: **passes local rerun, NOT canonical, self-seal claim caveated** (do not cite `tower_self_seals=true` or `4q_fiber_product_computed=true` as standing).

## What is genuine (held under adversarial attack)
- Both negative controls **genuinely fire** (tamper-tested: flipping a control → agreement checker exit 1): `perturbed_marginal_excluded` (diag(0.7,0,0,0.3) is a real off-class miss); `label_echo_trap` (GHZ4|012 is a classical mixture XXX=0 vs GHZ3 pure XXX=1 — fires on the computed partial-trace signature, not a name match).
- The z3/cvc5 SMT flip is **load-bearing** (ZZ is the sole separator; erasing ZZ → UNSAT; coupled to measured values). 3 engines genuinely independent (Julia eig / JAX vmap+SMT / PyTorch jacrev; reads_peer_result=false). 1q forecast honestly fenced (`hopf_fibration_computed=false`, "Hopf NOT tested"). 4q thickened to 10 states incl W4 (Schmidt `[√¾,√¼]`, distinct from GHZ4).

## The 3 defects (must fix before "DONE")
1. **FIXTURE-CURATED self-seal (structural, undisclosed).** spec.json injects 8 `closure_*` states that are byte-exact the partial-trace images of the higher-rung states; removing them flips `tower_self_seals` True→False (29 projection failures). The seal is largely a tautology of stocking the lower rungs with exactly the needed marginals. FIX: reword to **"seals by construction on a marginal-closed fixture"**, DISCLOSE the closure injection, and add an honest test of the seal on a genuinely-open (non-prestocked) higher-state set — reporting the real result even if it does NOT seal (that is informative, not a failure to hide).
2. **`4q_fiber_product_computed: true` overclaims.** The function computes a rank-tuple lattice (Hasse structure) + marginal-rank consistency, NOT a fiber product over 2q/3q Schmidt strata. FIX: rename to `rank_tuple_lattice_computed`, or actually construct + verify the fiber-product universal property. The agreement checker currently gates on the misnamed label.
3. **`audit_verdict.md` is STALE.** Its per-rung table (5/10/10/5) predates the hardening; the live run is **6/12/15/10 full, 6/10/14/10 erased**, and the old "fiber product of 2Q/3Q Schmidt stratifications" forecast text is gone from spec.json but survives in the doc. FIX: regenerate `audit_verdict.md` from the current run.

## Note
The full fleet (codex2 ×4 + grok + gemini + OpenRouter) held divergence rather than collapsing: codex2 arbiters led with the stale-table defect; gemini found the harsher curated-seal defect; both kept live. The convergence on "genuine SMT + genuine negatives + independent engines" is real (each verified separately). Reclassify-to-DONE only after the 3 fixes.
