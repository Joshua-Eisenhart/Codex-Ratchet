#!/usr/bin/env python3
"""Build the current tool -> function/API -> receipt matrix.

This is a receipt index, not an admission or promotion surface. It records the
fresh bounded tool-function wave and its exact claim ceiling.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "system_v5" / "evidence" / "tool_function_receipt_matrix.json"
OUT_MD = ROOT / "system_v5" / "docs" / "TOOL_FUNCTION_RECEIPT_MATRIX.md"


TARGETS: list[dict[str, Any]] = [
    {
        "tool": "pytorch",
        "function_api": "torch.autograd.grad/backward, torch.nn.Module, torch.matmul/tensor shape ops",
        "receipt": "system_v4/probes/a2_state/sim_results/pytorch_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["density_matrix_representability", "operator_family_fixture"],
    },
    {
        "tool": "pytorch",
        "function_api": "torch.autograd.grad(outputs, inputs, create_graph=True) first/second derivative fixture",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_pytorch_autograd_gradient_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["differentiable_constraint_micro", "entropy_gradient_fit"],
    },
    {
        "tool": "pytorch",
        "function_api": "torch.linalg.eigvalsh plus torch.autograd.grad entropy gradient over normalized 2x2 PSD density fixture",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_pytorch_density_entropy_gradient_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["density_matrix_representability", "entropy_gradient_fit"],
    },
    {
        "tool": "pytorch",
        "function_api": "torch complex tensor density construction and autograd.grad derivative readouts over Hopf-coordinate carrier variables",
        "receipt": "system_v4/probes/a2_state/sim_results/pytorch_hopf_fiber_base_density_gradient_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["declared_fiber_base_coordinate_readout_baseline", "differentiable_coordinate_readout_baseline"],
    },
    {
        "tool": "pytorch",
        "function_api": "torch complex tensors, density construction, Bloch readout, autograd.grad, and finite-difference checks over declared Hopf/Weyl fiber-base carrier coordinates",
        "receipt": "system_v4/probes/a2_state/sim_results/pytorch_hopf_weyl_fiber_base_gradient_readout_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "differentiable_density_readout_baseline",
        ],
    },
    {
        "tool": "pyg",
        "function_api": "torch_geometric.nn.GCNConv MessagePassing over Hopf-fiber edge_index",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_pyg_hopf_graph_deep_capability_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["graph_shell_geometry", "werner_local_structure"],
    },
    {
        "tool": "pyg",
        "function_api": "torch_geometric.nn.MessagePassing.propagate directed additive aggregation",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_e3nn_pyg_equivariance_under_mp_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["graph_cell_complex_geometry", "operator_family_fixture"],
    },
    {
        "tool": "pyg",
        "function_api": "torch_geometric.data.Data/Batch, MessagePassing.propagate, global_mean_pool over SymPy-derived graph fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/tool_integration_sympy_pyg_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["graph_symbolic_fit", "graph_shell_geometry"],
    },
    {
        "tool": "pyg",
        "function_api": "torch_geometric.data.Data/Batch, MessagePassing.propagate, global_mean_pool over TopoNetX Hasse graph fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/tool_integration_toponetx_pyg_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["topology_to_graph_fit", "cell_complex_geometry"],
    },
    {
        "tool": "pyg",
        "function_api": "torch_geometric.data.Data.validate and MessagePassing.propagate consuming exact NetworkX DiGraph node/edge fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_networkx_pyg_graph_roundtrip_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["graph_cell_handoff", "density_graph_carrier"],
    },
    {
        "tool": "networkx",
        "function_api": "networkx.DiGraph nodes/edges/predecessors as exact source graph for PyG Data handoff",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_networkx_pyg_graph_roundtrip_micro_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["graph_cell_handoff", "density_graph_carrier"],
    },
    {
        "tool": "networkx",
        "function_api": "networkx DiGraph/topological_sort/ancestors/descendants/transitive_reduction over Hopf receipt dependency DAG",
        "receipt": "system_v4/probes/a2_state/sim_results/networkx_hopf_receipt_dependency_reduction_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "finite_hopf_torus_fixture_controls_baseline",
            "receipt_dependency_dag_controls",
        ],
    },
    {
        "tool": "pyg",
        "function_api": "torch_geometric.data.Batch.from_data_list tensor concatenation, edge-index offsetting, batch vector, and ptr",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_pyg_batching_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["graph_batching_fixture", "graph_shell_geometry"],
    },
    {
        "tool": "qutip",
        "function_api": "qutip.basis, ket2dm, sigmax/sigmaz expectation",
        "receipt": "system_v4/probes/a2_state/sim_results/qutip_capability_results.json",
        "role": "bridge_useful",
        "depth": "load_bearing",
        "candidate_lego_targets": ["channel_cptp_map", "lindbladian_evolution"],
    },
    {
        "tool": "qutip",
        "function_api": "qutip.mesolve Lindblad open-system evolution",
        "receipt": "system_v4/probes/a2_state/sim_results/qutip_open_system_bridge_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["lindbladian_evolution", "channel_cptp_map"],
    },
    {
        "tool": "qutip",
        "function_api": "qutip entropy_vn / tensor density operators for mutual-information microfit",
        "receipt": "system_v4/probes/a2_state/sim_results/mutual_information_qutip_microfit_results.json",
        "role": "bridge_useful",
        "depth": "load_bearing",
        "candidate_lego_targets": ["mutual_information_measure", "density_matrix_object"],
    },
    {
        "tool": "qutip",
        "function_api": "qutip Qobj/ket2dm/expect/sigmax/sigmay/sigmaz density readouts over sampled Hopf-coordinate carrier paths",
        "receipt": "system_v4/probes/a2_state/sim_results/qutip_hopf_fiber_base_density_readout_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["declared_fiber_base_coordinate_readout_baseline", "density_object_path_readout_baseline"],
    },
    {
        "tool": "qutip",
        "function_api": "qutip Qobj.expm/qeye/sigmaz unitary phase-generator transport over a two-component density carrier",
        "receipt": "system_v4/probes/a2_state/sim_results/qutip_hopf_loop_phase_generator_density_transport_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_fiber_base_coordinate_readout_baseline",
            "density_operator_phase_generator_transport_baseline",
        ],
    },
    {
        "tool": "qutip",
        "function_api": "qutip Qobj ket carriers, density objects, dag/tr/expect, and Pauli readouts over declared Hopf/Weyl fiber-base loop paths",
        "receipt": "system_v4/probes/a2_state/sim_results/qutip_hopf_weyl_fiber_base_carrier_transport_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "density_object_path_readout_baseline",
        ],
    },
    {
        "tool": "qutip",
        "function_api": "qutip Qobj ket carriers, density objects, Pauli expectation readouts, and path metrics over Hopf/Weyl vertical fiber and horizontal base-lift paths",
        "receipt": "system_v4/probes/a2_state/sim_results/qutip_hopf_weyl_vertical_horizontal_density_transport_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "density_object_vertical_horizontal_transport_baseline",
        ],
    },
    {
        "tool": "qutip",
        "function_api": "qutip basis/ket2dm/projector/Qobj branch updates/sigmax/expect over two-level measurement-feedback-erasure calibration",
        "receipt": "system_v4/probes/a2_state/sim_results/qutip_two_level_measure_feedback_erasure_bounds_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "information_work_erasure_cycle_calibration_fixture",
            "two_level_density_branch_feedback_baseline",
        ],
    },
    {
        "tool": "qutip",
        "function_api": "qutip basis/ket2dm/destroy/mesolve/expect/entropy_vn over two-level thermal-reset erasure-floor calibration",
        "receipt": "system_v4/probes/a2_state/sim_results/qutip_two_level_thermal_reset_erasure_floor_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "thermal_reset_erasure_floor_calibration_fixture",
            "two_level_dissipative_reset_baseline",
        ],
    },
    {
        "tool": "qutip",
        "function_api": "qutip basis/ket2dm/expect/Qobj.tr over two-level thermal endpoint states and hot/cold Hamiltonian gap-change work/heat accounting",
        "receipt": "system_v4/probes/a2_state/sim_results/qutip_two_level_two_bath_gap_change_work_heat_bounds_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "work_heat_cycle_calibration_fixture",
            "two_level_density_work_heat_baseline",
        ],
    },
    {
        "tool": "qiskit",
        "function_api": "QuantumCircuit, Statevector, DensityMatrix, Operator expectation_value",
        "receipt": "system_v4/probes/a2_state/sim_results/qiskit_capability_results.json",
        "role": "bridge_useful",
        "depth": "load_bearing",
        "candidate_lego_targets": ["unitary_channel_map", "density_matrix_object"],
    },
    {
        "tool": "qiskit",
        "function_api": "qiskit Statevector, DensityMatrix, and Operator expectation_value density readouts over sampled Hopf-coordinate carrier paths",
        "receipt": "system_v4/probes/a2_state/sim_results/qiskit_hopf_fiber_base_density_readout_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["declared_fiber_base_coordinate_readout_baseline", "density_object_path_readout_baseline"],
    },
    {
        "tool": "qiskit",
        "function_api": "qiskit Statevector/DensityMatrix/Operator phase-generator transport over a two-component density carrier",
        "receipt": "system_v4/probes/a2_state/sim_results/qiskit_hopf_loop_phase_generator_density_transport_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_fiber_base_coordinate_readout_baseline",
            "density_operator_phase_generator_transport_baseline",
        ],
    },
    {
        "tool": "qiskit",
        "function_api": "qiskit Statevector, DensityMatrix, Operator expectation_value, and trace readouts over declared Hopf/Weyl fiber-base loop paths",
        "receipt": "system_v4/probes/a2_state/sim_results/qiskit_hopf_weyl_fiber_base_carrier_transport_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "density_object_path_readout_baseline",
        ],
    },
    {
        "tool": "qiskit",
        "function_api": "qiskit Statevector carriers, DensityMatrix objects, Operator expectation readouts, and path metrics over Hopf/Weyl vertical fiber and horizontal base-lift paths",
        "receipt": "system_v4/probes/a2_state/sim_results/qiskit_hopf_weyl_vertical_horizontal_density_transport_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "density_object_vertical_horizontal_transport_baseline",
        ],
    },
    {
        "tool": "qiskit",
        "function_api": "qiskit DensityMatrix/Operator projectors and unitary branch updates over two-level measurement-feedback-erasure calibration",
        "receipt": "system_v4/probes/a2_state/sim_results/qiskit_two_level_measure_feedback_erasure_bounds_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "information_work_erasure_cycle_calibration_fixture",
            "two_level_density_branch_feedback_baseline",
        ],
    },
    {
        "tool": "qiskit",
        "function_api": "qiskit DensityMatrix/Kraus/Operator over two-level amplitude-damping reset erasure-floor calibration",
        "receipt": "system_v4/probes/a2_state/sim_results/qiskit_two_level_kraus_reset_erasure_floor_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "thermal_reset_erasure_floor_calibration_fixture",
            "two_level_dissipative_reset_baseline",
        ],
    },
    {
        "tool": "qiskit",
        "function_api": "qiskit DensityMatrix/Operator over two-level thermal endpoint states and hot/cold Hamiltonian gap-change work/heat accounting",
        "receipt": "system_v4/probes/a2_state/sim_results/qiskit_two_level_two_bath_gap_change_work_heat_bounds_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "work_heat_cycle_calibration_fixture",
            "two_level_density_work_heat_baseline",
        ],
    },
    {
        "tool": "clifford",
        "function_api": "Cl(3)/Cl(6) layout blades, rotor products, grade/scalar extraction",
        "receipt": "system_v4/probes/a2_state/sim_results/clifford_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["clifford_generator_basis", "clifford_geometry"],
    },
    {
        "tool": "clifford",
        "function_api": "clifford Cl(3) rotor transport over SymPy-derived Weyl Bloch-vector fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/tool_integration_clifford_weyl_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["clifford_bloch_vector_rotor_fixture", "two_component_spinor_coordinate_fixture"],
    },
    {
        "tool": "clifford",
        "function_api": "clifford Cl(3) blades, MultiVector.exp, rotor sandwich transport, and coefficient readout over projected Hopf outer-loop vector fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/clifford_hopf_outer_rotation_readout_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["declared_fiber_base_coordinate_readout_baseline", "clifford_projected_loop_transport_baseline"],
    },
    {
        "tool": "clifford",
        "function_api": "clifford Cl(4) basis vectors and inner products over Hopf/Weyl vertical fiber, raw base, and horizontal base-lift tangent fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/clifford_hopf_weyl_fiber_horizontal_base_tangent_inner_product_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "clifford_vertical_horizontal_tangent_metric_baseline",
        ],
    },
    {
        "tool": "clifford",
        "function_api": "clifford Cl(4) basis-vector MultiVector inner products over Hopf/Weyl vertical fiber, raw base, horizontal base-lift, and wrong-sign tangent projection sweeps",
        "receipt": "system_v4/probes/a2_state/sim_results/clifford_hopf_weyl_vertical_horizontal_tangent_projection_sweep_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "hopf_weyl_vertical_horizontal_carrier_loop_tangent_projection_baseline",
            "declared_two_component_carrier_readout_baseline",
        ],
    },
    {
        "tool": "gudhi",
        "function_api": "SimplexTree, Rips/filtration persistence and Betti summaries",
        "receipt": "system_v4/probes/a2_state/sim_results/gudhi_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["persistence_geometry", "concurrence_measure"],
    },
    {
        "tool": "gudhi",
        "function_api": "gudhi.SimplexTree insert/assign_filtration/persistence on a tiny filtered complex",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_gudhi_simplex_persistence_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["persistence_geometry", "cell_complex_geometry"],
    },
    {
        "tool": "gudhi",
        "function_api": "gudhi.SimplexTree insert/make_filtration_non_decreasing/compute_persistence over PyTorch-derived concurrence and I_c filtrations",
        "receipt": "system_v4/probes/a2_state/sim_results/gudhi_concurrence_filtration_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["concurrence_measure", "persistence_geometry"],
    },
    {
        "tool": "gudhi",
        "function_api": "gudhi.SimplexTree insert/compute_persistence(persistence_dim_max=True)/betti_numbers over explicit torus and cycle complexes",
        "receipt": "system_v4/probes/a2_state/sim_results/gudhi_hopf_torus_fiber_base_homology_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["declared_fiber_base_coordinate_readout_baseline", "hopf_torus_fiber_base_homology_baseline"],
    },
    {
        "tool": "gudhi",
        "function_api": "gudhi.RipsComplex/create_simplex_tree/compute_persistence/persistence_intervals_in_dimension over Hopf/Weyl vertical fiber and horizontal base-lift Bloch-density readout point clouds",
        "receipt": "system_v4/probes/a2_state/sim_results/gudhi_hopf_weyl_vertical_horizontal_density_readout_rips_homology_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "density_readout_loop_homology_baseline",
        ],
    },
    {
        "tool": "gudhi",
        "function_api": "gudhi.SimplexTree insert/compute_persistence/betti_numbers over triangulated connected two-layer Hopf-torus carrier fixture",
        "receipt": "system_v4/probes/a2_state/sim_results/gudhi_connected_hopf_torus_layer_homology_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "finite_hopf_torus_fixture_controls_baseline",
            "connected_layer_simplicial_homology_baseline",
        ],
    },
    {
        "tool": "toponetx",
        "function_api": "CellComplex/SimplicialComplex rank cells and incidence_matrix",
        "receipt": "system_v4/probes/a2_state/sim_results/toponetx_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["cell_rank_binding_fixture", "cell_complex_geometry"],
    },
    {
        "tool": "toponetx",
        "function_api": "CellComplex rank-2 cell incidence_matrix(2)",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_xgi_toponetx_higher_order_incidence_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["cell_complex_geometry", "hypergraph_shell_geometry"],
    },
    {
        "tool": "toponetx",
        "function_api": "TopoNetX CellComplex periodic rank-2 torus layers with incidence_matrix and hodge_laplacian_matrix zero-mode readouts",
        "receipt": "system_v4/probes/a2_state/sim_results/toponetx_two_hopf_torus_layer_incidence_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["finite_hopf_torus_fixture_controls_baseline", "declared_fiber_base_coordinate_readout_baseline"],
    },
    {
        "tool": "toponetx",
        "function_api": "TopoNetX CellComplex connected two-layer torus cells with interlayer rank-2 cells and Hodge-Laplacian zero-mode proxies",
        "receipt": "system_v4/probes/a2_state/sim_results/toponetx_connected_hopf_torus_layer_incidence_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "finite_hopf_torus_fixture_controls_baseline",
            "connected_layer_cell_complex_baseline",
        ],
    },
    {
        "tool": "toponetx",
        "function_api": "TopoNetX CellComplex add_node/add_cell/incidence_matrix/hodge_laplacian_matrix over Hopf/Weyl vertical fiber and horizontal base-lift Bloch-density readout cycle fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/toponetx_hopf_weyl_vertical_horizontal_density_readout_cycle_incidence_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "density_readout_cycle_incidence_baseline",
        ],
    },
    {
        "tool": "toponetx",
        "function_api": "SimplicialComplex.to_hasse_graph node/edge carrier feeding PyG graph fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/tool_integration_toponetx_pyg_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["topology_to_graph_fit", "cell_complex_geometry"],
    },
    {
        "tool": "xgi",
        "function_api": "xgi.Hypergraph hyperedge membership and shared incidence intersection",
        "receipt": "system_v4/probes/a2_state/sim_results/xgi_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["hypergraph_shell_geometry", "dual_hypergraph_geometry"],
    },
    {
        "tool": "xgi",
        "function_api": "xgi.Hypergraph incidence matrix and node/edge membership on a tiny hypergraph",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_xgi_hypergraph_incidence_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["hypergraph_shell_geometry", "cell_complex_geometry"],
    },
    {
        "tool": "xgi",
        "function_api": "XGI hyperedge incidence matched to TopoNetX rank-2 cells",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_xgi_toponetx_higher_order_incidence_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["hypergraph_shell_geometry", "cell_complex_geometry"],
    },
    {
        "tool": "xgi",
        "function_api": "XGI Hypergraph named hyperedges, node memberships, edge memberships, incidence_matrix, and connected_components over Hopf receipt groups",
        "receipt": "system_v4/probes/a2_state/sim_results/xgi_hopf_receipt_hyperedge_incidence_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["finite_hopf_torus_fixture_controls_baseline", "declared_fiber_base_coordinate_readout_baseline"],
    },
    {
        "tool": "rustworkx",
        "function_api": "rustworkx PyDiGraph DAG construction, topological_sort, transitive_reduction, dijkstra_shortest_paths, cycle detection",
        "receipt": "system_v4/probes/a2_state/sim_results/rustworkx_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["graph_shell_geometry", "dependency_dag_and_collapse"],
    },
    {
        "tool": "rustworkx",
        "function_api": "rustworkx PyDiGraph descendants/topological_sort/shortest_path reachability on a tiny DAG",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_rustworkx_dag_reachability_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["dependency_dag_and_collapse", "graph_shell_geometry"],
    },
    {
        "tool": "rustworkx",
        "function_api": "rustworkx PyDiGraph topological_sort/ancestors/descendants/transitive_reduction over Hopf receipt dependency DAG",
        "receipt": "system_v4/probes/a2_state/sim_results/rustworkx_hopf_receipt_dependency_reduction_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["finite_hopf_torus_fixture_controls_baseline", "receipt_dependency_dag_controls"],
    },
    {
        "tool": "rustworkx",
        "function_api": "rustworkx PyGraph add_node/add_edge/number_connected_components/is_connected/cycle_basis over Hopf/Weyl vertical fiber and horizontal base-lift Bloch-density readout cycle graphs",
        "receipt": "system_v4/probes/a2_state/sim_results/rustworkx_hopf_weyl_vertical_horizontal_density_readout_cycle_graph_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "density_readout_cycle_graph_baseline",
        ],
    },
    {
        "tool": "scipy",
        "function_api": "scipy.linalg.eigvalsh, scipy.optimize.minimize, scipy.spatial.distance.cdist, and scipy.stats.entropy baseline controls",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_capability_scipy_isolated_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["classical_spectral_baseline", "classical_distance_entropy_baseline"],
    },
    {
        "tool": "scipy",
        "function_api": "scipy.integrate.solve_ivp numerical Hopf horizontal-lift chi-shift ODE over base latitude loops",
        "receipt": "system_v4/probes/a2_state/sim_results/scipy_hopf_horizontal_lift_chi_shift_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["hopf_loop_holonomy_geometry_baseline", "declared_fiber_base_coordinate_readout_baseline"],
    },
    {
        "tool": "scipy",
        "function_api": "scipy.integrate.solve_ivp horizontal-lift chi-shift ODE over connected two-theta-layer Hopf-torus coordinates",
        "receipt": "system_v4/probes/a2_state/sim_results/scipy_connected_hopf_torus_horizontal_transport_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "finite_hopf_torus_fixture_controls_baseline",
            "connected_layer_horizontal_transport_baseline",
        ],
    },
    {
        "tool": "numpy",
        "function_api": "numpy complex arrays, exp, outer, trace, linalg.norm, and unwrap over sampled Hopf-coordinate carrier paths",
        "receipt": "system_v4/probes/a2_state/sim_results/numpy_hopf_weyl_fiber_base_loop_readout_geometry_results.json",
        "role": "classical_baseline",
        "depth": "supportive",
        "candidate_lego_targets": ["declared_fiber_base_coordinate_readout_baseline", "classical_hopf_path_metric_baseline"],
    },
    {
        "tool": "numpy",
        "function_api": "numpy complex carrier sampling with declared Weyl-sheet orientation sign, Hopf fiber/base loop families, density readouts, and signed xy area",
        "receipt": "system_v4/probes/a2_state/sim_results/numpy_weyl_sheet_hopf_loop_readout_separation_results.json",
        "role": "classical_baseline",
        "depth": "supportive",
        "candidate_lego_targets": ["declared_fiber_base_coordinate_readout_baseline", "z2x_z2_product_label_readout_baseline"],
    },
    {
        "tool": "numpy",
        "function_api": "numpy isclose scalar heat/work/efficiency accounting for reversible two-bath four-stroke cycle calibration",
        "receipt": "system_v4/probes/a2_state/sim_results/carnot_two_bath_four_stroke_work_heat_bounds_results.json",
        "role": "classical_baseline",
        "depth": "supportive",
        "candidate_lego_targets": ["work_heat_cycle_calibration_fixture", "two_bath_four_stroke_work_heat_efficiency_bound_baseline"],
    },
    {
        "tool": "numpy",
        "function_api": "numpy log/sum/isclose binary entropy, feedback work bound, and Landauer erasure floor for one-bit cycle calibration",
        "receipt": "system_v4/probes/a2_state/sim_results/szilard_measure_feedback_erasure_landauer_bounds_results.json",
        "role": "classical_baseline",
        "depth": "supportive",
        "candidate_lego_targets": ["information_work_erasure_cycle_calibration_fixture", "one_bit_measure_feedback_erasure_work_bound_baseline"],
    },
    {
        "tool": "z3",
        "function_api": "z3 Solver/SolverFor QF_LIA add/check/model and UNSAT witness",
        "receipt": "system_v4/probes/a2_state/sim_results/z3_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "distinguishability_relation"],
    },
    {
        "tool": "z3",
        "function_api": "z3 SolverFor('QF_LIA') shared SAT/UNSAT agreement fixture",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_cvc5_z3_unsat_agreement_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "probe_object"],
    },
    {
        "tool": "z3",
        "function_api": "z3 SolverFor('QF_NIA') consuming exact SymPy polynomial coefficients and derivatives for bounded integer-root fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/tool_integration_z3_sympy_results.json",
        "role": "classical_bridge",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "exact_algebra_crosschecks"],
    },
    {
        "tool": "z3",
        "function_api": "z3 Solver with integer Pauli-label orientation predicate SAT/UNSAT controls",
        "receipt": "system_v4/probes/a2_state/sim_results/pauli_orientation_integer_predicate_baseline_results.json",
        "role": "classical_baseline",
        "depth": "supportive",
        "candidate_lego_targets": ["bare_pauli_label_partition_negative_control", "declared_fiber_base_coordinate_readout_baseline"],
    },
    {
        "tool": "z3",
        "function_api": "z3 Bool/And/Not/Implies/Solver.check SAT/UNSAT negative control for bare Pauli labels versus Hopf/Weyl carrier-projection metric predicates",
        "receipt": "system_v4/probes/a2_state/sim_results/z3_bare_pauli_no_carrier_fiber_base_metric_unsat_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "bare_pauli_label_partition_negative_control",
            "declared_two_component_carrier_readout_baseline",
        ],
    },
    {
        "tool": "z3",
        "function_api": "z3 Real/Q/Solver.check bounded rational SAT/UNSAT controls for Hopf/Weyl vertical fiber and horizontal base-lift metric predicates",
        "receipt": "system_v4/probes/a2_state/sim_results/z3_hopf_weyl_vertical_horizontal_metric_predicate_controls_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "vertical_horizontal_metric_predicate_controls",
        ],
    },
    {
        "tool": "z3",
        "function_api": "z3 finite Z2 x Z2 product readout SAT/UNSAT separation for sheet-flip and loop-flip labels",
        "receipt": "system_v4/probes/a2_state/sim_results/z3_sheet_loop_flip_product_readout_separation_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["z2x_z2_product_label_readout_baseline", "declared_fiber_base_coordinate_readout_baseline"],
    },
    {
        "tool": "z3",
        "function_api": "z3 SolverFor('QF_LIA') SAT/UNSAT equality checks over selected Hopf-torus integer readout vector fields",
        "receipt": "system_v4/probes/a2_state/sim_results/z3_hopf_torus_readout_vector_separation_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["finite_hopf_torus_fixture_controls_baseline", "readout_vector_separation_controls"],
    },
    {
        "tool": "z3",
        "function_api": "z3 SolverFor('QF_LIA') bounded integer partial-order constraints over Hopf receipt dependency DAG",
        "receipt": "system_v4/probes/a2_state/sim_results/z3_hopf_receipt_dependency_partial_order_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "finite_hopf_torus_fixture_controls_baseline",
            "receipt_dependency_dag_controls",
        ],
    },
    {
        "tool": "cvc5",
        "function_api": "cvc5 Solver.assertFormula/checkSat/getValue QF_LIA fixture",
        "receipt": "system_v4/probes/a2_state/sim_results/cvc5_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_fixture", "density_matrix_carrier_fixture"],
    },
    {
        "tool": "cvc5",
        "function_api": "cvc5 shared QF_LIA SAT/UNSAT agreement with z3",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_cvc5_z3_unsat_agreement_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "probe_object"],
    },
    {
        "tool": "cvc5",
        "function_api": "cvc5 Solver.synthFun/addSygusConstraint/checkSynth/getSynthSolution bounded LIA SyGuS fixture",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_cvc5_sygus_synthesis_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "sygus_integer_grammar_fixture"],
    },
    {
        "tool": "cvc5",
        "function_api": "cvc5 QF_NIA constraints consuming exact SymPy polynomial coefficients and derivatives for bounded integer-root fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/tool_integration_cvc5_sympy_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "exact_algebra_crosschecks"],
    },
    {
        "tool": "cvc5",
        "function_api": "cvc5 QF_LIA SAT/UNSAT equality checks over selected Hopf-torus integer readout vector fields",
        "receipt": "system_v4/probes/a2_state/sim_results/cvc5_hopf_torus_readout_vector_separation_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["finite_hopf_torus_fixture_controls_baseline", "readout_vector_separation_controls"],
    },
    {
        "tool": "cvc5",
        "function_api": "cvc5 Boolean SAT/UNSAT negative control for bare Pauli labels versus Hopf/Weyl carrier-projection metric predicates",
        "receipt": "system_v4/probes/a2_state/sim_results/cvc5_bare_pauli_no_carrier_fiber_base_metric_unsat_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "bare_pauli_label_partition_negative_control",
            "declared_two_component_carrier_readout_baseline",
        ],
    },
    {
        "tool": "cvc5",
        "function_api": "cvc5 QF_LRA rational SAT/UNSAT controls for Hopf/Weyl vertical fiber and horizontal base-lift metric predicates",
        "receipt": "system_v4/probes/a2_state/sim_results/cvc5_hopf_weyl_vertical_horizontal_metric_predicate_controls_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "vertical_horizontal_metric_predicate_controls",
        ],
    },
    {
        "tool": "sympy",
        "function_api": "sympy symbolic expression/matrix simplification and exact algebra",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_capability_results.json",
        "role": "classical_bridge",
        "depth": "load_bearing",
        "candidate_lego_targets": ["entropy_family_crosschecks", "operator_family_fixture"],
    },
    {
        "tool": "sympy",
        "function_api": "sympy.diff/integrate/factor/simplify exact scalar identity checks",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_sympy_symbolic_identity_micro_results.json",
        "role": "classical_bridge",
        "depth": "load_bearing",
        "candidate_lego_targets": ["exact_algebra_crosschecks", "operator_family_fixture"],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Poly/all_coeffs/diff/factor/gcd/discriminant feeding z3 bounded integer-root fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/tool_integration_z3_sympy_results.json",
        "role": "classical_bridge",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "exact_algebra_crosschecks"],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Poly/all_coeffs/diff/factor/gcd/discriminant feeding cvc5 bounded integer-root fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/tool_integration_cvc5_sympy_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "exact_algebra_crosschecks"],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Matrix.inv / exact matrix equality inverse identity checks",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_sympy_matrix_identity_micro_results.json",
        "role": "classical_bridge",
        "depth": "load_bearing",
        "candidate_lego_targets": ["exact_matrix_identity", "operator_family_fixture"],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Matrix/exp/diff/simplify/subs for exact Hopf-coordinate density derivative readouts",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_hopf_fiber_base_density_readout_identities_results.json",
        "role": "classical_baseline",
        "depth": "supportive",
        "candidate_lego_targets": ["declared_fiber_base_coordinate_readout_baseline", "exact_hopf_coordinate_identity_baseline"],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Matrix/exp/diff/simplify/subs for declared Weyl-sheet orientation signs in Hopf-coordinate density derivative ratios",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_weyl_sheet_hopf_loop_derivative_sign_results.json",
        "role": "classical_baseline",
        "depth": "supportive",
        "candidate_lego_targets": ["declared_fiber_base_coordinate_readout_baseline", "z2x_z2_product_label_readout_baseline"],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Matrix/diag/eye/exp/diff/trace/trigsimp for exact phase-generator density transport",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_hopf_loop_phase_generator_density_transport_results.json",
        "role": "classical_baseline",
        "depth": "supportive",
        "candidate_lego_targets": [
            "declared_fiber_base_coordinate_readout_baseline",
            "density_operator_phase_generator_transport_baseline",
        ],
    },
    {
        "tool": "sympy",
        "function_api": "sympy diff/integrate/simplify exact Hopf U(1) connection curvature and first-Chern integral",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_hopf_connection_curvature_c1_integral_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["hopf_connection_curvature_geometry_baseline", "curvature_integral_baseline"],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Matrix/diff/integrate/simplify contrast between Hopf connection curvature and carrier-free Pauli-label controls",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_hopf_connection_curvature_pauli_label_gap_results.json",
        "role": "classical_baseline",
        "depth": "supportive",
        "candidate_lego_targets": ["bare_pauli_label_partition_negative_control", "hopf_connection_curvature_geometry_baseline"],
    },
    {
        "tool": "sympy",
        "function_api": "sympy symbols/cos/integrate/simplify exact Hopf connection loop integrals and horizontal-lift chi shifts",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_hopf_loop_holonomy_area_dependence_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "hopf_loop_holonomy_geometry_baseline",
            "declared_fiber_base_coordinate_readout_baseline",
        ],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Matrix/diff/trigsimp/simplify exact S3 carrier and S2 projection speed identities for Hopf/Weyl fiber-base coordinates",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_hopf_weyl_fiber_base_s3_s2_distance_identities_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "exact_carrier_projection_identity_baseline",
        ],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Matrix/diff/conjugate/re/trigsimp/simplify exact Hopf/Weyl vertical fiber and horizontal base-lift metric independence identities",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_hopf_weyl_fiber_horizontal_base_loop_independence_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "exact_vertical_horizontal_loop_metric_baseline",
        ],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Matrix/diff/conjugate/re/trigsimp/simplify exact Hopf/Weyl vertical fiber, raw base, horizontal base-lift, and wrong-sign tangent projection coefficient identities",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_hopf_weyl_vertical_horizontal_tangent_projection_identities_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "hopf_weyl_vertical_horizontal_carrier_loop_tangent_projection_baseline",
            "declared_two_component_carrier_readout_baseline",
        ],
    },
    {
        "tool": "sympy",
        "function_api": "sympy symbols/exp/simplify/subs exact two-level thermal population and two-bath gap-change work/heat identities",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_two_level_two_bath_gap_change_work_heat_identities_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "work_heat_cycle_calibration_fixture",
            "exact_two_level_work_heat_identity_baseline",
        ],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Rational/log/simplify exact two-level binary measurement information, conditional feedback work, and Landauer erasure-floor identities",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_two_level_measure_feedback_erasure_identities_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "information_work_erasure_cycle_calibration_fixture",
            "exact_measure_feedback_erasure_identity_baseline",
        ],
    },
    {
        "tool": "sympy",
        "function_api": "sympy Matrix partition of Pauli matrices into diagonal and off-diagonal labels",
        "receipt": "system_v4/probes/a2_state/sim_results/pauli_orientation_integer_predicate_baseline_results.json",
        "role": "classical_baseline",
        "depth": "supportive",
        "candidate_lego_targets": ["bare_pauli_label_partition_negative_control", "declared_fiber_base_coordinate_readout_baseline"],
    },
    {
        "tool": "sympy",
        "function_api": "sympy roots/discriminant/exact rational edge-weight construction feeding PyG graph fixtures",
        "receipt": "system_v4/probes/a2_state/sim_results/tool_integration_sympy_pyg_results.json",
        "role": "classical_bridge",
        "depth": "load_bearing",
        "candidate_lego_targets": ["graph_symbolic_fit", "exact_algebra_crosschecks"],
    },
    {
        "tool": "geomstats",
        "function_api": "geomstats metric.geodesic, exp/log, SPD distance, Frechet mean",
        "receipt": "system_v4/probes/a2_state/sim_results/geomstats_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["geometry_crosschecks_same_carrier", "quantum_metric_nonuniqueness"],
    },
    {
        "tool": "geomstats",
        "function_api": "geomstats SO(3) metric distance/log/exp consistency on tiny rotations",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_geomstats_so3_distance_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["geometry_crosschecks_same_carrier", "so3_rotation_geometry_fixture"],
    },
    {
        "tool": "geomstats",
        "function_api": "geomstats Hypersphere(dim=2).metric.dist intrinsic path-length readouts over projected Hopf-coordinate loops",
        "receipt": "system_v4/probes/a2_state/sim_results/geomstats_hopf_projected_fiber_base_sphere_distance_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["declared_fiber_base_coordinate_readout_baseline", "projected_sphere_distance_baseline"],
    },
    {
        "tool": "geomstats",
        "function_api": "geomstats Hypersphere(dim=3).metric.dist and Hypersphere(dim=2).metric.dist over sampled Hopf/Weyl S3 carrier and S2 projection loops",
        "receipt": "system_v4/probes/a2_state/sim_results/geomstats_hopf_weyl_fiber_base_s3_s2_distance_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "carrier_projection_distance_baseline",
        ],
    },
    {
        "tool": "geomstats",
        "function_api": "geomstats Hypersphere(dim=3).metric.dist and Hypersphere(dim=2).metric.dist over sampled Hopf/Weyl vertical fiber and horizontal base-lift loops",
        "receipt": "system_v4/probes/a2_state/sim_results/geomstats_hopf_weyl_fiber_horizontal_base_loop_distance_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "vertical_horizontal_loop_metric_distance_baseline",
        ],
    },
    {
        "tool": "geomstats",
        "function_api": "geomstats Hypersphere(dim=3).metric.inner_product and Hypersphere(dim=2).metric.inner_product over Hopf/Weyl vertical fiber, raw base, and horizontal base-lift tangent projection sweeps",
        "receipt": "system_v4/probes/a2_state/sim_results/geomstats_hopf_weyl_vertical_horizontal_tangent_projection_sweep_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "hopf_weyl_vertical_horizontal_carrier_loop_tangent_projection_baseline",
            "declared_two_component_carrier_readout_baseline",
        ],
    },
    {
        "tool": "e3nn",
        "function_api": "e3nn.o3.Irreps and D_from_matrix vector representation",
        "receipt": "system_v4/probes/a2_state/sim_results/e3nn_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["operator_family_fixture", "graph_cell_complex_geometry"],
    },
    {
        "tool": "e3nn",
        "function_api": "e3nn.o3.spherical_harmonics equivariance under a tiny SO(3) rotation fixture",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_e3nn_spherical_harmonics_equivariance_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["operator_family_fixture", "so3_rotation_geometry_fixture"],
    },
    {
        "tool": "e3nn",
        "function_api": "e3nn.o3.spherical_harmonics, matrix_to_angles, and wigner_D l=1 SO(3) equivariance over projected Hopf base-loop samples",
        "receipt": "system_v4/probes/a2_state/sim_results/e3nn_hopf_base_loop_so3_equivariance_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["hopf_base_loop_so3_readout_equivariance_baseline", "declared_fiber_base_coordinate_readout_baseline"],
    },
    {
        "tool": "e3nn",
        "function_api": "e3nn.o3.spherical_harmonics/matrix_to_angles/wigner_D/angles_to_matrix l=1 SO(3) equivariance over Hopf/Weyl vertical fiber and horizontal base-lift Bloch-density readouts",
        "receipt": "system_v4/probes/a2_state/sim_results/e3nn_hopf_weyl_vertical_horizontal_density_so3_equivariance_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": [
            "declared_two_component_carrier_readout_baseline",
            "density_readout_so3_equivariance_baseline",
        ],
    },
    {
        "tool": "e3nn",
        "function_api": "e3nn vector irrep action commuting with PyG MessagePassing.propagate",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_e3nn_pyg_equivariance_under_mp_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["operator_family_fixture", "graph_cell_complex_geometry"],
    },
]


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - report path is the point
        return {"_load_error": str(exc)}
    return data if isinstance(data, dict) else {"_non_object": True}


def all_pass(payload: dict[str, Any]) -> bool:
    if payload.get("all_pass") is True or payload.get("overall_pass") is True:
        return True
    summary = payload.get("summary")
    if isinstance(summary, dict):
        return bool(summary.get("all_pass") or summary.get("passed") == summary.get("total"))
    return False


def result_classification(payload: dict[str, Any]) -> str | None:
    value = payload.get("classification")
    return str(value) if value is not None else None


def infer_receipt_schema(payload: dict[str, Any]) -> dict[str, Any]:
    """Describe the receipt contract without pretending an explicit schema exists."""
    observed = payload.get("schema")
    fields = sorted(k for k in payload.keys() if not k.startswith("_"))
    has_manifest = isinstance(payload.get("tool_manifest"), dict)
    has_depth = isinstance(payload.get("tool_integration_depth"), dict)
    has_classification = payload.get("classification") is not None
    has_pass = (
        payload.get("all_pass") is not None
        or payload.get("overall_pass") is not None
        or isinstance(payload.get("summary"), dict)
    )
    if observed:
        schema = str(observed)
        source = "explicit_receipt_schema"
        resolved = True
    elif has_manifest and has_depth and has_classification and has_pass:
        schema = "implicit_sim_result_receipt.v1"
        source = "inferred_from_required_receipt_fields"
        resolved = True
    else:
        schema = None
        source = "unresolved_missing_required_receipt_fields"
        resolved = False
    return {
        "schema": schema,
        "observed": observed,
        "source": source,
        "resolved": resolved,
        "fields": fields,
    }


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in TARGETS:
        path = ROOT / target["receipt"]
        payload = load_json(path)
        manifest = payload.get("tool_manifest") if isinstance(payload.get("tool_manifest"), dict) else {}
        depth = payload.get("tool_integration_depth") if isinstance(payload.get("tool_integration_depth"), dict) else {}
        tool = target["tool"]
        receipt_schema = infer_receipt_schema(payload)
        rows.append(
            {
                **target,
                "receipt_exists": path.exists(),
                "receipt_all_pass": all_pass(payload),
                "receipt_classification": result_classification(payload),
                "receipt_schema": receipt_schema["schema"],
                "receipt_schema_observed": receipt_schema["observed"],
                "receipt_schema_source": receipt_schema["source"],
                "receipt_schema_resolved": receipt_schema["resolved"],
                "receipt_contract_fields": receipt_schema["fields"],
                "manifest_reason": (manifest.get(tool) or {}).get("reason") if isinstance(manifest.get(tool), dict) else None,
                "observed_depth": depth.get(tool),
                "boundary_source": "receipt" if payload.get("claim_ceiling") or payload.get("out_of_scope") else "matrix_default",
                "boundary_gap": not (payload.get("claim_ceiling") and payload.get("out_of_scope")),
                "claim_ceiling": payload.get("claim_ceiling") or "tool_function_receipt_only_not_admission_or_promotion",
                "out_of_scope": payload.get("out_of_scope") or [
                    "no QIT admission",
                    "no GStack admission",
                    "no axis admission",
                    "no bridge or engine claim",
                    "no scientific lego coupling promotion",
                ],
            }
        )
    return rows


def write_markdown(rows: list[dict[str, Any]], generated_at: str) -> None:
    lines = [
        "# Tool Function Receipt Matrix",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Boundary: receipt index only. This does not admit, promote, or validate a lego, coupling, bridge, axis, GStack, QIT, or engine claim.",
        "Role values are matrix metadata only; they are not executable sim labels and must not be used to generate sim filenames.",
        "",
        "## Summary",
        "",
        f"- Rows: `{len(rows)}`",
        f"- Passing rows: `{sum(1 for row in rows if row['receipt_all_pass'])}`",
        f"- Missing receipts: `{sum(1 for row in rows if not row['receipt_exists'])}`",
        f"- Explicit receipt schemas missing: `{sum(1 for row in rows if row['receipt_schema_observed'] is None)}`",
        f"- Receipt contract shapes unresolved: `{sum(1 for row in rows if not row['receipt_schema_resolved'])}`",
        "",
        "## Matrix",
        "",
        "| tool | exact function/API surface | receipt | classification | role | depth | pass | candidate lego targets |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        targets = ", ".join(f"`{item}`" for item in row["candidate_lego_targets"])
        lines.append(
            f"| `{row['tool']}` | {row['function_api']} | `{row['receipt']}` | "
            f"`{row['receipt_classification']}` | `{row['role']}` | `{row['observed_depth'] or row['depth']}` | "
            f"`{row['receipt_all_pass']}` | {targets} |"
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_rows()
    payload = {
        "schema": "tool_function_receipt_matrix.v1",
        "generated_at": generated_at,
        "boundary": "receipt_index_only_not_admission_or_promotion",
        "summary": {
            "row_count": len(rows),
            "passing_count": sum(1 for row in rows if row["receipt_all_pass"]),
            "missing_receipt_count": sum(1 for row in rows if not row["receipt_exists"]),
            "receipt_boundary_gap_count": sum(1 for row in rows if row["boundary_gap"]),
            "receipt_schema_observed_missing_count": sum(1 for row in rows if row["receipt_schema_observed"] is None),
            "receipt_schema_unresolved_count": sum(1 for row in rows if not row["receipt_schema_resolved"]),
            "tools": sorted({row["tool"] for row in rows}),
        },
        "rows": rows,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(rows, generated_at)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["summary"]["missing_receipt_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
