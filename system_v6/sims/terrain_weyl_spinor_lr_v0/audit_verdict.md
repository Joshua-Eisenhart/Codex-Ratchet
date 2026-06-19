# audit_verdict.md -- terrain_weyl_spinor_lr_v0

Auditor: codex1 cross-backend audit
Date: 2026-06-11
Scope: fresh read-only audit of `terrain_weyl_spinor_lr_v0`, except this verdict file.
Route truth: partial Wizard v4.2 sim-mode audit. Three Codex-native sidecar subagents completed read-only lanes for source/path evidence, schema/tool evidence, and mirror residual recomputation. No child subsubagent hierarchy or full v4.2 council topology is claimed.

## Claim And Ceiling

Claim under audit: the owner nesting rung says committed S5 terrain generators are lifted to Weyl-spinor-level dynamics, L/R labels are chirality labels, and the lifted/signed rows should answer the committed terrain-sweep anti-collapse caveat for two indistinguishable pairs.

Accepted public status label: exists, with result evidence already present. I did not rerun packet CLIs because they write repo result files outside the one-file audit allowance.

Accepted ceiling: scratch diagnostic only. No formal admission, no engine admission, no native all-three runtime claim, no native JAX claim, no PyTorch graph/autograd claim, and no terrain-on-spinor-on-shell three-level nest.

Verdict: PARTIAL ACCEPT WITH NAMED CAVEATS. The lift/projection and quotient rows are genuine at the calibrated bar. The load-bearing exact mirror-pair claim is refuted for all four families. The lifted/signed rows do separate the two sweep-caveat pairs, but as signed/time-direction diagnostics, not as exact sigma_y mirror equivalence.

## Fresh Checks Run

- Read authority/process docs and calibration: `AGENTS.md`, `CODEX.md`, `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`, `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`, `system_v5/docs/LEGO_SIM_CONTRACT.md`, and `system_v6/receipts/audit_bar_calibration_20260610.md`.
- Read packet sources/results: `terrain_weyl_spinor_lr_v0.py`, `terrain_weyl_spinor_lr_v0_julia.jl`, `terrain_weyl_spinor_lr_v0_envelope.py`, `validate_terrain_weyl_spinor_lr_v0.py`, and all four result JSONs.
- Scratch recomputation from JSON only, no repo writes: direct SymPy recompute of `A_R - M A_L M`, `M=diag(-1,1,-1)`, for all four committed S5 pairs.
- Scratch extraction of lift/projection, quotient, chirality, wrong-mirror, schema, lineage, tool, validator, and prior sweep rows from committed JSONs.
- Sidecar checks: source/path lane, schema/tool lane, and independent mirror-recompute lane all returned usable read-only receipts.

## Q1 -- The Lift Is Genuine

Verdict: PASS, with convention caveat.

Quoted source: `terrain_weyl_spinor_lr_v0.py:4-6` says the packet consumes committed S5 affine Bloch generators by hash and lifts them to one quantum-jump unraveling; it also says the unraveling is a convention and the ensemble density flow is load-bearing.

The code pins the lift rows in `native_lift_spec`; for example `Se_Funnel_L` has `hamiltonian_coeff = 1/5`, Pauli jumps, and chirality `L` at `terrain_weyl_spinor_lr_v0.py:248-253`. Projection uses finite Liouvillian evolution and Bloch readout at `terrain_weyl_spinor_lr_v0.py:286-328`.

Recomputed/checked result evidence:

- S5 parent result hash is `8c5474786973f067e55c0200392c1a27cbe8bf5d71cfd632b507d066b6cc9b1e`, matching the expected committed hash in lineage.
- `max_native_projection_residual = 6.106226635438361e-16`.
- `Se_Funnel_L` round-trip at `r0=[0.2,-0.4,1/3]`, `t=1.0`: lift projection `[0.1584318236418265, -0.177437058221172, 0.07891576312830834]`; committed affine `[0.1584318236418265, -0.1774370582211721, 0.07891576312830847]`; residual `1.3877787807814457e-16`.
- The 4/25 anchor passes: `bloch_angular_frequency_squared = "4/25"`, computed as `4*(1/5)^2`, not read as a literal upstream field.

Named caveat: the no-jump spinor path is not unique. The packet correctly labels this as an unraveling choice; the density/Lindblad projection is the invariant row.

## Q2 -- Mirror Pairing Row

Verdict: FAIL for the load-bearing exact mirror-pair claim. No pair is exact under `A_R = M A_L M`, although all `b` residuals are zero.

Hand recomputation from committed S5 matrices:

