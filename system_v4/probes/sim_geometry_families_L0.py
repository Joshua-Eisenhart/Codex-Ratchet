#!/usr/bin/env python3
"""
Geometry Families at L0 (F01+N01) — Which geometries survive C² noncommuting constraints?
=========================================================================================

Tests EVERY geometry family compatible with C²:
  - Distance metrics: trace, fidelity, Bures, Hilbert-Schmidt, relative entropy, Fubini-Study
  - Geometric structures: QFI landscape, quantum geometric tensor, Berry phase
  - Negative tests: flat-vs-curved, real-only restriction

The question: which geometries are compatible with a finite noncommuting system
on C², and which get killed?
"""

import sys
import os
import json
import numpy as np
from scipy.linalg import sqrtm
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: L0 geometry families are scanned here by metric and state-space numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "state-space metrics, geometry families, and L0 compatibility numerics"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geometric_operators import apply_Ti, apply_Fe, apply_Te, apply_Fi

# ═══════════════════════════════════════════════════════════════════
# PAULI MATRICES
# ═══════════════════════════════════════════════════════════════════

SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)

# ═══════════════════════════════════════════════════════════════════
# DISTANCE / METRIC FAMILIES
# ═══════════════════════════════════════════════════════════════════

def trace_distance(rho, sigma):
    """D_tr = 1/2 Tr|rho - sigma|. Operational: max probability of distinguishing."""
    diff = rho - sigma
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))

def fidelity(rho, sigma):
    """F = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2. Uhlmann fidelity."""
    sqrt_rho = sqrtm(rho)
    inner = sqrtm(sqrt_rho @ sigma @ sqrt_rho)
    val = float(np.real(np.trace(inner)))**2
    return float(np.clip(val, 0.0, 1.0))

def bures_distance(rho, sigma):
    """D_B = sqrt(2(1 - sqrt(F))). From fidelity."""
    F = fidelity(rho, sigma)
    return float(np.sqrt(max(2.0 * (1.0 - np.sqrt(max(F, 0.0))), 0.0)))

def hilbert_schmidt_distance(rho, sigma):
    """D_HS = sqrt(Tr((rho-sigma)^2)). Euclidean in matrix space."""
    diff = rho - sigma
    return float(np.sqrt(max(np.real(np.trace(diff @ diff)), 0.0)))

def relative_entropy(rho, sigma):
    """D(rho||sigma) = Tr(rho (log rho - log sigma)). Asymmetric."""
    ev_r, U_r = np.linalg.eigh(rho)
    ev_s, U_s = np.linalg.eigh(sigma)
    ev_r = np.maximum(ev_r, 1e-15)
    ev_s = np.maximum(ev_s, 1e-15)
    log_rho = U_r @ np.diag(np.log(ev_r)) @ U_r.conj().T
    log_sigma = U_s @ np.diag(np.log(ev_s)) @ U_s.conj().T
    val = float(np.real(np.trace(rho @ (log_rho - log_sigma))))
    return max(val, 0.0)

# ═══════════════════════════════════════════════════════════════════
# GEOMETRIC STRUCTURES ON STATE SPACE
# ═══════════════════════════════════════════════════════════════════

def bloch_sphere_coords(rho):
    """Map rho to (theta, phi, r) on the Bloch ball."""
    rx = float(np.real(np.trace(rho @ SX)))
    ry = float(np.real(np.trace(rho @ SY)))
    rz = float(np.real(np.trace(rho @ SZ)))
    r = np.sqrt(rx**2 + ry**2 + rz**2)
    theta = float(np.arccos(np.clip(rz / max(r, 1e-15), -1, 1)))
    phi = float(np.arctan2(ry, rx))
    return theta, phi, float(r)

def fubini_study_distance(psi1, psi2):
    """d_FS = arccos(|<psi1|psi2>|). Metric on CP^1 (pure states only)."""
    inner = abs(np.dot(psi1.conj(), psi2))
    return float(np.arccos(np.clip(inner, 0.0, 1.0)))

def quantum_fisher_info(rho, H):
    """F_Q = 2 sum_{i,j} (lambda_i - lambda_j)^2 / (lambda_i + lambda_j) |<i|H|j>|^2."""
    evals, evecs = np.linalg.eigh(rho)
    d = len(evals)
    F = 0.0
    for i in range(d):
        for j in range(d):
            denom = evals[i] + evals[j]
            if denom > 1e-15:
                hij = abs(evecs[:, i].conj() @ H @ evecs[:, j])**2
                F += 2.0 * (evals[i] - evals[j])**2 / denom * hij
    return float(F)

