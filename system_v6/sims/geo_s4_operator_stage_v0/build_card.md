# geo_s4_operator_stage_v0 build card v2

Status: rebuild after `REJECT AS CLAIMED`. Builder packet only. Separate audit required before using this as audit evidence.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Scope:
- Build the genuinely new S4 operator-channel geometry receipts from `system_v6/receipts/s4_build_spec_20260610.md`.
- Primary affine and commutator rows use the source-locked/blind standard Bloch basis `bloch_basis=(sigma_x,sigma_y_standard,sigma_z)` with right-handed active rotations.
- Emit the S1 pinned-y conversion layer `J=diag(1,-1,1)` and the converted pinned-basis rows as a crosswalk, not as the primary blind-match table.
- Cite already-computed source-lock, S1, matrix64, and S5 terrain packets. Do not rebuild them.
- Preserve `audit_verdict.md` untouched.
- Preserve the v1 build card under `SUPERSEDED/`.

Packet target:
- `system_v6/sims/geo_s4_operator_stage_v0/`

Engine roles:
- Julia: carrier-side independent density/channel derivation from Kraus/unitary forms, Symbolics row extraction, Julia Z3 pinned-entry contradiction proof.
- JAX/SymPy: exact symbolic derivation of affine channel tables, ellipsoid/fixed/iterated-basin/commutator receipts, z3/cvc5 pinned-entry contradiction controls.
- PyTorch: source-locked pinned-parameter tensor mirror and batched commutator table with SMT controls; not a symbolic CAS.

Rebuild gates:
- V1 rotation convention: source-locked/right-handed active standard rows are primary; S1 pinned-y rows are emitted through the explicit `J M J` conversion layer.
- V2 basins: basin/orbit receipts carry iterated formulas and computed limit/non-limit receipts per channel.
- V3 controls: negative controls are executed mutation receipts with failing values, not declarative booleans.
- V4 Julia: Julia derives rows from density/channel forms instead of only writing formula rows.
- V5 SMT honesty: solver checks are labeled as pinned-entry contradiction checks, not full symbolic commutator-table proofs.

Out of scope:
- Spinor/Hopf path lifts, global phase, Hopf holonomy, terrain-generator basins, S5 fixed-point claims, runtime closure, operator-family completion, Axis admission, physics.
