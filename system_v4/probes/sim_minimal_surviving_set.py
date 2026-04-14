#!/usr/bin/env python3
"""
sim_minimal_surviving_set.py
============================

FINAL CONSTRAINT ANALYSIS: Minimal Generating Set of 43 L7 Survivors.

Takes the 43 legos that survived L0-L7 and determines:
  1. Redundancy detection via correlation analysis on 100 random density matrices
  2. z3 minimal generating set (minimum cover)
  3. Categorization into functional groups
  4. Hypothetical L8/L9/L10 kill analysis

Uses: numpy, scipy, z3. NO engine imports.
"""

import json
import pathlib
import time
import traceback
from datetime import datetime, UTC
from itertools import combinations

import numpy as np
from scipy.linalg import sqrtm, logm, expm
from scipy.stats import spearmanr
from z3 import (
classification = "classical_baseline"  # auto-backfill
    Solver, Bool, And, Or, Not, Implies, sat, unsat,
    BoolVal, Optimize, Sum, If as Z3If,
)

np.random.seed(42)
EPS = 1e-14
TOL = 1e-10
N_STATES = 100
CORR_THRESHOLD = 0.999  # Spearman rank correlation threshold for "redundant"

# ── Pauli matrices ──────────────────────────────────────────────────
I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
paulis = [I2, sx, sy, sz]
I4 = np.eye(4, dtype=complex)

# ══════════════════════════════════════════════════════════════════════
# THE 43 L7 SURVIVORS
# ══════════════════════════════════════════════════════════════════════
# 19 STRUCTURAL (operators/gates/channels/decompositions — the engine IS these)
STRUCTURAL = [
    'density_matrix', 'purification',
    'z_dephasing', 'x_dephasing', 'depolarizing',
    'amplitude_damping', 'phase_damping',
    'bit_flip', 'phase_flip', 'bit_phase_flip',
    'unitary_rotation', 'z_measurement',
    'CNOT', 'CZ', 'SWAP', 'Hadamard', 'T_gate', 'iSWAP',
    'cartan_kak',
]

# 21 TYPE-SENSITIVE (survive L6+L7, distinguish Type1 from Type2)
TYPE_SENSITIVE = [
    'bloch_vector', 'stokes_parameters', 'eigenvalue_decomposition',
    'wigner_function', 'husimi_q', 'coherence_vector',
    'characteristic_function', 'relative_entropy',
    'fubini_study', 'bures_distance', 'hs_distance', 'trace_distance',
    'svd', 'spectral', 'pauli_decomposition',
    'l1_coherence', 'relative_entropy_coherence',
    'wigner_negativity',
    'hopf_connection', 'chiral_overlap', 'chiral_current',
]

# 3 TYPE-BLIND (survive L6, reduced at L7 — don't distinguish chirality)
TYPE_BLIND = [
    'mutual_information', 'mutual_information_corr', 'quantum_discord',
]

ALL_43 = STRUCTURAL + TYPE_SENSITIVE + TYPE_BLIND
assert len(ALL_43) == 43, f"Expected 43, got {len(ALL_43)}"


# ══════════════════════════════════════════════════════════════════════
# STATE GENERATION
# ══════════════════════════════════════════════════════════════════════
def random_density_4x4():
    """Generate a random 4x4 density matrix (2-qubit) via Ginibre ensemble."""
    G = np.random.randn(4, 4) + 1j * np.random.randn(4, 4)
    rho = G @ G.conj().T
    rho /= np.trace(rho)
    return rho

def partial_trace(rho_2q, keep=0):
    rho = rho_2q.reshape(2, 2, 2, 2)
    if keep == 0:
        return np.trace(rho, axis1=1, axis2=3)
    else:
        return np.trace(rho, axis1=0, axis2=2)


# ══════════════════════════════════════════════════════════════════════
# LEGO MEASUREMENT FUNCTIONS (state-dependent only — 24 measurable legos)
# ══════════════════════════════════════════════════════════════════════
def von_neumann_entropy(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > EPS]
    return float(-np.sum(evals * np.log2(evals)))

def fidelity(rho, sigma):
    sr = sqrtm(rho)
    val = sqrtm(sr @ sigma @ sr)
    return float(np.real(np.trace(val)) ** 2)

def relative_entropy_val(rho, sigma):
    log_rho = logm(rho)
    log_sig = logm(sigma)
    val = np.trace(rho @ (log_rho - log_sig))
    return float(np.real(val))

