# G2 Forced-vs-Installed Discriminator Audit Verdict

Verdict: GENUINE-WITH-CAVEATS

Target: `system_v6/sims/g2_forced_vs_installed_discriminator/`

Bottom line: the discriminator is not decorative. The derivation dimensions recompute independently, the bare-root lanes encode finiteness plus noncommutation only, the final booleans are computed from lane outputs, the corrupted-table control changes the computed derivation dimension, and the envelope holds the scratch/promotion ceiling. Caveat: the seven-unit closure SAT encoding checks pairwise anticommutation plus closure against a fixed Fano/Cayley table; it is not a solver-level proof of exact Fano-line orientation. That is acceptable for this scratch discriminator, but should be hardened before stronger claims.

## Checks

1. Independent derivation recomputation: PASS
   - I rebuilt standard quaternion and octonion tables independently and solved the derivation linear system `D(xy)=D(x)y+xD(y)` with exact SymPy rank.
   - Results: `H rank=13 nullity=3`, `O rank=50 nullity=14`, `O_corrupted rank=61 nullity=3`.
   - This matches the stored target results.

2. Bare-root SAT lanes: PASS
   - In the target, `z3_root_sat` and `cvc5_root_sat` bind only table-derived commutator coordinates and require at least one nonzero commutator.
   - The lane records `finite_table_bound=True`, basis dimension, and commutator-coordinate count. There is no derivation-dimension, 7-unit, octonion, or G2 constraint in the bare-root SAT formula.
   - The forced-commutative control adds only `commutator == 0` and correctly flips the bare-root query to UNSAT.

3. Seven-unit closure encoding: PASS WITH CAVEAT
   - The table is built from explicit Fano triples in all legs, and my independent pair scan found `O_pair_closure_bad_count=0`.
   - The SAT encoding uses seven distinct imaginary slots and requires each selected pair to anticommute and multiply to exactly one signed imaginary unit.
   - This is not a tautological `is_octonion` predicate. It is a structural table predicate.
   - Caveat: the solver does not explicitly assert the Fano incidence/orientation graph; it delegates that to the fixed table and pairwise predicate. Since O has exactly seven imaginary slots, SAT necessarily selects all seven, but hardening should add exact Fano line/orientation checks and a closure-breaking corrupt-table control.

4. Verdict booleans computed from lane outputs: PASS
   - Leg verdicts compute `bare_counterexamples`, `forced_by_root`, `installed_by_carrier_constraint`, `controls`, `shared_scalars`, and `all_pass` from SMT statuses and derivation dimensions.
   - Envelope verdicts recompute from loaded leg payloads: `h_root_pass`, `m2_root_pass`, `o_dim_14`, `h_dim_3`, `m2_dim_3`, SAT status agreement, erased-control status, corrupted-table control, and divergence.
   - I did not find a hand-assigned final verdict independent of lane outputs.

5. Corrupted-table control: PASS
   - Perturbation: flip one Fano product coefficient, `e1 * e2`, implemented as `c[3,1,2] = -c[3,1,2]` in Python and the matching 1-based Julia index.
   - Computed effect: `dim Der(O)` changes from `14` to `3` in Julia, JAX, PyTorch, and my exact independent recomputation.

6. Comparison against prior r4 nonassoc discriminator: PASS WITH MINOR REGRESSION
   - Same core design pattern survives: bare root admits H-like counterexamples, stronger 7-unit/Cl6-style carrier constraint excludes H and admits O, negative controls flip, and the envelope holds scratch-only status.
   - No regression in envelope computation, status ceiling, or installed-not-forced logic.
   - Minor regression: the prior r4 PyTorch leg had a distinct `torch.func.jacrev` sensitivity check. The G2 PyTorch leg mostly mirrors the SMT/rank design with Torch rank computation. This is acceptable for this target, but less independent than r4's PyTorch role.

7. Pin/envelope/ceiling: PASS
   - `validate_three_engine_sim_result.py system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json` returned `ok: true`.
   - Envelope: `schema_version=three_engine_sim_result_v1`, `mode=all_three_full_sims`, lanes `julia/jax/pytorch`, `reads_peer_result=false`, `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `all_pass=true`.
   - Source hashes are present in leg and envelope receipts.

## Hardening List

1. Add an explicit Fano incidence/orientation verifier to the seven-unit lane, not just pairwise anticommutes-and-closes.
2. Add a corrupted-table closure control that runs the seven-unit SAT query on the corrupted O table and expects UNSAT or an explicit mismatch, not only a derivation-dimension change.
3. Make the PyTorch lane independently useful again, for example with a Torch-side linear-system nullspace basis residual, autograd sensitivity to structure constants, or a distinct table-perturbation sensitivity check.
4. Include the exact perturbation coordinate and before/after coefficient in the JSON receipt.
5. Add a source-to-result freshness check in the envelope or validator so stale leg JSON cannot pass after source edits.

## Evidence Commands

- Independent exact recomputation: inline Python/SymPy audit returned `H (13, 3, 64, 16)`, `O (50, 14, 512, 64)`, `O_corrupted (61, 3, 512, 64)`, `O_pair_closure_bad_count 0`.
- Repo validator: `python3 scripts/validate_three_engine_sim_result.py system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json` returned `ok: true`.
