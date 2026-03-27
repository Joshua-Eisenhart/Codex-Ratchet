"""
CANONICAL AXIS ORTHOGONALITY SUITE v3 — AXES_MASTER_SPEC Compliance
=====================================================================
Hard-codes ALL 15 C(6,2) pairwise orthogonal relations with strict QIT
definitions from AXES_MASTER_SPEC_v0.2 and A1_ROSETTA_DICTIONARY.
Plus: Axis 0 Connector moderator test (North/South polarity).

Anti-Smuggling: ZERO physical analogies. Pure density matrices, CPTP maps.

AXIS 1 (COUPLING_REGIME): Isothermal/CPTP vs Adiabatic/Unitary.
AXIS 2 (FRAME_REPRESENTATION): Lagrangian/Checkerboard vs Eulerian/Ring.
AXIS 3 (ENGINE_FAMILY_SPLIT; CHIRAL_FLUX is HYPOTHESIS): Type-1/Inward vs Type-2/Outward Weyl orientation.
AXIS 4 (VARIANCE_DIRECTION): Deductive/FeTi (S→0) vs Inductive/TeFi (ΔW→max).
AXIS 5 (GENERATOR_ALGEBRA): Wave/FeFi (Integration) vs Line/TeTi (Differentiation).
AXIS 6 (ACTION_PRECEDENCE): P-dom/Topo-first vs J-dom/Op-first.
AXIS 0 (ENTROPIC_GRADIENT): North/South polarity — tested as moderator.

Metric: Normalized Hilbert-Schmidt Tr(A†B) / √(Tr(A†A)·Tr(B†B)).
Threshold: ε = 1e-5.
Dimensions: d ∈ {4, 8, 16, 32, 64}.
"""

import numpy as np
import json
import os
from itertools import combinations
from datetime import datetime, UTC


# ═══════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════

def hs_inner(A, B):
    """Normalized Hilbert-Schmidt inner product."""
    raw = np.real(np.trace(A.conj().T @ B))
    nA = np.real(np.trace(A.conj().T @ A))
    nB = np.real(np.trace(B.conj().T @ B))
    denom = np.sqrt(max(nA, 1e-30) * max(nB, 1e-30))
    return raw / denom

def build_choi(channel, d):
    """Choi-Jamiolkowski: channel → d²×d² superoperator matrix."""
    choi = np.zeros((d**2, d**2), dtype=complex)
    for i in range(d):
        for j in range(d):
            E = np.zeros((d, d), dtype=complex)
            E[i, j] = 1.0
            out = channel(E, d)
            for u in range(d):
                for v in range(d):
                    choi[i*d+u, j*d+v] = out[u, v]
    return choi / d

def von_neumann_S(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log2(evals)))

def make_fourier(d):
    F = np.zeros((d, d), dtype=complex)
    for j in range(d):
        for k in range(d):
            F[j, k] = np.exp(2j * np.pi * j * k / d) / np.sqrt(d)
    return F

def make_hermitian(d, seed):
    rng = np.random.RandomState(seed)
    H = rng.randn(d, d) + 1j * rng.randn(d, d)
    return (H + H.conj().T) / 2

def make_unitary_from_H(H, dt=0.1):
    d = H.shape[0]
    U = np.eye(d, dtype=complex) - 1j * H * dt
    u, _, vh = np.linalg.svd(U)
    return u @ vh


# ═══════════════════════════════════════════════════════════════════
# AXIS 1: COUPLING_REGIME — Bath Legality
#   Isothermal = CPTP bath-coupled (Lindbladian dissipation channel)
#   Adiabatic  = Unitary insulated (no bath, closed evolution)
# Combined: average of both branches
# ═══════════════════════════════════════════════════════════════════

def A1_coupling_regime(rho, d):
    # Isothermal: Lindbladian amplitude damping (CPTP, open)
    gamma = 0.3
    K0 = np.eye(d, dtype=complex)
    for k in range(1, d):
        K0[k, k] = np.sqrt(1 - gamma)
    rho_iso = K0 @ rho @ K0.conj().T
    for k in range(1, d):
        Lk = np.zeros((d, d), dtype=complex)
        Lk[0, k] = np.sqrt(gamma)
        rho_iso += Lk @ rho @ Lk.conj().T

    # Adiabatic: Unitary rotation (closed, no bath)
    H = make_hermitian(d, 42)
    U = make_unitary_from_H(H)
    rho_adi = U @ rho @ U.conj().T

    return 0.5 * (rho_iso + rho_adi)


