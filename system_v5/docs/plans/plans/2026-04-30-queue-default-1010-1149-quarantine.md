# Queue Default 1010-1149 Quarantine Table

Date: 2026-04-30

Scope: read-only triage for `system_v5/ops/queue_default.txt` rows 1010-1149.

Inputs checked:
- `system_v5/ops/stage_gate.json`: `active_stage=lego`, `allow_default_queue_late_stage=false`, `allow_tier_d_launch=false`
- `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`: hard build guardrail keeps tool sims, tool integrations, and lego sims active; broad coupling/coexistence/topology-variant/emergence promotion and bridge/axis/engine surfaces remain gated.
- `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`: exploratory coupling does not authorize higher-stage promotion; broad queueing for coupling/coexistence/topology/emergence/bridge/axis is blocked without cited gate evidence.

Legend:
- `ALLOW`: eligible for small-batch review under the active lego gate; still must pass normal sim contract checks before launch.
- `QUARANTINE`: do not launch from the default queue while the gate is lego; at most exploratory/read-only until the gate advances.

Conservative rule for this slice: rows that name broad cascade, pipeline, phase, layer, cross, composition, integrated, topology-variant, emergence, bridge, or axis-style work are `QUARANTINE` unless a future controller cites the gate evidence that admits them.

| Row | Queue item | Decision | Reason |
|---:|---|---|---|
| 1010 | `sim_meta_learning` | QUARANTINE | broad/meta-stage framing |
| 1011 | `sim_pure_lego_process_tomography` | ALLOW | pure lego-local |
| 1012 | `sim_lego_qit_batch` | ALLOW | lego batch; small-batch review required |
| 1013 | `sim_negative_entanglement` | ALLOW | negative test surface |
| 1014 | `sim_pure_lego_quantum_thermodynamics` | ALLOW | pure lego-local |
| 1015 | `sim_quantum_discord_depolarizing_c2` | ALLOW | bounded channel/discord probe |
| 1016 | `sim_negative_channels` | ALLOW | negative test surface |
| 1017 | `sim_cvc5_shells_crosscheck` | QUARANTINE | crosscheck/shell-wide wording |
| 1018 | `sim_negative_entropy_boundaries` | ALLOW | negative boundary probe |
| 1019 | `sim_qec_ratchet` | ALLOW | bounded lego-style QEC probe |
| 1020 | `sim_l6_binding_radius_sweep` | ALLOW | bounded single-layer sweep |
| 1021 | `sim_lego_lindblad_dissipator` | ALLOW | explicit lego |
| 1022 | `navier_stokes_formal_sim` | ALLOW | formal/tool-style standalone probe |
| 1023 | `sim_lego_flux_candidates` | ALLOW | explicit lego candidate work |
| 1024 | `sim_pure_lego_wilczek_zee_holonomy` | ALLOW | pure lego-local |
| 1025 | `sim_q2_clifford_structure` | ALLOW | bounded tool/structure probe |
| 1026 | `sim_lego_fiber_bundles` | ALLOW | explicit lego |
| 1027 | `sim_pure_lego_contact_structure_s3` | ALLOW | pure lego-local |
| 1028 | `sim_substrate_divergence_resolution` | QUARANTINE | broad substrate/divergence resolution |
| 1029 | `sim_deep_quantum_geometry` | QUARANTINE | broad deep-geometry scope |
| 1030 | `sim_weyl_two_model_crosscheck` | QUARANTINE | crosscheck/multi-model scope |
| 1031 | `sim_layer4_5_6_formal_tools` | QUARANTINE | multi-layer scope |
| 1032 | `sim_pure_lego_channels_choi_lindblad` | ALLOW | pure lego-local channel work |
| 1033 | `sim_z3_quantum_capacity_bound` | ALLOW | bounded proof/tool probe |
| 1034 | `sim_operator_basis_search` | ALLOW | bounded search probe |
| 1035 | `sim_topology_entropy_dynamics` | QUARANTINE | topology/dynamics integration |
| 1036 | `sim_berry_qfi_entangled_path` | ALLOW | bounded geometry/entanglement probe |
| 1037 | `sim_partial_trace_audit` | ALLOW | bounded audit/probe |
| 1038 | `sim_shell_global_companion_audit` | QUARANTINE | global shell scope |
| 1039 | `sim_pure_lego_majorization_steering_coherence` | ALLOW | pure lego-local |
| 1040 | `sim_lego_stinespring_complementary` | ALLOW | explicit lego |
| 1041 | `sim_pyg_dynamic_edge_werner` | ALLOW | bounded tool/graph probe |
| 1042 | `sim_lego_pauli_algebra` | ALLOW | explicit lego |
| 1043 | `sim_z3_channel_boundary_theorem` | ALLOW | bounded proof/tool probe |
| 1044 | `sim_entropy_type_sweep_L4_L6` | QUARANTINE | multi-layer sweep |
| 1045 | `sim_pure_lego_levi_civita_connection` | ALLOW | pure lego-local |
| 1046 | `sim_lego_dirac_gamma` | ALLOW | explicit lego |
| 1047 | `sim_pure_lego_random_circuits_typicality` | ALLOW | pure lego-local |
| 1048 | `sim_pure_lego_ml_density_matrix` | ALLOW | pure lego-local |
| 1049 | `sim_lego_stagewise_deltas` | QUARANTINE | stagewise wording |
| 1050 | `sim_torch_channel_taxonomy` | ALLOW | bounded taxonomy/tool probe |
| 1051 | `sim_lego_toric_code` | ALLOW | explicit lego |
| 1052 | `sim_lego_info_geometry` | ALLOW | explicit lego |
| 1053 | `sim_geom_topology_layers` | QUARANTINE | topology plus layers |
| 1054 | `sim_pure_lego_quantum_combs` | ALLOW | pure lego-local |
| 1055 | `sim_geom_layer_6_7` | QUARANTINE | multi-layer scope |
| 1056 | `sim_weyl_nested_shell` | QUARANTINE | nesting/shell-wide scope |
| 1057 | `sim_pure_lego_quaternion_octonion` | ALLOW | pure lego-local |
| 1058 | `sim_pure_spinor_transport` | ALLOW | bounded pure probe |
| 1059 | `sim_entropy_topology_compatibility` | QUARANTINE | topology compatibility/integration |
| 1060 | `sim_negative_density_matrices` | ALLOW | negative test surface |
| 1061 | `sim_weyl_geometry_carrier_array` | QUARANTINE | carrier-array integration scope |
| 1062 | `qit_complete_math_reference` | ALLOW | reference/docs-only; not a sim launch |
| 1063 | `sim_pure_lego_multiqubit_cp_admissibility` | ALLOW | pure lego-local |
| 1064 | `sim_geom_cp1_u1_projective` | ALLOW | bounded geometry probe |
| 1065 | `sim_lego_ppt_witnesses` | ALLOW | explicit lego |
| 1066 | `sim_werner_topology_boundary` | QUARANTINE | topology boundary scope |
| 1067 | `sim_contact_structure_s3` | ALLOW | bounded structure probe |
| 1068 | `sim_pure_lego_contextuality` | ALLOW | pure lego-local |
| 1069 | `sim_3qubit_dag_formal_ordering` | QUARANTINE | ordering/stack implication |
| 1070 | `sim_z3_s6_unitary_impossibility` | ALLOW | bounded proof/tool probe |
| 1071 | `sim_sasakian_structure_s3` | ALLOW | bounded structure probe |
| 1072 | `sim_pure_lego_bell_witnesses_steering` | ALLOW | pure lego-local |
| 1073 | `sim_torch_bit_phase_flip` | ALLOW | bounded channel probe |
| 1074 | `sim_geom_symplectic_kahler_contact` | ALLOW | bounded geometry lego-style probe |
| 1075 | `sim_minimal_surviving_set` | QUARANTINE | set-level selection/summary scope |
| 1076 | `sim_negative_advanced_legos` | ALLOW | negative lego-stage probe |
| 1077 | `sim_q3_bipartite_analysis` | ALLOW | bounded analysis probe |
| 1078 | `sim_weyl_spinor_hopf` | ALLOW | bounded lego-style probe |
| 1079 | `sim_density_hopf_geometry` | ALLOW | bounded geometry probe |
| 1080 | `sim_berry_qfi_shell_paths` | QUARANTINE | shell/path integration scope |
| 1081 | `sim_lego_quantum_thermo` | ALLOW | explicit lego |
| 1082 | `sim_geom_layer_8_9_10` | QUARANTINE | multi-layer scope |
| 1083 | `sim_werner_manifold_scan` | ALLOW | bounded manifold scan |
| 1084 | `sim_lego_graph_cluster_states` | ALLOW | explicit lego |
| 1085 | `sim_lorentzian_geometry` | ALLOW | bounded geometry probe |
| 1086 | `sim_torch_shells_displacement_metric` | QUARANTINE | shells/metric integration |
| 1087 | `sim_pure_lego_holographic` | ALLOW | pure lego-local |
| 1088 | `sim_twilight_zone` | QUARANTINE | ambiguous broad scope |
| 1089 | `sim_layered_foundation` | QUARANTINE | layered foundation scope |
| 1090 | `sim_torch_lindblad` | ALLOW | bounded torch probe |
| 1091 | `sim_3qubit_dag_formal_ordering_v2` | QUARANTINE | ordering/stack implication |
| 1092 | `sim_qit_repair_comparison_surface` | QUARANTINE | comparison surface scope |
| 1093 | `sim_pure_lego_geodesic_exponential_map` | ALLOW | pure lego-local |
| 1094 | `sim_compound_operator_geometry` | QUARANTINE | compound/integration scope |
| 1095 | `sim_gnn_cascade_integrated` | QUARANTINE | cascade plus integrated pipeline |
| 1096 | `sim_torch_gnn_extended_training` | QUARANTINE | extended training/pipeline scope |
| 1097 | `sim_torch_ratchet_pipeline_v2` | QUARANTINE | pipeline scope |
| 1098 | `sim_geometry_families_L0` | ALLOW | bounded single-layer family probe |
| 1099 | `sim_gudhi_s2_topology_recovery` | ALLOW | bounded topology tool probe |
| 1100 | `sim_werner_qwci_gap` | ALLOW | bounded gap probe |
| 1101 | `sim_hopf_foliation_structure` | ALLOW | bounded structure probe |
| 1102 | `sim_phase7_divergence_analysis` | QUARANTINE | phase/divergence scope |
| 1103 | `sim_g_structure_tower` | QUARANTINE | tower/layered scope |
| 1104 | `sim_lego_lindblad_spectral` | ALLOW | explicit lego |
| 1105 | `sim_weyl_geometry_alignment_overlay_v2` | QUARANTINE | alignment/overlay integration |
| 1106 | `sim_cross_layer_negative_propagation` | QUARANTINE | cross-layer propagation |
| 1107 | `sim_constrain_legos_L6_L7` | QUARANTINE | multi-layer lego constraint |
| 1108 | `sim_phase_damping_fixed_point_geometry` | ALLOW | bounded channel geometry probe |
| 1109 | `sim_lego_gksl_kossakowski` | ALLOW | explicit lego |
| 1110 | `sim_lego_povm_measurement` | ALLOW | explicit lego |
| 1111 | `sim_torch_shells_gradient_flow` | QUARANTINE | shells/flow integration |
| 1112 | `sim_layer13_19_formal_tools` | QUARANTINE | multi-layer scope |
| 1113 | `sim_e3nn_ic_pipeline` | QUARANTINE | pipeline scope |
| 1114 | `sim_lego_positive_maps` | ALLOW | explicit lego |
| 1115 | `sim_torch_graph_integrated_pipeline` | QUARANTINE | integrated pipeline |
| 1116 | `sim_w_ghz_analytic_resolution` | ALLOW | bounded analytic probe |
| 1117 | `sim_pure_lego_mega_protocols` | QUARANTINE | mega/protocol breadth |
| 1118 | `sim_four_topology_pauli_map` | QUARANTINE | topology-map integration |
| 1119 | `sim_torch_ratchet_gnn` | ALLOW | bounded torch/GNN probe |
| 1120 | `sim_layer0_1_formal_tools` | QUARANTINE | multi-layer scope |
| 1121 | `sim_e3nn_ic_invariance` | ALLOW | bounded tool/invariance probe |
| 1122 | `sim_layer7_12_formal_tools` | QUARANTINE | multi-layer scope |
| 1123 | `sim_lego_coherent_info_advanced` | ALLOW | explicit lego; advanced but local |
| 1124 | `sim_tools_load_bearing` | ALLOW | tool-integration surface |
| 1125 | `sim_constraint_manifold_L0_L1` | QUARANTINE | manifold/multi-layer scope |
| 1126 | `sim_weyl_relay_gradient_sweep` | QUARANTINE | relay/sweep integration |
| 1127 | `sim_geometric_constraint_manifold_pyg` | QUARANTINE | manifold integration |
| 1128 | `sim_torch_gnn_directional_gate` | ALLOW | bounded tool/gate probe |
| 1129 | `sim_information_geometry` | ALLOW | bounded geometry probe |
| 1130 | `sim_negative_compound_failures` | QUARANTINE | compound failure surface |
| 1131 | `sim_constrain_legos_L5` | ALLOW | single-layer lego constraint |
| 1132 | `sim_z3_channel_composition_boundary` | QUARANTINE | composition boundary |
| 1133 | `sim_constraint_shells_binding_crosscheck` | QUARANTINE | shell/crosscheck scope |
| 1134 | `sim_constrain_legos_L4` | ALLOW | single-layer lego constraint |
| 1135 | `sim_torch_gnn_gradient_ref_ablation` | ALLOW | bounded ablation probe |
| 1136 | `sim_substrate_insensitive_analysis` | QUARANTINE | substrate-wide analysis |
| 1137 | `sim_torch_constraint_shells` | QUARANTINE | shells integration |
| 1138 | `sim_torch_constraint_shells_v2` | QUARANTINE | shells integration |
| 1139 | `sim_3qubit_full_cascade` | QUARANTINE | full cascade |
| 1140 | `sim_full_ratchet_cascade` | QUARANTINE | full cascade |
| 1141 | `sim_root_constraint_ablation` | ALLOW | bounded root ablation |
| 1142 | `sim_constrain_legos_L1` | ALLOW | single-layer lego constraint |
| 1143 | `sim_compound_legos_forced` | QUARANTINE | compound forced scope |
| 1144 | `sim_4qubit_cascade` | QUARANTINE | cascade |
| 1145 | `sim_negative_constraint_cascade` | QUARANTINE | cascade |
| 1146 | `sim_constrain_legos_L2` | ALLOW | single-layer lego constraint |
| 1147 | `sim_phase7_baseline_validation` | QUARANTINE | phase-level validation |
| 1148 | `sim_constrain_legos_L0` | ALLOW | single-layer lego constraint |
| 1149 | `sim_constrain_legos_L3` | ALLOW | single-layer lego constraint |

Summary:
- `ALLOW`: 83 rows
- `QUARANTINE`: 57 rows
- No rows in this table advance public status labels or authorize broad launch.
- If `stage_gate.json` advances beyond lego, rerun this triage against the new active gate before launch.
