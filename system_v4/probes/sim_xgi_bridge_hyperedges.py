#!/usr/bin/env python3
"""
sim_xgi_bridge_hyperedges.py
────────────────────────────
Extends the XGI family hypergraph (sim_xgi_family_hypergraph.py) by adding
bridge hyperedges that connect measure families to structural operator families.
Tests whether the 8-component fragmentation found in the original sim is real
(structural) or an artifact of missing cross-type edges.

Classification: canonical
"""

import json
import os
import numpy as np
from collections import Counter

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
    "xgi":        {"tried": True,  "used": True,  "reason": "primary tool — hypergraph construction, incidence, connectivity analysis"},
    "toponetx":   {"tried": False, "used": False, "reason": "not relevant — bridge analysis is purely hypergraph-level"},
    "gudhi":      {"tried": False, "used": False, "reason": "not relevant — no persistence needed for bridge test"},
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
    "toponetx": None,
    "gudhi": None,
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
# DATA: 28 IRREDUCIBLE FAMILIES (imported from parent sim)
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

# ── Original hyperedges (intra-type only) ─────────────────────────────

ORIGINAL_HYPEREDGE_DEFS = {
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

# ── Bridge hyperedges (cross-type: measure <-> operator) ──────────────

BRIDGE_HYPEREDGE_DEFS = {
    "coherence_sensitive_channels": [
        "z_dephasing", "x_dephasing", "l1_coherence", "relative_entropy_coherence",
    ],
    "phase_space_states": [
        "density_matrix", "purification", "husimi_q", "wigner_negativity",
        "eigenvalue_decomposition",
    ],
    "entanglement_witnesses": [
        "CNOT", "CZ", "iSWAP", "mutual_information", "quantum_discord",
    ],
    "geometric_operators": [
        "Hadamard", "unitary_rotation", "hopf_connection", "chiral_overlap",
    ],
    "measurement_collapse": [
        "z_measurement", "eigenvalue_decomposition", "l1_coherence",
    ],
}

# Merge all hyperedges
ALL_HYPEREDGE_DEFS = {**ORIGINAL_HYPEREDGE_DEFS, **BRIDGE_HYPEREDGE_DEFS}
ORIGINAL_NAMES = list(ORIGINAL_HYPEREDGE_DEFS.keys())
BRIDGE_NAMES = list(BRIDGE_HYPEREDGE_DEFS.keys())
ALL_NAMES = list(ALL_HYPEREDGE_DEFS.keys())

# Convert to index lists
ORIGINAL_EDGES = [
    [FAMILY_INDEX[f] for f in members]
    for members in ORIGINAL_HYPEREDGE_DEFS.values()
]
BRIDGE_EDGES = [
    [FAMILY_INDEX[f] for f in members]
    for members in BRIDGE_HYPEREDGE_DEFS.values()
]
ALL_EDGES = ORIGINAL_EDGES + BRIDGE_EDGES


# =====================================================================
# HYPERGRAPH BUILDERS
# =====================================================================

def build_original_hypergraph():
    """Build the original hypergraph (no bridges)."""
    H = xgi.Hypergraph()
    H.add_nodes_from(range(len(ALL_FAMILIES)))
    H.add_edges_from(ORIGINAL_EDGES)
    return H


def build_bridged_hypergraph():
    """Build the extended hypergraph with bridge edges."""
    H = xgi.Hypergraph()
    H.add_nodes_from(range(len(ALL_FAMILIES)))
    H.add_edges_from(ALL_EDGES)
    return H


def build_complete_hypergraph():
    """Build a single-edge complete hypergraph (all nodes in one edge)."""
    H = xgi.Hypergraph()
    H.add_nodes_from(range(len(ALL_FAMILIES)))
    H.add_edges_from([list(range(len(ALL_FAMILIES)))])
    return H


# =====================================================================
# ANALYSIS HELPERS
# =====================================================================

def get_components(H):
    """Return number of connected components."""
    return xgi.number_connected_components(H)


def get_isolates(H):
    """Return families with degree 0."""
    degrees = H.nodes.degree.aslist()
    return [ALL_FAMILIES[i] for i, d in enumerate(degrees) if d == 0]


def get_incidence_rank(H):
    """Return incidence matrix rank."""
    I = xgi.incidence_matrix(H, sparse=False)
    return int(np.linalg.matrix_rank(I)), I.shape


def get_degree_map(H):
    """Return {family_name: degree} dict."""
    degrees = H.nodes.degree.aslist()
    return {ALL_FAMILIES[i]: degrees[i] for i in range(len(ALL_FAMILIES))}


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    H_orig = build_original_hypergraph()
    H_bridge = build_bridged_hypergraph()

    orig_components = get_components(H_orig)
    bridge_components = get_components(H_bridge)

    # P1: Adding bridges reduces connected components from 8
    results["P1_bridges_reduce_components"] = {
        "original_components": orig_components,
        "bridged_components": bridge_components,
        "reduction": orig_components - bridge_components,
        "pass": bridge_components < orig_components,
        "detail": f"Components: {orig_components} -> {bridge_components} (reduced by {orig_components - bridge_components})",
    }

    # P2: unitary_rotation and z_measurement are no longer isolates
    orig_isolates = get_isolates(H_orig)
    bridge_isolates = get_isolates(H_bridge)
    orig_degrees = get_degree_map(H_orig)
    bridge_degrees = get_degree_map(H_bridge)

    ur_was_isolate = orig_degrees.get("unitary_rotation", 0) == 0
    zm_was_isolate = orig_degrees.get("z_measurement", 0) == 0
    ur_now_connected = bridge_degrees.get("unitary_rotation", 0) > 0
    zm_now_connected = bridge_degrees.get("z_measurement", 0) > 0

    results["P2_isolates_now_connected"] = {
        "unitary_rotation_was_isolate": ur_was_isolate,
        "z_measurement_was_isolate": zm_was_isolate,
        "unitary_rotation_now_degree": bridge_degrees.get("unitary_rotation", 0),
        "z_measurement_now_degree": bridge_degrees.get("z_measurement", 0),
        "original_isolates": orig_isolates,
        "bridged_isolates": bridge_isolates,
        "pass": ur_now_connected and zm_now_connected,
        "detail": "Both former isolates now participate in bridge hyperedges",
    }

    # P3: Incidence matrix rank increases
    orig_rank, orig_shape = get_incidence_rank(H_orig)
    bridge_rank, bridge_shape = get_incidence_rank(H_bridge)

    results["P3_incidence_rank_increases"] = {
        "original_rank": orig_rank,
        "original_shape": list(orig_shape),
        "bridged_rank": bridge_rank,
        "bridged_shape": list(bridge_shape),
        "rank_increase": bridge_rank - orig_rank,
        "pass": bridge_rank > orig_rank,
        "detail": f"Incidence rank: {orig_rank} -> {bridge_rank} (+{bridge_rank - orig_rank})",
    }

    # P4: Each bridge edge contains at least one structural op AND one measure
    bridge_cross_type = {}
    for name, members in BRIDGE_HYPEREDGE_DEFS.items():
        has_structural = any(m in STRUCTURAL_OPS for m in members)
        has_measure = any(m in TYPE_MEASURES for m in members)
        bridge_cross_type[name] = {
            "has_structural": has_structural,
            "has_measure": has_measure,
            "is_cross_type": has_structural and has_measure,
        }
    all_cross = all(v["is_cross_type"] for v in bridge_cross_type.values())
    results["P4_all_bridges_cross_type"] = {
        "bridge_details": bridge_cross_type,
        "all_cross_type": all_cross,
        "pass": all_cross,
        "detail": "Every bridge edge spans the structural/measure boundary",
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    H_orig = build_original_hypergraph()
    orig_components = get_components(H_orig)

    # N1: Random bridge edges do NOT systematically reduce components the same way
    np.random.seed(42)
    n_random_trials = 20
    random_reductions = []
    for trial in range(n_random_trials):
        H_rand = build_original_hypergraph()
        rand_edges = []
        for bridge_members in BRIDGE_EDGES:
            sz = len(bridge_members)
            rand_edge = list(np.random.choice(len(ALL_FAMILIES), size=sz, replace=False))
            rand_edges.append(rand_edge)
        H_rand.add_edges_from(rand_edges)
        rand_components = get_components(H_rand)
        random_reductions.append(orig_components - rand_components)

    H_bridge = build_bridged_hypergraph()
    bridge_components = get_components(H_bridge)
    our_reduction = orig_components - bridge_components

    mean_random_reduction = float(np.mean(random_reductions))
    # Our purposeful bridges should reduce more than random on average
    better_than_random_mean = our_reduction > mean_random_reduction
    # Count how many random trials match or beat our reduction
    random_match_count = sum(1 for r in random_reductions if r >= our_reduction)

    results["N1_random_bridges_less_effective"] = {
        "our_reduction": our_reduction,
        "random_reductions": random_reductions,
        "mean_random_reduction": mean_random_reduction,
        "random_trials_matching_ours": random_match_count,
        "better_than_random_mean": better_than_random_mean,
        "pass": better_than_random_mean,
        "detail": f"Our bridges reduce by {our_reduction}, random avg reduces by {mean_random_reduction:.1f}",
    }

    # N2: Removing any single bridge edge should not restore full 8-component fragmentation
    #     (bridges are redundant enough that no single removal undoes everything)
    single_removal_components = {}
    for i, name in enumerate(BRIDGE_NAMES):
        H_minus = xgi.Hypergraph()
        H_minus.add_nodes_from(range(len(ALL_FAMILIES)))
        edges_minus = ALL_EDGES[:len(ORIGINAL_EDGES) + i] + ALL_EDGES[len(ORIGINAL_EDGES) + i + 1:]
        H_minus.add_edges_from(edges_minus)
        single_removal_components[name] = get_components(H_minus)

    any_restores_8 = any(c == orig_components for c in single_removal_components.values())
    results["N2_no_single_bridge_critical"] = {
        "components_after_removing_each": single_removal_components,
        "any_restores_original": any_restores_8,
        "pass": not any_restores_8,
        "detail": "No single bridge removal restores the original 8-component fragmentation",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    H_bridge = build_bridged_hypergraph()
    bridge_components = get_components(H_bridge)

    # B1: Complete hypergraph trivially gives 1 component; ours is between 1 and 8
    H_complete = build_complete_hypergraph()
    complete_components = get_components(H_complete)

    results["B1_between_complete_and_original"] = {
        "original_components": 8,
        "bridged_components": bridge_components,
        "complete_components": complete_components,
        "strictly_between": 1 <= bridge_components < 8,
        "not_trivially_complete": bridge_components > complete_components or bridge_components == 1,
        "pass": complete_components <= bridge_components < 8,
        "detail": f"Components: complete={complete_components}, bridged={bridge_components}, original=8",
    }

    # B2: Bridge edges only — no original edges — what connectivity do bridges alone give?
    H_bridges_only = xgi.Hypergraph()
    H_bridges_only.add_nodes_from(range(len(ALL_FAMILIES)))
    H_bridges_only.add_edges_from(BRIDGE_EDGES)
    bridges_only_components = get_components(H_bridges_only)
    bridges_only_isolates = get_isolates(H_bridges_only)

    results["B2_bridges_alone_connectivity"] = {
        "bridges_only_components": bridges_only_components,
        "bridges_only_isolates": bridges_only_isolates,
        "num_isolates": len(bridges_only_isolates),
        "pass": bridges_only_components > 1,
        "detail": "Bridges alone should NOT connect everything (they are targeted, not complete)",
    }

    # B3: Degree distribution comparison — bridges should increase measure degrees more
    orig_degrees = get_degree_map(build_original_hypergraph())
    bridge_degrees = get_degree_map(H_bridge)

    struct_increase = np.mean([
        bridge_degrees[f] - orig_degrees[f] for f in STRUCTURAL_OPS
    ])
    measure_increase = np.mean([
        bridge_degrees[f] - orig_degrees[f] for f in TYPE_MEASURES
    ])
    results["B3_measure_degree_boost"] = {
        "structural_avg_degree_increase": float(struct_increase),
        "measure_avg_degree_increase": float(measure_increase),
        "measures_boosted_more": measure_increase >= struct_increase,
        "pass": measure_increase > 0,
        "detail": f"Structural avg increase: {struct_increase:.2f}, Measure avg increase: {measure_increase:.2f}",
    }

    # B4: Edge overlap between original and bridge edges
    H_full = build_bridged_hypergraph()
    edges_as_sets = [set(H_full.edges.members(eid)) for eid in H_full.edges]
    n_orig = len(ORIGINAL_EDGES)
    cross_overlaps = {}
    for i in range(n_orig):
        for j in range(n_orig, len(edges_as_sets)):
            shared = edges_as_sets[i] & edges_as_sets[j]
            if shared:
                key = f"{ORIGINAL_NAMES[i]}--{BRIDGE_NAMES[j - n_orig]}"
                cross_overlaps[key] = {
                    "shared_count": len(shared),
                    "shared_families": [ALL_FAMILIES[idx] for idx in shared],
                }
    results["B4_cross_edge_overlaps"] = {
        "num_cross_overlaps": len(cross_overlaps),
        "overlaps": cross_overlaps,
        "pass": len(cross_overlaps) > 0,
        "detail": "Bridge edges must share nodes with original edges to actually bridge",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    H_orig = build_original_hypergraph()
    H_bridge = build_bridged_hypergraph()

    # Compute comparison stats
    orig_degrees = get_degree_map(H_orig)
    bridge_degrees = get_degree_map(H_bridge)
    orig_rank, orig_shape = get_incidence_rank(H_orig)
    bridge_rank, bridge_shape = get_incidence_rank(H_bridge)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Count passes
    all_tests = {**positive, **negative, **boundary}
    n_pass = sum(1 for v in all_tests.values() if v.get("pass"))
    n_total = len(all_tests)

    results = {
        "name": "xgi_bridge_hyperedges",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "tests_passed": n_pass,
            "tests_total": n_total,
            "all_pass": n_pass == n_total,
        },
        "data": {
            "families": ALL_FAMILIES,
            "family_count": len(ALL_FAMILIES),
            "original_hyperedge_count": len(ORIGINAL_NAMES),
            "bridge_hyperedge_count": len(BRIDGE_NAMES),
            "total_hyperedge_count": len(ALL_NAMES),
            "original_hyperedge_names": ORIGINAL_NAMES,
            "bridge_hyperedge_names": BRIDGE_NAMES,
            "bridge_definitions": {
                name: members
                for name, members in BRIDGE_HYPEREDGE_DEFS.items()
            },
        },
        "comparison": {
            "original_components": get_components(H_orig),
            "bridged_components": get_components(H_bridge),
            "original_incidence_rank": orig_rank,
            "bridged_incidence_rank": bridge_rank,
            "original_isolates": get_isolates(H_orig),
            "bridged_isolates": get_isolates(H_bridge),
            "degree_changes": {
                f: {"original": orig_degrees[f], "bridged": bridge_degrees[f]}
                for f in ALL_FAMILIES
                if bridge_degrees[f] != orig_degrees[f]
            },
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "xgi_bridge_hyperedges_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {n_pass}/{n_total} passed")
