# TOOL MANIFEST AUDIT

| Field | Value |
|-------|-------|
| last_verified | 2026-04-07 |
| status | Machine-generated from repo scan. All counts are grep-verified. |
| scope | `system_v4/probes/` (all .py files, recursive) and `system_v4/probes/a2_state/sim_results/` (all .json files) |
| total_py_files | 11,242 |
| total_json_results | 577 (561 non-history + 16 history) |

---

## Import Usage (across .py files in system_v4/probes/)

| Tool | Files Importing | Count | % of Total .py | Real Usage (excl. template/cross-check) |
|------|----------------|-------|----------------|----------------------------------------|
| z3 | see list below | 34 | 0.30% | 29 (real sims) |
| sympy | see list below | 21 | 0.19% | 16 |
| clifford | see list below | 28 | 0.25% | 23 |
| toponetx | see list below | 22 | 0.20% | 17 |
| torch | see list below | 16 | 0.14% | 11 |
| torch_geometric / pyg | see list below | 15 | 0.13% | 8 |
| gudhi | see list below | 9 | 0.08% | 3 |
| cvc5 | see list below | 6 | 0.05% | **0** (template/cross-check only) |
| geomstats | see list below | 5 | 0.04% | **0** (template/cross-check only) |
| e3nn | see list below | 5 | 0.04% | **0** (template/cross-check only) |
| rustworkx | see list below | 5 | 0.04% | **0** (template/cross-check only) |
| xgi | see list below | 5 | 0.04% | **0** (template/cross-check only) |

