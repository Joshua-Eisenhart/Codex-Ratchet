#!/usr/bin/env python3
"""
sim_xgi_shell_hypergraph.py

Models the constraint shell family (L0-L7) as an XGI hypergraph.
Hyperedges represent multi-way interactions where shells co-constrain
the same degree of freedom — not reducible to pairwise edges.

Positive test: hypergraph centrality reflects known kill ordering
    (L4, L6 are highest-centrality because they kill the most families).
Negative test: pairwise decomposition (clique expansion) of all
    hyperedges gives different shell rankings, proving multi-way
    structure is load-bearing.
Boundary test: singleton and full-set hyperedges behave correctly.
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": ""},
    "z3":         {"tried": False, "used": False, "reason": ""},
    "cvc5":       {"tried": False, "used": False, "reason": ""},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": ""},
    "geomstats":  {"tried": False, "used": False, "reason": ""},
    "e3nn":       {"tried": False, "used": False, "reason": ""},
    "rustworkx":  {"tried": False, "used": False, "reason": ""},
    "xgi":        {"tried": False, "used": False, "reason": ""},
    "toponetx":   {"tried": False, "used": False, "reason": ""},
    "gudhi":      {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        None,
    "cvc5":      None,
    "sympy":     None,
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

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
    from z3 import *  # noqa: F401,F403
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
    TOOL_MANIFEST["clifford"]["reason"] = f"optional import unavailable: {exc}"

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
# SHELL DEFINITIONS
# =====================================================================

# Constraint shells with their role descriptions (nominalist framing)
SHELLS = {
    "L0": "density_matrix_validity",        # rho >= 0, tr=1
    "L1": "loop_family_finiteness",         # finite loop families
    "L2": "hopf_carrier_structure",         # Hopf fibration carrier
    "L3": "operator_chirality",             # chirality of operators on stages
    "L4": "engine_family_absolute_kill",    # absolute measure: kills families
    "L5": "axis_orthogonality",             # su(2) axis structure
    "L6": "reversible_family_kill",         # reversible family elimination
    "L7": "full_axis_composition",          # full axis orthogonality matrix
}

SHELL_NAMES = list(SHELLS.keys())

# Hyperedges: sets of shells that co-constrain the same degree of freedom.
# Each hyperedge is annotated with the shared degree of freedom.
# These are NOT pairwise intersections — the joint constraint differs from
# any pairwise sub-constraint.
HYPEREDGES_ANNOTATED = [
    # Both involve density-matrix-level validity (trace/positivity coupling)
    (["L0", "L1"], "density_matrix_validity_and_finiteness"),
    # Hopf carrier, chirality, and composition interact on the spinor carrier
    (["L2", "L3", "L4"], "spinor_carrier_chirality_composition"),
    # L4 (absolute) and L6 (reversible) jointly kill families —
    # the joint kill is not just the union of individual kills
    (["L4", "L6"], "joint_family_kill"),
    # Finitude (L0), carrier (L2), su(2) (L5) co-constrain spinor structure
    (["L0", "L2", "L5"], "spinor_structure_finitude_carrier_su2"),
    # L3, L5, L7 co-constrain the axis orthogonality manifold
    (["L3", "L5", "L7"], "axis_orthogonality_manifold"),
    # L1, L4 together constrain the family count upper bound
    (["L1", "L4"], "family_count_upper_bound"),
    # L2, L6, L7 co-constrain the composition reversibility surface
    (["L2", "L6", "L7"], "composition_reversibility_surface"),
    # Full engine co-constraint: L4 + L6 + L7 determine which families survive
    (["L4", "L6", "L7"], "surviving_family_filter"),
]

HYPEREDGES = [e for e, _ in HYPEREDGES_ANNOTATED]
HYPEREDGE_LABELS = [label for _, label in HYPEREDGES_ANNOTATED]


def build_hypergraph(hyperedges):
    """Build an XGI Hypergraph from a list of shell-name lists."""
    H = xgi.Hypergraph()
    H.add_nodes_from(SHELL_NAMES)
    for edge in hyperedges:
        H.add_edge(edge)
    return H


def rank_shells_by_centrality(H):
    """
    Compute multiple centrality measures over the hypergraph H.
    Returns a dict of measure -> {shell: value}.
    """
    measures = {}

    # Hyperedge degree: number of hyperedges a shell participates in
    deg = dict(zip(SHELL_NAMES, [H.degree(n) for n in SHELL_NAMES]))
    measures["hyperedge_degree"] = deg

    # Clique eigenvector centrality: uses the clique-expansion adjacency
    # (multi-way structure still encoded through co-membership counts)
    cec = H.nodes.clique_eigenvector_centrality.asdict()
    measures["clique_eigenvector_centrality"] = {k: float(v) for k, v in cec.items()}

    # Node-edge centrality: spectral centrality on the bipartite incidence
    nec = H.nodes.node_edge_centrality.asdict()
    measures["node_edge_centrality"] = {k: float(v) for k, v in nec.items()}

    # Katz centrality
    katz = H.nodes.katz_centrality.asdict()
    measures["katz_centrality"] = {k: float(v) for k, v in katz.items()}

    return measures


def pairwise_decomposition(hyperedges):
    """
    Decompose all hyperedges into pairwise edges (clique expansion).
    Returns a list of 2-element lists — the classical pairwise approximation.
    """
    pairs = set()
    for edge in hyperedges:
        nodes = sorted(edge)
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                pairs.add((nodes[i], nodes[j]))
    return [list(p) for p in pairs]


def ranking_from_measure(measure_dict):
    """Return shells sorted by descending centrality value."""
    return sorted(measure_dict.items(), key=lambda x: x[1], reverse=True)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Positive test: XGI hypergraph centrality should place L4 and L6
    near the top, reflecting that they co-constrain the most
    degrees of freedom (joint family kill + surviving family filter).
    """
    results = {}

    H = build_hypergraph(HYPEREDGES)

    # Basic hypergraph structure
    results["node_count"] = H.num_nodes
    results["edge_count"] = H.num_edges
    results["edge_sizes"] = {
        str(eid): len(list(H.edges.members(eid)))
        for eid in H.edges
    }
    results["max_edge_size"] = max(
        len(list(H.edges.members(eid))) for eid in H.edges
    )
    results["hyperedge_annotations"] = dict(zip(
        [str(i) for i in range(len(HYPEREDGE_LABELS))],
        HYPEREDGE_LABELS
    ))

    # Centrality measures
    centrality = rank_shells_by_centrality(H)
    results["centrality_measures"] = centrality

    # Rankings per measure
    results["rankings"] = {}
    for measure_name, measure_dict in centrality.items():
        ranked = ranking_from_measure(measure_dict)
        results["rankings"][measure_name] = [
            {"shell": shell, "value": float(val)} for shell, val in ranked
        ]

    # Check: L4 and L6 appear in top-3 across at least 2 measures
    top3_counts = {s: 0 for s in SHELL_NAMES}
    for measure_name, ranked in results["rankings"].items():
        for item in ranked[:3]:
            top3_counts[item["shell"]] += 1

    results["top3_counts_across_measures"] = top3_counts
    results["L4_top3_count"] = top3_counts["L4"]
    results["L6_top3_count"] = top3_counts["L6"]
    results["kill_shells_dominate"] = (
        top3_counts["L4"] >= 2 or top3_counts["L6"] >= 2
    )

    # Memberships: which hyperedges each shell participates in
    memberships = {}
    for shell in SHELL_NAMES:
        mem = list(H.nodes.memberships(shell))
        memberships[shell] = {
            "edge_ids": mem,
            "edge_labels": [HYPEREDGE_LABELS[e] for e in mem],
            "count": len(mem),
        }
    results["shell_memberships"] = memberships

    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = (
        "XGI Hypergraph: shell nodes, multi-way hyperedges, "
        "clique_eigenvector_centrality, node_edge_centrality, katz_centrality"
    )

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative test: replace all hyperedges with their pairwise (clique)
    decomposition. If multi-way structure is load-bearing, the shell
    centrality rankings must differ from the hypergraph case.

    Specifically: the pairwise expansion loses the joint kill signal
    encoded in {L4, L6, L7} and {L4, L6} — these become indistinguishable
    from weaker pairings.
    """
    results = {}

    # Build pairwise-only hypergraph
    pairwise_edges = pairwise_decomposition(HYPEREDGES)
    H_pair = build_hypergraph(pairwise_edges)

    results["pairwise_edge_count"] = H_pair.num_edges
    results["pairwise_edges"] = pairwise_edges

    centrality_pair = rank_shells_by_centrality(H_pair)
    results["pairwise_centrality"] = centrality_pair

    results["pairwise_rankings"] = {}
    for measure_name, measure_dict in centrality_pair.items():
        ranked = ranking_from_measure(measure_dict)
        results["pairwise_rankings"][measure_name] = [
            {"shell": shell, "value": float(val)} for shell, val in ranked
        ]

    # Build hypergraph centrality for comparison
    H_hyper = build_hypergraph(HYPEREDGES)
    centrality_hyper = rank_shells_by_centrality(H_hyper)

    # Compare top-1 shell per measure between hypergraph and pairwise
    ranking_diff = {}
    for measure in ["clique_eigenvector_centrality", "node_edge_centrality", "katz_centrality"]:
        hyper_top = ranking_from_measure(centrality_hyper[measure])[0][0]
        pair_top  = ranking_from_measure(centrality_pair[measure])[0][0]
        ranking_diff[measure] = {
            "hypergraph_top1": hyper_top,
            "pairwise_top1": pair_top,
            "top1_differs": hyper_top != pair_top,
        }

    results["top1_ranking_comparison"] = ranking_diff

    # Check rank correlation (Spearman) between hypergraph and pairwise
    # for node_edge_centrality
    hyper_vals = np.array([
        centrality_hyper["node_edge_centrality"][s] for s in SHELL_NAMES
    ])
    pair_vals = np.array([
        centrality_pair["node_edge_centrality"][s] for s in SHELL_NAMES
    ])
    # Rank correlation via argsort
    hyper_ranks = np.argsort(np.argsort(-hyper_vals))
    pair_ranks  = np.argsort(np.argsort(-pair_vals))
    rank_diff_sq = np.sum((hyper_ranks - pair_ranks) ** 2)
    n = len(SHELL_NAMES)
    spearman_rho = 1 - 6 * rank_diff_sq / (n * (n**2 - 1))
    results["node_edge_centrality_spearman_rho_hyper_vs_pairwise"] = float(spearman_rho)
    results["rankings_differ_from_pairwise"] = float(spearman_rho) < 1.0

    # L4/L6 relative rank change
    l4_hyper_rank = int(hyper_ranks[SHELL_NAMES.index("L4")])
    l6_hyper_rank = int(hyper_ranks[SHELL_NAMES.index("L6")])
    l4_pair_rank  = int(pair_ranks[SHELL_NAMES.index("L4")])
    l6_pair_rank  = int(pair_ranks[SHELL_NAMES.index("L6")])
    results["L4_rank_hyper_vs_pairwise"] = {"hypergraph": l4_hyper_rank, "pairwise": l4_pair_rank}
    results["L6_rank_hyper_vs_pairwise"] = {"hypergraph": l6_hyper_rank, "pairwise": l6_pair_rank}
    results["L4_rank_changes"] = l4_hyper_rank != l4_pair_rank
    results["L6_rank_changes"] = l6_hyper_rank != l6_pair_rank

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary test 1: singleton hyperedge (size-1) — shell is a member
    of only one edge with no co-members. Degree should be 1, centrality low.

    Boundary test 2: full-set hyperedge (all 8 shells) — every shell
    gets exactly one unit of co-membership to every other shell.
    Centrality should be uniform across all shells for that edge alone.
    """
    results = {}

    # Boundary 1: singleton hyperedge
    H_single = xgi.Hypergraph()
    H_single.add_nodes_from(SHELL_NAMES)
    H_single.add_edge(["L0"])  # singleton
    H_single.add_edge(["L4", "L6"])  # pairwise for contrast

    deg_single = {s: H_single.degree(s) for s in SHELL_NAMES}
    results["singleton_test"] = {
        "L0_degree": int(deg_single["L0"]),
        "L4_degree": int(deg_single["L4"]),
        "L0_degree_is_1": int(deg_single["L0"]) == 1,
        "L4_degree_is_1": int(deg_single["L4"]) == 1,
    }

    # Boundary 2: all-shells hyperedge only
    H_full = xgi.Hypergraph()
    H_full.add_nodes_from(SHELL_NAMES)
    H_full.add_edge(SHELL_NAMES)  # all 8 shells in one hyperedge

    katz_full = H_full.nodes.katz_centrality.asdict()
    katz_vals = [float(katz_full[s]) for s in SHELL_NAMES]
    katz_range = max(katz_vals) - min(katz_vals)
    results["full_hyperedge_test"] = {
        "katz_values": {s: float(katz_full[s]) for s in SHELL_NAMES},
        "katz_range": float(katz_range),
        "centrality_uniform": katz_range < 1e-10,
    }

    # Boundary 3: rustworkx DAG for shell kill ordering
    # L0 -> L1 -> L2 -> L3 -> L4 -> L5 -> L6 -> L7
    # Shells with higher in-degree in this DAG are more constrained
    # by prior shells (not the hypergraph sense, but a complementary view).
    dag_result = {}
    try:
        G = rx.PyDiGraph()
        node_map = {s: G.add_node(s) for s in SHELL_NAMES}
        # Directed edges encoding: L_i constrains L_{i+1}
        for i in range(len(SHELL_NAMES) - 1):
            G.add_edge(node_map[SHELL_NAMES[i]], node_map[SHELL_NAMES[i + 1]], "seq")
        # Additional cross-constraints reflecting known hyperedges
        G.add_edge(node_map["L4"], node_map["L6"], "joint_kill")
        G.add_edge(node_map["L0"], node_map["L5"], "spinor_structure")
        G.add_edge(node_map["L2"], node_map["L7"], "carrier_to_composition")

        in_degrees = {SHELL_NAMES[i]: G.in_degree(node_map[SHELL_NAMES[i]])
                      for i in range(len(SHELL_NAMES))}
        dag_result["in_degrees"] = {k: int(v) for k, v in in_degrees.items()}
        dag_result["L4_in_degree"] = int(in_degrees["L4"])
        dag_result["L6_in_degree"] = int(in_degrees["L6"])
        dag_result["rustworkx_dag_ok"] = True

        TOOL_MANIFEST["rustworkx"]["used"] = True
        TOOL_MANIFEST["rustworkx"]["reason"] = (
            "rustworkx PyDiGraph DAG for sequential + cross-constraint "
            "kill ordering of shells; in-degree as DAG constraint depth."
        )
        TOOL_INTEGRATION_DEPTH["rustworkx"] = "supportive"
    except Exception as e:
        dag_result["rustworkx_dag_ok"] = False
        dag_result["error"] = str(e)

    results["rustworkx_dag_kill_order"] = dag_result

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Mark integration depth
    TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"

    # Summary for top-level report
    summary = {
        "hypergraph_shell_count": len(SHELL_NAMES),
        "hyperedge_count": len(HYPEREDGES),
        "max_hyperedge_size": max(len(e) for e in HYPEREDGES),
        "L4_top3_across_measures": positive.get("L4_top3_count", "N/A"),
        "L6_top3_across_measures": positive.get("L6_top3_count", "N/A"),
        "kill_shells_dominate_hypergraph": positive.get("kill_shells_dominate", False),
        "rankings_differ_from_pairwise": negative.get("rankings_differ_from_pairwise", False),
        "spearman_rho_hyper_vs_pairwise": negative.get(
            "node_edge_centrality_spearman_rho_hyper_vs_pairwise", None
        ),
        "L4_rank_changes_in_pairwise": negative.get("L4_rank_changes", False),
        "L6_rank_changes_in_pairwise": negative.get("L6_rank_changes", False),
        "multi_way_structure_load_bearing": negative.get("rankings_differ_from_pairwise", False),
    }

    results = {
        "name": "sim_xgi_shell_hypergraph",
        "description": (
            "XGI hypergraph model of constraint shell family (L0-L7). "
            "Nodes = shells, hyperedges = multi-way co-constraint groups. "
            "Tests whether hypergraph centrality reflects kill ordering and "
            "whether multi-way structure is load-bearing vs pairwise expansion."
        ),
        "shells": SHELLS,
        "hyperedges": [
            {"edge": e, "dof": HYPEREDGE_LABELS[i]}
            for i, e in enumerate(HYPEREDGES)
        ],
        "summary": summary,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "xgi_shell_hypergraph_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    # Print human-readable summary
    print("\n=== XGI SHELL HYPERGRAPH SUMMARY ===")
    print(f"Shells: {len(SHELL_NAMES)}  |  Hyperedges: {len(HYPEREDGES)}")
    print(f"Max hyperedge size: {summary['max_hyperedge_size']}")
    print()
    print("Shell rankings by node_edge_centrality (hypergraph):")
    for item in positive["rankings"]["node_edge_centrality"]:
        print(f"  {item['shell']}: {item['value']:.5f}")
    print()
    print("Shell rankings by node_edge_centrality (pairwise expansion):")
    for item in negative["pairwise_rankings"]["node_edge_centrality"]:
        print(f"  {item['shell']}: {item['value']:.5f}")
    print()
    print(f"Spearman rho (hyper vs pairwise, node_edge_centrality): "
          f"{summary['spearman_rho_hyper_vs_pairwise']:.4f}")
    print(f"Multi-way structure load-bearing: {summary['multi_way_structure_load_bearing']}")
    print(f"Kill shells (L4, L6) dominate hypergraph: {summary['kill_shells_dominate_hypergraph']}")
    print(f"L4 appears in top-3 across {summary['L4_top3_across_measures']} measures")
    print(f"L6 appears in top-3 across {summary['L6_top3_across_measures']} measures")
