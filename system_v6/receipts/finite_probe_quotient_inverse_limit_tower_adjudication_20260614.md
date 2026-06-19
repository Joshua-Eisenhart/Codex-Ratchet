# Adjudication — finite_probe_quotient_inverse_limit_tower_1q_through_4q (2026-06-14)

```yaml
receipt_kind: layer_adjudication (first real nesting tower; layers 1->2->3 + 4q one-beyond)
sim: system_v7/sims/finite_probe_quotient_inverse_limit_tower_1q_through_4q
status_label: passes local rerun  (NOT canonical by process)
classification: scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false (machine-enforced)
provenance: workflow w4wwel916 (codex2 build; wizard council Popper/Feynman/Orwell + adversarial; council-collapse-auditor; fresh-context fabrication-auditor)
```

## What is genuinely true (fresh-audit + adversarial + independent recompute)
- **Real nesting tower.** Rungs 1q/2q/3q/4q are genuinely distinct objects (Hilbert dims 2/4/8/16). Independent recompute: `bell_ab_bell_cd` has Schmidt rank 4 at cut 02|13 and rank 1 at 01|23 — impossible below 4q; asymmetric biseparable strata [2,2,1] vs [1,2,2]. Not 1q copies.
- **Compatibility law non-trivial + computed.** `q_B(Tr_{A\B}(rho_A)) == q_B(rho_B)`; predicate genuinely can fail (an arbitrary marginal `diag(.7,0,0,.3)` is not in the 2q class table). `tower_self_seals=true`, 4q one-beyond round-trip all true.
- **SMT flip load-bearing, NOT a count tautology.** z3+cvc5 over exact rationals: `mix_00_11` vs `maxmix_2` differ on exactly one probe (ZZ=1.0 vs 0.0); SAT under full M, UNSAT when ZZ erased. Per-rung quotient counts agree across 3 legs: 1q 5/5, 2q 10/8, 3q 10/9, 4q 5/5 (real flip at 2q/3q under ZZ erasure).
- **Three distinct legs**, `reads_peer_result=false` all three (Julia exact eigdecomp + partial trace / JAX vmap + z3/cvc5 / PyTorch jacrev). `all_three_agree=true`.

## Collapse-audit catch (the project's named failure mode, caught)
Three of four voices (Popper, Orwell, Adversarial) converged on labeling the z3/cvc5 SMT a "v6 count-tautology inflator." The collapse-auditor read JAX source (lines 385–432) and showed the assertion is a disjunction of **computed exact-rational expectation differences** — structurally distinct from the v6 count-tautology (`COUNT>0` over a counter). **Correlated mislabel, not validation.** The mislabel is retracted.

## Genuine open findings (carry forward — do NOT promote past scratch)
1. **GATE BUG (blocking admission, not a sim defect):** `validate_name_math_correlation.py` fails the tower on tokens `1q`/`4q` ("Hilbert dim 2/16 absent"). The dims ARE present at `rungs.1q.hilbert_dimension=2` … `4q=16` and `hilbert_dimensions_by_depth`; the gate's scanner only looks in flat/ladder containers, not the nested `rungs` dict. **Fix the gate scanner** (after WF#1 lands, to avoid scripts/ collision). Admission fails solely on this.
2. **load_bearing label on z3/cvc5 — owner-tunable fork (collapse-auditor: "must reach the owner"):** the solver does ground constant-folding (a disjunction with no free variables ≈ Python `any()`), not quantifier reasoning. By the existing mechanical gate (`validate_smt_not_tautology.py`, 0 violations) the label holds; the deeper question — does `load_bearing` require the solver to *reason*, or merely be the authoritative decision procedure for the predicate — is a definitional choice the owner may want to tighten. NOT blocking; the underlying math is honest and correctly ceiled.
3. **Forecast overclaim (Orwell):** `forecast_matches_computed["4q"]=true` with prose "fiber product of Schmidt stratifications / rank-tuple lattice" — the fiber product is NOT computed; 5 states are merely individually separated. Downgrade to "partial — states separated; fiber-product not computed." The 1q "Hopf tori matched" checks only Bloch-radius-1, not the fibration.
4. **Fixture-curated self-seal:** `tower_self_seals=true` is a consistency pass over a closed hand-chosen ~30-state set, not a tower theorem. Honestly disclosed. Needs adversarial boundary-state injection + larger sets to strengthen.
5. **Thin 4q (5 states, no W4/no mixed classes):** 4q multipartite classification underdetermined.

## Per the layer-completeness contract (WF#4, in progress)
Layers 1–3 + 4q one-beyond are at `passes local rerun`. To be **DONE** they still need: the gate-scanner fix (so admission passes), more negatives / boundary states (finding 4–5), the 4q forecast actually computed not asserted (finding 3), and an independent cross-engine partial-trace source audit (Orwell's surviving challenge). The ceiling is honestly set; nothing was promoted.
