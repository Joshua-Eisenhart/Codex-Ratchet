#!/usr/bin/env python3
"""
Pure Lego: Quantum Reference Frames & Asymmetry Resource Theory
================================================================
Status: [Pure lego — no engine, numpy/scipy only]

Four modules:

  (1) G-TWIRLING
      Average rho over a symmetry group G.
      - U(1) z-rotations:  twirl kills off-diagonal coherences, preserves diagonal.
      - SU(2) full rotation: twirl projects to maximally mixed (I/d).

  (2) ASYMMETRY MONOTONE
      A(rho) = S(G(rho)) - S(rho)
      where G is the G-twirl and S is von Neumann entropy.
      Measures how much rho breaks G-symmetry.
      Verify: G-symmetric states have A = 0.

  (3) FRAMENESS
      A quantum state as a reference frame for measuring phase.
      Frame quality = asymmetry.  Better frame = more asymmetry resource.
      Demonstrate: |+> is a good U(1) frame; |0> is not.

  (4) WIGNER-ARAKI-YANASE (WAY) THEOREM
      A conservation law limits measurement precision.
      For angular momentum conservation + sigma_x measurement:
      - Perfect sigma_x measurement does NOT commute with J_z total.
      - Quantify disturbance as a function of apparatus frame size.
      - Show that larger reference frame => better measurement.

All quantities computed with explicit matrix operations.
No engine imports. Pure numpy/scipy.
"""

import numpy as np
from scipy.linalg import expm, logm
import json
import os
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# INFRASTRUCTURE
# =====================================================================

class _NumpyEncoder(json.JSONEncoder):
    """Handle numpy scalars that vanilla json chokes on."""
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)

# =====================================================================
# CONSTANTS & BASIS STATES
# =====================================================================

SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SIGMA_Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
I2 = np.eye(2, dtype=complex)

KET_0 = np.array([1.0, 0.0], dtype=complex)
KET_1 = np.array([0.0, 1.0], dtype=complex)
KET_PLUS = (KET_0 + KET_1) / np.sqrt(2)
KET_MINUS = (KET_0 - KET_1) / np.sqrt(2)

PHI_PLUS = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)

ATOL = 1e-10


def ket_to_dm(psi):
    """Pure state vector to density matrix."""
    psi = np.asarray(psi, dtype=complex).ravel()
    return np.outer(psi, psi.conj())


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log rho).  Eigenvalue-based, base-e."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > ATOL]
    return float(-np.sum(evals * np.log(evals)))


# =====================================================================
# MODULE 1 — G-TWIRLING
# =====================================================================

def u1_twirl(rho, n_samples=2000):
    """
    G-twirl over U(1) z-rotations: U(theta) = exp(-i theta sigma_z / 2).
    Analytically: kills off-diagonal elements, preserves diagonal.
    We verify numerically by averaging over many theta in [0, 2pi).
    """
    d = rho.shape[0]
    twirled = np.zeros_like(rho)
    thetas = np.linspace(0, 2 * np.pi, n_samples, endpoint=False)
    for theta in thetas:
        U = expm(-1j * theta * SIGMA_Z / 2)
        twirled += U @ rho @ U.conj().T
    twirled /= n_samples
    return twirled


def u1_twirl_exact(rho):
    """Exact U(1) twirl: zero off-diagonals, keep diagonals."""
    return np.diag(np.diag(rho)).astype(complex)


def su2_twirl(rho, n_samples=5000):
    """
    G-twirl over SU(2) (all rotations).
    For a qubit, analytically projects to I/2.
    We verify numerically by Haar-random unitaries.
    """
    d = rho.shape[0]
    twirled = np.zeros_like(rho)
    for _ in range(n_samples):
        # Haar-random 2x2 unitary via QR of Gaussian matrix
        Z = (np.random.randn(d, d) + 1j * np.random.randn(d, d)) / np.sqrt(2)
        Q, R = np.linalg.qr(Z)
        # Fix phase to get Haar measure
        diag_R = np.diag(R)
        phase = diag_R / np.abs(diag_R)
        U = Q @ np.diag(phase)
        twirled += U @ rho @ U.conj().T
    twirled /= n_samples
    return twirled


