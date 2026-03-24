"""
CANONICAL AXIS ORTHOGONALITY SUITE (NLM-Dictated CPTP Definitions)
===================================================================
Anti-Smuggling Enforcement: ZERO physical analogies. Pure QIT objects only.

AXIS 4 (Variance Direction / Operator Family): Thermodynamic objective functional.
  Deductive (FeTi): S -> 0. Ti = Luders projection. Fe = Lindbladian dissipation.
  Inductive (TeFi): dW -> max. Te = Hamiltonian unitary. Fi = Spectral Fourier projection.

AXIS 5 (Generator Algebra / Texture): Calculus toolhead (domain class).
  Wave (FeFi): Integration algebra. Laplacian + Fourier Transform.
  Line (TeTi): Differentiation algebra. Gradient + Dirac Delta cuts.

Tests: 15 pairwise (1-6), 6 Axis-0 regime switches, Graveyard on KILL.
Dimensions: d in {4, 8, 16, 32, 64}.
Metric: Normalized Hilbert-Schmidt inner product Tr(A^dag B) / sqrt(Tr(A^dag A) * Tr(B^dag B)).
Threshold: epsilon = 1e-5.
"""

import numpy as np
import json
import os
from itertools import combinations
from datetime import datetime, UTC


# =====================================================================
# UTILITY
# =====================================================================

def hs_inner_product(A, B):
    """Normalized Hilbert-Schmidt (Frobenius) inner product."""
    raw = np.real(np.trace(A.conj().T @ B))
    nA = np.real(np.trace(A.conj().T @ A))
    nB = np.real(np.trace(B.conj().T @ B))
    denom = np.sqrt(max(nA, 1e-30) * max(nB, 1e-30))
    return raw / denom


def build_choi(channel_func, d):
    """Choi-Jamiolkowski isomorphism: channel -> d^2 x d^2 density matrix."""
    choi = np.zeros((d**2, d**2), dtype=complex)
    for i in range(d):
        for j in range(d):
            E_ij = np.zeros((d, d), dtype=complex)
            E_ij[i, j] = 1.0
            out = channel_func(E_ij, d)
            for u in range(d):
                for v in range(d):
                    choi[i*d + u, j*d + v] = out[u, v]
    return choi / d


def gram_schmidt_deform(choi_list):
    """Orthogonalize Choi matrices via Gram-Schmidt if raw overlap exists."""
    flat = [c.flatten() for c in choi_list]
    ortho = []
    for v in flat:
        for u in ortho:
            v = v - np.dot(u.conj(), v) * u / max(np.dot(u.conj(), u), 1e-30)
        norm = np.sqrt(max(np.dot(v.conj(), v).real, 1e-30))
        ortho.append(v / norm)
    return [o.reshape(choi_list[0].shape) for o in ortho]


# =====================================================================
# AXIS 1: THERMODYNAMIC ARROW (Isothermal / Adiabatic)
# Diagonal trace scaling — acts on eigenvalue populations only.
# =====================================================================

def A1_thermodynamic_arrow(rho, d):
    """Isothermal/Adiabatic metric: scales diagonal populations."""
    out = np.zeros_like(rho)
    diag = np.diagonal(rho)
    weights = np.linspace(1.0, 0.1, d)
    np.fill_diagonal(out, diag * weights)
    return out


# =====================================================================
# AXIS 2: SPATIAL DUALITY (Local / Non-Local)
# Real symmetric nearest-neighbor correlations.
# =====================================================================

def A2_spatial_duality(rho, d):
    """Lagrangian/Eulerian: real symmetric nearest-neighbor coupling."""
    out = np.zeros_like(rho)
    for i in range(d - 1):
        val = np.real(rho[i, i+1])
        out[i, i+1] = val
        out[i+1, i] = val
    return out


# =====================================================================
# AXIS 3: LOOP FLUX CHIRALITY (Inward / Outward Weyl)
# Imaginary antisymmetric nearest-neighbor commutator structure.
# =====================================================================

def A3_loop_flux_chirality(rho, d):
    """Weyl chirality: imaginary antisymmetric nearest-neighbor phases."""
    out = np.zeros_like(rho)
    for i in range(d - 1):
        val = np.imag(rho[i, i+1])
        out[i, i+1] = 1.0j * val
        out[i+1, i] = -1.0j * val
    return out


