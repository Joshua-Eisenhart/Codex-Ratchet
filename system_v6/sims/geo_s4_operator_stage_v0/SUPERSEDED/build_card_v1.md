# geo_s4_operator_stage_v0 build card

Status: builder packet only. Separate audit required before using this as audit evidence.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Scope:
- Build the genuinely new S4 operator-channel geometry receipts from `system_v6/receipts/s4_build_spec_20260610.md`.
- Use the S1 pinned Bloch convention: `bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)` and `r_i=Tr(rho*basis_i)`.
- Cite already-computed source-lock, S1, matrix64, and S5 terrain packets. Do not rebuild them.

Packet target:
- `system_v6/sims/geo_s4_operator_stage_v0/`

Engine roles:
- Julia: carrier-side pinned Pauli/operator semantics, Symbolics formula rows, Julia Z3 proof.
- JAX/SymPy: exact symbolic derivation of affine channel tables, ellipsoid/fixed/basin/commutator receipts, z3/cvc5 proof controls.
- PyTorch: pinned exact tensor mirror and batched commutator table with SMT controls; not a symbolic CAS.

Out of scope:
- Spinor/Hopf path lifts, global phase, Hopf holonomy, terrain-generator basins, S5 fixed-point claims, runtime closure, operator-family completion, Axis admission, physics.