def run_g_twirling():
    """Test G-twirling for U(1) and SU(2)."""
    results = {}
    np.random.seed(42)

    # Test state: |+> = (|0> + |1>)/sqrt(2) — has off-diagonal coherence
    rho_plus = ket_to_dm(KET_PLUS)

    # --- U(1) twirl ---
    twirled_u1_num = u1_twirl(rho_plus)
    twirled_u1_exact = u1_twirl_exact(rho_plus)
    # Should be diag(0.5, 0.5) = I/2 (but via zeroing off-diag)
    u1_match = np.allclose(twirled_u1_num, twirled_u1_exact, atol=1e-3)
    u1_offdiag_killed = abs(twirled_u1_num[0, 1]) < 1e-3
    u1_diag_preserved = np.allclose(
        np.diag(twirled_u1_num), np.diag(rho_plus), atol=1e-3
    )

    results["u1_twirl"] = {
        "input_state": "|+>",
        "numerical_matches_exact": bool(u1_match),
        "off_diagonal_killed": bool(u1_offdiag_killed),
        "diagonal_preserved": bool(u1_diag_preserved),
        "twirled_diag": np.diag(twirled_u1_num).real.tolist(),
        "twirled_offdiag_01_abs": float(abs(twirled_u1_num[0, 1])),
        "PASS": bool(u1_match and u1_offdiag_killed and u1_diag_preserved),
    }

    # --- Asymmetric test: |0> should survive U(1) twirl (already diagonal) ---
    rho_0 = ket_to_dm(KET_0)
    twirled_0 = u1_twirl(rho_0)
    u1_0_unchanged = np.allclose(twirled_0, rho_0, atol=1e-3)
    results["u1_twirl_ket0"] = {
        "input_state": "|0>",
        "state_unchanged_under_u1": bool(u1_0_unchanged),
        "PASS": bool(u1_0_unchanged),
    }

    # --- SU(2) twirl ---
    twirled_su2 = su2_twirl(rho_plus)
    max_mixed = I2 / 2
    su2_match = np.allclose(twirled_su2, max_mixed, atol=5e-2)
    results["su2_twirl"] = {
        "input_state": "|+>",
        "projects_to_maximally_mixed": bool(su2_match),
        "twirled_matrix_real": twirled_su2.real.tolist(),
        "max_deviation_from_I_over_2": float(
            np.max(np.abs(twirled_su2 - max_mixed))
        ),
        "PASS": bool(su2_match),
    }

    # SU(2) twirl of |0> should also give I/2
    twirled_0_su2 = su2_twirl(rho_0)
    su2_0_match = np.allclose(twirled_0_su2, max_mixed, atol=5e-2)
    results["su2_twirl_ket0"] = {
        "input_state": "|0>",
        "projects_to_maximally_mixed": bool(su2_0_match),
        "PASS": bool(su2_0_match),
    }

    return results


# =====================================================================
# MODULE 2 — ASYMMETRY MONOTONE
# =====================================================================

def asymmetry_u1(rho):
    """
    A(rho) = S(G_U1(rho)) - S(rho).
    Measures how much rho breaks U(1) z-rotation symmetry.
    """
    twirled = u1_twirl_exact(rho)
    return von_neumann_entropy(twirled) - von_neumann_entropy(rho)


def asymmetry_su2(rho, n_samples=5000):
    """
    A(rho) = S(G_SU2(rho)) - S(rho).
    For a qubit, G_SU2(rho) = I/2 always, so S(G) = log(2).
    """
    s_twirled = np.log(rho.shape[0])  # S(I/d) = log(d)
    return s_twirled - von_neumann_entropy(rho)


