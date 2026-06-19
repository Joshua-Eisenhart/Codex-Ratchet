# S4 build spec prep - operator channel symbolic packet - 2026-06-10

Status: read-lane spec only, not a build. Deliverable target for a future builder: one bounded S4 packet for genuinely new operator-channel geometry receipts only.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not claim canonical operator-family completion, Axis-level admission, engine/runtime closure, terrain-generator closure, or physics.

## Stage anchor

The canonical geometry program puts S4 after S3 density/observable geometry and before S5 terrain generators. S4 scope is: Pauli algebra tables; `D_z`, `D_x`, `R_x`, `R_z` with exact Bloch actions; ellipsoid images `r -> M r + c`; commutators; fixed axes (`system_v6/receipts/geometry_sim_program_canonical_20260610.md:16-21`).

Binding stack rule: Bloch-level operator work must say what the density/Bloch quotient sees and erases, and must not pretend this is the spinor/Hopf foundation (`system_v6/receipts/geometry_sim_program_canonical_20260610.md:5-14`).

## Already computed - cite, do not rebuild

1. Base Pauli matrices, projectors, and operator source line locks exist.
   - `system_v6/sims/source_locked_operator_base_packet/source_locked_operator_base_packet_jax.py:45-61` defines `SX`, `SY`, `SZ`, `P0/P1`, `QP/QM`, and source citations for `Ti/Te/Fi/Fe`.
   - `system_v6/sims/source_locked_operator_base_packet/results/source_locked_operator_base_packet_envelope_results.json:1516-1521` records the source lineages.

2. The four current source-locked operator channel forms exist.
   - `Ti` = z-basis dephasing, `Te` = x-basis dephasing, `Fi` = x-axis unitary rotation, `Fe` = z-axis unitary rotation.
   - Source implementation: `system_v6/sims/source_locked_operator_base_packet/source_locked_operator_base_packet_jax.py:167-221`.
   - Result form table: `system_v6/sims/source_locked_operator_base_packet/results/source_locked_operator_base_packet_envelope_results.json:848-866`.
   - Reuse them as source forms. Do not rebuild the source-lock packet.

3. Sparse numeric commutator/order facts for the four base operators already exist.
   - `system_v6/sims/source_locked_operator_base_packet/results/source_locked_operator_base_packet_envelope_results.json:36-70` stores trace-norm commutator values on `rho_0`.
   - Structural zero explanation is in `system_v6/sims/source_locked_operator_base_packet/audit_verdict.md:51-56`.
   - This is not an exact symbolic commutator table over channel affine maps; it is prior evidence to cite and harden against, not the new S4 output.

4. Matrix64 already computed terrain/operator order gaps.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:11-13` admits the 64-cell chart only as scratch diagnostic.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:28-36` says each row has ordered outputs, `Delta_T_O_matrix_plus_minus`, norms, observables, trajectory, and a fingerprint ladder.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:76-99` adjudicates F7 trajectory distinctness and manual commuting/noncommuting cells.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:135-150` records the post-hardening validator and ceiling. S4 must not rerun matrix64.

5. S1 exact closure has Pauli/Bloch convention pins.
   - `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_envelope.py:38-47` pins `sigma_y_standard`, the Bloch basis, and `r_i = Tr(rho * basis_i)`.
   - `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_envelope.py:108-113` proves the pinned Bloch density quotient symbolically.
   - S4 must import or cite this convention. Do not make a second Bloch-sign convention.

6. Terrain-generator fixed-point/strata evidence exists, but it does not satisfy this S4 channel spec.
   - `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:1025-1135` computes fixed-point and strata checks for S5 terrain channels.
   - `system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json:2957,3018,3079` records `fixed_pass=true` across engines.
   - This can be cited as context only. The new S4 object is the four named base operator channels, not the eight S5 terrain flows.

## Genuinely new S4 work

Build only these new receipts:

1. Exact affine Bloch channel table for `D_z`, `D_x`, `R_x`, `R_z`.
   - Emit exact `M` and `c` for each channel in `r -> M r + c`.
   - The expected class is unital for all four current base channels, so `c=0` should be derived, not assumed.
   - Use symbolic parameters first: `q_z`, `q_x`, `theta_x`, `phi_z`; then include the source-locked pin row `q_z=q_x=3/10`, `theta_x=pi/2`, `phi_z=pi/2`.

