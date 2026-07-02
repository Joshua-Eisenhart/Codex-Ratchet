# Actual Deep Sim Execution Matrix - 2026-05-30

This is an execution matrix, not an admission claim. It replaces the earlier bad "8-128 depth" framing with fresh runs of actual deep probes where those probes exist.

## Boundary

Fresh execution matrix only. It reports passes local rerun for bounded deep scouts/diagnostics. It does not claim any protected downstream admission, order-composition readiness, bridge progress, or terminal consumer status.

## Counts

- `individual_layer_full_spinor_network_rows`: 9
- `individual_layer_full_spinor_network_passed`: 9
- `one_target_geometry_network_deepening_rows`: 1
- `one_target_geometry_network_deepening_passed`: 1
- `geometry_full_network_target_rows`: 24
- `geometry_full_network_target_passed`: 24
- `standalone_structure_candidate_spinor_network_rows`: 12
- `standalone_structure_candidate_spinor_network_passed`: 12
- `actual_g_structure_known_math_rows`: 10
- `actual_g_structure_known_math_passed`: 10
- `standalone_known_geometry_math_rows`: 22
- `standalone_known_geometry_math_passed`: 22
- `tool_by_tool_depth_all_pass`: True
- `tool_by_tool_tool_rows_passed`: 15

## One-Target Geometry Network Deepening

This row was added after the Claude audit corrected the JAX-wave status. It is
not a repeat of the 24-target shared JAX wrapper.

| Target/result | Pass | Max sites | Bonds | JAX/Torch delta | Min order gap | Min entanglement gap | Locked |
|---|---:|---:|---:|---:|---:|---:|---|
| `nested_hopf_tori_full_deep_network_probe_results.json` | True | 64 | 2/4 | 4.440892098500626e-16 | 0.041310739817546946 | 0.6931471824645996 | yes |

What this one row adds beyond the earlier JAX finite-sample scout:

- explicit shell/leaf/site Hopf spinors `psi(eta,phi,chi)`;
- MPS, PEPS2D, and PEPS3D carrier views;
- geometry-specific leaf/fiber/base transport;
- JAX x64 versus PyTorch parity;
- QIT readouts from spinor-network density cuts;
- SymPy, z3, cvc5, rustworkx, XGI, TopoNetX, and GUDHI checks;
- product/no-entanglement, PEPS3D-erased, fiber/base-scrambled,
  order-erased, scalar-entropy-primary, and generic-dynamics controls.

Boundary:

```text
This is one bounded standalone target-deepening scout.
It does not prove nested Hopf tori as the selected G-structure.
It does not complete any manifold layer.
Protected downstream consumers remain blocked.
```
- `tool_by_tool_tool_count`: 15

## 24-Target Geometry Full-Network Batch

This row closes the specific gap identified by the JAX geometry audit: the
target invariants were real, but the shared finite-sample carrier was shallow.
The new batch keeps the invariant functions load-bearing and adds a
target-modulated spinor-network carrier, MPS/PEPS2D/PEPS3D carrier views,
target-specific transport coefficients, JAX x64 / PyTorch parity, QIT readouts,
proof/topology checks, and controls for every target.

| Result | Targets | Passed | Max sites | Bonds | Max JAX/Torch delta | Min order gap | Min MI | Min log-neg | Locked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `jax_geometry_full_network_targets_probe_results.json` | 24 | 24 | 64 | 2/4 | 2.6645352591003757e-15 | 0.030740976485093868 | 0.00030874578251566194 | 0.008356669068900065 | yes |

Per-target subreceipts were written under:

```text
system_v5/ops/formal_scouts/results/jax_geometry_full_network_targets_20260530/
```

Boundary:

```text
This is an aggregate bounded formal-scout batch over standalone geometry targets.
It does not select an official G-structure.
It does not complete manifold layers.
Protected downstream consumers remain blocked.
```

## Individual Layer Full Spinor-Network Scouts

