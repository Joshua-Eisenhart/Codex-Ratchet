# BUILD CARD: geo_s6_stacked_flows_hopf_v0

Status: builder packet only. Separate audit required before using this as audit evidence.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Scope:
- Build genuinely new S6 restricted/stacked Hopf-shell leakage receipts only.
- Import and cite S2 `A/F/h/T_eta`, S4 process lessons, S5 v2 exported `A,b`, Matrix64 `Delta_T,O`, and the source placement tables.
- Do not rebuild S2, S4, S5, Matrix64, terrain source locks, or the canonical geometry program.
- Every admitted row names `arrow_type` under the nesting-law receipt.
- Shell coordinate is `z=cos(2 eta)` and leakage is `dz/dt=e_z^T(A r_eta(chi)+b)`.
- S6 leakage integrals are the restricted-mode flux layer; no competing flux object is introduced.
- Terrain actions on `A`, `F`, `h`, and `Phi_ij` are computed only for pure-Hopf lifted rows and marked `undefined_without_mixed_lift` for nonunitary rows.
- `Phi_D=U o E o U o E` and `Phi_I=E o U o E o U` are executed on one shared density/Bloch carrier with computed `g_DI`.

Packet target:
- `system_v6/sims/geo_s6_stacked_flows_hopf_v0/`

Engine roles:
- Julia: carrier-side matrix/signature computation plus Z3 bound contradiction.
- JAX/SymPy: exact symbolic leakage formulas, integrals, placement rows, overlay rows, loop-order gap, and can-fail mutations.
- PyTorch: torch tensor/autograd mirror for load-bearing leakage and loop-order signatures plus SMT controls.

Build gates:
- S6.1 prior receipts are imported by path/hash and not rebuilt.
- S6.2 every map declares RESTRICTED/STACKED mode and arrow type.
- S6.3 every `z_dot` row derives directly from S5 exported `A,b`.
- S6.4 shell classification separates shell leakage from purity/Hopf-foliation leakage.
- S6.5 inner, outer, and shell-average leakage integrals are computed as the S6 flux layer.
- S6.6 `A/F/h/Phi_ij` action status is computed or blocked with `undefined_without_mixed_lift`.
- S6.7 all 16 placements are computed pairings.
- S6.8 Matrix64 is reused, not rebuilt.
- S6.9 `Phi_D`, `Phi_I`, `Delta_DI`, and `g_DI` are executed on one carrier with order controls.
- S6.10 round-trip, consistency, executed mutation, cross-engine fatality, and literal ceiling gates are mandatory.

Out of scope:
- canonical stacked geometry, Axis admission, runtime closure, physics, completed constraint manifold, mixed-state/Uhlmann lift, S2/S4/S5/Matrix64 regeneration.