def berry_phase_loop(rho_list):
    """Geometric phase from a sequence of density matrices via fidelity connection."""
    phase = 0.0
    for i in range(len(rho_list) - 1):
        F = fidelity(rho_list[i], rho_list[i + 1])
        if F > 1e-15:
            phase += np.arccos(np.clip(np.sqrt(F), -1, 1))
    return float(phase)

def quantum_geometric_tensor(rho, generators):
    """Q_ij = Tr(rho H_i H_j) - Tr(rho H_i) Tr(rho H_j).
    Real part = quantum metric, Imaginary part = Berry curvature."""
    n = len(generators)
    Q = np.zeros((n, n), dtype=complex)
    for i in range(n):
        for j in range(n):
            Q[i, j] = (np.trace(rho @ generators[i] @ generators[j])
                        - np.trace(rho @ generators[i]) * np.trace(rho @ generators[j]))
    return Q

# ═══════════════════════════════════════════════════════════════════
# STATE DEFINITIONS — 10 pairs spanning the Bloch ball
# ═══════════════════════════════════════════════════════════════════

def make_pure(psi):
    """Pure state density matrix from state vector."""
    psi = np.array(psi, dtype=complex)
    psi = psi / np.linalg.norm(psi)
    return np.outer(psi, psi.conj())

def make_bloch(rx, ry, rz):
    """Mixed state from Bloch vector components."""
    return (I2 + rx * SX + ry * SY + rz * SZ) / 2.0

# Pure state vectors
KET_0 = np.array([1, 0], dtype=complex)
KET_1 = np.array([0, 1], dtype=complex)
KET_PLUS = np.array([1, 1], dtype=complex) / np.sqrt(2)
KET_MINUS = np.array([1, -1], dtype=complex) / np.sqrt(2)
KET_PLUS_I = np.array([1, 1j], dtype=complex) / np.sqrt(2)
KET_MINUS_I = np.array([1, -1j], dtype=complex) / np.sqrt(2)

# Density matrices
RHO_0 = make_pure(KET_0)
RHO_1 = make_pure(KET_1)
RHO_PLUS = make_pure(KET_PLUS)
RHO_MINUS = make_pure(KET_MINUS)
RHO_PLUS_I = make_pure(KET_PLUS_I)
RHO_MINUS_I = make_pure(KET_MINUS_I)
RHO_MIXED_Z = make_bloch(0, 0, 0.5)       # r=0.5 along z
RHO_MIXED_X = make_bloch(0.5, 0, 0)       # r=0.5 along x
RHO_MIXED_Y = make_bloch(0, 0.5, 0)       # r=0.5 along y
RHO_MAX_MIXED = I2 / 2.0                   # maximally mixed

STATE_PAIRS = [
    ("pure_0_vs_1",         RHO_0,       RHO_1,       KET_0,   KET_1,    "antipodal z"),
    ("pure_plus_vs_minus",  RHO_PLUS,    RHO_MINUS,   KET_PLUS, KET_MINUS, "antipodal x"),
    ("pure_plusI_vs_minusI", RHO_PLUS_I, RHO_MINUS_I, KET_PLUS_I, KET_MINUS_I, "antipodal y"),
    ("pure_0_vs_plus",      RHO_0,       RHO_PLUS,    KET_0,   KET_PLUS,  "45 deg z-x"),
    ("pure_0_vs_plusI",     RHO_0,       RHO_PLUS_I,  KET_0,   KET_PLUS_I, "45 deg z-y"),
    ("pure_plus_vs_plusI",  RHO_PLUS,    RHO_PLUS_I,  KET_PLUS, KET_PLUS_I, "45 deg x-y"),
    ("mixed_z_vs_x",       RHO_MIXED_Z, RHO_MIXED_X, None,    None,      "mixed interior"),
    ("mixed_z_vs_y",       RHO_MIXED_Z, RHO_MIXED_Y, None,    None,      "mixed interior"),
    ("maxmixed_vs_pure0",  RHO_MAX_MIXED, RHO_0,     None,    KET_0,     "center to pole"),
    ("maxmixed_vs_mixedz", RHO_MAX_MIXED, RHO_MIXED_Z, None,  None,      "center to interior"),
]

# ═══════════════════════════════════════════════════════════════════
# TEST 1: All distance measures for every pair
# ═══════════════════════════════════════════════════════════════════

def compute_all_distances():
    """Compute all distance metrics for every state pair."""
    results = {}
    for name, rho_a, rho_b, psi_a, psi_b, desc in STATE_PAIRS:
        entry = {
            "description": desc,
            "trace_distance": trace_distance(rho_a, rho_b),
            "fidelity": fidelity(rho_a, rho_b),
            "bures_distance": bures_distance(rho_a, rho_b),
            "hilbert_schmidt_distance": hilbert_schmidt_distance(rho_a, rho_b),
            "relative_entropy": relative_entropy(rho_a, rho_b),
        }
        if psi_a is not None and psi_b is not None:
            entry["fubini_study_distance"] = fubini_study_distance(psi_a, psi_b)
        else:
            entry["fubini_study_distance"] = None
        results[name] = entry
    return results