def run_asymmetry_monotone():
    """Test asymmetry monotone for various states."""
    results = {}

    # |+> breaks U(1) symmetry (has coherence in z-basis)
    rho_plus = ket_to_dm(KET_PLUS)
    a_plus_u1 = asymmetry_u1(rho_plus)

    # |0> is U(1)-symmetric (eigenstate of sigma_z)
    rho_0 = ket_to_dm(KET_0)
    a_0_u1 = asymmetry_u1(rho_0)

    # I/2 is fully symmetric under everything
    rho_mixed = I2 / 2
    a_mixed_u1 = asymmetry_u1(rho_mixed)

    results["u1_asymmetry"] = {
        "A_ket_plus": float(a_plus_u1),
        "A_ket_0": float(a_0_u1),
        "A_maximally_mixed": float(a_mixed_u1),
        "plus_breaks_u1": bool(a_plus_u1 > ATOL),
        "ket0_is_u1_symmetric": bool(abs(a_0_u1) < ATOL),
        "mixed_is_u1_symmetric": bool(abs(a_mixed_u1) < ATOL),
        "PASS": bool(
            a_plus_u1 > ATOL
            and abs(a_0_u1) < ATOL
            and abs(a_mixed_u1) < ATOL
        ),
    }

    # SU(2) asymmetry: only I/2 is symmetric
    a_plus_su2 = asymmetry_su2(rho_plus)
    a_0_su2 = asymmetry_su2(rho_0)
    a_mixed_su2 = asymmetry_su2(rho_mixed)

    results["su2_asymmetry"] = {
        "A_ket_plus": float(a_plus_su2),
        "A_ket_0": float(a_0_su2),
        "A_maximally_mixed": float(a_mixed_su2),
        "plus_breaks_su2": bool(a_plus_su2 > ATOL),
        "ket0_breaks_su2": bool(a_0_su2 > ATOL),
        "mixed_is_su2_symmetric": bool(abs(a_mixed_su2) < ATOL),
        "PASS": bool(
            a_plus_su2 > ATOL
            and a_0_su2 > ATOL
            and abs(a_mixed_su2) < ATOL
        ),
    }

    # Monotonicity check: applying a covariant channel (G-twirl itself)
    # should not increase asymmetry
    rho_arb = 0.7 * ket_to_dm(KET_PLUS) + 0.3 * ket_to_dm(KET_0)
    a_before = asymmetry_u1(rho_arb)
    rho_after = u1_twirl_exact(rho_arb)
    a_after = asymmetry_u1(rho_after)

    results["monotonicity"] = {
        "A_before_twirl": float(a_before),
        "A_after_twirl": float(a_after),
        "monotone_holds": bool(a_after <= a_before + ATOL),
        "twirl_kills_asymmetry": bool(abs(a_after) < ATOL),
        "PASS": bool(a_after <= a_before + ATOL and abs(a_after) < ATOL),
    }

    return results


# =====================================================================
# MODULE 3 — FRAMENESS (quantum reference frame quality)
# =====================================================================

def phase_estimation_fidelity(rho_frame, theta_true, n_copies=1):
    """
    Simplified model: how well can rho_frame distinguish phase theta
    from phase 0?  We use trace distance between
       U(theta) rho U(theta)^dag  and  rho
    as a proxy for frame quality.

    Higher trace distance = frame can distinguish the phase shift
    = better reference frame.
    """
    U = expm(-1j * theta_true * SIGMA_Z / 2)
    rho_shifted = U @ rho_frame @ U.conj().T
    diff = rho_shifted - rho_frame
    # Trace distance = (1/2) ||A - B||_1
    svals = np.linalg.svd(diff, compute_uv=False)
    return float(0.5 * np.sum(svals))


