# Audit verdict - finite_probe_quotient_inverse_limit_tower_1q_through_4q

**Classification:** `scratch_diagnostic`
**promotion_allowed:** `false`
**formal_admission_allowed:** `false`
**does_not_self_upgrade:** this verdict is the build's own self-assessment. A fresh-context audit is required before citation or promotion. Nothing here becomes canonical by being written.

**Status ladder reached:** `passes local rerun` (the Julia leg, JAX leg, PyTorch leg, and agreement check ran to exit 0 locally). NOT `canonical by process`.

---

## What this sim is

A finite stratified inverse-limit tower of probe-relative quotients at `1q`, `2q`, `3q`, and `4q`.

- The finite state sets are small exact-rational density-matrix fixtures, with product states, entangled states, mixed marginals, marginal-radius variation, closure marginals, and a 4q one-beyond nesting test.
- The probe family is the joint Pauli tensor family over `{I, X, Z}` excluding all-`I`; the erased family removes pairwise `ZZ` probes.
- Each rung computes `S/~_M`, spectra, von Neumann entropy, partial-trace marginals, quotient classes, and erased-probe quotient classes.
- The tower law checks that lower-rung quotient class identity is preserved under partial trace projections.

## Measured per-rung result

Read from the fresh agreement JSON written by `check_agreement.py`.

| Rung | Finite set size | Full quotient count | Erased quotient count | Separating observation |
|---|---:|---:|---:|---|
| `1q` | 6 | 6 | 6 | no pairwise `ZZ` probe exists at this rung |
| `2q` | 12 | 12 | 10 | erasing `ZZ` merges `mix_00_11` with `maxmix_2` and merges the two Bell states under the active signature |
| `3q` | 15 | 15 | 14 | erasing pairwise `ZZ` merges `mix_000_111` with `maxmix_3` |
| `4q` | 10 | 10 | 10 | the one-beyond set remains separated by the remaining probes |

## Closure injection (disclosed)

The `closure_*` states in `spec.json` are deliberately injected partial-trace marginals of higher-rung `4q` states. Their presence stocks the lower rungs with the exact marginals needed by selected higher states, so the tower seal should be read as `seals_by_construction_on_marginal_closed_fixture=true`.

Injected closure labels:

- `closure_1q_w4_keep0`: marginal of `w4`, keep `0`.
- `closure_2q_w4_keep01`: marginal of `w4`, keep `01`.
- `closure_2q_dicke4_2_keep01`: marginal of `dicke4_2`, keep `01`.
- `closure_3q_w4_keep012`: marginal of `w4`, keep `012`.
- `closure_3q_dicke4_2_keep012`: marginal of `dicke4_2`, keep `012`.
- `closure_3q_ghz_ab_prod_cd_keep023`: marginal of `ghz_ab_prod_cd`, keep `023`.
- `closure_3q_bell_ac_prod_bd_keep012`: marginal of `bell_ac_prod_bd`, keep `012`.
- `closure_3q_bell_ac_prod_bd_keep123`: marginal of `bell_ac_prod_bd`, keep `123`.

## Load-bearing SMT flip

The SMT check is not a count tautology. It asks whether an active product/local Pauli probe separates the exact rational expectation signatures of `mix_00_11` and `maxmix_2`.

| Solver | Full active probes | Erased active probes | Verdict |
|---|---|---|---|
| z3 | `sat` | `unsat` | flip confirmed |
| cvc5 | `sat` | `unsat` | flip confirmed |

The entanglement-separability probe oracle also finds witnesses for `bell_phi_plus` above threshold `1/2`; the quotient-class flip is the load-bearing proof gate because deleting `ZZ` removes the separating formula.

## Three engines

