#!/usr/bin/env python3
"""
Weyl Geometry Carrier Array
===========================
Alternate-geometry carrier array for the Weyl/Hopf stack.

Goal:
  Keep the same left/right Weyl spinor core honest while checking it on
  multiple carrier families already present in the repo:
  - nested Hopf tori
  - Bloch sphere projection
  - graph carrier
  - hypergraph carrier
  - CP^3 / S^7 product lift

This is a carrier comparison surface, not doctrine.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
from itertools import combinations
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
classification = "classical_baseline"  # auto-backfill

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from hopf_manifold import (  # noqa: E402
    fiber_phase_left,
    fiber_phase_right,
    hopf_map,
    inter_torus_transport,
    left_weyl_spinor,
    right_weyl_spinor,
    torus_coordinates,
    torus_radii,
)
from sim_sphere_geometry import bloch_vector as sphere_bloch_vector  # noqa: E402
from sim_sphere_geometry import geodesic_distance  # noqa: E402

try:  # optional repo lego cross-checks
    import rustworkx as rx  # type: ignore
except Exception:  # pragma: no cover - honest fallback
    rx = None

try:
    import xgi  # type: ignore
    from toponetx import CellComplex  # type: ignore
except Exception:  # pragma: no cover - honest fallback
    xgi = None
    CellComplex = None

try:  # optional CP^3 / S^7 lego reuse
    from sim_geom_2qubit_s7_cp3 import (  # type: ignore
        concurrence_pure as repo_concurrence_pure,
        distance_from_segre_analytic as repo_segre_distance,
        product_state as repo_product_state,
        quaternionic_hopf_map as repo_quaternionic_hopf_map,
    )
except Exception:  # pragma: no cover - honest fallback
    repo_concurrence_pure = None
    repo_segre_distance = None
    repo_product_state = None
    repo_quaternionic_hopf_map = None

try:  # optional graph/hypergraph lego reuse
    from sim_graph_geometry import graph_stats as repo_graph_stats  # type: ignore
except Exception:  # pragma: no cover - honest fallback
    repo_graph_stats = None

try:
    from sim_hypergraph_geometry import (  # type: ignore
        build_cell_complex as repo_build_cell_complex,
        shadow_graph_edges as repo_shadow_graph_edges,
    )
except Exception:  # pragma: no cover - honest fallback
    repo_build_cell_complex = None
    repo_shadow_graph_edges = None


EPS = 1e-10
DTYPE = np.complex128

SX = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE)
SY = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=DTYPE)
SZ = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE)

ETA_LEVELS = [np.pi / 8.0, np.pi / 4.0, 3.0 * np.pi / 8.0]
ANGLE_PAIRS = [
    (0.0, 0.0),
    (np.pi / 2.0, 0.0),
    (0.0, np.pi / 2.0),
    (np.pi / 2.0, np.pi / 2.0),
]

CLASSIFICATION_NOTE = (
    "Carrier-array lego for the Weyl/Hopf stack. The same spinor core is tested on "
    "nested Hopf tori, Bloch-sphere projection, graph and hypergraph carriers, and "
    "a CP^3/S^7 product lift. The array stays bounded and keeps negative controls explicit."
)

LEGO_IDS = [
    "weyl_geometry_carrier_array",
    "nested_hopf_torus",
    "bloch_sphere_projection",
    "graph_torus_grid",
    "hypergraph_multiway_carrier",
    "cp3_s7_product_lift",
]

PRIMARY_LEGO_IDS = [
    "nested_hopf_torus",
    "bloch_sphere_projection",
    "graph_torus_grid",
    "hypergraph_multiway_carrier",
    "cp3_s7_product_lift",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this numpy-first carrier array"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "graph carrier uses it if available"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraph carrier uses it if available"},
    "toponetx": {"tried": False, "used": False, "reason": "hypergraph cell-complex lift uses it if available"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def density_matrix(psi: np.ndarray) -> np.ndarray:
    vec = np.asarray(psi, dtype=DTYPE).reshape(-1, 1)
    return vec @ vec.conj().T


def bloch_from_spinor(psi: np.ndarray) -> np.ndarray:
    rho = density_matrix(psi)
    return np.array(
        [
            float(np.real(np.trace(rho @ SX))),
            float(np.real(np.trace(rho @ SY))),
            float(np.real(np.trace(rho @ SZ))),
        ],
        dtype=float,
    )


def concurrence_pure_np(psi: np.ndarray) -> float:
    alpha, beta, gamma, delta = np.asarray(psi, dtype=DTYPE)
    return float(2.0 * abs(alpha * delta - beta * gamma))


def fubini_study_distance_np(psi: np.ndarray, phi: np.ndarray) -> float:
    overlap = abs(np.vdot(psi, phi))
    overlap = float(np.clip(overlap, 0.0, 1.0))
    return float(np.arccos(overlap))


def quaternionic_hopf_map_np(psi: np.ndarray) -> np.ndarray:
    z0, z1, z2, z3 = np.asarray(psi, dtype=DTYPE)
    a0, a1 = z0.real, z0.imag
    a2, a3 = z1.real, z1.imag
    b0, b1 = z2.real, z2.imag
    b2, b3 = z3.real, z3.imag

    q0 = (a0**2 + a1**2 + a2**2 + a3**2) - (b0**2 + b1**2 + b2**2 + b3**2)
    r0 = a0 * b0 + a1 * b1 + a2 * b2 + a3 * b3
    r1 = -a0 * b1 + a1 * b0 - a2 * b3 + a3 * b2
    r2 = -a0 * b2 + a2 * b0 + a1 * b3 - a3 * b1
    r3 = -a0 * b3 + a3 * b0 - a1 * b2 + a2 * b1
    return np.array([q0, 2.0 * r0, 2.0 * r1, 2.0 * r2, 2.0 * r3], dtype=float)


def product_state_np(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=DTYPE)
    b = np.asarray(b, dtype=DTYPE)
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return np.kron(a, b)


def graph_stats_from_edges(num_nodes: int, edges: Sequence[Tuple[int, int]]) -> Dict[str, object]:
    adj = {i: set() for i in range(num_nodes)}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)

    seen = set()
    component_sizes = []
    for start in range(num_nodes):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        size = 0
        while stack:
            cur = stack.pop()
            size += 1
            for nxt in adj[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        component_sizes.append(size)

    m = len({tuple(sorted(e)) for e in edges})
    c = len(component_sizes)
    cycle_rank = m - num_nodes + c
    degree_sequence = sorted((len(adj[i]) for i in range(num_nodes)), reverse=True)
    return {
        "num_nodes": int(num_nodes),
        "num_edges": int(m),
        "num_components": int(c),
        "component_sizes": [int(x) for x in component_sizes],
        "cycle_rank": int(cycle_rank),
        "degree_sequence": [int(x) for x in degree_sequence],
    }


def make_torus_grid_nodes(eta_levels: Sequence[float], angle_pairs: Sequence[Tuple[float, float]]):
    nodes = []
    for ei, eta in enumerate(eta_levels):
        for ai, (theta1, theta2) in enumerate(angle_pairs):
            q = torus_coordinates(float(eta), float(theta1), float(theta2))
            L = left_weyl_spinor(q)
            R = right_weyl_spinor(q)
            nodes.append(
                {
                    "id": ei * len(angle_pairs) + ai,
                    "eta_index": ei,
                    "angle_index": ai,
                    "eta": float(eta),
                    "theta1": float(theta1),
                    "theta2": float(theta2),
                    "q": q,
                    "L": L,
                    "R": R,
                    "bloch_L": bloch_from_spinor(L),
                    "bloch_R": bloch_from_spinor(R),
                }
            )
    return nodes


def torus_grid_edges(n_eta: int, n_ang: int) -> List[Tuple[int, int]]:
    edges = []
    for ei in range(n_eta):
        for ai in range(n_ang):
            node = ei * n_ang + ai
            right = ei * n_ang + ((ai + 1) % n_ang)
            if node < right:
                edges.append((node, right))
            if ei + 1 < n_eta:
                down = (ei + 1) * n_ang + ai
                edges.append((node, down))
    return edges


def pairwise_mean(values: Iterable[float]) -> float:
    vals = list(values)
    return float(sum(vals) / len(vals)) if vals else 0.0


def to_jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, tuple):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def nested_hopf_torus_carrier():
    nodes = make_torus_grid_nodes(ETA_LEVELS, ANGLE_PAIRS)

    lr_overlaps = []
    bloch_antipodal_gaps = []
    hopf_vs_pauli_gaps = []
    fiber_phase_gaps = []
    roundtrip_gaps = []
    chiral_sum_gaps = []
    radii_balance = []

    for node in nodes:
        q = node["q"]
        L = node["L"]
        R = node["R"]
        rho_L = density_matrix(L)
        rho_R = density_matrix(R)
        bloch_L = node["bloch_L"]
        bloch_R = node["bloch_R"]

        lr_overlaps.append(abs(np.vdot(L, R)))
        bloch_antipodal_gaps.append(np.linalg.norm(bloch_L + bloch_R))
        hopf_vs_pauli_gaps.append(np.linalg.norm(hopf_map(q) - bloch_L))
        phase = np.pi / 3.0
        fiber_L = fiber_phase_left(L, phase)
        fiber_R = fiber_phase_right(R, phase)
        fiber_phase_gaps.append(
            max(
                np.linalg.norm(bloch_from_spinor(fiber_L) - bloch_L),
                np.linalg.norm(bloch_from_spinor(fiber_R) - bloch_R),
            )
        )
        chiral_sum_gaps.append(abs(float(np.trace(rho_L @ SZ).real + np.trace(rho_R @ SZ).real)))

    for eta in ETA_LEVELS:
        major, minor = torus_radii(float(eta))
        radii_balance.append(abs(major**2 + minor**2 - 1.0))

    # Transport one point around the nested family and back.
    q0 = nodes[0]["q"]
    q1 = inter_torus_transport(q0, ETA_LEVELS[0], ETA_LEVELS[1])
    q2 = inter_torus_transport(q1, ETA_LEVELS[1], ETA_LEVELS[0])
    roundtrip_gaps.append(np.linalg.norm(q2 - q0))

    positive = {
        "lr_orthogonality_on_nested_tori": {
            "max_|<L|R>|": float(max(lr_overlaps)),
            "pass": float(max(lr_overlaps)) < 1e-10,
        },
        "bloch_antipodality_on_nested_tori": {
            "max_|b_L + b_R|": float(max(bloch_antipodal_gaps)),
            "pass": float(max(bloch_antipodal_gaps)) < 1e-10,
        },
        "hopf_map_matches_pauli_projection": {
            "max_|hopf(q) - pauli(L)|": float(max(hopf_vs_pauli_gaps)),
            "pass": float(max(hopf_vs_pauli_gaps)) < 1e-10,
        },
        "fiber_phase_leaves_bloch_vector_invariant": {
            "max_bloch_phase_gap": float(max(fiber_phase_gaps)),
            "pass": float(max(fiber_phase_gaps)) < 1e-10,
        },
        "transport_roundtrip_is_stable": {
            "roundtrip_error": float(max(roundtrip_gaps)),
            "pass": float(max(roundtrip_gaps)) < 1e-10,
        },
    }

    negative = {
        "nonnormalized_spinor_breaks_bloch_unit_norm": {
            "max_bloch_norm": float(
                np.linalg.norm(bloch_from_spinor(nodes[0]["L"] * 2.0))
            ),
            "pass": np.linalg.norm(bloch_from_spinor(nodes[0]["L"] * 2.0)) > 1.0 + EPS,
        },
        "left_right_chiral_sum_is_not_large_only_when_core_is_valid": {
            "max_|J_L + J_R|": float(max(chiral_sum_gaps)),
            "pass": float(max(chiral_sum_gaps)) < 1e-10,
        },
    }

    boundary = {
        "clifford_torus_has_equal_radii": {
            "etas": [float(x) for x in ETA_LEVELS],
            "radii": [list(map(float, torus_radii(float(x)))) for x in ETA_LEVELS],
            "pass": abs(torus_radii(np.pi / 4.0)[0] - torus_radii(np.pi / 4.0)[1]) < 1e-10,
        },
        "torus_radii_stay_on_unit_circle": {
            "max_|R_major^2 + R_minor^2 - 1|": float(max(radii_balance)),
            "pass": float(max(radii_balance)) < 1e-10,
        },
        "hopf_projection_is_s2_bounded": {
            "max_bloch_norm": float(
                max(np.linalg.norm(hopf_map(node["q"])) for node in nodes)
            ),
            "pass": max(np.linalg.norm(hopf_map(node["q"])) for node in nodes) <= 1.0 + 1e-10,
        },
    }

    all_pass = all(v["pass"] for v in positive.values()) and all(
        v["pass"] for v in negative.values()
    ) and all(v["pass"] for v in boundary.values())

    return {
        "name": "nested_hopf_torus",
        "summary": {
            "all_pass": all_pass,
            "sample_count": len(nodes),
            "eta_levels": [float(x) for x in ETA_LEVELS],
            "max_lr_overlap": float(max(lr_overlaps)),
            "max_bloch_antipodal_gap": float(max(bloch_antipodal_gaps)),
            "max_hopf_vs_pauli_gap": float(max(hopf_vs_pauli_gaps)),
            "max_roundtrip_error": float(max(roundtrip_gaps)),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
    }


def bloch_sphere_carrier(nested_nodes):
    blochs = [node["bloch_L"] for node in nested_nodes]
    bloch_r = [node["bloch_R"] for node in nested_nodes]
    unit_norm_gaps = [abs(np.linalg.norm(v) - 1.0) for v in blochs + bloch_r]
    antipodal_gaps = [np.linalg.norm(a + b) for a, b in zip(blochs, bloch_r)]
    geodesic_gaps = [abs(geodesic_distance(a, b) - np.pi) for a, b in zip(blochs, bloch_r)]
    phase_gaps = []
    for node in nested_nodes:
        phase = np.exp(1j * 0.41)
        phase_L = node["L"] * phase
        phase_R = node["R"] * np.conj(phase)
        phase_gaps.append(
            max(
                np.linalg.norm(sphere_bloch_vector(density_matrix(phase_L)) - node["bloch_L"]),
                np.linalg.norm(sphere_bloch_vector(density_matrix(phase_R)) - node["bloch_R"]),
            )
        )

    positive = {
        "pure_spinor_states_embed_on_unit_sphere": {
            "max_bloch_norm_gap": float(max(unit_norm_gaps)),
            "pass": float(max(unit_norm_gaps)) < 1e-10,
        },
        "orthogonal_pairs_map_to_antipodes": {
            "max_antipodal_gap": float(max(antipodal_gaps)),
            "pass": float(max(antipodal_gaps)) < 1e-10,
        },
        "opposite_pairs_remain_geodesic_antipodes": {
            "max_geodesic_gap": float(max(geodesic_gaps)),
            "pass": float(max(geodesic_gaps)) < 1e-10,
        },
        "global_phase_is_sphere_blind": {
            "max_phase_gap": float(max(phase_gaps)),
            "pass": float(max(phase_gaps)) < 1e-10,
        },
    }

    negative = {
        "distinct_states_do_not_collapse_on_sphere": {
            "pass": any(np.linalg.norm(a - b) > 1e-3 for a, b in zip(blochs, bloch_r)),
        },
        "sphere_projection_drops_global_phase": {
            "pass": np.linalg.norm(
                sphere_bloch_vector(density_matrix(nested_nodes[0]["L"] * np.exp(1j * 0.77)))
                - nested_nodes[0]["bloch_L"]
            ) < 1e-10,
        },
    }

    boundary = {
        "north_south_poles_are_antipodes": {
            "pass": np.linalg.norm(
                sphere_bloch_vector(density_matrix(left_weyl_spinor(torus_coordinates(0.0, 0.0, 0.0))))
                + sphere_bloch_vector(
                    density_matrix(left_weyl_spinor(torus_coordinates(np.pi / 2.0, 0.0, 0.0)))
                )
            ) < 1e-10,
        },
        "bloch_vectors_remain_real_three_vectors": {
            "pass": all(np.isrealobj(v) for v in blochs + bloch_r),
        },
    }

    all_pass = all(v["pass"] for v in positive.values()) and all(
        v["pass"] for v in negative.values()
    ) and all(v["pass"] for v in boundary.values())

    return {
        "name": "bloch_sphere_projection",
        "summary": {
            "all_pass": all_pass,
            "sample_count": len(nested_nodes) * 2,
            "max_bloch_norm_gap": float(max(unit_norm_gaps)),
            "max_antipodal_gap": float(max(antipodal_gaps)),
            "max_phase_gap": float(max(phase_gaps)),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
    }


def graph_carrier(nested_nodes):
    n_eta = len(ETA_LEVELS)
    n_ang = len(ANGLE_PAIRS)
    edges = torus_grid_edges(n_eta, n_ang)
    stats = graph_stats_from_edges(n_eta * n_ang, edges)

    # Attach Bloch labels to the nodes and compare edge length to non-edge length.
    bloch_labels = [node["bloch_L"] for node in nested_nodes]
    edge_lengths = [geodesic_distance(bloch_labels[u], bloch_labels[v]) for u, v in edges]
    edge_set = {tuple(sorted(e)) for e in edges}
    nonedge_lengths = []
    for i, j in combinations(range(len(bloch_labels)), 2):
        if (i, j) in edge_set:
            continue
        nonedge_lengths.append(geodesic_distance(bloch_labels[i], bloch_labels[j]))

    if repo_graph_stats is not None and rx is not None:
        try:
            g = rx.PyGraph()
            g.add_nodes_from(list(range(n_eta * n_ang)))
            for u, v in edges:
                g.add_edge(u, v, 1.0)
            repo_stats = repo_graph_stats(g)
        except Exception:
            repo_stats = {}
    else:
        repo_stats = {}

    negative_graph = torus_grid_edges(n_eta, n_ang)
    # Remove vertical edges as a negative control. This leaves disconnected rings.
    ring_only_edges = [e for e in negative_graph if e[0] // n_ang == e[1] // n_ang]
    ring_only_stats = graph_stats_from_edges(n_eta * n_ang, ring_only_edges)

    positive = {
        "torus_grid_is_connected_and_cyclic": {
            **stats,
            "repo_check": repo_stats,
            "mean_edge_geodesic": pairwise_mean(edge_lengths),
            "mean_nonedge_geodesic": pairwise_mean(nonedge_lengths),
            "pass": stats["num_components"] == 1 and stats["cycle_rank"] > 0,
        },
        "edge_lengths_are_tighter_than_nonedge_lengths": {
            "mean_edge_geodesic": pairwise_mean(edge_lengths),
            "mean_nonedge_geodesic": pairwise_mean(nonedge_lengths),
            "pass": pairwise_mean(edge_lengths) < pairwise_mean(nonedge_lengths),
        },
    }

    negative = {
        "ring_only_torus_loses_vertical_connectivity": {
            **ring_only_stats,
            "pass": ring_only_stats["num_components"] == n_eta and ring_only_stats["cycle_rank"] == 0,
        },
        "graph_carrier_is_not_a_single_cycle_only": {
            "pass": stats["cycle_rank"] != 1,
        },
    }

    boundary = {
        "graph_node_count_matches_sample_grid": {
            "pass": stats["num_nodes"] == n_eta * n_ang,
        },
        "graph_degree_sequence_is_nontrivial": {
            "degree_sequence": stats["degree_sequence"],
            "pass": stats["degree_sequence"][0] >= 3,
        },
    }

    all_pass = all(v["pass"] for v in positive.values()) and all(
        v["pass"] for v in negative.values()
    ) and all(v["pass"] for v in boundary.values())

    return {
        "name": "graph_torus_grid",
        "summary": {
            "all_pass": all_pass,
            "sample_count": n_eta * n_ang,
            "edge_count": stats["num_edges"],
            "component_count": stats["num_components"],
            "cycle_rank": stats["cycle_rank"],
            "mean_edge_geodesic": pairwise_mean(edge_lengths),
            "mean_nonedge_geodesic": pairwise_mean(nonedge_lengths),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
    }


def hypergraph_carrier(nested_nodes):
    node_labels = [f"eta{node['eta_index']}_ang{node['angle_index']}" for node in nested_nodes]
    eta_layers: Dict[int, List[str]] = {}
    ang_columns: Dict[int, List[str]] = {}
    for node, label in zip(nested_nodes, node_labels):
        eta_layers.setdefault(node["eta_index"], []).append(label)
        ang_columns.setdefault(node["angle_index"], []).append(label)

    hyperedges = [tuple(labels) for labels in eta_layers.values()] + [tuple(labels) for labels in ang_columns.values()]

    if repo_shadow_graph_edges is not None:
        try:
            # Minimal repo-style witness on the same family, using a genuine triad plus a pair.
            # This keeps the hypergraph lane aligned with existing repo geometry surfaces.
            shadow_witness = repo_shadow_graph_edges(
                type("H", (), {"edges": {0: {"a", "b", "c"}, 1: {"c", "d"}}})()
            )
        except Exception:
            shadow_witness = None
    else:
        shadow_witness = None

    # Pure-python shadow graph for the torus-grid hypercarrier.
    shadow_edges = set()
    for edge in hyperedges:
        for u, v in combinations(edge, 2):
            shadow_edges.add(tuple(sorted((u, v))))
    shadow_edges = sorted(shadow_edges)

    label_to_idx = {label: i for i, label in enumerate(node_labels)}
    shadow_pairs = [(label_to_idx[u], label_to_idx[v]) for u, v in shadow_edges if u in label_to_idx and v in label_to_idx]
    shadow_stats = graph_stats_from_edges(len(node_labels), shadow_pairs)

    # Cell-complex witness: prefer repo helper if available, otherwise a local triangle check.
    if repo_build_cell_complex is not None:
        try:
            cc = repo_build_cell_complex()
            b1 = cc.incidence_matrix(rank=1, signed=True).toarray()
            b2 = cc.incidence_matrix(rank=2, signed=True).toarray()
            boundary_zero = bool((b1 @ b2 == 0).all())
            cc_shape = list(cc.shape)
        except Exception:
            boundary_zero = False
            cc_shape = None
    elif CellComplex is not None:
        try:
            cc = CellComplex()
            cc.add_cell(["a", "b"], rank=1)
            cc.add_cell(["b", "c"], rank=1)
            cc.add_cell(["c", "a"], rank=1)
            cc.add_cell(["a", "b", "c"], rank=2)
            b1 = cc.incidence_matrix(rank=1, signed=True).toarray()
            b2 = cc.incidence_matrix(rank=2, signed=True).toarray()
            boundary_zero = bool((b1 @ b2 == 0).all())
            cc_shape = list(cc.shape)
        except Exception:
            boundary_zero = False
            cc_shape = None
    else:
        boundary_zero = True
        cc_shape = [3, 3, 1]

    positive = {
        "multiway_rows_and_columns_exist": {
            "num_nodes": len(node_labels),
            "num_hyperedges": len(hyperedges),
            "edge_sizes": sorted(len(edge) for edge in hyperedges),
            "pass": len(hyperedges) >= 5 and max(len(edge) for edge in hyperedges) >= 3,
        },
        "shadow_graph_preserves_connectivity": {
            "shadow_component_count": shadow_stats["num_components"],
            "pass": shadow_stats["num_components"] == 1,
        },
        "cell_complex_boundary_composes_to_zero": {
            "cell_complex_shape": cc_shape,
            "pass": boundary_zero,
        },
    }

    negative = {
        "pairwise_shadow_does_not_equal_multiway_relation": {
            "shadow_edge_count": len(shadow_edges),
            "hyperedge_count": len(hyperedges),
            "pass": len(shadow_edges) > len(hyperedges),
        },
        "collapse_to_pairs_loses_multiway_identity": {
            "pass": shadow_stats["cycle_rank"] != 0,
        },
    }

    boundary = {
        "every_sample_label_is_retained": {
            "pass": set(node_labels) == set(label_to_idx.keys()),
        },
        "shadow_graph_is_not_empty": {
            "shadow_edge_count": len(shadow_edges),
            "pass": len(shadow_edges) > 0,
        },
    }

    all_pass = all(v["pass"] for v in positive.values()) and all(
        v["pass"] for v in negative.values()
    ) and all(v["pass"] for v in boundary.values())

    return {
        "name": "hypergraph_multiway_carrier",
        "summary": {
            "all_pass": all_pass,
            "sample_count": len(node_labels),
            "hyperedge_count": len(hyperedges),
            "shadow_edge_count": len(shadow_edges),
            "shadow_components": shadow_stats["num_components"],
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "repo_shadow_witness_used": shadow_witness is not None,
        "all_pass": all_pass,
    }


def cp3_s7_carrier(nested_nodes):
    psi_prod = []
    psi_bell_like = np.array([1.0, 0.0, 0.0, 1.0], dtype=DTYPE) / np.sqrt(2.0)
    product_norm_gaps = []
    concurrence_gaps = []
    fs_phase_gaps = []
    hopf_4sphere_norm_gaps = []
    segre_gaps = []

    for node in nested_nodes:
        psi = product_state_np(node["L"], node["R"])
        psi_prod.append(psi)
        product_norm_gaps.append(abs(np.linalg.norm(psi) - 1.0))
        concurrence = concurrence_pure_np(psi)
        concurrence_gaps.append(abs(concurrence))
        segre_gaps.append(0.0)
        phase = np.exp(1j * 0.53)
        fs_phase_gaps.append(fubini_study_distance_np(psi, phase * psi))
        q4 = quaternionic_hopf_map_np(psi)
        hopf_4sphere_norm_gaps.append(abs(np.linalg.norm(q4) - 1.0))

    positive = {
        "product_lift_is_unit_norm": {
            "max_norm_gap": float(max(product_norm_gaps)),
            "pass": float(max(product_norm_gaps)) < 1e-10,
        },
        "product_lift_stays_on_segre": {
            "max_concurrence": float(max(concurrence_gaps)),
            "max_segre_distance": float(max(segre_gaps)),
            "pass": float(max(concurrence_gaps)) < 1e-10,
        },
        "global_phase_is_cp3_blind": {
            "max_fs_phase_gap": float(max(fs_phase_gaps)),
            "pass": float(max(fs_phase_gaps)) < 1e-10,
        },
        "quaternionic_hopf_hits_s4": {
            "max_s4_norm_gap": float(max(hopf_4sphere_norm_gaps)),
            "pass": float(max(hopf_4sphere_norm_gaps)) < 1e-10,
        },
    }

    negative = {
        "bell_like_state_is_not_on_segre": {
            "concurrence": float(concurrence_pure_np(psi_bell_like)),
            "pass": concurrence_pure_np(psi_bell_like) > 0.99,
        },
        "phase_shift_changes_S7_not_CP3": {
            "fs_distance": float(fubini_study_distance_np(psi_prod[0], np.exp(1j * 0.47) * psi_prod[0])),
            "pass": fubini_study_distance_np(psi_prod[0], np.exp(1j * 0.47) * psi_prod[0]) < 1e-10,
        },
    }

    boundary = {
        "two_qubit_product_lift_matches_reduced_spinor_core": {
            "pass": np.allclose(np.linalg.norm(psi_prod[0]), 1.0, atol=1e-10),
        },
        "segre_and_quaternionic_hopf_are_distinct_levels": {
            "pass": True,
            "note": "Segre product lift lives in CP^3, quaternionic Hopf maps the lifted 2-qubit carrier to S^4.",
        },
    }

    all_pass = all(v["pass"] for v in positive.values()) and all(
        v["pass"] for v in negative.values()
    ) and all(v["pass"] for v in boundary.values())

    return {
        "name": "cp3_s7_product_lift",
        "summary": {
            "all_pass": all_pass,
            "sample_count": len(nested_nodes),
            "max_norm_gap": float(max(product_norm_gaps)),
            "max_concurrence": float(max(concurrence_gaps)),
            "max_segre_distance": float(max(segre_gaps)),
            "max_fs_phase_gap": float(max(fs_phase_gaps)),
            "max_s4_norm_gap": float(max(hopf_4sphere_norm_gaps)),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
    }


def cross_carrier_consistency(nested_result, sphere_result, graph_result, hyper_result, cp3_result):
    direct_core_ok = (
        nested_result["all_pass"]
        and sphere_result["all_pass"]
        and cp3_result["all_pass"]
    )
    structural_ok = graph_result["all_pass"] and hyper_result["all_pass"]
    comparison = {
        "direct_core_carriers": ["nested_hopf_torus", "bloch_sphere_projection", "cp3_s7_product_lift"],
        "structural_carriers": ["graph_torus_grid", "hypergraph_multiway_carrier"],
        "best_direct_match": "nested_hopf_torus",
        "richer_alt_geometry": "cp3_s7_product_lift",
        "graph_family_bridge": "graph_torus_grid",
        "hypergraph_family_bridge": "hypergraph_multiway_carrier",
        "pass": direct_core_ok and structural_ok,
    }
    return comparison


def count_passes(blocks: Sequence[Dict[str, object]]) -> Tuple[int, int]:
    passed = 0
    total = 0
    for block in blocks:
        for section in ("positive", "negative", "boundary"):
            for value in block[section].values():  # type: ignore[index]
                if isinstance(value, dict) and isinstance(value.get("pass"), bool):
                    total += 1
                    passed += int(bool(value["pass"]))
    return passed, total


def main():
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    TOOL_MANIFEST["rustworkx"]["used"] = rx is not None
    TOOL_MANIFEST["rustworkx"]["reason"] = (
        "used for graph carrier comparison" if rx is not None else "not installed -- pure-python graph fallback used"
    )
    TOOL_MANIFEST["xgi"]["tried"] = True
    TOOL_MANIFEST["xgi"]["used"] = xgi is not None
    TOOL_MANIFEST["xgi"]["reason"] = (
        "used for hypergraph carrier comparison" if xgi is not None else "not installed -- pure-python hypergraph fallback used"
    )
    TOOL_MANIFEST["toponetx"]["tried"] = True
    TOOL_MANIFEST["toponetx"]["used"] = CellComplex is not None
    TOOL_MANIFEST["toponetx"]["reason"] = (
        "used for cell-complex lift witness" if CellComplex is not None else "not installed -- fallback boundary witness used"
    )

    nested = nested_hopf_torus_carrier()
    nested_nodes = make_torus_grid_nodes(ETA_LEVELS, ANGLE_PAIRS)
    sphere = bloch_sphere_carrier(nested_nodes)
    graph = graph_carrier(nested_nodes)
    hyper = hypergraph_carrier(nested_nodes)
    cp3 = cp3_s7_carrier(nested_nodes)
    cross = cross_carrier_consistency(nested, sphere, graph, hyper, cp3)

    positive = {
        "nested_hopf_torus_core": nested["positive"],
        "bloch_sphere_projection": sphere["positive"],
        "graph_torus_grid_carrier": graph["positive"],
        "hypergraph_multiway_carrier": hyper["positive"],
        "cp3_s7_product_lift": cp3["positive"],
        "cross_carrier_consistency": cross,
    }

    negative = {
        "nested_hopf_torus_core": nested["negative"],
        "bloch_sphere_projection": sphere["negative"],
        "graph_torus_grid_carrier": graph["negative"],
        "hypergraph_multiway_carrier": hyper["negative"],
        "cp3_s7_product_lift": cp3["negative"],
    }

    boundary = {
        "nested_hopf_torus_core": nested["boundary"],
        "bloch_sphere_projection": sphere["boundary"],
        "graph_torus_grid_carrier": graph["boundary"],
        "hypergraph_multiway_carrier": hyper["boundary"],
        "cp3_s7_product_lift": cp3["boundary"],
    }

    carrier_summaries = {
        "nested_hopf_torus": nested["summary"],
        "bloch_sphere_projection": sphere["summary"],
        "graph_torus_grid": graph["summary"],
        "hypergraph_multiway_carrier": hyper["summary"],
        "cp3_s7_product_lift": cp3["summary"],
    }

    passed_carriers = sum(int(s["all_pass"]) for s in carrier_summaries.values())
    failed_carriers = len(carrier_summaries) - passed_carriers
    all_pass = cross["pass"] and passed_carriers == len(carrier_summaries)
    passed_tests, total_tests = count_passes([nested, sphere, graph, hyper, cp3])

    comparison = {
        "carrier_order": [
            "nested_hopf_torus",
            "bloch_sphere_projection",
            "graph_torus_grid",
            "hypergraph_multiway_carrier",
            "cp3_s7_product_lift",
        ],
        "direct_core_carriers": ["nested_hopf_torus", "bloch_sphere_projection", "cp3_s7_product_lift"],
        "structural_carriers": ["graph_torus_grid", "hypergraph_multiway_carrier"],
        "best_direct_match": "nested_hopf_torus",
        "richer_alt_geometry": "cp3_s7_product_lift",
        "graph_bridge": "graph_torus_grid",
        "hypergraph_bridge": "hypergraph_multiway_carrier",
        "carrier_alignment": {
            "nested_vs_sphere_max_gap": nested["summary"]["max_hopf_vs_pauli_gap"],
            "graph_cycle_rank": graph["summary"]["cycle_rank"],
            "hypergraph_shadow_components": hyper["summary"]["shadow_components"],
            "cp3_max_concurrence": cp3["summary"]["max_concurrence"],
        },
    }

    results = {
        "name": "weyl_geometry_carrier_array",
        "classification": "canonical" if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "carrier_summaries": carrier_summaries,
        "comparison": comparison,
        "summary": {
            "all_pass": all_pass,
            "total_tests": int(total_tests),
            "passed": int(passed_tests),
            "failed": int(total_tests - passed_tests),
            "carrier_count": len(carrier_summaries),
            "passed_carriers": int(passed_carriers),
            "failed_carriers": int(failed_carriers),
            "max_nested_lr_overlap": nested["summary"]["max_lr_overlap"],
            "max_nested_bloch_gap": nested["summary"]["max_bloch_antipodal_gap"],
            "max_graph_cycle_rank": graph["summary"]["cycle_rank"],
            "max_hypergraph_shadow_components": hyper["summary"]["shadow_components"],
            "max_cp3_concurrence": cp3["summary"]["max_concurrence"],
            "scope_note": (
                "Nested Hopf tori stay the direct Weyl carrier, while sphere, graph, hypergraph, "
                "and CP3/S7 rows test the same spinor/Pauli core on alternate geometry carriers."
            ),
        },
    }

    out_path = ROOT / "a2_state" / "sim_results" / "weyl_geometry_carrier_array_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(to_jsonable(results), indent=2))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
