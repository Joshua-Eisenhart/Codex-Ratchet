#!/usr/bin/env python3
"""
Build the next executable normalization queue from the actual lego registry.

Consumes:
  - actual_lego_registry.json
  - controller_alignment_audit_results.json

Emits:
  - actual_lego_normalization_queue.json

Goal:
  move from "registry rows exist" to "next bounded lego-first sim work is explicit".
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
REGISTRY_PATH = RESULTS_DIR / "actual_lego_registry.json"
ALIGN_PATH = RESULTS_DIR / "controller_alignment_audit_results.json"
OUT_PATH = RESULTS_DIR / "actual_lego_normalization_queue.json"

SECTION_PRIORITY = {
    "Root And Admission Legos": 1,
    "Constraint And Carrier Reference Legos": 1,
    "State Representation Legos": 2,
    "Compression And Spectral Legos": 2,
    "Geometry Legos": 3,
    "Operator And Channel Legos": 3,
    "Loop, Connection, And Placement Legos": 3,
    "Bipartite And Correlation Legos": 4,
    "Entropy Legos": 5,
    "Graph / Topology Legos": 5,
    "Bridge, Axis, And Support Legos": 6,
    "Boundary Falsifier Legos": 6,
}

NORMALIZATION_TARGETS = {
    "probe_object": {
        "probe": "sim_probe_object.py",
        "confidence": "high",
        "note": "Direct local admissible-probe lego with finite POVM-style probe rules and invalid counterexamples.",
    },
    "distinguishability_relation": {
        "probe": "sim_distinguishability_relation.py",
        "confidence": "high",
        "note": "Direct local probe-relative distinguishability lego on bounded one-qubit states and finite projective probe families.",
    },
    "probe_identity_preservation": {
        "probe": "sim_probe_identity_preservation.py",
        "confidence": "high",
        "note": "Direct local lego for same-state same-probe repeatability and nontrivial state separation.",
    },
    "representation_violation_check": {
        "probe": "sim_representation_violation_check.py",
        "confidence": "high",
        "note": "Direct local rejection row for invalid candidate state representations on a tiny 2x2 scope.",
    },
    "positivity_constraint": {
        "probe": "sim_positivity_constraint.py",
        "confidence": "high",
        "note": "Direct local PSD admission lego on bounded valid and invalid density candidates.",
    },
    "carrier_probe_support": {
        "probe": "sim_carrier_probe_support.py",
        "confidence": "high",
        "note": "Direct local carrier/probe compatibility lego on bounded qubit carriers and finite effect families.",
    },
    "f01_finitude_constraint": {
        "probe": "sim_constraint_manifold_L0_L1.py",
        "confidence": "high",
        "note": "Best current early manifold/finitude surface.",
    },
    "admissibility_manifold_mc": {
        "probe": "sim_constraint_manifold_L0_L1.py",
        "confidence": "high",
        "note": "Direct match for early admissibility manifold work.",
    },
    "helstrom_guess_bound": {
        "probe": "sim_helstrom_guess_bound.py",
        "confidence": "high",
        "note": "Direct local Helstrom operational guessing lego on bounded qubit state pairs.",
    },
    "trace_distance_geometry": {
        "probe": "sim_trace_distance_geometry.py",
        "confidence": "high",
        "note": "Direct local metric lego for trace-distance behavior on bounded qubit state pairs.",
    },
    "bures_geometry": {
        "probe": "sim_bures_geometry.py",
        "confidence": "high",
        "note": "Direct local Bures-distance lego on bounded qubit state pairs and mixed states.",
    },
    "fubini_study_geometry": {
        "probe": "sim_fubini_study_geometry.py",
        "confidence": "high",
        "note": "Direct local Fubini-Study metric lego on bounded pure-state rays.",
    },
    "nested_torus_geometry": {
        "probe": "sim_nested_torus_geometry.py",
        "confidence": "high",
        "note": "Direct local nested-torus geometry lego using fixed radii, radial separation, and area bounds only.",
    },
    "sphere_geometry": {
        "probe": "sim_sphere_geometry.py",
        "confidence": "high",
        "note": "Direct local sphere-geometry lego on one qubit carrier via Bloch-sphere embedding and local geodesic checks.",
    },
    "covariance_operator": {
        "probe": "sim_covariance_operator.py",
        "confidence": "high",
        "note": "Direct local covariance-operator lego with PSD, trace-one, and spectral checks.",
    },
    "spectral_decomposition": {
        "probe": "sim_torch_eigendecomp.py",
        "confidence": "high",
        "note": "Direct local eigendecomposition lego with clean canonical result surface.",
    },
    "eigenvalue_spectrum_view": {
        "probe": "sim_eigenvalue_spectrum_view.py",
        "confidence": "high",
        "note": "Direct local spectral-view lego showing what eigenvalue-only state descriptions preserve and what they collapse.",
    },
    "principal_subspace": {
        "probe": "sim_torch_eigendecomp.py",
        "confidence": "high",
        "note": "Direct local principal-mode recovery surface from differentiable eigendecomposition.",
    },
    "spectral_truncation": {
        "probe": "sim_spectral_truncation.py",
        "confidence": "high",
        "note": "Direct local truncation lego with monotone fidelity and trace-distance checks.",
    },
    "entanglement_spectrum": {
        "probe": "sim_entanglement_spectrum.py",
        "confidence": "high",
        "note": "Direct local reduced-spectrum lego on a tiny bipartite family.",
    },
    "svd_factorization": {
        "probe": "sim_svd_factorization.py",
        "confidence": "high",
        "note": "Direct local singular-value factorization lego with exact reconstruction checks.",
    },
    "low_rank_psd_approximation": {
        "probe": "sim_low_rank_psd_approximation.py",
        "confidence": "high",
        "note": "Direct local PSD-preserving low-rank approximation lego with trace renormalization.",
    },
    "operator_low_rank_factorization": {
        "probe": "sim_operator_low_rank_factorization.py",
        "confidence": "high",
        "note": "Direct local operator-factorization lego with exact reconstruction at full rank and monotone low-rank recovery.",
    },
    "qpca_spectral_extraction": {
        "probe": "sim_qpca_spectral_extraction.py",
        "confidence": "high",
        "note": "Direct local QPCA lego with dominant-mode recovery and classical surrogate comparison.",
    },
    "schmidt_mode_truncation": {
        "probe": "sim_lego_entropy_entanglement_spectrum.py",
        "confidence": "medium",
        "note": "Best current local bipartite spectral proxy; still needs a cleaner direct lego.",
    },
    "coarse_grained_operator_algebra": {
        "probe": "sim_coarse_grained_operator_algebra.py",
        "confidence": "high",
        "note": "Direct local partial-trace coarse-graining algebra lego on bounded two-qubit operators.",
    },
    "correlation_tensor_principal_directions": {
        "probe": "sim_correlation_tensor_principal_directions.py",
        "confidence": "high",
        "note": "Direct local principal-direction lego on bounded two-qubit correlation tensors.",
    },
    "geometry_preserving_basis_change": {
        "probe": "sim_pure_lego_reference_frames.py",
        "confidence": "medium",
        "note": "Closest basis/frame-change lego already present.",
    },
    "graph_geometry": {
        "probe": "sim_graph_geometry.py",
        "confidence": "high",
        "note": "Direct local graph-carrier lego with cycle rank, connectivity, and Laplacian checks.",
    },
    "stokes_parameterization": {
        "probe": "sim_stokes_parameterization.py",
        "confidence": "high",
        "note": "Direct local Stokes-parameterization lego on a tiny admitted qubit state set.",
    },
    "graph_shell_geometry": {
        "probe": "sim_graph_shell_geometry.py",
        "confidence": "high",
        "note": "Direct local shell-graph lego using only binary shell relations and graph-native invariants.",
    },
    "operator_coordinate_representation": {
        "probe": "sim_operator_coordinate_representation.py",
        "confidence": "high",
        "note": "Direct local Pauli-operator-coordinate lego with exact reconstruction and representation-separation checks.",
    },
    "pauli_generator_basis": {
        "probe": "sim_pauli_generator_basis.py",
        "confidence": "high",
        "note": "Direct local Pauli-basis lego on {I, X, Y, Z} as the qubit operator basis.",
    },
    "clifford_generator_basis": {
        "probe": "sim_clifford_generator_basis.py",
        "confidence": "high",
        "note": "Direct local Clifford-generator lego on the minimal one-qubit generating set {H, S}.",
    },
    "commutator_algebra": {
        "probe": "sim_commutator_algebra.py",
        "confidence": "high",
        "note": "Direct local commutator-algebra lego on the qubit Pauli generators.",
    },
    "pauli_algebra_relations": {
        "probe": "sim_pauli_algebra_relations.py",
        "confidence": "high",
        "note": "Direct local Pauli-algebra lego covering multiplication and commutation identities on the qubit carrier.",
    },
    "local_operator_action": {
        "probe": "sim_local_operator_action.py",
        "confidence": "high",
        "note": "Direct local operator-action lego on a tiny admitted qubit state set under unitary conjugation.",
    },
    "characteristic_representation": {
        "probe": "sim_characteristic_representation.py",
        "confidence": "high",
        "note": "Direct local characteristic-function lego on Pauli-label evaluations, kept separate from operator-coordinate and Bloch rows.",
    },
    "husimi_phase_space_representation": {
        "probe": "sim_husimi_phase_space_representation.py",
        "confidence": "high",
        "note": "Direct local qubit Husimi-Q representation lego on a fixed Bloch-sphere grid, kept separate from phase-space geometry.",
    },
    "channel_space_geometry": {
        "probe": "sim_channel_space_geometry.py",
        "confidence": "high",
        "note": "Direct local channel-geometry lego comparing bounded qubit channels by Choi and output-family separation.",
    },
    "schmidt_mode_truncation": {
        "probe": "sim_schmidt_mode_truncation.py",
        "confidence": "high",
        "note": "Direct local Schmidt-mode truncation lego on one bounded bipartite pure-state family.",
    },
    "geometry_preserving_basis_change": {
        "probe": "sim_geometry_preserving_basis_change.py",
        "confidence": "high",
        "note": "Direct local unitary basis-change row preserving local geometry on a bounded state family.",
    },
    "terrain_family_fourfold": {
        "probe": "sim_engine_16_placements.py",
        "confidence": "high",
        "note": "Best direct terrain-family match.",
    },
    "loop_vector_fields": {
        "probe": "sim_loop_vector_fields.py",
        "confidence": "high",
        "note": "Direct local tangent-field row on one bounded phase loop.",
    },
    "base_loop_law": {
        "probe": "sim_base_loop_law.py",
        "confidence": "high",
        "note": "Direct local base-loop lego on one fixed sample showing density traversal and closure.",
    },
    "placement_law": {
        "probe": "sim_engine_16_placements.py",
        "confidence": "high",
        "note": "Direct placement-table surface.",
    },
    "loop_order_family": {
        "probe": "sim_loop_order_family.py",
        "confidence": "high",
        "note": "Direct local loop-order row on one bounded carrier with two noncommuting steps.",
    },
    "signed_operator_variant": {
        "probe": "sim_engine_16_placements.py",
        "confidence": "medium",
        "note": "Closest current surface to the signed operator table.",
    },
    "operator_parameter_tuple": {
        "probe": "sim_dissipative_kraus_shell_compatibility.py",
        "confidence": "medium",
        "note": "Best current parameterized operator/channel surface.",
    },
    "bridge_family_xi_point": {
        "probe": "sim_bridge_family_xi_point.py",
        "confidence": "high",
        "note": "Direct local point-bridge row on one bounded packet family, without selector or search claims.",
    },
    "axis0_kernel_phi0": {
        "probe": "sim_axis0_kernel_phi0.py",
        "confidence": "high",
        "note": "Direct late-layer signed kernel row on one bounded point-bridge family with MI kept as an unsigned companion.",
    },
    "unsigned_entropy_family": {
        "probe": "sim_unsigned_entropy_family.py",
        "confidence": "high",
        "note": "Direct late-layer unsigned entropy family {S, I} on one bounded point-bridge family, kept separate from signed Phi0 work.",
    },
    "shell_weighted_entropy_field": {
        "probe": "sim_shell_weighted_entropy_field.py",
        "confidence": "high",
        "note": "Direct late-layer shell-weighted entropy field on one bounded shell family, kept separate from history-transport bundles.",
    },
    "shell_window_support": {
        "probe": "sim_shell_window_support.py",
        "confidence": "high",
        "note": "Direct late-layer support-object lego for contiguous shell-window selection on one bounded shell family.",
    },
    "relative_entropy_nonmetric_boundary": {
        "probe": "sim_relative_entropy_nonmetric_boundary.py",
        "confidence": "high",
        "note": "Direct local falsifier showing that relative entropy fails metric behavior on a bounded state family, contrasted against trace distance.",
    },
    "hilbert_schmidt_flatness_rejection": {
        "probe": "sim_hilbert_schmidt_flatness_rejection.py",
        "confidence": "high",
        "note": "Direct local falsifier showing that near-equal Hilbert-Schmidt separation can still hide distinct curved-state geometry.",
    },
    "real_only_geometry_rejection": {
        "probe": "sim_real_only_geometry_rejection.py",
        "confidence": "high",
        "note": "Direct local falsifier showing that real-only restriction collapses distinct complex phase states and their cycle geometry.",
    },
    "gauge_group_correspondence": {
        "probe": "sim_gauge_group_correspondence.py",
        "confidence": "high",
        "note": "Direct local commutator-closure correspondence row on one bounded generator set, without broader physics identification claims.",
    },
    "viability_vs_attractor": {
        "probe": "sim_viability_vs_attractor.py",
        "confidence": "high",
        "note": "Direct local trajectory row contrasting viability-preserving and attractor-collapsing updates on one bounded admitted carrier.",
    },
    "povm_measurement_family": {
        "probe": "sim_lego_povm_measurement.py",
        "confidence": "high",
        "note": "Direct existing POVM lego.",
    },
    "measurement_instrument": {
        "probe": "sim_measurement_instrument.py",
        "confidence": "high",
        "note": "Direct local instrument lego for outcome probabilities, post-states, and induced CPTP channel consistency.",
    },
    "joint_operator_action": {
        "probe": "sim_joint_operator_action.py",
        "confidence": "high",
        "note": "Direct local two-qubit operator-action lego on a tiny admitted state set with one-step joint unitaries only.",
    },
    "channel_capacity": {
        "probe": "sim_channel_capacity.py",
        "confidence": "high",
        "note": "Direct local one-shot channel-capacity proxy lego on a tiny fixed binary ensemble.",
    },
    "partial_trace_operator": {
        "probe": "sim_reduced_state_object.py",
        "confidence": "high",
        "note": "Direct local partial-trace and marginal-consistency lego on small bipartite states.",
    },
    "reduced_state_object": {
        "probe": "sim_reduced_state_object.py",
        "confidence": "high",
        "note": "Direct local reduced-state lego on product and Bell joint states.",
    },
    "joint_density_matrix": {
        "probe": "sim_joint_density_matrix.py",
        "confidence": "high",
        "note": "Direct local joint-state lego on small valid and invalid two-qubit density operators.",
    },
    "correlation_tensor_object": {
        "probe": "sim_correlation_tensor_object.py",
        "confidence": "high",
        "note": "Direct local bipartite tensor lego on bounded product, Bell, and classical-correlation states.",
    },
    "mutual_information_measure": {
        "probe": "sim_mutual_information_measure.py",
        "confidence": "high",
        "note": "Direct local mutual-information lego on bounded two-qubit joint states.",
    },
    "von_neumann_entropy": {
        "probe": "sim_von_neumann_entropy.py",
        "confidence": "high",
        "note": "Direct local spectral von Neumann entropy lego on bounded qubit states.",
    },
    "entanglement_entropy": {
        "probe": "sim_entanglement_entropy.py",
        "confidence": "high",
        "note": "Direct local pure-state entanglement entropy lego on bounded two-qubit Schmidt-family states.",
    },
    "holevo_quantity": {
        "probe": "sim_holevo_quantity.py",
        "confidence": "high",
        "note": "Direct local Holevo-quantity lego on bounded two-state qubit ensembles.",
    },
    "relative_entropy_js": {
        "probe": "sim_relative_entropy_js.py",
        "confidence": "high",
        "note": "Direct local symmetric JS-style entropy-comparison lego on bounded qubit state pairs.",
    },
    "conditional_entropy": {
        "probe": "sim_conditional_entropy.py",
        "confidence": "high",
        "note": "Direct local conditional-entropy lego on bounded two-qubit product, Bell, and classical-mixture states.",
    },
    "shannon_entropy": {
        "probe": "sim_shannon_entropy.py",
        "confidence": "high",
        "note": "Direct local Shannon-entropy lego on explicit measurement outcome distributions, kept separate from von Neumann entropy.",
    },
    "coherent_information_measure": {
        "probe": "sim_coherent_information_measure.py",
        "confidence": "high",
        "note": "Direct local coherent-information lego on bounded two-qubit product, Bell, classical-mixture, and Werner states.",
    },
    "negativity_measure": {
        "probe": "sim_negativity_measure.py",
        "confidence": "high",
        "note": "Direct local negativity lego on bounded two-qubit product, Bell, and Werner states.",
    },
    "logarithmic_negativity": {
        "probe": "sim_negativity_measure.py",
        "confidence": "high",
        "note": "Direct local log-negativity lego on the same bounded two-qubit state family.",
    },
    "channel_cptp_map": {
        "probe": "sim_lego_choi_state_duality.py",
        "confidence": "high",
        "note": "Direct CP/TP channel legality surface via Choi duality and Kraus recovery.",
    },
    "kraus_operator_sum": {
        "probe": "sim_lego_choi_state_duality.py",
        "confidence": "high",
        "note": "Direct Kraus recovery and completeness surface from the Choi eigenstructure.",
    },
    "lindbladian_evolution": {
        "probe": "sim_lego_lindblad_dissipator.py",
        "confidence": "high",
        "note": "Direct infinitesimal open-system dynamics and dissipator-spectrum lego.",
    },
    "blackwell_style_comparison": {
        "probe": "sim_blackwell_style_comparison.py",
        "confidence": "high",
        "note": "Direct local cvc5 lego for operational informativeness via stochastic post-processing synthesis.",
    },
    "cell_complex_geometry": {
        "probe": "sim_cell_complex_geometry.py",
        "confidence": "high",
        "note": "Direct local cell-complex carrier lego with Betti and Hodge checks on bounded topology exemplars.",
    },
    "persistence_geometry": {
        "probe": "sim_persistence_geometry.py",
        "confidence": "high",
        "note": "Direct local GUDHI lego for persistence on bounded sampled carriers with distinct H1 signatures.",
    },
    "schmidt_decomposition": {
        "probe": "sim_schmidt_decomposition.py",
        "confidence": "high",
        "note": "Direct local Schmidt-factorization lego with rank, coefficient, and reconstruction checks.",
    },
}

TOOL_TARGETS = {
    "sim_pure_lego_qpca_tensor_rmt.py": ["torch"],
    "sim_pure_lego_ml_density_matrix.py": ["torch"],
    "sim_pure_lego_reference_frames.py": ["sympy"],
    "sim_lego_povm_measurement.py": ["cvc5"],
    "sim_lego_choi_state_duality.py": ["z3"],
    "sim_lego_lindblad_dissipator.py": ["sympy", "z3"],
    "sim_engine_16_placements.py": ["sympy"],
    "sim_fiber_base_transport_test.py": ["geomstats"],
    "sim_dissipative_kraus_shell_compatibility.py": ["cvc5"],
    "sim_pyg_dynamic_edge_werner.py": ["pyg"],
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def result_path_for_probe(probe: str | None) -> Path | None:
    if not probe or not probe.endswith(".py"):
        return None
    stem = probe[:-3]
    if stem.startswith("sim_"):
        stem = stem[4:]
    return RESULTS_DIR / f"{stem}_results.json"


def existing_result_truth(probe: str | None) -> dict:
    path = result_path_for_probe(probe)
    if path is None or not path.exists():
        return {}
    data = read_json(path)
    return {
        "result_json": path.name,
        "classification": data.get("classification"),
        "all_pass": data.get("all_pass"),
    }


def shallow_tools() -> set[str]:
    if not ALIGN_PATH.exists():
        return set()
    align = read_json(ALIGN_PATH)
    return set(align.get("tool_stack_summary", {}).get("shallow_tools", []))


def build_rows() -> list[dict]:
    registry = read_json(REGISTRY_PATH)
    shallow = shallow_tools()
    rows = []

    for row in registry.get("rows", []):
        if row["section"] not in SECTION_PRIORITY:
            continue
        if row["current_coverage"] not in {"not_normalized_yet", "partial"}:
            continue
        if row["section"] in {"Bridge, Axis, And Support Legos", "Boundary Falsifier Legos"}:
            continue

        target = NORMALIZATION_TARGETS.get(row["lego_id"])
        suggested_probe = row["suggested_first_probe"]
        if target is not None:
            probe = target["probe"]
            confidence = target["confidence"]
            note = target["note"]
        elif suggested_probe and suggested_probe != "no clean standalone probe yet":
            probe = suggested_probe
            confidence = "high" if row["current_coverage"] == "partial" else "medium"
            note = "Registry already points to a plausible existing probe."
        else:
            probe = None
            confidence = "low"
            note = "No reusable probe identified yet; likely needs a new dedicated local lego."

        tool_pressure = [tool for tool in TOOL_TARGETS.get(probe or "", []) if tool in shallow]
        result_truth = existing_result_truth(probe)
        needs_new_probe = probe is None or confidence == "low"
        result_truth_warning = None
        if result_truth.get("classification") == "exploratory_signal":
            result_truth_warning = "existing_probe_is_exploratory"
        elif result_truth.get("all_pass") is False:
            result_truth_warning = "existing_probe_has_failed_checks"
        priority = SECTION_PRIORITY[row["section"]]
        if row["current_coverage"] == "not_normalized_yet":
            priority -= 0.25
        if tool_pressure:
            priority -= 0.1

        rows.append({
            "lego_id": row["lego_id"],
            "lego_name": row["lego_name"],
            "section": row["section"],
            "current_coverage": row["current_coverage"],
            "priority": priority,
            "reusable_probe": probe,
            "existing_result_json": result_truth.get("result_json"),
            "existing_result_classification": result_truth.get("classification"),
            "existing_result_all_pass": result_truth.get("all_pass"),
            "result_truth_warning": result_truth_warning,
            "mapping_confidence": confidence,
            "needs_new_probe": needs_new_probe,
            "tool_pressure": tool_pressure,
            "stop_rule": (
                "Stop if the reused probe still cannot isolate this lego cleanly or remains exploratory."
                if probe
                else "Stop if a new dedicated local probe is not clearly narrower than the registry row."
            ),
            "note": note,
        })

    rows.sort(
        key=lambda item: (
            item["priority"],
            item["needs_new_probe"],
            item["mapping_confidence"] == "low",
            item["lego_id"],
        )
    )
    return rows


def main() -> int:
    rows = build_rows()
    report = {
        "name": "actual_lego_normalization_queue",
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": rows,
        "summary": {
            "task_count": len(rows),
            "existing_probe_count": sum(1 for row in rows if row["reusable_probe"]),
            "new_probe_needed_count": sum(1 for row in rows if row["needs_new_probe"]),
            "high_confidence_count": sum(1 for row in rows if row["mapping_confidence"] == "high"),
            "tool_pressure_task_count": sum(1 for row in rows if row["tool_pressure"]),
            "exploratory_probe_count": sum(1 for row in rows if row["result_truth_warning"] == "existing_probe_is_exploratory"),
        },
    }
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"task_count={report['summary']['task_count']}")
    print(f"existing_probe_count={report['summary']['existing_probe_count']}")
    print(f"new_probe_needed_count={report['summary']['new_probe_needed_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