| Leg | Computation style | Distinct load-bearing work | Peer result reads |
|---|---|---|---|
| Julia | `exact_hermitian_eigendecomposition_and_partial_trace` | `eigvals(Hermitian(...))`, loop partial traces, SVD Schmidt spectra | `false` |
| JAX | `vmap_batched_expectation_and_marginal_tensor` | batched probe expectations, tensor partial traces, z3+cvc5 exact rational SMT flip | `false` |
| PyTorch | `autograd_jacobian_over_state_parameters` | `torch.func.jacrev` derivative of probe expectations for a mixture parameter | `false` |

The only shared input is `spec.json`. The agreement checker is the only file that reads peer results.

## Compatibility and seal finding

The compatibility law passed in all three legs on the marginal-closed fixture.

- Construction-seal field: `seals_by_construction_on_marginal_closed_fixture=true`.
- The 4q one-beyond round trip passed: `one_beyond_self_seals=true`.
- The open fixture test rebuilds lower-rung full-probe class tables with all `closure_*` labels removed.
- Open fixture result: `open_fixture_seals=false`; `69` of `98` projections landed in existing non-closure classes and `29` of `98` did not.
- Finding string: `does NOT seal on open fixture: 29 of 98 higher-state projections have no matching non-closure lower class`.

This means the closed-fixture seal is useful as a fixture-consistency check, but it is not evidence that arbitrary open higher-rung states project into existing lower non-closure classes.

## Section-5 forecast versus computed geometry

Forecast text in `spec.json`:

`local Hopf tori (S^1->S^3->S^2 single-qubit pure-state surface) -> at 2Q become marginal-radius shells (A-marginal Bloch radius r_A in [0,1] as a separating coordinate, concentric product/entangled shells) -> at 3Q become Schmidt strata (rank tuples (rank_A,rank_B,rank_C) across the three cuts) -> at 4Q become a computed finite rank-tuple lattice with cross-rung marginal-rank consistency checks for the observed pure states.`

Computed checks:

| Rung | Forecast matched | Computed evidence |
|---|---|---|
| `1q` | `true` | pure states have unit Bloch radius and `qmax` has radius 0; Hopf fibration was not tested |
| `2q` | `true` | marginal radii include pure, mixed, and intermediate shells |
| `3q` | `true` | rank tuples include product `[1,1,1]`, biseparable permutations of `[1,2,2]`, and genuinely tripartite `[2,2,2]` |
| `4q` | `true` | `rank_tuple_lattice_computed=true`; the rank-tuple lattice and cross-rung marginal-rank consistency checks pass |

## Lineage

- **F01:** simultaneous-distinguishability surface. The probe family acts jointly; `~_M` is the joint kernel of probe expectations, extended here to multi-qubit probe tensors and partial-trace-compatible quotients.
- **N01:** order/persistence note. The inverse-system projections compose in fixed parent-to-child order; the compatibility law is the persistence-under-projection condition. This sim records projection order and compatibility, but makes no numeric order-gap claim.
- **Root axiom `a = a iff a ~ b`:** identity at each rung is the probe-relative class `S/~_M`; tower identity is the compatible family across rungs.

## Honest limits / what would flip the verdict

- This is a bounded finite fixture, not a full survivor import and not a formal proof.
- The v6 survivor counts are cited only as provenance in `legacy_project_labels`; they are not runtime data.
- The construction seal is only for this exact marginal-closed state set and this exact probe family.
- The open fixture test currently does not seal; any prose claiming an open-fixture seal would be wrong.
- The verdict flips to failed if any leg reads another leg's result, if `spec.json` is found to smuggle quotient counts or computed invariants, if z3 and cvc5 do not both show `sat -> unsat` for full versus erased probes, if any rung is missing, or if projection compatibility is checked by label echo rather than computed partial traces.

## Reproduce

```bash
/opt/homebrew/bin/julia finite_probe_quotient_inverse_limit_tower_1q_through_4q_julia.jl
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 finite_probe_quotient_inverse_limit_tower_1q_through_4q_jax.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 finite_probe_quotient_inverse_limit_tower_1q_through_4q_pytorch.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 check_agreement.py
```