2. Exact ellipsoid image receipts.
   - For each channel, derive the image of the Bloch ball under `M`.
   - Emit semi-axis lengths, axis directions, rank, determinant where meaningful, and whether the image is a sphere, spheroid, disk limit, line limit, or point limit.
   - Include boundary parameter cases: `q=0`, `0<q<1`, `q=1`; rotation angles `0`, `pi/2`, `pi`, and generic symbolic angle.

3. Fixed-axis and fixed-point proofs.
   - For each channel, solve `M r + c = r` symbolically under the admissible parameter cases.
   - Separate fixed axis, fixed plane, fixed point set, and full-channel identity cases.
   - For `D_z` and `D_x`, classify the dephasing axis as fixed and transverse components as contracted for `0<q<1`.
   - For `R_x` and `R_z`, classify the rotation axis as fixed and non-axis orbits as non-attracting except special angle identity cases.

4. Basin classification for the named operator channels.
   - For iterated channels, classify convergence sets: dephasing converges to the axis projection for `0<q<1`; full dephasing `q=1` reaches the axis projection in one step; rotations preserve radius and have periodic/dense orbit classes depending on angle.
   - Do not use S5 terrain-attractor language unless explicitly marked as out of scope for this packet.

5. Exact symbolic commutator table.
   - Compute `[M_i, M_j] = M_i M_j - M_j M_i` for all ordered pairs among `D_z`, `D_x`, `R_x`, `R_z`.
   - Also compute affine commutator data for `r -> M r + c`, even if all current `c` values derive to zero.
   - Emit exact symbolic entries, pinned exact entries, zero/nonzero classification, and a structural reason.
   - Include cross-check links to the older numeric sparse table, but do not rely on numeric trace norms as the proof.

6. Quotient-erasure note.
   - State that this packet operates on density/Bloch channels only.
   - It cannot see global phase, spinor path lift, Hopf fiber holonomy, or three-slot bracketing except through cited lower/higher stage boundaries.

## Proposed packet boundary

Suggested sim id: `geo_s4_operator_channel_symbolic_v0`.

Allowed output path for the future build:
`system_v6/sims/geo_s4_operator_channel_symbolic_v0/`

Required files for the future build:
- `build_card.md`
- `geo_s4_operator_channel_symbolic_v0_julia.jl`
- `geo_s4_operator_channel_symbolic_v0_jax.py`
- `geo_s4_operator_channel_symbolic_v0_pytorch.py`
- `geo_s4_operator_channel_symbolic_v0_envelope.py`
- `results/geo_s4_operator_channel_symbolic_v0_{julia,jax,pytorch,envelope}_results.json`
- optional `audit_verdict.md` only after a separate audit lane runs

Do not edit or regenerate the already-computed source-locked operator, S1 exact, terrain-generator, or matrix64 packets.

## Positive ledger

The future build passes only if the envelope proves all of these:

