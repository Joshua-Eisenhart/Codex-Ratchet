# geo_s5_terrain_flows_v0 build card

Status: builder packet only. Separate audit required before using this as audit evidence.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Scope:
- Build the genuinely new S5 one-qubit terrain-generator flow receipts from `system_v6/receipts/s5_build_spec_20260610.md`.
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
- S5.1 source lineage: cite sources and prior packets without rebuilding already-computed terrain sheet, Matrix64, S4, or S1 results.
- S5.2 exact generator table: all eight terrain rows emit symbolic `A,b` and pinned `A,b`.
- S5.3 exact flow rows: every row carries an honest exact flow representation and pinned consistency check.
- S5.4 all-time CPTP boundary: GKSL structure is the proof path; sampled Choi checks are regression fixtures only.
- S5.5 fixed points and basins: fixed-point solves stay separate from limit, basin, slice, and non-limit orbit receipts.
- S5.6 pure Hamiltonian purity: pure Ne preserves Bloch radius and spectrum; weak-Ne controls fail purity preservation.
- S5.7 non-unitality: Ni rows have `X(I) != 0` and finite-time identity displacement; scoped non-Ni rows are unital.
- S5.8 controls: negative controls are executed mutations with observed failing values.
- S5.9 quotient boundary: one-qubit density/Bloch quotient only.
- S5.10 claim ceiling: no formal admission, no canonical terrain-family completion, no Axis-level admission, no runtime closure.

Out of scope:
- Spinor phase, Hopf fiber holonomy, S6 terrain/operator/Hopf stacking, Matrix64 closure, induced geometry on survivor sets, completed terrain-family claims, Axis admission, physics.
