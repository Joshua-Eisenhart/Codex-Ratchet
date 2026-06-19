# BLIND Expected Values: `terrain_operator_precedence_64_matrix`

Blind rule observed: I did not read, list, or glob `system_v6/sims/terrain_operator_precedence_64_matrix/`.

Allowed inputs used:
- `/tmp/m64_build_card_20260610.md`
- `system_v6/receipts/matrix64_mine_20260610.md`
- `system_v6/receipts/terrain_operator_map_20260609.md`
- `system_v5/READ ONLY Reference Docs/operator math explicit.md`
- `system_v5/READ ONLY Reference Docs/terrain math.md`
- committed packets: `terrain_generator_sheet_packet`, `source_locked_operator_base_packet`, `mct_dynamic_admissibility_packet_v0`

## 1. Commutation Predictions Per Cell Class

### Source-locked operator axes

| base operator | source form | axis class | predicted commutation rule |
|---|---|---|---|
| `Ti` | `D_z`, Bloch `(lambda1 x, lambda1 y, z)` | z-dephasing | Commutes with z-axis channels/rotations and diagonal-in-z dissipative channels; generically not with x rotations unless degenerate. |
| `Te` | `D_x`, Bloch `(x, lambda2 y, lambda2 z)` | x-dephasing | Commutes with x-axis channels/rotations; generically not with z rotations unless degenerate. |
| `Fi` | `R_x(theta)` | x-rotation | Commutes with x-dephasing and x-axis Hamiltonian flow; generically not with z dephasing/rotation. |
| `Fe` | `R_z(phi)` | z-rotation | Commutes with z-dephasing and z-axis phase-covariant channels; generically not with x dephasing/rotation. |

Derivation/source: `operator math explicit.md:3-4,796-810` says only four intrinsic operators exist and signs are composition order. `terrain_operator_map_20260609.md:43-50` gives the base maps. `terrain_operator_map_20260609.md:56-63` and the committed `source_locked_operator_base_packet` classify `Ti-Te`, `Ti-Fe`, `Te-Fi` as zero controls and `Ti-Fi`, `Te-Fe`, `Fi-Fe` as nonzero; packet lines include known nonzeros at result JSON lines 36-39 and known zeros at 41-44.

### Terrain classes

| terrain class | source generator | `Ti` | `Te` | `Fi` | `Fe` | derivation/source |
|---|---|---:|---:|---:|---:|---|
| `Se/Funnel`, `Se/Cannon` | isotropic Pauli dissipator plus `-i eps[H_L/R,rho]` | `depends` | `depends` | `depends` | `depends` | The dissipator `sum_j D[sigma_j]` is isotropic and should commute with all four Bloch-axis maps, but the Hamiltonian term commutes only when pinned `H0` is aligned with the operator axis or `eps=0`. `H_L=+H0`, `H_R=-H0` at `terrain math.md:56-57`; Se laws at `terrain math.md:76-77`. |
| `Ne/Vortex`, `Ne/Spiral` | pure `-i[H_L/R,rho]` | `depends` | `depends` | `depends` | `depends` | A Hamiltonian flow commutes with x-axis operators iff `H0` is x-aligned, with z-axis operators iff `H0` is z-aligned, otherwise generically not. Sign flip `H_R=-H0` changes orientation, not the axis-commutation class. Source: `terrain math.md:78-79`; sheet signs at `56-64`. |
| `Ni/Pit`, `Ni/Source` | `D[sigma_-]` or `D[sigma_+]` plus `-i eps[H_L/R,rho]` | `commute if z-pinned` | `generically not` | `generically not` | `commute if z-pinned` | The jump term is z-basis/phase-covariant, so it commutes with z dephasing/rotation and not with x dephasing/rotation. The Hamiltonian term preserves that verdict only if `eps=0` or `H0 || z`; otherwise even `Ti/Fe` become generic noncommuters. Source: `terrain math.md:80-81`; committed packet notes Pit/Source direction and H-sign sensitivity at `terrain_generator_sheet_packet` result lines 4722-4728, 4775-4788. |
| `Si/Hill`, `Si/Citadel` | Hamiltonian plus projective dephasing along `m_L/m_R` | `commute if m||z` | `commute if m||x` | `commute if m||x` | `commute if m||z` | The channel is diagonal in the pinned projector frame. It commutes with operator axes matching that frame and generically not otherwise. Source: `terrain math.md:82-83`; projectors at `terrain math.md:89-90`; packet says `omega/K` frame magnitude is pinned-choice, not source-forced, at result lines 4787-4788. |

Signed-cell prediction: for each terrain/base pair, `+` is `Phi_T(O(rho))` and `-` is `O(Phi_T(rho))`; the two signed cells merge exactly when `Delta_{T,O}(rho)=0`. Source: `terrain_operator_map_20260609.md:36-39,104-111,172-175`.

