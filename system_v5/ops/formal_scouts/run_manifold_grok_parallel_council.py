#!/usr/bin/env python3
"""Run a bounded MMM-loaded Grok fanout over manifold follow-up lanes."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import pathlib
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from provider_mmm_prompt import build_mmm_prompt_block


ROOT = pathlib.Path(__file__).resolve().parent
OUT_DIR = ROOT / "provider_receipts"
MODEL = "grok-4.3"
ENDPOINT = "https://api.x.ai/v1/chat/completions"

COMMON_MINI_IDS = [
    "failure.premortem_council",
    "failure.falsifier_council",
    "failure.loophole_auditor_council",
    "follow_up.next_move_selector",
    "follow_up.lane_council",
    "follow_up.compile_gate_council",
    "premortem.likely_failure",
    "premortem.dangerous_failure",
    "premortem.hidden_assumption",
    "premortem.sim_evidence_corruption",
    "voice.hume",
    "voice.feynman",
    "voice.popper",
    "voice.pushback",
    "voice.factory",
    "voice.strategy",
    "voice.systems",
    "expert.domain_specialist",
    "expert.standard_checker",
    "lane.direct",
    "lane.alternative",
]

FACTS = """Indexed local receipt facts to use as bounded evidence boundaries; provider must not treat this prompt as a fresh validation:
- Formal-scout source/result estate: 331 sources and 331 result receipts.
- formal_scout_readiness_index: validator_pass_count=316, formal_scout_validator_fail_count=14, preserved_validator_fail_count=14, actionable_validator_fail_count=0, non_formal_boundary_count=1, readme_missing_count=0, source_without_result_count=0, provider_receipts.validator_pass_fail=770/0, provider_receipts.strict_live_pass_fail=615/155.
- sim_estate_integration_index rows from the indexed controller summary: manifold=285, PEPS/PEPS3D/MPS=98, Axis0=152, basin=151, auto_LiRPA/le-wm=36.
- Current tool-role gate: 188 scanned nonclassical/source-native result surfaces, 178 tool_role_candidate rows, and 10 blocked_result_not_all_pass rows preserved as nonclearance evidence.
- Current NumPy quarantine gate: 16 NumPy-pattern source files total, 0 hard source quarantines, 0 review-required surfaces, 15 reviewed NumPy-bearing boundary files preserved as nonclassical-claim blocked, 1 quarantine-scanner self-hit / legacy-baseline boundary file separate, and 0 receipt hard quarantines.
- system_v5/grok_sim has 2502 proposal/process files in the current sim-estate index. It is proposal and failure-pattern mining until translated into v5 formal scouts.
- /tmp/engine_v2 has 275 scratch files. It is scratch/council/provider routing estate, not canonical sim evidence.
- Later chronological repair-log bullets preserve older local count fragments, including older NumPy hard-quarantine, receipt, and tool-role counts. Treat every rolling NumPy/tool-role count in those bullets as historical repair-log context only; the current NumPy/readiness/tool-role status is the fixed boundary above.
- Indexed receipt row: 8-qubit stage/topology/flux scout indexed result receipt reports: geometric_constraint_manifold_stage_flux_8qubit_pytorch_topology_probe all_pass=true, minimum_width_qubits=8, stage_count=8, topology graph nodes=8 edges=15, constraint_layer_applications=104, symbolic slot factorization=n_qubits * stage_count * constraint_layers, flux_erased_gap=1.1620295213386314, flux_reversed_gap=2.8426671937579564, reversed_order_gap=1.9438529684890409, topology_erased_gap=0.7710356978605593. PyTorch/rustworkx/sympy/z3 are load-bearing. It is formal_scout/nonpromotion.
- Indexed receipt row: 32-substage MPS scout indexed result receipt reports: single_chiral_thirty_two_substage_site_width_mps_topology_flux_probe all_pass=true with one MPS site per 8-stage x 4-substage pair, 32_site_carrier_executes, stage_substage_bijection, topology_flux_controls_separate, substage_grain_not_collapsed, valid_mps_boundary, and z3_noncollapse_unsat. It avoids dense 2**32 construction and uses PyTorch/rustworkx/sympy/z3 as load-bearing tools. It is formal_scout/nonpromotion.
- Indexed receipt row: PEPS3D64 slot closeout scout indexed result receipt reports: source_native_peps3d_64_site_slot_dynamics_closeout_probe all_pass=true with a 4x4x4 oriented nearest-neighbor topology/flux helper, 144 oriented edges, finite site flux drive, topology_flux_drives_64_site_slot_strength, zero-flux control, shuffled-topology-flux control, and identity control. Direct PEPS3D carrier numerics are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore. PEPS3D environment contraction and long-horizon claims remain blocked.
- Indexed receipt row: PEPS3D64 bond-dimension scout indexed result receipt reports: source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe all_pass=true across bond dimensions 2, 3, and 4. Direct PEPS3D carrier tensors, slot updates, and parameter counts are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through the imported EngineCore path.
- Indexed receipt row: PEPS3D48 regime-crossing scout indexed result receipt reports: source_native_peps3d_48_site_regime_crossing_probe all_pass=true over the 32/48/64 ladder. Direct carrier tensors, contraction arrays, norms, and parameter counts are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore/quimb paths. Historical rolling NumPy fragment at that older checkpoint: hard-quarantine sources were 19 and receipt NumPy-without-PyTorch count was 21.
- Indexed receipt row: PEPS3D52/56/60 regime-ladder scout indexed result receipt reports: source_native_peps3d_52_56_60_site_regime_ladder_probe all_pass=true. Direct carrier tensors, contraction arrays, EFE summaries, norms, and parameter counts are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore/quimb paths. Historical rolling NumPy fragment at that older checkpoint: hard-quarantine sources were 18 and receipt NumPy-without-PyTorch count was 20.
- Indexed receipt row: PEPS3D32/64 capacity scout indexed result receipt reports: source_native_peps3d_32_64_site_capacity_probe all_pass=true. Direct source-rank matrices, PEPS3D carrier tensors, contraction arrays, norms, and capacity signatures are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore/quimb paths. Historical rolling NumPy fragment at that older checkpoint: hard-quarantine sources were 17 and receipt NumPy-without-PyTorch count was 19.
- Indexed receipt row: source-native 32-site slot-contract replay scout indexed result receipt reports: source_native_slot_contract_32_site_multicarrier_replay_probe all_pass=true. Direct PEPS/PEPS3D carrier tensors, slot feature-rank matrix, contraction arrays, and contraction norm are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore/quimb paths. Historical rolling NumPy fragment at that older checkpoint: hard-quarantine sources were 16 and receipt NumPy-without-PyTorch count was 18.
- Indexed receipt row: source-native multicarrier 8/16/32-site scaling scout indexed result receipt reports: source_native_multicarrier_8_16_32_site_scaling_probe all_pass=true. Direct source-rank matrices, PEPS/PEPS3D carrier tensors, contraction arrays, norms, and parameter counts are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore/quimb paths. Historical rolling NumPy fragment at that older checkpoint: hard-quarantine sources were 15 and receipt NumPy-without-PyTorch count was 17.
- Indexed receipt row: source-native high-rank engine-history family scout indexed result receipt reports: source_native_high_rank_engine_history_family_probe all_pass=true. Direct source-history feature matrices, rank metrics, PEPS3D carrier tensors, contraction arrays, and contraction norms are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore/quimb paths. Historical rolling NumPy fragment at that older checkpoint: hard-quarantine sources were 14 and receipt NumPy-without-PyTorch count was 16.
- Indexed receipt row: source-native Hopf/FEP/IGT chirality prediction scout indexed result receipt reports: source_native_hopf_fep_igt_chirality_prediction_probe all_pass=true while keeping headline_hypothesis_survived=false. Direct density projection, dominant-spinor eigensolve, Hopf-base vector arithmetic, prediction errors, and bootstrap statistics are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore and holodeck_fep_engine.hopf_map. Historical rolling NumPy fragment at that older checkpoint: hard-quarantine sources were 13 and receipt NumPy-without-PyTorch count was 16.
- Indexed receipt row: Axis0 router basis-invariance portability scout indexed result receipt reports: axis0_router_basis_invariance_portability_probe all_pass=true. Direct permutation/sign-flip basis sampling and torch autograd witness are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through the imported 15-signature admission probe. Historical rolling NumPy fragment at that older checkpoint: hard-quarantine sources were 12 and receipt NumPy-without-PyTorch count was 16.
- Indexed receipt row: Axis0 router 15-signature admission portability scout indexed result receipt reports: axis0_router_admission_15_signature_portability_probe all_pass=true with TESTED_SET_PASS_WITH_CL_0_4_BOUNDARY preserved. Direct squared-norm tensors, triple-product masks, and portability summary metrics are now local PyTorch; direct source NumPy use is removed. Historical rolling NumPy counts for that older checkpoint are superseded by the refreshed index facts at the top of this prompt.
- Indexed receipt row: source-native active-inference strategy-policy scout indexed result receipt reports: source_native_active_inference_strategy_policy_probe all_pass=true, policy_count=16, selected_policy=E0:stage_window_03_04, no_manifold_selected_policy=E1:stage_window_05_06, EFE formula=risk + ambiguity - epistemic_gain. Direct density projection, Pauli observations, KL/entropy, softmax posterior, EFE scoring, and finite policy statistics are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore/imported chart constants. Historical rolling NumPy fragment at that older checkpoint: hard-quarantine sources were 10 and receipt NumPy-without-PyTorch count was 16; broader PyTorch/NumPy separation gate still reports 11 numpy_dominant receipts.
- Indexed receipt row: source-native engine boundary/path/FEP reconstruction scout indexed result receipt reports: source_native_engine_boundary_path_fep_reconstruction_probe all_pass=true, source_substage_count=64, compatible_refinement_count=256, fep_mean_gap=0.5119476491270742, mean_axis0_path_entropy_delta_abs=0.38910447858446073. Direct boundary density reconstruction, tomography distributions, feature matrices, centroid controls, and finite path statistics are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through the boundary/path helper and EngineCore adapters. Historical rolling fragments at that older checkpoint: NumPy hard-quarantine sources were 9, receipt NumPy-without-PyTorch count was 16, PyTorch/NumPy separation reported admissible=78, mixed=37, numpy_dominant=11, and tool-role gate reported surfaces=89, blocked=49, candidates=40; current fixed boundary is listed at the top of this prompt.
- Indexed receipt row: source-native engine transition-phase boundary/path/FEP scout indexed result receipt reports: source_native_engine_transition_phase_boundary_path_fep_probe all_pass=true, source_transition_records=64, mean_manifold_delta_norm=1.0760717965627729, mean_abs_axis0_path_entropy_delta=0.8092534060185717, selection_random_mean_gap=0.5064823817990793. Direct transition phase density statistics, path features, feature matrices, centroid controls, and ablation metrics are now local PyTorch; direct source NumPy use is removed; NumPy/SciPy are supportive/transitive only through EngineCore and boundary/path helper adapters. Historical rolling fragments at that older checkpoint: NumPy hard-quarantine sources were 8, receipt NumPy-without-PyTorch count was 16, PyTorch/NumPy separation reported admissible=79, mixed=36, numpy_dominant=11, and tool-role gate reported surfaces=89, blocked=48, candidates=41; current fixed boundary is listed at the top of this prompt.
- Indexed receipt row: high-N MPS engine boundary/path/FEP transport scout indexed result receipt reports: high_n_mps_engine_boundary_path_fep_transport_probe all_pass=true, n_qubits=8, max_mps_bond=12, mean_abs_axis0_path_entropy_delta=0.8947267133268829, fep_random_mean_gap=0.36315153998762584, min_control_signature_distance=1.591488034823774. Direct reduced-density contractions, boundary densities, signatures, controls, and MPS handoff statistics are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore/transport/quimb helper adapters. Historical rolling fragments at that older checkpoint: NumPy hard-quarantine sources were 7, receipt NumPy-without-PyTorch count was 15, PyTorch/NumPy separation reported admissible=80, mixed=36, numpy_dominant=11, quimb_upstream=6, and tool-role gate reported surfaces=89, blocked=47, candidates=42; current fixed boundary is listed at the top of this prompt.
- Indexed receipt row: MPS local boundary/path/FEP scaling scout indexed result receipt reports: mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe all_pass=true, n_values=[8,16,32], max_mps_bond_by_n={8:16,16:16,32:14}, mean_abs_axis0_path_entropy_delta_by_n={8:0.9048760402659712,16:0.9359718272005046,32:0.9535871444759316}, min_control_signature_distance_by_n={8:0.524783504483155,16:0.3591085568973372,32:0.10821627254127433}. Direct boundary densities, signatures, controls, and finite statistics are now local PyTorch; direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore/transport/quimb helper adapters; dense handoff remains false. Historical rolling fragments at that older checkpoint: NumPy hard-quarantine sources were 6, receipt NumPy-without-PyTorch count was 14, PyTorch/NumPy separation reported admissible=81, mixed=36, numpy_dominant=11, quimb_upstream=5, and tool-role gate reported surfaces=89, blocked=46, candidates=43; current fixed boundary is listed at the top of this prompt.
- Indexed receipt row: source-native multicarrier subdense environment-contraction scout indexed result receipt reports: source_native_multicarrier_subdense_environment_contraction_probe all_pass=true with local PyTorch MPS16/PEPS16/PEPS3D32/PEPS3D64 carrier tensors, pair-environment densities, signatures, controls, and finite statistics; site_counts={mps_16:16,peps_16:16,peps3d_32:32,peps3d_64:64}, axis0_zeroed_gaps={mps_16:0.08719325403908042,peps_16:0.056373823435927686,peps3d_32:0.02835790924510959,peps3d_64:0.012190850077691733}, scalar_mean_gaps={mps_16:0.03453339619346865,peps_16:0.018244282506571577,peps3d_32:0.007305975859938436,peps3d_64:0.007235937208876443}. Direct source NumPy use is removed; NumPy is supportive/transitive only through EngineCore/quimb helper adapters; quimb partial_trace, cotengra/opt_einsum, and z3 witnesses all pass. Historical rolling fragments at that older checkpoint: NumPy hard-quarantine sources were 5, receipt NumPy-without-PyTorch count was 13, PyTorch/NumPy separation reported admissible=82, mixed=36, numpy_dominant=11, quimb_upstream=4, and tool-role gate reported surfaces=89, blocked=45, candidates=44; current fixed boundary is listed at the top of this prompt.
- Indexed receipt row: full 13-layer both-chiral G-structure source-native composition scout indexed result receipt reports: full_thirteen_layer_active_g_structure_both_chiral_source_native_composition_probe all_pass=true, n_substages_joint=64, n_layers_above_threshold=13, log_neg_peak=0.7969351418737837, holonomy_total_diff=1.1656933196345447, berry_phase_nonzero_seeds=24, layer_disabled_diff=0.6252370162569503, single_chiral_log_neg_peak=0.0, random_history_mean_pairwise_bloch_distance=0.3316325918928686, z3_layers_carry_signal_unsat=true. Direct density algebra, RK4 Lindblad evolution, tensor-network bridge states, partial traces, Bloch readouts, eigensolves, and G-structure control metrics are now local PyTorch; direct source NumPy and SciPy use are removed; NumPy is supportive/transitive only through EngineCore/quimb helper adapters. Historical rolling fragments at that older checkpoint: NumPy hard-quarantine sources were 4, receipt NumPy-without-PyTorch count was 12, PyTorch/NumPy separation reported admissible=83, mixed=36, numpy_dominant=11, quimb_upstream=3, and tool-role gate reported surfaces=89, blocked=44, candidates=45; current fixed boundary is listed at the top of this prompt.
- Indexed receipt row: boundary/path/FEP helper scout indexed result receipt reports: holographic_boundary_path_ensemble_axis0_fep_selection_probe all_pass=true, sim_execution_kind=nonclassical, axis0_path_entropy_delta=-1.3924705064055671, axis0_correlation_diversity_delta=-0.014805758062955476, fep_selection_gap=0.32850406694434964, interior_spread=0.2777756077222097, max_boundary_gap=5.569462030903819e-16, min_control_boundary_gap=0.5029384103510988. Direct finite density matrices, partial traces, spectra, KL, Kraus histories, and path/FEP statistics are now local PyTorch; NumPy is supportive/transitive adapter compatibility only; NetworkX/GUDHI/Z3 remain load-bearing. Importer sims mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe, high_n_mps_engine_boundary_path_fep_transport_probe, source_native_engine_boundary_path_fep_reconstruction_probe, and source_native_engine_transition_phase_boundary_path_fep_probe all indexed result receipt report true against the PyTorch helper. Historical rolling fragments at that older checkpoint: NumPy hard-quarantine sources were 3, receipt NumPy-without-PyTorch count was 11, PyTorch/NumPy separation reported admissible=84, mixed=36, numpy_dominant=10, quimb_upstream=3, and tool-role gate reported surfaces=89, blocked=44, candidates=45; current fixed boundary is listed at the top of this prompt.
- Indexed receipt row: Axis0 branch-closure guards indexed result receipt report: axis0_path_entropy_branch_closure_probe all_pass=true with sim_execution_kind=nonclassical and PyTorch load-bearing finite vector/numeric witness checks; path_entropy status remains blocked_diagnostic_only_schedule_confound_proxy. axis0_holographic_boundary_branch_closure_probe all_pass=true with PyTorch load-bearing finite vector/numeric blocker checks; holographic_boundary_interior_reconstruction status remains blocked_diagnostic_only_boundary_interior_reconstruction_proxy. Direct source NumPy use is removed from both guards; promotion_allowed remains false.
- Indexed receipt row: singular lego-wired tool-fit blocker reruns with direct source NumPy removed and Axis0 candidate aggregation/statistics moved to local PyTorch. It remains intentionally validator-red: classification=tool_lego_fit_probe, all_pass=false, blockers are v1 ablation not remove-and-rerun per lego, cycle-level autograd remains severed at engine_core.py:561, and HBI remains blocked by KL gap below floor. This is cleanup/quarantine evidence, not promotion.
- NumPy quarantine slice is currently closed for active hard quarantine: hard_quarantine_count=0, review_required_count=0, receipt hard quarantine count=0. Fifteen reviewed NumPy-bearing boundary files remain nonclassical-claim blocked rather than promoted; remaining red/non-formal rows stay preserved as blocker evidence.
- Indexed receipt row: repaired topology-coupled layer-order and row-count falsifier indexed result receipt reports: topology_coupled_layer_order_and_row_count_falsifier_probe all_pass=true, companion_pass=12/12, reversal/scramble/inflation/deflation all separate under order-sensitive XGI ordered-triple hashes plus TopoNetX orientation sums. This closes the old reversal-blind topology blocker without promoting beyond formal-scout scope.
- Indexed receipt row: PEPS3D size-normalized environment scaling scout indexed result receipt reports: lirpa_peps3d_size_normalized_environment_scaling_probe all_pass=true, sim_execution_kind=nonclassical, local size-normalized PEPS3D32/PEPS3D64 signal survives honest denominator discipline, and stale local NumPy dependency is removed; upstream compressed-summary status is recorded explicitly.
- Indexed receipt row: Weyl holonomy/MPS curvature transport scout indexed result receipt reports: weyl_holonomy_mps_curvature_transport_probe all_pass=true, sim_execution_kind=nonclassical, local connection algebra, holonomy, MPS tensor updates, and contraction numerics are now PyTorch load-bearing while quimb/cotengra/opt_einsum, SymPy, Z3, and source-native engine histories remain load-bearing.
- Indexed receipt row: PEPS3D64 no-dense environment/topology/flux scout indexed result receipt reports: peps3d_64_site_no_dense_environment_topology_flux_probe all_pass=true with 64 sites, 144 oriented nearest-neighbor edges, max_observed_tensor_numel=128, max_observed_matrix_elements=448, and controls for zero flux, shuffled topology, scalar/summary-only projection, 8-site collapse, and identity/no environment. PyTorch/quimb/cotengra/rustworkx/sympy/z3 are load-bearing; no dense 2**64 state or full dense environment is constructed.
- Indexed receipt row: direct le-wm training/checkpoint microcycle scout indexed result receipt reports: lewm_training_checkpoint_microcycle_probe all_pass=true, directly imports /Users/joshuaeisenhart/GitHub/le-wm/module.py and uses ARPredictor.forward, loss.backward, state_dict, and load_state_dict as load-bearing surfaces. It rejects shuffled target/branch, frozen/no-training, and scalar/import-only controls; PyTorch and z3 are load-bearing; no checkpoint file or world-model claim is promoted.
- Indexed receipt row: graph/proof topology-persistence semantic coupling scout indexed result receipt reports: graph_proof_topology_persistence_semantic_coupling_probe all_pass=true with 8 rows, 7 scout_level semantic rows, and 1 killed row-count-only control. rustworkx, GUDHI, z3, cvc5, and SymPy are load-bearing; TopoNetX and XGI are supportive. It requires label-scramble/storage invariance and edge-rewire variance for the same semantic edge/order claim.
- Indexed receipt row: variable LiRPA policy-bound scaling scout: lirpa_policy_bound_variable_qubit_scaling_probe all_pass=true and robust_scaling_admission=admitted_finite_robust_scaling. Current site-count families are MPS=[8,16,32], PEPS=[9,16,25] from 3x3/4x4/5x5 sheets, and PEPS3D=[8,18,32,64] from 2x2x2/3x3x2/4x4x2/4x4x4 volumes. Do not use the stale 2x2 PEPS=4 framing; current PEPS scaling starts at 3x3=9 while 2x2x2=8 belongs to PEPS3D.
- Integrated suite minimum-width policy: integrated_constraint_manifold_suite_fresh_rerun_probe all_pass=true with minimum_nonclassical_width=8; the six-qubit sklearn-digits reservoir row multiqubit_reservoir_digits_6q is retained only as calibration_only real-data boundary evidence, not nonclassical maturity evidence.
- QIT engine work execution is now sim_constraint_manifold_qit_work_execution_probe.py / constraint_manifold_qit_work_execution_probe_results.json: all_pass=true, 64 QIT work records execute over a 2 sheets x 2 loop placements x 4 stages x 4 substages factorization, 16 unique stage-loop signatures, total_abs_work=0.47932229716889513, work_span=0.0318719376705609. PyTorch and rustworkx are load-bearing for density-state work execution and the 64-record DAG order witness.
- Live nested G-structure scout repair now indexed result receipt reports: clifford_sympy_geomstats_nested_g_structure_live_state_probe all_pass=true, total_live_states=32, classification=formal_scout, README indexed, tools include supportive PyTorch/EngineCore bridge plus load-bearing sympy, Cl(1,3), geomstats, and z3 graveyard controls. This is formal-scout readiness evidence only, not manifold promotion.
- Indexed receipt row: G-structure reduction/permutation scout indexed result receipt reports: g_structure_reduction_permutation_compatibility_probe all_pass=true, reversal gap=0.9959354898787369, adjacent swap gap=0.8468028105763468, min nonbaseline permutation gap=0.769788932110614, PyTorch load-bearing with sympy/rustworkx/geomstats support. It is order-sensitive finite evidence, not final G-structure promotion.
- Indexed receipt row: PyTorch PEPS3D nested-order substrate scout indexed result receipt reports: pytorch_peps3d_nested_order_substrate_probe all_pass=true, uses a 2x2x2 tensor substrate with a 13-layer operator schedule and rejects reversal, neighbor-shuffle, scalar projection, rank collapse, and edge-blind summary controls through PyTorch/rustworkx/sympy/z3/cvc5. It is a substrate formal scout only.
- Indexed receipt row: semantic graph edge-structure scout indexed result receipt reports: semantic_graph_edge_structure_falsifier_probe all_pass=true, rewired_output_distance=0.005681425794552067, holds node labels/semantic positions fixed while changing DAG edges, and blocks edge-blind row-count/sorted-sequence graph-proof overclaims.
- Indexed receipt row: direct le-wm/auto_LiRPA branch scout indexed result receipt reports: lewm_lirpa_direct_module_branch_sensitivity_probe all_pass=true, direct le-wm score=8.725e-06, identity=0.3851, shuffled=0.3053, scalar Axis0 projection=0.4036, LiRPA certified scalar-minus-vector gap=0.4025 at eps=0.002. This makes le-wm and auto_LiRPA load-bearing on the same transition, but remains formal_scout/nonpromotion.
- Indexed receipt row: orientation-sensitive topology scout indexed result receipt reports: topology_orientation_sensitive_layer_order_falsifier_probe all_pass=true, full reverse distinguished, orientation-erased readout remains reverse-blind as a control. The older topology_coupled_layer_order_and_row_count_falsifier stays validator-red as evidence of the old symmetric readout.
- Tool-manifest comprehension lint now indexed result receipt reports as a passing lint harness while preserving 107 upstream BLANKET_LB_COMPREHENSION findings as nonpromotion/hygiene backlog.
- Indexed receipt row: Axis0 15-signature admission portability scout indexed result receipt reports: axis0_router_admission_15_signature_portability_probe all_pass=true; fep_gradient_polarity and correlation_diversity_derivative are 14/15, retrocausal_many_futures_policy_scoring is 15/15, Cl(0,4) is the retained tested boundary, label=TESTED_SET_PASS_WITH_CL_0_4_BOUNDARY.
- Indexed receipt row: singular Axis0 cycle/path sensitivity ablation scout indexed result receipt reports: singular_lego_axis0_cycle_path_sensitivity_ablation_probe all_pass=true; active_min_delta=0.0013832279785517684, active_min_grad=5.911712395066628e-06, import_max_delta=0.0, path_entropy_status=blocked_degenerate_plateau, detached_autograd_blocked=true. It separates live sensitivity from import-only wiring while keeping path entropy blocked.
- Indexed receipt row: finite-fixture basin closure falsifier indexed result receipt reports: dynamic_basin_finite_fixture_closure_falsifier_probe all_pass=true; finite_fixture_status=closed_killed, open_fixture_remainder=false, countermodel_count=108, worst countermodel seed=2020, state_eps=0.018, operator_drift_eps=0.006, horizon=512, order_rms_gap=0.1987154483795166 versus EPS_ORDER_RMS=0.12.
- Indexed receipt row: multitool tool-group removal-sensitivity scout indexed result receipt reports: constraint_manifold_multitool_tool_group_removal_sensitivity_probe all_pass=true; load-bearing groups are carrier/tensor, topology/graph, proof/symbolic/SMT, and equivariant/neural; serialization is supportive. It directly attacks blanket load-bearing tool overclaims for the highest-risk multitool manifold row.
- Indexed receipt row: G2/Spin7 containment-direction scout indexed result receipt reports: g2_spin7_containment_direction_falsifier_probe all_pass=true; reverse_omega_gap=0.0, reverse_phi_gap=9.16515138991168, g2_survivor_count=8, spin7_term_count=14. It blocks reverse-containment overclaim and keeps directionality explicit.
- Indexed receipt row: nested operational assembly removal-sensitivity scout indexed result receipt reports: nested_constraint_manifold_operational_assembly_tool_group_removal_sensitivity_probe all_pass=true; tensor_carrier_l2_delta=1.0544298648602441, graph_order_l2_delta=25.02002850622411, proof_guard_l2_delta=1.0, supportive_serialization_noise_l2_delta=0.0. Load-bearing groups are tensor_carrier, graph_order, and proof_symbolic_guard.
- Indexed receipt row: source chiral-density multicarrier removal-sensitivity scout indexed result receipt reports: source_chiral_density_multicarrier_module_removal_sensitivity_probe all_pass=true; carrier/tensor delta=114.8719824573, chiral-density delta=6.9852028246, graph/order delta=27.2183761455, proof/symbolic delta=1.0, import-only control delta=0.0.
- Indexed receipt row: PEPS3D/LiRPA receipt-ablation boundary scout indexed result receipt reports: lirpa_peps3d_receipt_ablation_boundary_probe all_pass=true; direct auto_LiRPA bound engine, 8 sites, 12 edges, 13 layers, full nominal score=4.094352722167969 with bounds [4.072027683258057, 4.116677761077881], min control margin=0.2162151336669922. It remains formal_scout/nonpromotion.
- Indexed receipt row: basin countermodel family portability scout indexed result receipt reports: basin_countermodel_family_portability_probe all_pass=true; finite_fixture_status=open, 220/384 rows are countermodels but 164/384 row-level variants remain non-countermodels, every 96/96 family cell has at least one countermodel horizon. This blocks closure overclaim.
- Indexed receipt row: semantic G-structure layer-operator coupling scout indexed result receipt reports: g_structure_semantic_layer_operator_coupling_probe all_pass=true; adjacent semantic role swap gap=0.032311532692754275, full reverse semantic gap=0.29680938911505883, index-only relabel gap=0.0, label/storage scramble gap=0.0; PyTorch/z3/cvc5 load-bearing, sympy/clifford/geomstats supportive.
- Indexed receipt row: semantic-family G-structure permutation scout indexed result receipt reports: g_structure_semantic_family_permutation_falsifier_probe all_pass=true; thirteen layers, six semantic families, max intra-family swap gap=1.5011122659325205e-16, min inter-family swap gap=0.15826338785092378, semantic_family_distinction_gap=0.15826338785092364. It kills label-scramble, storage-reindex, row-count-only, and index-only controls with PyTorch/rustworkx/z3/cvc5 load-bearing.
- Indexed receipt row: graph/proof semantic coupling matrix scout indexed result receipt reports: graph_proof_tool_semantic_coupling_matrix_probe all_pass=true; 13 matrix rows, killed=2, open=1, scout_level=10; killed_label_or_row_count_count=2, scout_level_edge_sensitive_count=9; load-bearing tools rustworkx, PyTorch, z3, cvc5, sympy; supportive networkx, XGI, TopoNetX, GUDHI, PyG.
- Indexed receipt row: Axis0 admitted-candidate vector-bundle ablation scout indexed result receipt reports: axis0_admitted_candidate_vector_bundle_ablation_probe all_pass=true; all three admitted candidates survive, min_component_grad_norm=0.16254655207865212, min_drop_axis_gap=4.660646117174995, scalar_projection_gap=3.7867963486105434, zero_axis_gap=10.243875525801977; path_entropy and HBI remain blocked, upstream_scalar_actuator_repaired=false.
- Indexed receipt row: direct LiRPA/le-wm vs Axis0-control falsifier indexed result receipt reports: lirpa_lewm_load_bearing_vs_axis0_control_falsifier_probe all_pass=true; direct auto_LiRPA and direct local le-wm both load-bearing in the same Axis0 routing/control decision; no-LiRPA L2=0.0034539704211056232, no-le-wm L2=0.017553796991705894, no-both L2=0.020169202238321304, ornamental-score-only matches no-both exactly and differs from baseline, certified scalar-lower-minus-vector-upper gap=0.10595224797725677 at eps=0.0025.
- Indexed receipt row: dynamic cross-track finite-fixture closure scout indexed result receipt reports: dynamic_cross_track_finite_fixture_closure_falsifier_probe all_pass=true while finite_fixture_status=open/open_row_level_remainder; 288 rows, 120 countermodels, 168 non-countermodel rows, worst countermodel vector_track_rms_gap=0.20328886806964874. It kills real convergence and blocks basin promotion without pretending closure.
- Current preserved formal-scout validator-red rows: 14 total, covering persistence-feature underperformance, ten stale/noncovering EngineCore finite-boundary quarantine receipts, failed XGI higher-order coupling, and two torch-readout reservoir counterevidence receipts. Grok/legacy NumPy quarantine is not a current validator-red row; the current audit reports zero linked admitted NumPy-blocked evidence rows while preserving quarantined proposal/baseline evidence. Current non-formal boundary: singular_lego_wired_axis0_plural_manifold_engine remains a tool-lego-fit boundary row, not a formal-scout pass.
- Hardened root chart-invariance scout: root_manifold_g_structure_holonomy_chart_invariance_probe all_pass=true, root_object=geometric_constraint_manifold, axis0_pass_condition=false, chart_count=5, phase_count=3, min_basin_gap=0.3132355213165283, max_basin_cosine=0.9999511241912842, min_flux_delta=0.02338375151157379, min_holonomy_gap=0.000056147685991032116, g_structure_schedule_family_count=3, auto_LiRPA separation_margin=0.02899661660194397, le-wm relative_loss_advantage=0.9766726493835449. It now includes runtime-data graph/PyG chart-ablation, data-gated hypergraph/simplicial/persistence checks, all-chart SymPy derivative comparison, all-chart Clifford/geomstats/e3nn checks, min-cosine z3/cvc5 arithmetic coverage, rejects gauge-equivalent/symmetric/folded controls, and remains formal_scout/nonpromotion.
- Indexed receipt row: semantic graph/proof label-scramble falsifier: semantic_graph_proof_label_scramble_falsifier_probe all_pass=true, consumes green graph-order, layer-name-blindness, and G-structure semantic-order receipts; label_scramble_distance=0.0, storage_reindex_distance=0.0, semantic_order_scramble_distance=0.18629670783079982, z3/cvc5 cross_solver_agree=true. It blocks display-label, storage-index, and row-count-only graph-proof overclaims.
- Indexed receipt row: long-horizon basin falsifier: dynamic_basin_long_horizon_perturbed_convergence_falsifier_probe all_pass=true over 30 seeds x 3 initial families x 2 perturbation classes x horizons 64/128/256/512; basin_admission_status=blocked and current_real_convergence_claim_status=killed by solver_disagreement_proxy_exceeds_eps. It is blocker execution, not basin maturity.
- Previous deep root scout: deep_geometric_ratchet_dynamic_tensor_network_basin_probe all_pass=true with six nesting depths, constant exploration, increasing constraint pressure, order-sensitive dynamic PyTorch tensor-network readouts, varying G-structure pressure, two similar asymmetric flux-separated sheets, auto_LiRPA, le-wm, and graph/topology/geometry/proof tools. Axis0 is excluded from pass conditions.
- Indexed receipt row: dynamic falsifier: dynamic_manifold_stability_cross_track_lirpa_falsifier_probe all_pass=true, current_real_convergence_claim_status=killed, finite_fixture_status=open, cross_track_divergence=1.6890580774828772, track_a_vs_b_max_coh_gap=0.3016344264689347, final_vector_vs_scalar_state_gap=0.051966845989227295, horizons=[64,128,256], enforcement_orders=[evolve_then_enforce,enforce_then_evolve].
- Indexed receipt row: Axis0 vector fixture: axis0_vector_bundle_thirteen_shell_pytorch_peps3d_lirpa_noncollapse_probe all_pass=true, shell_count=13, axis0_dimension=3, load-bearing tools=[pytorch, auto_LiRPA, torch_geometric, rustworkx, z3, cvc5], load-bearing external module=[le_wm_module], rejects scalar projection, zero-axis, drop-one, and blocked candidates; it is not an upstream scalar actuator repair.
- Axis0 state: admitted candidates are fep_gradient_polarity, correlation_diversity_derivative, retrocausal_many_futures_policy_scoring. Blocked candidates are path_entropy and holographic_boundary_interior_reconstruction. The upstream path now uses operator-aware vector-local drive; the remaining blocker is per-candidate control-family degeneracy, not a scalar-only projection diagnosis.
- Indexed receipt row: operator-local vector actuator improvement scout indexed result receipt reports: axis0_operator_local_vector_actuator_degeneracy_break_probe all_pass=true as an improvement probe against the current upstream path, not a final repair proof. It keeps blocked candidates inert, preserves scalar-mean separation, and improves control-family max-correlation for two of the three admitted candidates relative to the current upstream drive-control receipt, but does not yet clear an absolute low-correlation ceiling.
- Indexed receipt row: carrier-family-decoupled operator-local vector actuator scout indexed result receipt reports: axis0_operator_local_vector_actuator_family_decoupling_probe all_pass=true as a stronger improvement probe over the live upstream path. It keeps blocked candidates inert, preserves scalar-mean separation, improves control-family max-correlation for two admitted candidates again, and increases mean improvement over the first operator-local probe, but still does not clear an absolute low-correlation ceiling for full upstream actuator admission.
- Indexed receipt row: foundation reset gate indexed result receipt reports: two_root_constraint_attractor_basin_foundation_gate_probe all_pass=true as a blocking audit, not a basin proof. It identifies F01 finitude and N01 noncommutation as the two root constraints, finds executable_root_receipt_count=0 for current manifold/basin receipts, keeps root_basin_admission_status=blocked, and sets current_real_attractor_basin_convergence_claim_status=killed_or_unproven. Axis0 is downstream and should not be the primary salience target until the root manifold and Axis1-6 substrate are better founded.
- Current promotion boundary: all named manifold/Axis0/basin receipts are formal_scout with promotion_allowed=false unless later promoted by an explicit promotion manifest and current validators; provider output is proposal/audit only.
- Known tool gaps: the current indexed formal-scout gate reports zero linked admitted NumPy-blocked evidence rows, but this is still a gate/result fact rather than a proof theorem; the foundation gap is now upstream of Axis0: F01/N01 must become executable pass/ablation predicates for root-manifold attractor-basin convergence. quimb/cotengra substrate and environment-contraction capability still need bounded capability scouts; graph/proof tools need semantic coupling checks rather than row-count checks.
"""

GROUNDING_TARGETS = [
    "system_v5/evidence/sim_estate_integration_index.json",
    "system_v5/docs/SIM_ESTATE_INTEGRATION_INDEX.md",
    "system_v5/ops/MANIFOLD_WIZARD_OPERATION.md",
    "system_v5/ops/formal_scouts/results/root_manifold_g_structure_holonomy_chart_invariance_probe_results.json",
    "system_v5/ops/formal_scouts/results/deep_geometric_ratchet_dynamic_tensor_network_basin_probe_results.json",
    "system_v5/ops/formal_scouts/results/dynamic_manifold_stability_cross_track_lirpa_falsifier_probe_results.json",
    "system_v5/ops/formal_scouts/results/axis0_vector_bundle_thirteen_shell_pytorch_peps3d_lirpa_noncollapse_probe_results.json",
    "system_v5/ops/formal_scouts/results/integrated_nested_geometric_constraint_manifold_dynamic_tensor_network_probe_results.json",
    "system_v5/ops/formal_scouts/results/thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe_results.json",
    "system_v5/ops/formal_scouts/results/axis0_lewm_lirpa_pytorch_assembly_probe_results.json",
]


@dataclass(frozen=True)
class Lane:
    lane_id: str
    route_card: str
    council_role: str
    task: str


LANES = [
    Lane(
        "axis0_upstream_actuator",
        "grok.axis0_upstream_actuator_premortem",
        "failure.premortem_council+failure.falsifier_council",
        "Audit the smallest executable repair path from Axis0 vector-bundle fixture to upstream non-scalar actuation. Name the exact failure chain if scalar projection is accidentally treated as repaired. Return killed/open/survived finite-claim labels and one concrete next formal scout.",
    ),
    Lane(
        "dynamic_stability_horizon",
        "grok.dynamic_stability_horizon_audit",
        "failure.falsifier_council+follow_up.compile_gate_council",
        "Audit the dynamic_manifold_stability_cross_track_lirpa_falsifier result. Decide what follow-up is needed after current_real_convergence_claim_status=killed and finite_fixture_status=open. Focus on horizons, enforcement order, vector/scalar controls, trace/Choi/CE metrics, and what would keep the finite fixture open vs kill it.",
    ),
    Lane(
        "peps3d_tensor_substrate",
        "grok.peps3d_tensor_substrate_gap_audit",
        "decision.experts_council+failure.falsifier_council",
        "Audit where PEPS/PEPS3D is actually load-bearing and where quimb/cotengra substrate or environment-contraction capability gaps remain after the NumPy quarantine closure. Return the smallest PyTorch/PEPS3D or quimb/cotengra capability scout that would change the evidence map.",
    ),
    Lane(
        "graph_proof_semantics",
        "grok.graph_proof_semantic_gap_audit",
        "decision.experts_council+failure.loophole_auditor_council",
        "Audit z3, cvc5, sympy, Clifford, rustworkx, PyG, XGI, TopoNetX, and GUDHI integration. Identify which current predicates are semantic and which could still pass under label scramble or row-count substitution.",
    ),
    Lane(
        "g_structure_nesting_order",
        "grok.g_structure_nesting_order_audit",
        "decision.context_strategy+failure.falsifier_council",
        "Treat the geometric constraint manifold as an order-sensitive nested G-structure candidate. Audit the current 13-layer order and name the next semantic layer/operator check that would move beyond index-driven layer names.",
    ),
    Lane(
        "lirpa_lewm_branch_exploration",
        "grok.lirpa_lewm_branch_exploration_audit",
        "decision.move_selection+follow_up.lane_council",
        "Explore branches for using auto_LiRPA and le-wm in the manifold without ornamental execution. Rank branches that make LiRPA/le-wm load-bearing over dynamic tensor-network or Axis0-control behavior.",
    ),
    Lane(
        "basin_convergence_premortem",
        "grok.basin_convergence_premortem",
        "failure.premortem_council+voice.popper",
        "Premortem the attractor-basin evidence path. Assume the team again overclaims convergence six months from now. Identify the exact receipt misuse, early warning signs, and the one falsifier that should block the claim.",
    ),
    Lane(
        "followup_selector",
        "grok.manifold_followup_selector",
        "follow_up.next_move_selector+follow_up.compile_gate_council",
        "Select the next three automatic follow-up prompts after this loop. Each must be executable as a narrow formal scout or provider audit, with payoff, use condition, and stop/block condition. Suppress orchestration-only follow-ups.",
    ),
]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_lane_prompt(lane: Lane) -> tuple[str, dict[str, Any]]:
    mmm_block, metadata = build_mmm_prompt_block(
        route_card=lane.route_card,
        council_role=lane.council_role,
        mini_ids=COMMON_MINI_IDS,
    )
    prompt = f"""{mmm_block}

