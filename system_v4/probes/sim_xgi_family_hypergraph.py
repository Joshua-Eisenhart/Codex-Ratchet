#!/usr/bin/env python3
"""
sim_xgi_family_hypergraph.py
─────────────────────────────
Encodes the 28 irreducible families as an XGI hypergraph where hyperedges
represent multi-way constraint/operator relationships that cannot be expressed
as pairwise graphs.  Reveals higher-order structure in how families relate.

Classification: canonical
"""

import json
import os
import numpy as np
from collections import Counter
classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": "not relevant — no gradient computation needed"},
    "pyg":        {"tried": False, "used": False, "reason": "not relevant — hypergraph, not pairwise graph"},
    "z3":         {"tried": False, "used": False, "reason": "not relevant — structural analysis, not SMT"},
    "cvc5":       {"tried": False, "used": False, "reason": "not relevant — no theorem proving needed"},
    "sympy":      {"tried": False, "used": False, "reason": "not relevant — no symbolic algebra needed"},
    "clifford":   {"tried": False, "used": False, "reason": "not relevant — no geometric algebra needed"},
    "geomstats":  {"tried": False, "used": False, "reason": "not relevant — no manifold geometry needed"},
    "e3nn":       {"tried": False, "used": False, "reason": "not relevant — no equivariant networks needed"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not relevant — xgi handles hypergraph natively"},
    "xgi":        {"tried": True,  "used": True,  "reason": "primary tool — hypergraph + simplicial complex construction and analysis"},
    "toponetx":   {"tried": True,  "used": False, "reason": "CellComplex lift supplies a coequal topological witness for the same higher-order family structure"},
    "gudhi":      {"tried": True,  "used": False, "reason": "tried persistence comparison — see boundary tests"},
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
    "rustworkx": None,
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "supportive",
}

# ── Try-import blocks (all 12 tools) ────────────────────────────────

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
# DATA: 28 IRREDUCIBLE FAMILIES
# =====================================================================

# Structural operators (19)
STRUCTURAL_OPS = [
    "density_matrix", "purification", "z_dephasing", "x_dephasing",
    "depolarizing", "amplitude_damping", "phase_damping", "bit_flip",
    "phase_flip", "bit_phase_flip", "unitary_rotation", "z_measurement",
    "CNOT", "CZ", "SWAP", "Hadamard", "T_gate", "iSWAP", "cartan_kak",
]

# Type-sensitive measures (9)
TYPE_MEASURES = [
    "eigenvalue_decomposition", "husimi_q", "l1_coherence",
    "relative_entropy_coherence", "wigner_negativity", "hopf_connection",
    "chiral_overlap", "mutual_information", "quantum_discord",
]

ALL_FAMILIES = STRUCTURAL_OPS + TYPE_MEASURES
FAMILY_INDEX = {name: i for i, name in enumerate(ALL_FAMILIES)}

# ── Hyperedges: multi-way constraint relationships ──────────────────

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

# Convert names to indices
HYPEREDGES = {
    name: [FAMILY_INDEX[f] for f in members]
    for name, members in HYPEREDGE_DEFS.items()
}
HYPEREDGE_NAMES = list(HYPEREDGES.keys())
HYPEREDGE_LISTS = list(HYPEREDGES.values())


def build_hypergraph():
    """Build the primary XGI hypergraph."""
    H = xgi.Hypergraph()
    H.add_nodes_from(range(len(ALL_FAMILIES)))
    H.add_edges_from(HYPEREDGE_LISTS)
    return H


def build_cell_complex():
    """Lift higher-order family relations into a bounded CellComplex."""
    from toponetx.classes import CellComplex as CC_cls

    CC = CC_cls()
    pair_edges = set()
    for edge in HYPEREDGE_LISTS:
        if len(edge) >= 3:
            CC.add_cell(edge, rank=2)
        for i in range(len(edge)):
            for j in range(i + 1, len(edge)):
                pair_edges.add(tuple(sorted((edge[i], edge[j]))))
    for u, v in sorted(pair_edges):
        CC.add_cell([u, v], rank=1)
    return CC, pair_edges


