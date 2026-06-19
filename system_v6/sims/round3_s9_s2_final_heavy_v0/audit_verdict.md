# Audit verdict - round3_s9_s2_final_heavy_v0

Bottom line: VERDICT `GENUINE-WITH-CAVEATS`. This packet closes the last registered round-3 heavy rows for the bounded registry space: `S9.R3.5_path_ordered_loop_neighbor` is excluded only under the pinned path-ordered transport convention, and `S2.R3.5_boundary_conditioning_variant` is a valid finite-cover family under the canonical distinct nonboundary fixed-leaf disintegration rule. No co-survivors are minted here. Ceiling remains `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

Do not cite this as global S2 or S9 uniqueness, convention-independent S9 exclusion, arbitrary S2 measurable conditioning, formal admission, bridge/axis/physics evidence, or global stack uniqueness.

## Verdict

- Repo vocabulary: `GENUINE-WITH-CAVEATS`.
- Classification: `scratch_diagnostic`.
- Engine mode: `all_three_final_heavy_symbolic_transport`.
- Registered rows covered: exactly `S9.R3.5_path_ordered_loop_neighbor` and `S2.R3.5_boundary_conditioning_variant`.
- Builder boundary: before this audit file was written, `audit_verdict.md` was absent and the envelope gate `no_builder_audit_verdict=true`; builder prose stayed in `builder_self_assessment.md`.
- Read-only boundary: I did not run lane entrypoints or the packet-local validator in place because they rewrite result JSONs. I reran read-only generic validators and mirrored the packet-local assertions in a no-write scratch check.

## Named caveats

- C1 - S9 pin-relative only: the S9 exclusion is `excluded-under-pinned-path-ordered-transport-convention`, not an intrinsic kill. It is reopenable if the leaf-by-leaf transport convention or loop calibration changes.
- C2 - S9 has two active pin families: the light pass used the pinned S2/S9 `phi` holonomy convention for `S9.R3.1` through `S9.R3.4`; this heavy packet adds the pinned path-ordered transport convention for `S9.R3.5`. The heavy pin is not merely the same pin restated.
- C3 - SMT depth: z3, cvc5, and Julia Z3 bind computed finite witness values with UNSAT positives and SAT erased flips. They are useful polarity guards, but they do not independently derive the quaternion transport formula or the S2 disintegration law.
- C4 - One SMT witness label is not the citable S9 row witness: the solver rows name a `pi/120` gap from the `eta=pi/4` finite binding, while the citable first S9 witness is the packet table's `eta=pi/6` gap `pi/160` with candidate commutator value `4*sin(41*pi/160)**4`.
- C5 - Tool honesty: `sympy` carries the exact S9/S2 symbolic rows; `diffrax` and Julia `DifferentialEquations` are load-bearing only as one-generator ODE controls, not as the exact two-loop symbolic proof; `torch.func` is a numeric mirror/sensitivity lane for S9, not the arbiter; `build_three_engine_envelope` is load-bearing envelope construction, not math evidence.
- C6 - S2 scope: the accepted cover rule is finite, distinct, nonboundary fixed-eta Hopf leaves with weights proportional to `sin(2*eta)`. Boundary leaves, duplicate leaves, transverse/non-leaf conditioning, finite-k positive-measure conditioning, and arbitrary measurable unions remain fenced.
- C7 - Closure scope: round-3 closure is only for the registered finite alternative spaces in `round3_discriminator_registry_20260611.md` and the consolidated heavy queue. Reopenable convention pins and unenumerated subvariants remain outside the closure sentence.

## Transport reality

Accepted.

The packet computes path-ordered products as exact quaternion exponentials for loop families `(x0,x1)->i` and `(x0,x2)->j`. For `q_i(theta)=cos(theta)+i sin(theta)` and `q_j(theta)=cos(theta)+j sin(theta)`, the squared commutator gap is:

```text
||q_i q_j - q_j q_i||^2 = 4*sin(theta)^4
```

Independent recomputation matched the citable row:

| Check | Value |
| --- | --- |
| Anchor leaf | `eta=pi/6` |
| Anchor theta | `pi/4` |
| Anchor commutator gap squared | `1` |
| Candidate theta | `41*pi/160` |
| Candidate commutator gap squared | `4*sin(41*pi/160)**4` |
| Theta gap | `pi/160` |

The deliberate gauge-reparameterization alias survives: `1 - 2*sin(eta)^2` simplifies to `cos(2*eta)`, the JAX exact alias gate reports `alias_pass=true`, and the envelope requires alias preservation across JAX, Julia, and PyTorch (`s9_alias_control_pass_all_lanes=true`). If this alias had separated, the packet would fail as gauge-broken; it did not.

## Pin honesty

Accepted with C1 and C2.

The envelope boundary says `excluded-under-pinned-path-ordered-transport-convention; reopenable under convention/calibration change`, and the JAX candidate rows say `reopenable_if: the pinned leaf-by-leaf S9 transport convention or loop calibration changes`. No intrinsic-kill wording is accepted for S9.R3.5.

Pin inventory:

| Pin | Where used | Status |
| --- | --- | --- |
| Pinned S2/S9 `phi` holonomy convention | S9 light pass `S9.R3.1` through `S9.R3.4` | Four light exclusions accepted as convention-pinned and reopenable. |
| Pinned path-ordered transport convention | This heavy packet `S9.R3.5` | Additional pin; excludes the heavy transport neighbor under the loop calibration only. |

## Cover validity

Accepted.

The packet uses the canonical finite distinct nonboundary fixed-leaf rule from `geo_union_rule_k_leaves_v0`: for leaves `eta_i`, weights are

```text
w_i = sin(2*eta_i) / sum_j sin(2*eta_j)
```

The three registered unions are valid before flux comparison:

| Union | Validity | Weights | Annular-Stokes result |
| --- | --- | --- | --- |
| `{pi/12, pi/6}` | valid distinct nonboundary ordered leaves | `((-1 + sqrt(3))/2, -(-3 + sqrt(3))/2)` | flux `pi*(-1 + sqrt(3))/2`, boundary gap same, defect `0` |
| `{pi/6, pi/4}` | valid distinct nonboundary ordered leaves | `(-3 + 2*sqrt(3), -2*(-2 + sqrt(3)))` | flux `pi/2`, boundary gap same, defect `0` |
| `{pi/4, pi/3}` | valid distinct nonboundary ordered leaves | `(-2*(-2 + sqrt(3)), -3 + 2*sqrt(3))` | flux `pi/2`, boundary gap same, defect `0` |

The invalid control `invalid.overlapping_duplicate_pi6` fails at the validity gate: `distinct_fixed_eta_leaves=false`, `valid=false`, `flux_compared=false`, and flux/stokes fields are null. That is the right failure mode, not a downstream flux coincidence.

## Solver and tool honesty

Accepted with C3-C5.

The solver polarity rows are green:

| Solver | Positive | Flip |
| --- | --- | --- |
| z3 | `unsat` | `sat` |
| cvc5 | `unsat` | `sat` |
| Julia Z3 | `unsat` | `sat` |

The honest citation is "SMT binds finite witness values with erased flips." Do not cite it as "SMT derived path-ordered transport." The exact transport and cover rows are CAS/symbolic rows, with ODE and PyTorch lanes acting as controls/mirrors.

## Validators

Fresh read-only validators passed:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/round3_s9_s2_final_heavy_v0/results/round3_s9_s2_final_heavy_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s9_s2_final_heavy_v0/results/round3_s9_s2_final_heavy_v0_envelope_results.json"}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/round3_s9_s2_final_heavy_v0/results/round3_s9_s2_final_heavy_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s9_s2_final_heavy_v0/results/round3_s9_s2_final_heavy_v0_envelope_results.json"}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-tool-intent system_v6/sims/round3_s9_s2_final_heavy_v0/results/round3_s9_s2_final_heavy_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s9_s2_final_heavy_v0/results/round3_s9_s2_final_heavy_v0_envelope_results.json"}
```