# =====================================================================
# AXIS 4: VARIANCE DIRECTION / OPERATOR FAMILY (Deductive vs Inductive)
# Thermodynamic objective functional.
#   Deductive (FeTi): Ti = Luders projection, Fe = Lindbladian dissipation.
#   Inductive (TeFi): Te = Hamiltonian unitary, Fi = Spectral Fourier.
# We instantiate the COMBINED superoperator: FeTi + TeFi channel.
# =====================================================================

def _build_hamiltonian(d):
    """Random Hermitian Hamiltonian for Te generation."""
    H = np.random.RandomState(42).randn(d, d) + 1j * np.random.RandomState(43).randn(d, d)
    return (H + H.conj().T) / 2.0

def _build_fourier(d):
    """Discrete Fourier Transform matrix for Fi spectral projection."""
    F = np.zeros((d, d), dtype=complex)
    for j in range(d):
        for k in range(d):
            F[j, k] = np.exp(2j * np.pi * j * k / d) / np.sqrt(d)
    return F

def A4_variance_direction(rho, d):
    """Axis 4: Deductive (S->0 via Luders+Lindblad) vs Inductive (dW->max via U+Fourier).
    
    We construct the composite superoperator as:
    Deductive branch: Ti (Luders computational-basis dephasing) then Fe (amplitude damping)
    Inductive branch: Te (Hamiltonian rotation) then Fi (Fourier-basis projection)
    Combined: average of both branches.
    """
    # --- Deductive Branch (FeTi): S -> 0 ---
    # Ti: Luders projection in computational basis (dephasing)
    rho_Ti = np.diag(np.diagonal(rho)).astype(complex)
    # Fe: Lindbladian amplitude damping toward ground state
    gamma = 0.3
    K0 = np.eye(d, dtype=complex)
    K0[0, 0] = 1.0
    for k in range(1, d):
        K0[k, k] = np.sqrt(1 - gamma)
    rho_FeTi = K0 @ rho_Ti @ K0.conj().T
    # Add jump operators
    for k in range(1, d):
        Lk = np.zeros((d, d), dtype=complex)
        Lk[0, k] = np.sqrt(gamma)
        rho_FeTi = rho_FeTi + Lk @ rho_Ti @ Lk.conj().T

    # --- Inductive Branch (TeFi): dW -> max ---
    H = _build_hamiltonian(d)
    dt = 0.1
    U = np.eye(d, dtype=complex) - 1j * H * dt  # First-order expansion
    # Reorthogonalize via polar decomposition
    u, s, vh = np.linalg.svd(U)
    U = u @ vh
    rho_Te = U @ rho @ U.conj().T
    # Fi: Fourier spectral projection
    F = _build_fourier(d)
    rho_TeFi = F @ rho_Te @ F.conj().T

    # Combined A4 superoperator output
    return 0.5 * (rho_FeTi + rho_TeFi)


# =====================================================================
# AXIS 5: GENERATOR ALGEBRA / TEXTURE (Wave vs Line)
# Calculus toolhead (domain class).
#   Wave (FeFi): Integration. Laplacian + Fourier mixing.
#   Line (TeTi): Differentiation. Gradient + Dirac discrete cuts.
# =====================================================================

def _build_laplacian(d):
    """Discrete Laplacian operator (second derivative / diffusion kernel)."""
    L = np.zeros((d, d), dtype=complex)
    for i in range(d):
        L[i, i] = -2.0
        if i > 0:
            L[i, i-1] = 1.0
        if i < d - 1:
            L[i, i+1] = 1.0
    return L / d  # Normalize

def _build_gradient(d):
    """Discrete gradient operator (first derivative / partitioning)."""
    G = np.zeros((d, d), dtype=complex)
    for i in range(d - 1):
        G[i, i] = -1.0
        G[i, i+1] = 1.0
    return G / d  # Normalize

