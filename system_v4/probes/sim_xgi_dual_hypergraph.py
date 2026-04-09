#!/usr/bin/env python3
"""
sim_xgi_dual_hypergraph.py
---------------------------
Constructs the dual hypergraph of the 28-family XGI hypergraph: the 13
constraint-roles become nodes and families become hyperedges.  Two
constraint-roles are connected by a hyperedge whenever they share at
least one family -- that shared family IS the hyperedge.

Hypothesis: constraint-roles are more natural structural units than
individual families.

Classification: canonical
"""

import json
import os
import numpy as np
from collections import Counter, defaultdict

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": "not relevant -- no gradient computation needed"},
    "pyg":        {"tried": False, "used": False, "reason": "not relevant -- hypergraph, not pairwise graph"},
    "z3":         {"tried": False, "used": False, "reason": "not relevant -- structural analysis, not SMT"},
    "cvc5":       {"tried": False, "used": False, "reason": "not relevant -- no theorem proving needed"},
    "sympy":      {"tried": False, "used": False, "reason": "not relevant -- no symbolic algebra needed"},
    "clifford":   {"tried": False, "used": False, "reason": "not relevant -- no geometric algebra needed"},
    "geomstats":  {"tried": False, "used": False, "reason": "not relevant -- no manifold geometry needed"},
    "e3nn":       {"tried": False, "used": False, "reason": "not relevant -- no equivariant networks needed"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not relevant -- xgi handles hypergraph natively"},
    "xgi":        {"tried": True,  "used": True,  "reason": "primary tool -- dual hypergraph construction and analysis"},
    "toponetx":   {"tried": False, "used": False, "reason": "not relevant for this sim"},
    "gudhi":      {"tried": False, "used": False, "reason": "not relevant for this sim"},
}

# -- Try-import blocks (all 12 tools) ----------------------------------

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
    import xgi
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
# DATA: 28 IRREDUCIBLE FAMILIES  (mirrored from sim_xgi_family_hypergraph)
# =====================================================================

STRUCTURAL_OPS = [
    "density_matrix", "purification", "z_dephasing", "x_dephasing",
    "depolarizing", "amplitude_damping", "phase_damping", "bit_flip",
    "phase_flip", "bit_phase_flip", "unitary_rotation", "z_measurement",
    "CNOT", "CZ", "SWAP", "Hadamard", "T_gate", "iSWAP", "cartan_kak",
]

TYPE_MEASURES = [
    "eigenvalue_decomposition", "husimi_q", "l1_coherence",
    "relative_entropy_coherence", "wigner_negativity", "hopf_connection",
    "chiral_overlap", "mutual_information", "quantum_discord",
]

ALL_FAMILIES = STRUCTURAL_OPS + TYPE_MEASURES
FAMILY_INDEX = {name: i for i, name in enumerate(ALL_FAMILIES)}

# -- 13 constraint-roles (original hyperedges) --------------------------

HYPEREDGE_DEFS = {
    "channel_family": [
        "z_dephasing", "x_dephasing", "depolarizing", "amplitude_damping",
        "phase_damping", "bit_flip", "phase_flip", "bit_phase_flip",
    ],
    "entangling_gates": ["CNOT", "CZ", "iSWAP", "cartan_kak"],
    "clifford_group": ["CNOT", "CZ", "SWAP", "Hadamard", "phase_flip"],
    "universal_gate_set": ["CNOT", "Hadamard", "T_gate"],
    "coherence_measures": ["l1_coherence", "relative_entropy_coherence"],
    "phase_space_reps": ["husimi_q", "wigner_negativity", "eigenvalue_decomposition"],
    "geometric_structure": ["hopf_connection", "chiral_overlap"],
    "pauli_channels": ["bit_flip", "phase_flip", "bit_phase_flip"],
    "dephasing_pair": ["z_dephasing", "x_dephasing"],
    "state_preparation": ["density_matrix", "purification"],
    "information_measures": ["mutual_information", "quantum_discord"],
    "non_clifford_completion": ["T_gate", "cartan_kak"],
    "damping_channels": ["amplitude_damping", "phase_damping"],
}

ROLE_NAMES = list(HYPEREDGE_DEFS.keys())
ROLE_INDEX = {name: i for i, name in enumerate(ROLE_NAMES)}


# =====================================================================
# ORIGINAL HYPERGRAPH (families=nodes, roles=edges)
# =====================================================================

def build_original_hypergraph():
    """Build the original XGI hypergraph (28 family-nodes, 13 role-edges)."""
    H = xgi.Hypergraph()
    H.add_nodes_from(range(len(ALL_FAMILIES)))
    for role_name in ROLE_NAMES:
        members = HYPEREDGE_DEFS[role_name]
        H.add_edge([FAMILY_INDEX[f] for f in members])
    return H


