# BUILD CARD v2 (REBUILD after REJECT AS CLAIMED): geo_s5_terrain_flows_v0

Status: rebuilt builder packet only. Separate audit required before using this as audit evidence. The v1 card is preserved at `SUPERSEDED/build_card_v1.md`; `audit_verdict.md` remains the rejected historical verdict.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Scope:
- Rebuild the S5 one-qubit terrain-generator flow receipts after the rejected v1 extraction bug.
- Primary rows use the source-locked standard Bloch basis `bloch_basis=(sigma_x,sigma_y_standard,sigma_z)` with right-handed active rotations.
- Emit the S1/S4 pinned-y conversion crosswalk `J=diag(1,-1,1)` for rotation-bearing rows. The crosswalk is not the primary table.
- Cite already-computed source locks, terrain-generator sheet rows, Matrix64 applications, and S4 v2 process lessons. Do not rebuild those packets.
- Keep pure Ne separate from weak-dissipator Ne variants.

Packet target:
- `system_v6/sims/geo_s5_terrain_flows_v0/`

Engine roles:
- Julia: carrier-side independent derivation from density-generator forms plus Julia Z3 pinned-entry contradiction proof.
- JAX/SymPy: exact symbolic `A,b`, flow, fixed-point, basin, unitality, purity, and can-fail mutation receipts plus z3/cvc5 pinned-entry contradiction controls.
- PyTorch: pinned tensor/autograd mirror for generator rows, flow samples, non-unitality, basin limits, and SMT controls. PyTorch is not the symbolic CAS.

Build gates:
- V1 affine extraction fixed: derive `A,b` by symbolic expansion/differentiation. Pure `Ne` rows must emit the nonzero `C_+` and `C_-` antisymmetric precession matrices, with validator assertions for both rows.
- V2 round-trip gate: every claimed closed-form flow differentiates back to the exported `A,b`.
- V3 fixed-set consistency: fixed sets are derived from exported `A,b` by kernel/eigen/solve checks. Pure `Ne` fixed set is `span(n)`.
- V4 basin/orbit consistency: limits and nonlimits are tied to exported generators through eigenvalue signs and computed witnesses, not row labels.
- V5 controls: negative controls are executed mutation computations with observed failing values.
- V6 cross-engine fatality: any load-bearing pinned `A,b` row disagreement across Julia/JAX/PyTorch above tolerance fails the envelope.
- S5 ceiling remains: no formal admission, no canonical terrain-family completion, no Axis-level admission, no runtime closure.

Out of scope:
- Spinor phase, Hopf fiber holonomy, S6 terrain/operator/Hopf stacking, Matrix64 closure, induced geometry on survivor sets, completed terrain-family claims, Axis admission, physics.