Mass-parallel Grok manifold council lane.

Authority boundary:
- This is external provider audit/proposal, not admitted local evidence.
- Local formal-scout receipts, validators, and Codex controller synthesis remain authority.
- Do not promote any claim. Return next executable scouts, falsifiers, blockers, and overclaim boundaries.
- Preserve the geometric constraint manifold as the root object.

{FACTS}

Lane id: {lane.lane_id}
Lane task:
{lane.task}

Return concise JSON-like sections:
- mmm_saliency_delta
- saliency_failure_mode
- lane_verdict
- evidence_used
- killed_or_blocked_claims
- smallest_next_executable_scout
- tool_or_manifold_gap
- overclaims_to_block
- stop_condition
"""
    return prompt, metadata


def provider_receipt(
    *,
    lane: Lane,
    status: str,
    proposal_text: str = "",
    blocked_reason: str = "",
    wizard_mmm: dict[str, Any],
    prompt_sha256: str,
    raw_response: Any = None,
) -> dict[str, Any]:
    live_api_proof = {}
    if proposal_text:
        live_api_proof = {
            "endpoint": ENDPOINT,
            "model": MODEL,
            "answer_sha256": _sha256(proposal_text),
        }
    return {
        "schema": "PROVIDER_PROPOSAL_RECEIPT_v1",
        "provider": "grok",
        "route": lane.route_card,
        "lane_id": lane.lane_id,
        "status": status,
        "classification": "provider_audit",
        "promotion_allowed": False,
        "evidence_allowed": False,
        "claim_ceiling": "Provider audit/proposal only. Local formal-scout receipts and validators remain authority.",
        "repo_grounding": {
            "targets": GROUNDING_TARGETS,
            "local_facts_embedded_in_prompt": True,
            "wizard_mmm_loaded_in_prompt": bool(wizard_mmm.get("mmm_loaded")),
        },
        "wizard_mmm": wizard_mmm,
        "prompt_sha256": prompt_sha256,
        "model": MODEL,
        "proposal_text": proposal_text,
        "blocked_reason": blocked_reason,
        "live_api_proof": live_api_proof,
        "raw_response": raw_response,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def run_lane(lane: Lane, *, timeout: float, stamp: str) -> pathlib.Path:
    prompt, wizard_mmm = build_lane_prompt(lane)
    prompt_sha256 = _sha256(prompt)
    key = os.environ.get("XAI_API_KEY")
    if not key:
        receipt = provider_receipt(
            lane=lane,
            status="blocked",
            blocked_reason="XAI_API_KEY not set",
            wizard_mmm=wizard_mmm,
            prompt_sha256=prompt_sha256,
        )
    else:
        try:
            raw = post_json(
                ENDPOINT,
                {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                {
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                },
                timeout,
            )
            text = raw["choices"][0]["message"]["content"]
            usage = raw.get("usage") or {}
            receipt = provider_receipt(
                lane=lane,
                status="completed",
                proposal_text=text,
                wizard_mmm=wizard_mmm,
                prompt_sha256=prompt_sha256,
                raw_response={"id": raw.get("id"), "model": raw.get("model"), "usage": usage},
            )
        except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            receipt = provider_receipt(
                lane=lane,
                status="blocked",
                blocked_reason=repr(exc),
                wizard_mmm=wizard_mmm,
                prompt_sha256=prompt_sha256,
            )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{stamp}_grok_{lane.lane_id}_parallel_manifold_audit.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    parser.add_argument("--lanes", nargs="*", default=[lane.lane_id for lane in LANES])
    args = parser.parse_args()

    lane_map = {lane.lane_id: lane for lane in LANES}
    selected = [lane_map[lane_id] for lane_id in args.lanes if lane_id in lane_map]
    unknown = [lane_id for lane_id in args.lanes if lane_id not in lane_map]
    if unknown:
        raise SystemExit(f"unknown lane ids: {', '.join(unknown)}")
    if not selected:
        raise SystemExit("no lanes selected")

    outputs: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = [executor.submit(run_lane, lane, timeout=args.timeout, stamp=args.stamp) for lane in selected]
        for future in concurrent.futures.as_completed(futures):
            outputs.append(str(future.result()))
            print(outputs[-1])
    print(json.dumps({"stamp": args.stamp, "count": len(outputs), "outputs": sorted(outputs)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
