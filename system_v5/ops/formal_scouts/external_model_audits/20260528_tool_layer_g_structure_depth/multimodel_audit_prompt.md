You are an external audit model for Joshua Eisenhart's Codex Ratchet repo.

Audit only the evidence in this packet. Do not overclaim. Treat these as formal-scout/local-receipt evidence, not final manifold proof.

TASK:
Assess whether the current tool-by-tool layer/G-structure/geometry depth work is on track for the user's actual goal: work every relevant tool one by one through all separate layers, candidate G-structures, and geometry surfaces, deepening toward strong full sims. Identify drift, shallow spots, missing gates, and the next best bounded packets.

STRICT FRAME:
- The primary goal is separate layer sims and separate G-structure/geometry sims first, before official G-structure selection, layer embedding, stacking, flux, Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, or final manifold admission.
- PEPS2D/PEPS3D/MPS/tensor-network tools are finite computational carriers/views for spinor networks. Do not treat labels as proof.
- Entropy is a derived QIT readout unless a sim explicitly makes the shell possibility-gradient object primary.
- A green scout can still be shallow if it only proves one function surface per tool.
- Use repo gates: explicit finite map, F01/N01, torch-native spinors/densities, PEPS3D carrier from start, controls, tool ablations, blocked consumers.

OUTPUT FORMAT:
1. Verdict: ON_TRACK / PARTIAL_ON_TRACK / DRIFT / BLOCKED, with one paragraph.
2. Findings: severity P0/P1/P2/P3, each with packet field/path evidence from the audit packet.
3. What is genuinely earned.
4. What is not earned and must stay locked.
5. Shallow or fake-depth risks.
6. Next 5 bounded packets in priority order, each with exact stop condition.
7. One falsifier that would prove this campaign is drifting again.
8. One sentence I can send back to the formal sim TUI.