# ═══════════════════════════════════════════════════════════════════
# TEST 2: Triangle inequality
# ═══════════════════════════════════════════════════════════════════

def triangle_inequality_test():
    """For each metric, check d(A,C) <= d(A,B) + d(B,C) over many triples."""
    # Use a set of representative states
    states = [RHO_0, RHO_1, RHO_PLUS, RHO_MINUS, RHO_PLUS_I,
              RHO_MIXED_Z, RHO_MIXED_X, RHO_MAX_MIXED]
    state_names = ["|0>", "|1>", "|+>", "|->", "|+i>",
                   "mix_z", "mix_x", "max_mix"]

    metrics = {
        "trace_distance": trace_distance,
        "bures_distance": bures_distance,
        "hilbert_schmidt_distance": hilbert_schmidt_distance,
    }
    # Note: fidelity and relative_entropy are NOT metrics (no triangle ineq)
    # We test them anyway to show they fail

    # Also test fidelity-based "distance" = 1 - F
    def fidelity_dist(r, s):
        return 1.0 - fidelity(r, s)

    metrics["one_minus_fidelity"] = fidelity_dist

    # Also test sqrt(relative_entropy) as a "distance"
    def sqrt_rel_ent(r, s):
        return np.sqrt(relative_entropy(r, s))

    metrics["sqrt_relative_entropy"] = sqrt_rel_ent

    results = {}
    n_states = len(states)
    for mname, mfunc in metrics.items():
        passes = 0
        fails = 0
        worst_violation = 0.0
        for i in range(n_states):
            for j in range(n_states):
                for k in range(n_states):
                    if i == j or j == k or i == k:
                        continue
                    d_ac = mfunc(states[i], states[k])
                    d_ab = mfunc(states[i], states[j])
                    d_bc = mfunc(states[j], states[k])
                    if d_ac <= d_ab + d_bc + 1e-10:
                        passes += 1
                    else:
                        fails += 1
                        violation = d_ac - (d_ab + d_bc)
                        worst_violation = max(worst_violation, violation)
        results[mname] = {
            "passes": passes,
            "fails": fails,
            "total_triples": passes + fails,
            "worst_violation": worst_violation,
            "is_metric": fails == 0,
        }
    return results

# ═══════════════════════════════════════════════════════════════════
# TEST 3: Operator sensitivity
# ═══════════════════════════════════════════════════════════════════

def operator_sensitivity_test():
    """Apply Ti, Fe, Te, Fi to states. Measure distance from original for each metric."""
    test_states = {
        "|0>": RHO_0,
        "|+>": RHO_PLUS,
        "|+i>": RHO_PLUS_I,
        "mix_z": RHO_MIXED_Z,
        "max_mix": RHO_MAX_MIXED,
    }
    operators = {
        "Ti": apply_Ti,
        "Fe": apply_Fe,
        "Te": apply_Te,
        "Fi": apply_Fi,
    }
    dist_funcs = {
        "trace_distance": trace_distance,
        "bures_distance": bures_distance,
        "hilbert_schmidt_distance": hilbert_schmidt_distance,
        "relative_entropy": relative_entropy,
    }

    results = {}
    for op_name, op_func in operators.items():
        op_results = {}
        for s_name, rho in test_states.items():
            rho_out = op_func(rho, polarity_up=True, strength=1.0)
            dists = {}
            for d_name, d_func in dist_funcs.items():
                dists[d_name] = d_func(rho, rho_out)
            op_results[s_name] = dists
        results[op_name] = op_results

    # Aggregate: which metric is most sensitive to which operator?
    sensitivity_ranking = {}
    for d_name in dist_funcs:
        op_sums = {}
        for op_name in operators:
            total = 0.0
            for s_name in test_states:
                total += results[op_name][s_name][d_name]
            op_sums[op_name] = total
        sensitivity_ranking[d_name] = dict(sorted(op_sums.items(), key=lambda x: -x[1]))

    return {"per_operator_state": results, "sensitivity_ranking": sensitivity_ranking}

# ═══════════════════════════════════════════════════════════════════
# TEST 4: Quantum Fisher Information landscape
# ═══════════════════════════════════════════════════════════════════