**Template/cross-check files** (appear in nearly every tool's count but are not real sims):
- `SIM_TEMPLATE.py` -- the canonical sim skeleton, imports all 12 tools
- `sim_cvc5_cross_check.py` -- cross-check harness, imports all 12 tools
- `sim_rustworkx_cascade_dag.py` -- cascade DAG builder, imports all 12 tools
- `sim_gudhi_cascade_persistence.py` -- persistence harness, imports all 12 tools
- `sim_xgi_family_hypergraph.py` -- hypergraph builder, imports all 12 tools
- `phase1_first_experiments.py` -- early experiment file (cvc5, gudhi only)

---

### Detailed File Lists

#### z3 (34 files)
```
sim_negative_constraint_cascade.py    sim_constrain_legos_L0.py
sim_pure_lego_gates_decompositions.py sim_constrain_legos_L4.py
sim_constrain_legos_L5.py             sim_rustworkx_cascade_dag.py
sim_pure_lego_channels_choi_lindblad.py sim_bc1_fence_investigation.py
sim_layer7_12_formal_tools.py         sim_constraint_manifold_L0_L1.py
sim_constraint_manifold_L7_L8_L9.py   sim_constrain_legos_L1.py
sim_constraint_manifold_L2_L3.py      sim_pure_lego_no_go_theorems.py
sim_compound_legos_forced.py          sim_cvc5_cross_check.py
sim_z3_fence_exhaustive_negatives.py  sim_constraint_manifold_L4_L5_L6.py
sim_negative_channels.py              sim_negative_density_matrices.py
sim_constrain_legos_L3.py             sim_minimal_surviving_set.py
sim_gudhi_cascade_persistence.py      sim_pure_lego_bell_witnesses_steering.py
sim_axis_algebraic_relations.py       sim_layer0_1_formal_tools.py
sim_root_constraint_ablation.py       sim_layer13_19_formal_tools.py
sim_constrain_legos_L2.py             sim_constrain_legos_L6_L7.py
mass_stabilization_sim.py             sim_xgi_family_hypergraph.py
SIM_TEMPLATE.py                       sim_checkerboard_admissibility.py
```

#### sympy (21 files)
```
sim_layer7_12_formal_tools.py         sim_constrain_legos_L1.py
sim_pure_lego_majorization_steering_coherence.py sim_operator_basis_search.py
sim_rustworkx_cascade_dag.py          sim_constrain_legos_L0.py
sim_pure_lego_qfi_wy_qgt.py          sim_constrain_legos_L5.py
sim_constraint_manifold_L0_L1.py      sim_layer4_5_6_formal_tools.py
sim_constraint_manifold_L4_L5_L6.py   sim_layer0_1_formal_tools.py
sim_cvc5_cross_check.py               sim_gudhi_cascade_persistence.py
sim_root_constraint_ablation.py       sim_layer13_19_formal_tools.py
sim_constraint_manifold_L2_L3.py      sim_xgi_family_hypergraph.py
mass_stabilization_sim.py             sim_constrain_legos_L2.py
SIM_TEMPLATE.py
```

#### clifford (28 files)
```
engine_pure_clifford.py               sim_axis_7_12_audit.py
sim_layer6_operators_algebra.py       sim_rustworkx_cascade_dag.py
sim_negative_geometry.py              sim_layer4_5_6_formal_tools.py
sim_deep_quantum_geometry.py          sim_operator_geometry_compatibility.py
sim_constraint_manifold_L2_L3.py      sim_pure_spinor_transport.py
sim_constraint_manifold_L4_L5_L6.py   sim_compound_operator_geometry.py
sim_layer7_12_formal_tools.py         sim_layer0_1_formal_tools.py
sim_pure_lego_clifford_algebra.py     sim_cvc5_cross_check.py
sim_constrain_legos_L3.py             sim_axis0_orbit_phase_alignment.py
sim_gudhi_cascade_persistence.py      sim_xgi_family_hypergraph.py
engine_geometric.py                   sim_constrain_legos_L2.py
mass_stabilization_sim.py             sim_full_torus_spinor_dynamics.py
sim_pure_geometry_hopf_tori.py        clifford_engine_bridge.py
sim_layer2_3_formal_tools.py          SIM_TEMPLATE.py
```

#### toponetx (22 files)
```
sim_pure_lego_topology_graphs.py      sim_layer7_12_formal_tools.py
sim_constraint_manifold_L10_L11_L12.py sim_rustworkx_cascade_dag.py
sim_pure_spinor_transport.py          sim_unified_engine_tuning.py
sim_negative_topology_graphs.py       sim_constraint_manifold_L2_L3.py
engine_unified.py                     engine_graph_driven.py
sim_cvc5_cross_check.py               sim_layer13_19_formal_tools.py
engine_toponetx_constrained.py        sim_gudhi_cascade_persistence.py
sim_xgi_family_hypergraph.py          sim_pure_geometry_hopf_tori.py
mass_stabilization_sim.py             sim_layer2_3_formal_tools.py
SIM_TEMPLATE.py                       toponetx_torus_bridge.py
sim_axis3_fiber_base.py               engine_geometric.py
```

#### torch (16 files)
```
sim_pure_lego_topology_graphs.py      sim_layer7_12_formal_tools.py
pyg_engine_bridge.py                  sim_constraint_manifold_L4_L5_L6.py
sim_rustworkx_cascade_dag.py          sim_negative_topology_graphs.py
engine_pyg_message_passing.py         sim_cvc5_cross_check.py
sim_layer4_5_6_formal_tools.py        sim_axis0_orbit_phase_alignment.py
sim_gudhi_cascade_persistence.py      sim_layer13_19_formal_tools.py
sim_edge_state_writeback.py           engine_graph_driven.py
sim_xgi_family_hypergraph.py          SIM_TEMPLATE.py
```

#### torch_geometric / pyg (15 files)
```
sim_pure_lego_topology_graphs.py      sim_rustworkx_cascade_dag.py
engine_pyg_message_passing.py         sim_layer4_5_6_formal_tools.py
sim_constraint_manifold_L4_L5_L6.py   sim_layer7_12_formal_tools.py
pyg_engine_bridge.py                  sim_negative_topology_graphs.py
sim_cvc5_cross_check.py               engine_graph_driven.py
sim_gudhi_cascade_persistence.py      sim_layer13_19_formal_tools.py
sim_xgi_family_hypergraph.py          mass_stabilization_sim.py
SIM_TEMPLATE.py
```

#### gudhi (9 files)
```
sim_rustworkx_cascade_dag.py          followup_anomaly_investigation.py
sim_cvc5_cross_check.py               sim_gudhi_cascade_persistence.py
probe_topology_all.py                 sim_xgi_family_hypergraph.py
mass_stabilization_sim.py             phase1_first_experiments.py
SIM_TEMPLATE.py
```
Real usage (3 files): `followup_anomaly_investigation.py`, `probe_topology_all.py`, `mass_stabilization_sim.py`

#### cvc5 (6 files) -- ALL template/cross-check
```
sim_rustworkx_cascade_dag.py          sim_cvc5_cross_check.py
sim_gudhi_cascade_persistence.py      sim_xgi_family_hypergraph.py
phase1_first_experiments.py           SIM_TEMPLATE.py
```

#### geomstats (5 files) -- ALL template/cross-check
```
sim_rustworkx_cascade_dag.py          sim_cvc5_cross_check.py
sim_gudhi_cascade_persistence.py      SIM_TEMPLATE.py
sim_xgi_family_hypergraph.py
```

#### e3nn (5 files) -- ALL template/cross-check
```
sim_cvc5_cross_check.py               sim_rustworkx_cascade_dag.py
sim_gudhi_cascade_persistence.py      SIM_TEMPLATE.py
sim_xgi_family_hypergraph.py
```

#### rustworkx (5 files) -- ALL template/cross-check
```
sim_rustworkx_cascade_dag.py          sim_cvc5_cross_check.py
sim_gudhi_cascade_persistence.py      sim_xgi_family_hypergraph.py
SIM_TEMPLATE.py
```

#### xgi (5 files) -- ALL template/cross-check
```
sim_rustworkx_cascade_dag.py          sim_cvc5_cross_check.py
sim_gudhi_cascade_persistence.py      sim_xgi_family_hypergraph.py
SIM_TEMPLATE.py
```

---

## Result Schema Adoption (across .json files in sim_results/)

Total non-history JSON files: **561**

| Field | Files Containing | Count | % of Total |
|-------|-----------------|-------|------------|
| tools_used | 39 files | 39 | 7.0% |
| classification | 20 files | 20 | 3.6% |
| tool_manifest | 4 files | 4 | 0.7% |

### Files with `tool_manifest` (4)
```
cvc5_cross_check_results.json
gudhi_cascade_persistence_results.json
rustworkx_cascade_dag_results.json
xgi_family_hypergraph_results.json
```

### Files with `classification` (20)
```
axis0_stack_packet_run_results.json       cvc5_cross_check_results.json
pre_entropy_packet_validation.json        matched_marginal_packet_validation.json
constrain_legos_L5_results.json           SIM_MANIFEST.json
carrier_selection_packet_validation.json  gudhi_cascade_persistence_results.json
constrain_legos_L6_L7_results.json        root_emergence_packet_validation.json
c1_bridge_object_packet_validation.json   constraint_manifold_L2_L3_results.json
entropy_readout_packet_validation.json    pure_lego_definetti_symmetry_results.json
c1_bridge_object_packet_results.json      xgi_family_hypergraph_results.json
cut2_bridge_investigation_results.json    rustworkx_cascade_dag_results.json
negative_constraint_cascade_results.json  pure_lego_channel_capacity_results.json
```

### Files with `tools_used` (39)
All 39 are layer-formal or layer-results files from the constraint manifold series:
```
layer0_root_constraints_results.json      layer0_root_constraints_formal_results.json
layer1_admissibility_fences_results.json  layer1_admissibility_fences_formal_results.json
layer2_carrier_formal_results.json        layer3_connection_loop_geometry_results.json
layer3_connection_formal_results.json     layer4_weyl_chirality_results.json
layer4_weyl_chirality_formal_results.json layer5_four_topologies_results.json
layer5_four_topologies_formal_results.json layer6_operators_algebra_results.json
layer6_operators_algebra_formal_results.json layer7_composition_order_results.json
layer7_composition_order_formal_results.json layer8_polarity_dynamics_results.json
layer8_polarity_formal_results.json       layer9_strength_goldilocks_results.json
layer9_strength_goldilocks_formal_results.json layer10_dual_stack_necessity_results.json
layer10_dual_stack_formal_results.json    layer11_torus_transport_results.json
layer11_torus_transport_formal_results.json layer12_entanglement_dynamics_results.json
layer12_entanglement_dynamics_formal_results.json layer13_entanglement_earned_results.json
layer13_entanglement_earned_formal_results.json layer14_bridge_crosses_partition_results.json
layer14_bridge_crosses_partition_formal_results.json layer15_sustained_positive_ic_results.json
layer15_sustained_positive_ic_formal_results.json layer16_3q_vs_2q_advantage_results.json
layer16_3q_vs_2q_advantage_formal_results.json layer17_entropy_emergence_results.json
layer17_entropy_emergence_formal_results.json layer18_axes_from_entropy_results.json
layer18_axes_from_entropy_formal_results.json layer19_axis0_functions_results.json
layer19_axis0_formal_results.json
```

---

## Gap Analysis

### Tools installed but with ZERO real sim usage
| Tool | Status | Notes |
|------|--------|-------|
| **cvc5** | 0 real sims | Only in SIM_TEMPLATE + cross-check harness. No sim has ever used cvc5 for actual constraint solving. |
| **geomstats** | 0 real sims | Template-only. No Riemannian manifold computation in any sim. |
| **e3nn** | 0 real sims | Template-only. No equivariant neural network usage. |
| **rustworkx** | 0 real sims | Template-only. No graph algorithm usage (despite sim_rustworkx_cascade_dag.py existing as a harness). |
| **xgi** | 0 real sims | Template-only. No hypergraph computation in any real sim. |

### Tools with minimal real usage (watch list)
| Tool | Real Count | Notes |
|------|-----------|-------|
| **gudhi** | 3 sims | `followup_anomaly_investigation.py`, `probe_topology_all.py`, `mass_stabilization_sim.py` |
| **torch_geometric** | 8 sims | Concentrated in engine bridges and formal-layer sims |
| **torch** | 11 sims | Mostly as a dependency of PyG, not standalone autograd usage |

### Tools with strong adoption
| Tool | Real Count | Notes |
|------|-----------|-------|
| **z3** | 29 sims | Strongest adoption. Core constraint/fence/ablation/manifold sims. |
| **clifford** | 23 sims | Strong. Geometry, spinor, operator sims. |
| **toponetx** | 17 sims | Solid. Topology, manifold, engine sims. |
| **sympy** | 16 sims | Solid. Formal tools, constraint layers, pure legos. |

### Result files lacking `tool_manifest`
- **557 of 561** non-history JSON files (99.3%) lack the `tool_manifest` field.
- Only 4 files have it, all from the cascade/cross-check harness.
- The `tools_used` field (39 files, 7.0%) is more common but still covers only the layer-formal results.
- The `classification` field (20 files, 3.6%) is present in packet validations and recent constrain_legos results.

### Pre-template vs post-template split
- **Post-template** (contains `tools_used` OR `classification` OR `tool_manifest`): ~45 unique files (some overlap) = **~8%** of 561
- **Pre-template** (no schema fields): **~92%** of result files were generated before the SIM_TEMPLATE schema was adopted
- The layer0-19 formal results (39 files with `tools_used`) represent the most systematic post-template batch

### Critical observations
1. **5 of 12 canonical tools have zero real sim usage.** The tool ladder is declared but not exercised for cvc5, geomstats, e3nn, rustworkx, and xgi.
2. **tool_manifest is nearly absent from results.** Only 4 of 561 files carry it. This field is not being emitted by any real sim runner.
3. **The SIM_TEMPLATE imports all 12 tools but most sims do not follow the template.** The vast majority of .py files (11,200+) predate the template or are utility/engine code that does not use the canonical import pattern.
4. **tools_used adoption is confined to one batch.** The 39 layer-formal results suggest one systematic run adopted the schema; no other sim family has followed.
5. **PyTorch/PyG adoption is real but narrow.** 11 torch + 8 pyg files exist, mostly in engine bridges and formal-layer sims. The PYTORCH_RATCHET_BUILD_PLAN calls for much deeper integration.