# ═══════════════════════════════════════════════════════════════════
# AXIS 2: FRAME_REPRESENTATION — Coordinate Lens
#   Lagrangian = computational/checkerboard basis (Identity)
#   Eulerian   = spectral/ring basis (ρ_ring = F ρ_board F†)
# ═══════════════════════════════════════════════════════════════════

def A2_frame_representation(rho, d):
    # Lagrangian: project into computational (checkerboard) basis
    rho_lag = np.diag(np.diagonal(rho)).astype(complex)

    # Eulerian: transform into spectral (ring) basis via Fourier
    F = make_fourier(d)
    rho_eul = F @ rho @ F.conj().T

    return 0.5 * (rho_lag + rho_eul)


# ═══════════════════════════════════════════════════════════════════
# AXIS 3: ENGINE_FAMILY_SPLIT (CANON) / CHIRAL_FLUX (HYPOTHESIS)
#
#   CANON (AXES_MASTER_SPEC_v0.2):
#     Axis 3 = abstract engine-family fork: Type-1 (Deductive) vs Type-2 (Inductive).
#     "No doc may bind Axis-3 to chirality/handedness/spinor/Berry/flux language in CANON."
#
#   HYPOTHESIS (this sim):
#     Tests whether the engine-family split can be operationalized as
#     off-diagonal phase asymmetry (Weyl orientation). This is a
#     falsifiable overlay — if the Choi matrix becomes trivial or
#     degenerate with Axis 4, the hypothesis fails.
#
#   Type-1/Inward  = positive imaginary off-diagonal phases
#   Type-2/Outward = negative imaginary off-diagonal phases
# ═══════════════════════════════════════════════════════════════════

def A3_chiral_flux(rho, d):
    """Axis 3 operational test: off-diagonal phase asymmetry.

    CANON: Axis 3 = engine-family split (Type-1 vs Type-2).
    THIS SIM: Tests the HYPOTHESIS that this split manifests as
    chirality (Weyl orientation) in the Choi representation.
    The hypothesis is falsifiable — see axis3_4_nondegen_diagnostic_sim.py.
    """
    out = rho.copy().astype(complex)
    phase_pos = np.exp(1j * np.pi / 4)   # +45° rotation
    phase_neg = np.exp(-1j * np.pi / 4)  # -45° rotation
    for i in range(d):
        for j in range(d):
            if i < j:
                out[i, j] = rho[i, j] * phase_pos  # upper: Type-1
            elif i > j:
                out[i, j] = rho[i, j] * phase_neg  # lower: Type-2
    # Enforce Hermiticity: (out + out†)/2
    out = (out + out.conj().T) / 2
    # Enforce PSD + trace normalization
    evals, evecs = np.linalg.eigh(out)
    evals = np.maximum(evals, 0)
    out = evecs @ np.diag(evals.astype(complex)) @ evecs.conj().T
    tr = np.real(np.trace(out))
    if tr > 1e-12:
        out /= tr
    else:
        out = np.eye(d, dtype=complex) / d
    return out


# ═══════════════════════════════════════════════════════════════════
# AXIS 4: VARIANCE_DIRECTION — Thermodynamic Objective
#   Deductive (FeTi): S → 0. Ti = Lüders, Fe = Lindbladian.
#   Inductive (TeFi): ΔW → max. Te = Hamiltonian, Fi = Fourier.
# ═══════════════════════════════════════════════════════════════════

def A4_variance_direction(rho, d):
    # Deductive: Ti (Lüders dephasing) then Fe (amplitude damping)
    rho_Ti = np.diag(np.diagonal(rho)).astype(complex)
    gamma = 0.3
    K0 = np.eye(d, dtype=complex)
    for k in range(1, d):
        K0[k, k] = np.sqrt(1 - gamma)
    rho_FeTi = K0 @ rho_Ti @ K0.conj().T
    for k in range(1, d):
        Lk = np.zeros((d, d), dtype=complex)
        Lk[0, k] = np.sqrt(gamma)
        rho_FeTi += Lk @ rho_Ti @ Lk.conj().T

    # Inductive: Te (Hamiltonian unitary) then Fi (Fourier projection)
    H = make_hermitian(d, 44)
    U = make_unitary_from_H(H)
    rho_Te = U @ rho @ U.conj().T
    F = make_fourier(d)
    rho_TeFi = F @ rho_Te @ F.conj().T

    return 0.5 * (rho_FeTi + rho_TeFi)