def bloch_vector_1q(rho_1q):
    return np.array([
        float(np.real(np.trace(rho_1q @ sx))),
        float(np.real(np.trace(rho_1q @ sy))),
        float(np.real(np.trace(rho_1q @ sz))),
    ])

def bloch_length(rho_1q):
    return float(np.linalg.norm(bloch_vector_1q(rho_1q)))

def stokes_norm(rho_1q):
    s = np.array([
        float(np.real(np.trace(rho_1q))),
        float(np.real(np.trace(rho_1q @ sx))),
        float(np.real(np.trace(rho_1q @ sy))),
        float(np.real(np.trace(rho_1q @ sz))),
    ])
    return float(np.linalg.norm(s))

def eigenvalue_norm(rho_1q):
    return float(np.linalg.norm(np.sort(np.real(np.linalg.eigvalsh(rho_1q)))))

def wigner_function_norm(rho_1q):
    A = [
        0.5 * (I2 + sz + sx + sy),
        0.5 * (I2 + sz - sx - sy),
        0.5 * (I2 - sz - sx + sy),
        0.5 * (I2 - sz + sx - sy),
    ]
    W = np.array([float(np.real(np.trace(a @ rho_1q))) for a in A])
    return float(np.linalg.norm(W))

def husimi_q_norm(rho_1q):
    directions = [
        np.array([1, 0], dtype=complex),
        np.array([0, 1], dtype=complex),
        np.array([1, 1], dtype=complex) / np.sqrt(2),
        np.array([1, 1j], dtype=complex) / np.sqrt(2),
    ]
    vals = []
    for d in directions:
        proj = np.outer(d, d.conj())
        vals.append(float(np.real(np.trace(proj @ rho_1q))))
    return float(np.linalg.norm(vals))

def coherence_vector_val(rho_1q):
    return bloch_length(rho_1q)

def characteristic_function_norm(rho_1q):
    disps = [I2, sx, sy, sz]
    vals = np.array([float(np.real(np.trace(D @ rho_1q))) for D in disps])
    return float(np.linalg.norm(vals))

def relative_entropy_to_mixed(rho_1q):
    mixed = 0.5 * I2
    return relative_entropy_val(rho_1q, mixed)

def mutual_information_val(rho_2q):
    rho_A = partial_trace(rho_2q, keep=0)
    rho_B = partial_trace(rho_2q, keep=1)
    return von_neumann_entropy(rho_A) + von_neumann_entropy(rho_B) - von_neumann_entropy(rho_2q)

def quantum_discord_approx(rho_2q):
    rho_A = partial_trace(rho_2q, keep=0)
    rho_B = partial_trace(rho_2q, keep=1)
    S_AB = von_neumann_entropy(rho_2q)
    S_B = von_neumann_entropy(rho_B)
    best_cc = -np.inf
    for basis_op in [sz, sx, sy]:
        evals, evecs = np.linalg.eigh(basis_op)
        cc = S_B
        for k in range(2):
            proj = np.outer(evecs[:, k], evecs[:, k].conj())
            proj_2q = np.kron(proj, I2)
            rho_post = proj_2q @ rho_2q @ proj_2q
            p_k = float(np.real(np.trace(rho_post)))
            if p_k > EPS:
                rho_cond = rho_post / p_k
                rho_cond_B = partial_trace(rho_cond, keep=1)
                cc -= p_k * von_neumann_entropy(rho_cond_B)
        if cc > best_cc:
            best_cc = cc
    MI = von_neumann_entropy(rho_A) + S_B - S_AB
    return max(0.0, MI - best_cc)

def fubini_study_val(rho_1q, ref_1q):
    F = fidelity(rho_1q, ref_1q)
    arg = np.clip(np.sqrt(np.clip(F, 0, 1)), -1, 1)
    return float(np.arccos(arg))

def bures_distance_val(rho_1q, ref_1q):
    F = fidelity(rho_1q, ref_1q)
    return float(np.sqrt(np.clip(2 * (1 - np.sqrt(np.clip(F, 0, 1))), 0, None)))

def hs_distance_val(rho_1q, ref_1q):
    diff = rho_1q - ref_1q
    return float(np.sqrt(np.real(np.trace(diff @ diff.conj().T))))