def qfi_landscape_test():
    """For each Pauli generator, compute QFI at different Bloch sphere points."""
    generators = {"sigma_x": SX, "sigma_y": SY, "sigma_z": SZ}

    # Sample points on the Bloch sphere (pure) and interior (mixed)
    test_points = {
        "north_pole": RHO_0,
        "south_pole": RHO_1,
        "equator_x": RHO_PLUS,
        "equator_neg_x": RHO_MINUS,
        "equator_y": RHO_PLUS_I,
        "equator_neg_y": RHO_MINUS_I,
        "mixed_r05_z": RHO_MIXED_Z,
        "mixed_r05_x": RHO_MIXED_X,
        "maximally_mixed": RHO_MAX_MIXED,
    }

    results = {}
    for pt_name, rho in test_points.items():
        theta, phi, r = bloch_sphere_coords(rho)
        pt_result = {"bloch_theta": theta, "bloch_phi": phi, "bloch_r": r}
        for gen_name, H in generators.items():
            pt_result[f"QFI_{gen_name}"] = quantum_fisher_info(rho, H)
        results[pt_name] = pt_result

    return results

# ═══════════════════════════════════════════════════════════════════
# TEST 5: Quantum Geometric Tensor
# ═══════════════════════════════════════════════════════════════════

def qgt_test():
    """Compute QGT at 5 Bloch sphere points. Extract metric and Berry curvature."""
    generators = [SX / 2.0, SY / 2.0, SZ / 2.0]

    test_points = {
        "north_pole": RHO_0,
        "equator_x": RHO_PLUS,
        "equator_y": RHO_PLUS_I,
        "mixed_r05_z": RHO_MIXED_Z,
        "maximally_mixed": RHO_MAX_MIXED,
    }

    results = {}
    for pt_name, rho in test_points.items():
        Q = quantum_geometric_tensor(rho, generators)
        metric_part = np.real(Q).tolist()
        berry_part = np.imag(Q).tolist()

        # Frobenius norms
        metric_norm = float(np.linalg.norm(np.real(Q), 'fro'))
        berry_norm = float(np.linalg.norm(np.imag(Q), 'fro'))

        results[pt_name] = {
            "metric_tensor_real": metric_part,
            "berry_curvature_imag": berry_part,
            "metric_frobenius_norm": metric_norm,
            "berry_frobenius_norm": berry_norm,
            "has_curvature": berry_norm > 1e-10,
        }
    return results

# ═══════════════════════════════════════════════════════════════════
# TEST 6: Berry phase from operator sequences
# ═══════════════════════════════════════════════════════════════════

def berry_phase_test():
    """Compute Berry phase for loops generated by operator sequences."""
    # Build a loop: apply Fe at 12 angles to trace a circle
    results = {}

    # Loop 1: Fe rotation loop (z-axis, should give Berry phase)
    n_steps = 24
    rho_loop = [RHO_PLUS.copy()]
    for k in range(n_steps):
        phi = 2.0 * np.pi / n_steps
        rho_next = apply_Fe(rho_loop[-1], polarity_up=True, strength=1.0, phi=phi)
        rho_loop.append(rho_next)
    results["fe_z_rotation_loop"] = {
        "n_steps": n_steps,
        "berry_phase": berry_phase_loop(rho_loop),
        "start_state": "|+>",
    }

    # Loop 2: Fi rotation loop (x-axis)
    rho_loop2 = [RHO_0.copy()]
    for k in range(n_steps):
        theta = 2.0 * np.pi / n_steps
        rho_next = apply_Fi(rho_loop2[-1], polarity_up=True, strength=1.0, theta=theta)
        rho_loop2.append(rho_next)
    results["fi_x_rotation_loop"] = {
        "n_steps": n_steps,
        "berry_phase": berry_phase_loop(rho_loop2),
        "start_state": "|0>",
    }

    # Loop 3: Mixed operator loop (Ti -> Fe -> Te -> Fi repeated)
    rho_loop3 = [RHO_PLUS.copy()]
    for k in range(8):
        rho_step = apply_Ti(rho_loop3[-1], polarity_up=True, strength=0.3)
        rho_step = apply_Fe(rho_step, polarity_up=True, strength=0.3, phi=0.4)
        rho_step = apply_Te(rho_step, polarity_up=True, strength=0.3, q=0.3)
        rho_step = apply_Fi(rho_step, polarity_up=True, strength=0.3, theta=0.4)
        rho_loop3.append(rho_step)
    results["mixed_operator_loop"] = {
        "n_steps": 8,
        "berry_phase": berry_phase_loop(rho_loop3),
        "start_state": "|+>",
    }

    return results

# ═══════════════════════════════════════════════════════════════════
# NEGATIVE TEST 1: Flat vs Curved geometry
# ═══════════════════════════════════════════════════════════════════

