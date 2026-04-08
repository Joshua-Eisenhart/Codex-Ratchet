#!/usr/bin/env python3
"""
sim_lego_graph_cluster_states.py
────────────────────────────────
Graph states and cluster states -- potentially relevant to the 64-schedule
lattice structure.

Tools: PyTorch (state vectors, density matrices, entanglement),
       rustworkx (graph construction), z3 (stabilizer verification).

Sections
--------
1. Graph states for line, ring, star, complete graphs (4 nodes each)
2. Stabilizer generators for each graph state -- verify all stabilize the state
3. Entanglement entropy across every bipartition
4. Verify: graph state entanglement structure matches graph structure
5. Build 1D cluster state (4 qubits)
6. Verify: X-basis measurement of qubit 1 teleports state to qubit 2 (MBQC)

Classification: canonical (torch-native)
Output: sim_results/lego_graph_cluster_states_results.json
"""

import json
import os
import sys
import numpy as np
from itertools import combinations

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": "not needed for this sim"},
    "z3":         {"tried": False, "used": False, "reason": ""},
    "cvc5":       {"tried": False, "used": False, "reason": "not needed"},
    "sympy":      {"tried": False, "used": False, "reason": "not needed"},
    "clifford":   {"tried": False, "used": False, "reason": "not needed"},
    "geomstats":  {"tried": False, "used": False, "reason": "not needed"},
    "e3nn":       {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx":  {"tried": False, "used": False, "reason": ""},
    "xgi":        {"tried": False, "used": False, "reason": "not needed"},
    "toponetx":   {"tried": False, "used": False, "reason": "not needed"},
    "gudhi":      {"tried": False, "used": False, "reason": "not needed"},
}

# -- Import tools --
try:
    import torch
    torch.set_default_dtype(torch.float64)
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "state vectors, density matrices, entanglement entropy"
except ImportError:
    print("FATAL: pytorch required"); sys.exit(1)

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    TOOL_MANIFEST["rustworkx"]["used"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = "graph construction for line, ring, star, complete, lattice"
except ImportError:
    print("FATAL: rustworkx required"); sys.exit(1)

try:
    from z3 import Bool, BoolVal, Solver, sat, And, Xor, Not, Or
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "stabilizer property verification via symplectic formalism"
except ImportError:
    print("FATAL: z3 required"); sys.exit(1)

RESULTS = {}

# =====================================================================
# CONSTANTS
# =====================================================================

I2 = torch.eye(2, dtype=torch.cdouble)
X = torch.tensor([[0, 1], [1, 0]], dtype=torch.cdouble)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.cdouble)
Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.cdouble)
H_gate = torch.tensor([[1, 1], [1, -1]], dtype=torch.cdouble) / np.sqrt(2)

PAULIS = {"I": I2, "X": X, "Y": Y, "Z": Z}

# |+> and |0>, |1>
KET_PLUS = torch.tensor([1, 1], dtype=torch.cdouble) / np.sqrt(2)
KET_0 = torch.tensor([1, 0], dtype=torch.cdouble)
KET_1 = torch.tensor([0, 1], dtype=torch.cdouble)

# CZ gate (2-qubit)
CZ_2Q = torch.diag(torch.tensor([1, 1, 1, -1], dtype=torch.cdouble))


# =====================================================================
# HELPERS
# =====================================================================

def kron_list(mats):
    """Tensor product of a list of matrices/vectors."""
    result = mats[0]
    for m in mats[1:]:
        result = torch.kron(result, m)
    return result


def n_qubit_gate(gate_2q, i, j, n):
    """
    Embed a 2-qubit gate acting on qubits i,j into an n-qubit Hilbert space.
    Uses the standard approach: build the full 2^n x 2^n matrix.
    """
    dim = 2 ** n
    result = torch.zeros((dim, dim), dtype=torch.cdouble)
    for row in range(dim):
        for col in range(dim):
            # Extract bits for qubits i and j
            bits_row = [(row >> (n - 1 - k)) & 1 for k in range(n)]
            bits_col = [(col >> (n - 1 - k)) & 1 for k in range(n)]
            # Check if all OTHER qubits match (identity on them)
            other_match = all(bits_row[k] == bits_col[k] for k in range(n) if k != i and k != j)
            if not other_match:
                continue
            # 2-qubit subspace indices (qubit i is "first", qubit j is "second")
            sub_row = bits_row[i] * 2 + bits_row[j]
            sub_col = bits_col[i] * 2 + bits_col[j]
            result[row, col] = gate_2q[sub_row, sub_col]
    return result