Non-degenerate generic expectation before pins: all `Se`/`Ne` cells and most `Si` cells are not decidable from sources alone because `H0` and `m_L/m_R` are not source-forced. `Ni` has the strongest axis prediction: `Ti/Fe` are the expected commuting controls under a z-preserving Hamiltonian pin; `Te/Fi` are expected noncommuting.

## 2. `n_distinct` Bounds Per Ladder Rung

Let `C` be the number of commuting terrain/base pairs among the 32 unsigned pairs (`8 terrains x 4 base operators`) after builder pins `H0`, `m_L/m_R`, coefficients, finite time, and `rho`.

| rung | predicted bound/status | reason/source |
|---|---|---|
| `F0_address` | exactly `64` | Address fingerprint is raw enumeration, not behavior. Mine receipt defines `F0_address` at `matrix64_mine_20260610.md:220-225`; build card pins 64 cells. |
| `F1_final_density` | `1..64`, not source-predictable; existing related runtime object had `n_distinct=16`, but this chart object need not reproduce it | Final density can collapse commuting pairs, fixed states, eigenstates, density-blind phase/sheet differences, and tolerance-rounded near-equalities. The 16-count is explicitly a different runtime object, not this matrix: `matrix64_mine_20260610.md:271-291`. |
| `F2_order_pair` | lower-bound formula after pins: `64 - C`; cannot honestly give a numeric bound before pins | A commuting signed pair has identical ordered outputs and merges `2 -> 1`; a noncommuting pair keeps both signs distinct. `C` is pin-dependent from section 1. Source: `matrix64_mine_20260610.md:220` and `terrain_operator_map_20260609.md:108-111`. |
| `F3_delta` | same lower-bound formula: `64 - C`; stronger than `F1` for Axis-6, but same sign-merge logic as `F2` | `Delta` is zero exactly on commuting cells and nonzero on generic noncommuting cells. Source: `matrix64_mine_20260610.md:220`; `terrain_operator_map_20260609.md:108`. |
| `F4_observable` | can exceed `F1` if observables separate final-density collisions; can be less than or equal to `F2/F3` if chosen observables are coarse | `F4` adds `Tr(O rho)` and terrain observables over time, so it is not bounded above by final-density count except by 64. Source: `matrix64_mine_20260610.md:221`. |
| `F5_entropy_purity` | can exceed `F1` only where entropy/purity/unitality columns see differences not visible in rounded final density; cannot prove Axis-6 distinctness alone | Scalar thermodynamic invariants are coarser than full density/order-pair data. Source: `matrix64_mine_20260610.md:222`. |
| `F6_spinor_sheet_loop` | can exceed `F1`; expected to recover density-blind phase/sheet/loop distinctions | Density erases fiber phase, while sheet sign and loop path are separate fields. Source: `matrix64_mine_20260610.md:223`; `terrain math.md:30-49,56-64`; terrain packet line refs at result lines 4775-4788. |
| `F7_trajectory` | can exceed `F1`; likely strongest behavior rung before orthogonality because it records intermediate order, not just final output | Source: `matrix64_mine_20260610.md:224`. |
| `F8_axis_orthogonality` | can exceed `F1`; expected to separate Axis-4 and Axis-6 if both are implemented as actual DOFs | Source: `matrix64_mine_20260610.md:225`; `working_math_scaffold_20260609.md:179`; `terrain_operator_map_20260609.md:104,133,172-175`. |

Rungs that can exceed `F1`: `F2` through `F8`, because each adds fields that can split final-density collisions. `F0` can numerically exceed `F1`, but it is enumeration-only and carries no behavior claim. Rungs that cannot be honestly claimed to exceed `F1` before builder pins and runs: all behavior rungs, because `rho`, parameter choices, and tolerance can collapse them.

## 3. Erased-Precedence Control

Prediction:
- Under normal `F2/F3`, each signed pair `(T,O+)` vs `(T,O-)` merges iff `Delta_{T,O}=0`.
- Under erased precedence, every one of the 32 signed pairs must merge, because the control computes or records only one order for each terrain/base pair.
- The required reduction under `F2/F3` is therefore from `64 - C` normal classes to at most `32` erased-sign classes, before any additional terrain/operator coincidences.

For `F1_final_density`, fewer new merges are guaranteed:
- Pairs with `Delta=0` were already merged before sign erasure.
- Noncommuting pairs can also already coincide under `F1` if the pinned `rho` is a fixed point/eigenstate, if final density is a coarse quotient, or if tolerance rounds the difference away.
- Therefore the predicted new `F1` merges are `<= 32 - C`, not exactly `32 - C`.