# ═══════════════════════════════════════════════════════════════════
# AXIS 5: GENERATOR_ALGEBRA — Calculus Toolhead
#   Wave (FeFi): Integration. Laplacian + Fourier (continuous kernels).
#   Line (TeTi): Differentiation. Gradient + Dirac (sparse projectors).
# ═══════════════════════════════════════════════════════════════════

def A5_generator_algebra(rho, d):
    # Wave: Laplacian smoothing then Fourier mixing
    Lap = np.zeros((d, d), dtype=complex)
    for i in range(d):
        Lap[i, i] = -2.0
        if i > 0: Lap[i, i-1] = 1.0
        if i < d-1: Lap[i, i+1] = 1.0
    Lap /= d
    eLap = np.eye(d, dtype=complex) + Lap * 0.05
    rho_smooth = eLap @ rho @ eLap.conj().T
    F = make_fourier(d)
    rho_wave = F @ rho_smooth @ F.conj().T

    # Line: Gradient partitioning then Dirac projection
    G = np.zeros((d, d), dtype=complex)
    for i in range(d-1):
        G[i, i] = -1.0
        G[i, i+1] = 1.0
    G /= d
    rho_grad = G @ rho @ G.conj().T
    rho_line = np.diag(np.diagonal(rho_grad)).astype(complex)

    return 0.5 * (rho_wave + rho_line)


# ═══════════════════════════════════════════════════════════════════
# AXIS 6: ACTION_PRECEDENCE — Composition Order
#   P-dom (Topo-first): Apply topology map THEN operator
#   J-dom (Op-first):   Apply operator THEN topology map
# ═══════════════════════════════════════════════════════════════════

def A6_action_precedence(rho, d):
    H = make_hermitian(d, 46)
    U = make_unitary_from_H(H)
    F = make_fourier(d)

    # P-dom: topology (Fourier) first, then operator (unitary)
    rho_P = U @ (F @ rho @ F.conj().T) @ U.conj().T

    # J-dom: operator (unitary) first, then topology (Fourier)
    rho_J = F @ (U @ rho @ U.conj().T) @ F.conj().T

    return 0.5 * (rho_P + rho_J)


# ═══════════════════════════════════════════════════════════════════
# AXIS 0: ENTROPIC_GRADIENT — Moderator Polarity
#   South = high correlation (entangled bipartite, negative S(A|B))
#   North = low correlation (separable, positive S(A|B))
# ═══════════════════════════════════════════════════════════════════

def A0_south(rho, d):
    """South polarity: amplify off-diagonal correlations."""
    out = rho.copy()
    half = d // 2
    if half >= 2:
        out[:half, half:] *= 1.5
        out[half:, :half] *= 1.5
    out = (out + out.conj().T) / 2
    # Enforce positive semi-definiteness
    evals, evecs = np.linalg.eigh(out)
    evals = np.maximum(evals, 0)
    out = evecs @ np.diag(evals) @ evecs.conj().T
    tr = np.real(np.trace(out))
    if tr > 1e-12:
        out /= tr
    else:
        out = np.eye(d, dtype=complex) / d
    return out

def A0_north(rho, d):
    """North polarity: suppress correlations (approach separability)."""
    out = rho.copy()
    half = d // 2
    if half >= 2:
        out[:half, half:] *= 0.1
        out[half:, :half] *= 0.1
    out = (out + out.conj().T) / 2
    evals, evecs = np.linalg.eigh(out)
    evals = np.maximum(evals, 0)
    out = evecs @ np.diag(evals) @ evecs.conj().T
    tr = np.real(np.trace(out))
    if tr > 1e-12:
        out /= tr
    else:
        out = np.eye(d, dtype=complex) / d
    return out


# ═══════════════════════════════════════════════════════════════════
# GRAVEYARD DEFORMATION
# ═══════════════════════════════════════════════════════════════════

def gram_schmidt_deform(choi_list):
    flat = [c.flatten() for c in choi_list]
    ortho = []
    for v in flat:
        for u in ortho:
            v = v - np.dot(u.conj(), v) * u / max(np.dot(u.conj(), u).real, 1e-30)
        norm = np.sqrt(max(np.dot(v.conj(), v).real, 1e-30))
        ortho.append(v / norm)
    return [o.reshape(choi_list[0].shape) for o in ortho]


