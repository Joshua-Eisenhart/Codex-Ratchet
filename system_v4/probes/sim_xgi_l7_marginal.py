#!/usr/bin/env python3
"""
sim_xgi_l7_marginal.py

Quantify L7's marginal contribution to the joint kill with L4 and L6
by comparing three hypergraph variants:

  H1: includes {L4, L6} only (2-way joint kill)
  H2: includes {L4, L6, L7} (3-way, L7 added)
  H3: includes {L4, L7} (L7 present, L6 absent)

Positive test: adding L7 to the {L4,L6} hyperedge materially shifts
  node_edge_centrality for L4 and/or L6 (marginal contribution of L7 > 0).

Negative test: L7 alone with L4 (H3, no L6) produces a different
  centrality profile than L7 with both L4 and L6 (H2), confirming
  L6 is not interchangeable with L7 in the joint kill.

Boundary test: compare marginal contribution magnitudes —
  is L7's marginal contribution to L4/L6 centrality larger or smaller
  than L6's marginal contribution to L4/L7 centrality?
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


def fill_unused_tool_reasons():
    for tool_name, tool_info in TOOL_MANIFEST.items():
        if tool_info["tried"] and not tool_info["used"] and not tool_info["reason"]:
            tool_info["reason"] = (
                "available in environment but not used in this structural XGI lane"
            )

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

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
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

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

SHELLS = {
    "L0": "density_matrix_validity",
    "L1": "loop_family_finiteness",
    "L2": "hopf_carrier_structure",
    "L3": "operator_chirality",
    "L4": "engine_family_absolute_kill",
    "L5": "axis_orthogonality",
    "L6": "reversible_family_kill",
    "L7": "full_axis_composition",
}

SHELL_NAMES = list(SHELLS.keys())

# Base hyperedges shared across all three variants (everything except the
# joint kill edges that we're varying).
BASE_HYPEREDGES = [
    ["L0", "L1"],         # density_matrix_validity_and_finiteness
    ["L2", "L3", "L4"],   # spinor_carrier_chirality_composition
    ["L0", "L2", "L5"],   # spinor_structure_finitude_carrier_su2
    ["L3", "L5", "L7"],   # axis_orthogonality_manifold
    ["L1", "L4"],         # family_count_upper_bound
    ["L2", "L6", "L7"],   # composition_reversibility_surface
]

# The varied edge:
EDGE_L4_L6     = ["L4", "L6"]         # H1: 2-way joint kill
EDGE_L4_L6_L7  = ["L4", "L6", "L7"]  # H2: 3-way (L7 added)
EDGE_L4_L7     = ["L4", "L7"]         # H3: L7 without L6

H1_HYPEREDGES = BASE_HYPEREDGES + [EDGE_L4_L6]
H2_HYPEREDGES = BASE_HYPEREDGES + [EDGE_L4_L6_L7]
H3_HYPEREDGES = BASE_HYPEREDGES + [EDGE_L4_L7]

# For the "L6 marginal" comparison we also need:
# H4: base + {L4, L7} + {L4, L6, L7} — adding L6 to what was L4+L7
EDGE_L4_L6_L7_alt = ["L4", "L6", "L7"]  # same as H2 extra edge
H4_HYPEREDGES = BASE_HYPEREDGES + [EDGE_L4_L7, EDGE_L4_L6_L7_alt]


def build_hypergraph(hyperedges):
    """Build an XGI Hypergraph from a list of shell-name lists."""
    H = xgi.Hypergraph()
    H.add_nodes_from(SHELL_NAMES)
    for edge in hyperedges:
        H.add_edge(edge)
    return H


def get_node_edge_centrality(H):
    """Return node_edge_centrality dict for the hypergraph."""
    nec = H.nodes.node_edge_centrality.asdict()
    return {k: float(v) for k, v in nec.items()}


def get_all_centralities(H):
    """Return all four centrality measures."""
    measures = {}
    deg = {s: int(H.degree(s)) for s in SHELL_NAMES}
    measures["hyperedge_degree"] = deg
    cec = H.nodes.clique_eigenvector_centrality.asdict()
    measures["clique_eigenvector_centrality"] = {k: float(v) for k, v in cec.items()}
    nec = H.nodes.node_edge_centrality.asdict()
    measures["node_edge_centrality"] = {k: float(v) for k, v in nec.items()}
    katz = H.nodes.katz_centrality.asdict()
    measures["katz_centrality"] = {k: float(v) for k, v in katz.items()}
    return measures


def ranking(measure_dict):
    """Return shells sorted descending by centrality."""
    return sorted(measure_dict.items(), key=lambda x: x[1], reverse=True)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Compare H1 ({L4,L6}) vs H2 ({L4,L6,L7}).
    Does adding L7 shift L4 or L6 node_edge_centrality?
    """
    results = {}

    H1 = build_hypergraph(H1_HYPEREDGES)
    H2 = build_hypergraph(H2_HYPEREDGES)

    c_H1 = get_all_centralities(H1)
    c_H2 = get_all_centralities(H2)

    results["H1_description"] = "base hyperedges + {L4, L6} (2-way joint kill)"
    results["H2_description"] = "base hyperedges + {L4, L6, L7} (3-way, L7 added)"

    results["H1_centralities"] = c_H1
    results["H2_centralities"] = c_H2

    # Marginal shift of adding L7: delta = c_H2 - c_H1 for each shell
    delta_nec = {
        s: c_H2["node_edge_centrality"][s] - c_H1["node_edge_centrality"][s]
        for s in SHELL_NAMES
    }
    delta_cec = {
        s: c_H2["clique_eigenvector_centrality"][s] - c_H1["clique_eigenvector_centrality"][s]
        for s in SHELL_NAMES
    }

    results["L7_marginal_delta_nec"] = delta_nec
    results["L7_marginal_delta_cec"] = delta_cec

    results["L4_nec_H1"] = c_H1["node_edge_centrality"]["L4"]
    results["L4_nec_H2"] = c_H2["node_edge_centrality"]["L4"]
    results["L6_nec_H1"] = c_H1["node_edge_centrality"]["L6"]
    results["L6_nec_H2"] = c_H2["node_edge_centrality"]["L6"]
    results["L7_nec_H1"] = c_H1["node_edge_centrality"]["L7"]
    results["L7_nec_H2"] = c_H2["node_edge_centrality"]["L7"]

    # Test: does adding L7 materially shift L4 or L6? (threshold 0.001)
    THRESHOLD = 0.001
    results["L7_addition_shifts_L4_nec"] = abs(delta_nec["L4"]) > THRESHOLD
    results["L7_addition_shifts_L6_nec"] = abs(delta_nec["L6"]) > THRESHOLD
    results["L7_addition_shifts_any_kill_shell"] = (
        abs(delta_nec["L4"]) > THRESHOLD or abs(delta_nec["L6"]) > THRESHOLD
    )

    # Rankings H1 vs H2
    results["H1_nec_ranking"] = [
        {"shell": s, "value": v} for s, v in ranking(c_H1["node_edge_centrality"])
    ]
    results["H2_nec_ranking"] = [
        {"shell": s, "value": v} for s, v in ranking(c_H2["node_edge_centrality"])
    ]

    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = (
        "XGI Hypergraph: three variant hypergraphs (H1, H2, H3) to isolate "
        "L7 marginal contribution to joint kill; node_edge_centrality, "
        "clique_eigenvector_centrality, katz_centrality computed on each"
    )

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative test: compare H2 ({L4,L6,L7}) vs H3 ({L4,L7}, no L6).
    L7 alone with L4 should give a materially different centrality profile
    than L7 with both L4 and L6 — confirming L6 is not interchangeable with L7.
    """
    results = {}

    H2 = build_hypergraph(H2_HYPEREDGES)
    H3 = build_hypergraph(H3_HYPEREDGES)

    c_H2 = get_all_centralities(H2)
    c_H3 = get_all_centralities(H3)

    results["H2_description"] = "base + {L4, L6, L7}"
    results["H3_description"] = "base + {L4, L7} (L7 without L6)"

    results["H2_nec"] = c_H2["node_edge_centrality"]
    results["H3_nec"] = c_H3["node_edge_centrality"]

    delta_H2_vs_H3 = {
        s: c_H2["node_edge_centrality"][s] - c_H3["node_edge_centrality"][s]
        for s in SHELL_NAMES
    }
    results["delta_H2_vs_H3_nec"] = delta_H2_vs_H3

    results["L6_centrality_H2"] = c_H2["node_edge_centrality"]["L6"]
    results["L6_centrality_H3"] = c_H3["node_edge_centrality"]["L6"]
    results["L6_drops_without_joint_edge"] = (
        c_H3["node_edge_centrality"]["L6"] < c_H2["node_edge_centrality"]["L6"]
    )

    results["H3_nec_ranking"] = [
        {"shell": s, "value": v} for s, v in ranking(c_H3["node_edge_centrality"])
    ]

    # Rank correlation H2 vs H3 (Spearman)
    nec_H2_vals = np.array([c_H2["node_edge_centrality"][s] for s in SHELL_NAMES])
    nec_H3_vals = np.array([c_H3["node_edge_centrality"][s] for s in SHELL_NAMES])
    r_H2 = np.argsort(np.argsort(-nec_H2_vals))
    r_H3 = np.argsort(np.argsort(-nec_H3_vals))
    spearman = 1 - 6 * np.sum((r_H2 - r_H3) ** 2) / (len(SHELL_NAMES) * (len(SHELL_NAMES)**2 - 1))
    results["spearman_rho_H2_vs_H3"] = float(spearman)
    results["H2_H3_rankings_differ"] = float(spearman) < 1.0

    # Top-1 shell in H2 vs H3?
    top_H2 = ranking(c_H2["node_edge_centrality"])[0][0]
    top_H3 = ranking(c_H3["node_edge_centrality"])[0][0]
    results["top1_H2"] = top_H2
    results["top1_H3"] = top_H3
    results["top1_differs_H2_H3"] = top_H2 != top_H3

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary test: compare marginal contributions.

    L7 marginal contribution = delta(nec[L4]) + delta(nec[L6]) when L7
    is added to {L4, L6} (i.e., H1 -> H2).

    L6 marginal contribution = delta(nec[L4]) + delta(nec[L7]) when L6
    is added to {L4, L7} (i.e., H3 -> H2 or H3 -> H4).

    We use the sum of absolute nec changes across L4 and the co-member
    as a proxy for "marginal contribution magnitude".

    Also compute the full delta vector (all shells) for both marginals.
    """
    results = {}

    H1 = build_hypergraph(H1_HYPEREDGES)  # base + {L4, L6}
    H2 = build_hypergraph(H2_HYPEREDGES)  # base + {L4, L6, L7}
    H3 = build_hypergraph(H3_HYPEREDGES)  # base + {L4, L7}

    c_H1 = get_node_edge_centrality(H1)
    c_H2 = get_node_edge_centrality(H2)
    c_H3 = get_node_edge_centrality(H3)

    # L7 marginal: H1 -> H2 (adding L7 to {L4, L6})
    delta_L7 = {s: c_H2[s] - c_H1[s] for s in SHELL_NAMES}
    L7_marginal_L4 = abs(delta_L7["L4"])
    L7_marginal_L6 = abs(delta_L7["L6"])
    L7_marginal_total = sum(abs(v) for v in delta_L7.values())

    # L6 marginal: H3 -> H2 (adding L6 to {L4, L7})
    delta_L6 = {s: c_H2[s] - c_H3[s] for s in SHELL_NAMES}
    L6_marginal_L4 = abs(delta_L6["L4"])
    L6_marginal_L7 = abs(delta_L6["L7"])
    L6_marginal_total = sum(abs(v) for v in delta_L6.values())

    results["L7_marginal_contribution"] = {
        "description": "delta nec when L7 added to {L4,L6} (H1 -> H2)",
        "delta_by_shell": delta_L7,
        "abs_impact_on_L4": L7_marginal_L4,
        "abs_impact_on_L6": L7_marginal_L6,
        "total_abs_delta": L7_marginal_total,
    }

    results["L6_marginal_contribution"] = {
        "description": "delta nec when L6 added to {L4,L7} (H3 -> H2)",
        "delta_by_shell": delta_L6,
        "abs_impact_on_L4": L6_marginal_L4,
        "abs_impact_on_L7": L6_marginal_L7,
        "total_abs_delta": L6_marginal_total,
    }

    results["L7_marginal_total_abs"] = L7_marginal_total
    results["L6_marginal_total_abs"] = L6_marginal_total
    results["L6_larger_marginal_than_L7"] = L6_marginal_total > L7_marginal_total
    results["winner"] = "L6" if L6_marginal_total > L7_marginal_total else "L7"
    results["winner_description"] = (
        "L6 has a larger total marginal contribution to the joint kill "
        "than L7 (summed over all shells)"
        if L6_marginal_total > L7_marginal_total
        else "L7 has a larger total marginal contribution to the joint kill "
             "than L6 (summed over all shells)"
    )

    # What does L7 uniquely add vs L6 adds?
    results["L7_unique_add_impact_on_L7_shell"] = abs(delta_L7["L7"])
    results["L6_unique_add_impact_on_L6_shell"] = abs(delta_L6["L6"])

    # Rank comparison: which shell changes rank the most under L7 addition?
    nec_H1_arr = np.array([c_H1[s] for s in SHELL_NAMES])
    nec_H2_arr = np.array([c_H2[s] for s in SHELL_NAMES])
    r_H1 = np.argsort(np.argsort(-nec_H1_arr))
    r_H2 = np.argsort(np.argsort(-nec_H2_arr))
    rank_changes = {SHELL_NAMES[i]: int(r_H2[i]) - int(r_H1[i]) for i in range(len(SHELL_NAMES))}
    results["rank_changes_H1_to_H2"] = rank_changes
    results["L7_rank_change_H1_to_H2"] = rank_changes.get("L7")

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"

    summary = {
        "L4_nec_H1": positive.get("L4_nec_H1"),
        "L4_nec_H2": positive.get("L4_nec_H2"),
        "L6_nec_H1": positive.get("L6_nec_H1"),
        "L6_nec_H2": positive.get("L6_nec_H2"),
        "L7_nec_H1": positive.get("L7_nec_H1"),
        "L7_nec_H2": positive.get("L7_nec_H2"),
        "L7_addition_shifts_L4": positive.get("L7_addition_shifts_L4_nec"),
        "L7_addition_shifts_L6": positive.get("L7_addition_shifts_L6_nec"),
        "L7_addition_shifts_any_kill_shell": positive.get("L7_addition_shifts_any_kill_shell"),
        "L6_drops_without_joint_edge": negative.get("L6_drops_without_joint_edge"),
        "H2_H3_rankings_differ": negative.get("H2_H3_rankings_differ"),
        "spearman_rho_H2_vs_H3": negative.get("spearman_rho_H2_vs_H3"),
        "L7_marginal_total_abs": boundary.get("L7_marginal_total_abs"),
        "L6_marginal_total_abs": boundary.get("L6_marginal_total_abs"),
        "larger_marginal_contributor": boundary.get("winner"),
    }

    fill_unused_tool_reasons()

    results = {
        "name": "sim_xgi_l7_marginal",
        "description": (
            "Quantify L7 marginal contribution to joint kill (L4+L6) via "
            "three XGI hypergraph variants: H1={L4,L6}, H2={L4,L6,L7}, H3={L4,L7}. "
            "Measures shift in node_edge_centrality for L4, L6 when L7 added/removed."
        ),
        "shells": SHELLS,
        "hypergraph_variants": {
            "H1": {"extra_edge": EDGE_L4_L6,    "description": "base + {L4,L6}"},
            "H2": {"extra_edge": EDGE_L4_L6_L7, "description": "base + {L4,L6,L7}"},
            "H3": {"extra_edge": EDGE_L4_L7,    "description": "base + {L4,L7}"},
        },
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
    out_path = os.path.join(out_dir, "xgi_l7_marginal_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    print("\n=== XGI L7 MARGINAL CONTRIBUTION SUMMARY ===")
    print(f"node_edge_centrality — H1 vs H2 (effect of adding L7 to {{L4,L6}}):")
    print(f"  L4: {summary['L4_nec_H1']:.5f} -> {summary['L4_nec_H2']:.5f}")
    print(f"  L6: {summary['L6_nec_H1']:.5f} -> {summary['L6_nec_H2']:.5f}")
    print(f"  L7: {summary['L7_nec_H1']:.5f} -> {summary['L7_nec_H2']:.5f}")
    print(f"L7 addition shifts any kill shell: {summary['L7_addition_shifts_any_kill_shell']}")
    print(f"H2 vs H3 Spearman rho: {summary['spearman_rho_H2_vs_H3']:.4f}")
    print(f"L7 marginal total |delta nec|: {summary['L7_marginal_total_abs']:.6f}")
    print(f"L6 marginal total |delta nec|: {summary['L6_marginal_total_abs']:.6f}")
    print(f"Larger marginal contributor: {summary['larger_marginal_contributor']}")