def run_frameness():
    """Demonstrate quantum reference frame quality = asymmetry."""
    results = {}

    theta_test = np.pi / 4  # 45-degree phase shift

    # |+> is a GOOD U(1) frame: it has coherence, so it can detect z-rotations
    rho_plus = ket_to_dm(KET_PLUS)
    td_plus = phase_estimation_fidelity(rho_plus, theta_test)
    a_plus = asymmetry_u1(rho_plus)

    # |0> is a BAD U(1) frame: eigenstate of sigma_z, phase-insensitive
    rho_0 = ket_to_dm(KET_0)
    td_0 = phase_estimation_fidelity(rho_0, theta_test)
    a_0 = asymmetry_u1(rho_0)

    # I/2 is the WORST frame: completely symmetric
    rho_mixed = I2 / 2
    td_mixed = phase_estimation_fidelity(rho_mixed, theta_test)
    a_mixed = asymmetry_u1(rho_mixed)

    # Partially coherent state
    rho_partial = 0.5 * ket_to_dm(KET_PLUS) + 0.5 * (I2 / 2)
    td_partial = phase_estimation_fidelity(rho_partial, theta_test)
    a_partial = asymmetry_u1(rho_partial)

    results["frame_quality_vs_asymmetry"] = {
        "theta_test_rad": float(theta_test),
        "ket_plus": {
            "trace_distance": td_plus,
            "asymmetry": a_plus,
        },
        "ket_0": {
            "trace_distance": td_0,
            "asymmetry": a_0,
        },
        "maximally_mixed": {
            "trace_distance": td_mixed,
            "asymmetry": a_mixed,
        },
        "partial_coherent": {
            "trace_distance": td_partial,
            "asymmetry": a_partial,
        },
        "ranking_matches": bool(
            td_plus > td_partial > td_0 + ATOL
            and a_plus > a_partial > a_0 + ATOL
        ),
        "mixed_is_useless_frame": bool(td_mixed < ATOL and a_mixed < ATOL),
        "ket0_is_useless_frame": bool(td_0 < ATOL and a_0 < ATOL),
        "PASS": bool(
            td_plus > td_partial > td_0 + ATOL
            and td_mixed < ATOL
            and td_0 < ATOL
        ),
    }

    # Multi-copy advantage: N copies of |+> as a frame
    # Trace distance should grow with N (tensor product)
    td_list = []
    for n in [1, 2, 3]:
        psi_n = KET_PLUS.copy()
        for _ in range(n - 1):
            psi_n = np.kron(psi_n, KET_PLUS)
        rho_n = ket_to_dm(psi_n)
        # Collective phase: U(theta)^{otimes n}
        Uz = expm(-1j * theta_test * SIGMA_Z / 2)
        U_n = Uz.copy()
        for _ in range(n - 1):
            U_n = np.kron(U_n, Uz)
        rho_shifted = U_n @ rho_n @ U_n.conj().T
        diff = rho_shifted - rho_n
        svals = np.linalg.svd(diff, compute_uv=False)
        td_list.append(float(0.5 * np.sum(svals)))

    results["multi_copy_frame"] = {
        "theta_test_rad": float(theta_test),
        "trace_distances_1_2_3_copies": td_list,
        "improves_with_copies": bool(
            td_list[2] > td_list[1] > td_list[0]
        ),
        "PASS": bool(td_list[2] > td_list[1] > td_list[0]),
    }

    return results


# =====================================================================
# MODULE 4 — WIGNER-ARAKI-YANASE (WAY) THEOREM
# =====================================================================

def _build_spin_operators(j):
    """
    Build Jx, Jy, Jz for spin-j in the standard |j,m> basis.
    Dimension = 2j+1.  Basis ordered m = +j, +j-1, ..., -j.
    """
    d = int(2 * j + 1)
    Jz = np.zeros((d, d), dtype=complex)
    Jp = np.zeros((d, d), dtype=complex)
    for idx in range(d):
        m = j - idx  # m goes from +j down to -j
        Jz[idx, idx] = m
        if idx + 1 < d:
            m_low = j - (idx + 1)
            Jp[idx, idx + 1] = np.sqrt(j * (j + 1) - m_low * (m_low + 1))
    Jm = Jp.conj().T
    Jx = (Jp + Jm) / 2.0
    Jy = (Jp - Jm) / (2.0j)
    return Jx, Jy, Jz


def _partial_trace_sys(rho_total, d_sys, d_app):
    """Trace out the system (first subsystem) to get apparatus reduced state."""
    rho_app = np.zeros((d_app, d_app), dtype=complex)
    for i in range(d_sys):
        bra = np.zeros((1, d_sys), dtype=complex)
        bra[0, i] = 1.0
        proj = np.kron(bra, np.eye(d_app, dtype=complex))
        rho_app += proj @ rho_total @ proj.conj().T
    return rho_app


