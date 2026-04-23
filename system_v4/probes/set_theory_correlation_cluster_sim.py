#!/usr/bin/env python3
"""
Set Theory as Correlation Clusters SIM
========================================
Falsifiable thesis: "Sets" emerge as stable correlation clusters.
Connected components of a mutual-information graph remain invariant
(high Jaccard similarity) under small perturbations and dissolve
under large perturbations.

EvidenceToken: PASS if Jaccard >= 0.90 at small λ AND Jaccard <= 0.60 at large λ.
"""

import numpy as np
import json
import os
import sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken, von_neumann_entropy


def partial_trace_single(rho_full, n_qubits, trace_out):
    """Trace out a single qubit from an n-qubit density matrix."""
    d = 2 ** n_qubits
    rho = rho_full.reshape([2] * (2 * n_qubits))
    # Move traced-out axes to the end, then trace
    axes_order = list(range(2 * n_qubits))
    # trace_out-th ket axis and (trace_out + n_qubits)-th bra axis
    ket_ax = trace_out
    bra_ax = trace_out + n_qubits
    result = np.trace(rho, axis1=ket_ax, axis2=bra_ax)
    d_out = 2 ** (n_qubits - 1)
    return result.reshape(d_out, d_out)


def two_qubit_reduced(rho_full, n_qubits, i, j):
    """Get the 2-qubit reduced density matrix for qubits i,j."""
    # Trace out all qubits except i and j
    keep = sorted([i, j])
    trace_qubits = [q for q in range(n_qubits) if q not in keep]
    rho = rho_full
    cur_n = n_qubits
    for offset, q in enumerate(sorted(trace_qubits)):
        adjusted_q = q - offset
        rho = partial_trace_single(rho, cur_n, adjusted_q)
        cur_n -= 1
    return rho


def single_qubit_reduced(rho_full, n_qubits, i):
    """Get the 1-qubit reduced density matrix for qubit i."""
    trace_qubits = [q for q in range(n_qubits) if q != i]
    rho = rho_full
    cur_n = n_qubits
    for offset, q in enumerate(sorted(trace_qubits)):
        adjusted_q = q - offset
        rho = partial_trace_single(rho, cur_n, adjusted_q)
        cur_n -= 1
    return rho


def mutual_information_matrix(rho, n_qubits):
    """Compute pairwise mutual information I(i:j) for all qubit pairs."""
    mi = np.zeros((n_qubits, n_qubits))
    S_single = {}
    for i in range(n_qubits):
        S_single[i] = von_neumann_entropy(single_qubit_reduced(rho, n_qubits, i))

    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            rho_ij = two_qubit_reduced(rho, n_qubits, i, j)
            S_ij = von_neumann_entropy(rho_ij)
            I_ij = S_single[i] + S_single[j] - S_ij
            mi[i, j] = max(I_ij, 0.0)
            mi[j, i] = mi[i, j]
    return mi


def threshold_clusters(mi_matrix, tau):
    """Find connected components of the MI graph above threshold tau."""
    n = mi_matrix.shape[0]
    visited = [False] * n
    clusters = []

    def bfs(start):
        cluster = {start}
        queue = [start]
        visited[start] = True
        while queue:
            node = queue.pop(0)
            for neighbor in range(n):
                if not visited[neighbor] and mi_matrix[node, neighbor] > tau:
                    visited[neighbor] = True
                    cluster.add(neighbor)
                    queue.append(neighbor)
        return frozenset(cluster)

    for i in range(n):
        if not visited[i]:
            clusters.append(bfs(i))
    return set(clusters)


def jaccard_partitions(clusters_a, clusters_b):
    """Jaccard similarity between two set-of-sets partitions."""
    pairs_a = set()
    for c in clusters_a:
        for i in c:
            for j in c:
                if i < j:
                    pairs_a.add((i, j))
    pairs_b = set()
    for c in clusters_b:
        for i in c:
            for j in c:
                if i < j:
                    pairs_b.add((i, j))
    if not pairs_a and not pairs_b:
        return 1.0
    intersection = len(pairs_a & pairs_b)
    union = len(pairs_a | pairs_b)
    return intersection / max(union, 1)