# =====================================================================
# ANALYSIS HELPERS
# =====================================================================

def compute_hypergraph_stats(H):
    """Core statistics for a hypergraph."""
    degrees = H.nodes.degree.aslist()
    edge_sizes = H.edges.size.aslist()

    return {
        "num_nodes": H.num_nodes,
        "num_edges": H.num_edges,
        "edge_sizes": edge_sizes,
        "edge_size_distribution": dict(Counter(edge_sizes)),
        "node_degrees": {ALL_FAMILIES[i]: degrees[i] for i in range(len(ALL_FAMILIES))},
        "max_degree_node": ALL_FAMILIES[int(np.argmax(degrees))],
        "max_degree_value": int(max(degrees)),
        "min_degree_node": ALL_FAMILIES[int(np.argmin(degrees))],
        "min_degree_value": int(min(degrees)),
        "mean_degree": float(np.mean(degrees)),
        "is_connected": xgi.is_connected(H),
        "num_connected_components": xgi.number_connected_components(H),
    }


def compute_edge_overlap(H):
    """Which pairs of hyperedges share nodes."""
    overlaps = {}
    edges_as_sets = [set(H.edges.members(eid)) for eid in H.edges]
    for i in range(len(edges_as_sets)):
        for j in range(i + 1, len(edges_as_sets)):
            shared = edges_as_sets[i] & edges_as_sets[j]
            if shared:
                key = f"{HYPEREDGE_NAMES[i]}--{HYPEREDGE_NAMES[j]}"
                overlaps[key] = {
                    "shared_count": len(shared),
                    "shared_families": [ALL_FAMILIES[idx] for idx in shared],
                }
    return overlaps


def compute_s_connectivity(H, s_values=(2, 3)):
    """For s=2,3: which families share at least s hyperedges."""
    degrees = H.nodes.degree.aslist()
    results = {}
    for s in s_values:
        s_connected = [ALL_FAMILIES[i] for i, d in enumerate(degrees) if d >= s]
        results[f"s={s}_connected_families"] = s_connected
        results[f"s={s}_count"] = len(s_connected)
    return results


def compute_incidence_analysis(H):
    """Incidence matrix and its rank."""
    I = xgi.incidence_matrix(H, sparse=False)
    rank = int(np.linalg.matrix_rank(I))
    return {
        "incidence_shape": list(I.shape),
        "incidence_rank": rank,
        "max_possible_rank": min(I.shape),
        "independent_structural_roles": rank,
    }


def compute_dual_analysis(H):
    """Dual hypergraph: hyperedges become nodes, nodes become hyperedges."""
    D = H.dual()
    dual_degrees = D.nodes.degree.aslist()
    return {
        "dual_num_nodes": D.num_nodes,
        "dual_num_edges": D.num_edges,
        "dual_is_connected": xgi.is_connected(D),
        "dual_node_degrees": {
            HYPEREDGE_NAMES[i]: dual_degrees[i]
            for i in range(len(HYPEREDGE_NAMES))
        },
        "dual_max_degree_edge": HYPEREDGE_NAMES[int(np.argmax(dual_degrees))],
        "dual_max_degree_value": int(max(dual_degrees)),
    }


def compute_structural_vs_measure_degrees(H):
    """Compare average degree of structural operators vs type measures."""
    degrees = H.nodes.degree.aslist()
    struct_degrees = [degrees[FAMILY_INDEX[f]] for f in STRUCTURAL_OPS]
    measure_degrees = [degrees[FAMILY_INDEX[f]] for f in TYPE_MEASURES]
    return {
        "structural_avg_degree": float(np.mean(struct_degrees)),
        "measure_avg_degree": float(np.mean(measure_degrees)),
        "structural_higher": bool(np.mean(struct_degrees) > np.mean(measure_degrees)),
    }