# =====================================================================
# DUAL HYPERGRAPH CONSTRUCTION
# =====================================================================

def build_family_to_roles_map():
    """Map each family to the set of roles it belongs to."""
    fam_to_roles = defaultdict(set)
    for role_name, members in HYPEREDGE_DEFS.items():
        for fam in members:
            fam_to_roles[fam].add(role_name)
    return dict(fam_to_roles)


def build_dual_hypergraph():
    """
    Dual hypergraph: 13 constraint-roles are nodes.
    For each family that belongs to >=2 roles, create a hyperedge
    connecting those roles.  The family IS the hyperedge.
    """
    fam_to_roles = build_family_to_roles_map()

    D = xgi.Hypergraph()
    D.add_nodes_from(range(len(ROLE_NAMES)))

    dual_edge_labels = []  # track which family each edge represents
    for fam_name, roles in sorted(fam_to_roles.items()):
        if len(roles) >= 2:
            role_indices = sorted([ROLE_INDEX[r] for r in roles])
            D.add_edge(role_indices)
            dual_edge_labels.append(fam_name)

    return D, dual_edge_labels


# =====================================================================
# ANALYSIS
# =====================================================================

def compute_dual_stats(D, dual_edge_labels):
    """Core statistics for the dual hypergraph."""
    degrees = D.nodes.degree.aslist()
    edge_sizes = D.edges.size.aslist()

    degree_map = {ROLE_NAMES[i]: degrees[i] for i in range(len(ROLE_NAMES))}
    sorted_by_degree = sorted(degree_map.items(), key=lambda x: -x[1])

    return {
        "num_nodes": D.num_nodes,
        "num_edges": D.num_edges,
        "edge_labels": dual_edge_labels,
        "edge_sizes": edge_sizes,
        "edge_size_distribution": dict(Counter(edge_sizes)),
        "node_degrees": degree_map,
        "degree_ranking": sorted_by_degree,
        "max_degree_role": sorted_by_degree[0][0] if sorted_by_degree else None,
        "max_degree_value": sorted_by_degree[0][1] if sorted_by_degree else 0,
        "mean_degree": float(np.mean(degrees)),
        "is_connected": xgi.is_connected(D),
        "num_connected_components": xgi.number_connected_components(D),
    }


def find_bridge_families(dual_edge_labels, D):
    """Which families bridge the most constraint-roles (largest dual edges)."""
    edge_sizes = D.edges.size.aslist()
    bridge_info = []
    for i, fam_name in enumerate(dual_edge_labels):
        members = list(D.edges.members(i))
        bridge_info.append({
            "family": fam_name,
            "roles_bridged": edge_sizes[i],
            "roles": [ROLE_NAMES[m] for m in members],
        })
    bridge_info.sort(key=lambda x: -x["roles_bridged"])
    return bridge_info


def compute_dual_incidence(D):
    """Incidence matrix of the dual and its rank."""
    I_dual = xgi.incidence_matrix(D, sparse=False)
    rank_dual = int(np.linalg.matrix_rank(I_dual))
    return {
        "incidence_shape": list(I_dual.shape),
        "incidence_rank": rank_dual,
        "max_possible_rank": min(I_dual.shape),
    }, I_dual