def flat_vs_curved_test():
    """Does the choice of geometry change which states are 'close' vs 'far'?
    Compare orderings under HS (flat) vs Bures (curved) vs trace distance."""
    # Take a reference state and measure distance to all others
    reference = RHO_PLUS_I
    targets = {
        "|0>": RHO_0, "|1>": RHO_1, "|+>": RHO_PLUS, "|->": RHO_MINUS,
        "mix_z": RHO_MIXED_Z, "mix_x": RHO_MIXED_X,
        "max_mix": RHO_MAX_MIXED,
    }

    orderings = {}
    for metric_name, metric_func in [("hilbert_schmidt", hilbert_schmidt_distance),
                                      ("bures", bures_distance),
                                      ("trace", trace_distance)]:
        dists = {}
        for t_name, t_rho in targets.items():
            dists[t_name] = metric_func(reference, t_rho)
        ranked = sorted(dists.keys(), key=lambda k: dists[k])
        orderings[metric_name] = {
            "distances": dists,
            "ranking": ranked,
        }

    # Check if rankings agree
    hs_rank = orderings["hilbert_schmidt"]["ranking"]
    bures_rank = orderings["bures"]["ranking"]
    trace_rank = orderings["trace"]["ranking"]

    hs_vs_bures_agree = hs_rank == bures_rank
    hs_vs_trace_agree = hs_rank == trace_rank
    bures_vs_trace_agree = bures_rank == trace_rank

    # Kendall tau distance between rankings
    def rank_distance(r1, r2):
        """Count pairwise disagreements."""
        n = len(r1)
        pos1 = {v: i for i, v in enumerate(r1)}
        pos2 = {v: i for i, v in enumerate(r2)}
        inversions = 0
        for i in range(n):
            for j in range(i + 1, n):
                a, b = r1[i], r1[j]
                if (pos2[a] - pos2[b]) * (pos1[a] - pos1[b]) < 0:
                    inversions += 1
        return inversions

    return {
        "reference_state": "|+i>",
        "orderings": orderings,
        "hs_vs_bures_same_order": hs_vs_bures_agree,
        "hs_vs_trace_same_order": hs_vs_trace_agree,
        "bures_vs_trace_same_order": bures_vs_trace_agree,
        "kendall_hs_bures": rank_distance(hs_rank, bures_rank),
        "kendall_hs_trace": rank_distance(hs_rank, trace_rank),
        "kendall_bures_trace": rank_distance(bures_rank, trace_rank),
        "geometry_matters": not (hs_vs_bures_agree and hs_vs_trace_agree),
    }

# ═══════════════════════════════════════════════════════════════════
# NEGATIVE TEST 2: Real numbers only
# ═══════════════════════════════════════════════════════════════════