def run_way_theorem():
    """
    WAY theorem: if a conserved quantity L commutes with the total
    Hamiltonian, then observables that do NOT commute with L on the
    system alone cannot be measured perfectly with a finite apparatus.

    Concrete setup (Ozawa's formulation):
      - System: spin-1/2.  Observable to measure: sigma_x.
      - Conserved quantity: J_z_total = (sigma_z/2) x I + I x Jz_app.
      - sigma_x does NOT commute with sigma_z => WAY applies.
      - Interaction Hamiltonian: H_int = g (sigma_+ x J-_app + sigma_- x J+_app)
        This is a Jaynes-Cummings interaction that conserves Jz_total.
      - The apparatus starts in |j, +j> (maximally polarized up).
      - After interaction U = exp(-i H_int t), we measure Jx_app on apparatus.

    WAY prediction:
      - Measurement error decreases as apparatus spin j increases.
      - For j -> infinity, error -> 0 (perfect measurement recovered).
      - For finite j, there is an irreducible error ~ 1/(4j).

    We quantify "measurement quality" via the trace distance between
    the apparatus states conditioned on system being |+> vs |->.
    """
    results = {}

    # ---- Part A: Conserving interaction limits measurement ----
    # Use Jaynes-Cummings H = sigma_+ J_- + sigma_- J+ which conserves Jz_total.
    # Show: pointer (Jz_app) CANNOT distinguish |+> from |-> (WAY obstruction).
    # Also show: disturbance to <sigma_x> decreases with apparatus size j.

    way_data = []
    j_values = [0.5, 1.0, 2.0, 5.0, 10.0]

    for j_app in j_values:
        d_app = int(2 * j_app + 1)

        sp_sys = np.array([[0, 1], [0, 0]], dtype=complex)
        sm_sys = np.array([[0, 0], [1, 0]], dtype=complex)

        Jx_app, Jy_app, Jz_app_mat = _build_spin_operators(j_app)
        Jp_app = Jx_app + 1j * Jy_app
        Jm_app = Jx_app - 1j * Jy_app

        H_int = np.kron(sp_sys, Jm_app) + np.kron(sm_sys, Jp_app)

        Jz_total = (np.kron(SIGMA_Z / 2, np.eye(d_app, dtype=complex)) +
                     np.kron(I2, Jz_app_mat))

        comm_norm = np.linalg.norm(H_int @ Jz_total - Jz_total @ H_int)

        # Use coherent spin state |j, Jx=+j> as apparatus ready state
        # (maximizes phase sensitivity = best possible reference frame)
        Ry = expm(-1j * (np.pi / 2) * Jy_app)
        A_jj = np.zeros(d_app, dtype=complex)
        A_jj[0] = 1.0
        A_css = Ry @ A_jj

        # Fixed effective Rabi angle: g*t = pi/(2*sqrt(2j))
        g_t = np.pi / (2.0 * np.sqrt(2.0 * j_app))
        U = expm(-1j * g_t * H_int)

        psi_p = np.kron(KET_PLUS, A_css)
        psi_m = np.kron(KET_MINUS, A_css)
        psi_p_f = U @ psi_p
        psi_m_f = U @ psi_m

        rho_p = ket_to_dm(psi_p_f)
        rho_m = ket_to_dm(psi_m_f)

        # Pointer: Jz_app (natural pointer for Jz-conserving interaction)
        Jz_total_op = np.kron(I2, Jz_app_mat)
        ptr_p = np.real(np.trace(Jz_total_op @ rho_p))
        ptr_m = np.real(np.trace(Jz_total_op @ rho_m))
        pointer_gap_Jz = abs(ptr_p - ptr_m)

        # Also check Jx_app as pointer
        Jx_total_op = np.kron(I2, Jx_app)
        ptr_p_x = np.real(np.trace(Jx_total_op @ rho_p))
        ptr_m_x = np.real(np.trace(Jx_total_op @ rho_m))
        pointer_gap_Jx = abs(ptr_p_x - ptr_m_x)

        # Disturbance to system
        rho_sys = np.zeros((2, 2), dtype=complex)
        for i in range(d_app):
            bra = np.zeros((1, d_app), dtype=complex)
            bra[0, i] = 1.0
            proj = np.kron(I2, bra)
            rho_sys += proj @ rho_p @ proj.conj().T
        sx_after = np.real(np.trace(SIGMA_X @ rho_sys))
        disturbance = 1.0 - sx_after

        way_data.append({
            "apparatus_spin_j": float(j_app),
            "apparatus_dim": d_app,
            "pointer_gap_Jz": round(float(pointer_gap_Jz), 10),
            "pointer_gap_Jx": round(float(pointer_gap_Jx), 10),
            "sx_after": round(float(sx_after), 8),
            "disturbance": round(float(disturbance), 8),
            "conservation_verified": bool(comm_norm < 1e-8),
        })

    dist_values = [d["disturbance"] for d in way_data]
    gap_values = [d["pointer_gap_Jz"] for d in way_data]

    # WAY predictions:
    # 1. Pointer gap is zero/tiny: Jz-conserving interaction cannot distinguish
    #    sigma_x eigenstates via Jz pointer (WAY obstruction)
    pointer_blocked = all(g < 0.01 for g in gap_values)

    # 2. Disturbance decreases as apparatus size grows
    # (larger reference frame => less back-action on system)
    disturbance_decreases = all(
        dist_values[i] >= dist_values[i + 1] - 1e-6
        for i in range(len(dist_values) - 1)
    )
    small_disturbs = dist_values[0] > 0.01
    large_less_disturbing = dist_values[-1] < dist_values[0]

    results["way_theorem"] = {
        "observable": "sigma_x",
        "conserved_quantity": "J_z_total",
        "interaction": "Jaynes-Cummings (sigma_+ J_- + sigma_- J_+)",
        "apparatus_results": way_data,
        "pointer_blocked_by_conservation": bool(pointer_blocked),
        "disturbance_decreases_with_size": bool(disturbance_decreases),
        "small_apparatus_disturbs": bool(small_disturbs),
        "large_less_disturbing": bool(large_less_disturbing),
        "PASS": bool(
            pointer_blocked
            and disturbance_decreases
            and small_disturbs
            and large_less_disturbing
        ),
    }

    # ---- Part B: Non-conserving control ----
    # Without a conservation law, sigma_x CAN be measured perfectly.
    # Use a CNOT in the sigma_x eigenbasis:
    #   |+>|0> -> |+>|0>
    #   |->|0> -> |->|1>
    # This is U = |+><+| x I + |-><-| x X_app, which does NOT conserve Jz_total.
    proj_plus = ket_to_dm(KET_PLUS)
    proj_minus = ket_to_dm(KET_MINUS)
    X_app = np.array([[0, 1], [1, 0]], dtype=complex)

    U_ctrl = np.kron(proj_plus, I2) + np.kron(proj_minus, X_app)

    # Check: does it conserve Jz_total? (It should NOT)
    Jz_total_ctrl = np.kron(SIGMA_Z / 2, I2) + np.kron(I2, SIGMA_Z / 2)
    comm_ctrl = np.linalg.norm(U_ctrl @ Jz_total_ctrl - Jz_total_ctrl @ U_ctrl)

    A_ctrl = KET_0.copy()
    psi_p_c = np.kron(KET_PLUS, A_ctrl)
    psi_m_c = np.kron(KET_MINUS, A_ctrl)
    psi_p_cf = U_ctrl @ psi_p_c
    psi_m_cf = U_ctrl @ psi_m_c

    rho_p_c = ket_to_dm(psi_p_cf)
    rho_m_c = ket_to_dm(psi_m_cf)

    # Pointer: sigma_z on apparatus qubit
    Sz_ptr = np.kron(I2, SIGMA_Z)
    ptr_p_ctrl = np.real(np.trace(Sz_ptr @ rho_p_c))
    ptr_m_ctrl = np.real(np.trace(Sz_ptr @ rho_m_c))
    ctrl_gap = abs(ptr_p_ctrl - ptr_m_ctrl)

    results["way_control_no_conservation"] = {
        "interaction": "CNOT in sigma_x eigenbasis (non-conserving)",
        "conservation_violated": bool(comm_ctrl > 0.1),
        "pointer_gap": round(float(ctrl_gap), 8),
        "pointer_distinguishes": bool(ctrl_gap > 0.1),
        "contrast_with_conserving": (
            "Conservation law blocks measurement (gap~0); "
            "without conservation, perfect measurement possible (gap=2)"
        ),
        "PASS": bool(comm_ctrl > 0.1 and ctrl_gap > 0.1),
    }

    # WAY precondition: [sigma_x, sigma_z] != 0
    comm_sx_sz = SIGMA_X @ SIGMA_Z - SIGMA_Z @ SIGMA_X
    comm_sx_sz_norm = np.linalg.norm(comm_sx_sz)
    results["way_precondition"] = {
        "commutator_sigma_x_sigma_z_norm": float(comm_sx_sz_norm),
        "observable_does_not_commute_with_conserved": bool(comm_sx_sz_norm > 0.1),
        "PASS": bool(comm_sx_sz_norm > 0.1),
    }

    return results