No-write packet-local mirror check returned:

```text
{"ok": true, "anchor_gap": "1", "candidate_gap": "4*sin(41*pi/160)**4", "theta_gap": "pi/160", "errors": []}
```

I did not run `validate_round3_s9_s2_final_heavy_v0.py` in place because it writes `results/round3_s9_s2_final_heavy_v0_validator_results.json`, and this audit was authorized to write only this verdict file.

## Citable per-row table

| Layer/row | Light verdict | Heavy verdict | Citable status after this audit |
| --- | --- | --- | --- |
| `S2.R3.0_committed` | anchor | no heavy row | Anchor self-classifies in light pass. |
| `S2.R3.1_large_gauge_chi_shift` | `excluded-under-pinned-lifted-holonomy-convention` | no heavy row | Reopenable if lifted-holonomy pin changes. |
| `S2.R3.2_same_curvature_shifted_holonomy` | excluded by leaf holonomy spectrum | no heavy row | Closed for registered row. |
| `S2.R3.3_endpoint_chern_preserving_bump` | excluded by curvature density and annular Stokes | no heavy row | Closed for registered row. |
| `S2.R3.4_two_leaf_holonomy_match` | excluded by expanded leaf holonomy vector | no heavy row | Closed for registered row. |
| `S2.R3.5_boundary_conditioning_variant` | `open + queued-heavy-local` | valid-cover family; all three unions match annular-Stokes anchor; invalid duplicate fails before flux | Closed for registered finite unions; arbitrary/boundary/transverse conditioning remains fenced. |
| `S3.R3.0_committed_pauli_xyz` | anchor | no heavy row queued | Anchor self-classifies. |
| `S3.R3.1_mub_xyz_alias_probe` | exact canonical-form alias | no heavy row queued | Alias, not separate row. |
| `S3.R3.2_sic_tetrahedron` | known IC co-survivor backed by `608bbd763` | no heavy row queued | Registered S3 co-survivor remains; no heavy-local S3 queue. |
| `S3.R3.3_noisy_pauli_ic` | excluded by projective sharpness/N01 row | no heavy row queued | Closed for registered row. |
| `S3.R3.4_z_refined_equatorial_trine` | excluded by z-coarsening/six-state separation | no heavy row queued | Closed for registered row. |
| `S3.R3.5_rank4_random_null_fixed` | excluded by composite IC+z+order row | no heavy row queued | Closed for registered row. |
| `S4.R3.0_committed_DzDxRxRz` | anchor | anchor self-passes heavy rows | Anchor self-classifies. |
| `S4.R3.1_z_amplitude_damping_pair` | `open + queued-heavy-local` | excluded by N01/commutator and fixed-axis rows | Closed for registered row by `bec8bc0d4`. |
| `S4.R3.2_x_amplitude_damping_pair` | `open + queued-heavy-local` | `excluded-under-pinned-z-probe-convention` by quotient descent/mortality | Closed for registered row, reopenable if z-probe pin changes, by `bec8bc0d4`. |
| `S4.R3.3_dephase_rotate_hybrid` | `open + queued-heavy-local` | excluded by shell preservation/leakage then N01 | Closed for registered row by `bec8bc0d4`. |
| `S4.R3.4_axis_permuted_committed` | `excluded-under-pinned-parent-z-probe-convention` | no heavy row | Reopenable if parent z-probe/S4 role-order pin changes. |
| `S4.R3.5_weak_nonunital_pauli_channel` | `open + queued-heavy-local` | excluded by fixed-axis plus Choi positivity | Closed for registered row by `bec8bc0d4`. |
| `S5.R3.0_committed_8` | anchor | anchor self-passes heavy rows | Anchor self-classifies. |
| `S5.R3.1_alpha_mix_rotation_contraction` | trio `open + queued-heavy-local` | all three alpha rows excluded by mirror structure and N01 full signature | Closed for registered rows by `de47dbccc`. |
| `S5.R3.2_committed_coeff_epsilon` | plus/minus `open + queued-heavy-local` | both excluded by fixed-point/basin and N01 gap | Closed for registered rows by `de47dbccc`; basin wording chart-relative. |
| `S5.R3.3_nonunital_weak_shift` | plus/minus `open + queued-heavy-local` | both excluded by validity, fixed point, quotient 56/56 | Closed for registered rows by `de47dbccc`. |
| `S5.R3.4_pairwise_LR_mirror_preserver` | excluded by Ni/Si mirror frame row | no heavy row | Closed for registered row. |
| `S5.R3.5_basin_preserving_null` | `open + queued-heavy-local` | excluded by time-flow/N01 row after quotient survival | Closed for registered row by `de47dbccc`. |
| `S67.R3.0_committed_torus_ring` | anchor | anchor self-passes heavy rows | Anchor self-classifies. |
| `S67.R3.1_mobius_reflection_shifted` | `open + queued-heavy-local` | excluded by lens quotient commensurability | Closed for registered row by `ac5df5a06`. |
| `S67.R3.2_klein_double_twist` | `open + queued-heavy-local` | excluded by cover-orbit well-definedness then lens row | Closed for registered row by `ac5df5a06`. |
| `S67.R3.3_shear_torus` | `open + queued-heavy-local` | excluded by lens descent and S6 leakage taxonomy | Closed for registered row by `ac5df5a06`. |
| `S67.R3.4_cycle_with_one_chord` | `open + queued-heavy-local` | excluded by bounded word cost and cycle holonomy | Closed for registered row by `ac5df5a06`. |
| `S67.R3.5_ladder_prism_graph` | `open + queued-heavy-local` | excluded by locality cost plus leakage class row | Closed for registered row by `ac5df5a06`. |
| `S9.R3.0_committed_hopf` | anchor | anchor self-passes transport row | Anchor self-classifies. |
| `S9.R3.1_c1_small_density_bump` | `excluded-under-pinned-phi-holonomy-convention` via curvature density before holonomy | no heavy row | Reopenable if `phi` holonomy pin changes. |
| `S9.R3.2_one_leaf_match_pi6` | `excluded-under-pinned-phi-holonomy-convention` via expanded holonomy spectrum | no heavy row | Reopenable if `phi` holonomy pin changes. |
| `S9.R3.3_one_leaf_match_pi4` | `excluded-under-pinned-phi-holonomy-convention` via expanded holonomy spectrum | no heavy row | Reopenable if `phi` holonomy pin changes. |
| `S9.R3.4_two_leaf_match_pi6_pi4` | `excluded-under-pinned-phi-holonomy-convention` via annular flux plus off-anchor holonomy | no heavy row | Reopenable if `phi` holonomy pin changes. |
| `S9.R3.5_path_ordered_loop_neighbor` | `open + queued-heavy-local` | `excluded-under-pinned-path-ordered-transport-convention`; no co-survivors minted | Closed for registered row, reopenable if transport pin/calibration changes. |