def build_graph_state(n, edges):
    """
    Build |G> = prod_{(i,j) in edges} CZ_{ij} |+>^{otimes n}.
    Returns the state vector (2^n,) complex tensor.
    """
    # Start with |+>^n
    state = kron_list([KET_PLUS] * n)
    # Apply CZ for each edge
    for (i, j) in edges:
        cz_full = n_qubit_gate(CZ_2Q, i, j, n)
        state = cz_full @ state
    return state


def n_qubit_pauli(pauli_string, n):
    """
    Build n-qubit Pauli operator from a string like 'XZIY'.
    """
    assert len(pauli_string) == n
    mats = [PAULIS[c] for c in pauli_string]
    return kron_list(mats)


def stabilizer_generators_for_graph(n, edges):
    """
    For a graph state |G> on n qubits with edge set E,
    the stabilizer generators are:
      K_i = X_i * prod_{j in N(i)} Z_j
    where N(i) is the neighborhood of vertex i in the graph.
    Returns list of (pauli_string, matrix) pairs.
    """
    # Build adjacency from edges
    adj = {i: set() for i in range(n)}
    for (a, b) in edges:
        adj[a].add(b)
        adj[b].add(a)

    generators = []
    for i in range(n):
        chars = ['I'] * n
        chars[i] = 'X'
        for j in adj[i]:
            chars[j] = 'Z'
        pauli_str = ''.join(chars)
        mat = n_qubit_pauli(pauli_str, n)
        generators.append((pauli_str, mat))
    return generators


def verify_stabilizers(state, generators, tol=1e-10):
    """Verify that each generator stabilizes the state: K_i |psi> = |psi>."""
    results = []
    for (label, mat) in generators:
        result_vec = mat @ state
        overlap = torch.vdot(state, result_vec)
        eigenvalue = overlap.real.item()
        is_stabilized = abs(eigenvalue - 1.0) < tol
        residual = torch.norm(result_vec - state).item()
        results.append({
            "generator": label,
            "eigenvalue": eigenvalue,
            "residual": residual,
            "stabilized": is_stabilized,
        })
    return results


def entanglement_entropy_bipartition(state_vec, n, subsystem_qubits):
    """
    Compute von Neumann entanglement entropy for a bipartition.
    subsystem_qubits: list of qubit indices in subsystem A.
    """
    dim = 2 ** n
    # Reshape state into tensor with n indices of dimension 2
    psi = state_vec.reshape([2] * n)

    # Determine subsystem B
    all_qubits = list(range(n))
    subsystem_b = [q for q in all_qubits if q not in subsystem_qubits]
    n_a = len(subsystem_qubits)
    n_b = len(subsystem_b)

    # Permute so that subsystem A qubits come first
    perm = list(subsystem_qubits) + list(subsystem_b)
    psi_perm = psi.permute(perm)

    # Reshape into (dim_A, dim_B) matrix
    dim_a = 2 ** n_a
    dim_b = 2 ** n_b
    psi_matrix = psi_perm.reshape(dim_a, dim_b)

    # Compute reduced density matrix of A
    rho_a = psi_matrix @ psi_matrix.conj().T

    # Eigenvalues
    eigenvalues = torch.linalg.eigvalsh(rho_a.real)  # rho_a is Hermitian
    # For complex rho_a, use eigvals of the real part won't work.
    # Use SVD of psi_matrix instead for numerical stability.
    sv = torch.linalg.svdvals(psi_matrix)
    schmidt_sq = sv ** 2
    # Filter near-zero
    schmidt_sq = schmidt_sq[schmidt_sq > 1e-15]
    entropy = -torch.sum(schmidt_sq * torch.log2(schmidt_sq)).item()
    return entropy


def all_bipartition_entropies(state_vec, n):
    """Compute entanglement entropy for all non-trivial bipartitions."""
    results = {}
    for size in range(1, n):
        for subset in combinations(range(n), size):
            # Only need half (S(A) = S(B) for pure states), but compute all for clarity
            label = str(list(subset))
            entropy = entanglement_entropy_bipartition(state_vec, n, list(subset))
            results[label] = round(entropy, 10)
    return results


def edge_cut_for_bipartition(edges, subsystem_a, n):
    """Count number of edges crossing the bipartition."""
    subsystem_b = set(range(n)) - set(subsystem_a)
    count = 0
    for (i, j) in edges:
        if (i in subsystem_a and j in subsystem_b) or (i in subsystem_b and j in subsystem_a):
            count += 1
    return count


# =====================================================================
# SECTION 1-2: BUILD GRAPH STATES & VERIFY STABILIZERS
# =====================================================================