def trace_distance_val(rho_1q, ref_1q):
    diff = rho_1q - ref_1q
    evals = np.linalg.eigvalsh(diff @ diff.conj().T)
    return float(0.5 * np.sum(np.sqrt(np.clip(evals, 0, None))))

def svd_norm(rho_1q):
    return float(np.linalg.norm(np.linalg.svd(rho_1q, compute_uv=False)))

def spectral_norm(rho_1q):
    return float(np.linalg.norm(np.sort(np.real(np.linalg.eigvalsh(rho_1q)))))

def pauli_decomp_norm(rho_1q):
    coeffs = np.array([float(np.real(np.trace(P @ rho_1q))) / 2.0 for P in [I2, sx, sy, sz]])
    return float(np.linalg.norm(coeffs))

def l1_coherence_val(rho_1q):
    return float(np.sum(np.abs(rho_1q)) - np.sum(np.abs(np.diag(rho_1q))))

def relative_entropy_coherence_val(rho_1q):
    diag_rho = np.diag(np.diag(rho_1q))
    return von_neumann_entropy(diag_rho) - von_neumann_entropy(rho_1q)

def wigner_negativity_val(rho_1q):
    A = [
        0.5 * (I2 + sz + sx + sy),
        0.5 * (I2 + sz - sx - sy),
        0.5 * (I2 - sz - sx + sy),
        0.5 * (I2 - sz + sx - sy),
    ]
    W = np.array([float(np.real(np.trace(a @ rho_1q))) for a in A])
    return float(np.sum(np.minimum(W, 0)))

def hopf_connection_val(rho_1q):
    evals, evecs = np.linalg.eigh(rho_1q)
    psi = evecs[:, -1]
    dpsi = np.array([-psi[1], psi[0]], dtype=complex) * 0.01
    return float(np.imag(np.vdot(psi, dpsi)))

def chiral_overlap_norm(rho_1q):
    C = 1j * sx @ sy @ sz
    evals_C, evecs_C = np.linalg.eigh(C)
    overlaps = []
    for k in range(2):
        proj = np.outer(evecs_C[:, k], evecs_C[:, k].conj())
        overlaps.append(float(np.real(np.trace(proj @ rho_1q))))
    return float(np.linalg.norm(overlaps))

def chiral_current_norm(rho_1q):
    C = 1j * sx @ sy @ sz
    vals = []
    for P in [sx, sy, sz]:
        anti_comm = C @ P + P @ C
        vals.append(float(np.real(np.trace(anti_comm @ rho_1q / 2))))
    return float(np.linalg.norm(vals))


# ══════════════════════════════════════════════════════════════════════
# MEASURABLE LEGO REGISTRY — maps name -> function(rho_2q, rho_A, rho_B, ref_A)
# ══════════════════════════════════════════════════════════════════════
# For the redundancy analysis, we need a scalar value per state per lego.
# Structural legos are operators, not state measurements — they get
# separate treatment (always irreducible as a class).

MEASURABLE_LEGOS = {
    # 1q measures (computed on reduced state rho_A)
    'bloch_vector':               lambda rA, rB, r2q, ref: bloch_length(rA),
    'stokes_parameters':          lambda rA, rB, r2q, ref: stokes_norm(rA),
    'eigenvalue_decomposition':   lambda rA, rB, r2q, ref: eigenvalue_norm(rA),
    'wigner_function':            lambda rA, rB, r2q, ref: wigner_function_norm(rA),
    'husimi_q':                   lambda rA, rB, r2q, ref: husimi_q_norm(rA),
    'coherence_vector':           lambda rA, rB, r2q, ref: coherence_vector_val(rA),
    'characteristic_function':    lambda rA, rB, r2q, ref: characteristic_function_norm(rA),
    'relative_entropy':           lambda rA, rB, r2q, ref: relative_entropy_to_mixed(rA),
    'svd':                        lambda rA, rB, r2q, ref: svd_norm(rA),
    'spectral':                   lambda rA, rB, r2q, ref: spectral_norm(rA),
    'pauli_decomposition':        lambda rA, rB, r2q, ref: pauli_decomp_norm(rA),
    'l1_coherence':               lambda rA, rB, r2q, ref: l1_coherence_val(rA),
    'relative_entropy_coherence': lambda rA, rB, r2q, ref: relative_entropy_coherence_val(rA),
    'wigner_negativity':          lambda rA, rB, r2q, ref: wigner_negativity_val(rA),
    'hopf_connection':            lambda rA, rB, r2q, ref: hopf_connection_val(rA),
    'chiral_overlap':             lambda rA, rB, r2q, ref: chiral_overlap_norm(rA),
    'chiral_current':             lambda rA, rB, r2q, ref: chiral_current_norm(rA),
    # Distance measures (rho_A vs ref_A)
    'fubini_study':               lambda rA, rB, r2q, ref: fubini_study_val(rA, ref),
    'bures_distance':             lambda rA, rB, r2q, ref: bures_distance_val(rA, ref),
    'hs_distance':                lambda rA, rB, r2q, ref: hs_distance_val(rA, ref),
    'trace_distance':             lambda rA, rB, r2q, ref: trace_distance_val(rA, ref),
    # 2q measures
    'mutual_information':         lambda rA, rB, r2q, ref: mutual_information_val(r2q),
    'mutual_information_corr':    lambda rA, rB, r2q, ref: mutual_information_val(r2q),
    'quantum_discord':            lambda rA, rB, r2q, ref: quantum_discord_approx(r2q),
}