## Round-3 closure scoreboard

| Layer | Light verdict | Heavy verdict | What remains open |
| --- | --- | --- | --- |
| S2 | Anchor/alias pass accepted; R3.1 convention-pinned; R3.2-R3.4 excluded; R3.5 queued | R3.5 valid-cover family accepted in this packet | Only lifted-holonomy pin reopen for R3.1 and unenumerated/fenced conditioning variants. |
| S3 | MUB alias; SIC known IC co-survivor; R3.3-R3.5 excluded; no heavy queue | No registered heavy row | SIC remains a registered co-survivor; unenumerated POVM/probe families remain outside closure. |
| S4 | R3.4 convention-pinned; R3.1/R3.2/R3.3/R3.5 queued | All four queued rows excluded in `bec8bc0d4` | Only z-probe/role-order pin reopen for R3.4 and unenumerated channel alphabets. |
| S5 | R3.4 excluded; eight heavy rows queued | All eight queued rows excluded in `de47dbccc` | Unenumerated terrain-flow families; chart-relative basin language cannot be widened. |
| S6/S7 | Five heavy rows queued; reparameterized cycle alias accepted | All five queued rows excluded in `ac5df5a06` | Unenumerated graph/cover/lens variants; no global topology uniqueness. |
| S9 | R3.1-R3.4 excluded under pinned `phi` holonomy convention; R3.5 queued | R3.5 excluded under pinned path-ordered transport convention in this packet | Two reopenable pin families plus unenumerated S9 transport/nondivision variants. |