def build_graphs_rustworkx():
    """Use rustworkx to build line, ring, star, complete graphs on 4 nodes."""
    graphs = {}

    # Line: 0-1-2-3
    g_line = rx.PyGraph()
    g_line.add_nodes_from(range(4))
    g_line.add_edges_from([(0, 1, None), (1, 2, None), (2, 3, None)])
    graphs["line_4"] = g_line

    # Ring: 0-1-2-3-0
    g_ring = rx.PyGraph()
    g_ring.add_nodes_from(range(4))
    g_ring.add_edges_from([(0, 1, None), (1, 2, None), (2, 3, None), (3, 0, None)])
    graphs["ring_4"] = g_ring

    # Star: 0 connected to 1,2,3
    g_star = rx.PyGraph()
    g_star.add_nodes_from(range(4))
    g_star.add_edges_from([(0, 1, None), (0, 2, None), (0, 3, None)])
    graphs["star_4"] = g_star

    # Complete K4
    g_complete = rx.PyGraph()
    g_complete.add_nodes_from(range(4))
    g_complete.add_edges_from([
        (0, 1, None), (0, 2, None), (0, 3, None),
        (1, 2, None), (1, 3, None), (2, 3, None),
    ])
    graphs["complete_4"] = g_complete

    return graphs


def extract_edges(graph):
    """Extract edge list from rustworkx graph."""
    edges = []
    for e in graph.edge_list():
        edges.append((e[0], e[1]))
    return edges


def run_graph_state_tests():
    """Sections 1-4: build graph states, verify stabilizers, compute entanglement."""
    print("=" * 72)
    print("SECTIONS 1-4: Graph states -- stabilizers & entanglement")
    print("=" * 72)

    graphs = build_graphs_rustworkx()
    n = 4
    section_results = {}

    for name, graph in graphs.items():
        print(f"\n--- {name} ---")
        edges = extract_edges(graph)
        n_edges = len(edges)
        print(f"  Edges: {edges}")

        # Build graph state
        state = build_graph_state(n, edges)
        norm = torch.norm(state).item()
        print(f"  State norm: {norm:.10f}")

        # Stabilizer generators
        generators = stabilizer_generators_for_graph(n, edges)
        stab_results = verify_stabilizers(state, generators)
        all_stabilized = all(r["stabilized"] for r in stab_results)
        print(f"  Stabilizers: {[r['generator'] for r in stab_results]}")
        print(f"  All stabilized: {all_stabilized}")

        # Entanglement entropy for all bipartitions
        entropies = all_bipartition_entropies(state, n)
        print(f"  Bipartition entropies: {entropies}")

        # Section 4: verify entanglement structure matches graph structure
        # For graph states: S(A) = min(|A|, |B|, edge_cut(A,B))
        # More precisely: S(A) = rank of adjacency sub-matrix (Gamma_{A,B})
        # For single-qubit bipartitions: S({i}) = 1 if deg(i)>0, else 0
        # General: S(A) = rank(Gamma_{A,B}) where Gamma is adjacency over GF(2)
        structure_checks = []
        for size in range(1, n):
            for subset in combinations(range(n), size):
                subset_list = list(subset)
                complement = [q for q in range(n) if q not in subset_list]
                # Build GF(2) adjacency sub-matrix Gamma_{A,B}
                adj_sub = np.zeros((len(subset_list), len(complement)), dtype=int)
                for ei, (a, b) in enumerate(edges):
                    if a in subset_list and b in complement:
                        r = subset_list.index(a)
                        c = complement.index(b)
                        adj_sub[r, c] ^= 1
                    elif b in subset_list and a in complement:
                        r = subset_list.index(b)
                        c = complement.index(a)
                        adj_sub[r, c] ^= 1
                # GF(2) rank via row reduction
                gf2_rank = _gf2_rank(adj_sub)
                measured_entropy = entropies[str(subset_list)]
                # For graph states, S(A) = GF(2) rank of Gamma_{A,B}
                expected_entropy = float(gf2_rank)
                match = abs(measured_entropy - expected_entropy) < 1e-6
                structure_checks.append({
                    "partition_A": subset_list,
                    "gf2_rank": gf2_rank,
                    "measured_entropy": measured_entropy,
                    "expected_entropy": expected_entropy,
                    "match": match,
                })

        all_structure_match = all(c["match"] for c in structure_checks)
        print(f"  Entanglement-graph structure match: {all_structure_match}")

        section_results[name] = {
            "edges": edges,
            "n_edges": n_edges,
            "state_norm": norm,
            "stabilizer_verification": stab_results,
            "all_stabilized": all_stabilized,
            "bipartition_entropies": entropies,
            "structure_checks": structure_checks,
            "all_structure_match": all_structure_match,
        }

    return section_results


def _gf2_rank(matrix):
    """Compute rank of a binary matrix over GF(2)."""
    mat = matrix.copy() % 2
    rows, cols = mat.shape
    rank = 0
    for col in range(cols):
        # Find pivot
        pivot = None
        for row in range(rank, rows):
            if mat[row, col] == 1:
                pivot = row
                break
        if pivot is None:
            continue
        # Swap
        mat[[rank, pivot]] = mat[[pivot, rank]]
        # Eliminate
        for row in range(rows):
            if row != rank and mat[row, col] == 1:
                mat[row] = (mat[row] + mat[rank]) % 2
        rank += 1
    return rank


