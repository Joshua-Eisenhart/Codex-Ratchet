#!/usr/bin/env python3
"""
Missing Axis Search
====================

If Ax1 ≈ Ax5 (overlap 0.9997), we have 6 independent axes, not 7.
Is there a 7th axis hiding in the system?

METHOD:
  1. Build displacement vectors for the 6 verified-distinct axes
  2. Generate many random quantum operations (channels, unitaries, measurements)
  3. For each, compute its displacement and project out the 6 known components
  4. Measure the RESIDUAL — the part not explained by known axes
  5. If residuals are consistently large, there's a missing axis
  6. Use PCA on the residuals to find its structure

KNOWN 6 AXES (after Ax1/Ax5 merge):
  Ax0: coarse/fine (fiber averaging)
  Ax1=5: dissipation class (CPTP vs Unitary / FGA vs FSA) ← MERGED
  Ax2: boundary (Eulerian vs Lagrangian)
  Ax3: chirality (Hopf fiber phase e^{±iθ})
  Ax4: composition order (B∘A vs A∘B)
  Ax6: action side (Aρ vs ρA)

CANDIDATES FOR 7th AXIS:
  - Entanglement structure (system-environment)
  - Measurement basis choice
  - Operator strength / coupling constant
  - Coherence class (off-diagonal structure)
  - Berry phase sign
  - Spectral gap
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from proto_ratchet_sim_runner import make_random_density_matrix
except ImportError:
    def make_random_density_matrix(d):
        A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        rho = A @ A.conj().T
        return rho / np.trace(rho)


def ensure_valid(rho):
    """Project to valid density matrix."""
    rho = (rho + rho.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0)
    rho = evecs @ np.diag(evals) @ evecs.conj().T
    tr = np.trace(rho)
    if abs(tr) > 1e-12:
        rho /= tr
    return rho


# ═══════════════════════════════════════════════════════════════════
# THE 6 KNOWN AXIS DISPLACEMENTS (using best formulations)
# ═══════════════════════════════════════════════════════════════════

def get_axis_displacements(rho, d):
    """Return 6 displacement matrices for the known axes."""
    displacements = []
    
    # Ax0: coarse/fine (partial dephasing)
    diag = np.diag(np.diag(rho))
    d0 = (0.2 * rho + 0.8 * diag) - (0.8 * rho + 0.2 * diag)  # coarse − fine
    displacements.append(d0)
    
    # Ax1=5 (merged): CPTP vs Unitary
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2
    U = la.expm(-1j * H * 0.3)
    rho_uni = U @ rho @ U.conj().T
    L = np.zeros((d, d), dtype=complex)
    for k in range(d-1):
        L[k, k+1] = 0.3
    lind = L @ rho @ L.conj().T - 0.5 * (L.conj().T @ L @ rho + rho @ L.conj().T @ L)
    rho_cptp = ensure_valid(rho + lind * 0.3)
    d15 = rho_cptp - rho_uni
    displacements.append(d15)
    
    # Ax2: boundary (Eulerian vs Lagrangian)
    P = np.eye(d, dtype=complex)
    P[d-1, d-1] = 0.7
    rho_euler = ensure_valid(P @ rho @ P.conj().T)
    H2 = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H2 = (H2 + H2.conj().T) / 2
    U2 = la.expm(-1j * H2 * 0.5)
    rho_lagr = U2 @ rho @ U2.conj().T
    d2 = rho_euler - rho_lagr
    displacements.append(d2)
    
    # Ax3: chirality via Hopf fiber phase (the CORRECT formulation)
    theta = 0.4
    phase_p = np.exp(1j * theta) * np.eye(d)
    phase_m = np.exp(-1j * theta) * np.eye(d)
    d3 = (phase_p @ rho @ phase_p.conj().T) - (phase_m @ rho @ phase_m.conj().T)
    displacements.append(d3)
    
    # Ax4: composition order (B∘A vs A∘B)
    def map_A(r):
        return 0.7 * r + 0.3 * np.diag(np.diag(r))
    gamma = 0.2
    K0 = np.eye(d, dtype=complex)
    K1 = np.zeros((d, d), dtype=complex)
    for k in range(1, d):
        K0[k, k] = np.sqrt(1 - gamma)
        K1[k-1, k] = np.sqrt(gamma)
    def map_B(r):
        out = K0 @ r @ K0.conj().T + K1 @ r @ K1.conj().T
        return out / max(abs(np.trace(out)), 1e-12)
    d4 = map_B(map_A(rho)) - map_A(map_B(rho))
    displacements.append(d4)
    
    # Ax6: action side (Aρ − ρA)
    A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    A /= np.linalg.norm(A)
    d6 = A @ rho - rho @ A
    displacements.append(d6)
    
    return displacements


# ═══════════════════════════════════════════════════════════════════
# CANDIDATE 7TH AXIS OPERATIONS
# ═══════════════════════════════════════════════════════════════════

def candidate_displacements(rho, d):
    """Generate displacements from candidate 7th axis operations."""
    candidates = {}
    
    # Candidate A: Measurement basis rotation
    # Apply measurement in computational basis vs Hadamard basis
    proj_z = np.diag(np.diag(rho))  # z-basis measurement
    H_had = np.ones((d, d), dtype=complex) / np.sqrt(d)  # crude Hadamard
    for i in range(d):
        for j in range(d):
            H_had[i, j] *= np.exp(2j * np.pi * i * j / d)
    rho_had = H_had @ rho @ H_had.conj().T
    proj_x = np.diag(np.diag(rho_had))
    proj_x = H_had.conj().T @ proj_x @ H_had  # back to original basis
    candidates["A: measurement_basis"] = proj_z - proj_x
    
    # Candidate B: Operator strength (strong vs weak coupling)
    L = np.zeros((d, d), dtype=complex)
    for k in range(d-1):
        L[k, k+1] = 1.0
    lind_strong = L @ rho @ L.conj().T - 0.5 * (L.conj().T @ L @ rho + rho @ L.conj().T @ L)
    L_weak = L * 0.1
    lind_weak = L_weak @ rho @ L_weak.conj().T - 0.5 * (L_weak.conj().T @ L_weak @ rho + rho @ L_weak.conj().T @ L_weak)
    candidates["B: coupling_strength"] = lind_strong - lind_weak
    
    # Candidate C: Coherence class (off-diagonal vs diagonal)
    rho_diag = np.diag(np.diag(rho))
    rho_offdiag = rho - rho_diag
    candidates["C: coherence_class"] = rho_offdiag  # displacement = off-diagonal part itself
    
    # Candidate D: Spectral gap (how separated the eigenvalues are)
    evals, evecs = np.linalg.eigh(rho)
    # Spread eigenvalues (large gap)
    evals_spread = np.sort(evals)
    if len(evals_spread) >= 2:
        evals_spread[0] = max(evals_spread[0] - 0.1, 0)
        evals_spread[-1] = evals_spread[-1] + 0.1
    evals_spread = np.maximum(evals_spread, 0)
    evals_spread /= sum(evals_spread)
    rho_gapped = evecs @ np.diag(evals_spread) @ evecs.conj().T
    # Compress eigenvalues (small gap)
    evals_flat = np.ones(d) / d
    rho_flat = evecs @ np.diag(evals_flat) @ evecs.conj().T
    candidates["D: spectral_gap"] = rho_gapped - rho_flat
    
    # Candidate E: Entanglement-like structure
    # Partial transpose (simulates entanglement witness)
    rho_pt = rho.T  # transpose = partial transpose for single qudit
    candidates["E: partial_transpose"] = rho - rho_pt
    
    # Candidate F: Phase structure (imaginary part prominence)
    rho_real = np.real(rho).astype(complex)
    rho_imag = 1j * np.imag(rho)
    candidates["F: phase_structure"] = rho_imag  # just the imaginary part
    
    # Candidate G: Squeezing (variance asymmetry between conjugate observables)
    sx = np.zeros((d, d), dtype=complex)
    sz = np.zeros((d, d), dtype=complex)
    for k in range(d-1):
        sx[k, k+1] = 1.0
        sx[k+1, k] = 1.0
    for k in range(d):
        sz[k, k] = (2*k - d + 1) / (d - 1)
    var_x = np.real(np.trace(sx @ sx @ rho) - np.trace(sx @ rho)**2)
    var_z = np.real(np.trace(sz @ sz @ rho) - np.trace(sz @ rho)**2)
    # Squeeze state: reduce variance in one, increase in other
    squeeze_factor = 0.3
    rho_sq = rho + squeeze_factor * (sz @ rho @ sz - rho) * 0.1
    rho_sq = ensure_valid(rho_sq)
    rho_antisq = rho + squeeze_factor * (sx @ rho @ sx - rho) * 0.1
    rho_antisq = ensure_valid(rho_antisq)
    candidates["G: squeezing"] = rho_sq - rho_antisq
    
    return candidates


# ═══════════════════════════════════════════════════════════════════
# RESIDUAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════

def project_out(target, basis_vectors):
    """Project out components along basis vectors. Return residual."""
    residual = target.copy().flatten()
    for b in basis_vectors:
        b_flat = b.flatten()
        norm_b = np.linalg.norm(b_flat)
        if norm_b < 1e-12:
            continue
        b_hat = b_flat / norm_b
        proj = np.dot(residual.conj(), b_hat) * b_hat
        residual = residual - proj
    return residual


def run_missing_axis_search():
    d = 8
    n_trials = 200
    
    print("=" * 70)
    print("MISSING AXIS SEARCH")
    print("=" * 70)
    print(f"\n  Known 6 axes (after Ax1/Ax5 merge)")
    print(f"  Searching for 7th via residual analysis at d={d}")
    
    # For each candidate, measure:
    # 1. Average residual norm after projecting out known 6
    # 2. Overlap with each known axis
    candidate_names = []
    candidate_residuals = []
    candidate_overlaps = {}
    
    axis_labels = ["Ax0", "Ax1=5", "Ax2", "Ax3", "Ax4", "Ax6"]
    
    for trial in range(n_trials):
        np.random.seed(trial + 10000)
        rho = make_random_density_matrix(d)
        
        np.random.seed(trial + 10000)
        known_disps = get_axis_displacements(rho, d)
        
        np.random.seed(trial + 10000)
        cand_disps = candidate_displacements(rho, d)
        
        if trial == 0:
            candidate_names = list(cand_disps.keys())
            candidate_residuals = [0.0] * len(candidate_names)
            for cn in candidate_names:
                candidate_overlaps[cn] = [0.0] * 6
        
        for ci, cn in enumerate(candidate_names):
            cd = cand_disps[cn]
            
            # Measure overlap with each known axis
            cd_norm = np.linalg.norm(cd, 'fro')
            if cd_norm < 1e-12:
                continue
            for ai, ad in enumerate(known_disps):
                ad_norm = np.linalg.norm(ad, 'fro')
                if ad_norm < 1e-12:
                    continue
                ov = abs(np.trace(ad.conj().T @ cd)) / (ad_norm * cd_norm)
                candidate_overlaps[cn][ai] += float(ov)
            
            # Compute residual
            residual = project_out(cd, known_disps)
            residual_frac = np.linalg.norm(residual) / cd_norm
            candidate_residuals[ci] += residual_frac
    
    # Average
    for ci in range(len(candidate_names)):
        candidate_residuals[ci] /= n_trials
    for cn in candidate_names:
        candidate_overlaps[cn] = [v / n_trials for v in candidate_overlaps[cn]]
    
    # Print results
    print(f"\n  {'Candidate':30s} {'Residual':>10s} {'MaxOvl':>8s} {'With':>8s} {'Verdict':>12s}")
    print(f"  {'─'*30} {'─'*10} {'─'*8} {'─'*8} {'─'*12}")
    
    best_candidate = None
    best_residual = 0.0
    
    for ci, cn in enumerate(candidate_names):
        res = candidate_residuals[ci]
        ovls = candidate_overlaps[cn]
        max_ovl = max(ovls)
        max_ax = axis_labels[ovls.index(max_ovl)]
        
        if res > 0.5 and max_ovl < 0.5:
            verdict = "🔥 CANDIDATE"
        elif res > 0.3 and max_ovl < 0.5:
            verdict = "⚠️  POSSIBLE"
        elif res < 0.1:
            verdict = "❌ CAPTURED"
        else:
            verdict = "⚠️  PARTIAL"
        
        print(f"  {cn:30s} {res:10.4f} {max_ovl:8.4f} {max_ax:>8s} {verdict:>12s}")
        
        if res > best_residual:
            best_residual = res
            best_candidate = cn
    
    print(f"\n  HIGHEST RESIDUAL: {best_candidate} ({best_residual:.4f})")
    
    if best_residual > 0.5:
        print(f"  🔥 STRONG CANDIDATE for 7th axis!")
    elif best_residual > 0.3:
        print(f"  ⚠️  Possible candidate, needs further testing")
    else:
        print(f"  ❌ No strong 7th axis candidate found")
        print(f"     The system may genuinely have only 6 independent axes")
    
    # Detailed overlap table for best candidate
    if best_candidate:
        print(f"\n  Overlap breakdown for {best_candidate}:")
        for ai, al in enumerate(axis_labels):
            ov = candidate_overlaps[best_candidate][ai]
            bar = "█" * int(ov * 40)
            print(f"    vs {al:8s}: {ov:.4f}  {bar}")
    
    # Save results
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    
    results = {
        "schema": "MISSING_AXIS_SEARCH_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "d": d,
        "n_trials": n_trials,
        "known_axes": axis_labels,
        "candidates": {
            cn: {
                "residual": candidate_residuals[ci],
                "overlaps": dict(zip(axis_labels, candidate_overlaps[cn])),
            }
            for ci, cn in enumerate(candidate_names)
        },
        "best_candidate": best_candidate,
        "best_residual": best_residual,
    }
    
    out_file = os.path.join(out_dir, "missing_axis_search_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_file}")
    
    return results


if __name__ == "__main__":
    run_missing_axis_search()