## Exact citable closure sentence

Within the finite round-3 alternative spaces registered in `round3_discriminator_registry_20260611.md` and the consolidated heavy queue from `round3_s9_alias_pass_v0`, the round-3 discriminator program is closed at `scratch_diagnostic` ceiling: S4, S5, S6/S7, S9.R3.5, and S2.R3.5 have had all registered heavy rows adjudicated with no new heavy co-survivors minted; S3 retains its prior receipt-backed SIC co-survivor and no heavy row; the only surviving reopen paths are explicitly convention-pinned rows and unenumerated subvariants outside the registry, so this is registered-space closure, not global uniqueness or formal admission.

## Future citation rule

Future citations may say:

```text
round3_s9_s2_final_heavy_v0 is a bounded final-heavy scratch diagnostic: S9.R3.5 is excluded under the pinned path-ordered transport convention by exact quaternion loop signatures, with the deliberate gauge-reparameterization alias preserved; S2.R3.5 admits exactly the three registered finite distinct nonboundary leaf unions under the canonical sin(2eta) disintegration rule, all matching annular-Stokes, while the duplicate/overlapping control fails before flux; no new co-survivors are minted; the registered round-3 heavy queue is closed.
```

Future citations must not say:

```text
S2 or S9 are unique; S9.R3.5 is intrinsically killed independent of convention; arbitrary S2 conditioning is admitted; SMT derived the full transport law; PyTorch arbitrated the claim; round-3 proves global stack uniqueness; formal admission or promotion is allowed.
```

