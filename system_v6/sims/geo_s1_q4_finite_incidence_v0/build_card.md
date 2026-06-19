# geo_s1_q4_finite_incidence_v0

CLAIM UNDER TEST: the finite-incidence/reconstruction behavior from the committed q=2 and q=3 packets persists over the first non-prime finite field, `GF(4)`, while exposing a stronger projective quotient boundary and a char-2 Frobenius boundary.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

Mode: `julia_canon_plus_jax_diagnostic`; no PyTorch lane because there is no graph/network/autograd claim path.

Read-first anchors:

- `system_v6/sims/geo_s1_q3_finite_incidence_v0/`
- `system_v6/sims/geo_s1_q3_finite_incidence_v0/audit_verdict.md`
- `system_v6/sims/twistor_incidence_finite_packet_v0/`

Acceptance gates:

- G1: derive `PG(3,4)` over `GF(4)`, not by copied constants: `255` nonzero raw vectors, `85` projective point classes, `357` lines, `85` planes, `5` points per line, `21` lines through each point.
- G2: pair-line uniqueness: every unordered point pair is on exactly one line; z3 and cvc5 structural checks over computed counts return `unsat`, and a scrambled-incidence control returns `sat`.
- G3: line-intersection graph invariants are computed: `357` vertices, regular degree `100`, `17850` edges, one component.
- G4: projective quotient ablation fires: raw/projective ratio is `3.0`, strictly stronger than q=3 ratio `2.0` and q=2 ratio `1.0`.
- G5: reconstruction rows are like-for-like with q=2/q=3: recover all point pencils with zero mismatch; report persist/strengthen/weaken honestly.
- G6: char-2 GF(4) boundary is explicit: Frobenius `x -> x^2` is tested as a nontrivial field automorphism that preserves projective incidence and line graph structure.

Required artifacts:

- `geo_s1_q4_finite_incidence_v0_jax.py`
- `geo_s1_q4_finite_incidence_v0_julia.jl`
- `geo_s1_q4_finite_incidence_v0_envelope.py`
- `results/*.json`

Forbidden in builder output:

- No `audit_verdict.md`.
- No git add, commit, or broad staging.
- No promotion, bridge, axis, physics, manifold, GR, or Penrose-validation claim.