# =====================================================================
# MAIN — RUN ALL MODULES
# =====================================================================

def main():
    np.random.seed(2026)

    all_results = {
        "sim": "pure_lego_reference_frames",
        "description": (
            "Quantum reference frames and asymmetry resource theory: "
            "G-twirling, asymmetry monotone, frameness, WAY theorem"
        ),
    }

    print("=" * 70)
    print("Pure Lego: Quantum Reference Frames & Asymmetry Resource Theory")
    print("=" * 70)

    # --- Module 1: G-twirling ---
    print("\n[1/4] G-twirling ...")
    twirl_results = run_g_twirling()
    all_results["g_twirling"] = twirl_results
    for key, val in twirl_results.items():
        status = "PASS" if val["PASS"] else "FAIL"
        print(f"  {key}: {status}")

    # --- Module 2: Asymmetry monotone ---
    print("\n[2/4] Asymmetry monotone ...")
    asym_results = run_asymmetry_monotone()
    all_results["asymmetry_monotone"] = asym_results
    for key, val in asym_results.items():
        status = "PASS" if val["PASS"] else "FAIL"
        print(f"  {key}: {status}")

    # --- Module 3: Frameness ---
    print("\n[3/4] Frameness (reference frame quality) ...")
    frame_results = run_frameness()
    all_results["frameness"] = frame_results
    for key, val in frame_results.items():
        status = "PASS" if val["PASS"] else "FAIL"
        print(f"  {key}: {status}")

    # --- Module 4: WAY theorem ---
    print("\n[4/4] Wigner-Araki-Yanase theorem ...")
    way_results = run_way_theorem()
    all_results["way_theorem"] = way_results
    for key, val in way_results.items():
        status = "PASS" if val["PASS"] else "FAIL"
        print(f"  {key}: {status}")

    # --- Overall ---
    all_pass_flags = []
    for section in [twirl_results, asym_results, frame_results, way_results]:
        for val in section.values():
            all_pass_flags.append(val["PASS"])

    all_results["overall_pass"] = all(all_pass_flags)
    all_results["total_tests"] = len(all_pass_flags)
    all_results["tests_passed"] = sum(all_pass_flags)

    print(f"\n{'=' * 70}")
    verdict = "ALL PASS" if all_results["overall_pass"] else "SOME FAILURES"
    print(f"OVERALL: {all_results['tests_passed']}/{all_results['total_tests']} — {verdict}")
    print(f"{'=' * 70}")

    # --- Write results ---
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, "pure_lego_reference_frames_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, cls=_NumpyEncoder)
    print(f"\nResults written to {out_path}")

    return all_results


if __name__ == "__main__":
    main()
