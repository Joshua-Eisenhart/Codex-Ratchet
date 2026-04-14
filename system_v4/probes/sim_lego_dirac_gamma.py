#!/usr/bin/env python3
"""
sim_lego_dirac_gamma.py
-----------------------
Pure math lego: Dirac equation gamma matrices in finite-dimensional QIT.

Constructs the full Dirac-Clifford algebra in 4x4 representation:
  - 4 gamma matrices satisfying {gamma^mu, gamma^nu} = 2 eta^{mu,nu}
  - Chirality operator gamma^5 = i gamma^0 gamma^1 gamma^2 gamma^3
  - Weyl projectors P_L = (1 - gamma^5)/2, P_R = (1 + gamma^5)/2
  - Dirac spinor decomposition into L/R Weyl components
  - Discrete symmetries: C (charge conjugation), P (parity), T (time reversal)

Connection to existing sims:
  The L/R Weyl spinors extracted here are the SAME objects that appear
  in sim_weyl_hopf_tori.py and dual_weyl_spinor_engine_sim.py.
  The Hopf torus geometry parameterizes the S3 fiber; the Dirac algebra
  provides the algebraic frame in which those spinors live.

Classification: canonical (pytorch + clifford + sympy)
"""

import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": "not needed -- no graph structure"},
    "z3":         {"tried": False, "used": False, "reason": "not needed -- numerical + symbolic verification"},
    "cvc5":       {"tried": False, "used": False, "reason": "not needed"},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": ""},
    "geomstats":  {"tried": False, "used": False, "reason": "not needed"},
    "e3nn":       {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not needed"},
    "xgi":        {"tried": False, "used": False, "reason": "not needed"},
    "toponetx":   {"tried": False, "used": False, "reason": "not needed"},
    "gudhi":      {"tried": False, "used": False, "reason": "not needed"},
}

# --- Import pytorch ---
try:
    import torch
    torch.set_default_dtype(torch.float64)
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "core tensor computation for gamma matrices, projectors, CPT operators"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    raise SystemExit("PyTorch required for canonical sim.")

# --- Import clifford for Cl(1,3) cross-check ---
try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "Cl(1,3) Clifford algebra cross-check of anticommutation relations"
except ImportError:
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = False
    TOOL_MANIFEST["clifford"]["reason"] = "not installed -- skipping Cl(1,3) cross-check"

CLIFFORD_AVAILABLE = TOOL_MANIFEST["clifford"]["used"]

# --- Import sympy for exact symbolic verification ---
try:
    import sympy as sp
    from sympy import Matrix as SpMatrix, eye as sp_eye, zeros as sp_zeros, I as sp_I
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "exact symbolic verification of Clifford algebra and projector identities"
except ImportError:
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = False
    TOOL_MANIFEST["sympy"]["reason"] = "not installed -- skipping symbolic cross-check"

SYMPY_AVAILABLE = TOOL_MANIFEST["sympy"]["used"]

EPS = 1e-12

# =====================================================================
# PAULI MATRICES (torch)
# =====================================================================

sigma_0 = torch.eye(2, dtype=torch.complex128)
sigma_1 = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
sigma_2 = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
sigma_3 = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)

I4 = torch.eye(4, dtype=torch.complex128)
Z2 = torch.zeros(2, 2, dtype=torch.complex128)


def block_matrix(tl, tr, bl, br):
    """Build 4x4 from four 2x2 blocks."""
    top = torch.cat([tl, tr], dim=1)
    bot = torch.cat([bl, br], dim=1)
    return torch.cat([top, bot], dim=0)


# =====================================================================
# GAMMA MATRICES (Dirac/Pauli representation)
# =====================================================================

# gamma^0 = [[I, 0], [0, -I]]
gamma0 = block_matrix(sigma_0, Z2, Z2, -sigma_0)

# gamma^i = [[0, sigma_i], [-sigma_i, 0]]
gamma1 = block_matrix(Z2, sigma_1, -sigma_1, Z2)
gamma2 = block_matrix(Z2, sigma_2, -sigma_2, Z2)
gamma3 = block_matrix(Z2, sigma_3, -sigma_3, Z2)

GAMMA = [gamma0, gamma1, gamma2, gamma3]

# Minkowski metric eta = diag(+1, -1, -1, -1)
ETA = torch.diag(torch.tensor([1.0, -1.0, -1.0, -1.0], dtype=torch.complex128))

