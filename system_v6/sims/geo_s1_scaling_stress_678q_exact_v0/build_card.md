# Build Card: geo_s1_scaling_stress_678q_exact_v0

Builder lane packet for the 6Q/7Q/8Q scaling, stress, and boundary regime.

Claim: the exact S1 qubit-ladder machinery survives serious dimensional growth for `n in {6,7,8}`:

- `C^(2^n)`
- `S^(2^(n+1)-1)`
- `CP^(2^n - 1)`
- density real dimension `4^n - 1`, namely `4095`, `16383`, `65535`
- `Cl_(2n)` on `C^(2^n)`
- `gamma_(2n+1)` split `32+32`, `64+64`, `128+128`
- max pairwise anticommuting Hermitian-unitary family `2n+1`, namely `13`, `15`, `17`

These are scaling rungs only. They are not new minimum claims. The 8Q rung is the finite overbuild boundary for this directive.

Binding directive copied into this packet:

- `directive_addendum.md`

Acceptance target:

- three-engine lane receipts with identical PIN and `source_sha256`
- per-rung `F01`, `N01`, and `T01` receipts complete
- exact constructive Clifford/stabilizer families
- finite exhaustive Pauli-string checks where feasible
- representation-bound theorem receipt proven once and instantiated per rung
- resource-bound rows classified as `diagnostic_float_nonclaim`
- normal three-engine validator with `--require-pytorch --strict-source-backed`
- packet-local exact-strength validator
- classification ceiling preserved: `scratch_diagnostic`, `promotion_allowed=false`