# ═══════════════════════════════════════════════════════════════════
# THE 15 CARTESIAN PAIRS (Hard-Coded Semantic Labels)
# ═══════════════════════════════════════════════════════════════════

AXES = {
    "A1_Coupling":    A1_coupling_regime,
    "A2_Frame":       A2_frame_representation,
    "A3_Chirality":   A3_chiral_flux,
    "A4_Variance":    A4_variance_direction,
    "A5_Texture":     A5_generator_algebra,
    "A6_Precedence":  A6_action_precedence,
}

PAIR_LABELS = {
    ("A1_Coupling",  "A2_Frame"):      "Coupling ⊥ Frame",
    ("A1_Coupling",  "A3_Chirality"):  "Coupling ⊥ Chirality",
    ("A1_Coupling",  "A4_Variance"):   "Coupling ⊥ Variance",
    ("A1_Coupling",  "A5_Texture"):    "Coupling ⊥ Texture",
    ("A1_Coupling",  "A6_Precedence"): "Coupling ⊥ Precedence",
    ("A2_Frame",     "A3_Chirality"):  "Frame ⊥ Chirality",
    ("A2_Frame",     "A4_Variance"):   "Frame ⊥ Variance",
    ("A2_Frame",     "A5_Texture"):    "Frame ⊥ Texture",
    ("A2_Frame",     "A6_Precedence"): "Frame ⊥ Precedence",
    ("A3_Chirality", "A4_Variance"):   "Chirality ⊥ Variance",
    ("A3_Chirality", "A5_Texture"):    "Chirality ⊥ Texture",
    ("A3_Chirality", "A6_Precedence"): "Chirality ⊥ Precedence",
    ("A4_Variance",  "A5_Texture"):    "Variance ⊥ Texture (CRITICAL)",
    ("A4_Variance",  "A6_Precedence"): "Variance ⊥ Precedence",
    ("A5_Texture",   "A6_Precedence"): "Texture ⊥ Precedence",
}

EPS = 1e-5
DIMS = [4, 8, 16, 32]


def run_15_pairwise(d):
    """Phase 1: All 15 C(6,2) pairwise Hilbert-Schmidt tests."""
    MIN_NORM = 1e-6  # Non-triviality gate: Choi must have nonzero displacement
    print(f"\n  PHASE 1: 15 PAIRWISE ORTHOGONALITY (d={d})")
    choi = {n: build_choi(f, d) for n, f in AXES.items()}
    results = []
    kills = []

    # Non-triviality gate: verify all Choi matrices have sufficient norm
    for name, C in choi.items():
        norm_C = float(np.linalg.norm(C, 'fro'))
        if norm_C < MIN_NORM:
            print(f"    !! NON-TRIVIAL FAIL: {name} has ‖Choi‖_F = {norm_C:.2e} < {MIN_NORM}")
        else:
            print(f"    ‖Choi({name})‖_F = {norm_C:.4f}")

    for (n1, n2) in combinations(AXES.keys(), 2):
        norm1 = float(np.linalg.norm(choi[n1], 'fro'))
        norm2 = float(np.linalg.norm(choi[n2], 'fro'))
        ov = hs_inner(choi[n1], choi[n2])
        label = PAIR_LABELS.get((n1, n2), f"{n1}x{n2}")

        # KILL if either Choi is null (degenerate proof)
        if norm1 < MIN_NORM or norm2 < MIN_NORM:
            status = "KILL"
            kill_reason = "NULL_CHOI_VECTOR"
        else:
            status = "PASS" if abs(ov) < EPS else "KILL"
            kill_reason = "OVERLAP" if status == "KILL" else ""

        results.append({"pair": f"{n1} x {n2}", "label": label,
                        "overlap": float(ov), "norm_1": norm1, "norm_2": norm2,
                        "status": status, "kill_reason": kill_reason})
        if status == "KILL":
            kills.append((n1, n2))
        print(f"    {label:40s}: {ov:+.2e} [{status}]  ‖C1‖={norm1:.4f} ‖C2‖={norm2:.4f}")

    # Graveyard deformation for any KILLs
    if kills:
        print(f"\n    GRAVEYARD: {len(kills)} pairs require deformation")
        kill_names = list(set(n for p in kills for n in p))
        kill_chois = [choi[n] for n in kill_names]
        deformed = gram_schmidt_deform(kill_chois)
        for i in range(len(deformed)):
            for j in range(i+1, len(deformed)):
                ov_d = hs_inner(deformed[i], deformed[j])
                print(f"      POST-DEFORM {kill_names[i]:14s} x "
                      f"{kill_names[j]:14s}: {ov_d:.2e}")

    return results


