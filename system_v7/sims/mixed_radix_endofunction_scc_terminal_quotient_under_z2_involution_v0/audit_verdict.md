# Audit verdict - mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0

**Classification:** `scratch_diagnostic`
**promotion_allowed:** `false`
**formal_admission_allowed:** `false`
**does_not_self_upgrade:** this verdict is the build's own self-assessment. A fresh-context audit is required before citation or promotion.

**Status ladder reached:** `passes local rerun`. The Julia leg, JAX leg, PyTorch leg, agreement check, and name/math correlation gate all exited 0 in this build session.

---

## What this sim is

This is a finite pure-math reclamation of the v6 feedstock into v7 naming.

- Finite set: `Z/2 x Z/4 x Z/4 x Z/2`, encoded by mixed radix into 64 ids.
- Two orientation maps: `map_plus` and `map_minus`.
- Each orientation is an endofunction on the 64-element set.
- The quotient is the SCC partition of that endofunction graph.
- Terminal SCCs are sinks in the SCC condensation graph.
- The Z/2 involution complements coordinate index 3 and fixes the other three coordinates.

## Measured result

The three legs agree on the selected asymmetric parity law:

| Orientation | SCC quotient classes | Terminal SCC count | Terminal SCC sizes |
|---|---:|---:|---|
| `map_plus` | 41 | 1 | `[24]` |
| `map_minus` | 41 | 1 | `[24]` |

The result table is also written by `check_agreement.py` to `results/mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0_agreement_results.json`.

## Load-bearing SMT equivariance flip

The SMT question is:

`does there exist a state s with T(sigma(s)) != sigma(T(s))?`

The JAX leg encodes `T` and `sigma` as integer arrays constrained to the computed images for all 64 states. The query is a disjunction over computed image disequalities. It is not a count tautology: no solver assertion has the form `count == v` paired with `count != v`.

Expected structural flip:

- conserved law: z3 `unsat`, cvc5 `unsat`;
- selected asymmetric parity law: z3 `sat`, cvc5 `sat`;
- reference parity-toggle law: directly computed equivariant, preserved as a comparison row.

The reference parity-toggle row matters because the feedstock-style XOR update commutes with a parity-only involution. The non-equivariant SMT row is therefore a named structural control, not an uninspected relabel of the old result.

Fresh run details:

| Orientation | Conserved direct separators | Selected law direct separators | z3 conserved | z3 selected | cvc5 conserved | cvc5 selected |
|---|---:|---:|---|---|---|---|
| `map_plus` | 0 | 2 | `unsat` | `sat` | `unsat` | `sat` |
| `map_minus` | 0 | 6 | `unsat` | `sat` | `unsat` | `sat` |

## Three genuinely different methods

| Leg | Signature method |
|---|---|
| Julia | exact integer endofunction with `Graphs.strongly_connected_components` and `Graphs.condensation` |
| JAX | `jax.vmap` materializes the 64-entry transition table in one batched pass, then `networkx` computes SCCs, with z3+cvc5 SMT |
| PyTorch | sparse adjacency tensor plus boolean reachability closure from adjacency powers |

All three legs read only `spec.json`. No leg reads another leg's result.

## Lineage

- F01: the SCC quotient is computed over the simultaneous finite endofunction table.
- N01: the transition composes fixed readout, mixed-radix carry, and z2-coordinate update in a measured order.
- Root axiom: `a = a iff a ~ b`, with `~` realized here as mutual reachability in the computed graph.

## Honest limits / what would flip

- This is `scratch_diagnostic`; it does not promote itself.
- A fresh audit should inspect whether the selected asymmetric parity law is admissible for the next claim. The build preserves the feedstock-style parity-toggle comparison, but the SMT SAT row intentionally uses the asymmetric law required to make equivariance fail structurally.
- If any leg reads a peer result, if `spec.json` contains a precomputed transition table or SCC answer, or if the SMT block is reduced to a count identity, withdraw the result.

## Reproduce

```
/opt/homebrew/bin/julia /Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0/mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0_julia.jl
```

```
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 /Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0/mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0_jax.py
```

```
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 /Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0/mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0_pytorch.py
```

```
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 /Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0/check_agreement.py
```

```
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 /Users/joshuaeisenhart/Codex-Ratchet/scripts/validate_name_math_correlation.py /Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0
```