| Layer/result | Pass | Max sites | PEPS2D | PEPS3D | Rows | Min MI | Min log-neg | Locked |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `l0_response_quotient_full_spinor_network_layer_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.10205246050277372 | 0.20308055342612366 | yes |
| `l1_boundary_environment_full_spinor_network_layer_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.10205246612969611 | 0.20308055962883817 | yes |
| `l2_weyl_spinor_full_spinor_network_layer_probe_results.json` | True | 64 | 4 | 4 | 8 | 0.11083342945912283 | 0.21257890380031383 | yes |
| `l3_clifford_quaternion_full_spinor_network_layer_probe_results.json` | True | 64 | 4 | 4 | 8 | 0.10476533091096325 | 0.20605326072187952 | yes |
| `l4_terrain_generator_full_spinor_network_layer_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.10205246050277372 | 0.20308055342612366 | yes |
| `l5_operator_substage_full_spinor_network_layer_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.10205246612969611 | 0.20308055962883817 | yes |
| `l6_entropy_cut_full_spinor_network_layer_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.1147254619134559 | 0.2166792995805729 | yes |
| `l7_hopf_shell_full_spinor_network_layer_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.12922673949674687 | 0.23142719104877715 | yes |
| `l8_groupoid_gluing_full_spinor_network_layer_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.01527613628977756 | 0.07080148070648143 | yes |

## Structure Candidate Spinor-Network Scouts

| Candidate/result | Pass | Max sites | PEPS2D | PEPS3D | Rows | Min MI | Min log-neg |
|---|---:|---:|---:|---:|---:|---:|---:|
| `s3_spinor_carrier_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.020856876585424067 | 0.08413757299288634 |
| `s2_hopf_base_surface_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.02773685256582419 | 0.09855395682445935 |
| `hopf_fibration_s3_to_s2_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.036421165931108904 | 0.11464195469669124 |
| `nested_hopf_tori_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.030987590270831037 | 0.10480662940128786 |
| `clifford_torus_t2_in_s3_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.0274664207943228 | 0.09801952650203229 |
| `twistor_incidence_spinor_geometry_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.03634093895698901 | 0.11450167180986331 |
| `u1_hopf_principal_bundle_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.08198795746243065 | 0.1798744705462251 |
| `su2_spin3_unit_quaternion_double_cover_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.09737491852489463 | 0.19786969354294065 |
| `so3_orientation_frame_reduction_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.11451207350106762 | 0.2164561399487528 |
| `pin3_spin3_chirality_split_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.6564313431604227 | 0.5613925129193447 |
| `clifford_geometries_cl3_cl6_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.1534178654162725 | 0.25444029016622155 |
| `hybrid_hopf_spin_twistor_clifford_reduction_graph_g_structure_full_function_probe_results.json` | True | 64 | 4 | 4 | 4 | 0.07481587106328616 | 0.17096854975381134 |

## Actual G-Structure Known-Math Diagnostics

- `gstruct_clifford_module_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `gstruct_g2_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `gstruct_hybrid_reduction_chain_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `gstruct_seiberg_witten_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `gstruct_so3_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `gstruct_spin7_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `gstruct_spin_c_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `gstruct_su2_spin3_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `gstruct_su3_calabi_yau_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `gstruct_u1_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]

## Standalone Known-Geometry Diagnostics

- `geom_clifford_algebra_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_clifford_torus_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_conformal_stereographic_s2_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_connection_holonomy_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_contact_sasakian_s3_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_cp1_fubini_study_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_dirac_monopole_u1_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_distinguishability_quotient_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_division_algebra_projective_lines_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_fiber_base_paths_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_finite_cell_complex_k_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_higher_hopf_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_hopf_fibration_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_left_right_weyl_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_nested_hopf_tori_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_quaternion_sphere_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_s2_hopf_base_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_s3_spinor_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_spectral_triple_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_spinor_density_carrier_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_symplectic_structure_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]
- `geom_twistor_incidence_deep_probe_results.json`: pass=True, classification=diagnostic_only, blockers=[]

## Tool-By-Tool Depth Receipt

- `tool_by_tool_layer_g_structure_geometry_depth_probe_results.json`: all_pass=True, tool_rows_passed=15/15

## Still Not Done Or Not Admitted

- No terminal downstream admission claim was made or earned.
- Protected geometry-selection consumers remain blocked.
- Protected order-composition consumers remain blocked.
- Protected downstream consumers remain blocked.
- The original JAX finite geometry wave has now been followed by a 24-target full-network strengthening batch, but that remains bounded formal-scout evidence, not downstream admission evidence.
- Known-geometry rows are diagnostic known-math evidence; spinor-network embedding still needs separate carrier rows where not already covered by the candidate wrappers.

## Reconciliation With JAX Reality Audit

This matrix should not be read as saying the 24 JAX geometry rows were fake.
They were not. The invariant functions are target-specific and meaningful.

The original 24 JAX geometry rows were not deep. The later
`jax_geometry_full_network_targets_probe_results.json` batch is the deeper
follow-up for that exact target set.

The remaining boundary is no longer "the 24 JAX geometry targets have no
network batch"; it is "the network batch is still scout evidence and protected
downstream consumers remain blocked."