def random_perturbation(rho, lam, rng):
    """Apply a perturbation of strength lambda to a density matrix."""
    d = rho.shape[0]
    noise = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    noise = (noise + noise.conj().T) / 2
    noise /= max(np.linalg.norm(noise, 'fro'), 1e-30)
    rho_pert = (1 - lam) * rho + lam * noise
    # Enforce PSD + trace 1
    evals, evecs = np.linalg.eigh(rho_pert)
    evals = np.maximum(evals, 0)
    rho_pert = evecs @ np.diag(evals) @ evecs.conj().T
    rho_pert /= max(np.real(np.trace(rho_pert)), 1e-30)
    return rho_pert


def run_set_theory_sim():
    print("=" * 72)
    print("SET THEORY AS CORRELATION CLUSTERS SIM")
    print("=" * 72)

    n_qubits = 4
    d = 2 ** n_qubits
    n_trials = 20
    tau = 0.1  # MI threshold for cluster membership
    lam_small = 0.05
    lam_large = 0.8

    rng = np.random.default_rng(42)
    tokens = []

    # Build a structured state with known cluster structure:
    # Qubits 0,1 are entangled (Bell pair); Qubits 2,3 are entangled (Bell pair)
    # Expected clusters: {0,1} and {2,3}
    bell_01 = np.zeros(4, dtype=complex)
    bell_01[0] = 1 / np.sqrt(2)
    bell_01[3] = 1 / np.sqrt(2)
    rho_01 = np.outer(bell_01, bell_01.conj())

    bell_23 = np.zeros(4, dtype=complex)
    bell_23[0] = 1 / np.sqrt(2)
    bell_23[3] = 1 / np.sqrt(2)
    rho_23 = np.outer(bell_23, bell_23.conj())

    rho_base = np.kron(rho_01, rho_23)  # 16x16

    mi_base = mutual_information_matrix(rho_base, n_qubits)
    clusters_base = threshold_clusters(mi_base, tau)
    print(f"\n  Base MI matrix:\n{np.round(mi_base, 3)}")
    print(f"  Base clusters: {[sorted(c) for c in clusters_base]}")

    # Small perturbation stability
    jaccards_small = []
    for t in range(n_trials):
        rho_pert = random_perturbation(rho_base, lam_small, rng)
        mi_pert = mutual_information_matrix(rho_pert, n_qubits)
        clusters_pert = threshold_clusters(mi_pert, tau)
        j = jaccard_partitions(clusters_base, clusters_pert)
        jaccards_small.append(j)

    mean_j_small = float(np.mean(jaccards_small))
    print(f"\n  Small perturbation (λ={lam_small}): mean Jaccard = {mean_j_small:.4f}")

    # Large perturbation dissolution
    jaccards_large = []
    for t in range(n_trials):
        rho_pert = random_perturbation(rho_base, lam_large, rng)
        mi_pert = mutual_information_matrix(rho_pert, n_qubits)
        clusters_pert = threshold_clusters(mi_pert, tau)
        j = jaccard_partitions(clusters_base, clusters_pert)
        jaccards_large.append(j)

    mean_j_large = float(np.mean(jaccards_large))
    print(f"  Large perturbation (λ={lam_large}): mean Jaccard = {mean_j_large:.4f}")

    # Verdict
    stable = mean_j_small >= 0.90
    dissolves = mean_j_large <= 0.60
    overall = stable and dissolves

    print(f"\n  Stable under small perturbation (≥0.90): {'YES ✓' if stable else 'NO ✗'}")
    print(f"  Dissolves under large perturbation (≤0.60): {'YES ✓' if dissolves else 'NO ✗'}")
    print(f"  OVERALL: {'PASS' if overall else 'KILL'}")

    if overall:
        tokens.append(EvidenceToken("E_SIM_SET_THEORY_CLUSTER_OK", "S_SIM_SET_THEORY_CLUSTER", "PASS", mean_j_small))
    else:
        tokens.append(EvidenceToken("", "S_SIM_SET_THEORY_CLUSTER", "KILL", mean_j_small,
                                    f"small={mean_j_small:.3f},large={mean_j_large:.3f}"))

    # Save
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "set_theory_cluster_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "n_qubits": n_qubits, "tau": tau, "n_trials": n_trials,
            "mean_jaccard_small": mean_j_small, "mean_jaccard_large": mean_j_large,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_set_theory_sim()