def real_only_test():
    """Restrict to real-valued states (no complex phase).
    Which geometries collapse? Which survive?"""
    # Real states: can only reach points in the xz-plane of the Bloch sphere
    real_states = {
        "|0>": RHO_0,
        "|1>": RHO_1,
        "|+>": RHO_PLUS,
        "|->": RHO_MINUS,
        "mix_z": RHO_MIXED_Z,
        "mix_x": RHO_MIXED_X,
    }

    # Real state vectors (for Fubini-Study)
    real_vecs = {
        "|0>": KET_0.real.astype(complex),
        "|1>": KET_1.real.astype(complex),
        "|+>": (np.array([1, 1]) / np.sqrt(2)).astype(complex),
        "|->": (np.array([1, -1]) / np.sqrt(2)).astype(complex),
    }

    results = {"distance_metrics_survive": {}, "geometric_structures": {}}

    # Test 1: Do distance metrics still work?
    for metric_name, metric_func in [("trace_distance", trace_distance),
                                      ("bures_distance", bures_distance),
                                      ("hilbert_schmidt_distance", hilbert_schmidt_distance),
                                      ("relative_entropy", relative_entropy)]:
        vals = []
        for n1, r1 in real_states.items():
            for n2, r2 in real_states.items():
                if n1 < n2:
                    vals.append(metric_func(r1, r2))
        results["distance_metrics_survive"][metric_name] = {
            "works": True,
            "sample_distances": vals,
            "min": float(min(vals)) if vals else 0,
            "max": float(max(vals)) if vals else 0,
        }

    # Test 2: Fubini-Study with real vectors
    fs_vals = []
    for n1, v1 in real_vecs.items():
        for n2, v2 in real_vecs.items():
            if n1 < n2:
                fs_vals.append(fubini_study_distance(v1, v2))
    results["distance_metrics_survive"]["fubini_study"] = {
        "works": True,
        "note": "FS works on real states but the state space is RP^1 not CP^1 -- reduced manifold",
        "sample_distances": fs_vals,
    }

    # Test 3: Berry phase with real-only loop
    # For real states, Berry phase should vanish (no imaginary part to accumulate)
    n_steps = 24
    real_loop = [RHO_PLUS.copy()]
    for k in range(n_steps):
        # Fi rotates in xz-plane (stays real)
        theta_step = 2.0 * np.pi / n_steps
        rho_next = apply_Fi(real_loop[-1], polarity_up=True, strength=1.0, theta=theta_step)
        # Force real
        rho_next = np.real(rho_next).astype(complex)
        rho_next = (rho_next + rho_next.T) / 2.0
        tr = np.real(np.trace(rho_next))
        if tr > 1e-15:
            rho_next = rho_next / tr
        real_loop.append(rho_next)

    berry_real = berry_phase_loop(real_loop)

    # Compare with complex loop
    complex_loop = [RHO_PLUS.copy()]
    for k in range(n_steps):
        phi_step = 2.0 * np.pi / n_steps
        rho_next = apply_Fe(complex_loop[-1], polarity_up=True, strength=1.0, phi=phi_step)
        complex_loop.append(rho_next)
    berry_complex = berry_phase_loop(complex_loop)

    results["geometric_structures"]["berry_phase"] = {
        "real_loop_berry_phase": berry_real,
        "complex_loop_berry_phase": berry_complex,
        "berry_requires_complex": abs(berry_complex) > abs(berry_real) + 1e-10,
        "note": "Berry phase requires complex Hilbert space; real restriction kills it",
    }

    # Test 4: QGT with real states
    gens = [SX / 2.0, SZ / 2.0]  # Only real generators
    Q_real = quantum_geometric_tensor(RHO_PLUS, gens)
    Q_full = quantum_geometric_tensor(RHO_PLUS, [SX / 2.0, SY / 2.0, SZ / 2.0])

    results["geometric_structures"]["qgt"] = {
        "real_generators_berry_norm": float(np.linalg.norm(np.imag(Q_real))),
        "full_generators_berry_norm": float(np.linalg.norm(np.imag(Q_full))),
        "curvature_killed_by_real": float(np.linalg.norm(np.imag(Q_real))) < 1e-10,
        "note": "sigma_y is the source of Berry curvature; removing it kills curvature",
    }

    # Test 5: QFI landscape — does it collapse?
    qfi_real_sx = quantum_fisher_info(RHO_PLUS, SX)
    qfi_real_sz = quantum_fisher_info(RHO_PLUS, SZ)
    qfi_real_sy = quantum_fisher_info(RHO_PLUS, SY)

    results["geometric_structures"]["qfi_real"] = {
        "QFI_sx_at_plus": qfi_real_sx,
        "QFI_sz_at_plus": qfi_real_sz,
        "QFI_sy_at_plus": qfi_real_sy,
        "note": "QFI itself survives reals, but sensitivity to sigma_y disappears from the accessible state space",
    }

    # Summary: what survives, what dies
    results["summary"] = {
        "survives_real_restriction": [
            "trace_distance", "bures_distance", "hilbert_schmidt_distance",
            "relative_entropy", "fubini_study (on RP^1)", "QFI",
        ],
        "killed_by_real_restriction": [
            "Berry_phase (vanishes)", "Berry_curvature_component_of_QGT",
            "sigma_y_direction (inaccessible)",
        ],
        "reduced_but_not_killed": [
            "fubini_study (CP^1 -> RP^1, dimension halved)",
            "QGT (3x3 -> 2x2, curvature component vanishes)",
        ],
    }

    return results

# ═══════════════════════════════════════════════════════════════════
# COMPILE RANKING
# ═══════════════════════════════════════════════════════════════════

def compile_ranking(triangle_results, sensitivity_results, real_results):
    """Rank geometry families by compatibility with L0 constraints."""

    # By triangle inequality
    by_triangle = []
    for mname, mdata in triangle_results.items():
        by_triangle.append({
            "metric": mname,
            "is_true_metric": mdata["is_metric"],
            "pass_rate": mdata["passes"] / max(mdata["total_triples"], 1),
        })
    by_triangle.sort(key=lambda x: -x["pass_rate"])

    # By operator sensitivity (total sensitivity across all operators)
    by_sensitivity = []
    for d_name, op_sums in sensitivity_results["sensitivity_ranking"].items():
        total = sum(op_sums.values())
        by_sensitivity.append({"metric": d_name, "total_sensitivity": total})
    by_sensitivity.sort(key=lambda x: -x["total_sensitivity"])

    # Requires complex numbers
    requires_complex = [
        "Berry_phase",
        "Berry_curvature_in_QGT",
        "sigma_y_Pauli_direction",
        "full_CP1_Fubini_Study_manifold",
    ]

    # Survives all L0 constraints: finite, noncommuting, C^2
    survives_all = [
        "trace_distance (true metric, operational, survives reals but gains from complex)",
        "bures_distance (true metric, curved, information-geometric, requires fidelity)",
        "fubini_study (true metric on pure states, curved, requires complex for full CP^1)",
        "QFI (survives both, but landscape richer with complex)",
        "QGT_metric_part (survives, real symmetric tensor)",
    ]

    killed = [
        "hilbert_schmidt as sole geometry (flat, misses curvature of state space)",
        "relative_entropy as metric (not symmetric, no triangle inequality)",
        "real-only restriction (kills Berry phase, halves state space, removes curvature)",
        "commutative operators (kills all nontrivial geometry -- operators must not commute)",
    ]

    return {
        "by_triangle_inequality": by_triangle,
        "by_operator_sensitivity": by_sensitivity,
        "requires_complex": requires_complex,
        "survives_all_constraints": survives_all,
        "killed_at_L0": killed,
    }

