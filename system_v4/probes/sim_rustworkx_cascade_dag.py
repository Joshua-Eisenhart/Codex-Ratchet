#!/usr/bin/env python3
"""
SIM: rustworkx_cascade_dag
Builds the L0-L7 constraint cascade kill ordering as a rustworkx DAG.
Verifies structural properties: acyclicity, topological sort, critical path,
diamond dependency, parallel paths, and kill-set disjointness (via z3).
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": False, "used": False, "reason": "not relevant to DAG analysis"},
    "pyg": {"tried": False, "used": False, "reason": "not relevant to DAG analysis"},
    # --- Proof layer ---
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": "not relevant to this sim"},
    # --- Symbolic layer ---
    "sympy": {"tried": False, "used": False, "reason": "not relevant to DAG analysis"},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": False, "reason": "not relevant to DAG analysis"},
    "geomstats": {"tried": False, "used": False, "reason": "not relevant to DAG analysis"},
    "e3nn": {"tried": False, "used": False, "reason": "not relevant to DAG analysis"},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": "not relevant to DAG analysis"},
    # --- Topology layer ---
    "toponetx": {"tried": False, "used": False, "reason": "not relevant to DAG analysis"},
    "gudhi": {"tried": False, "used": False, "reason": "not relevant to DAG analysis"},
}

# Try importing each tool
try:
    import torch  # noqa: F401
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Solver, Bool, And, Not, sat, unsat  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except Exception as exc:
    TOOL_MANIFEST["clifford"]["reason"] = f"unavailable ({exc.__class__.__name__}: {exc})"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# CASCADE DATA
# =====================================================================

LAYERS = {
    "L0": {
        "name": "N01 (noncommutation + finitude)",
        "role": "root constraint",
        "kills": [],
    },
    "L1": {
        "name": "CPTP",
        "role": "completely positive trace preserving",
        "kills": [],
    },
    "L2": {
        "name": "d=2+Hopf",
        "role": "dimension lock + Hopf fiber topology",
        "kills": [],
    },
    "L3": {
        "name": "Chirality",
        "role": "left/right sector structure",
        "kills": [],
    },
    "L4": {
        "name": "Composition",
        "role": "cyclic dynamics, KILLS 18 families",
        "kills": [
            "von_neumann", "renyi", "tsallis", "min_entropy", "max_entropy",
            "linear_entropy", "participation_ratio", "conditional_entropy",
            "coherent_information", "entanglement_entropy", "berry_phase",
            "qgt_curvature", "concurrence", "negativity",
            "entanglement_of_formation", "hopf_fiber_coordinate",
            "monopole_curvature", "geometric_phase_quantization",
        ],
    },
    "L5": {
        "name": "su(2)",
        "role": "algebra closure",
        "kills": [],
    },
    "L6": {
        "name": "Irreversibility",
        "role": "CPTP contraction, KILLS 5 families",
        "kills": [
            "schmidt", "hopf_invariant", "chirality_operator_C",
            "berry_holonomy_operator", "chirality_bipartition_marker",
        ],
    },
    "L7": {
        "name": "Dual-Type",
        "role": "type1/type2 distinction",
        "kills": [],
    },
}

DEPENDENCY_EDGES = [
    ("L0", "L1"),  # CPTP requires finitude
    ("L1", "L2"),  # Hopf requires CPTP structure
    ("L2", "L3"),  # chirality requires Hopf
    ("L0", "L4"),  # composition requires noncommutation directly
    ("L3", "L4"),  # composition requires chirality structure
    ("L4", "L5"),  # su(2) requires composition
    ("L4", "L6"),  # irreversibility requires composition
    ("L6", "L7"),  # dual-type requires irreversibility
]


# =====================================================================
# DAG BUILDER HELPERS
# =====================================================================

def build_cascade_dag():
    """Build the full L0-L7 cascade DAG and return (dag, layer_indices)."""
    dag = rx.PyDiGraph()
    layer_indices = {}
    for layer_id, data in LAYERS.items():
        idx = dag.add_node({
            "id": layer_id,
            "name": data["name"],
            "role": data["role"],
            "kill_count": len(data["kills"]),
        })
        layer_indices[layer_id] = idx
    for src, dst in DEPENDENCY_EDGES:
        dag.add_edge(
            layer_indices[src],
            layer_indices[dst],
            {"type": "dependency", "from": src, "to": dst},
        )
    return dag, layer_indices


def get_ancestors(dag, node_idx):
    """Return set of ancestor node indices for a given node."""
    return rx.ancestors(dag, node_idx)


def get_descendants(dag, node_idx):
    """Return set of descendant node indices for a given node."""
    return rx.descendants(dag, node_idx)


def longest_path_length(dag):
    """Compute the longest path in the DAG (number of edges)."""
    return rx.dag_longest_path_length(dag)


def longest_path(dag):
    """Return the longest path as a list of node indices."""
    return rx.dag_longest_path(dag)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    dag, idx = build_cascade_dag()

    # -- 1. DAG is acyclic --
    is_acyclic = rx.is_directed_acyclic_graph(dag)
    results["acyclic"] = {
        "passed": is_acyclic,
        "detail": "DAG has no cycles",
    }

    # -- 2. Topological sort respects all dependency edges --
    topo = rx.topological_sort(dag)
    topo_pos = {node: i for i, node in enumerate(topo)}
    all_edges_respected = True
    edge_checks = []
    for src, dst in DEPENDENCY_EDGES:
        src_pos = topo_pos[idx[src]]
        dst_pos = topo_pos[idx[dst]]
        ok = src_pos < dst_pos
        edge_checks.append({"edge": f"{src}->{dst}", "ok": ok})
        if not ok:
            all_edges_respected = False
    topo_layer_order = [dag[n]["id"] for n in topo]
    results["topological_sort"] = {
        "passed": all_edges_respected,
        "order": topo_layer_order,
        "edge_checks": edge_checks,
    }

    # -- 3. L4 ancestors include {L0, L1, L2, L3} --
    l4_ancestors = get_ancestors(dag, idx["L4"])
    l4_ancestor_ids = {dag[a]["id"] for a in l4_ancestors}
    expected_l4 = {"L0", "L1", "L2", "L3"}
    results["l4_ancestors"] = {
        "passed": expected_l4.issubset(l4_ancestor_ids),
        "ancestors": sorted(l4_ancestor_ids),
        "expected": sorted(expected_l4),
    }

    # -- 4. L6 ancestors include {L0, L1, L2, L3, L4} --
    l6_ancestors = get_ancestors(dag, idx["L6"])
    l6_ancestor_ids = {dag[a]["id"] for a in l6_ancestors}
    expected_l6 = {"L0", "L1", "L2", "L3", "L4"}
    results["l6_ancestors"] = {
        "passed": expected_l6.issubset(l6_ancestor_ids),
        "ancestors": sorted(l6_ancestor_ids),
        "expected": sorted(expected_l6),
    }

    # -- 5. Critical path length is 6 edges (L0->L1->L2->L3->L4->L6->L7) --
    crit_len = longest_path_length(dag)
    crit_path_indices = longest_path(dag)
    crit_path_ids = [dag[n]["id"] for n in crit_path_indices]
    results["critical_path"] = {
        "passed": crit_len == 6,
        "length_edges": crit_len,
        "path": crit_path_ids,
        "expected_path": ["L0", "L1", "L2", "L3", "L4", "L6", "L7"],
    }

    # -- 6. L4 has in-degree 2 (diamond dependency from L0 and L3) --
    l4_in_degree = dag.in_degree(idx["L4"])
    results["l4_diamond_dependency"] = {
        "passed": l4_in_degree == 2,
        "in_degree": l4_in_degree,
        "detail": "L4 receives edges from both L0 (direct) and L3 (via chain)",
    }

    # -- 7. L5 and L6 are parallel (not ordered relative to each other) --
    l5_ancestors = get_ancestors(dag, idx["L5"])
    l6_ancestors_set = get_ancestors(dag, idx["L6"])
    l5_descendants = get_descendants(dag, idx["L5"])
    l6_descendants = get_descendants(dag, idx["L6"])
    l5_not_ancestor_of_l6 = idx["L5"] not in l6_ancestors_set
    l6_not_ancestor_of_l5 = idx["L6"] not in l5_ancestors
    l5_not_descendant_of_l6 = idx["L5"] not in l6_descendants
    l6_not_descendant_of_l5 = idx["L6"] not in l5_descendants
    are_parallel = (
        l5_not_ancestor_of_l6 and l6_not_ancestor_of_l5
        and l5_not_descendant_of_l6 and l6_not_descendant_of_l5
    )
    results["l5_l6_parallel"] = {
        "passed": are_parallel,
        "detail": "L5 and L6 share no ancestor/descendant relation",
    }

    # -- 8. Total kill count --
    total_kills = sum(len(LAYERS[l]["kills"]) for l in LAYERS)
    results["total_kill_count"] = {
        "passed": total_kills == 23,
        "l4_kills": len(LAYERS["L4"]["kills"]),
        "l6_kills": len(LAYERS["L6"]["kills"]),
        "total": total_kills,
    }

    # -- 9. z3: kill sets are disjoint --
    results["z3_kill_disjointness"] = _z3_kill_disjointness()

    return results


def _z3_kill_disjointness():
    """Use z3 to prove L4 and L6 kill sets share no element."""
    try:
        from z3 import Solver, Bool, And, Not, sat  # noqa: F811
    except ImportError:
        return {"passed": False, "detail": "z3 not available"}

    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "prove kill-set disjointness between L4 and L6"

    l4_kills = set(LAYERS["L4"]["kills"])
    l6_kills = set(LAYERS["L6"]["kills"])
    all_families = sorted(l4_kills | l6_kills)

    solver = Solver()
    # For each family, create two booleans: in_l4 and in_l6
    in_l4 = {f: Bool(f"in_l4_{f}") for f in all_families}
    in_l6 = {f: Bool(f"in_l6_{f}") for f in all_families}

    # Assert ground truth membership
    for f in all_families:
        if f in l4_kills:
            solver.add(in_l4[f])
        else:
            solver.add(Not(in_l4[f]))
        if f in l6_kills:
            solver.add(in_l6[f])
        else:
            solver.add(Not(in_l6[f]))

    # Assert there EXISTS a family in BOTH sets (we want this UNSAT)
    overlap_vars = [And(in_l4[f], in_l6[f]) for f in all_families]
    from z3 import Or  # noqa: F811
    solver.push()
    solver.add(Or(*overlap_vars))
    check = solver.check()
    solver.pop()

    is_disjoint = (check == unsat)
    python_disjoint = len(l4_kills & l6_kills) == 0

    return {
        "passed": is_disjoint and python_disjoint,
        "z3_result": str(check),
        "python_intersection": sorted(l4_kills & l6_kills),
        "detail": "z3 confirms no family is killed by both L4 and L6",
    }


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    results = {}

    # -- 1. Adding back-edge L7->L0 breaks acyclicity --
    dag, idx = build_cascade_dag()
    dag.add_edge(idx["L7"], idx["L0"], {"type": "back-edge", "from": "L7", "to": "L0"})
    has_cycle = not rx.is_directed_acyclic_graph(dag)
    results["back_edge_breaks_acyclicity"] = {
        "passed": has_cycle,
        "detail": "Adding L7->L0 correctly creates a cycle",
    }

    # -- 2. Removing L0->L4 disconnects the diamond --
    dag2, idx2 = build_cascade_dag()
    # Find the edge index for L0->L4
    edges_from_l0 = dag2.out_edges(idx2["L0"])
    removed = False
    for src, dst, data in edges_from_l0:
        if dst == idx2["L4"]:
            dag2.remove_edge(src, dst)
            removed = True
            break
    l4_in_degree_after = dag2.in_degree(idx2["L4"])
    results["remove_l0_l4_breaks_diamond"] = {
        "passed": removed and l4_in_degree_after == 1,
        "in_degree_after": l4_in_degree_after,
        "detail": "Removing L0->L4 reduces L4 in-degree from 2 to 1",
    }

    # -- 3. Reversed kill order produces different topological sort --
    dag3 = rx.PyDiGraph()
    # Build a DAG where L6 kills happen before L4
    reversed_edges = [
        ("L0", "L1"), ("L1", "L2"), ("L2", "L3"),
        ("L0", "L6"),  # L6 now directly from root
        ("L3", "L6"),  # L6 gets chirality
        ("L6", "L4"),  # L4 now AFTER L6
        ("L4", "L5"),
        ("L4", "L7"),  # L7 after L4 instead of L6
    ]
    rev_idx = {}
    for lid in LAYERS:
        i = dag3.add_node({"id": lid})
        rev_idx[lid] = i
    for s, d in reversed_edges:
        dag3.add_edge(rev_idx[s], rev_idx[d], {})
    rev_topo = rx.topological_sort(dag3)
    rev_topo_ids = [dag3[n]["id"] for n in rev_topo]

    # In the reversed version, L6 must appear before L4
    l6_before_l4 = rev_topo_ids.index("L6") < rev_topo_ids.index("L4")
    results["reversed_kill_order_different_topo"] = {
        "passed": l6_before_l4,
        "reversed_order": rev_topo_ids,
        "detail": "With reversed kill dependencies, L6 precedes L4 in topo sort",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # -- 1. Single-node DAG (only L0) is trivially acyclic --
    dag1 = rx.PyDiGraph()
    dag1.add_node({"id": "L0", "name": "root"})
    results["single_node_acyclic"] = {
        "passed": rx.is_directed_acyclic_graph(dag1),
        "node_count": len(dag1),
        "edge_count": dag1.num_edges(),
    }

    # -- 2. Linear chain (no diamond) is structurally different --
    dag_linear = rx.PyDiGraph()
    lin_idx = {}
    for lid in ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"]:
        lin_idx[lid] = dag_linear.add_node({"id": lid})
    linear_edges = [
        ("L0", "L1"), ("L1", "L2"), ("L2", "L3"),
        ("L3", "L4"), ("L4", "L5"), ("L5", "L6"), ("L6", "L7"),
    ]
    for s, d in linear_edges:
        dag_linear.add_edge(lin_idx[s], lin_idx[d], {})

    # Linear chain has no diamond: L4 in-degree should be 1
    l4_in_linear = dag_linear.in_degree(lin_idx["L4"])
    # And full cascade has L4 in-degree 2
    dag_full, idx_full = build_cascade_dag()
    l4_in_full = dag_full.in_degree(idx_full["L4"])
    # Also the linear chain has only 7 edges vs 8 in cascade
    results["linear_vs_cascade"] = {
        "passed": (l4_in_linear == 1 and l4_in_full == 2
                   and dag_linear.num_edges() != dag_full.num_edges()),
        "linear_edges": dag_linear.num_edges(),
        "cascade_edges": dag_full.num_edges(),
        "linear_l4_in_degree": l4_in_linear,
        "cascade_l4_in_degree": l4_in_full,
    }

    # -- 3. Merged L4+L6 into single node changes DAG structure --
    dag_merged = rx.PyDiGraph()
    mg_idx = {}
    merged_layers = ["L0", "L1", "L2", "L3", "L4_L6", "L5", "L7"]
    for lid in merged_layers:
        mg_idx[lid] = dag_merged.add_node({"id": lid})
    merged_edges = [
        ("L0", "L1"), ("L1", "L2"), ("L2", "L3"),
        ("L0", "L4_L6"), ("L3", "L4_L6"),
        ("L4_L6", "L5"), ("L4_L6", "L7"),
    ]
    for s, d in merged_edges:
        dag_merged.add_edge(mg_idx[s], mg_idx[d], {})
    merged_is_acyclic = rx.is_directed_acyclic_graph(dag_merged)
    merged_node_count = len(dag_merged)
    merged_longest = rx.dag_longest_path_length(dag_merged)
    results["merged_l4_l6"] = {
        "passed": (merged_is_acyclic
                   and merged_node_count == 7
                   and merged_longest < longest_path_length(dag_full)),
        "node_count": merged_node_count,
        "longest_path_edges": merged_longest,
        "original_longest": longest_path_length(dag_full),
        "detail": "Merging L4+L6 reduces nodes by 1 and shortens critical path",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    # Mark tools used
    TOOL_MANIFEST["rustworkx"]["used"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = "DAG construction, acyclicity, topo sort, critical path, ancestors"

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_passed = (
        all(t.get("passed", False) for t in positive.values())
        and all(t.get("passed", False) for t in negative.values())
        and all(t.get("passed", False) for t in boundary.values())
    )

    results = {
        "name": "rustworkx_cascade_dag",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_passed": all_passed,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "rustworkx_cascade_dag_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"ALL PASSED: {all_passed}")