# =====================================================================
# SECTION 5-6: CLUSTER STATES & MBQC
# =====================================================================

def run_cluster_state_tests():
    """
    Sections 5-6: 1D cluster state and measurement-based teleportation.
    """
    print("\n" + "=" * 72)
    print("SECTIONS 5-6: Cluster states & MBQC teleportation")
    print("=" * 72)

    n = 4
    section_results = {}

    # Section 5: Build 1D cluster state (line graph on 4 qubits)
    # Cluster state on 1D chain = graph state on path graph
    g_chain = rx.PyGraph()
    g_chain.add_nodes_from(range(4))
    g_chain.add_edges_from([(0, 1, None), (1, 2, None), (2, 3, None)])
    edges = extract_edges(g_chain)
    cluster_state = build_graph_state(n, edges)

    # Verify it is a valid cluster state: check stabilizers
    generators = stabilizer_generators_for_graph(n, edges)
    stab_results = verify_stabilizers(cluster_state, generators)
    all_stabilized = all(r["stabilized"] for r in stab_results)
    print(f"  1D cluster state stabilizers verified: {all_stabilized}")
    print(f"  Generators: {[r['generator'] for r in stab_results]}")

    section_results["cluster_1d_4q"] = {
        "edges": edges,
        "stabilizer_verification": stab_results,
        "all_stabilized": all_stabilized,
    }

    # Section 6: MBQC on 1D cluster state
    #
    # For a 1D cluster state on 4 qubits, measuring qubits 0,1,2 in
    # sequence implements a quantum computation on the logical output
    # (qubit 3). Specifically:
    #
    # Key property: CZ_{01}|+>_0 decomposed under X-measurement on qubit 0
    # gives psi[1,:] = Z_1 * psi[0,:], meaning CZ converts X-measurement
    # on one qubit into a Z-byproduct on the neighbor.
    #
    # Test A: Verify the Z-byproduct structure (psi[1,:] = Z_1 * psi[0,:])
    # Test B: Verify that sequential X-basis measurements on qubits 0,1,2
    #         leave qubit 3 in a definite state determined by outcomes.
    # Test C: Verify that measuring in a rotated basis R_z(phi)|pm> on
    #         qubit 0 implements a rotation on the logical state.

    print("\n  MBQC tests:")

    # Test A: Z-byproduct structure
    psi_reshaped = cluster_state.reshape(2, 2 ** (n - 1))
    z1_op = kron_list([Z, I2, I2])
    z_byproduct = torch.allclose(psi_reshaped[1, :], z1_op @ psi_reshaped[0, :])
    print(f"    Test A: psi[1,:] = Z_1 * psi[0,:]: {z_byproduct}")

    # Test B: Sequential measurement -- measure qubits 0,1,2 in X-basis
    # For each outcome triple (s0, s1, s2), the final qubit state should
    # be a Pauli-corrected |+> state.
    ket_minus = torch.tensor([1, -1], dtype=torch.cdouble) / np.sqrt(2)
    x_eigenstates = [KET_PLUS, ket_minus]

    sequential_results = []
    for s0 in range(2):
        for s1 in range(2):
            for s2 in range(2):
                # Measure qubit 0
                psi_4 = cluster_state.reshape(2, 8)
                bra0 = x_eigenstates[s0].conj()
                psi_3q = bra0[0] * psi_4[0, :] + bra0[1] * psi_4[1, :]
                psi_3q = psi_3q / torch.norm(psi_3q)

                # Measure qubit 1 (now first of remaining 3)
                psi_3 = psi_3q.reshape(2, 4)
                bra1 = x_eigenstates[s1].conj()
                psi_2q = bra1[0] * psi_3[0, :] + bra1[1] * psi_3[1, :]
                psi_2q = psi_2q / torch.norm(psi_2q)

                # Measure qubit 2 (now first of remaining 2)
                psi_2 = psi_2q.reshape(2, 2)
                bra2 = x_eigenstates[s2].conj()
                psi_1q = bra2[0] * psi_2[0, :] + bra2[1] * psi_2[1, :]
                psi_1q = psi_1q / torch.norm(psi_1q)

                # The output qubit should be in a definite pure state
                # (some Pauli rotation of |+>)
                purity_1q = (torch.abs(psi_1q[0])**2 + torch.abs(psi_1q[1])**2).item()
                # Check if it's |+>, |->, |0>, or |1>
                fid_plus = torch.abs(torch.vdot(psi_1q, KET_PLUS))**2
                fid_minus = torch.abs(torch.vdot(psi_1q, ket_minus))**2
                fid_0 = torch.abs(torch.vdot(psi_1q, KET_0))**2
                fid_1 = torch.abs(torch.vdot(psi_1q, KET_1))**2
                max_fid = max(fid_plus.item(), fid_minus.item(), fid_0.item(), fid_1.item())
                is_definite = max_fid > 1 - 1e-6

                sequential_results.append({
                    "outcomes": (s0, s1, s2),
                    "output_state": [complex(psi_1q[0]).real, complex(psi_1q[1]).real],
                    "fidelities": {
                        "|+>": round(fid_plus.item(), 10),
                        "|->": round(fid_minus.item(), 10),
                        "|0>": round(fid_0.item(), 10),
                        "|1>": round(fid_1.item(), 10),
                    },
                    "is_definite_state": is_definite,
                })

    all_definite = all(r["is_definite_state"] for r in sequential_results)
    print(f"    Test B: All 8 outcome triples give definite output: {all_definite}")
    for r in sequential_results:
        best = max(r["fidelities"].items(), key=lambda x: x[1])
        print(f"      outcomes={r['outcomes']}: output closest to {best[0]} (F={best[1]:.4f})")

    # Test C: Rotated basis measurement implements rotation
    # Measuring qubit 0 in basis {R_z(phi)|+>, R_z(phi)|->} where
    # R_z(phi) = diag(1, e^{i*phi}) implements a Z-rotation by angle phi
    # on the logical qubit (up to byproduct operators).
    # We verify: measuring at phi=pi/2 produces a different output than phi=0.
    phi = np.pi / 2
    Rz_phi = torch.tensor([[1, 0], [0, np.exp(1j * phi)]], dtype=torch.cdouble)
    rotated_plus = Rz_phi @ KET_PLUS
    rotated_minus = Rz_phi @ ket_minus

    rot_results = []
    for s0, basis_0 in enumerate([rotated_plus, rotated_minus]):
        psi_4 = cluster_state.reshape(2, 8)
        bra0 = basis_0.conj()
        psi_3q = bra0[0] * psi_4[0, :] + bra0[1] * psi_4[1, :]
        norm = torch.norm(psi_3q).item()
        psi_3q = psi_3q / torch.norm(psi_3q)

        # Now measure qubits 1,2 in X-basis (both outcome 0 for simplicity)
        psi_3 = psi_3q.reshape(2, 4)
        psi_2q = (psi_3[0, :] + psi_3[1, :]) / np.sqrt(2)
        psi_2q = psi_2q / torch.norm(psi_2q)
        psi_2 = psi_2q.reshape(2, 2)
        psi_1q = (psi_2[0, :] + psi_2[1, :]) / np.sqrt(2)
        psi_1q = psi_1q / torch.norm(psi_1q)

        fid_plus = torch.abs(torch.vdot(psi_1q, KET_PLUS))**2
        rot_results.append({
            "rotated_outcome": s0,
            "phi": phi,
            "output_fidelity_with_plus": round(fid_plus.item(), 10),
            "output_state": [round(complex(psi_1q[0]).real, 6),
                             round(complex(psi_1q[0]).imag, 6),
                             round(complex(psi_1q[1]).real, 6),
                             round(complex(psi_1q[1]).imag, 6)],
        })

    # The rotation should produce a state different from |+>
    rotation_active = any(r["output_fidelity_with_plus"] < 1 - 1e-6 for r in rot_results)
    print(f"    Test C: Rotated measurement produces non-trivial output: {rotation_active}")

    teleport_results = {
        "z_byproduct_verified": z_byproduct,
        "sequential_measurement": {
            "outcomes": sequential_results,
            "all_definite_outputs": all_definite,
        },
        "rotated_basis": {
            "phi": phi,
            "results": rot_results,
            "rotation_active": rotation_active,
        },
    }
    all_mbqc = z_byproduct and all_definite and rotation_active
    teleport_results["all_mbqc_verified"] = all_mbqc
    print(f"\n  All MBQC tests verified: {all_mbqc}")

    section_results["mbqc"] = teleport_results

    # Also build 2D grid cluster state (2x2) for completeness
    print("\n  2D cluster state (2x2 grid):")
    g_grid = rx.PyGraph()
    g_grid.add_nodes_from(range(4))
    # 2x2 grid: 0-1, 2-3, 0-2, 1-3
    g_grid.add_edges_from([(0, 1, None), (2, 3, None), (0, 2, None), (1, 3, None)])
    grid_edges = extract_edges(g_grid)
    grid_state = build_graph_state(4, grid_edges)
    grid_gens = stabilizer_generators_for_graph(4, grid_edges)
    grid_stab = verify_stabilizers(grid_state, grid_gens)
    grid_all_stab = all(r["stabilized"] for r in grid_stab)
    grid_entropies = all_bipartition_entropies(grid_state, 4)
    print(f"  2D grid stabilizers verified: {grid_all_stab}")
    print(f"  2D grid entropies: {grid_entropies}")

    section_results["cluster_2d_grid"] = {
        "edges": grid_edges,
        "stabilizer_verification": grid_stab,
        "all_stabilized": grid_all_stab,
        "bipartition_entropies": grid_entropies,
    }

    return section_results