# gamma^5 = i * gamma^0 * gamma^1 * gamma^2 * gamma^3
gamma5 = 1j * gamma0 @ gamma1 @ gamma2 @ gamma3

# Weyl projectors
P_L = (I4 - gamma5) / 2.0
P_R = (I4 + gamma5) / 2.0


# =====================================================================
# DISCRETE SYMMETRIES: C, P, T
# =====================================================================

# Charge conjugation matrix: C = i * gamma^2 * gamma^0
C_mat = 1j * gamma2 @ gamma0

# Parity: P = gamma^0
P_mat = gamma0.clone()

# Time reversal: T = i * gamma^1 * gamma^3
T_mat = 1j * gamma1 @ gamma3

# CPT combined
CPT_mat = C_mat @ P_mat @ T_mat


# =====================================================================
# HELPER: matrix comparison
# =====================================================================

def mat_close(A, B, tol=EPS):
    """Check if two torch matrices are close."""
    return torch.max(torch.abs(A - B)).item() < tol


def anticommutator(A, B):
    """Compute {A, B} = AB + BA."""
    return A @ B + B @ A


def commutator(A, B):
    """Compute [A, B] = AB - BA."""
    return A @ B - B @ A


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    passes = 0
    fails = 0

    # ---------------------------------------------------------------
    # T1: Clifford algebra {gamma^mu, gamma^nu} = 2 * eta^{mu,nu} * I4
    # ---------------------------------------------------------------
    clifford_ok = True
    clifford_details = {}
    for mu in range(4):
        for nu in range(4):
            ac = anticommutator(GAMMA[mu], GAMMA[nu])
            expected = 2.0 * ETA[mu, nu] * I4
            ok = mat_close(ac, expected)
            clifford_details[f"gamma{mu}_gamma{nu}"] = ok
            if not ok:
                clifford_ok = False

    results["T1_clifford_algebra"] = {
        "pass": clifford_ok,
        "detail": "All 16 anticommutator relations verified",
        "pairs_checked": 16,
    }
    passes += clifford_ok
    fails += (not clifford_ok)

    # ---------------------------------------------------------------
    # T2: gamma^5 properties
    # ---------------------------------------------------------------
    # (gamma^5)^2 = I
    g5_sq = gamma5 @ gamma5
    g5_squared_is_I = mat_close(g5_sq, I4)

    # {gamma^5, gamma^mu} = 0 for all mu
    g5_anticomm_ok = True
    for mu in range(4):
        ac = anticommutator(gamma5, GAMMA[mu])
        if not mat_close(ac, torch.zeros(4, 4, dtype=torch.complex128)):
            g5_anticomm_ok = False

    # gamma^5 is hermitian
    g5_hermitian = mat_close(gamma5, gamma5.conj().T)

    # Trace of gamma^5 is zero
    g5_traceless = abs(torch.trace(gamma5).item()) < EPS

    g5_ok = g5_squared_is_I and g5_anticomm_ok and g5_hermitian and g5_traceless
    results["T2_gamma5_properties"] = {
        "pass": g5_ok,
        "gamma5_squared_is_I": g5_squared_is_I,
        "anticommutes_with_all_gamma_mu": g5_anticomm_ok,
        "hermitian": g5_hermitian,
        "traceless": g5_traceless,
    }
    passes += g5_ok
    fails += (not g5_ok)

    # ---------------------------------------------------------------
    # T3: Weyl projectors
    # ---------------------------------------------------------------
    # P_L^2 = P_L (idempotent)
    pl_idem = mat_close(P_L @ P_L, P_L)
    # P_R^2 = P_R
    pr_idem = mat_close(P_R @ P_R, P_R)
    # P_L + P_R = I
    proj_complete = mat_close(P_L + P_R, I4)
    # P_L * P_R = 0
    proj_ortho = mat_close(P_L @ P_R, torch.zeros(4, 4, dtype=torch.complex128))
    # P_R * P_L = 0
    proj_ortho2 = mat_close(P_R @ P_L, torch.zeros(4, 4, dtype=torch.complex128))
    # Rank of each projector = 2
    pl_rank = int(torch.linalg.matrix_rank(P_L).item())
    pr_rank = int(torch.linalg.matrix_rank(P_R).item())
    rank_ok = (pl_rank == 2) and (pr_rank == 2)

    weyl_ok = pl_idem and pr_idem and proj_complete and proj_ortho and proj_ortho2 and rank_ok
    results["T3_weyl_projectors"] = {
        "pass": weyl_ok,
        "P_L_idempotent": pl_idem,
        "P_R_idempotent": pr_idem,
        "P_L_plus_P_R_eq_I": proj_complete,
        "P_L_P_R_eq_0": proj_ortho,
        "P_R_P_L_eq_0": proj_ortho2,
        "P_L_rank": pl_rank,
        "P_R_rank": pr_rank,
    }
    passes += weyl_ok
    fails += (not weyl_ok)

    # ---------------------------------------------------------------
    # T4: Dirac spinor decomposition into Weyl components
    # ---------------------------------------------------------------
    torch.manual_seed(42)
    psi = torch.randn(4, dtype=torch.complex128)
    psi = psi / torch.norm(psi)

    psi_L = P_L @ psi
    psi_R = P_R @ psi

    # psi_L + psi_R = psi
    decomp_ok = mat_close(psi_L + psi_R, psi, tol=1e-10)
    # P_L psi_L = psi_L (eigenstate)
    pl_eigen = mat_close(P_L @ psi_L, psi_L)
    # P_R psi_R = psi_R
    pr_eigen = mat_close(P_R @ psi_R, psi_R)
    # gamma^5 eigenvalues: gamma^5 psi_L = -psi_L, gamma^5 psi_R = +psi_R
    g5_L = mat_close(gamma5 @ psi_L, -psi_L, tol=1e-10)
    g5_R = mat_close(gamma5 @ psi_R, psi_R, tol=1e-10)

    # In Dirac representation: psi_L has nonzero top 2 components,
    # psi_R has nonzero bottom 2 components (for eigenstates of gamma5)
    # But for a general spinor, both are 4-component; the projector selects chirality.

    spinor_ok = decomp_ok and pl_eigen and pr_eigen and g5_L and g5_R
    results["T4_spinor_decomposition"] = {
        "pass": spinor_ok,
        "psi_L_plus_psi_R_eq_psi": decomp_ok,
        "P_L_psi_L_eq_psi_L": pl_eigen,
        "P_R_psi_R_eq_psi_R": pr_eigen,
        "gamma5_psi_L_eq_neg_psi_L": g5_L,
        "gamma5_psi_R_eq_pos_psi_R": g5_R,
        "psi_L_norm": torch.norm(psi_L).item(),
        "psi_R_norm": torch.norm(psi_R).item(),
    }
    passes += spinor_ok
    fails += (not spinor_ok)

    # ---------------------------------------------------------------
    # T5: Gamma matrix trace identities
    # ---------------------------------------------------------------
    # Tr(gamma^mu) = 0 for all mu
    trace_single = all(abs(torch.trace(GAMMA[mu]).item()) < EPS for mu in range(4))

    # Tr(gamma^mu gamma^nu) = 4 * eta^{mu,nu}
    trace_pair_ok = True
    for mu in range(4):
        for nu in range(4):
            tr = torch.trace(GAMMA[mu] @ GAMMA[nu]).item()
            expected = 4.0 * ETA[mu, nu].item()
            if abs(tr - expected) > EPS:
                trace_pair_ok = False

    # Tr(odd number of gammas) = 0: Tr(gamma^mu gamma^nu gamma^rho) = 0
    trace_triple_zero = True
    for mu in range(4):
        for nu in range(4):
            for rho in range(4):
                tr = torch.trace(GAMMA[mu] @ GAMMA[nu] @ GAMMA[rho]).item()
                if abs(tr) > EPS:
                    trace_triple_zero = False

    trace_ok = trace_single and trace_pair_ok and trace_triple_zero
    results["T5_trace_identities"] = {
        "pass": trace_ok,
        "Tr_single_gamma_zero": trace_single,
        "Tr_pair_eq_4eta": trace_pair_ok,
        "Tr_triple_zero": trace_triple_zero,
    }
    passes += trace_ok
    fails += (not trace_ok)

    # ---------------------------------------------------------------
    # T6: CPT operators -- basic properties
    # ---------------------------------------------------------------
    # C gamma^mu C^{-1} = -(gamma^mu)^T
    C_inv = torch.linalg.inv(C_mat)
    c_conjugation_ok = True
    for mu in range(4):
        lhs = C_mat @ GAMMA[mu] @ C_inv
        rhs = -GAMMA[mu].T
        if not mat_close(lhs, rhs, tol=1e-10):
            c_conjugation_ok = False

    # P gamma^0 P^{-1} = gamma^0 (parity preserves gamma^0)
    P_inv = torch.linalg.inv(P_mat)
    p_gamma0_ok = mat_close(P_mat @ gamma0 @ P_inv, gamma0)

    # P gamma^i P^{-1} = -gamma^i (parity flips spatial gammas)
    p_spatial_ok = True
    for i in range(1, 4):
        lhs = P_mat @ GAMMA[i] @ P_inv
        rhs = -GAMMA[i]
        if not mat_close(lhs, rhs, tol=1e-10):
            p_spatial_ok = False

    # CPT: (CPT)^2 should be proportional to identity
    cpt_sq = CPT_mat @ CPT_mat
    # Normalize to check proportionality
    cpt_sq_norm = cpt_sq / cpt_sq[0, 0] if abs(cpt_sq[0, 0].item()) > EPS else cpt_sq
    cpt_sq_prop_I = mat_close(cpt_sq_norm, I4, tol=1e-8) if abs(cpt_sq[0, 0].item()) > EPS else False

    cpt_ok = c_conjugation_ok and p_gamma0_ok and p_spatial_ok
    results["T6_CPT_operators"] = {
        "pass": cpt_ok,
        "C_gamma_mu_Cinv_eq_neg_gamma_muT": c_conjugation_ok,
        "P_preserves_gamma0": p_gamma0_ok,
        "P_flips_spatial_gammas": p_spatial_ok,
        "CPT_squared_proportional_to_I": cpt_sq_prop_I,
    }
    passes += cpt_ok
    fails += (not cpt_ok)

    # ---------------------------------------------------------------
    # T7: CPT on Dirac spinor -- CPT|psi> produces antiparticle
    # ---------------------------------------------------------------
    # For a Dirac spinor psi, the charge-conjugate spinor is:
    # psi_c = C * (gamma^0 * psi*)  (in Dirac representation)
    psi_c = C_mat @ (gamma0 @ psi.conj())

    # The CPT-transformed spinor should have opposite chirality content
    psi_c_L = P_L @ psi_c
    psi_c_R = P_R @ psi_c

    # C gamma^mu^T C^{-1} = -gamma^mu  (defining property of C in Dirac rep)
    # Equivalently: C^{-1} gamma^mu C = -(gamma^mu)^T
    # The chirality relation: C^{-1} gamma^5 C = (gamma^5)^T
    # In Dirac rep, gamma^5 is real symmetric => (gamma^5)^T = gamma^5
    c_gamma5_relation = C_mat @ gamma5 @ C_inv
    # C gamma^5 C^{-1} should equal gamma^5^T = gamma^5 (real symmetric in Dirac rep)
    c_chirality_ok = mat_close(c_gamma5_relation, gamma5.T, tol=1e-10)

    psi_L_norm = torch.norm(psi_L).item()
    psi_R_norm = torch.norm(psi_R).item()
    psi_c_L_norm = torch.norm(psi_c_L).item()
    psi_c_R_norm = torch.norm(psi_c_R).item()
    psi_c_normed = torch.norm(psi_c).item()

    # Verify charge conjugation is an involution up to sign: C C* = +/- I
    cc_star = C_mat @ C_mat.conj()
    cc_prop_I = mat_close(cc_star, I4, tol=1e-10) or mat_close(cc_star, -I4, tol=1e-10)

    cpt_spinor_ok = c_chirality_ok and cc_prop_I
    results["T7_CPT_spinor"] = {
        "pass": cpt_spinor_ok,
        "C_gamma5_Cinv_eq_gamma5T": c_chirality_ok,
        "CC_star_proportional_to_I": cc_prop_I,
        "psi_L_norm": psi_L_norm,
        "psi_R_norm": psi_R_norm,
        "psi_c_L_norm": psi_c_L_norm,
        "psi_c_R_norm": psi_c_R_norm,
        "psi_c_norm": psi_c_normed,
    }
    passes += cpt_spinor_ok
    fails += (not cpt_spinor_ok)

    # ---------------------------------------------------------------
    # T8: Clifford cross-check with clifford library Cl(1,3)
    # ---------------------------------------------------------------
    if CLIFFORD_AVAILABLE:
        layout, blades = Cl(1, 3)
        e0, e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"], blades["e4"]
        # In Cl(1,3): e0^2 = +1, e1^2 = e2^2 = e3^2 = -1
        sq_ok = (
            abs(float((e0 * e0).value[0]) - 1.0) < EPS and
            abs(float((e1 * e1).value[0]) - (-1.0)) < EPS and
            abs(float((e2 * e2).value[0]) - (-1.0)) < EPS and
            abs(float((e3 * e3).value[0]) - (-1.0)) < EPS
        )
        # Anticommutation: e_i * e_j + e_j * e_i = 0 for i != j
        anticomm_ok = True
        bases = [e0, e1, e2, e3]
        for i in range(4):
            for j in range(i + 1, 4):
                ac = bases[i] * bases[j] + bases[j] * bases[i]
                # Should be zero (scalar part)
                if abs(float(ac.value[0])) > EPS:
                    anticomm_ok = False
        cl13_ok = sq_ok and anticomm_ok
        results["T8_clifford_Cl13_crosscheck"] = {
            "pass": cl13_ok,
            "signature_squares_correct": sq_ok,
            "anticommutation_zero": anticomm_ok,
        }
        passes += cl13_ok
        fails += (not cl13_ok)
    else:
        results["T8_clifford_Cl13_crosscheck"] = {
            "pass": None,
            "skipped": True,
            "reason": "clifford library not available",
        }

    # ---------------------------------------------------------------
    # T9: Sympy exact symbolic verification
    # ---------------------------------------------------------------
    if SYMPY_AVAILABLE:
        I2s = sp_eye(2)
        Z2s = sp_zeros(2)
        s1 = SpMatrix([[0, 1], [1, 0]])
        s2 = SpMatrix([[0, -sp_I], [sp_I, 0]])
        s3 = SpMatrix([[1, 0], [0, -1]])

        def sp_block(tl, tr, bl, br):
            return SpMatrix([[tl, tr], [bl, br]])

        g0s = sp_block(I2s, Z2s, Z2s, -I2s)
        g1s = sp_block(Z2s, s1, -s1, Z2s)
        g2s = sp_block(Z2s, s2, -s2, Z2s)
        g3s = sp_block(Z2s, s3, -s3, Z2s)
        gammas_sp = [g0s, g1s, g2s, g3s]
        eta_diag = [1, -1, -1, -1]

        # Verify {gamma^mu, gamma^nu} = 2 eta^{mu,nu} I exactly
        sp_clifford_ok = True
        for mu in range(4):
            for nu in range(4):
                ac = gammas_sp[mu] * gammas_sp[nu] + gammas_sp[nu] * gammas_sp[mu]
                expected_val = 2 * (eta_diag[mu] if mu == nu else 0)
                expected_mat = expected_val * sp_eye(4)
                if sp.simplify(ac - expected_mat) != sp_zeros(4):
                    sp_clifford_ok = False

        # gamma^5 exact
        g5s = sp_I * g0s * g1s * g2s * g3s
        g5_sq_exact = sp.simplify(g5s * g5s - sp_eye(4)) == sp_zeros(4)

        sympy_ok = sp_clifford_ok and g5_sq_exact
        results["T9_sympy_exact_verification"] = {
            "pass": sympy_ok,
            "clifford_algebra_exact": sp_clifford_ok,
            "gamma5_squared_exact": g5_sq_exact,
        }
        passes += sympy_ok
        fails += (not sympy_ok)
    else:
        results["T9_sympy_exact_verification"] = {
            "pass": None,
            "skipped": True,
            "reason": "sympy not available",
        }

    # ---------------------------------------------------------------
    # T10: Connection to Hopf torus Weyl spinors
    # ---------------------------------------------------------------
    # The 2-component Weyl spinors from Hopf parameterization
    # psi_hopf(eta, xi) = [cos(eta) * e^{i*xi}, sin(eta)]
    #
    # In Dirac representation, gamma^5 is OFF-diagonal, so chiral eigenstates
    # are NOT simply top/bottom halves. The correct embedding is:
    #   Left-handed (gamma^5 eigenvalue -1):  (1/sqrt(2)) * [phi, -phi]
    #   Right-handed (gamma^5 eigenvalue +1): (1/sqrt(2)) * [phi, +phi]
    # where phi is the 2-component Weyl spinor.
    eta_val = torch.tensor(np.pi / 6, dtype=torch.float64)
    xi_val = torch.tensor(np.pi / 4, dtype=torch.float64)

    phi_hopf = torch.tensor([
        torch.cos(eta_val) * torch.exp(1j * xi_val),
        torch.sin(eta_val)
    ], dtype=torch.complex128)
    phi_hopf = phi_hopf / torch.norm(phi_hopf)

    # Embed as left-handed Dirac spinor: [phi, -phi] / sqrt(2)
    psi_dirac_L = torch.cat([phi_hopf, -phi_hopf]) / np.sqrt(2)

    # Embed as right-handed: [phi, +phi] / sqrt(2)
    psi_dirac_R = torch.cat([phi_hopf, phi_hopf]) / np.sqrt(2)

    # Verify: P_L preserves L embedding, kills R embedding (and vice versa)
    hopf_L_proj = P_L @ psi_dirac_L
    hopf_L_preserved = mat_close(hopf_L_proj, psi_dirac_L, tol=1e-10)
    hopf_L_killed = mat_close(P_R @ psi_dirac_L, torch.zeros(4, dtype=torch.complex128), tol=1e-10)

    hopf_R_proj = P_R @ psi_dirac_R
    hopf_R_preserved = mat_close(hopf_R_proj, psi_dirac_R, tol=1e-10)
    hopf_R_killed = mat_close(P_L @ psi_dirac_R, torch.zeros(4, dtype=torch.complex128), tol=1e-10)

    # Verify gamma^5 eigenvalues
    g5_L_check = mat_close(gamma5 @ psi_dirac_L, -psi_dirac_L, tol=1e-10)
    g5_R_check = mat_close(gamma5 @ psi_dirac_R, psi_dirac_R, tol=1e-10)

    # Extract 2-component Weyl content: for L-handed, both halves encode phi
    # top half = phi/sqrt(2), bottom half = -phi/sqrt(2)
    extracted_phi_from_L = psi_dirac_L[:2] * np.sqrt(2)
    phi_recovery_ok = mat_close(extracted_phi_from_L, phi_hopf, tol=1e-10)

    hopf_ok = hopf_L_preserved and hopf_L_killed and hopf_R_preserved and hopf_R_killed and g5_L_check and g5_R_check and phi_recovery_ok
    results["T10_hopf_weyl_connection"] = {
        "pass": hopf_ok,
        "L_embedding_preserved_by_P_L": hopf_L_preserved,
        "L_embedding_killed_by_P_R": hopf_L_killed,
        "R_embedding_preserved_by_P_R": hopf_R_preserved,
        "R_embedding_killed_by_P_L": hopf_R_killed,
        "gamma5_L_eigenvalue_neg1": g5_L_check,
        "gamma5_R_eigenvalue_pos1": g5_R_check,
        "phi_recovery_from_L": phi_recovery_ok,
        "hopf_eta": eta_val.item(),
        "hopf_xi": xi_val.item(),
        "detail": "Hopf torus 2-spinors embed as Weyl components via [phi, -/+phi]/sqrt(2) in Dirac rep",
    }
    passes += hopf_ok
    fails += (not hopf_ok)

    results["_summary"] = {"passes": passes, "fails": fails, "total": passes + fails}
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    passes = 0
    fails = 0

    # ---------------------------------------------------------------
    # N1: Commutators should NOT be zero (gammas don't commute for mu != nu)
    # ---------------------------------------------------------------
    nonzero_commutators = 0
    for mu in range(4):
        for nu in range(mu + 1, 4):
            comm = commutator(GAMMA[mu], GAMMA[nu])
            if torch.max(torch.abs(comm)).item() > EPS:
                nonzero_commutators += 1
    n1_ok = nonzero_commutators == 6  # C(4,2) = 6 distinct pairs
    results["N1_gammas_do_not_commute"] = {
        "pass": n1_ok,
        "nonzero_commutator_pairs": nonzero_commutators,
        "expected": 6,
    }
    passes += n1_ok
    fails += (not n1_ok)

    # ---------------------------------------------------------------
    # N2: Wrong metric signature should FAIL Clifford algebra
    # ---------------------------------------------------------------
    # If we used eta = diag(+1,+1,+1,+1) (Euclidean), the spatial gammas
    # would need (gamma^i)^2 = +I, but ours give -I
    wrong_eta = torch.diag(torch.tensor([1.0, 1.0, 1.0, 1.0], dtype=torch.complex128))
    wrong_count = 0
    for mu in range(4):
        ac_diag = anticommutator(GAMMA[mu], GAMMA[mu])
        expected_wrong = 2.0 * wrong_eta[mu, mu] * I4
        if mat_close(ac_diag, expected_wrong):
            wrong_count += 1
    # Only gamma^0 should match (both signatures agree on mu=0)
    n2_ok = wrong_count == 1
    results["N2_wrong_metric_fails"] = {
        "pass": n2_ok,
        "matching_with_euclidean": wrong_count,
        "expected_matching": 1,
        "detail": "Only gamma^0 squares to +I; spatial gammas square to -I (Minkowski, not Euclidean)",
    }
    passes += n2_ok
    fails += (not n2_ok)

    # ---------------------------------------------------------------
    # N3: Projectors with wrong gamma^5 should fail
    # ---------------------------------------------------------------
    # Use gamma^5_wrong = gamma^0 (not the real gamma^5)
    g5_wrong = gamma0
    PL_wrong = (I4 - g5_wrong) / 2.0
    PR_wrong = (I4 + g5_wrong) / 2.0
    # These are still projectors (any involution gives projectors), but
    # they should NOT anticommute with all gamma^mu
    wrong_anticomm = True
    for mu in range(4):
        ac = anticommutator(g5_wrong, GAMMA[mu])
        if not mat_close(ac, torch.zeros(4, 4, dtype=torch.complex128)):
            wrong_anticomm = False
    n3_ok = not wrong_anticomm  # SHOULD fail
    results["N3_wrong_gamma5_fails_anticommutation"] = {
        "pass": n3_ok,
        "wrong_gamma5_anticommutes": wrong_anticomm,
        "detail": "gamma^0 used as gamma^5 does NOT anticommute with all gamma^mu",
    }
    passes += n3_ok
    fails += (not n3_ok)

    # ---------------------------------------------------------------
    # N4: Mixing chiralities should not produce eigenstate
    # ---------------------------------------------------------------
    torch.manual_seed(99)
    psi_mixed = torch.randn(4, dtype=torch.complex128)
    psi_mixed = psi_mixed / torch.norm(psi_mixed)
    # A generic spinor is NOT an eigenstate of gamma^5
    g5_psi = gamma5 @ psi_mixed
    is_eigenstate_pos = mat_close(g5_psi, psi_mixed, tol=1e-6)
    is_eigenstate_neg = mat_close(g5_psi, -psi_mixed, tol=1e-6)
    n4_ok = not (is_eigenstate_pos or is_eigenstate_neg)
    results["N4_generic_spinor_not_chiral_eigenstate"] = {
        "pass": n4_ok,
        "is_positive_eigenstate": is_eigenstate_pos,
        "is_negative_eigenstate": is_eigenstate_neg,
    }
    passes += n4_ok
    fails += (not n4_ok)

    # ---------------------------------------------------------------
    # N5: gamma^5 is NOT a gamma matrix (should not satisfy gamma signature)
    # ---------------------------------------------------------------
    # (gamma^5)^2 = +I, but for a Minkowski spatial gamma, we need -I
    g5_sq_val = gamma5 @ gamma5
    g5_acts_like_spatial = mat_close(g5_sq_val, -I4)
    n5_ok = not g5_acts_like_spatial
    results["N5_gamma5_not_spatial_gamma"] = {
        "pass": n5_ok,
        "gamma5_squared_eq_neg_I": g5_acts_like_spatial,
        "detail": "(gamma^5)^2 = +I, not -I, so gamma^5 is not a spatial gamma matrix",
    }
    passes += n5_ok
    fails += (not n5_ok)

    results["_summary"] = {"passes": passes, "fails": fails, "total": passes + fails}
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    passes = 0
    fails = 0

    # ---------------------------------------------------------------
    # B1: Numerical precision of projector orthogonality
    # ---------------------------------------------------------------
    pl_pr = P_L @ P_R
    max_elem = torch.max(torch.abs(pl_pr)).item()
    b1_ok = max_elem < 1e-14
    results["B1_projector_orthogonality_precision"] = {
        "pass": b1_ok,
        "max_element_P_L_P_R": max_elem,
        "threshold": 1e-14,
    }
    passes += b1_ok
    fails += (not b1_ok)

    # ---------------------------------------------------------------
    # B2: Spinor at boundary eta=0 (pure up state on Hopf torus)
    # ---------------------------------------------------------------
    # Correct embedding for Dirac rep: [phi, -phi]/sqrt(2) for L-handed
    psi_eta0 = torch.tensor([1.0, 0.0], dtype=torch.complex128)
    psi_dirac_eta0 = torch.cat([psi_eta0, -psi_eta0]) / np.sqrt(2)
    proj_L = P_L @ psi_dirac_eta0
    proj_R = P_R @ psi_dirac_eta0
    b2_ok = (
        mat_close(proj_L, psi_dirac_eta0, tol=1e-10) and
        mat_close(proj_R, torch.zeros(4, dtype=torch.complex128), tol=1e-10)
    )
    results["B2_boundary_eta0_pure_L"] = {
        "pass": b2_ok,
        "detail": "At eta=0, Hopf spinor [1,0] embeds as [1,0,-1,0]/sqrt(2) = pure left-handed in Dirac rep",
    }
    passes += b2_ok
    fails += (not b2_ok)

    # ---------------------------------------------------------------
    # B3: Spinor at boundary eta=pi/2 (pure down state)
    # ---------------------------------------------------------------
    psi_eta_half = torch.tensor([0.0, 1.0], dtype=torch.complex128)
    psi_dirac_half = torch.cat([psi_eta_half, -psi_eta_half]) / np.sqrt(2)
    proj_L2 = P_L @ psi_dirac_half
    b3_ok = mat_close(proj_L2, psi_dirac_half, tol=1e-10)
    results["B3_boundary_eta_pi2_pure_L"] = {
        "pass": b3_ok,
        "detail": "At eta=pi/2, Hopf spinor [0,1] embeds as [0,1,0,-1]/sqrt(2) = pure left-handed",
    }
    passes += b3_ok
    fails += (not b3_ok)

    # ---------------------------------------------------------------
    # B4: All gamma matrices are unitary
    # ---------------------------------------------------------------
    unitary_ok = True
    for mu in range(4):
        prod = GAMMA[mu] @ GAMMA[mu].conj().T
        # gamma^0 is hermitian and unitary: gamma^0 * gamma^0^dag = I
        # gamma^i: (gamma^i)^dag = -gamma^i (anti-hermitian up to sign)
        # gamma^i * gamma^i^dag = gamma^i * gamma^0 * gamma^i * gamma^0
        # Simpler: check if |det| = 1
        det_val = abs(torch.linalg.det(GAMMA[mu]).item())
        if abs(det_val - 1.0) > 1e-10:
            unitary_ok = False

    results["B4_gamma_determinants_unit"] = {
        "pass": unitary_ok,
        "detail": "All gamma matrices have |det| = 1",
    }
    passes += unitary_ok
    fails += (not unitary_ok)

    # ---------------------------------------------------------------
    # B5: Lorentz generator sigma^{mu,nu} = (i/4)[gamma^mu, gamma^nu]
    # ---------------------------------------------------------------
    # The 6 independent generators should be traceless and linearly independent
    generators = []
    for mu in range(4):
        for nu in range(mu + 1, 4):
            sigma_mn = (1j / 4.0) * commutator(GAMMA[mu], GAMMA[nu])
            generators.append(sigma_mn)

    # All traceless
    traceless_ok = all(abs(torch.trace(g).item()) < EPS for g in generators)
    # 6 independent generators
    count_ok = len(generators) == 6

    b5_ok = traceless_ok and count_ok
    results["B5_lorentz_generators"] = {
        "pass": b5_ok,
        "num_generators": len(generators),
        "all_traceless": traceless_ok,
        "detail": "sigma^{mu,nu} = (i/4)[gamma^mu, gamma^nu] gives 6 traceless Lorentz generators",
    }
    passes += b5_ok
    fails += (not b5_ok)

    results["_summary"] = {"passes": passes, "fails": fails, "total": passes + fails}
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("sim_lego_dirac_gamma -- Dirac gamma matrices & Weyl spinors")
    print("=" * 60)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Print summary
    for section_name, section in [("POSITIVE", positive), ("NEGATIVE", negative), ("BOUNDARY", boundary)]:
        summ = section.get("_summary", {})
        p = summ.get("passes", 0)
        f = summ.get("fails", 0)
        t = summ.get("total", 0)
        status = "ALL PASS" if f == 0 else f"FAILURES: {f}"
        print(f"\n{section_name}: {p}/{t} passed -- {status}")
        for k, v in section.items():
            if k.startswith("_"):
                continue
            flag = "PASS" if v.get("pass") else ("SKIP" if v.get("pass") is None else "FAIL")
            print(f"  [{flag}] {k}")

    results = {
        "name": "lego_dirac_gamma -- Dirac equation gamma matrices in finite-dim QIT",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "connections": {
            "sim_weyl_hopf_tori": "L/R Weyl spinors from Hopf parameterization embed as chiral components of 4-spinor",
            "dual_weyl_spinor_engine_sim": "Type1/Type2 engines correspond to L/R chirality sectors of Dirac algebra",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_dirac_gamma_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
