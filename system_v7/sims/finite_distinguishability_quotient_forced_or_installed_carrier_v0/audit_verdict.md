# Audit verdict - finite_distinguishability_quotient_forced_or_installed_carrier_v0

**Computed verdict:** `installed`
**Classification:** `scratch_diagnostic`
**promotion_allowed:** `false`
**formal_admission_allowed:** `false`
**does_not_self_upgrade:** this verdict is the build's own self-assessment. A fresh-context audit is required before citation or promotion. Nothing here becomes canonical by being written.

**Status ladder reached:** `passes local rerun`. The Julia leg, JAX leg, PyTorch leg, and agreement check ran to exit 0 locally. NOT `canonical by process`.

---

## What this sim is

A finite pure-data test on:

- a six-element finite set `S`;
- a two-probe finite family `P`;
- the joint kernel relation `~_P`;
- explicit update maps `U1,U2` with an order-dependent composition witness;
- explicit commuting-control maps `V1,V2`;
- five candidate finite representations of the same quotient/probe data.

The base object contains no Pauli matrices, complex numbers, Hilbert spaces, or density matrices.

## Exact preorder used

For this finite fixture, `A <= B` iff:

1. `A` and `B` reproduce the same quotient class partition.
2. The class-token map `i -> i` preserves every probe-outcome vector.
3. `strength_rank(A) <= strength_rank(B)`.

Strict weakness is `A <= B` and not `B <= A`.

The rank order is:

`C1 bare_set_quotient < C2 classical_probability_simplex < C3 real_vector_real_operator < C4 complex_operator_density_matrix < C5 ordered_cone_gpt`.

## Min(Surv)

The active quotient classes are:

`[[s0, s1], [s2, s3], [s4], [s5]]`.

Survivors under `F01 + N01 + reproduce quotient` are expected to be:

`C1`, `C3`, `C4`, and `C5`.

`C2` fails active `N01` because this fixture restricts it to a commuting diagonal update family, while `U1,U2` have a measured order-dependent composition witness.

`Min(Surv) = [C1]`. It is not plural-incomparable: `C1` is strictly below every other survivor by the computed preorder.

## SMT flip

The z3 and cvc5 flip asks:

`exists a commutative update structure reproducing the measured quotient maps and the U1/U2 action?`

The full `U1,U2` case is `unsat` in both solvers. The erased-control `V1,V2` case is `sat` in both solvers. That means this data forces noncommuting update structure, not complex/density-matrix structure.

The secondary real-operator check is `sat` in both solvers. A real transition-matrix structure can reproduce the quotient and the witnessed noncommutation, so complexness is not forced by this finite data.

## Controls

| Control | Predicted behavior | Expected result |
|---|---|---|
| `commuting_update` | With `V1,V2`, a commutative structure survives | pass |
| `label_shuffle` | Relabelling probe outcomes preserves the quotient and verdict | pass |
| `probe_erase` | Removing `p_alpha` collapses the quotient from 4 classes to 2 | pass |
| `matrix_form_installed_vs_forced` | `C1` reproduces all probe outcomes without constructing a density matrix | pass |

## Verdict

The complex/density-matrix representation is `installed` in this fixture, not forced.

Reason: full SMT says noncommuting updates are forced by `U1,U2`, erased SMT says the control behaves, real-operator SMT says real structure suffices, and `Min(Surv)` contains `C1`, a strictly weaker survivor below `C4`.

## Fenced ceiling

This is a bounded finite diagnostic. It does not promote the result to canonical, does not formally admit the representation order, and does not claim a theorem beyond this exact `S`, `P`, update maps, candidate set, and preorder.

## Reproduce

```bash
/opt/homebrew/bin/julia finite_distinguishability_quotient_forced_or_installed_carrier_v0_julia.jl
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 finite_distinguishability_quotient_forced_or_installed_carrier_v0_jax.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 finite_distinguishability_quotient_forced_or_installed_carrier_v0_pytorch.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 check_agreement.py
```