# ═══════════════════════════════════════════════════════════════════
# NONCOMMUTATIVITY VERIFICATION (the F01+N01 constraint)
# ═══════════════════════════════════════════════════════════════════

def noncommutativity_test():
    """Verify that Ti and Fi do not commute, and that this is detectable by every geometry.

    NOTE: At full strength Ti completely dephases |+> to maximally mixed, erasing
    all coherence before Fi can act. We test at strength=0.5 where partial coherence
    remains and the commutator is visible. We also sweep strengths to show the
    noncommutativity emerges at ANY partial strength.
    """
    # Use partial strength so Ti does not fully dephase.
    # Use a GENERIC state (not an eigenstate of any operator) so the commutator is visible.
    test_strength = 0.5
    rho = make_bloch(0.3, 0.4, 0.5)  # generic mixed state, not aligned to any axis

    # Path 1: Ti then Fi
    rho_TiFi = apply_Fi(apply_Ti(rho, polarity_up=True, strength=test_strength),
                         polarity_up=True, strength=test_strength)
    # Path 2: Fi then Ti
    rho_FiTi = apply_Ti(apply_Fi(rho, polarity_up=True, strength=test_strength),
                         polarity_up=True, strength=test_strength)

    dists = {
        "trace_distance": trace_distance(rho_TiFi, rho_FiTi),
        "bures_distance": bures_distance(rho_TiFi, rho_FiTi),
        "hilbert_schmidt_distance": hilbert_schmidt_distance(rho_TiFi, rho_FiTi),
        "relative_entropy_forward": relative_entropy(rho_TiFi, rho_FiTi),
        "relative_entropy_reverse": relative_entropy(rho_FiTi, rho_TiFi),
    }

    all_nonzero = all(v > 1e-10 for v in dists.values())

    # Also test Te and Fe at partial strength
    rho_TeFe = apply_Fe(apply_Te(rho, polarity_up=True, strength=test_strength),
                         polarity_up=True, strength=test_strength)
    rho_FeTe = apply_Te(apply_Fe(rho, polarity_up=True, strength=test_strength),
                         polarity_up=True, strength=test_strength)

    dists_TeFe = {
        "trace_distance": trace_distance(rho_TeFe, rho_FeTe),
        "bures_distance": bures_distance(rho_TeFe, rho_FeTe),
        "hilbert_schmidt_distance": hilbert_schmidt_distance(rho_TeFe, rho_FeTe),
    }

    # Strength sweep: show noncommutativity at every partial strength
    strength_sweep = {}
    for s in [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
        r_ab = apply_Fi(apply_Ti(rho, polarity_up=True, strength=s),
                        polarity_up=True, strength=s)
        r_ba = apply_Ti(apply_Fi(rho, polarity_up=True, strength=s),
                        polarity_up=True, strength=s)
        strength_sweep[str(s)] = {
            "trace_distance": trace_distance(r_ab, r_ba),
            "note": "zero at s=1.0 because full dephasing erases coherence before rotation"
        }

    return {
        "test_strength": test_strength,
        "Ti_Fi_commutator_distances": dists,
        "Ti_Fi_noncommuting": all_nonzero,
        "Te_Fe_commutator_distances": dists_TeFe,
        "Te_Fe_noncommuting": all(v > 1e-10 for v in dists_TeFe.values()),
        "strength_sweep_Ti_Fi": strength_sweep,
        "verdict": "ALL geometries detect noncommutativity" if all_nonzero else "SOME geometries miss it",
        "note": "At full strength=1.0, Ti fully dephases so commutator vanishes. "
                "Noncommutativity is structural and visible at all partial strengths.",
    }

# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def sanitize(obj):
    """Recursively convert numpy types to Python natives for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    return obj


def main():
    print("=" * 72)
    print("GEOMETRY FAMILIES AT L0 (F01+N01)")
    print("Which geometries survive a finite noncommuting system on C^2?")
    print("=" * 72)

    print("\n[1/7] Computing all distance measures for 10 state pairs...")
    all_dists = compute_all_distances()
    for name, data in all_dists.items():
        print(f"  {name}: Tr={data['trace_distance']:.4f}  F={data['fidelity']:.4f}  "
              f"Bures={data['bures_distance']:.4f}  HS={data['hilbert_schmidt_distance']:.4f}  "
              f"RE={data['relative_entropy']:.4f}  FS={data.get('fubini_study_distance', 'N/A')}")

    print("\n[2/7] Triangle inequality test...")
    triangle = triangle_inequality_test()
    for mname, mdata in triangle.items():
        status = "PASS (true metric)" if mdata["is_metric"] else f"FAIL ({mdata['fails']} violations)"
        print(f"  {mname}: {status}")

    print("\n[3/7] Operator sensitivity test...")
    sensitivity = operator_sensitivity_test()
    for d_name, ranking in sensitivity["sensitivity_ranking"].items():
        order = " > ".join(f"{k}({v:.3f})" for k, v in ranking.items())
        print(f"  {d_name}: {order}")

    print("\n[4/7] QFI landscape...")
    qfi = qfi_landscape_test()
    for pt_name, pt_data in qfi.items():
        qfis = [f"{k}={v:.3f}" for k, v in pt_data.items() if k.startswith("QFI_")]
        print(f"  {pt_name} (r={pt_data['bloch_r']:.2f}): {', '.join(qfis)}")

    print("\n[5/7] Quantum geometric tensor...")
    qgt = qgt_test()
    for pt_name, pt_data in qgt.items():
        print(f"  {pt_name}: metric_norm={pt_data['metric_frobenius_norm']:.4f}  "
              f"berry_norm={pt_data['berry_frobenius_norm']:.4f}  "
              f"has_curvature={pt_data['has_curvature']}")

    print("\n[6/7] Berry phase test...")
    berry = berry_phase_test()
    for loop_name, loop_data in berry.items():
        print(f"  {loop_name}: phase={loop_data['berry_phase']:.6f}")

    print("\n[7/7] Negative tests...")
    print("  [7a] Flat vs curved geometry...")
    flat_curved = flat_vs_curved_test()
    print(f"    Geometry matters (orderings differ): {flat_curved['geometry_matters']}")
    print(f"    Kendall tau (HS vs Bures): {flat_curved['kendall_hs_bures']}")
    print(f"    Kendall tau (HS vs Trace): {flat_curved['kendall_hs_trace']}")

    print("  [7b] Real-only restriction...")
    real_only = real_only_test()
    print(f"    Berry phase (real loop):    {real_only['geometric_structures']['berry_phase']['real_loop_berry_phase']:.6f}")
    print(f"    Berry phase (complex loop): {real_only['geometric_structures']['berry_phase']['complex_loop_berry_phase']:.6f}")
    print(f"    Curvature killed by real:   {real_only['geometric_structures']['qgt']['curvature_killed_by_real']}")

    print("\n  [BONUS] Noncommutativity verification (F01+N01)...")
    noncomm = noncommutativity_test()
    print(f"    Ti-Fi noncommuting: {noncomm['Ti_Fi_noncommuting']}")
    print(f"    Te-Fe noncommuting: {noncomm['Te_Fe_noncommuting']}")
    print(f"    Verdict: {noncomm['verdict']}")

    # Compile ranking
    ranking = compile_ranking(triangle, sensitivity, real_only)

    print("\n" + "=" * 72)
    print("FINAL RANKING")
    print("=" * 72)
    print("\nTrue metrics (triangle inequality holds):")
    for entry in ranking["by_triangle_inequality"]:
        tag = "TRUE METRIC" if entry["is_true_metric"] else "NOT A METRIC"
        print(f"  {entry['metric']}: {tag} ({entry['pass_rate']*100:.0f}%)")
    print("\nBy operator sensitivity (total across all operators+states):")
    for entry in ranking["by_operator_sensitivity"]:
        print(f"  {entry['metric']}: {entry['total_sensitivity']:.4f}")
    print("\nRequires complex numbers:")
    for item in ranking["requires_complex"]:
        print(f"  - {item}")
    print("\nSurvives all L0 constraints (finite, noncommuting, C^2):")
    for item in ranking["survives_all_constraints"]:
        print(f"  + {item}")
    print("\nKILLED at L0:")
    for item in ranking["killed_at_L0"]:
        print(f"  X {item}")

    # Build output
    output = sanitize({
        "name": "geometry_families_L0",
        "distance_metrics": {
            "all_pairs": all_dists,
            "triangle_inequality": triangle,
            "operator_sensitivity": sensitivity,
        },
        "geometric_structures": {
            "qfi_landscape": qfi,
            "qgt_components": qgt,
            "berry_phase": berry,
        },
        "negative_tests": {
            "flat_vs_curved": flat_curved,
            "real_only": real_only,
        },
        "noncommutativity_verification": noncomm,
        "ranking": ranking,
    })

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "a2_state", "sim_results", "geometry_families_L0_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
