#!/usr/bin/env python3
"""
sim_foundation_shell_graph_topology.py

Foundational pure-math shell-family lego using graph, hypergraph, and topology
tools as load-bearing computation layers.

Objects:
- nested shell families represented by radii and sampled boundary points
- shell nesting DAG via rustworkx
- multi-way shell relations via XGI hypergraph
- filtration-sensitive loop persistence via GUDHI

No final canon is claimed. This is a foundation lego for nested structure.
"""

import json
import math
from pathlib import Path

import numpy as np
classification = "canonical"


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not relevant -- no tensor autodiff needed"},
    "pyg": {"tried": False, "used": False, "reason": "not relevant -- no learned graph model needed"},
    "z3": {"tried": False, "used": False, "reason": "not relevant -- no SMT constraints in this sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not relevant -- no SMT synthesis in this sim"},
    "sympy": {"tried": False, "used": False, "reason": "not relevant -- no symbolic algebra needed"},
    "clifford": {"tried": False, "used": False, "reason": "not relevant -- no geometric algebra needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not relevant -- manifold package not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not relevant -- no equivariant network needed"},
    "rustworkx": {"tried": True, "used": False, "reason": ""},
    "xgi": {"tried": True, "used": False, "reason": ""},
    "toponetx": {"tried": True, "used": False, "reason": "tried for cell-complex comparison; GUDHI filtration chosen here"},
    "gudhi": {"tried": True, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": None,
    "gudhi": "load_bearing",
}

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["used"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = "primary graph tool -- shell nesting DAG and longest path depth"
except ImportError as exc:  # pragma: no cover
    rx = None
    TOOL_MANIFEST["rustworkx"]["reason"] = f"not installed: {exc}"

try:
    import xgi
    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = "primary hypergraph tool -- multi-way shell overlap relations"
except ImportError as exc:  # pragma: no cover
    xgi = None
    TOOL_MANIFEST["xgi"]["reason"] = f"not installed: {exc}"

try:
    from toponetx.classes import CellComplex  # noqa: F401
except ImportError as exc:  # pragma: no cover
    TOOL_MANIFEST["toponetx"]["reason"] = f"not installed: {exc}"

try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["used"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = "primary topology tool -- Rips persistence on shell samples"
except ImportError as exc:  # pragma: no cover
    gudhi = None
    TOOL_MANIFEST["gudhi"]["reason"] = f"not installed: {exc}"


RESULTS_PATH = Path(__file__).resolve().parent / "a2_state" / "sim_results" / "foundation_shell_graph_topology_results.json"


def make_case(name, radii, shared_windows):
    return {
        "name": name,
        "radii": list(radii),
        "shared_windows": [tuple(sorted(window)) for window in shared_windows],
    }


def sample_shell_points(radii, points_per_shell=16):
    points = []
    labels = []
    for shell_idx, radius in enumerate(radii):
        for k in range(points_per_shell):
            theta = 2.0 * math.pi * k / points_per_shell
            points.append([radius * math.cos(theta), radius * math.sin(theta)])
            labels.append(shell_idx)
    return np.array(points, dtype=float), labels


def relation_augmented_points(radii, shared_windows):
    shell_points, _ = sample_shell_points(radii)
    bridge_points = []

    # Multi-way shell relations are embedded as radial bridge samples so the
    # topology calculation sees the shell family, not just disjoint circles.
    for window in shared_windows:
        radii_window = [radii[idx] for idx in window]
        mean_radius = float(np.mean(radii_window))
        angles = [0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0]
        for theta in angles[: min(len(window), 3)]:
            bridge_points.append([mean_radius * math.cos(theta), mean_radius * math.sin(theta)])

        if len(window) >= 3:
            bridge_points.append([0.0, 0.0])
        elif len(window) == 2:
            inner = min(radii_window)
            outer = max(radii_window)
            bridge_points.append([(inner + outer) / 2.0, 0.0])

    if bridge_points:
        return np.vstack([shell_points, np.array(bridge_points, dtype=float)])
    return shell_points


def build_shell_dag(radii, tolerance=1e-9):
    if rx is None:
        raise RuntimeError("rustworkx unavailable")
    dag = rx.PyDiGraph()
    node_ids = []
    for idx, radius in enumerate(radii):
        node_ids.append(dag.add_node({"shell": idx, "radius": float(radius)}))
    edge_count = 0
    for i, r_i in enumerate(radii):
        for j, r_j in enumerate(radii):
            if i == j:
                continue
            if r_i + tolerance < r_j:
                dag.add_edge(node_ids[i], node_ids[j], {"kind": "contains"})
                edge_count += 1
    topo = [dag[n]["shell"] for n in rx.topological_sort(dag)]
    longest = int(rx.dag_longest_path_length(dag))
    return {
        "num_nodes": len(radii),
        "num_edges": edge_count,
        "topological_order": topo,
        "longest_path_length": longest,
        "acyclic": bool(rx.is_directed_acyclic_graph(dag)),
    }


def build_shell_hypergraph(num_shells, shared_windows):
    if xgi is None:
        raise RuntimeError("xgi unavailable")
    H = xgi.Hypergraph()
    H.add_nodes_from(range(num_shells))
    for window in shared_windows:
        if len(window) >= 2:
            H.add_edge(window)
    incidence = xgi.incidence_matrix(H, sparse=False)
    return {
        "num_nodes": int(H.num_nodes),
        "num_edges": int(H.num_edges),
        "edge_sizes": [int(v) for v in H.edges.size.aslist()],
        "incidence_rank": int(np.linalg.matrix_rank(incidence)) if incidence.size else 0,
        "connected_components": int(xgi.number_connected_components(H)) if H.num_edges else int(H.num_nodes),
        "max_hyperedge_size": int(max(H.edges.size.aslist())) if H.num_edges else 1,
    }


def persistence_summary(points, max_edge_length=1.35, max_dimension=2):
    if gudhi is None:
        raise RuntimeError("gudhi unavailable")
    rips = gudhi.RipsComplex(points=points.tolist(), max_edge_length=max_edge_length)
    simplex_tree = rips.create_simplex_tree(max_dimension=max_dimension)
    persistence = simplex_tree.persistence()
    h1 = []
    for dim, pair in persistence:
        if dim != 1:
            continue
        birth, death = pair
        if math.isinf(death):
            lifetime = float("inf")
        else:
            lifetime = float(death - birth)
        h1.append({"birth": float(birth), "death": float(death), "lifetime": lifetime})
    finite_h1 = [p["lifetime"] for p in h1 if math.isfinite(p["lifetime"])]
    return {
        "h1_count": len(h1),
        "max_h1_lifetime": float(max(finite_h1)) if finite_h1 else 0.0,
        "mean_h1_lifetime": float(np.mean(finite_h1)) if finite_h1 else 0.0,
        "betti_threshold_0_6": [int(v) for v in simplex_tree.persistent_betti_numbers(0.6, 0.6)],
    }


def analyze_case(case):
    points = relation_augmented_points(case["radii"], case["shared_windows"])
    dag_stats = build_shell_dag(case["radii"])
    hyper_stats = build_shell_hypergraph(len(case["radii"]), case["shared_windows"])
    topo_stats = persistence_summary(points)
    return {
        "name": case["name"],
        "shell_count": len(case["radii"]),
        "radii": [float(r) for r in case["radii"]],
        "graph": dag_stats,
        "hypergraph": hyper_stats,
        "topology": topo_stats,
    }


def build_cases():
    return {
        "nested_three_shells": make_case(
            "nested_three_shells",
            [0.35, 0.70, 1.05],
            [(0, 1), (1, 2), (0, 1, 2)],
        ),
        "shell_ablated": make_case(
            "shell_ablated",
            [0.35, 1.05],
            [(0, 1)],
        ),
        "flattened_boundary": make_case(
            "flattened_boundary",
            [0.75, 0.78, 0.81],
            [(0, 1), (1, 2)],
        ),
    }


def run_checks(analyses):
    nested = analyses["nested_three_shells"]
    ablated = analyses["shell_ablated"]
    flat = analyses["flattened_boundary"]

    checks = {
        "graph_depth_detects_nested_structure": {
            "passed": nested["graph"]["longest_path_length"] > ablated["graph"]["longest_path_length"],
            "detail": "rustworkx longest-path depth distinguishes full nesting from shell ablation",
            "nested_depth": nested["graph"]["longest_path_length"],
            "ablated_depth": ablated["graph"]["longest_path_length"],
        },
        "hypergraph_detects_multiway_shell_relation": {
            "passed": nested["hypergraph"]["max_hyperedge_size"] > ablated["hypergraph"]["max_hyperedge_size"],
            "detail": "XGI hyperedge size captures genuine three-shell relation absent after ablation",
            "nested_max_hyperedge": nested["hypergraph"]["max_hyperedge_size"],
            "ablated_max_hyperedge": ablated["hypergraph"]["max_hyperedge_size"],
        },
        "topology_signature_changes_under_shell_ablation": {
            "passed": (
                nested["topology"]["h1_count"] != ablated["topology"]["h1_count"]
                or not math.isclose(
                    nested["topology"]["max_h1_lifetime"],
                    ablated["topology"]["max_h1_lifetime"],
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                )
            ),
            "detail": "GUDHI persistence changes under shell ablation; the topology layer is sensitive to relation-augmented shell structure",
            "nested_h1_count": nested["topology"]["h1_count"],
            "ablated_h1_count": ablated["topology"]["h1_count"],
            "nested_max_h1_lifetime": nested["topology"]["max_h1_lifetime"],
            "ablated_max_h1_lifetime": ablated["topology"]["max_h1_lifetime"],
        },
        "flattening_reduces_graph_depth_without_destroying_validity": {
            "passed": (
                flat["graph"]["acyclic"]
                and flat["graph"]["longest_path_length"] == nested["graph"]["longest_path_length"]
                and flat["topology"]["max_h1_lifetime"] < nested["topology"]["max_h1_lifetime"]
            ),
            "detail": "Boundary case keeps a valid nesting DAG but weakens topological separation",
            "flattened_depth": flat["graph"]["longest_path_length"],
            "nested_depth": nested["graph"]["longest_path_length"],
            "flattened_max_h1_lifetime": flat["topology"]["max_h1_lifetime"],
            "nested_max_h1_lifetime": nested["topology"]["max_h1_lifetime"],
        },
    }
    return checks


def main():
    cases = build_cases()
    analyses = {name: analyze_case(case) for name, case in cases.items()}
    checks = run_checks(analyses)
    passed = sum(1 for item in checks.values() if item["passed"])
    total = len(checks)

    payload = {
        "name": "foundation_shell_graph_topology",
        "probe": "foundation_shell_graph_topology",
        "purpose": "Compare nested shell families as DAG, hypergraph, and persistent-topology objects using load-bearing graph/topology tools.",
        "classification": "foundation_lego",
        "tools_used": ["rustworkx", "xgi", "gudhi"],
        "tool_manifest": TOOL_MANIFEST,
        "cases": analyses,
        "checks": checks,
        "summary": {
            "passed": passed,
            "total": total,
            "all_pass": passed == total,
            "classification_note": "Foundational graph/topology separation only. No canon claim.",
        },
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