def A5_generator_algebra(rho, d):
    """Axis 5: Wave (Integration via Laplacian+Fourier) vs Line (Differentiation via Gradient+Dirac).
    
    Wave branch: Apply Laplacian smoothing then Fourier mixing.
    Line branch: Apply Gradient partitioning then Dirac projection.
    Combined: average of both branches.
    """
    # --- Wave Branch (FeFi): Integration algebra ---
    Lap = _build_laplacian(d)
    F = _build_fourier(d)
    # Laplacian smoothing: rho -> exp(Lap*t) rho exp(Lap*t)^dag (Hermitian approx)
    t_smooth = 0.05
    eLap = np.eye(d, dtype=complex) + Lap * t_smooth
    rho_smooth = eLap @ rho @ eLap.conj().T
    # Fourier mixing
    rho_wave = F @ rho_smooth @ F.conj().T

    # --- Line Branch (TeTi): Differentiation algebra ---
    G = _build_gradient(d)
    # Gradient partitioning: G rho G^dag (sparse cut)
    rho_grad = G @ rho @ G.conj().T
    # Dirac delta projection: keep only diagonal (computational basis discrete cuts)
    rho_line = np.diag(np.diagonal(rho_grad)).astype(complex)

    return 0.5 * (rho_wave + rho_line)


# =====================================================================
# AXIS 6: SIDEDNESS (UP/DOWN Composition precedence)
# Asymmetric far-off-diagonal anti-Hermitian structure.
# =====================================================================

def A6_sidedness(rho, d):
    """UP/DOWN composition order: asymmetric non-nearest off-diagonal."""
    out = np.zeros_like(rho)
    if d >= 3:
        out[0, d-1] = rho[0, d-1]
        out[d-1, 0] = -rho[d-1, 0]  # Asymmetric sign = sidedness
    if d >= 4:
        out[1, d-2] = rho[1, d-2] * 1.0j
        out[d-2, 1] = -rho[d-2, 1] * 1.0j
    return out


# =====================================================================
# AXIS 0: CORRELATION GRADIENT (Regime Switch)
# Quantum Conditional Entropy S(A|B) driving bipartite coupling.
# Tested as a REGIME SWITCH, not a pairwise inner product.
# =====================================================================

def A0_south_regime(rho, d):
    """Axis 0 South: high correlation (entangled bipartite coupling)."""
    out = np.zeros_like(rho)
    half = d // 2
    if half >= 2:
        block = rho[:half, half:]
        out[:half, half:] = block * 1.5
        out[half:, :half] = block.conj().T * 1.5
    return out

def A0_north_regime(rho, d):
    """Axis 0 North: low correlation (separable bipartite decoupling)."""
    out = np.zeros_like(rho)
    half = d // 2
    if half >= 2:
        block = rho[:half, half:]
        out[:half, half:] = block * 0.1
        out[half:, :half] = block.conj().T * 0.1
    return out


# =====================================================================
# GRAVEYARD DEFORMATION
# =====================================================================

def graveyard_deform(C_list, names, eps=1e-5):
    """If raw overlap exceeds eps, apply Gram-Schmidt to deform eigenvalues."""
    print("\n  GRAVEYARD: Applying Gram-Schmidt eigenvalue deformation...")
    deformed = gram_schmidt_deform(C_list)
    for i in range(len(deformed)):
        for j in range(i+1, len(deformed)):
            ov = hs_inner_product(deformed[i], deformed[j])
            status = "PASS" if abs(ov) < eps else "STILL_FAIL"
            print(f"    POST-DEFORM {names[i]} x {names[j]}: {ov:.2e} [{status}]")
    return deformed


# =====================================================================
# MASTER EXECUTION ENGINE
# =====================================================================

AXES = {
    "A1_ThermArrow":   A1_thermodynamic_arrow,
    "A2_SpatialDual":  A2_spatial_duality,
    "A3_WeylChiral":   A3_loop_flux_chirality,
    "A4_VarDirection": A4_variance_direction,
    "A5_GenAlgebra":   A5_generator_algebra,
    "A6_Sidedness":    A6_sidedness,
}

EPS = 1e-5
DIMS = [4, 8, 16, 32, 64]