AUDIT PACKET JSON:
{
  "audit_created_at": "2026-05-28T07:38:04.590749+00:00",
  "g_structure_candidate_result": {
    "blocked_consumers": [
      "layer_embedding",
      "official_layered_ratchet_G_structure_selection",
      "stacking",
      "cross_layer_order_closure",
      "flux",
      "Xi/Phi0",
      "Axis0",
      "Holodeck/FEP",
      "physics/gravity",
      "final_manifold_admission"
    ],
    "candidates": [
      "Clifford_geometries_Cl3_Cl6",
      "Clifford_torus_T2_in_S3",
      "Hopf_fibration_S3_to_S2",
      "Hybrid_Hopf_Spin_Twistor_Clifford_reduction_graph",
      "Nested_Hopf_tori",
      "Pin3_Spin3_chirality_split",
      "S2_Hopf_base_surface",
      "S3_spinor_carrier",
      "SO3_orientation_frame_reduction",
      "SU2_Spin3_unit_quaternion_double_cover",
      "Twistor_incidence_spinor_geometry",
      "U1_Hopf_principal_bundle"
    ],
    "path": "system_v5/ops/formal_scouts/results/g_structure_candidate_space_full_function_probe_results.json",
    "source": "system_v5/ops/formal_scouts/sim_g_structure_candidate_space_full_function_probe.py",
    "summary": {
      "all_pass": true,
      "candidate_count": 12,
      "elapsed_seconds": 16.417613,
      "max_sites": 64,
      "min_entanglement_gap_vs_product_mps": 2.0794413089752197,
      "min_log_negativity": 0.08413757299288634,
      "min_mutual_information": 0.020856876585424067,
      "min_pyg_message_gap": 2.890460968017578,
      "peps2d_bond_dim": 4,
      "peps3d_bond_dim": 4,
      "row_count": 48,
      "selected_official_g_structure": null,
      "site_counts": [
        8,
        16,
        32,
        64
      ]
    }
  },
  "layer_dependency_status": {
    "bond4_individual_paths": [
      "system_v5/ops/formal_scouts/results/l0_response_quotient_peps3d_bond4_tool_ablation_layer_probe_results.json",
      "system_v5/ops/formal_scouts/results/l1_boundary_environment_peps3d_bond4_tool_ablation_layer_probe_results.json",
      "system_v5/ops/formal_scouts/results/l2_weyl_spinor_peps3d_bond4_tool_ablation_layer_probe_results.json",
      "system_v5/ops/formal_scouts/results/l3_clifford_quaternion_peps3d_bond4_tool_ablation_layer_probe_results.json",
      "system_v5/ops/formal_scouts/results/l4_terrain_generator_peps3d_bond4_tool_ablation_layer_probe_results.json",
      "system_v5/ops/formal_scouts/results/l5_operator_substage_peps3d_bond4_tool_ablation_layer_probe_results.json",
      "system_v5/ops/formal_scouts/results/l6_entropy_cut_peps3d_bond4_tool_ablation_layer_probe_results.json",
      "system_v5/ops/formal_scouts/results/l7_hopf_shell_peps3d_bond4_tool_ablation_layer_probe_results.json",
      "system_v5/ops/formal_scouts/results/l8_groupoid_gluing_peps3d_bond4_tool_ablation_layer_probe_results.json"
    ],
    "bond4_individual_result_count": 9,
    "full_spinor_layers": [
      {
        "all_pass": true,
        "layer": "L0",
        "max_sites": 64,
        "min_entanglement_gap_vs_product_mps": 2.0794413089752197,
        "min_log_negativity": 0.20308055342612366,
        "min_mutual_information": 0.10205246050277372,
        "min_pyg_message_gap": 2.915475845336914,
        "peps2d_bond_dim": 4,
        "peps3d_bond_dim": 4,
        "result_path": "system_v5/ops/formal_scouts/results/l0_response_quotient_full_spinor_network_layer_probe_results.json",
        "row_count": 4
      },
      {
        "all_pass": true,
        "layer": "L1",
        "max_sites": 64,
        "min_entanglement_gap_vs_product_mps": 2.0794413089752197,
        "min_log_negativity": 0.20308055962883817,
        "min_mutual_information": 0.10205246612969611,
        "min_pyg_message_gap": 2.915475845336914,
        "peps2d_bond_dim": 4,
        "peps3d_bond_dim": 4,
        "result_path": "system_v5/ops/formal_scouts/results/l1_boundary_environment_full_spinor_network_layer_probe_results.json",
        "row_count": 4
      },
      {
        "all_pass": true,
        "layer": "L2",
        "max_sites": 64,
        "min_entanglement_gap_vs_product_mps": 2.079441547393799,
        "min_log_negativity": 0.12598602205091244,
        "min_mutual_information": 0.04316704244885996,
        "min_pyg_message_gap": 1.2298386096954346,
        "peps2d_bond_dim": 4,
        "peps3d_bond_dim": 4,
        "result_path": "system_v5/ops/formal_scouts/results/l2_weyl_spinor_full_spinor_network_layer_probe_results.json",
        "row_count": 8
      },
      {
        "all_pass": true,
        "layer": "L3",
        "max_sites": 64,
        "min_entanglement_gap_vs_product_mps": 2.079441547393799,
        "min_log_negativity": 0.07495133483954947,
        "min_mutual_information": 0.016930405817572186,
        "min_pyg_message_gap": 1.2416900396347046,
        "peps2d_bond_dim": 4,
        "peps3d_bond_dim": 4,
        "result_path": "system_v5/ops/formal_scouts/results/l3_clifford_quaternion_full_spinor_network_layer_probe_results.json",
        "row_count": 8
      },
      {
        "all_pass": true,
        "layer": "L4",
        "max_sites": 64,
        "min_entanglement_gap_vs_product_mps": 2.0794413089752197,
        "min_log_negativity": 0.20308055342612366,
        "min_mutual_information": 0.10205246050277372,
        "min_pyg_message_gap": 2.915475845336914,
        "peps2d_bond_dim": 4,
        "peps3d_bond_dim": 4,
        "result_path": "system_v5/ops/formal_scouts/results/l4_terrain_generator_full_spinor_network_layer_probe_results.json",
        "row_count": 4
      },
      {
        "all_pass": true,
        "layer": "L5",
        "max_sites": 64,
        "min_entanglement_gap_vs_product_mps": 2.079441547393799,
        "min_log_negativity": 0.20308055962883817,
        "min_mutual_information": 0.10205246612969611,
        "min_pyg_message_gap": 2.915475845336914,
        "peps2d_bond_dim": 4,
        "peps3d_bond_dim": 4,
        "result_path": "system_v5/ops/formal_scouts/results/l5_operator_substage_full_spinor_network_layer_probe_results.json",
        "row_count": 4
      },
      {
        "all_pass": true,
        "layer": "L6",
        "max_sites": 64,
        "min_entanglement_gap_vs_product_mps": 2.079441547393799,
        "min_log_negativity": 0.2166792995805729,
        "min_mutual_information": 0.1147254619134559,
        "min_pyg_message_gap": 3.8891489505767822,
        "peps2d_bond_dim": 4,
        "peps3d_bond_dim": 4,
        "result_path": "system_v5/ops/formal_scouts/results/l6_entropy_cut_full_spinor_network_layer_probe_results.json",
        "row_count": 4
      },
      {
        "all_pass": true,
        "layer": "L7",
        "max_sites": 64,
        "min_entanglement_gap_vs_product_mps": 2.0794413089752197,
        "min_log_negativity": 0.23142719104877715,
        "min_mutual_information": 0.12922673949674687,
        "min_pyg_message_gap": 5.540477275848389,
        "peps2d_bond_dim": 4,
        "peps3d_bond_dim": 4,
        "result_path": "system_v5/ops/formal_scouts/results/l7_hopf_shell_full_spinor_network_layer_probe_results.json",
        "row_count": 4
      },
      {
        "all_pass": true,
        "layer": "L8",
        "max_sites": 64,
        "min_entanglement_gap_vs_product_mps": 2.079441547393799,
        "min_log_negativity": 0.1972960083976146,
        "min_mutual_information": 0.09686601719362813,
        "min_pyg_message_gap": 2.041800022125244,
        "peps2d_bond_dim": 4,
        "peps3d_bond_dim": 4,
        "result_path": "system_v5/ops/formal_scouts/results/l8_groupoid_gluing_full_spinor_network_layer_probe_results.json",
        "row_count": 4
      }
    ],
    "locked_consumers": [
      "stacking",
      "cross_layer_order_closure",
      "post_stack_stress",
      "PEPS3D_closure_theorem",
      "flux",
      "Xi/Phi0",
      "Axis0",
      "Holodeck/FEP",
      "physics/gravity",
      "IGT/game_theory",
      "axes7_12",
      "final_manifold_admission"
    ],
    "not_claimed": [
      "full layer completion",
      "nested manifold admission",
      "stacking proof",
      "flux admission",
      "Xi/Phi0 admission",
      "Axis0 admission",
      "FEP/Holodeck admission",
      "physics/gravity admission",
      "final manifold completion"
    ],
    "source": "system_v5/ops/formal_scouts/layer_depth_campaign_status_20260528.json"
  },
  "local_validation_performed_this_turn": [
    "lint_sim_contract.py on sim_tool_by_tool_layer_g_structure_geometry_depth_probe.py: violation_total=0",
    "validate_formal_scout_results.py --fresh-rerun on tool_by_tool_layer_g_structure_geometry_depth_probe_results.json: all_pass=true",
    "lint_sim_contract.py on sim_g_structure_candidate_space_full_function_probe.py: violation_total=0",
    "validate_formal_scout_results.py --fresh-rerun on g_structure_candidate_space_full_function_probe_results.json: all_pass=true",
    "validate_formal_scout_results.py --fresh-rerun on 9 full-spinor layer results and 9 bond4 layer tool-ablation results: all_pass=true",
    "JSON parse, ASCII scan, trailing whitespace scan, git diff --check: clean for touched artifacts"
  ],
  "new_tool_by_tool_result": {
    "blocked_consumers": [
      "official_layered_ratchet_G_structure_selection",
      "layer_embedding_in_G_structure",
      "stacking",
      "cross_layer_order_closure",
      "flux",
      "Xi/Phi0",
      "Axis0",
      "Holodeck/FEP",
      "physics/gravity",
      "final_manifold_admission"
    ],
    "boundary": {
      "classification_is_formal_scout": {
        "classification": "formal_scout",
        "pass": true
      },
      "downstream_consumers_locked": {
        "blocked_consumers": [
          "official_layered_ratchet_G_structure_selection",
          "layer_embedding_in_G_structure",
          "stacking",
          "cross_layer_order_closure",
          "flux",
          "Xi/Phi0",
          "Axis0",
          "Holodeck/FEP",
          "physics/gravity",
          "final_manifold_admission"
        ],
        "pass": true
      },
      "promotion_disabled": {
        "pass": true,
        "promotion_allowed": false
      },
      "result_is_canonical_formal_scout_path": {
        "pass": true,
        "result_path": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/ops/formal_scouts/results/tool_by_tool_layer_g_structure_geometry_depth_probe_results.json"
      }
    },
    "graveyard_companions": {
      "layer_embedding_still_blocked": {
        "blocked_consumers": [
          "official_layered_ratchet_G_structure_selection",
          "layer_embedding_in_G_structure",
          "stacking",
          "cross_layer_order_closure",
          "flux",
          "Xi/Phi0",
          "Axis0",
          "Holodeck/FEP",
          "physics/gravity",
          "final_manifold_admission"
        ],
        "pass": true
      },
      "qubit_sphere_adapter_rejected": {
        "pass": true,
        "reason": "features use explicit Hopf S3->S2 map from spinor coordinates, not carrier.w.bloch"
      },
      "scalar_entropy_primary_rejected": {
        "pass": true,
        "reason": "entropy is derived from carrier rows and is not the object"
      },
      "single_blended_all_tools_claim_rejected": {
        "pass": true,
        "reason": "tool_rows are ordered one by one and each has its own ablation/failure condition"
      },
      "tool_import_only_rejected": {
        "pass": true,
        "reason": "each tool row has a function_surface, pass condition, and coverage, not just an import"
      }
    },
    "path": "system_v5/ops/formal_scouts/results/tool_by_tool_layer_g_structure_geometry_depth_probe_results.json",
    "positive": {
      "all_g_structure_rows_recomputed_without_bloch_adapter": {
        "g_row_count": 48,
        "g_structures": [
          "S3_spinor_carrier",
          "S2_Hopf_base_surface",
          "Hopf_fibration_S3_to_S2",
          "Nested_Hopf_tori",
          "Clifford_torus_T2_in_S3",
          "Twistor_incidence_spinor_geometry",
          "U1_Hopf_principal_bundle",
          "SU2_Spin3_unit_quaternion_double_cover",
          "SO3_orientation_frame_reduction",
          "Pin3_Spin3_chirality_split",
          "Clifford_geometries_Cl3_Cl6",
          "Hybrid_Hopf_Spin_Twistor_Clifford_reduction_graph"
        ],
        "pass": true
      },
      "all_layer_rows_recomputed_without_bloch_adapter": {
        "layer_row_count": 44,
        "layers": [
          "L0",
          "L1",
          "L2",
          "L3",
          "L4",
          "L5",
          "L6",
          "L7",
          "L8"
        ],
        "pass": true
      },
      "all_tools_worked_one_by_one": {
        "pass": true,
        "tool_count": 15,
        "tool_order": [
          "pytorch",
          "quimb",
          "cotengra",
          "opt_einsum",
          "pyg",
          "rustworkx",
          "xgi",
          "toponetx",
          "gudhi",
          "clifford",
          "sympy",
          "z3",
          "cvc5",
          "e3nn",
          "geomstats"
        ]
      },
      "derived_qit_entropy_family_survives": {
        "min_log_negativity": 0.07495133483954947,
        "min_mutual_information": 0.016930405817572186,
        "pass": true
      },
      "pyg_message_gap_survives": {
        "min_message_gap": 1.8594077825546265,
        "pass": true
      },
      "scale_8_16_32_64_preserved": {
        "pass": true,
        "site_counts": [
          8,
          16,
          32,
          64
        ]
      },
      "spinor_network_entanglement_survives": {
        "min_entanglement_gap_vs_product_mps": 2.0794413089752197,
        "pass": true
      }
    },
    "source": "system_v5/ops/formal_scouts/sim_tool_by_tool_layer_g_structure_geometry_depth_probe.py",
    "status": {
      "all_pass": true,
      "carrier_layer": "torch-native spinor network with MPS, PEPS2D, PEPS3D, PyG, explicit Hopf S3->S2 features, and QIT entropy-family readouts",
      "classification": "formal_scout",
      "codomain_or_output": "ordered per-tool depth rows with coverage, pass/fail, controls, and blocked consumers",
      "domain": "all current layer rows plus standalone G-structure candidate rows at 8/16/32/64 sites",
      "finite_map": "ToolDepth : (tool, layer row, G-structure row, geometry surface, site count, carrier/action/readout/control) -> tool-specific depth receipt",
      "geometry_layer": "L0-L8 layer geometries plus S3/S2/Hopf/nested-Hopf-tori/Clifford-tori/twistor/G-structure candidates",
      "next_admissible_step": "continue with deeper per-tool packets: choose one tool/function row and deepen it across the same layer/G/geometry estate, or write a blocker; do not open layer embedding or stacking from this receipt alone",
      "peps3d_embedding": "PEPS3D bond-4 carrier view recomputed for every layer and G-structure row",
      "promotion_allowed": false,
      "quaternion_action": "Cl3 bivector quaternion units and SU2/Spin3 double-cover rows included in tool and G-structure coverage",
      "sim_execution_kind": "nonclassical",
      "spinor_state": "torch.complex128 two-component spinors; QIT density states derived only for readouts"
    },
    "summary": {
      "all_pass": true,
      "elapsed_seconds": 25.194104,
      "g_structure_count": 12,
      "g_structure_row_count": 48,
      "geometry_surface_count": 15,
      "layer_count": 9,
      "layer_row_count": 44,
      "max_sites": 64,
      "min_entanglement_gap_vs_product_mps": 2.0794413089752197,
      "min_log_negativity": 0.07495133483954947,
      "min_mutual_information": 0.016930405817572186,
      "min_pyg_message_gap": 1.8594077825546265,
      "peps2d_bond_dim": 4,
      "peps3d_bond_dim": 4,
      "selected_official_g_structure": null,
      "site_counts": [
        8,
        16,
        32,
        64
      ],
      "tool_count": 15,
      "tool_rows_passed": 15
    },
    "tool_ablations": {
      "clifford": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove clifford function_surface: Clifford Cl3 quaternion units and Cl6 basis"
      },
      "cotengra": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove cotengra function_surface: cotengra contraction-cost search"
      },
      "cvc5": {
        "claim_delta": "map_unprovable",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove cvc5 function_surface: cvc5 all-row and downstream-lock cross-check"
      },
      "e3nn": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove e3nn function_surface: e3nn SO3 norm equivariance over explicit Hopf S2 vectors"
      },
      "geomstats": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove geomstats function_surface: geomstats S3 and S2 geodesic distances"
      },
      "gudhi": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove gudhi function_surface: GUDHI filtration over entropy/carrier-gap rows"
      },
      "opt_einsum": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove opt_einsum function_surface: opt_einsum endpoint contraction signatures"
      },
      "pyg": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove pyg function_surface: PyG GCNConv finite carrier message gap"
      },
      "pytorch": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove pytorch function_surface: torch autograd over relative spinor phase"
      },
      "quimb": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove quimb function_surface: quimb PEPS2D/PEPS3D construction"
      },
      "rustworkx": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove rustworkx function_surface: rustworkx DAG plus cycle-control"
      },
      "sympy": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove sympy function_surface: SymPy exact Hopf and Clifford-torus identities"
      },
      "toponetx": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove toponetx function_surface: TopoNetX cell-complex coverage"
      },
      "xgi": {
        "claim_delta": "claim_fails",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove xgi function_surface: XGI hyperedge coverage over tool/layer/G/geometry"
      },
      "z3": {
        "claim_delta": "map_unprovable",
        "non_vacuous": true,
        "pass": true,
        "stub_action": "remove z3 function_surface: z3 coverage and impossible shortcut order gate"
      }
    },
    "tool_rows": [
      {
        "function_surface": "torch autograd over relative spinor phase",
        "pass": true,
        "tool": "pytorch"
      },
      {
        "function_surface": "quimb PEPS2D/PEPS3D construction",
        "pass": true,
        "tool": "quimb"
      },
      {
        "function_surface": "cotengra contraction-cost search",
        "pass": true,
        "tool": "cotengra"
      },
      {
        "function_surface": "opt_einsum endpoint contraction signatures",
        "pass": true,
        "tool": "opt_einsum"
      },
      {
        "function_surface": "PyG GCNConv finite carrier message gap",
        "pass": true,
        "tool": "pyg"
      },
      {
        "function_surface": "rustworkx DAG plus cycle-control",
        "pass": true,
        "tool": "rustworkx"
      },
      {
        "function_surface": "XGI hyperedge coverage over tool/layer/G/geometry",
        "pass": true,
        "tool": "xgi"
      },
      {
        "function_surface": "TopoNetX cell-complex coverage",
        "pass": true,
        "tool": "toponetx"
      },
      {
        "function_surface": "GUDHI filtration over entropy/carrier-gap rows",
        "pass": true,
        "tool": "gudhi"
      },
      {
        "function_surface": "Clifford Cl3 quaternion units and Cl6 basis",
        "pass": true,
        "tool": "clifford"
      },
      {
        "function_surface": "SymPy exact Hopf and Clifford-torus identities",
        "pass": true,
        "tool": "sympy"
      },
      {
        "function_surface": "z3 coverage and impossible shortcut order gate",
        "pass": true,
        "tool": "z3"
      },
      {
        "function_surface": "cvc5 all-row and downstream-lock cross-check",
        "pass": true,
        "tool": "cvc5"
      },
      {
        "function_surface": "e3nn SO3 norm equivariance over explicit Hopf S2 vectors",
        "pass": true,
        "tool": "e3nn"
      },
      {
        "function_surface": "geomstats S3 and S2 geodesic distances",
        "pass": true,
        "tool": "geomstats"
      }
    ]
  },
  "repo_gates": {
    "nonclassical_gate": [
      "F01 finite carrier/probe/operator/path set",
      "N01 noncommuting/order-sensitive operation/control",
      "explicit domain/codomain finite map",
      "finite PEPS3D carrier from start",
      "torch-native spinor or spinor-derived density",
      "quaternion invariant when quaternion language used",
      "negative/control condition",
      "receipt path",
      "blocked downstream consumers"
    ],
    "tool_stage_order": "micro tool/function receipts -> tool-lego fit -> tool-tool coupling -> lego rows -> scientific lego couplings -> bridge/axis claims",
    "user_boundary": "Each layer and each G-structure/geometry candidate is supposed to remain a separate sim surface before official stacking/selection."
  },
  "status_artifact": {
    "coverage": {
      "g_structure_candidates": 12,
      "g_structure_rows": 48,
      "geometry_surfaces": 15,
      "layer_rows": 44,
      "layers": 9,
      "max_sites": 64,
      "peps2d_bond_dim": 4,
      "peps3d_bond_dim": 4,
      "site_counts": [
        8,
        16,
        32,
        64
      ],
      "tool_count": 15,
      "tool_rows_passed": 15
    },
    "current_truth": "A cross-cutting tool-by-tool depth scout now works each listed tool through the current independent layer rows, standalone G-structure candidates, and geometry surfaces at 8/16/32/64 sites. This is not official G-structure selection, layer embedding, stacking, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics/gravity, or final manifold admission.",
    "fresh_validation": {
      "dependency_validation": {
        "bond4_layer_tool_ablation_receipts_fresh_rerun": {
          "all_pass": true,
          "receipt_count": 9
        },
        "full_spinor_layer_receipts_fresh_rerun": {
          "all_pass": true,
          "receipt_count": 9
        },
        "g_structure_candidate_space_fresh_rerun": true
      },
      "lint_sim_contract": {
        "checked": 1,
        "violation_total": 0
      },
      "validate_formal_scout_results_fresh_rerun": {
        "all_pass": true,
        "fresh_rerun": true
      }
    },
    "measured_floor": {
      "min_entanglement_gap_vs_product_mps": 2.0794413089752197,
      "min_log_negativity": 0.07495133483954947,
      "min_mutual_information": 0.016930405817572186,
      "min_pyg_message_gap": 1.8594077825546265
    },
    "next_admissible_packets": [
      {
        "packet": "tool_depth_pytorch_autograd_spinor_phase_packet",
        "purpose": "deepen PyTorch/autograd from one global relative-phase witness into per-layer and per-G-structure gradient maps, left/right Weyl separation, and resource-fenced 8/16/32/64 stress.",
        "stop_condition": "fresh rerun passes or a concrete resource/blocker artifact is written"
      },
      {
        "packet": "tool_depth_quimb_cotengra_peps2d_peps3d_packet",
        "purpose": "deepen quimb/cotengra from construction and cost witnesses into independent PEPS2D and PEPS3D contraction/readout variants over every layer and G-structure candidate.",
        "stop_condition": "fresh rerun passes or the exact contraction/resource ceiling is recorded"
      },
      {
        "packet": "tool_depth_clifford_twistor_hopf_packet",
        "purpose": "deepen Clifford/SymPy geometry rows for Hopf fibration, nested Hopf tori, Clifford tori, twistor incidence, Spin/SU/Pin alternatives, and hybrid reductions without Bloch-sphere adapters.",
        "stop_condition": "fresh rerun passes or the first algebraic map that cannot be made finite is recorded"
      },
      {
        "packet": "tool_depth_topology_hypergraph_persistence_packet",
        "purpose": "deepen PyG, rustworkx, XGI, TopoNetX, and GUDHI from coverage witnesses into graph/hypergraph/cell/persistence controls over every layer and G-structure candidate.",
        "stop_condition": "fresh rerun passes or the exact topology/control mismatch is recorded"
      },
      {
        "packet": "tool_depth_e3nn_geomstats_orientation_packet",
        "purpose": "deepen e3nn/geomstats orientation checks into S3/S2/SO3 distance/equivariance families over representative and adversarial spinor rows.",
        "stop_condition": "fresh rerun passes or a concrete orientation/equivariance blocker is written"
      }
    ],
    "path": "system_v5/ops/formal_scouts/tool_by_tool_layer_g_structure_geometry_depth_status_20260528.json",
    "required_boundary": {
      "Axis0": "blocked",
      "Holodeck/FEP": "blocked",
      "Xi/Phi0": "blocked",
      "final_manifold_admission": "blocked",
      "flux": "blocked",
      "layer_embedding_in_g_structure": "blocked",
      "no_bloch_adapter": true,
      "official_g_structure_selection": "blocked",
      "physics/gravity": "blocked",
      "qit_entropy_is_derived_readout_not_primary_object": true,
      "stacking": "blocked",
      "torch_native_spinors": true
    },
    "route_truth": {
      "codex_native_subagents": "not_run_in_this_packet",
      "external_model_receipts": "not_run_in_this_packet",
      "reason": "This packet used local formal scout execution and validators. It is an execution receipt, not a full Wizard plurality receipt.",
      "wizard_v4_2_max_assembly": "partial_controller_local_only"
    }
  },
  "user_request": "Audit current tool-by-tool layer/G-structure/geometry depth work with Gemini, Opus, and Grok; use models deeply and broadly; determine whether it is on track, where it is shallow/drifted, and what should run next."
}