Source: signed polarity semantics at `terrain_operator_map_20260609.md:36-39`; erased-axis/commuting control at `terrain_operator_map_20260609.md:108-111`; build card G4 requires signed-pair merging under erased sign.

## 4. Orthogonality Prediction (`F8`)

Axis-4 and Axis-6 should move independent observables:

| varied DOF | fixed DOF | predicted independent observable | source |
|---|---|---|---|
| Axis-4 loop/order class | Axis-6 precedence fixed | Deductive-vs-inductive order witness: `g_DI = ||D(I(rho)) - I(D(rho))||_1`, entropy/coherent-info differences, Landauer-style terms where the MCT packet implements them. | `working_math_scaffold_20260609.md:175-179` defines Axis4 as deductive-vs-inductive order and Axis6 as operator-first vs terrain-first precedence. |
| Axis-6 terrain/operator precedence | Axis-4 loop/order fixed | `Delta_{T,O}(rho)=Phi_T(O(rho))-O(Phi_T(rho))`, Frobenius/trace norms, commuting/erased controls. | `terrain_operator_map_20260609.md:104,108,133,172-175` separates Axis-6 from loop/order class. |

Expected `F8` pass shape: varying Axis-4 with fixed Axis-6 changes loop/order observables without changing the selected terrain/operator precedence sign; varying Axis-6 with fixed Axis-4 changes `Delta_{T,O}`/order-pair observables without changing deductive-vs-inductive loop class. A result that uses one generic "order" flag for both should fail `F8`.

## 5. `FP_TOL` Sweep Prediction

Qualitative curve:
- At machine-epsilon-scale tolerances, commuting cells cluster at zero gap. The source-locked operator packet has zero controls around `1.6e-16` to `2.3e-16` for `Te-Fi`, `Ti-Fe`, `Ti-Te` (`source_locked_operator_base_packet` result lines 41-44).
- Genuine noncommuting cells should remain split until tolerance approaches the measured gap scale, not until `1e-12`/`1e-9`.
- The MCT packet gives scale anchors: `max_order_gap_noncommuting` is `0.101200738233...` across engines and a noncommuting flip partner is `0.113516789645...`; committed lines include `mct_dynamic_admissibility_packet_v0` result lines 684-689 and 198-199.
- Therefore the `n_distinct` curve should show an early cliff only for numerical-zero commuting pairs near machine epsilon, then remain stable over ordinary tolerances, then lose genuine noncommuting distinctions as `FP_TOL` approaches roughly `1e-1`.

Predicted failure signs:
- If noncommuting distinctions disappear at `1e-6` or `1e-4`, the implementation is underinstrumented or using a too-coarse fingerprint.
- If commuting controls remain split above `1e-12`, either the supposed commute is not actually source/pin commuting or the numeric path is unstable.
- If the curve has no change near the `0.1` gap scale, the sweep may not be tied to the actual `Delta`/norm fields.

## 6. Not Predictable Before Builder Pins

These must stay `depends_on_builder_pin`:

- Exact numeric `C` in `64 - C` for `F2/F3`.
- Exact commute table for `Se` and `Ne`, because `H0` direction and `eps`/weak-dissipator policy decide whether their Hamiltonian parts align with x or z operator axes. Source: `terrain math.md:76-79`; terrain packet notes weak Ne variants are pinned-choice at result lines 4740-4754.
- Exact commute table for `Ni` z-axis controls if the Hamiltonian part has nonzero non-z component. Source: `terrain math.md:80-81`.
- Exact commute table for `Si`, because `m_L/m_R`, projector frames, and `omega/kappa` pin the active axis. Source: `terrain math.md:82-83`; packet result lines 4787-4788.
- Whether `F1_final_density` reproduces, exceeds, or falls below the related `n_distinct=16` runtime count. This chart object is not the runtime hexagram object. Source: `matrix64_mine_20260610.md:271-291`.
- Exact `F4/F5` splits, because selected observables, entropy/purity columns, and pinned state determine scalar collisions.
- Exact `F6` splits, because phase/holonomy/sheet/chirality probes must be implemented and pinned.
- Exact `F7` splits, because the trajectory/stroke trace and state sweep are not source-forced.
- Exact `F8` count, because it requires a concrete Axis-4 variation protocol and a concrete Axis-6 variation protocol on the same carrier.
- Exact tolerance cliff positions for this matrix. The MCT packet gives `0.101/0.114` scale anchors, but the actual matrix gaps depend on the chosen terrain finite-time maps, coefficients, `rho`, and state sweep.

Bottom line: sources predict the sign-merge law and axis-class logic, not a single numeric `n_distinct` table. Numeric claims become valid only after the builder pins `rho`, `H0`, `m_L/m_R`, coefficients, finite-time terrain map, state sweep, observables, and `FP_TOL`.