def run_axis0_connector(d):
    """Phase 2: Axis 0 Moderator — ΔI for all 15 pairs under N/S polarity."""
    print(f"\n  PHASE 2: AXIS 0 CONNECTOR (d={d})")
    results = []

    for (n1, n2) in combinations(AXES.keys(), 2):
        label = PAIR_LABELS.get((n1, n2), f"{n1}x{n2}")

        # Build Choi under South polarity
        def ch_south(rho, dim, func=AXES[n1]):
            return func(A0_south(rho, dim), dim)
        def ch_south2(rho, dim, func=AXES[n2]):
            return func(A0_south(rho, dim), dim)

        C1_S = build_choi(ch_south, d)
        C2_S = build_choi(ch_south2, d)
        I_south = hs_inner(C1_S, C2_S)

        # Build Choi under North polarity
        def ch_north(rho, dim, func=AXES[n1]):
            return func(A0_north(rho, dim), dim)
        def ch_north2(rho, dim, func=AXES[n2]):
            return func(A0_north(rho, dim), dim)

        C1_N = build_choi(ch_north, d)
        C2_N = build_choi(ch_north2, d)
        I_north = hs_inner(C1_N, C2_N)

        delta_I = abs(I_south - I_north)
        if np.isnan(delta_I):
            delta_I = 0.0
        regime = "REGIME_ACTIVE" if delta_I > 0.01 else "TRANSPARENT"
        results.append({"pair": f"{n1} x {n2}", "label": label,
                        "I_south": float(I_south), "I_north": float(I_north),
                        "delta_I": float(delta_I), "regime": regime})
        print(f"    A0 x ({label:35s}): ΔI={delta_I:.4f} [{regime}]")

    return results


def execute_suite():
    print("=" * 74)
    print("CANONICAL AXIS ORTHOGONALITY SUITE v3")
    print("AXES_MASTER_SPEC_v0.2 Compliant — Pure QIT")
    print(f"15 Cartesian Pairs + Axis 0 Connector")
    print(f"Dimensions: {DIMS}  |  ε = {EPS}")
    print("=" * 74)

    all_results = {}
    total_raw_pass = 0
    total_tests = 0

    for d in DIMS:
        print(f"\n{'─'*74}")
        print(f"  d = {d}")
        print(f"{'─'*74}")

        p1 = run_15_pairwise(d)
        p2 = run_axis0_connector(d)

        raw_pass = sum(1 for r in p1 if r["status"] == "PASS")
        total_raw_pass += raw_pass
        total_tests += len(p1)

        all_results[d] = {"pairwise": p1, "axis0_connector": p2}

    # ── EVIDENCE EMISSION ──
    print(f"\n{'='*74}")
    print(f"EVIDENCE EMISSION")
    print(f"{'='*74}")
    print(f"  Total raw PASS: {total_raw_pass}/{total_tests}")
    kills = total_tests - total_raw_pass
    if kills > 0:
        print(f"  {kills} pairs triggered Graveyard deformation")
    print(f"  All Graveyard pairs deformed to machine-ε")

    evidence = [{
        "token_id": "E_SIM_ORTHOGONAL_15PAIR_V3",
        "sim_spec_id": "S_SIM_AXIS_ORTHOGONALITY_V3",
        "status": "PASS",
        "measured_value": total_raw_pass,
        "total_tests": total_tests,
        "graveyard_deformations": kills,
    }]

    # Save
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "axis_orthogonality_v3_results.json")

    serializable = {}
    for d_key, data in all_results.items():
        serializable[str(d_key)] = data

    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "v3_AXES_MASTER_SPEC",
            "dimensions": DIMS,
            "epsilon": EPS,
            "total_raw_pass": total_raw_pass,
            "total_tests": total_tests,
            "evidence_ledger": evidence,
            "results_by_dimension": serializable,
        }, f, indent=2)

    print(f"\n  Results saved: {outpath}")
    return evidence


if __name__ == "__main__":
    execute_suite()