def compare_with_original(H_orig, D):
    """Compare dual incidence rank with original."""
    I_orig = xgi.incidence_matrix(H_orig, sparse=False)
    I_dual = xgi.incidence_matrix(D, sparse=False)
    rank_orig = int(np.linalg.matrix_rank(I_orig))
    rank_dual = int(np.linalg.matrix_rank(I_dual))
    return {
        "original_incidence_shape": list(I_orig.shape),
        "original_incidence_rank": rank_orig,
        "dual_incidence_shape": list(I_dual.shape),
        "dual_incidence_rank": rank_dual,
        "rank_difference": rank_orig - rank_dual,
        "original_components": xgi.number_connected_components(H_orig),
        "dual_components": xgi.number_connected_components(D),
        "dual_fewer_components": (
            xgi.number_connected_components(D)
            < xgi.number_connected_components(H_orig)
        ),
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    D, labels = build_dual_hypergraph()
    H_orig = build_original_hypergraph()
    stats = compute_dual_stats(D, labels)
    bridges = find_bridge_families(labels, D)
    comparison = compare_with_original(H_orig, D)

    # P1: channel_family should be the most connected role
    #     (shares members with pauli_channels, dephasing_pair, damping_channels,
    #      clifford_group via phase_flip)
    cf_degree = stats["node_degrees"].get("channel_family", 0)
    results["P1_channel_family_most_connected"] = {
        "channel_family_degree": cf_degree,
        "max_degree_value": stats["max_degree_value"],
        "max_degree_role": stats["max_degree_role"],
        "pass": cf_degree == stats["max_degree_value"],
        "detail": (
            f"channel_family degree={cf_degree}, "
            f"max={stats['max_degree_value']} ({stats['max_degree_role']})"
        ),
    }

    # P2: CNOT should appear in the most dual hyperedges
    #     (bridges entangling_gates, clifford_group, universal_gate_set)
    cnot_edge_count = sum(1 for lab in labels if lab == "CNOT")
    max_bridge = bridges[0]["roles_bridged"] if bridges else 0
    cnot_bridge = next(
        (b for b in bridges if b["family"] == "CNOT"), None
    )
    cnot_roles_bridged = cnot_bridge["roles_bridged"] if cnot_bridge else 0
    results["P2_cnot_most_dual_edges"] = {
        "cnot_roles_bridged": cnot_roles_bridged,
        "max_roles_bridged": max_bridge,
        "top_bridge_family": bridges[0]["family"] if bridges else None,
        "cnot_is_top_or_tied": cnot_roles_bridged == max_bridge,
        "pass": cnot_roles_bridged == max_bridge,
        "detail": (
            f"CNOT bridges {cnot_roles_bridged} roles, "
            f"max bridge={max_bridge} ({bridges[0]['family'] if bridges else 'none'})"
        ),
    }

    # P3: Dual should have fewer components than original
    results["P3_dual_fewer_components"] = {
        "original_components": comparison["original_components"],
        "dual_components": comparison["dual_components"],
        "pass": comparison["dual_fewer_components"],
        "detail": (
            f"original={comparison['original_components']} components, "
            f"dual={comparison['dual_components']} components"
        ),
    }

    # P4: Degree distribution of dual nodes -- not uniform
    degree_vals = list(stats["node_degrees"].values())
    results["P4_degree_distribution_non_uniform"] = {
        "unique_degrees": len(set(degree_vals)),
        "degree_values": degree_vals,
        "pass": len(set(degree_vals)) > 1,
        "detail": "Dual node degrees should vary (roles participate differently)",
    }

    # P5: Dual incidence rank
    inc_info, _ = compute_dual_incidence(D)
    results["P5_dual_incidence_rank"] = {
        "rank": inc_info["incidence_rank"],
        "shape": inc_info["incidence_shape"],
        "max_possible": inc_info["max_possible_rank"],
        "pass": 0 < inc_info["incidence_rank"] <= inc_info["max_possible_rank"],
        "detail": f"rank={inc_info['incidence_rank']} of max {inc_info['max_possible_rank']}",
    }

    # P6: Dual has exactly 13 nodes (one per role)
    results["P6_dual_node_count"] = {
        "num_nodes": stats["num_nodes"],
        "expected": len(ROLE_NAMES),
        "pass": stats["num_nodes"] == len(ROLE_NAMES),
    }

    # P7: Incidence rank comparison
    results["P7_rank_comparison"] = {
        "original_rank": comparison["original_incidence_rank"],
        "dual_rank": comparison["dual_incidence_rank"],
        "pass": comparison["original_incidence_rank"] > 0 and comparison["dual_incidence_rank"] > 0,
        "detail": (
            f"original rank={comparison['original_incidence_rank']}, "
            f"dual rank={comparison['dual_incidence_rank']}"
        ),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: Dual of a hypergraph with no overlapping edges has no dual edges
    #     Using our construction: each node that belongs to >=2 edges creates
    #     a dual hyperedge.  Disjoint edges share no nodes, so 0 dual edges.
    disjoint_roles = {
        "role_a": ["fam_0", "fam_1"],
        "role_b": ["fam_2", "fam_3"],
        "role_c": ["fam_4", "fam_5"],
    }
    disjoint_fam_to_roles = defaultdict(set)
    for rname, members in disjoint_roles.items():
        for fam in members:
            disjoint_fam_to_roles[fam].add(rname)
    # Build dual: only families in >=2 roles produce edges
    D_disjoint = xgi.Hypergraph()
    D_disjoint.add_nodes_from(range(3))
    disjoint_dual_edges = 0
    for fam, roles in disjoint_fam_to_roles.items():
        if len(roles) >= 2:
            disjoint_dual_edges += 1
    d_components = xgi.number_connected_components(D_disjoint)
    results["N1_no_overlap_no_dual_edges"] = {
        "disjoint_dual_edges": disjoint_dual_edges,
        "disjoint_dual_components": d_components,
        "pass": disjoint_dual_edges == 0 and d_components == 3,
        "detail": "Disjoint hyperedges produce isolated dual nodes (no dual edges)",
    }

    # N2: Random role assignment should give different dual structure
    D_real, labels_real = build_dual_hypergraph()
    real_degrees = sorted(D_real.nodes.degree.aslist(), reverse=True)

    np.random.seed(42)
    # Shuffle family-to-role assignment: randomly assign each family to
    # roles (same cardinalities but random membership)
    all_fams = list(ALL_FAMILIES)
    role_sizes = [len(HYPEREDGE_DEFS[r]) for r in ROLE_NAMES]
    shuffled = np.random.permutation(len(all_fams))
    rand_roles = {}
    idx = 0
    for i, role_name in enumerate(ROLE_NAMES):
        sz = role_sizes[i]
        rand_roles[role_name] = [all_fams[j] for j in shuffled[idx:idx + sz]]
        idx += sz

    # Build dual from randomised roles
    rand_fam_to_roles = defaultdict(set)
    for rname, members in rand_roles.items():
        for fam in members:
            rand_fam_to_roles[fam].add(rname)

    D_rand = xgi.Hypergraph()
    D_rand.add_nodes_from(range(len(ROLE_NAMES)))
    for fam, roles in rand_fam_to_roles.items():
        if len(roles) >= 2:
            D_rand.add_edge(sorted([ROLE_INDEX[r] for r in roles]))

    rand_degrees = sorted(D_rand.nodes.degree.aslist(), reverse=True)
    results["N2_random_roles_differ"] = {
        "real_degrees_sorted": real_degrees,
        "random_degrees_sorted": rand_degrees,
        "distributions_differ": real_degrees != rand_degrees,
        "pass": real_degrees != rand_degrees,
        "detail": "Random role assignment must produce different dual topology",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    D, labels = build_dual_hypergraph()

    # B1: XGI's built-in .dual() on original should give same node count
    H_orig = build_original_hypergraph()
    D_builtin = H_orig.dual()
    results["B1_xgi_builtin_dual_node_count"] = {
        "builtin_dual_nodes": D_builtin.num_nodes,
        "our_dual_nodes": D.num_nodes,
        "match": D_builtin.num_nodes == D.num_nodes,
        "pass": D_builtin.num_nodes == len(ROLE_NAMES),
        "detail": "XGI built-in dual should also have 13 nodes",
    }

    # B2: Every dual edge should have size >= 2 (by construction)
    edge_sizes = D.edges.size.aslist()
    results["B2_all_edges_size_ge_2"] = {
        "min_edge_size": min(edge_sizes) if edge_sizes else 0,
        "max_edge_size": max(edge_sizes) if edge_sizes else 0,
        "all_ge_2": all(s >= 2 for s in edge_sizes),
        "pass": len(edge_sizes) > 0 and all(s >= 2 for s in edge_sizes),
        "detail": "Every dual edge connects at least 2 roles (by definition)",
    }

    # B3: Number of dual edges == number of multi-role families
    fam_to_roles = build_family_to_roles_map()
    multi_role_count = sum(1 for roles in fam_to_roles.values() if len(roles) >= 2)
    results["B3_edge_count_matches_multi_role_families"] = {
        "dual_edges": D.num_edges,
        "multi_role_families": multi_role_count,
        "pass": D.num_edges == multi_role_count,
        "detail": "One dual edge per family that spans multiple roles",
    }

    # B4: Isolated roles (degree 0) are those whose members are unique to them
    degrees = D.nodes.degree.aslist()
    isolated_roles = [ROLE_NAMES[i] for i, d in enumerate(degrees) if d == 0]
    results["B4_isolated_roles"] = {
        "isolated_roles": isolated_roles,
        "count": len(isolated_roles),
        "pass": True,  # informational
        "detail": "Roles with no shared families are isolated in dual",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    D, dual_edge_labels = build_dual_hypergraph()
    H_orig = build_original_hypergraph()

    stats = compute_dual_stats(D, dual_edge_labels)
    bridges = find_bridge_families(dual_edge_labels, D)
    inc_info, _ = compute_dual_incidence(D)
    comparison = compare_with_original(H_orig, D)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_tests = {**positive, **negative, **boundary}
    n_pass = sum(1 for v in all_tests.values() if v.get("pass"))
    n_total = len(all_tests)

    results = {
        "name": "xgi_dual_hypergraph",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "summary": {
            "tests_passed": n_pass,
            "tests_total": n_total,
            "all_pass": n_pass == n_total,
        },
        "data": {
            "role_names": ROLE_NAMES,
            "role_count": len(ROLE_NAMES),
            "dual_edge_labels": dual_edge_labels,
            "dual_edge_count": len(dual_edge_labels),
            "family_to_roles": {
                fam: sorted(roles)
                for fam, roles in build_family_to_roles_map().items()
            },
        },
        "analysis": {
            "dual_stats": stats,
            "bridge_families": bridges,
            "dual_incidence": inc_info,
            "comparison_with_original": comparison,
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "xgi_dual_hypergraph_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {n_pass}/{n_total} passed")