- `Ne_Vortex_L` has antisymmetric entries `+/- 2*sqrt(3)/3`; `Ne_Spiral_R` is sign-reversed. With `M=diag(-1,1,-1)`, residual:

```text
[[0, 0, -4*sqrt(3)/3],
 [0, 0, 0],
 [4*sqrt(3)/3, 0, 0]]
max_abs = 2.309401076758503
```

- `Se_Funnel_L` has `-4/5 I` plus antisymmetric entries `+/- 2*sqrt(3)/15`; `Se_Cannon_R` is sign-reversed. Residual:

```text
[[0, 0, -4*sqrt(3)/15],
 [0, 0, 0],
 [4*sqrt(3)/15, 0, 0]]
max_abs = 0.4618802153517006
```

All four family residuals:

| Family | Pair | sigma_y exact | max residual |
|---|---|---:|---:|
| Se | `Se_Funnel_L` / `Se_Cannon_R` | false | 0.4618802153517006 |
| Ne | `Ne_Vortex_L` / `Ne_Spiral_R` | false | 2.309401076758503 |
| Ni | `Ni_Pit_L` / `Ni_Source_R` | false | 0.4618802153517006 |
| Si | `Si_Hill_L` / `Si_Citadel_R` | false | 0.4 |

No smoothing found: the Q2 path is pairwise symbolic residual computation. The envelope's aggregate `max_sigma_y_abs_residual` is only a summary and does not hide per-pair failures.

Mechanism: Julia independently identifies the cause for the main H0 rows: `H0=(sigma_x+sigma_y+sigma_z)/sqrt(3)` is not sigma_y-odd because it contains the `sigma_y` component. Julia `QuantumOptics` reports `sigma_y_H0_sigma_y_plus_H0_norm = 1.6329931618554523`, while the boundary `Hxz=(sigma_x+sigma_z)/sqrt(2)` row has residual `0.0`.

## Q3 -- Separator Question

Verdict: SEPARATION EARNED at the lifted/signed diagnostic level; the prior terrain sweep itself left the two pairs indistinguishable on its declared leakage/survival/gap columns.

Prior sweep caveat from `ratchet_s6_terrain_sweep_v0`:

- `Ne_Spiral_R` / `Ne_Vortex_L`: indistinguishable on `leakage_class=cross_shell`, `survives_conditioning=false`, `order_gap_norm_squared=4`, `order_gap_zero_for_all_theta=false`, `s6_class_name_applied=cross_shell`.
- `Se_Cannon_R` / `Se_Funnel_L`: indistinguishable on `leakage_class=cross_shell`, `survives_conditioning=false`, `order_gap_norm_squared=4/25`, `order_gap_zero_for_all_theta=false`, `s6_class_name_applied=leave_foliation`.

The new packet separates exactly those pairs in the signed/time rows:

- `Ne_Vortex_L` / `Ne_Spiral_R` gamma5-odd readout evolves differently: at `t=1.0`, `gamma5_odd_sigma_z_L_minus_R = -0.19389884046899225` with mirror residual `0.5876324020730674`; at `t=1.5`, mirror residual `0.7075528876801579`.
- `Se_Funnel_L` / `Se_Cannon_R`: at `t=1.0`, `gamma5_odd_sigma_z_L_minus_R = 0.20769927484846995` with mirror residual `0.057890100600198224`; at `t=1.5`, mirror residual `0.05330407545278799`.

Named caveat: this is not a rescue of exact mirror-pairing. It answers the anti-collapse caveat by adding signed/orientation-sensitive lifted rows.

## Q4 -- Quotient-Erasure Row

Verdict: PASS.

For `Ne_Vortex_L`, the 2pi spinor sign flip is real on the lift and erased downstairs:

- `spinor_distance_to_initial = 1.9999999999999998`.
- `spinor_distance_to_negative_initial = 4.643631984240675e-16`.
- `density_return_gap_norm = 5.424783917482861e-16`.
- `erased_by_bloch_density_quotient = true`.

The phase row also erases: phase spinor distance `1.4142135623730951`, density gap `7.117297287638725e-18`.

The chirality-blind control is exactly zero across all sampled times: `max_blind_abs_signal = 0.0`.

The gamma5-odd readout is not mirror-exact over time for the real committed pairs, which is the separator signal. At `t=0` the mirror residual is zero because the initial right vector is chosen as `M r_L`; after evolution it departs.

## Q5 -- Wrong-Mirror Control

Verdict: PASS; the control fires.

The packet's wrong sigma_x mirror control on the Se pair reports nonzero residuals:

```text
t=0.25 -> 0.037207193434150077
t=0.5  -> 0.05972795852697402
t=1.0  -> 0.0760891093216215
t=1.5  -> 0.07153621636130336
```

The exact matrix-level wrong sigma_x row also fails for all families, with the same max classes as the sigma_y residual row. This is a can-fail control, not decorative.

Named caveat: the "where sigma_y is exact" precedent does not hold for the committed H0 terrain pairs here; Julia shows sigma_y is exact only for the Hxz boundary row, not H0.

## Q6 -- Schema, Tools, Lineage, And Standard

Verdict: PASS WITH SCHEMA-MODE CAVEAT.

Passes:

- Envelope `schema_version = three_engine_sim_result_v1`.
- Classification/ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Existing packet validator result: `ok=true`, `errors=[]`, checked python, Julia, and envelope paths.
- Parent lineage hashes are present for S5, S1, S2/S5, and nonassoc parents. S5 consumed input hash matches the committed result hash exactly.
- Shape-only repair receipt is present: `computed_subtree_hashes.kind = shape_only_repair_hash_receipt`, `fresh_full_rerun = true`, and per-subtree hashes cover python mirror/lift/anchors/quotient/chirality/SMT/controls and Julia mirror/QuantumOptics/Grassmann/Z3 rows.
- Julia leg is real and load-bearing: `QuantumOptics`, `Grassmann`, and `Z3` are recorded with load-bearing reasons and versions; capability receipts pass.
- z3/cvc5 mirror-residual identity controls are bound to computed residuals: nonzero residual query returns SAT; forced exactness returns UNSAT in both solvers.
- One-to-one tool calls are present for `sympy`, `scipy.linalg.expm`, `z3`, `cvc5`, `QuantumOptics`, `Grassmann`, and `Z3.jl`.
- Versions recorded: Python tool manifest includes cvc5 `1.3.3`, scipy `1.17.1`, sympy `1.14.0`, z3 `4.16.0.0`; Julia tool manifest includes QuantumOptics `1.2.6`, Grassmann `0.8.44`, Z3 `1.0.4`.
- Python seeds recorded as deterministic with `random_seed = null`.
- No fixture wording found in claim-bearing rows; the packet repeatedly labels itself scratch diagnostic and convention-bound.

Schema-mode caveat:

- The envelope has `engine_contract.mode = julia_canon_plus_python_exact_diagnostic`.
- The packet validator checks `engine_contract.mode`.
- There is no top-level `mode` field in the envelope. If the repaired fork standard requires `mode` as a top-level field, this packet fails that exact schema-shape expectation despite the local validator passing.

Other caveats:

- `engines.jax` is a scoped Python exact diagnostic lane; no native JAX package runtime is claimed.
- `pytorch` is omitted by design; no PyTorch graph/network/autograd claim is earned.
- Some parent lineage summary fields are null or empty (`s5_engine_result_hashes`, `s5_quotient_survival`, `s5_result_hash_from_mode_sweep_anchor`, `s1_double_cover_reference`), although consumed input hashes are present.

## Q7 -- Closure

Earned:

- The committed S5 `A,b` generator rows are consumed by hash.
- Each committed generator has a pinned spinor/density lift convention; native L/R sheet rows project back to the committed Bloch trajectories on exact rows, with the Se_Funnel_L 4/25 anchor passing.
- The L/R chirality reading is supported as Hamiltonian-sign/native-sheet labeling for Se, Ne, and Ni at the lift/projection level.
- The sweep's two indistinguishable anti-collapse pairs are separated by lifted signed/time rows.
- The 2pi sign flip is real upstairs and erased by the density/Bloch quotient.
- The chirality-blind control is exactly zero.
- Julia capability rows with QuantumOptics, Grassmann, and Z3.jl are real and load-bearing for this scratch diagnostic.

Not earned:

- Exact sigma_y mirror-pairing of committed S5 matrices. Refuted for Se, Ne, Ni, and Si.
- A clean all-eight exact L/R chirality theorem. `Si` remains frame-mismatched: committed rows use z/x dephasing frames and do not fit the H0 sheet override as committed dynamics.
- Top-level `mode` field compliance, if that is required by the repaired schema fork.
- Three-level nesting: no terrain-on-spinor-on-SHELL object yet.
- Formal engine admission, canonical status, native all-three runtime, native JAX, or PyTorch graph/autograd evidence.

Final verdict: PARTIAL ACCEPT / MIRROR CLAIM REFUTED. Keep the packet as a scratch diagnostic that genuinely lifts committed terrain flows and answers the separator caveat with signed spinor-level rows, but do not cite it as proving exact L/R mirror-pairing or as completing the next nesting rung.