MEASURABLE_NAMES = list(MEASURABLE_LEGOS.keys())
N_MEASURABLE = len(MEASURABLE_NAMES)


# ══════════════════════════════════════════════════════════════════════
# ANALYSIS 1: REDUNDANCY DETECTION
# ══════════════════════════════════════════════════════════════════════
def analysis_1_redundancy():
    """Compute all 24 measurable legos on 100 random 4x4 density matrices.
    Build correlation matrix. Find perfectly correlated clusters."""
    print("[A1] Computing lego values on 100 random states...")

    # Reference state for distance measures
    ref_1q = 0.5 * I2  # maximally mixed

    # Collect values: shape (N_STATES, N_MEASURABLE)
    values = np.zeros((N_STATES, N_MEASURABLE))
    errors = []

    for i in range(N_STATES):
        rho_2q = random_density_4x4()
        rho_A = partial_trace(rho_2q, keep=0)
        rho_B = partial_trace(rho_2q, keep=1)

        for j, name in enumerate(MEASURABLE_NAMES):
            try:
                val = MEASURABLE_LEGOS[name](rho_A, rho_B, rho_2q, ref_1q)
                values[i, j] = val
            except Exception as e:
                values[i, j] = np.nan
                errors.append(f"{name} state {i}: {e}")

    # Build Spearman rank correlation matrix
    print("[A1] Building correlation matrix...")
    corr_matrix = np.zeros((N_MEASURABLE, N_MEASURABLE))
    pval_matrix = np.zeros((N_MEASURABLE, N_MEASURABLE))

    for a in range(N_MEASURABLE):
        for b in range(N_MEASURABLE):
            if a == b:
                corr_matrix[a, b] = 1.0
                continue
            # Skip if either has NaN
            mask = ~(np.isnan(values[:, a]) | np.isnan(values[:, b]))
            if mask.sum() < 10:
                corr_matrix[a, b] = 0.0
                continue
            rho, pval = spearmanr(values[mask, a], values[mask, b])
            corr_matrix[a, b] = rho if not np.isnan(rho) else 0.0
            pval_matrix[a, b] = pval if not np.isnan(pval) else 1.0

    # Find clusters of perfectly correlated legos (|rho| >= threshold)
    print("[A1] Identifying redundancy clusters...")
    visited = set()
    clusters = []

    for i in range(N_MEASURABLE):
        if i in visited:
            continue
        cluster = [i]
        visited.add(i)
        for j in range(i + 1, N_MEASURABLE):
            if j in visited:
                continue
            if abs(corr_matrix[i, j]) >= CORR_THRESHOLD:
                cluster.append(j)
                visited.add(j)
        if len(cluster) > 1:
            clusters.append([MEASURABLE_NAMES[k] for k in cluster])

    # Identify which legos are derivable from others
    derivable_pairs = []
    for i in range(N_MEASURABLE):
        for j in range(i + 1, N_MEASURABLE):
            if abs(corr_matrix[i, j]) >= CORR_THRESHOLD:
                derivable_pairs.append({
                    "A": MEASURABLE_NAMES[i],
                    "B": MEASURABLE_NAMES[j],
                    "spearman_rho": float(corr_matrix[i, j]),
                    "p_value": float(pval_matrix[i, j]),
                })

    # Standalone (not in any cluster)
    clustered_names = set()
    for c in clusters:
        clustered_names.update(c)
    standalone = [n for n in MEASURABLE_NAMES if n not in clustered_names]

    return {
        "n_states": N_STATES,
        "n_measurable_legos": N_MEASURABLE,
        "correlation_threshold": CORR_THRESHOLD,
        "redundancy_clusters": clusters,
        "n_clusters": len(clusters),
        "derivable_pairs": derivable_pairs,
        "standalone_legos": standalone,
        "n_standalone": len(standalone),
        "correlation_matrix": {
            MEASURABLE_NAMES[i]: {
                MEASURABLE_NAMES[j]: round(float(corr_matrix[i, j]), 6)
                for j in range(N_MEASURABLE)
            }
            for i in range(N_MEASURABLE)
        },
        "errors": errors[:10],  # cap at 10
    }


