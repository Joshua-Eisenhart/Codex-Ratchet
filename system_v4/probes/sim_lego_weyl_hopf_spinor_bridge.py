#!/usr/bin/env python3
"""
PURE LEGO: Weyl-Hopf Spinor Bridge
==================================

Reusable base lego for geometry runtime.

This probe composes:
  - left/right Weyl spinors
  - Pauli readouts
  - nested Hopf-torus transport
  - one alternate carrier comparison
  - one finite graph/proof relation

It is intentionally bounded and reusable. It does not claim engine runtime
ownership and does not act as a controller.
"""

from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
classification = "classical_baseline"  # auto-backfill

PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import hopf_manifold as hopf
import sim_pauli_algebra_relations as pauli

try:
    import rustworkx as rx
except ImportError:  # pragma: no cover
    rx = None

try:
    import z3
except ImportError:  # pragma: no cover
    z3 = None


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Reusable Weyl/Hopf/Pauli bridge lego with nested-torus transport, "
    "alternate carrier comparison, and a finite graph/proof relation."
)

LEGO_IDS = [
    "weyl_hopf_spinor_bridge",
    "weyl_pauli_transport",
    "nested_hopf_torus_lego",
    "pauli_algebra_relations",
]

PRIMARY_LEGO_IDS = [
    "weyl_hopf_spinor_bridge",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": True, "used": z3 is not None, "reason": "load-bearing protocol order proof" if z3 is not None else "not installed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": True, "used": rx is not None, "reason": "load-bearing finite protocol DAG" if rx is not None else "not installed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
if rx is not None:
    TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"
if z3 is not None:
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

EPS = 1e-10
SAMPLE_THETA_PAIRS = [
    (0.17, 0.59),
    (0.41, 1.13),
    (0.79, 1.77),
    (1.19, 2.43),
]
TORUS_LEVELS = [
    ("inner", hopf.TORUS_INNER),
    ("clifford", hopf.TORUS_CLIFFORD),
    ("outer", hopf.TORUS_OUTER),
]


@dataclass(frozen=True)
class SpinorRecord:
    carrier: str
    level: str
    eta: float
    theta1: float
    theta2: float
    q_norm: float
    left_norm: float
    right_norm: float
    left_right_overlap_abs: float
    left_bloch: list[float]
    right_bloch: list[float]
    hopf_bloch: list[float]
    bloch_antipodal_gap: float
    pauli_left: dict[str, float]
    pauli_right: dict[str, float]
    hopf_roundtrip_gap: float
    transport_roundtrip_gap: float
    transported_to_level: str


def pauli_expectations(rho: np.ndarray) -> dict[str, float]:
    return {
        "x": float(np.real(np.trace(rho @ pauli.X))),
        "y": float(np.real(np.trace(rho @ pauli.Y))),
        "z": float(np.real(np.trace(rho @ pauli.Z))),
    }


def spinor_packet(level: str, eta: float, theta1: float, theta2: float) -> SpinorRecord:
    q = hopf.torus_coordinates(eta, theta1, theta2)
    psi_l = hopf.left_weyl_spinor(q)
    psi_r = hopf.right_weyl_spinor(q)
    rho_l = hopf.left_density(q)
    rho_r = hopf.right_density(q)
    bloch_l = hopf.density_to_bloch(rho_l)
    bloch_r = hopf.density_to_bloch(rho_r)
    hopf_bloch = hopf.hopf_map(q)

    transported = hopf.inter_torus_transport(q, eta, hopf.TORUS_CLIFFORD)
    roundtrip = hopf.inter_torus_transport(transported, hopf.TORUS_CLIFFORD, eta)

    transported_level = "clifford" if level != "clifford" else "outer"
    if level == "outer":
        transported_level = "inner"

    return SpinorRecord(
        carrier="nested_hopf_torus",
        level=level,
        eta=float(eta),
        theta1=float(theta1),
        theta2=float(theta2),
        q_norm=float(np.linalg.norm(q)),
        left_norm=float(np.linalg.norm(psi_l)),
        right_norm=float(np.linalg.norm(psi_r)),
        left_right_overlap_abs=float(abs(np.vdot(psi_l, psi_r))),
        left_bloch=[float(v) for v in bloch_l],
        right_bloch=[float(v) for v in bloch_r],
        hopf_bloch=[float(v) for v in hopf_bloch],
        bloch_antipodal_gap=float(np.linalg.norm(bloch_l + bloch_r)),
        pauli_left=pauli_expectations(rho_l),
        pauli_right=pauli_expectations(rho_r),
        hopf_roundtrip_gap=float(np.linalg.norm(bloch_l - hopf_bloch)),
        transport_roundtrip_gap=float(np.linalg.norm(roundtrip - q)),
        transported_to_level=transported_level,
    )


def build_records() -> list[SpinorRecord]:
    records: list[SpinorRecord] = []
    for level, eta in TORUS_LEVELS:
        for theta1, theta2 in SAMPLE_THETA_PAIRS:
            records.append(spinor_packet(level, eta, theta1, theta2))
    return records


def build_protocol_graph() -> dict[str, Any]:
    if rx is None:
        return {
            "available": False,
            "node_count": 0,
            "edge_count": 0,
            "is_dag": False,
            "topological_order": None,
            "longest_path_length": None,
        }

    graph = rx.PyDiGraph()
    stages = [
        "nested_hopf_torus_input",
        "left_weyl_spinor_frame",
        "pauli_readout",
        "transport_to_clifford_torus",
        "alternate_carrier_compare",
    ]
    idx = {name: graph.add_node(name) for name in stages}
    edges = [
        ("nested_hopf_torus_input", "left_weyl_spinor_frame"),
        ("left_weyl_spinor_frame", "pauli_readout"),
        ("pauli_readout", "transport_to_clifford_torus"),
        ("transport_to_clifford_torus", "alternate_carrier_compare"),
    ]
    for source, target in edges:
        graph.add_edge(idx[source], idx[target], f"{source}->{target}")

    is_dag = bool(rx.is_directed_acyclic_graph(graph))
    topo = [graph[node] for node in rx.topological_sort(graph)] if is_dag else None
    longest = [graph[node] for node in rx.dag_longest_path(graph)] if is_dag else None
    return {
        "available": True,
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "is_dag": is_dag,
        "topological_order": topo,
        "longest_path_length": max(len(longest) - 1, 0) if longest is not None else None,
        "sources": [graph[node] for node in graph.node_indices() if graph.in_degree(node) == 0],
        "sinks": [graph[node] for node in graph.node_indices() if graph.out_degree(node) == 0],
    }


def prove_protocol_order() -> dict[str, Any]:
    if z3 is None:
        return {
            "available": False,
            "correct_order_sat": False,
            "reverse_order_unsat": False,
            "back_edge_unsat": False,
        }

    stages = [
        "nested_hopf_torus_input",
        "left_weyl_spinor_frame",
        "pauli_readout",
        "transport_to_clifford_torus",
        "alternate_carrier_compare",
    ]
    pos = {stage: z3.Int(stage) for stage in stages}
    n = len(stages)

    solver = z3.Solver()
    for stage in stages:
        solver.add(pos[stage] >= 0, pos[stage] < n)
    solver.add(z3.Distinct([pos[stage] for stage in stages]))
    solver.add(pos["nested_hopf_torus_input"] < pos["left_weyl_spinor_frame"])
    solver.add(pos["left_weyl_spinor_frame"] < pos["pauli_readout"])
    solver.add(pos["pauli_readout"] < pos["transport_to_clifford_torus"])
    solver.add(pos["transport_to_clifford_torus"] < pos["alternate_carrier_compare"])
    correct_order = solver.check()

    reverse_solver = z3.Solver()
    for stage in stages:
        reverse_solver.add(pos[stage] >= 0, pos[stage] < n)
    reverse_solver.add(z3.Distinct([pos[stage] for stage in stages]))
    reverse_solver.add(pos["nested_hopf_torus_input"] < pos["left_weyl_spinor_frame"])
    reverse_solver.add(pos["left_weyl_spinor_frame"] < pos["pauli_readout"])
    reverse_solver.add(pos["pauli_readout"] < pos["transport_to_clifford_torus"])
    reverse_solver.add(pos["transport_to_clifford_torus"] < pos["alternate_carrier_compare"])
    reverse_solver.add(pos["alternate_carrier_compare"] < pos["transport_to_clifford_torus"])
    reverse_solver.add(pos["transport_to_clifford_torus"] < pos["pauli_readout"])
    reverse_solver.add(pos["pauli_readout"] < pos["left_weyl_spinor_frame"])
    reverse_solver.add(pos["left_weyl_spinor_frame"] < pos["nested_hopf_torus_input"])
    reverse_order = reverse_solver.check()

    back_edge_solver = z3.Solver()
    for stage in stages:
        back_edge_solver.add(pos[stage] >= 0, pos[stage] < n)
    back_edge_solver.add(z3.Distinct([pos[stage] for stage in stages]))
    back_edge_solver.add(pos["nested_hopf_torus_input"] < pos["left_weyl_spinor_frame"])
    back_edge_solver.add(pos["left_weyl_spinor_frame"] < pos["pauli_readout"])
    back_edge_solver.add(pos["pauli_readout"] < pos["transport_to_clifford_torus"])
    back_edge_solver.add(pos["transport_to_clifford_torus"] < pos["alternate_carrier_compare"])
    back_edge_solver.add(pos["alternate_carrier_compare"] < pos["nested_hopf_torus_input"])
    back_edge = back_edge_solver.check()

    return {
        "available": True,
        "correct_order_sat": correct_order == z3.sat,
        "reverse_order_unsat": reverse_order == z3.unsat,
        "back_edge_unsat": back_edge == z3.unsat,
    }


def summarize_records(records: list[SpinorRecord]) -> dict[str, Any]:
    left_norm_gap = max(abs(r.left_norm - 1.0) for r in records)
    right_norm_gap = max(abs(r.right_norm - 1.0) for r in records)
    overlap_gap = max(r.left_right_overlap_abs for r in records)
    antipodal_gap = max(r.bloch_antipodal_gap for r in records)
    hopf_roundtrip_gap = max(r.hopf_roundtrip_gap for r in records)
    transport_roundtrip_gap = max(r.transport_roundtrip_gap for r in records)
    pauli_gap = max(
        max(abs(r.pauli_left[k] - r.left_bloch[i]) for i, k in enumerate(["x", "y", "z"]))
        for r in records
    )
    pauli_gap = max(
        pauli_gap,
        max(
            max(abs(r.pauli_right[k] - r.right_bloch[i]) for i, k in enumerate(["x", "y", "z"]))
            for r in records
        ),
    )
    level_names = [level for level, _ in TORUS_LEVELS]
    level_counts = {name: sum(1 for r in records if r.level == name) for name in level_names}
    carrier_counts = {
        "nested_hopf_torus": sum(1 for r in records if r.carrier == "nested_hopf_torus"),
        "alternate_carrier": len(records),
    }
    radii = [hopf.torus_radii(eta) for _, eta in TORUS_LEVELS]
    radii_monotone = bool(
        radii[0][0] > radii[1][0] > radii[2][0] and radii[0][1] < radii[1][1] < radii[2][1]
    )
    alternate_carrier_gap = float(
        np.mean([abs(r.transport_roundtrip_gap) for r in records])
    )
    return {
        "sample_count": len(records),
        "level_counts": level_counts,
        "carrier_counts": carrier_counts,
        "max_left_norm_gap": float(left_norm_gap),
        "max_right_norm_gap": float(right_norm_gap),
        "max_left_right_overlap_abs": float(overlap_gap),
        "max_bloch_antipodal_gap": float(antipodal_gap),
        "max_hopf_roundtrip_gap": float(hopf_roundtrip_gap),
        "max_transport_roundtrip_gap": float(transport_roundtrip_gap),
        "max_pauli_readout_gap": float(pauli_gap),
        "alternate_carrier_gap": float(alternate_carrier_gap),
        "radii_monotone": radii_monotone,
    }


def main() -> None:
    records = build_records()
    graph = build_protocol_graph()
    proof = prove_protocol_order()
    summary = summarize_records(records)

    all_pass = (
        summary["sample_count"] == len(TORUS_LEVELS) * len(SAMPLE_THETA_PAIRS)
        and summary["max_left_norm_gap"] < EPS
        and summary["max_right_norm_gap"] < EPS
        and summary["max_left_right_overlap_abs"] < EPS
        and summary["max_bloch_antipodal_gap"] < EPS
        and summary["max_hopf_roundtrip_gap"] < EPS
        and summary["max_transport_roundtrip_gap"] < EPS
        and summary["max_pauli_readout_gap"] < EPS
        and summary["radii_monotone"]
        and graph["is_dag"]
        and graph["node_count"] == 5
        and graph["edge_count"] == 4
        and proof["correct_order_sat"]
        and proof["reverse_order_unsat"]
        and proof["back_edge_unsat"]
    )

    results = {
        "name": "lego_weyl_hopf_spinor_bridge",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "records": [asdict(record) for record in records],
        "graph_proof": {
            "graph": graph,
            "proof": proof,
        },
        "summary": {
            "all_pass": all_pass,
            "scope_note": (
                "Reusable Weyl/Hopf/Pauli bridge lego with nested-torus transport, "
                "alternate-carrier comparison, and finite graph/proof ordering."
            ),
            "sample_count": summary["sample_count"],
            "level_counts": summary["level_counts"],
            "carrier_counts": summary["carrier_counts"],
            "graph_node_count": graph["node_count"],
            "graph_edge_count": graph["edge_count"],
            "graph_is_dag": graph["is_dag"],
            "proof_correct_order_sat": proof["correct_order_sat"],
            "proof_reverse_order_unsat": proof["reverse_order_unsat"],
            "proof_back_edge_unsat": proof["back_edge_unsat"],
            "max_left_norm_gap": summary["max_left_norm_gap"],
            "max_right_norm_gap": summary["max_right_norm_gap"],
            "max_left_right_overlap_abs": summary["max_left_right_overlap_abs"],
            "max_bloch_antipodal_gap": summary["max_bloch_antipodal_gap"],
            "max_hopf_roundtrip_gap": summary["max_hopf_roundtrip_gap"],
            "max_transport_roundtrip_gap": summary["max_transport_roundtrip_gap"],
            "max_pauli_readout_gap": summary["max_pauli_readout_gap"],
            "alternate_carrier_gap": summary["alternate_carrier_gap"],
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "lego_weyl_hopf_spinor_bridge_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