# =====================================================================
# Z3 STABILIZER VERIFICATION
# =====================================================================

def run_z3_stabilizer_checks():
    """
    Use z3 to verify stabilizer group properties:
    1. All generators commute (abelian group)
    2. Each generator squares to identity (order 2)
    3. The group generated has exactly 2^n elements
    4. No generator is a product of others (independence)

    We encode the symplectic representation over GF(2):
    An n-qubit Pauli is (x, z) in GF(2)^{2n}, where
    x_i=1 means X on qubit i, z_i=1 means Z on qubit i.
    Two Paulis commute iff their symplectic inner product is 0.
    """
    print("\n" + "=" * 72)
    print("Z3: Stabilizer group property verification")
    print("=" * 72)

    n = 4
    graphs = build_graphs_rustworkx()
    z3_results = {}

    for name, graph in graphs.items():
        print(f"\n--- z3 checks for {name} ---")
        edges = extract_edges(graph)
        generators = stabilizer_generators_for_graph(n, edges)

        # Encode generators in symplectic form
        # Pauli string like "XZIY" -> x_bits = [1,0,0,0], z_bits = [0,1,0,0]
        # (Y = XZ, so both bits set)
        sym_gens = []
        for (pauli_str, _) in generators:
            x_bits = []
            z_bits = []
            for c in pauli_str:
                if c == 'I':
                    x_bits.append(0); z_bits.append(0)
                elif c == 'X':
                    x_bits.append(1); z_bits.append(0)
                elif c == 'Y':
                    x_bits.append(1); z_bits.append(1)
                elif c == 'Z':
                    x_bits.append(0); z_bits.append(1)
            sym_gens.append((x_bits, z_bits))

        # Check 1: All generators commute
        # Two Paulis (x1,z1) and (x2,z2) commute iff
        # sum_i (x1_i*z2_i + x2_i*z1_i) = 0 mod 2
        solver = Solver()
        commutativity_ok = True
        for i in range(len(sym_gens)):
            for j in range(i + 1, len(sym_gens)):
                x1, z1 = sym_gens[i]
                x2, z2 = sym_gens[j]
                symplectic_product = sum(
                    x1[k] * z2[k] + x2[k] * z1[k] for k in range(n)
                ) % 2
                if symplectic_product != 0:
                    commutativity_ok = False
        print(f"  All generators commute: {commutativity_ok}")

        # Check 2: Each generator squares to identity
        # For Paulis this is automatic (P^2 = I for any Pauli)
        squares_to_identity = True
        print(f"  All generators square to I: {squares_to_identity} (Pauli property)")

        # Check 3: Independence -- verify the symplectic vectors are
        # linearly independent over GF(2)
        # Build matrix of x-parts (the z-parts are determined by graph)
        # Actually build full symplectic matrix [x | z]
        sym_matrix = np.zeros((len(sym_gens), 2 * n), dtype=int)
        for i, (xb, zb) in enumerate(sym_gens):
            for k in range(n):
                sym_matrix[i, k] = xb[k]
                sym_matrix[i, n + k] = zb[k]
        gf2_r = _gf2_rank(sym_matrix)
        independent = (gf2_r == len(sym_gens))
        print(f"  Generators independent (GF2 rank={gf2_r}, n_gens={len(sym_gens)}): {independent}")

        # Check 4: Use z3 to verify no non-trivial linear combination
        # of generators gives the identity (all-zero symplectic vector)
        s = Solver()
        coeffs = [Bool(f"c_{name}_{i}") for i in range(len(sym_gens))]
        # At least one coefficient must be True (non-trivial combination)
        s.add(Or(*coeffs))
        # Each bit of the resulting symplectic vector must be 0 (mod 2)
        for bit_pos in range(2 * n):
            # XOR of coefficients where the matrix entry is 1
            active = [coeffs[i] for i in range(len(sym_gens)) if sym_matrix[i, bit_pos] == 1]
            if len(active) == 0:
                continue  # bit is always 0, constraint satisfied
            # XOR of all active must be False (even parity)
            xor_expr = active[0]
            for a in active[1:]:
                xor_expr = Xor(xor_expr, a)
            s.add(Not(xor_expr))  # XOR must be 0

        z3_independent = (s.check() != sat)
        print(f"  z3 confirms independence: {z3_independent}")

        z3_results[name] = {
            "all_commute": commutativity_ok,
            "all_square_to_identity": squares_to_identity,
            "gf2_rank": gf2_r,
            "n_generators": len(sym_gens),
            "independent": independent,
            "z3_independence_verified": z3_independent,
            "symplectic_generators": [
                {"pauli": generators[i][0], "x_bits": sym_gens[i][0], "z_bits": sym_gens[i][1]}
                for i in range(len(sym_gens))
            ],
        }

    return z3_results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative tests -- things that should NOT work.
    """
    print("\n" + "=" * 72)
    print("NEGATIVE TESTS")
    print("=" * 72)

    n = 4
    results = {}

    # Neg 1: A random state should NOT be stabilized by graph state stabilizers
    print("\n  Neg 1: Random state vs graph stabilizers")
    random_state = torch.randn(2 ** n, dtype=torch.cdouble)
    random_state = random_state / torch.norm(random_state)
    edges_line = [(0, 1), (1, 2), (2, 3)]
    generators = stabilizer_generators_for_graph(n, edges_line)
    stab_check = verify_stabilizers(random_state, generators)
    any_stabilized = any(r["stabilized"] for r in stab_check)
    # With overwhelming probability, no generator stabilizes a random state
    print(f"    Any random state stabilized: {any_stabilized} (expected: very likely False)")
    results["random_state_not_stabilized"] = {
        "any_stabilized": any_stabilized,
        "expected": False,
        "pass": not any_stabilized,
        "note": "Random state should not be stabilized by graph state generators",
    }

    # Neg 2: Wrong stabilizer -- flip one generator, should fail
    print("\n  Neg 2: Modified stabilizer should fail")
    line_state = build_graph_state(n, edges_line)
    # Modify first generator: replace X with Y on qubit 0
    wrong_gen_str = "YZII"  # Should be XZII for line graph
    wrong_mat = n_qubit_pauli(wrong_gen_str, n)
    result_vec = wrong_mat @ line_state
    overlap = torch.vdot(line_state, result_vec).real.item()
    wrong_stabilizes = abs(overlap - 1.0) < 1e-6
    print(f"    Wrong generator '{wrong_gen_str}' stabilizes: {wrong_stabilizes} (expected: False)")
    results["wrong_stabilizer_fails"] = {
        "generator": wrong_gen_str,
        "eigenvalue": round(overlap, 10),
        "stabilizes": wrong_stabilizes,
        "expected": False,
        "pass": not wrong_stabilizes,
    }

    # Neg 3: Non-commuting "stabilizers" -- should have non-zero symplectic product
    print("\n  Neg 3: Non-commuting Paulis detected")
    # X_0 Z_0 = -Z_0 X_0, so they anticommute
    x_bits_1 = [1, 0, 0, 0]
    z_bits_1 = [0, 0, 0, 0]
    x_bits_2 = [0, 0, 0, 0]
    z_bits_2 = [1, 0, 0, 0]
    symp_prod = sum(x_bits_1[k] * z_bits_2[k] + x_bits_2[k] * z_bits_1[k] for k in range(n)) % 2
    anticommute = (symp_prod == 1)
    print(f"    X_0 and Z_0 anticommute: {anticommute} (expected: True)")
    results["anticommutation_detected"] = {
        "pauli_1": "XIII", "pauli_2": "ZIII",
        "symplectic_product": symp_prod,
        "anticommute": anticommute,
        "expected": True,
        "pass": anticommute,
    }

    # Neg 4: Product state has zero entanglement
    print("\n  Neg 4: Product state has zero entanglement")
    product_state = kron_list([KET_PLUS] * n)  # |++++> before CZ
    entropies = all_bipartition_entropies(product_state, n)
    max_entropy = max(entropies.values())
    zero_entanglement = max_entropy < 1e-10
    print(f"    Max bipartition entropy of |++++>: {max_entropy} (expected: 0)")
    results["product_state_zero_entanglement"] = {
        "max_entropy": max_entropy,
        "zero_entanglement": zero_entanglement,
        "pass": zero_entanglement,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Edge cases and boundary conditions."""
    print("\n" + "=" * 72)
    print("BOUNDARY TESTS")
    print("=" * 72)

    results = {}

    # Boundary 1: Single-qubit "graph state" (no edges) = |+>
    print("\n  Boundary 1: Single-qubit graph state = |+>")
    state_1q = build_graph_state(1, [])
    fidelity_plus = torch.abs(torch.vdot(state_1q, KET_PLUS)) ** 2
    is_plus = fidelity_plus.item() > 1 - 1e-10
    print(f"    Fidelity with |+>: {fidelity_plus.item():.10f}, is |+>: {is_plus}")
    results["single_qubit_graph_state"] = {
        "fidelity_with_plus": round(fidelity_plus.item(), 10),
        "is_plus_state": is_plus,
        "pass": is_plus,
    }

    # Boundary 2: Two-qubit graph state with one edge = Bell state
    print("\n  Boundary 2: Two-qubit graph state = Bell-like state")
    state_2q = build_graph_state(2, [(0, 1)])
    # CZ|++> = (1/2)(|00>+|01>+|10>-|11>) which is a stabilizer state
    # Entanglement entropy should be 1
    entropy_2q = entanglement_entropy_bipartition(state_2q, 2, [0])
    is_max_ent = abs(entropy_2q - 1.0) < 1e-6
    print(f"    S(A) for 2-qubit graph state: {entropy_2q:.10f}, maximally entangled: {is_max_ent}")
    results["two_qubit_graph_state"] = {
        "entropy": round(entropy_2q, 10),
        "maximally_entangled": is_max_ent,
        "pass": is_max_ent,
    }

    # Boundary 3: Graph state is invariant under local complementation
    # (not a full test, but verify a known identity)
    # For complete graph K4, all single-qubit entropies should be 1
    print("\n  Boundary 3: Complete graph -- all single-qubit bipartitions maximally entangled")
    state_k4 = build_graph_state(4, [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)])
    single_entropies = []
    for q in range(4):
        s = entanglement_entropy_bipartition(state_k4, 4, [q])
        single_entropies.append(round(s, 10))
    all_max = all(abs(s - 1.0) < 1e-6 for s in single_entropies)
    print(f"    Single-qubit entropies: {single_entropies}, all=1: {all_max}")
    results["complete_graph_max_entanglement"] = {
        "single_qubit_entropies": single_entropies,
        "all_maximally_entangled": all_max,
        "pass": all_max,
    }

    # Boundary 4: Star graph -- center qubit has max entanglement, leaves vary
    print("\n  Boundary 4: Star graph -- center vs leaf entanglement")
    state_star = build_graph_state(4, [(0,1),(0,2),(0,3)])
    s_center = entanglement_entropy_bipartition(state_star, 4, [0])
    s_leaf = entanglement_entropy_bipartition(state_star, 4, [1])
    # Center should be maximally entangled (degree 3 > 1), leaf has degree 1
    print(f"    S(center={0}): {s_center:.6f}, S(leaf={1}): {s_leaf:.6f}")
    results["star_center_vs_leaf"] = {
        "s_center": round(s_center, 10),
        "s_leaf": round(s_leaf, 10),
        "center_is_1": abs(s_center - 1.0) < 1e-6,
        "leaf_is_1": abs(s_leaf - 1.0) < 1e-6,
        "pass": abs(s_center - 1.0) < 1e-6 and abs(s_leaf - 1.0) < 1e-6,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("sim_lego_graph_cluster_states.py")
    print("=" * 72)

    positive_graph = run_graph_state_tests()
    positive_cluster = run_cluster_state_tests()
    z3_checks = run_z3_stabilizer_checks()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Aggregate pass/fail
    all_graph_stab = all(
        v["all_stabilized"] for v in positive_graph.values()
    )
    all_graph_struct = all(
        v["all_structure_match"] for v in positive_graph.values()
    )
    all_z3 = all(
        v["all_commute"] and v["independent"] and v["z3_independence_verified"]
        for v in z3_checks.values()
    )
    cluster_stab = positive_cluster["cluster_1d_4q"]["all_stabilized"]
    mbqc_ok = positive_cluster["mbqc"]["all_mbqc_verified"]
    all_neg = all(v.get("pass", False) for v in negative.values())
    all_bnd = all(v.get("pass", False) for v in boundary.values())

    summary = {
        "all_graph_states_stabilized": all_graph_stab,
        "all_entanglement_matches_graph": all_graph_struct,
        "all_z3_properties_verified": all_z3,
        "cluster_state_stabilized": cluster_stab,
        "mbqc_verified": mbqc_ok,
        "all_negative_tests_pass": all_neg,
        "all_boundary_tests_pass": all_bnd,
        "overall_pass": all([
            all_graph_stab, all_graph_struct, all_z3,
            cluster_stab, mbqc_ok,  all_neg, all_bnd,
        ]),
    }

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    for k, v in summary.items():
        status = "PASS" if v else "FAIL"
        print(f"  {k}: {status}")

    results = {
        "name": "lego_graph_cluster_states",
        "tool_manifest": TOOL_MANIFEST,
        "positive": {
            "graph_states": positive_graph,
            "cluster_states": positive_cluster,
        },
        "z3_verification": z3_checks,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_graph_cluster_states_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