1. `P1_pauli_table_exact`: Pauli multiplication/commutator/anticommutator table is exact and convention-pinned to S1.
2. `P2_affine_channel_table_exact`: every named channel has exact `M,c` under symbolic and pinned parameters.
3. `P3_ellipsoid_image_exact`: every named channel has an exact image classification and boundary-case table.
4. `P4_fixed_sets_exact`: every named channel has exact fixed-axis/fixed-point/fixed-set proofs.
5. `P5_basin_classes_exact`: every named channel has an exact iterated-channel basin/orbit classification.
6. `P6_commutator_table_symbolic`: all 16 ordered channel commutators are exact symbolic receipts with zero/nonzero structural reasons.
7. `P7_prior_reuse_lineage`: result cites source-locked operator forms, S1 convention pins, and matrix64 order-gap prior evidence without rerunning them.
8. `P8_claim_ceiling`: result carries `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Negative controls

The future build must include controls that can fail:

1. Wrong Bloch convention: use standard `sigma_y` where S1 pin requires `-sigma_y_standard`; the convention check must detect the sign mismatch.
2. Wrong basis dephase: replace `D_z` with a y-basis dephase and show the fixed-axis/commutator table changes; cite the existing wrong-basis control as precedent, not proof.
3. Fake nonunital shift: inject a nonzero `c` into one current base channel and require the unital proof or affine commutator check to fail.
4. Rotation-as-contraction error: force `R_x` or `R_z` to shrink the Bloch ball; the ellipsoid/spectrum check must fail.
5. Dephase-as-rotation error: force `D_z` or `D_x` to preserve all radii; the ellipsoid and basin checks must fail for `0<q<1`.
6. Commutator echo error: assert `D_z` commutes with `R_x` under generic parameters; the symbolic commutator check must reject unless a special parameter case makes it true.
7. Numeric-only table error: remove symbolic entries and leave only pinned floating trace norms; the envelope must fail exactness.
8. Terrain leakage error: cite S5 terrain fixed-point rows as satisfying S4 operator basins; the boundary gate must fail.

## Blind list for audit lane

Keep these as audit expectations. A builder may encode them only as generated results from exact derivation, not as hand-entered verdicts.

1. All four current base operator channels are unital in the source-locked packet.
2. `D_z` fixes the z-axis and contracts the x/y plane for `0<q_z<1`.
3. `D_x` fixes the x-axis and contracts the y/z plane for `0<q_x<1`.
4. `R_x` fixes the x-axis and rotates the y/z plane.
5. `R_z` fixes the z-axis and rotates the x/y plane.
6. `D_z` and `D_x` commute as diagonal Bloch contractions.
7. `D_z` commutes with `R_z`; `D_x` commutes with `R_x`.
8. Generic cross-axis dephase/rotation pairs do not commute; special cases must be derived explicitly, such as identity contraction or rotation angles/axes that make the commutator collapse. Full erasure is not generically enough.
9. With pinned `theta_x=phi_z=pi/2`, rotations have finite order four on the transverse plane; this is orbit classification, not attraction.
10. Any nonzero affine shift for these four current base channels is a bug unless explicitly placed in a different future channel family.

## Audit attacks

Audit the future packet against these failure modes:

1. Source echo: result copies strings from `source_locked_operator_base_packet` but does not derive `M,c`, ellipsoids, fixed sets, or commutators.
2. Convention drift: result silently changes S1 Bloch y sign.
3. Numeric promotion: result uses floats or `isclose` as the claim path for symbolic identities.
4. Sparse-table overclaim: result cites the old `rho_0` trace-norm commutator table as if it were a symbolic channel table.
5. Matrix64 conflation: result treats terrain/operator order gaps as the base-operator commutator table.
6. S5 bleed-through: result imports terrain-generator fixed points/basins as S4 operator-channel fixed points/basins.
7. Parameter collapse: result proves only pinned `q=0.3`, `theta=pi/2`, `phi=pi/2` and omits symbolic parameter cases.
8. Boundary omission: result does not classify `q=0`, `q=1`, zero-angle, and identity special cases.
9. Fake basin language: result calls rotation orbits attractors.
10. Claim creep: result promotes the packet beyond `scratch_diagnostic` or says operator-family completion.

## Directive rules binding

1. Build genuinely new S4 receipts only. Cite existing packets for source locks, prior numeric checks, and conventions.
2. Use exact symbolic math for claim-bearing rows. Pinned numeric rows are cross-checks, not the proof.
3. Keep density/Bloch quotient scope explicit. Do not claim spinor/Hopf phase, terrain flow, or engine runtime behavior.
4. Use the interpreter and three-engine validation conventions already used by this repo when the future build is launched.
5. Keep Julia, JAX/SymPy, and PyTorch roles honest. PyTorch may be exact integer/rational tensor mirror or explicitly demoted; it must not masquerade as symbolic CAS.
6. Every result must include `classification`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, source lineage, exactness labels, can-fail controls, and claim ceiling.
7. If symbolic derivation and prior numeric packets disagree, preserve the divergence and mark the packet blocked pending audit. Do not smooth it into agreement.