# ══════════════════════════════════════════════════════════════════════
# ANALYSIS 2: z3 MINIMAL GENERATING SET
# ══════════════════════════════════════════════════════════════════════
def analysis_2_z3_minimal_set(redundancy_result):
    """Use z3 Optimize to find the minimum set S such that every lego
    is either in S or derivable from S."""
    print("[A2] z3 minimal generating set...")

    clusters = redundancy_result["redundancy_clusters"]
    standalone = redundancy_result["standalone_legos"]
    derivable_pairs = redundancy_result["derivable_pairs"]

    # Build derivability graph: if A and B are in same cluster,
    # keeping ONE suffices — the others are implied.
    # Additionally, structural legos are always needed (they're operators).

    # Create z3 Boolean variables for each of the 43 legos
    lego_vars = {name: Bool(name) for name in ALL_43}

    opt = Optimize()

    # Constraint: every lego must be "covered"
    # A lego is covered if it's in S OR if some cluster-mate is in S

    # Build cluster membership
    cluster_map = {}  # lego -> cluster_id
    for cid, cluster in enumerate(clusters):
        for name in cluster:
            cluster_map[name] = cid

    # For each lego: it's covered if it's selected OR any cluster-mate is selected
    for name in ALL_43:
        if name in STRUCTURAL:
            # Structural legos: always included (they ARE the engine)
            opt.add(lego_vars[name])
        elif name in cluster_map:
            # In a cluster: at least one cluster member must be selected
            cid = cluster_map[name]
            cluster_members = clusters[cid]
            opt.add(Or(*[lego_vars[m] for m in cluster_members]))
        else:
            # Standalone: must be selected (no redundant partner)
            opt.add(lego_vars[name])

    # Objective: minimize total selected
    cost = Sum([Z3If(lego_vars[name], 1, 0) for name in ALL_43])
    opt.minimize(cost)

    result = opt.check()
    if result == sat:
        model = opt.model()
        selected = [name for name in ALL_43 if str(model.evaluate(lego_vars[name])) == 'True']
        excluded = [name for name in ALL_43 if str(model.evaluate(lego_vars[name])) != 'True']
        min_size = len(selected)
    else:
        selected = ALL_43[:]
        excluded = []
        min_size = 43

    # Identify irreducible core (must be in every minimal set)
    irreducible = []
    for name in ALL_43:
        if name in STRUCTURAL:
            irreducible.append(name)
        elif name not in cluster_map:
            irreducible.append(name)

    # Identify fungible (one from cluster suffices)
    fungible_groups = []
    for cid, cluster in enumerate(clusters):
        rep = None
        for name in cluster:
            if name in [s for s in selected if s not in STRUCTURAL]:
                rep = name
                break
        fungible_groups.append({
            "cluster": cluster,
            "representative": rep or cluster[0],
            "redundant": [n for n in cluster if n != (rep or cluster[0])],
        })

    return {
        "z3_result": str(result),
        "minimal_set_size": min_size,
        "minimal_set": selected,
        "excluded_redundant": excluded,
        "irreducible_core": irreducible,
        "irreducible_count": len(irreducible),
        "fungible_groups": fungible_groups,
        "reduction": f"{43} -> {min_size} ({43 - min_size} redundant)",
    }


