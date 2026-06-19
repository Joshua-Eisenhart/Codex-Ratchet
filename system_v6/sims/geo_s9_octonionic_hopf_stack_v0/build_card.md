# BUILD CARD: geo_s9_octonionic_hopf_stack_v0

Object: the third Hopf fibration `S7 -> S15 -> S8` on the three-qubit carrier `C^8 ~= O^2`.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Mode: `julia_canon_plus_jax_diagnostic`. Julia is the carrier-side semantic owner for the octonion multiplication convention through `Octonions.jl` and `Z3.jl`; the repo `jax` lane is an exact Python sidecar using `sympy`, `qutip`, `z3`, and `cvc5`. PyTorch is excluded because this packet has no graph, network, or autograd claim path.

## Read-First Inputs

- Available committed quaternionic template evidence: `system_v6/sims/geo_s9_quaternionic_hopf_stack_v0/audit_verdict.md` plus its Julia/Python/envelope legs. There is no committed `build_card.md` for that packet in this checkout.
- Three-qubit anchor: `system_v6/sims/geo_s1_three_qubit_floor_exact_v0/build_card.md`, `audit_verdict.md`, and result envelope.
- Nonassociativity anchor: `system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json` and Julia mirror.
- Sedenion boundary anchor: `system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_envelope_results.json` and Julia leg.

## Claim Under Test

The normalized three-qubit state vector `psi in C^8` is `S15`. With the pinned right-`C_{e1}` coordinate convention on `O`, split `psi=(z0,...,z7)` into `(o1,o2) in O^2` and compute

```text
H_O(o1,o2) = (2*o1*conj(o2), |o1|^2 - |o2|^2) in O x R ~= R9.
```

Rows derive, rather than assert, that the image lies on `S8`, that a pole fiber is `S7` of unit octonions, and that this fiber is not a principal Lie-group fiber. Unit octonions form a Moufang loop, not a group; the packet must compute one nonassociative reassociation witness and a positive Moufang identity row with a flipped-table negative control.

## Required Rows

1. `O1_map`: pinned `C^8 ~= O^2` convention, image on `S8`, pole fiber `S7`, and generic right-action non-invariance boundary.
2. `O2_moufang_nonassoc`: associator witness `(e1,e2,e4)`, quaternion/repeated-input collapse controls, finite Moufang identity SMT with erased/flip control, and explicit `N01` label.
3. `O3_qit`: GHZ, W, full product states, and biseparable states. Emit octonionic base points, `tau`, and the `A|BC` one-tangle. State the honest finding: this map is a chosen `o1,o2` / `A|BC` decomposition readout and does not determine genuine tripartite `tau`.
4. `O4_no_connection`: state the no-principal-connection boundary. Compute the Spin dimensions `dim Spin(9)=36`, `dim Spin(8)=28`, `dim Spin(7)=21`, so `Spin(9)/Spin(8)=S8` and `Spin(9)/Spin(7)=S15` have the expected dimensions. Do not emit a Chern row.
5. `O5_foliation`: `|o1|=cos eta`, generic leaf `S7_{cos eta} x S7_{sin eta}`, exact shell volume, exact integral to `Vol(S15)=pi^8/2520`, and `r=|o1|^2 ~ Beta(4,4)`.
6. `O6_adams_boundary`: theorem-backed four-rung termination plus a recomputed sedenion zero-divisor boundary. Under the committed Cayley-Dickson convention, record honestly that `(e1+e10)(e4+e13)` is nonzero, while the committed same-class zero witness `(e1+e10)(e5+e14)=0` remains zero.

## Controls

- Product-state locus control.
- Bracketing-shuffle / reassociation control.
- Wrong-convention sign or coordinate flip control.
- Degenerate foliation endpoint control.
- `z3` and `cvc5` on the Moufang finite identity, with flipped-table erased control.
- Solver/CAS/package versions recorded.
- One-to-one `tool_calls` for claim-path tools.

## Acceptance

Fresh Julia leg exits 0. Fresh Python exact leg exits 0. Fresh envelope exits 0. Validator returns `ok:true` for the declared mode with source-backed checks. No `audit_verdict.md`, no `git add`, and no commit.
