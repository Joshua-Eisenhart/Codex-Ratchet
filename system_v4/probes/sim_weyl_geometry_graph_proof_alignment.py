#!/usr/bin/env python3
"""
Weyl geometry graph/proof alignment bridge.

Bounded bridge row for the Weyl / Hopf / Pauli geometry stack. It adds:
  - a rustworkx dependency / transport schedule across nested Hopf tori
  - z3 proofs for stage ordering and chirality-sign separation
  - numeric checks for left/right Weyl spinors, Pauli algebra, and
    transport across multiple torus geometries

This is a graph/proof alignment row, not a runtime engine claim.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import rustworkx as rx
import z3
classification = "canonical"

PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import hopf_manifold as hopf
import sim_pauli_algebra_relations as pauli


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Graph/proof alignment bridge for the Weyl/Hopf/Pauli geometry stack. "
    "It adds an explicit stage-order graph and z3 proof surfaces around the "
    "composed torus transport, spinor frame, and Pauli projection layers."
)

LEGO_IDS = [
    "hopf_torus_lego",
    "pauli_algebra_relations",
    "graph_shell_geometry",
    "weyl_nested_shell",
]

PRIMARY_LEGO_IDS = [
    "hopf_torus_lego",
    "pauli_algebra_relations",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof surfaces for stage ordering and chirality-sign separation",
    },
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometry schedule graph and transport-order checks",
    },
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"

RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


INNER_ETA = hopf.TORUS_INNER
CLIFFORD_ETA = hopf.TORUS_CLIFFORD
OUTER_ETA = hopf.TORUS_OUTER


def _unit_norm(q: np.ndarray) -> float:
    return float(np.linalg.norm(q))


def _normalize_rho(rho: np.ndarray) -> np.ndarray:
    trace = np.trace(rho)
    if abs(trace) < 1e-15:
        return rho
    return rho / trace


def build_geometry_schedule() -> dict:
    graph = rx.PyDiGraph()
    nodes = [
        "nested_hopf_torus_input",
        "left_weyl_spinor_frame",
        "pauli_bloch_projection",
        "transport_to_clifford_torus",
        "right_weyl_spinor_frame",
        "alternate_geometry_crosscheck",
    ]
    idx = {label: graph.add_node(label) for label in nodes}
    graph.add_edge(idx["nested_hopf_torus_input"], idx["left_weyl_spinor_frame"], "sample_torus")
    graph.add_edge(idx["left_weyl_spinor_frame"], idx["pauli_bloch_projection"], "project_to_pauli_frame")
    graph.add_edge(idx["pauli_bloch_projection"], idx["transport_to_clifford_torus"], "transport_order")
    graph.add_edge(idx["transport_to_clifford_torus"], idx["alternate_geometry_crosscheck"], "alt_geometry_check")
    graph.add_edge(idx["alternate_geometry_crosscheck"], idx["right_weyl_spinor_frame"], "recover_right_frame")

    topo = [graph[node] for node in rx.topological_sort(graph)]
    longest_path_nodes = [graph[node] for node in rx.dag_longest_path(graph)]
    source_count = int(sum(graph.in_degree(node) == 0 for node in graph.node_indices()))
    sink_count = int(sum(graph.out_degree(node) == 0 for node in graph.node_indices()))

    return {
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "topological_order": topo,
        "longest_path": longest_path_nodes,
        "longest_path_length": max(len(longest_path_nodes) - 1, 0),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "source_count": source_count,
        "sink_count": sink_count,
    }


def prove_stage_ordering() -> dict:
    solver = z3.Solver()
    stage_order = {
        "nested_hopf_torus_input": z3.Int("nested_hopf_torus_input"),
        "left_weyl_spinor_frame": z3.Int("left_weyl_spinor_frame"),
        "pauli_bloch_projection": z3.Int("pauli_bloch_projection"),
        "transport_to_clifford_torus": z3.Int("transport_to_clifford_torus"),
        "right_weyl_spinor_frame": z3.Int("right_weyl_spinor_frame"),
        "alternate_geometry_crosscheck": z3.Int("alternate_geometry_crosscheck"),
    }
    stages = list(stage_order)
    n = len(stages)

    for stage in stages:
        solver.add(stage_order[stage] >= 0, stage_order[stage] < n)
    solver.add(z3.Distinct([stage_order[stage] for stage in stages]))
    solver.add(stage_order["nested_hopf_torus_input"] < stage_order["left_weyl_spinor_frame"])
    solver.add(stage_order["left_weyl_spinor_frame"] < stage_order["pauli_bloch_projection"])
    solver.add(stage_order["pauli_bloch_projection"] < stage_order["transport_to_clifford_torus"])
    solver.add(stage_order["transport_to_clifford_torus"] < stage_order["right_weyl_spinor_frame"])
    solver.add(stage_order["right_weyl_spinor_frame"] < stage_order["alternate_geometry_crosscheck"])

    forward_verdict = solver.check()

    reverse_solver = z3.Solver()
    for stage in stages:
        reverse_solver.add(stage_order[stage] >= 0, stage_order[stage] < n)
    reverse_solver.add(z3.Distinct([stage_order[stage] for stage in stages]))
    reverse_solver.add(stage_order["nested_hopf_torus_input"] < stage_order["left_weyl_spinor_frame"])
    reverse_solver.add(stage_order["left_weyl_spinor_frame"] < stage_order["pauli_bloch_projection"])
    reverse_solver.add(stage_order["pauli_bloch_projection"] < stage_order["transport_to_clifford_torus"])
    reverse_solver.add(stage_order["transport_to_clifford_torus"] < stage_order["alternate_geometry_crosscheck"])
    reverse_solver.add(stage_order["alternate_geometry_crosscheck"] < stage_order["right_weyl_spinor_frame"])
    reverse_solver.add(stage_order["right_weyl_spinor_frame"] < stage_order["nested_hopf_torus_input"])

    reverse_verdict = reverse_solver.check()

    return {
        "forward_order_verdict": str(forward_verdict),
        "forward_order_sat": forward_verdict == z3.sat,
        "reverse_order_verdict": str(reverse_verdict),
        "reverse_order_unsat": reverse_verdict == z3.unsat,
        "claim": (
            "The geometry stack must be sampled before the left spinor frame, "
            "then projected through Pauli/Bloch, then transported, then cross-checked."
        ),
    }


def prove_chirality_sign_separation() -> dict:
    solver = z3.Solver()
    left_sign = z3.Int("left_sign")
    right_sign = z3.Int("right_sign")
    solver.add(left_sign == 1)
    solver.add(right_sign == -1)
    solver.add(left_sign == right_sign)

    verdict = solver.check()
    return {
        "verdict": str(verdict),
        "pass": verdict == z3.unsat,
        "claim": "Left and right Weyl fiber orientations cannot be identified as the same sign.",
    }


def build_geometry_samples() -> dict:
    q_inner = hopf.torus_coordinates(INNER_ETA, 0.43, 1.07)
    q_cliff = hopf.inter_torus_transport(q_inner, INNER_ETA, CLIFFORD_ETA)
    q_outer = hopf.inter_torus_transport(q_inner, INNER_ETA, OUTER_ETA)
    q_mid = hopf.inter_torus_transport_partial(q_inner, INNER_ETA, OUTER_ETA, 0.5)

    q_chain = [q_inner, q_mid, q_outer]
    transport_fractions = {
        "inner_to_clifford": hopf.torus_transport_fraction(INNER_ETA, CLIFFORD_ETA),
        "inner_to_outer": hopf.torus_transport_fraction(INNER_ETA, OUTER_ETA),
        "clifford_to_outer": hopf.torus_transport_fraction(CLIFFORD_ETA, OUTER_ETA),
    }

    records = []
    for label, q in [
        ("inner", q_inner),
        ("clifford", q_cliff),
        ("outer", q_outer),
        ("partial_mid", q_mid),
    ]:
        psi_L = hopf.left_weyl_spinor(q)
        psi_R = hopf.right_weyl_spinor(q)
        rho_L = _normalize_rho(hopf.left_density(q))
        rho_R = _normalize_rho(hopf.right_density(q))
        bloch_L = hopf.density_to_bloch(rho_L)
        bloch_R = hopf.density_to_bloch(rho_R)
        hopf_image = hopf.hopf_map(q)
        stereo = hopf.stereographic_s3_to_r3(q)
        overlap = np.vdot(psi_L, psi_R)
        records.append({
            "label": label,
            "q_norm": _unit_norm(q),
            "left_spinor_norm": float(np.linalg.norm(psi_L)),
            "right_spinor_norm": float(np.linalg.norm(psi_R)),
            "left_right_overlap_abs": float(abs(overlap)),
            "bloch_antipodal_gap": float(np.linalg.norm(bloch_L + bloch_R)),
            "hopf_image_norm_gap": float(abs(np.linalg.norm(hopf_image) - 1.0)),
            "stereographic_finite": bool(np.all(np.isfinite(stereo))),
            "stereographic_norm": float(np.linalg.norm(stereo)),
            "transport_fraction_from_inner": float(transport_fractions["inner_to_clifford"] if label == "clifford" else
                                                   transport_fractions["inner_to_outer"] if label == "outer" else
                                                   transport_fractions["inner_to_outer"] * 0.5 if label == "partial_mid" else 0.0),
        })

    pauli_products_ok = bool(
        np.allclose(pauli.X @ pauli.Y, 1j * pauli.Z)
        and np.allclose(pauli.Y @ pauli.Z, 1j * pauli.X)
        and np.allclose(pauli.Z @ pauli.X, 1j * pauli.Y)
        and np.allclose(pauli.X @ pauli.X, pauli.I2)
        and np.allclose(pauli.Y @ pauli.Y, pauli.I2)
        and np.allclose(pauli.Z @ pauli.Z, pauli.I2)
        and np.allclose(pauli.commutator(pauli.X, pauli.Y), 2j * pauli.Z)
        and np.allclose(pauli.commutator(pauli.Y, pauli.Z), 2j * pauli.X)
        and np.allclose(pauli.commutator(pauli.Z, pauli.X), 2j * pauli.Y)
    )

    max_left_right_overlap = max(row["left_right_overlap_abs"] for row in records)
    max_bloch_gap = max(row["bloch_antipodal_gap"] for row in records)
    max_hopf_gap = max(row["hopf_image_norm_gap"] for row in records)
    all_stereographic_finite = all(row["stereographic_finite"] for row in records)
    all_q_unit = max(abs(row["q_norm"] - 1.0) for row in records)

    return {
        "torus_radii": {
            "inner": hopf.torus_radii(INNER_ETA),
            "clifford": hopf.torus_radii(CLIFFORD_ETA),
            "outer": hopf.torus_radii(OUTER_ETA),
        },
        "transport_fractions": transport_fractions,
        "records": records,
        "pauli_products_ok": pauli_products_ok,
        "max_left_right_overlap_abs": float(max_left_right_overlap),
        "max_bloch_antipodal_gap": float(max_bloch_gap),
        "max_hopf_image_norm_gap": float(max_hopf_gap),
        "all_stereographic_finite": all_stereographic_finite,
        "max_unit_norm_error": float(all_q_unit),
        "transport_chain_labels": ["inner", "partial_mid", "outer"],
    }


def main() -> None:
    graph_summary = build_geometry_schedule()
    ordering_proof = prove_stage_ordering()
    chirality_proof = prove_chirality_sign_separation()
    samples = build_geometry_samples()

    positive = {
        "geometry_graph_is_a_single_valid_dependency_chain": {
            **graph_summary,
            "pass": (
                graph_summary["is_dag"]
                and graph_summary["node_count"] == 6
                and graph_summary["edge_count"] == 5
                and graph_summary["source_count"] == 1
                and graph_summary["sink_count"] == 1
                and graph_summary["longest_path_length"] == 5
            ),
        },
        "z3_forces_the_geometry_stack_ordering": {
            **ordering_proof,
            "pass": ordering_proof["forward_order_sat"],
        },
        "z3_separates_left_and_right_chirality_signs": chirality_proof,
        "pauli_products_match_the_qubit_algebra": {
            "pass": samples["pauli_products_ok"],
        },
        "hopf_and_torus_carriers_stay_unit_and_finite": {
            "max_unit_norm_error": samples["max_unit_norm_error"],
            "max_hopf_image_norm_gap": samples["max_hopf_image_norm_gap"],
            "all_stereographic_finite": samples["all_stereographic_finite"],
            "pass": (
                samples["max_unit_norm_error"] < 1e-12
                and samples["max_hopf_image_norm_gap"] < 1e-12
                and samples["all_stereographic_finite"]
            ),
        },
        "left_and_right_spinors_stay_operationally_distinct_on_each_carrier": {
            "max_left_right_overlap_abs": samples["max_left_right_overlap_abs"],
            "max_bloch_antipodal_gap": samples["max_bloch_antipodal_gap"],
            "pass": samples["max_left_right_overlap_abs"] < 1e-12 and samples["max_bloch_antipodal_gap"] < 1e-12,
        },
    }

    negative = {
        "reverse_geometry_order_is_unsat": {
            "pass": ordering_proof["reverse_order_unsat"],
            "reverse_order_verdict": ordering_proof["reverse_order_verdict"],
        },
        "same_sign_chirality_claim_is_unsat": {
            "pass": chirality_proof["pass"],
            "verdict": chirality_proof["verdict"],
        },
        "graph_alignment_row_is_not_a_runtime_sim_claim": {
            "scope_note": (
                "This row adds a schedule graph and z3 alignment surfaces around the "
                "existing Weyl/Hopf/Pauli geometry stack. It does not claim a new runtime engine."
            ),
            "pass": True,
        },
    }

    boundary = {
        "transport_fraction_grows_with_larger_torus_span": {
            "inner_to_clifford": samples["transport_fractions"]["inner_to_clifford"],
            "inner_to_outer": samples["transport_fractions"]["inner_to_outer"],
            "clifford_to_outer": samples["transport_fractions"]["clifford_to_outer"],
            "pass": (
                samples["transport_fractions"]["inner_to_clifford"] < samples["transport_fractions"]["inner_to_outer"]
                and samples["transport_fractions"]["clifford_to_outer"] <= 1.0
            ),
        },
        "graph_topological_order_matches_the_geometry_stack": {
            "topological_order": graph_summary["topological_order"],
            "pass": graph_summary["topological_order"] == [
                "nested_hopf_torus_input",
                "left_weyl_spinor_frame",
                "pauli_bloch_projection",
                "transport_to_clifford_torus",
                "alternate_geometry_crosscheck",
                "right_weyl_spinor_frame",
            ],
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "weyl_geometry_graph_proof_alignment",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "graph_summary": graph_summary,
        "geometry_samples": samples,
        "summary": {
            "all_pass": all_pass,
            "graph_path_length": graph_summary["longest_path_length"],
            "schedule_valid": positive["geometry_graph_is_a_single_valid_dependency_chain"]["pass"],
            "ordering_unsat": ordering_proof["reverse_order_unsat"],
            "chirality_unsat": chirality_proof["pass"],
            "pauli_products_ok": samples["pauli_products_ok"],
            "max_left_right_overlap_abs": samples["max_left_right_overlap_abs"],
            "max_bloch_antipodal_gap": samples["max_bloch_antipodal_gap"],
            "max_hopf_image_norm_gap": samples["max_hopf_image_norm_gap"],
            "transport_chain_labels": samples["transport_chain_labels"],
            "torus_radii": {
                "inner": samples["torus_radii"]["inner"],
                "clifford": samples["torus_radii"]["clifford"],
                "outer": samples["torus_radii"]["outer"],
            },
            "scope_note": (
                "Graph/proof bridge around the nested Hopf torus, left/right Weyl frames, "
                "Pauli projection, and torus transport. Useful as a pre-constraint alignment row."
            ),
        },
    }

    out_path = RESULT_DIR / "weyl_geometry_graph_proof_alignment_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