# ══════════════════════════════════════════════════════════════════════
# ANALYSIS 3: CATEGORIZATION
# ══════════════════════════════════════════════════════════════════════
def analysis_3_categorize():
    """Group the 43 survivors into functional categories."""
    print("[A3] Categorizing survivors...")

    categories = {
        "STRUCTURAL_CHANNELS": {
            "description": "Dissipative channels — the irreversible dynamics",
            "members": ['z_dephasing', 'x_dephasing', 'depolarizing',
                        'amplitude_damping', 'phase_damping',
                        'bit_flip', 'phase_flip', 'bit_phase_flip'],
            "role": "These ARE the ratchet. Without them, no irreversibility.",
        },
        "STRUCTURAL_GATES": {
            "description": "Unitary gates — the reversible dynamics",
            "members": ['unitary_rotation', 'CNOT', 'CZ', 'SWAP',
                        'Hadamard', 'T_gate', 'iSWAP'],
            "role": "Generate entanglement, create coherent structure between dissipative steps.",
        },
        "STRUCTURAL_DECOMPOSITIONS": {
            "description": "State representation / decomposition scaffolding",
            "members": ['density_matrix', 'purification', 'cartan_kak'],
            "role": "The mathematical container. Without density_matrix, nothing computable.",
        },
        "STRUCTURAL_MEASUREMENT": {
            "description": "Measurement operator",
            "members": ['z_measurement'],
            "role": "Collapse / readout. Bridges quantum to classical.",
        },
        "RELATIVE_MEASURES": {
            "description": "Relative entropy, mutual information, discord — compare states",
            "members": ['relative_entropy', 'mutual_information',
                        'mutual_information_corr', 'quantum_discord'],
            "role": "Quantify information relationships. MI and discord survive dynamics but are type-blind.",
        },
        "DISTANCE_METRICS": {
            "description": "Fubini-Study, Bures, HS, trace distance — geometric distances",
            "members": ['fubini_study', 'bures_distance', 'hs_distance', 'trace_distance'],
            "role": "Measure how far states have moved. All type-sensitive. Potentially redundant cluster.",
        },
        "STATE_REPRESENTATIONS": {
            "description": "Bloch, Stokes, Wigner, Husimi, characteristic function, eigenvalues",
            "members": ['bloch_vector', 'stokes_parameters', 'eigenvalue_decomposition',
                        'wigner_function', 'husimi_q', 'coherence_vector',
                        'characteristic_function', 'svd', 'spectral',
                        'pauli_decomposition'],
            "role": "Different views of the SAME state. High redundancy expected.",
        },
        "COHERENCE_ASYMMETRY": {
            "description": "Basis-dependent coherence measures",
            "members": ['l1_coherence', 'relative_entropy_coherence', 'wigner_negativity'],
            "role": "Quantify non-classicality. Survive cycling but basis-dependent.",
        },
        "TOPOLOGICAL_GEOMETRIC": {
            "description": "Hopf connection, chiral overlap/current",
            "members": ['hopf_connection', 'chiral_overlap', 'chiral_current'],
            "role": "Geometric/topological probes. Hopf connection survives as oscillating (unique behavior). Chiral measures type-sensitive.",
        },
    }

    # Cross-check: every lego is in exactly one category
    all_categorized = []
    for cat in categories.values():
        all_categorized.extend(cat["members"])

    missing = set(ALL_43) - set(all_categorized)
    duplicated = [x for x in all_categorized if all_categorized.count(x) > 1]

    assert len(missing) == 0, f"Missing from categories: {missing}"
    assert len(duplicated) == 0, f"Duplicated in categories: {duplicated}"

    # Category counts
    cat_counts = {k: len(v["members"]) for k, v in categories.items()}

    return {
        "categories": {
            k: {
                "description": v["description"],
                "members": v["members"],
                "count": len(v["members"]),
                "role": v["role"],
            }
            for k, v in categories.items()
        },
        "category_counts": cat_counts,
        "total_categorized": len(all_categorized),
        "structural_total": len(STRUCTURAL),
        "type_sensitive_total": len(TYPE_SENSITIVE),
        "type_blind_total": len(TYPE_BLIND),
    }