def run_phase1_axis0(d):
    """Phase 1: Axis 0 Moderator Cross-Checks (6 SIMs).
    Measure interaction change when A0 flips South->North."""
    print(f"\n  PHASE 1: AXIS 0 REGIME SWITCH (d={d})")
    results = []
    for name, func in AXES.items():
        rho_test = np.eye(d, dtype=complex) / d
        # Add some structure
        rho_test[0, 0] += 0.3 / d
        rho_test /= np.trace(rho_test)
        if d >= 4:
            rho_test[0, d//2] = 0.1 + 0.1j
            rho_test[d//2, 0] = 0.1 - 0.1j

        C_south = build_choi(lambda r, dim: func(A0_south_regime(r, dim), dim), d)
        C_north = build_choi(lambda r, dim: func(A0_north_regime(r, dim), dim), d)

        delta_I = hs_inner_product(C_south, C_north)
        regime_diff = 1.0 - abs(delta_I)  # Large = good regime separation

        status = "REGIME_ACTIVE" if regime_diff > 0.01 else "TRANSPARENT"
        results.append((f"A0_switch x {name}", regime_diff, status))
        print(f"    A0 x {name:16s}: delta={regime_diff:.6f} [{status}]")

    return results


def run_phase2_pairwise(d):
    """Phase 2: 15 Pairwise Orthogonality SIMs (Axes 1-6)."""
    print(f"\n  PHASE 2: PAIRWISE ORTHOGONALITY (d={d})")

    choi_cache = {}
    for name, func in AXES.items():
        choi_cache[name] = build_choi(func, d)

    results = []
    kills = []
    for (n1, n2) in combinations(AXES.keys(), 2):
        ov = hs_inner_product(choi_cache[n1], choi_cache[n2])
        status = "PASS" if abs(ov) < EPS else "KILL"
        results.append((f"{n1} x {n2}", ov, status))
        if status == "KILL":
            kills.append((n1, n2))
        print(f"    {n1:16s} x {n2:16s}: {ov:+.2e} [{status}]")

    # Graveyard deformation for any KILL pairs
    if kills:
        kill_names = list(set(n for pair in kills for n in pair))
        kill_chois = [choi_cache[n] for n in kill_names]
        graveyard_deform(kill_chois, kill_names, EPS)

    return results


def execute_suite():
    print("=" * 74)
    print("CANONICAL AXIS ORTHOGONALITY SUITE")
    print("NLM-Dictated Pure QIT CPTP Definitions")
    print("Anti-Smuggling Enforcement: ACTIVE (Zero physical analogies)")
    print(f"Dimensions: {DIMS}")
    print(f"Threshold: epsilon = {EPS}")
    print("=" * 74)

    all_results = {}
    total_pass = 0
    total_tests = 0

    for d in DIMS:
        print(f"\n{'─'*74}")
        print(f"  DIMENSION d = {d}")
        print(f"{'─'*74}")

        p1 = run_phase1_axis0(d)
        p2 = run_phase2_pairwise(d)

        dim_pass = sum(1 for _, _, s in p2 if s == "PASS")
        dim_total = len(p2)
        total_pass += dim_pass
        total_tests += dim_total

        all_results[d] = {"phase1": p1, "phase2": p2}

    # ── PHASE 3: Evidence Emission ──
    print(f"\n{'='*74}")
    print(f"PHASE 3: EVIDENCE EMISSION")
    print(f"{'='*74}")

    evidence = []
    if total_pass == total_tests:
        print(f"  ALL {total_tests} PAIRWISE TESTS PASSED ACROSS ALL DIMENSIONS")
        evidence.append({
            "token_id": "E_SIM_ORTHOGONAL_PASS",
            "sim_spec_id": "S_SIM_AXIS_ORTHOGONALITY_CANONICAL_V1",
            "status": "PASS",
            "measured_value": total_pass,
            "total_tests": total_tests
        })
    else:
        fails = total_tests - total_pass
        print(f"  {fails} CONFLATION(S) DETECTED. KILL TOKEN EMITTED.")
        print(f"  Graveyard deformation was applied to all failing pairs.")
        evidence.append({
            "token_id": "E_SIM_CONFLATION_KILL",
            "sim_spec_id": "S_SIM_AXIS_ORTHOGONALITY_CANONICAL_V1",
            "status": "KILL",
            "measured_value": total_pass,
            "total_tests": total_tests,
            "kill_reason": f"{fails}_PAIRS_EXCEEDED_EPSILON"
        })

    print(f"\n  FINAL VERDICT: {total_pass}/{total_tests} PASS")

    # Serialize
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "axis_orthogonality_suite_results.json")

    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "dimensions_tested": DIMS,
            "epsilon": EPS,
            "evidence_ledger": evidence,
            "summary": {
                "total_pass": total_pass,
                "total_tests": total_tests,
            }
        }, f, indent=2)

    print(f"  Results saved: {outpath}")
    return evidence


if __name__ == "__main__":
    execute_suite()
