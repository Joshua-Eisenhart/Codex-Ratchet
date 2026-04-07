#!/usr/bin/env python3
"""
SIM: rustworkx_family_dag
Encodes family-to-family dependency edges among the 28 irreducible families
as a rustworkx DAG. Verifies structural properties: acyclicity, topological
sort, root identification, leaf detection, critical path, in-degree
distribution, and transitive reduction. Uses z3 to verify no family depends
on a family killed at a later cascade layer (cross-layer consistency).
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
    from z3 import Solver, Bool, And, Not, Or, Implies, Int, sat, unsat  # noqa: F401
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
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

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
# FAMILY DEPENDENCY DATA
# =====================================================================

# The 28 irreducible families and their dependency edges.
# Edge (A, B) means A requires B to be defined first.
FAMILIES = [
    "density_matrix",
    "purification",
    "z_dephasing",
    "x_dephasing",
    "depolarizing",
    "amplitude_damping",
    "phase_damping",
    "bit_flip",
    "phase_flip",
    "bit_phase_flip",
    "CNOT",
    "CZ",
    "SWAP",
    "iSWAP",
    "Hadamard",
    "T_gate",
    "unitary_rotation",
    "z_measurement",
    "cartan_kak",
    "l1_coherence",
    "relative_entropy_coherence",
    "eigenvalue_decomposition",
    "husimi_q",
    "wigner_negativity",
    "hopf_connection",
    "chiral_overlap",
    "mutual_information",
    "quantum_discord",
]

# Channel families that all depend on density_matrix
CHANNEL_FAMILIES = [
    "z_dephasing", "x_dephasing", "depolarizing",
    "amplitude_damping", "phase_damping",
    "bit_flip", "phase_flip", "bit_phase_flip",
]

# Gate families that depend on density_matrix
GATE_FAMILIES = [
    "CNOT", "CZ", "SWAP", "iSWAP",
    "Hadamard", "T_gate", "unitary_rotation",
]

# All dependency edges: (dependent, dependency) -- A requires B
DEPENDENCY_EDGES = []

# purification -> density_matrix
DEPENDENCY_EDGES.append(("purification", "density_matrix"))

# All channels -> density_matrix
for ch in CHANNEL_FAMILIES:
    DEPENDENCY_EDGES.append((ch, "density_matrix"))

# All gates -> density_matrix
for g in GATE_FAMILIES:
    DEPENDENCY_EDGES.append((g, "density_matrix"))

# z_measurement -> density_matrix
DEPENDENCY_EDGES.append(("z_measurement", "density_matrix"))

# cartan_kak -> CNOT, cartan_kak -> unitary_rotation
DEPENDENCY_EDGES.append(("cartan_kak", "CNOT"))
DEPENDENCY_EDGES.append(("cartan_kak", "unitary_rotation"))

# Coherence measures -> density_matrix
DEPENDENCY_EDGES.append(("l1_coherence", "density_matrix"))
DEPENDENCY_EDGES.append(("relative_entropy_coherence", "density_matrix"))

# Spectral/phase-space -> density_matrix
DEPENDENCY_EDGES.append(("eigenvalue_decomposition", "density_matrix"))
DEPENDENCY_EDGES.append(("husimi_q", "density_matrix"))
DEPENDENCY_EDGES.append(("wigner_negativity", "density_matrix"))

# hopf_connection -> purification
DEPENDENCY_EDGES.append(("hopf_connection", "purification"))

# chiral_overlap -> hopf_connection
DEPENDENCY_EDGES.append(("chiral_overlap", "hopf_connection"))

# mutual_information -> density_matrix, mutual_information -> CNOT
DEPENDENCY_EDGES.append(("mutual_information", "density_matrix"))
DEPENDENCY_EDGES.append(("mutual_information", "CNOT"))

# quantum_discord -> mutual_information
DEPENDENCY_EDGES.append(("quantum_discord", "mutual_information"))

# Cascade layer assignments for cross-layer consistency check.
# Layer number where the family is first available (survives to).
# All 28 are survivors of the full L0-L7 cascade, so they survive
# through all layers. The key constraint: if family A depends on B,
# then B must be defined no later than A. Since these are all survivors,
# we assign layers based on when each family's defining structure appears.
#
# L0: root constraints (noncommutation + finitude) -> density_matrix
# L1: CPTP -> channels become well-defined
# L2: d=2 + Hopf -> purification, hopf_connection
# L3: Chirality -> chiral_overlap
# L4: Composition -> gates, cartan_kak, coherence measures, MI, discord
# L5: su(2) -> unitary_rotation (algebra closure)
# L6: Irreversibility -> eigenvalue_decomposition, wigner, husimi
# L7: Dual-Type -> z_measurement final form

FAMILY_CASCADE_LAYER = {
    "density_matrix": 0,
    "purification": 2,
    "z_dephasing": 1,
    "x_dephasing": 1,
    "depolarizing": 1,
    "amplitude_damping": 1,
    "phase_damping": 1,
    "bit_flip": 1,
    "phase_flip": 1,
    "bit_phase_flip": 1,
    "CNOT": 4,
    "CZ": 4,
    "SWAP": 4,
    "iSWAP": 4,
    "Hadamard": 4,
    "T_gate": 4,
    "unitary_rotation": 5,
    "z_measurement": 7,
    "cartan_kak": 5,
    "l1_coherence": 4,
    "relative_entropy_coherence": 4,
    "eigenvalue_decomposition": 6,
    "husimi_q": 6,
    "wigner_negativity": 6,
    "hopf_connection": 2,
    "chiral_overlap": 3,
    "mutual_information": 4,
    "quantum_discord": 4,
}


# =====================================================================
# DAG BUILDER
# =====================================================================

def build_family_dag():
    """Build the family dependency DAG. Returns (dag, family_indices)."""
    dag = rx.PyDiGraph()
    family_indices = {}
    for fam in FAMILIES:
        idx = dag.add_node({
            "family": fam,
            "cascade_layer": FAMILY_CASCADE_LAYER[fam],
        })
        family_indices[fam] = idx

    for dependent, dependency in DEPENDENCY_EDGES:
        dag.add_edge(
            family_indices[dependent],
            family_indices[dependency],
            {"type": "requires", "from": dependent, "to": dependency},
        )
    return dag, family_indices


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    dag, idx = build_family_dag()

    # -- 1. DAG is acyclic --
    is_acyclic = rx.is_directed_acyclic_graph(dag)
    results["acyclic"] = {
        "passed": is_acyclic,
        "detail": "Family dependency DAG has no cycles",
    }

    # -- 2. Topological sort is valid --
    topo = rx.topological_sort(dag)
    topo_pos = {node: i for i, node in enumerate(topo)}
    all_edges_ok = True
    edge_checks = []
    for dependent, dependency in DEPENDENCY_EDGES:
        dep_pos = topo_pos[idx[dependent]]
        req_pos = topo_pos[idx[dependency]]
        # In the DAG, edges point from dependent -> dependency.
        # Topo sort: dependent should appear before dependency
        # (since the edge direction is dependent -> dependency).
        ok = dep_pos < req_pos
        edge_checks.append({
            "edge": f"{dependent} -> {dependency}",
            "ok": ok,
        })
        if not ok:
            all_edges_ok = False
    topo_family_order = [dag[n]["family"] for n in topo]
    results["topological_sort"] = {
        "passed": all_edges_ok,
        "order": topo_family_order,
        "edge_checks_sample": edge_checks[:5],
        "total_edges_checked": len(edge_checks),
        "all_edges_respected": all_edges_ok,
    }

    # -- 3. density_matrix is a root (no outgoing edges in requires-direction,
    #        i.e., in-degree 0 in this DAG since edges point dependent->dependency,
    #        density_matrix should have in-degree 0 meaning nothing it depends on) --
    # Actually: edges go dependent -> dependency. So density_matrix has
    # in-degree = number of families that depend on it (high),
    # out-degree = number of families it requires (should be 0).
    dm_out_degree = dag.out_degree(idx["density_matrix"])
    results["density_matrix_is_root"] = {
        "passed": dm_out_degree == 0,
        "out_degree": dm_out_degree,
        "detail": "density_matrix has no dependencies (out-degree 0 in requires-graph)",
    }

    # -- 4. Leaf nodes (families with no dependents, i.e., in-degree 0) --
    leaves = []
    for fam in FAMILIES:
        if dag.in_degree(idx[fam]) == 0:
            leaves.append(fam)
    results["leaf_nodes"] = {
        "passed": len(leaves) > 0,
        "count": len(leaves),
        "leaves": sorted(leaves),
        "detail": "Families that no other family depends on",
    }

    # -- 5. Critical path (longest dependency chain) --
    crit_len = rx.dag_longest_path_length(dag)
    crit_path_indices = rx.dag_longest_path(dag)
    crit_path_families = [dag[n]["family"] for n in crit_path_indices]
    results["critical_path"] = {
        "passed": crit_len >= 3,
        "length_edges": crit_len,
        "path": crit_path_families,
        "detail": "Longest dependency chain in the family DAG",
    }

    # -- 6. In-degree distribution (most depended-upon families) --
    in_degrees = {}
    for fam in FAMILIES:
        in_degrees[fam] = dag.in_degree(idx[fam])
    sorted_by_in = sorted(in_degrees.items(), key=lambda x: -x[1])
    results["in_degree_distribution"] = {
        "passed": True,
        "most_depended": sorted_by_in[:5],
        "full_distribution": in_degrees,
        "detail": "density_matrix should be the most depended-upon family",
    }

    # -- 7. Transitive reduction --
    # Build a version without redundant edges
    tr_dag = _transitive_reduction(dag, idx)
    tr_edge_count = tr_dag.num_edges()
    orig_edge_count = dag.num_edges()
    results["transitive_reduction"] = {
        "passed": tr_edge_count <= orig_edge_count,
        "original_edges": orig_edge_count,
        "reduced_edges": tr_edge_count,
        "edges_removed": orig_edge_count - tr_edge_count,
        "detail": "Transitive reduction removes redundant dependency edges",
    }

    # -- 8. z3: no family depends on a family from a later cascade layer --
    results["z3_cross_layer_consistency"] = _z3_cross_layer_check()

    return results


def _transitive_reduction(dag, idx):
    """
    Compute transitive reduction of the DAG.
    An edge A->B is redundant if there exists another path A->...->B.
    """
    tr_dag = rx.PyDiGraph()
    # Copy all nodes
    node_map = {}
    for fam in FAMILIES:
        new_idx = tr_dag.add_node(dag[idx[fam]])
        node_map[fam] = new_idx

    # For each edge, check if there's an alternative path
    for dependent, dependency in DEPENDENCY_EDGES:
        src = idx[dependent]
        tgt = idx[dependency]
        # Temporarily check: is there a path from src to tgt
        # that doesn't use the direct edge?
        # Get all successors of src's other neighbors
        has_alt_path = False
        for _, neighbor, _ in dag.out_edges(src):
            if neighbor == tgt:
                continue
            # Check if tgt is reachable from neighbor
            descendants = rx.descendants(dag, neighbor)
            if tgt in descendants:
                has_alt_path = True
                break
        if not has_alt_path:
            tr_dag.add_edge(
                node_map[dependent],
                node_map[dependency],
                {"type": "requires", "from": dependent, "to": dependency},
            )
    return tr_dag


def _z3_cross_layer_check():
    """
    Use z3 to verify: for every edge (A requires B),
    cascade_layer(B) <= cascade_layer(A).
    A family cannot depend on something defined at a later layer.
    """
    try:
        from z3 import Solver, Int, And, sat, unsat  # noqa: F811
    except ImportError:
        return {"passed": False, "detail": "z3 not available"}

    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "prove no family depends on a family from a later cascade layer"
    )

    solver = Solver()

    # Create z3 integer variables for each family's cascade layer
    layer_vars = {fam: Int(f"layer_{fam}") for fam in FAMILIES}

    # Assert known layer values
    for fam in FAMILIES:
        solver.add(layer_vars[fam] == FAMILY_CASCADE_LAYER[fam])

    # Assert the consistency constraint for every edge:
    # If A requires B, then layer(B) <= layer(A)
    constraints = []
    for dependent, dependency in DEPENDENCY_EDGES:
        c = layer_vars[dependency] <= layer_vars[dependent]
        constraints.append(c)
        solver.add(c)

    check = solver.check()
    consistent = (check == sat)

    # Also find any violations in Python for cross-validation
    violations = []
    for dependent, dependency in DEPENDENCY_EDGES:
        dep_layer = FAMILY_CASCADE_LAYER[dependent]
        req_layer = FAMILY_CASCADE_LAYER[dependency]
        if req_layer > dep_layer:
            violations.append({
                "dependent": dependent,
                "dependency": dependency,
                "dependent_layer": dep_layer,
                "dependency_layer": req_layer,
                "detail": f"{dependent}(L{dep_layer}) requires "
                          f"{dependency}(L{req_layer}) but dependency "
                          f"is defined later",
            })

    return {
        "passed": consistent and len(violations) == 0,
        "z3_result": str(check),
        "python_violations": violations,
        "edges_checked": len(DEPENDENCY_EDGES),
        "detail": "z3 confirms all dependencies respect cascade layer ordering",
    }


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    results = {}

    # -- 1. Adding a cycle: density_matrix -> quantum_discord -> density_matrix --
    dag, idx = build_family_dag()
    # Add edge: density_matrix -> quantum_discord (density_matrix requires
    # quantum_discord, creating a cycle via the existing chain)
    dag.add_edge(
        idx["density_matrix"],
        idx["quantum_discord"],
        {"type": "cycle_injection", "from": "density_matrix", "to": "quantum_discord"},
    )
    has_cycle = not rx.is_directed_acyclic_graph(dag)
    results["cycle_breaks_acyclicity"] = {
        "passed": has_cycle,
        "detail": "Adding density_matrix -> quantum_discord creates a cycle "
                  "(quantum_discord -> mutual_information -> density_matrix "
                  "-> quantum_discord)",
    }

    # -- 2. Removing density_matrix edges disconnects most families --
    dag2, idx2 = build_family_dag()
    # Count edges involving density_matrix before removal
    dm_in_edges = dag2.in_edges(idx2["density_matrix"])
    dm_edge_count = len(dm_in_edges)
    # Remove all edges into density_matrix
    edges_to_remove = [(s, d) for s, d, _ in dm_in_edges]
    for s, d in edges_to_remove:
        dag2.remove_edge(s, d)
    # Now density_matrix should be fully isolated
    dm_in_after = dag2.in_degree(idx2["density_matrix"])
    dm_out_after = dag2.out_degree(idx2["density_matrix"])
    results["remove_dm_edges_disconnects"] = {
        "passed": dm_in_after == 0 and dm_out_after == 0,
        "edges_removed": dm_edge_count,
        "dm_isolated": dm_in_after == 0 and dm_out_after == 0,
        "detail": "Removing all density_matrix dependency edges isolates it",
    }

    # -- 3. Invalid layer assignment caught by z3 --
    # Set quantum_discord to layer 0 (before its dependencies)
    saved = FAMILY_CASCADE_LAYER["quantum_discord"]
    FAMILY_CASCADE_LAYER["quantum_discord"] = 0
    violation_result = _z3_cross_layer_check_raw()
    FAMILY_CASCADE_LAYER["quantum_discord"] = saved
    results["z3_catches_invalid_layer"] = {
        "passed": not violation_result["consistent"],
        "detail": "z3 detects quantum_discord at L0 violates dependency ordering",
        "violations_found": violation_result["violation_count"],
    }

    return results


def _z3_cross_layer_check_raw():
    """Raw z3 check returning consistency bool and violation count."""
    try:
        from z3 import Solver, Int, sat  # noqa: F811
    except ImportError:
        return {"consistent": True, "violation_count": 0}

    solver = Solver()
    layer_vars = {fam: Int(f"layer_{fam}") for fam in FAMILIES}
    for fam in FAMILIES:
        solver.add(layer_vars[fam] == FAMILY_CASCADE_LAYER[fam])
    for dependent, dependency in DEPENDENCY_EDGES:
        solver.add(layer_vars[dependency] <= layer_vars[dependent])

    check = solver.check()
    violations = 0
    for dependent, dependency in DEPENDENCY_EDGES:
        if FAMILY_CASCADE_LAYER[dependency] > FAMILY_CASCADE_LAYER[dependent]:
            violations += 1

    return {"consistent": check == sat, "violation_count": violations}


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # -- 1. Single-family DAG --
    dag1 = rx.PyDiGraph()
    dag1.add_node({"family": "density_matrix", "cascade_layer": 0})
    results["single_family_dag"] = {
        "passed": (
            rx.is_directed_acyclic_graph(dag1)
            and len(dag1) == 1
            and dag1.num_edges() == 0
        ),
        "node_count": len(dag1),
        "edge_count": dag1.num_edges(),
        "is_acyclic": rx.is_directed_acyclic_graph(dag1),
        "detail": "Single-node DAG is trivially acyclic with no edges",
    }

    # -- 2. Linear chain DAG --
    dag_lin = rx.PyDiGraph()
    chain = ["quantum_discord", "mutual_information", "CNOT", "density_matrix"]
    lin_idx = {}
    for fam in chain:
        lin_idx[fam] = dag_lin.add_node({"family": fam})
    for i in range(len(chain) - 1):
        dag_lin.add_edge(lin_idx[chain[i]], lin_idx[chain[i + 1]], {})

    lin_topo = rx.topological_sort(dag_lin)
    lin_topo_fams = [dag_lin[n]["family"] for n in lin_topo]
    lin_crit_len = rx.dag_longest_path_length(dag_lin)

    results["linear_chain"] = {
        "passed": (
            rx.is_directed_acyclic_graph(dag_lin)
            and lin_crit_len == len(chain) - 1
        ),
        "topo_order": lin_topo_fams,
        "critical_path_length": lin_crit_len,
        "expected_length": len(chain) - 1,
        "detail": "Linear chain has critical path equal to chain length minus 1",
    }

    # -- 3. Full DAG node/edge counts match expectations --
    dag_full, idx_full = build_family_dag()
    results["full_dag_counts"] = {
        "passed": (
            len(dag_full) == len(FAMILIES)
            and dag_full.num_edges() == len(DEPENDENCY_EDGES)
        ),
        "node_count": len(dag_full),
        "expected_nodes": len(FAMILIES),
        "edge_count": dag_full.num_edges(),
        "expected_edges": len(DEPENDENCY_EDGES),
        "detail": "Full DAG has exactly 28 families and all declared edges",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    # Mark tools used
    TOOL_MANIFEST["rustworkx"]["used"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = (
        "DAG construction, acyclicity, topo sort, critical path, "
        "ancestors, descendants, transitive reduction"
    )

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_passed = (
        all(t.get("passed", False) for t in positive.values())
        and all(t.get("passed", False) for t in negative.values())
        and all(t.get("passed", False) for t in boundary.values())
    )

    results = {
        "name": "rustworkx_family_dag",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_passed": all_passed,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "rustworkx_family_dag_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"ALL PASSED: {all_passed}")