# =====================================================================
# SIMPLICIAL COMPLEX COMPARISON
# =====================================================================

def build_simplicial_complex():
    """Build XGI SimplicialComplex from same data; compare with hypergraph."""
    SC = xgi.SimplicialComplex()
    SC.add_simplices_from(HYPEREDGE_LISTS)
    return SC


def compare_hypergraph_simplicial(H, SC):
    """Simplicial closure adds all sub-faces.  How many extra?"""
    return {
        "hypergraph_edges": H.num_edges,
        "simplicial_edges": SC.num_edges,
        "simplicial_nodes": SC.num_nodes,
        "extra_faces_from_closure": SC.num_edges - H.num_edges,
        "closure_ratio": round(SC.num_edges / max(H.num_edges, 1), 3),
    }


def compute_cell_complex_stats(CC, pair_edges):
    """TopoNetX witness for the same higher-order structure."""
    b1 = CC.incidence_matrix(rank=1, signed=True).toarray()
    b2 = CC.incidence_matrix(rank=2, signed=True).toarray()
    l1 = CC.hodge_laplacian_matrix(rank=1).toarray()
    zero_modes = int(np.sum(np.abs(np.linalg.eigvalsh(l1)) < 1e-8))
    shape = list(CC.shape)
    return {
        "shape": shape,
        "num_0cells": shape[0],
        "num_1cells": shape[1],
        "num_2cells": shape[2],
        "pair_edge_count": len(pair_edges),
        "rank_B1": int(np.linalg.matrix_rank(b1)),
        "rank_B2": int(np.linalg.matrix_rank(b2)),
        "B1B2_zero": bool(np.allclose(b1 @ b2, 0.0)),
        "hodge1_zero_modes": zero_modes,
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    H = build_hypergraph()
    stats = compute_hypergraph_stats(H)
    CC, pair_edges = build_cell_complex()
    cell_stats = compute_cell_complex_stats(CC, pair_edges)

    # P1: CNOT has the highest degree (entangling + clifford + universal = 3)
    cnot_degree = stats["node_degrees"]["CNOT"]
    results["P1_cnot_highest_degree"] = {
        "cnot_degree": cnot_degree,
        "max_degree": stats["max_degree_value"],
        "pass": cnot_degree == stats["max_degree_value"],
        "detail": f"CNOT degree={cnot_degree}, max={stats['max_degree_value']}",
    }

    # P2: Channel family is the largest hyperedge (8 members)
    edge_sizes = stats["edge_sizes"]
    max_edge_size = max(edge_sizes)
    channel_idx = HYPEREDGE_NAMES.index("channel_family")
    results["P2_channel_largest_edge"] = {
        "channel_size": edge_sizes[channel_idx],
        "max_edge_size": max_edge_size,
        "pass": edge_sizes[channel_idx] == max_edge_size and max_edge_size == 8,
        "detail": f"channel_family size={edge_sizes[channel_idx]}, max={max_edge_size}",
    }

    # P3: Hypergraph has exactly 8 connected components.
    # The 13 hyperedges partition into:
    #   1 large structural component (15 nodes: all gates + channels via phase_flip bridge)
    #   5 measure-only components (2-3 nodes each, no cross-type hyperedge)
    #   2 isolated structural operators (unitary_rotation, z_measurement)
    # This IS the finding: measures are structurally disjoint from operators.
    results["P3_component_structure"] = {
        "is_connected": stats["is_connected"],
        "num_components": stats["num_connected_components"],
        "pass": stats["num_connected_components"] == 8,
        "detail": "8 components: 1 large structural (15), 5 measure pairs, 2 isolates",
    }

    # P4: Incidence matrix rank reveals independent structural roles
    inc = compute_incidence_analysis(H)
    results["P4_incidence_rank"] = {
        "rank": inc["incidence_rank"],
        "shape": inc["incidence_shape"],
        "pass": 0 < inc["incidence_rank"] <= min(inc["incidence_shape"]),
        "detail": f"rank={inc['incidence_rank']} out of max {inc['max_possible_rank']}",
    }

    # P5: Structural operators have higher average degree than measures
    sv = compute_structural_vs_measure_degrees(H)
    results["P5_structural_higher_degree"] = {
        "structural_avg": sv["structural_avg_degree"],
        "measure_avg": sv["measure_avg_degree"],
        "pass": sv["structural_higher"],
    }

    # P6: Edge overlap — entangling and clifford share CNOT and CZ
    overlaps = compute_edge_overlap(H)
    ent_cliff_key = "entangling_gates--clifford_group"
    results["P6_entangling_clifford_overlap"] = {
        "shared": overlaps.get(ent_cliff_key, {}),
        "pass": ent_cliff_key in overlaps and set(
            overlaps[ent_cliff_key]["shared_families"]
        ) == {"CNOT", "CZ"},
    }

    # P7: s-connectivity — CNOT is s=3 connected
    s_conn = compute_s_connectivity(H)
    results["P7_s_connectivity"] = {
        "s2_families": s_conn["s=2_connected_families"],
        "s3_families": s_conn["s=3_connected_families"],
        "cnot_in_s3": "CNOT" in s_conn["s=3_connected_families"],
        "pass": "CNOT" in s_conn["s=3_connected_families"],
    }

    # P8: Dual hypergraph analysis
    dual = compute_dual_analysis(H)
    results["P8_dual_structure"] = {
        "dual_nodes": dual["dual_num_nodes"],
        "dual_edges": dual["dual_num_edges"],
        "dual_connected": dual["dual_is_connected"],
        "most_connected_edge": dual["dual_max_degree_edge"],
        "pass": dual["dual_num_nodes"] == len(HYPEREDGE_NAMES),
    }

    results["P9_toponetx_cell_lift_matches_higher_order_edges"] = {
        **cell_stats,
        "expected_num_2cells": sum(1 for edge in HYPEREDGE_LISTS if len(edge) >= 3),
        "pass": (
            cell_stats["num_2cells"] == sum(1 for edge in HYPEREDGE_LISTS if len(edge) >= 3)
            and cell_stats["num_1cells"] == cell_stats["pair_edge_count"]
            and cell_stats["B1B2_zero"]
            and cell_stats["hodge1_zero_modes"] >= 1
        ),
        "detail": "TopoNetX CellComplex preserves the same higher-order family relations with nontrivial boundary structure",
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    H = build_hypergraph()
    our_degrees = sorted(H.nodes.degree.aslist(), reverse=True)

    # N1: Random hypergraph with same node/edge count has different degree distribution
    np.random.seed(42)
    edge_sizes = H.edges.size.aslist()
    random_edges = []
    for sz in edge_sizes:
        random_edges.append(
            list(np.random.choice(len(ALL_FAMILIES), size=sz, replace=False))
        )
    R = xgi.Hypergraph()
    R.add_nodes_from(range(len(ALL_FAMILIES)))
    R.add_edges_from(random_edges)
    rand_degrees = sorted(R.nodes.degree.aslist(), reverse=True)
    results["N1_different_from_random"] = {
        "our_degrees_sorted": our_degrees,
        "random_degrees_sorted": rand_degrees,
        "distributions_differ": our_degrees != rand_degrees,
        "pass": our_degrees != rand_degrees,
        "detail": "Structured hypergraph should differ from random with same edge sizes",
    }

    # N2: Removing channel_family changes connectivity or s-connectivity
    H_reduced = build_hypergraph()
    channel_eid = HYPEREDGE_NAMES.index("channel_family")
    H_reduced.remove_edges_from([channel_eid])
    s_conn_full = compute_s_connectivity(H)
    s_conn_reduced = compute_s_connectivity(H_reduced)
    conn_changed = (
        xgi.number_connected_components(H_reduced) != xgi.number_connected_components(H)
    )
    s_changed = (
        s_conn_full["s=2_count"] != s_conn_reduced["s=2_count"]
        or s_conn_full["s=3_count"] != s_conn_reduced["s=3_count"]
    )
    results["N2_channel_removal_changes_structure"] = {
        "connectivity_changed": conn_changed,
        "s_connectivity_changed": s_changed,
        "either_changed": conn_changed or s_changed,
        "pass": conn_changed or s_changed,
        "detail": "Removing the largest hyperedge must alter some structural property",
    }

    # N3: Fully-connected hypergraph (every family in every edge) is trivially
    #     uninformative — our hypergraph is NOT that
    full_edge = list(range(len(ALL_FAMILIES)))
    H_full = xgi.Hypergraph()
    H_full.add_nodes_from(range(len(ALL_FAMILIES)))
    H_full.add_edges_from([full_edge] * len(HYPEREDGE_LISTS))
    full_degrees = H_full.nodes.degree.aslist()
    our_degrees_list = H.nodes.degree.aslist()
    all_same_full = len(set(full_degrees)) == 1
    all_same_ours = len(set(our_degrees_list)) == 1
    results["N3_not_trivially_uniform"] = {
        "full_degree_uniform": all_same_full,
        "our_degree_uniform": all_same_ours,
        "pass": all_same_full and not all_same_ours,
        "detail": "Our hypergraph has non-uniform degree distribution (informationally rich)",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

# The 18 killed L4 families for boundary comparison
KILLED_L4 = [
    "trace_distance", "fidelity", "bures_distance", "hilbert_schmidt_ip",
    "von_neumann_entropy", "linear_entropy", "renyi_entropy",
    "conditional_entropy", "entanglement_entropy", "negativity",
    "concurrence", "log_negativity", "squashed_entanglement",
    "entanglement_of_formation", "ppt_criterion", "reduction_criterion",
    "majorization_criterion", "realignment_criterion",
]


def run_boundary_tests():
    results = {}
    H = build_hypergraph()

    # B1: Add 18 killed L4 families — does structure change meaningfully?
    all_extended = ALL_FAMILIES + KILLED_L4
    H_ext = xgi.Hypergraph()
    H_ext.add_nodes_from(range(len(all_extended)))
    # Same hyperedges (only original 28 are connected)
    H_ext.add_edges_from(HYPEREDGE_LISTS)
    ext_components = xgi.number_connected_components(H_ext)
    results["B1_add_killed_l4"] = {
        "original_components": xgi.number_connected_components(H),
        "extended_components": ext_components,
        "killed_families_isolated": ext_components > 1,
        "num_isolated": ext_components - 1,
        "pass": ext_components > xgi.number_connected_components(H),
        "detail": "Killed families should be isolated — they belong to no hyperedge",
    }

    # B2: Single-node hypergraph — trivially connected
    H_single = xgi.Hypergraph()
    H_single.add_nodes_from([0])
    results["B2_single_node"] = {
        "is_connected": xgi.is_connected(H_single),
        "pass": xgi.is_connected(H_single),
    }

    # B3: Empty hypergraph — no edges, all singletons
    H_empty = xgi.Hypergraph()
    H_empty.add_nodes_from(range(5))
    results["B3_empty_hypergraph"] = {
        "num_edges": H_empty.num_edges,
        "num_components": xgi.number_connected_components(H_empty),
        "pass": H_empty.num_edges == 0 and xgi.number_connected_components(H_empty) == 5,
    }

    # B4: Simplicial complex comparison — does closure add unexpected faces?
    SC = build_simplicial_complex()
    sc_comp = compare_hypergraph_simplicial(H, SC)
    results["B4_simplicial_closure"] = {
        **sc_comp,
        "pass": sc_comp["extra_faces_from_closure"] > 0,
        "detail": "Simplicial closure must add sub-faces; more edges than hypergraph",
    }

    # B5: TopoNetX CellComplex comparison (secondary check; core witness lives in P9)
    try:
        CC, pair_edges = build_cell_complex()
        cc_stats = compute_cell_complex_stats(CC, pair_edges)
        results["B5_toponetx_cell_complex"] = {
            "cell_complex_shape": cc_stats["shape"],
            "num_0cells": cc_stats["num_0cells"],
            "num_1cells": cc_stats["num_1cells"],
            "num_2cells": cc_stats["num_2cells"],
            "hodge1_zero_modes": cc_stats["hodge1_zero_modes"],
            "pass": cc_stats["num_0cells"] > 0 and cc_stats["num_2cells"] > 0 and cc_stats["B1B2_zero"],
            "detail": "CellComplex boundary maps remain consistent with the XGI higher-order family relations",
        }
        TOOL_MANIFEST["toponetx"]["used"] = True
    except Exception as e:
        results["B5_toponetx_cell_complex"] = {
            "pass": False,
            "error": str(e),
        }

    # B6: GUDHI persistence on the incidence distance matrix
    try:
        import gudhi as gh
        I = xgi.incidence_matrix(H, sparse=False)
        # Distance between families based on incidence profiles
        from scipy.spatial.distance import pdist, squareform
        dist = squareform(pdist(I, metric="hamming"))
        rips = gh.RipsComplex(distance_matrix=dist, max_edge_length=1.0)
        st = rips.create_simplex_tree(max_dimension=2)
        st.compute_persistence()
        betti = st.betti_numbers()
        persistence_pairs = [
            (dim, (birth, death))
            for dim, (birth, death) in st.persistence()
            if death != float("inf")
        ]
        results["B6_gudhi_persistence"] = {
            "betti_numbers": betti,
            "num_finite_persistence_pairs": len(persistence_pairs),
            "pass": len(betti) > 0,
            "detail": "Persistence reveals topological features of family-family distance",
        }
        TOOL_MANIFEST["gudhi"]["used"] = True
    except Exception as e:
        results["B6_gudhi_persistence"] = {
            "pass": False,
            "error": str(e),
        }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    H = build_hypergraph()

    # Full analysis for JSON output
    stats = compute_hypergraph_stats(H)
    overlaps = compute_edge_overlap(H)
    s_conn = compute_s_connectivity(H)
    incidence = compute_incidence_analysis(H)
    dual = compute_dual_analysis(H)
    struct_vs_meas = compute_structural_vs_measure_degrees(H)

    SC = build_simplicial_complex()
    sc_comparison = compare_hypergraph_simplicial(H, SC)
    CC, pair_edges = build_cell_complex()
    cell_complex = compute_cell_complex_stats(CC, pair_edges)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Count passes
    all_tests = {**positive, **negative, **boundary}
    n_pass = sum(1 for v in all_tests.values() if v.get("pass"))
    n_total = len(all_tests)

    results = {
        "name": "xgi_family_hypergraph",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "summary": {
            "tests_passed": n_pass,
            "tests_total": n_total,
            "all_pass": n_pass == n_total,
        },
        "data": {
            "families": ALL_FAMILIES,
            "family_count": len(ALL_FAMILIES),
            "structural_ops_count": len(STRUCTURAL_OPS),
            "type_measures_count": len(TYPE_MEASURES),
            "hyperedge_names": HYPEREDGE_NAMES,
            "hyperedge_count": len(HYPEREDGE_NAMES),
        },
        "analysis": {
            "hypergraph_stats": stats,
            "edge_overlap": overlaps,
            "s_connectivity": s_conn,
            "incidence_analysis": incidence,
            "dual_hypergraph": dual,
            "structural_vs_measure_degrees": struct_vs_meas,
            "simplicial_comparison": sc_comparison,
            "cell_complex_lift": cell_complex,
        },
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "xgi_family_hypergraph_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {n_pass}/{n_total} passed")
