#!/usr/bin/env python3
"""
PURE LEGO: Weyl Geometry Protocol DAG
=====================================

Reusable protocol-order lego for nested Hopf torus geometry schedules.

This lane is intentionally narrow:
  - rustworkx is load-bearing for protocol DAG structure
  - z3 is load-bearing for precedence impossibility proofs
  - the numeric geometry checks stay bounded and reusable
  - no runtime engine claim is embedded here

The goal is a finite geometry-schedule lego that can be reused by later
Weyl/Hopf/Pauli carriers and by graph/proof alignment rows.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import rustworkx as rx
import z3

from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    density_to_bloch,
    hopf_map,
    inter_torus_transport,
    inter_torus_transport_partial,
    left_density,
    left_weyl_spinor,
    right_density,
    right_weyl_spinor,
    stereographic_s3_to_r3,
    torus_coordinates,
    torus_radii,
    torus_transport_fraction,
)


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical protocol-DAG lego for nested Weyl/Hopf geometry schedules. "
    "It keeps the graph/proof layer reusable and separate from any runtime "
    "carrier or engine claim."
)

LEGO_IDS = [
    "weyl_geometry_protocol_dag",
    "nested_hopf_torus_schedule",
]

PRIMARY_LEGO_IDS = [
    "weyl_geometry_protocol_dag",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing precedence impossibility proofs for nested geometry schedules",
    },
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite protocol DAG construction, source/sink checks, and topological ordering",
    },
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


@dataclass(frozen=True)
class GeometryFamily:
    family: str
    stages: list[str]
    edges: list[tuple[str, str]]
    negative_cycle_edge: tuple[str, str]
    negative_label: str


FAMILY = GeometryFamily(
    family="weyl_hopf_pauli_nested_schedule",
    stages=[
        "nested_hopf_torus_input",
        "left_weyl_spinor_frame",
        "pauli_bloch_projection",
        "transport_to_clifford_torus",
        "transport_to_outer_torus",
        "right_weyl_spinor_frame",
    ],
    edges=[
        ("nested_hopf_torus_input", "left_weyl_spinor_frame"),
        ("left_weyl_spinor_frame", "pauli_bloch_projection"),
        ("pauli_bloch_projection", "transport_to_clifford_torus"),
        ("transport_to_clifford_torus", "transport_to_outer_torus"),
        ("transport_to_outer_torus", "right_weyl_spinor_frame"),
    ],
    negative_cycle_edge=("right_weyl_spinor_frame", "nested_hopf_torus_input"),
    negative_label="closed_geometry_back_edge",
)


def _build_graph(stages: Iterable[str], edges: Iterable[tuple[str, str]]) -> dict:
    graph = rx.PyDiGraph()
    node_index = {stage: graph.add_node(stage) for stage in stages}
    for source, target in edges:
        graph.add_edge(node_index[source], node_index[target], f"{source}->{target}")

    is_dag = bool(rx.is_directed_acyclic_graph(graph))
    if is_dag:
        topological_order = [graph[node] for node in rx.topological_sort(graph)]
        longest_path = [graph[node] for node in rx.dag_longest_path(graph)]
    else:
        topological_order = None
        longest_path = None

    sources = [graph[node] for node in graph.node_indices() if graph.in_degree(node) == 0]
    sinks = [graph[node] for node in graph.node_indices() if graph.out_degree(node) == 0]

    return {
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "is_dag": is_dag,
        "topological_order": topological_order,
        "longest_path": longest_path,
        "longest_path_length": max(len(longest_path) - 1, 0) if longest_path is not None else None,
        "sources": sources,
        "sinks": sinks,
    }


def _prove_order_constraints(stages: list[str], edges: list[tuple[str, str]]) -> dict:
    solver = z3.Solver()
    pos = {stage: z3.Int(stage) for stage in stages}

    n = len(stages)
    for stage in stages:
        solver.add(pos[stage] >= 0, pos[stage] < n)
    solver.add(z3.Distinct([pos[stage] for stage in stages]))
    for source, target in edges:
        solver.add(pos[source] < pos[target])

    sat_correct_order = solver.check()

    reverse_solver = z3.Solver()
    for stage in stages:
        reverse_solver.add(pos[stage] >= 0, pos[stage] < n)
    reverse_solver.add(z3.Distinct([pos[stage] for stage in stages]))
    for source, target in edges:
        reverse_solver.add(pos[source] < pos[target])
    reverse_solver.add(pos[stages[-1]] < pos[stages[0]])
    reverse_verdict = reverse_solver.check()

    return {
        "correct_order_verdict": str(sat_correct_order),
        "correct_order_sat": sat_correct_order == z3.sat,
        "reverse_order_verdict": str(reverse_verdict),
        "reverse_order_unsat": reverse_verdict == z3.unsat,
    }


def _prove_cycle_control(stages: list[str], edges: list[tuple[str, str]], cycle_edge: tuple[str, str]) -> dict:
    solver = z3.Solver()
    pos = {stage: z3.Int(stage) for stage in stages}
    n = len(stages)

    for stage in stages:
        solver.add(pos[stage] >= 0, pos[stage] < n)
    solver.add(z3.Distinct([pos[stage] for stage in stages]))
    for source, target in edges + [cycle_edge]:
        solver.add(pos[source] < pos[target])

    verdict = solver.check()

    cycle_graph = _build_graph(stages, edges + [cycle_edge])
    return {
        "cycle_edge": f"{cycle_edge[0]}->{cycle_edge[1]}",
        "z3_verdict": str(verdict),
        "z3_unsat": verdict == z3.unsat,
        "graph_is_dag": cycle_graph["is_dag"],
        "graph_topological_order": cycle_graph["topological_order"],
    }


def _unit_norm(q: np.ndarray) -> float:
    return float(np.linalg.norm(q))


def _normalize_rho(rho: np.ndarray) -> np.ndarray:
    trace = np.trace(rho)
    if abs(trace) < 1e-15:
        return rho
    return rho / trace


def _sample_geometry_stack() -> dict:
    q_inner = torus_coordinates(TORUS_INNER, 0.29, 1.03)
    q_clifford = inter_torus_transport(q_inner, TORUS_INNER, TORUS_CLIFFORD)
    q_outer = inter_torus_transport(q_inner, TORUS_INNER, TORUS_OUTER)
    q_partial = inter_torus_transport_partial(q_inner, TORUS_INNER, TORUS_OUTER, 0.5)

    transport_fractions = {
        "inner_to_clifford": torus_transport_fraction(TORUS_INNER, TORUS_CLIFFORD),
        "inner_to_outer": torus_transport_fraction(TORUS_INNER, TORUS_OUTER),
        "clifford_to_outer": torus_transport_fraction(TORUS_CLIFFORD, TORUS_OUTER),
    }

    records = []
    for label, q in [
        ("inner", q_inner),
        ("clifford", q_clifford),
        ("outer", q_outer),
        ("partial_mid", q_partial),
    ]:
        psi_L = left_weyl_spinor(q)
        psi_R = right_weyl_spinor(q)
        rho_L = _normalize_rho(left_density(q))
        rho_R = _normalize_rho(right_density(q))
        bloch_L = density_to_bloch(rho_L)
        bloch_R = density_to_bloch(rho_R)
        hopf_image = hopf_map(q)
        stereo = stereographic_s3_to_r3(q)
        overlap = np.vdot(psi_L, psi_R)

        records.append(
            {
                "label": label,
                "q_norm": _unit_norm(q),
                "left_spinor_norm": float(np.linalg.norm(psi_L)),
                "right_spinor_norm": float(np.linalg.norm(psi_R)),
                "left_right_overlap_abs": float(abs(overlap)),
                "bloch_antipodal_gap": float(np.linalg.norm(bloch_L + bloch_R)),
                "hopf_image_norm_gap": float(abs(np.linalg.norm(hopf_image) - 1.0)),
                "stereographic_finite": bool(np.all(np.isfinite(stereo))),
                "stereographic_norm": float(np.linalg.norm(stereo)),
            }
        )

    max_left_right_overlap = max(row["left_right_overlap_abs"] for row in records)
    max_bloch_gap = max(row["bloch_antipodal_gap"] for row in records)
    max_hopf_gap = max(row["hopf_image_norm_gap"] for row in records)
    max_unit_error = max(abs(row["q_norm"] - 1.0) for row in records)
    all_stereographic_finite = all(row["stereographic_finite"] for row in records)

    pauli_x = np.array([[0, 1], [1, 0]], dtype=complex)
    pauli_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    pauli_z = np.array([[1, 0], [0, -1]], dtype=complex)
    pauli_i = np.eye(2, dtype=complex)
    pauli_products_ok = bool(
        np.allclose(pauli_x @ pauli_y, 1j * pauli_z)
        and np.allclose(pauli_y @ pauli_z, 1j * pauli_x)
        and np.allclose(pauli_z @ pauli_x, 1j * pauli_y)
        and np.allclose(pauli_x @ pauli_x, pauli_i)
        and np.allclose(pauli_y @ pauli_y, pauli_i)
        and np.allclose(pauli_z @ pauli_z, pauli_i)
    )

    return {
        "torus_radii": {
            "inner": torus_radii(TORUS_INNER),
            "clifford": torus_radii(TORUS_CLIFFORD),
            "outer": torus_radii(TORUS_OUTER),
        },
        "transport_fractions": transport_fractions,
        "records": records,
        "pauli_products_ok": pauli_products_ok,
        "max_left_right_overlap_abs": float(max_left_right_overlap),
        "max_bloch_antipodal_gap": float(max_bloch_gap),
        "max_hopf_image_norm_gap": float(max_hopf_gap),
        "max_unit_norm_error": float(max_unit_error),
        "all_stereographic_finite": all_stereographic_finite,
        "transport_chain_labels": ["inner", "partial_mid", "outer"],
    }


def main() -> None:
    graph_summary = _build_graph(FAMILY.stages, FAMILY.edges)
    ordering_proof = _prove_order_constraints(FAMILY.stages, FAMILY.edges)
    cycle_control = _prove_cycle_control(FAMILY.stages, FAMILY.edges, FAMILY.negative_cycle_edge)
    samples = _sample_geometry_stack()

    positive = {
        "geometry_graph_is_a_single_valid_dependency_chain": {
            **graph_summary,
            "pass": (
                graph_summary["is_dag"]
                and graph_summary["node_count"] == len(FAMILY.stages)
                and graph_summary["edge_count"] == len(FAMILY.edges)
                and graph_summary["sources"] == [FAMILY.stages[0]]
                and graph_summary["sinks"] == [FAMILY.stages[-1]]
                and graph_summary["longest_path_length"] == len(FAMILY.stages) - 1
            ),
        },
        "z3_forces_the_geometry_stack_ordering": {
            **ordering_proof,
            "pass": ordering_proof["correct_order_sat"],
        },
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
            "pass": (
                samples["max_left_right_overlap_abs"] < 1e-12
                and samples["max_bloch_antipodal_gap"] < 1e-12
            ),
        },
    }

    negative = {
        "reverse_geometry_order_is_unsat": {
            "pass": ordering_proof["reverse_order_unsat"],
            "reverse_order_verdict": ordering_proof["reverse_order_verdict"],
        },
        "back_edge_cycle_control_is_unsat": {
            "cycle_edge": cycle_control["cycle_edge"],
            "pass": cycle_control["z3_unsat"] and (cycle_control["graph_is_dag"] is False),
            "z3_verdict": cycle_control["z3_verdict"],
            "graph_is_dag": cycle_control["graph_is_dag"],
        },
        "graph_alignment_row_is_not_a_runtime_sim_claim": {
            "scope_note": (
                "This row adds a schedule graph and z3 alignment surfaces around the "
                "nested Weyl/Hopf/Pauli geometry stack. It does not claim a new runtime engine."
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
                samples["transport_fractions"]["inner_to_clifford"]
                < samples["transport_fractions"]["inner_to_outer"]
                and samples["transport_fractions"]["clifford_to_outer"] <= 1.0
            ),
        },
        "topological_order_matches_the_geometry_stack": {
            "topological_order": graph_summary["topological_order"],
            "pass": graph_summary["topological_order"] == FAMILY.stages,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "weyl_geometry_protocol_dag",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "rows": [
            {
                "family": FAMILY.family,
                "stages": FAMILY.stages,
                "edges": [f"{a}->{b}" for a, b in FAMILY.edges],
                "negative_control": FAMILY.negative_label,
                "graph": graph_summary,
                "proofs": {
                    "order_constraints": ordering_proof,
                    "cycle_control": cycle_control,
                },
                "positive": positive,
                "negative": negative,
                "boundary": boundary,
            }
        ],
        "summary": {
            "all_pass": all_pass,
            "graph_path_length": graph_summary["longest_path_length"],
            "schedule_valid": positive["geometry_graph_is_a_single_valid_dependency_chain"]["pass"],
            "ordering_unsat": ordering_proof["reverse_order_unsat"],
            "cycle_control_unsat": cycle_control["z3_unsat"],
            "pauli_products_ok": samples["pauli_products_ok"],
            "max_left_right_overlap_abs": samples["max_left_right_overlap_abs"],
            "max_bloch_antipodal_gap": samples["max_bloch_antipodal_gap"],
            "max_hopf_image_norm_gap": samples["max_hopf_image_norm_gap"],
            "transport_chain_labels": samples["transport_chain_labels"],
            "torus_radii": samples["torus_radii"],
            "scope_note": (
                "Reusable graph/proof lego for the nested Weyl/Hopf/Pauli geometry schedule. "
                "Useful as a pre-constraint alignment row."
            ),
        },
    }

    out_path = RESULT_DIR / "lego_weyl_geometry_protocol_dag_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str) + "\n")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