# ══════════════════════════════════════════════════════════════════════
# ANALYSIS 4: HYPOTHETICAL L8/L9/L10 KILLS
# ══════════════════════════════════════════════════════════════════════
def analysis_4_hypothetical_kills():
    """What would future constraint layers kill?"""
    print("[A4] Hypothetical L8/L9/L10 analysis...")

    # L8: Entangling gate required
    # If the engine MUST use entangling gates, which legos need entanglement?
    # Legos that are purely 1q measures and don't reference entanglement structure
    # would be INSENSITIVE to whether entanglement exists.
    # But they still SURVIVE — they just don't NEED entanglement.
    # What gets KILLED: nothing, actually. All 1q measures still exist on the
    # reduced state of an entangled pair. The constraint is on the ENGINE, not the legos.
    # However: legos that produce IDENTICAL values with or without entanglement
    # would be entanglement-insensitive.

    needs_entanglement = [
        'mutual_information', 'mutual_information_corr', 'quantum_discord',
        'CNOT', 'CZ', 'SWAP', 'iSWAP', 'cartan_kak',
    ]
    entanglement_sensitive_1q = [
        # These change on the reduced state when entanglement exists vs not
        'bloch_vector', 'stokes_parameters', 'eigenvalue_decomposition',
        'relative_entropy', 'l1_coherence', 'relative_entropy_coherence',
        'coherence_vector', 'wigner_negativity',
        'svd', 'spectral', 'pauli_decomposition',
        'wigner_function', 'husimi_q', 'characteristic_function',
        'chiral_overlap', 'chiral_current', 'hopf_connection',
    ]
    entanglement_neutral = [
        # These exist regardless — structural or distance-only
        'density_matrix', 'purification',
        'z_dephasing', 'x_dephasing', 'depolarizing',
        'amplitude_damping', 'phase_damping',
        'bit_flip', 'phase_flip', 'bit_phase_flip',
        'unitary_rotation', 'z_measurement',
        'Hadamard', 'T_gate',
        'fubini_study', 'bures_distance', 'hs_distance', 'trace_distance',
    ]

    l8_survives = needs_entanglement + entanglement_sensitive_1q
    l8_neutral = entanglement_neutral
    l8_killed = []  # L8 doesn't kill — it REQUIRES. Everything still computable.

    # L9: Specific operator strength
    # If the engine requires a specific dephasing strength p* (Goldilocks),
    # legos insensitive to p would be killed.
    strength_sensitive = [
        'bloch_vector', 'stokes_parameters', 'coherence_vector',
        'relative_entropy', 'l1_coherence', 'relative_entropy_coherence',
        'mutual_information', 'mutual_information_corr', 'quantum_discord',
        'wigner_negativity',
        'fubini_study', 'bures_distance', 'hs_distance', 'trace_distance',
        'eigenvalue_decomposition', 'svd', 'spectral',
        'wigner_function', 'husimi_q', 'characteristic_function',
        'pauli_decomposition',
        'chiral_overlap', 'chiral_current', 'hopf_connection',
    ]
    strength_insensitive = [
        # Structural operators don't depend on the dephasing strength — they ARE the operator
        'density_matrix', 'purification',
        'z_dephasing', 'x_dephasing', 'depolarizing',
        'amplitude_damping', 'phase_damping',
        'bit_flip', 'phase_flip', 'bit_phase_flip',
        'unitary_rotation', 'z_measurement',
        'CNOT', 'CZ', 'SWAP', 'Hadamard', 'T_gate', 'iSWAP',
        'cartan_kak',
    ]

    # L10: Specific torus eta
    # If the geometry is a specific torus with fixed eta parameter,
    # legos that don't reference torus geometry are eta-independent.
    eta_sensitive = [
        'hopf_connection', 'chiral_overlap', 'chiral_current',
        'fubini_study', 'bures_distance',
    ]
    eta_insensitive = [n for n in ALL_43 if n not in eta_sensitive]

    return {
        "L8_entangling_gate_required": {
            "description": "L8 constrains the ENGINE to use entangling gates. All legos survive (they're computed on states that result from entangling dynamics).",
            "survives": len(ALL_43),
            "killed": 0,
            "killed_list": l8_killed,
            "note": "L8 is a PROCESS constraint, not a lego filter. It constrains which structural legos MUST be used (CNOT/CZ/iSWAP), but doesn't eliminate measures.",
            "entanglement_dependent_legos": needs_entanglement,
            "entanglement_sensitive_1q": entanglement_sensitive_1q,
        },
        "L9_specific_operator_strength": {
            "description": "L9 requires specific dephasing strength p*. Legos that are QUALITATIVELY insensitive to p wouldn't distinguish p* from p*+epsilon.",
            "strength_sensitive_count": len(strength_sensitive),
            "strength_insensitive_count": len(strength_insensitive),
            "strength_sensitive": strength_sensitive,
            "strength_insensitive": strength_insensitive,
            "note": "Structural operators are strength-insensitive by definition (they ARE the operator at any p). All 24 measurable legos ARE strength-sensitive. So L9 is really a constraint on the structural operators, not the measures.",
            "effective_kills": 0,
        },
        "L10_specific_torus_eta": {
            "description": "L10 constrains to a specific torus geometry eta. Legos not referencing geometric structure are eta-independent.",
            "eta_sensitive_count": len(eta_sensitive),
            "eta_insensitive_count": len(eta_insensitive),
            "eta_sensitive": eta_sensitive,
            "eta_insensitive": eta_insensitive,
            "note": "Only topological/geometric legos (hopf_connection, chiral measures, geometric distances) are eta-sensitive. L10 doesn't KILL them — it SHARPENS them to a specific geometry.",
            "effective_kills": 0,
        },
        "meta_observation": "L8/L9/L10 are ENGINE constraints, not LEGO filters. They constrain which structural legos must be active and with what parameters. The 24 measurable legos survive all three — they measure RESULTS of constrained dynamics. The real action of L8+ is selecting which of the 19 structural legos are REQUIRED vs optional.",
    }


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════
def main():
    t0 = time.time()
    results = {
        "probe": "sim_minimal_surviving_set",
        "purpose": "Determine the MINIMAL generating set of the 43 L7 survivors. Which are redundant? Which are irreducible?",
        "timestamp": datetime.now(UTC).isoformat(),
        "input": {
            "total_L7_survivors": 43,
            "structural": len(STRUCTURAL),
            "type_sensitive": len(TYPE_SENSITIVE),
            "type_blind": len(TYPE_BLIND),
        },
    }

    try:
        # Analysis 1: Redundancy
        a1 = analysis_1_redundancy()
        results["analysis_1_redundancy"] = a1

        # Analysis 2: z3 minimal set
        a2 = analysis_2_z3_minimal_set(a1)
        results["analysis_2_z3_minimal_set"] = a2

        # Analysis 3: Categories
        a3 = analysis_3_categorize()
        results["analysis_3_categories"] = a3

        # Analysis 4: Hypothetical kills
        a4 = analysis_4_hypothetical_kills()
        results["analysis_4_hypothetical_kills"] = a4

        # ── FINAL SUMMARY ──
        # The irreducible core
        irreducible_measures = [n for n in a2["irreducible_core"] if n not in STRUCTURAL]
        fungible = a2["fungible_groups"]

        results["final_minimal_set"] = {
            "total_43_survivors": ALL_43,
            "minimal_generating_set_size": a2["minimal_set_size"],
            "minimal_generating_set": a2["minimal_set"],
            "irreducible_structural": [n for n in a2["irreducible_core"] if n in STRUCTURAL],
            "irreducible_measures": irreducible_measures,
            "fungible_clusters": fungible,
            "reduction_summary": a2["reduction"],
            "key_insight": (
                "The 19 structural legos are ALL irreducible — they are operators, not measurements. "
                "Among the 24 measurable legos, redundancy clusters reveal which are "
                "just different views of the same information. The minimal generating set "
                "needs ONE representative from each cluster plus all standalone measures."
            ),
        }

    except Exception as e:
        results["error"] = f"{type(e).__name__}: {e}"
        results["traceback"] = traceback.format_exc()

    results["runtime_seconds"] = round(time.time() - t0, 2)

    # Write results
    out_path = pathlib.Path(__file__).parent / "a2_state" / "sim_results" / "minimal_surviving_set_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n[DONE] Results written to {out_path}")
    print(f"       Runtime: {results['runtime_seconds']}s")

    if "analysis_2_z3_minimal_set" in results:
        a2r = results["analysis_2_z3_minimal_set"]
        a1r = results["analysis_1_redundancy"]
        print(f"       Minimal set size: {a2r['minimal_set_size']} / 43")
        print(f"       Redundancy clusters: {a1r['n_clusters']}")
        print(f"       Standalone legos: {a1r['n_standalone']}")
    elif "error" in results:
        print(f"       ERROR: {results['error']}")

    return results


if __name__ == "__main__":
    main()
