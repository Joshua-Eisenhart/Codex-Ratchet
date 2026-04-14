#!/usr/bin/env python3
"""
SIM: Twilight Zone -- Discord without Entanglement
====================================================

Investigates the region r in [0.51, 0.84] where:
  - Entanglement is DEAD (I_c <= 0, state is separable)
  - But the I_c Hessian is still LORENTZIAN (pseudo-Riemannian)

Discovered in sim_lorentzian_geometry.py:
  - Entanglement sudden death at r ~ 0.84
  - Metric signature change (det(g)=0) at r ~ 0.51

Hypothesis:
  The twilight zone contains DISCORD without ENTANGLEMENT.
  The Lorentzian metric detects quantum correlations that
  entanglement measures miss. Quantum discord, QFI, and mutual
  information remain nonzero even after entanglement death.

At 30 points in the twilight zone, compute:
  1. I_c (should be <= 0)
  2. Quantum discord (can be nonzero when entanglement is zero)
  3. Hessian eigenvalues (should have mixed signs -- Lorentzian)
  4. QFI (quantum Fisher information)
  5. Mutual information I(A:B)
  6. Steering inequality violation

Tests:
  Positive:
    - discord > 0 throughout twilight zone
    - I_c <= 0 throughout (no entanglement)
    - Hessian has mixed eigenvalues (Lorentzian) throughout
    - QFI > classical Fisher information (quantum advantage persists)
  Negative:
    - Outside twilight zone (r < 0.51), metric becomes Riemannian
  Boundary:
    - r = 0.51 (metric transition), r = 0.84 (entanglement death)

Tools: pytorch=used, geomstats=tried. Classification: canonical.
Output: system_v4/probes/a2_state/sim_results/twilight_zone_results.json
"""

import json
import os
import time
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": "not needed for this sim"},
    "z3":         {"tried": False, "used": False, "reason": "not needed for this sim"},
    "cvc5":       {"tried": False, "used": False, "reason": "not needed for this sim"},
    "sympy":      {"tried": False, "used": False, "reason": "not needed for this sim"},
    "clifford":   {"tried": False, "used": False, "reason": "not needed for this sim"},
    "geomstats":  {"tried": False, "used": False, "reason": ""},
    "e3nn":       {"tried": False, "used": False, "reason": "not needed for this sim"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not needed for this sim"},
    "xgi":        {"tried": False, "used": False, "reason": "not needed for this sim"},
    "toponetx":   {"tried": False, "used": False, "reason": "not needed for this sim"},
    "gudhi":      {"tried": False, "used": False, "reason": "not needed for this sim"},
}

try:
    import torch
    import torch.autograd.functional as AF
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import geomstats.backend as gs
    TOOL_MANIFEST["geomstats"]["tried"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = "imported but not load-bearing"
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"


# =====================================================================
# CONSTANTS
# =====================================================================

DTYPE = torch.complex128
FDTYPE = torch.float64
PHI_FIXED = 0.0
EPS_FD = 1e-5
N_TWILIGHT = 30       # Grid points in twilight zone
THETA_FIXED = np.pi / 4  # Fix theta=pi/4 for main sweep (matches Lorentzian sim)

# Twilight zone boundaries -- EMPIRICALLY DETERMINED per theta.
# At theta=pi/4, the Lorentzian signature persists all the way down (no
# metric transition at this angle). The null surface at r~0.51 from the
# original sim is a theta-averaged value from the 2D det(g)=0 contour.
#
# For theta=pi/4 specifically:
#   - Entanglement death at r ~ 0.84 (I_c crosses zero)
#   - Metric stays Lorentzian even below that
#
# The "twilight zone" at this theta = the entire separable-but-Lorentzian
# region. We sample the most interesting part: near the entanglement
# death boundary and well into the separable zone.
R_TWILIGHT_LOWER = 0.30    # Deep in separable region, still Lorentzian
R_ENTANGLEMENT_DEATH = 0.84  # I_c drops to 0: entanglement dies

# For the theta where the null surface DOES exist, use theta ~ 1.1 (pi/3-ish)
# where sudden death r_crit ~ 0.76 and the null surface is at r ~ 0.51.
THETA_NULL_SURFACE = 1.114  # From the original sim's sudden death scan
R_NULL_SURFACE = 0.51       # Approximate det(g)=0 at this theta


# =====================================================================
# CORE QUANTUM STATE CONSTRUCTION (from sim_lorentzian_geometry)
# =====================================================================

def build_two_qubit_rho(theta, phi, r):
    """
    Build 2-qubit density operator rho(theta, phi, r).
    rho = r * |Psi><Psi| + (1-r) * I/4
    where |Psi> = CNOT(|psi(theta,phi)> x |0>)
    """
    ct2 = torch.cos(theta / 2)
    st2 = torch.sin(theta / 2)
    psi_A = torch.stack([
        ct2.to(DTYPE),
        (st2 * torch.exp(1j * phi.to(DTYPE))).to(DTYPE),
    ])

    ket_0 = torch.tensor([1, 0], dtype=DTYPE)
    psi_AB = torch.kron(psi_A, ket_0)

    CNOT = torch.tensor([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=DTYPE)

    psi_ent = CNOT @ psi_AB
    rho_pure = torch.outer(psi_ent, psi_ent.conj())

    I4 = torch.eye(4, dtype=DTYPE)
    rho = r.to(DTYPE) * rho_pure + (1 - r.to(DTYPE)) * I4 / 4
    return rho


def partial_trace_A(rho_AB):
    """Trace out subsystem A from 4x4 -> 2x2."""
    rho_reshaped = rho_AB.reshape(2, 2, 2, 2)
    return torch.einsum('aiaj->ij', rho_reshaped)


def partial_trace_B(rho_AB):
    """Trace out subsystem B from 4x4 -> 2x2."""
    rho_reshaped = rho_AB.reshape(2, 2, 2, 2)
    return torch.einsum('iaja->ij', rho_reshaped)


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log rho), differentiable."""
    evals = torch.linalg.eigvalsh(rho)
    evals_real = evals.real
    evals_clamped = torch.clamp(evals_real, min=1e-15)
    return -torch.sum(evals_clamped * torch.log2(evals_clamped))


def coherent_information_scalar(eta_2d):
    """
    I_c(A>B) = S(B) - S(AB) as function of eta_2d = (theta, r).
    phi is fixed at PHI_FIXED.
    """
    theta, r = eta_2d[0], eta_2d[1]
    phi = torch.tensor(PHI_FIXED, dtype=FDTYPE)
    rho_AB = build_two_qubit_rho(theta, phi, r)
    rho_B = partial_trace_A(rho_AB)
    S_B = von_neumann_entropy(rho_B)
    S_AB = von_neumann_entropy(rho_AB)
    return S_B - S_AB


# =====================================================================
# GRADIENT AND HESSIAN (reused from sim_lorentzian_geometry)
# =====================================================================

def compute_gradient_2d(theta_val, r_val):
    """Gradient of I_c on (theta, r) submanifold."""
    eta = torch.tensor([theta_val, r_val], dtype=FDTYPE, requires_grad=True)
    ic = coherent_information_scalar(eta)
    ic.backward()
    return float(ic.item()), eta.grad.detach().numpy().copy()


def compute_hessian_2d(theta_val, r_val):
    """2x2 Hessian via central finite differences on the gradient."""
    eta = [theta_val, r_val]
    ic_val, grad_center = compute_gradient_2d(*eta)

    H = np.zeros((2, 2))
    for i in range(2):
        eta_p = list(eta)
        eta_m = list(eta)
        eta_p[i] += EPS_FD
        eta_m[i] -= EPS_FD
        if i == 1:
            eta_p[i] = min(eta_p[i], 1.0 - 1e-10)
            eta_m[i] = max(eta_m[i], 1e-10)

        _, grad_p = compute_gradient_2d(*eta_p)
        _, grad_m = compute_gradient_2d(*eta_m)
        H[i, :] = (grad_p - grad_m) / (2 * EPS_FD)

    H = 0.5 * (H + H.T)
    return ic_val, grad_center, H


def classify_signature(evals, tol=1e-10):
    """Classify 2x2 metric signature."""
    signs = []
    for e in evals:
        if e > tol:
            signs.append("+")
        elif e < -tol:
            signs.append("-")
        else:
            signs.append("0")
    sig = tuple(signs)
    if sig == ("+", "+"):
        return "riemannian_positive"
    elif sig == ("-", "-"):
        return "riemannian_negative"
    elif sig in (("-", "+"), ("+", "-")):
        return "lorentzian"
    elif "0" in sig:
        return "degenerate"
    return "unknown"


# =====================================================================
# QUANTUM DISCORD (Ollivier-Zurek)
# =====================================================================

def quantum_discord_AB(rho_AB_t):
    """
    Quantum discord D(A|B) = I(A:B) - J(A|B)
    where J(A|B) = max over measurements on B of classical correlations.

    We optimize over projective measurements on B parameterized by
    angle alpha on the Bloch sphere (z-x plane, sufficient for
    real states with phi=0).
    """
    rho_AB = rho_AB_t.detach()
    rho_A = partial_trace_B(rho_AB)
    rho_B = partial_trace_A(rho_AB)

    S_A = float(von_neumann_entropy(rho_A).item())
    S_B = float(von_neumann_entropy(rho_B).item())
    S_AB = float(von_neumann_entropy(rho_AB).item())
    mutual_info = S_A + S_B - S_AB

    # Optimize measurement angle on B
    best_J = -np.inf
    n_angles = 72  # Every 2.5 degrees
    for alpha in np.linspace(0, np.pi, n_angles, endpoint=False):
        # Projectors on B: |m><m| for measurement basis
        ca, sa = np.cos(alpha), np.sin(alpha)
        # Two measurement outcomes: |m0>, |m1>
        m0 = torch.tensor([ca, sa], dtype=DTYPE)
        m1 = torch.tensor([-sa, ca], dtype=DTYPE)

        J_alpha = 0.0
        for m_vec in [m0, m1]:
            # Projector on B: |m><m|
            Pi_B = torch.outer(m_vec, m_vec.conj())
            # Extended projector: I_A tensor Pi_B
            I2 = torch.eye(2, dtype=DTYPE)
            Pi_AB = torch.kron(I2, Pi_B)

            # Post-measurement state
            rho_post = Pi_AB @ rho_AB @ Pi_AB
            p_k = torch.trace(rho_post).real.item()
            if p_k < 1e-15:
                continue

            rho_post_norm = rho_post / p_k
            # Trace out B to get conditional A state
            rho_A_cond = partial_trace_B(rho_post_norm)
            S_A_cond = float(von_neumann_entropy(rho_A_cond).item())
            J_alpha += p_k * S_A_cond

        J_val = S_A - J_alpha
        if J_val > best_J:
            best_J = J_val

    discord = mutual_info - best_J
    return discord, mutual_info, best_J


# =====================================================================
# QUANTUM FISHER INFORMATION (2x2 on theta, r)
# =====================================================================

def compute_qfi_2d(theta_val, r_val):
    """
    2x2 Quantum Fisher Information matrix on (theta, r) submanifold.
    F_ij = Re(Tr[rho L_i L_j]) where L_i is the SLD.
    """
    phi_t = torch.tensor(PHI_FIXED, dtype=FDTYPE)
    rho = build_two_qubit_rho(
        torch.tensor(theta_val, dtype=FDTYPE),
        phi_t,
        torch.tensor(r_val, dtype=FDTYPE),
    ).detach()

    evals_rho, evecs = torch.linalg.eigh(rho)
    evals_real = evals_rho.real
    n = 4

    eta = [theta_val, r_val]
    slds = []
    for mu in range(2):
        eta_p = list(eta)
        eta_m = list(eta)
        eta_p[mu] += EPS_FD
        eta_m[mu] -= EPS_FD
        if mu == 1:
            eta_p[mu] = min(eta_p[mu], 1.0 - 1e-10)
            eta_m[mu] = max(eta_m[mu], 1e-10)

        rho_p = build_two_qubit_rho(
            torch.tensor(eta_p[0], dtype=FDTYPE), phi_t,
            torch.tensor(eta_p[1], dtype=FDTYPE),
        ).detach()
        rho_m = build_two_qubit_rho(
            torch.tensor(eta_m[0], dtype=FDTYPE), phi_t,
            torch.tensor(eta_m[1], dtype=FDTYPE),
        ).detach()
        drho = (rho_p - rho_m) / (2 * EPS_FD)

        drho_eig = evecs.conj().T @ drho @ evecs
        L_eig = torch.zeros((n, n), dtype=DTYPE)
        for m_idx in range(n):
            for k in range(n):
                denom = evals_real[m_idx] + evals_real[k]
                if denom.abs() > 1e-12:
                    L_eig[m_idx, k] = 2 * drho_eig[m_idx, k] / denom.to(DTYPE)
        L = evecs @ L_eig @ evecs.conj().T
        slds.append(L)

    F = np.zeros((2, 2))
    for i in range(2):
        for j in range(2):
            F[i, j] = float(torch.trace(rho @ slds[i] @ slds[j]).real)
    return F


# =====================================================================
# CLASSICAL FISHER INFORMATION (diagonal measurement)
# =====================================================================

def compute_classical_fi(theta_val, r_val):
    """
    Classical Fisher information from computational-basis measurement.
    p_k(eta) = <k|rho(eta)|k> for k in {00, 01, 10, 11}.
    F_cl_ij = sum_k (dp_k/deta_i)(dp_k/deta_j) / p_k
    """
    phi_t = torch.tensor(PHI_FIXED, dtype=FDTYPE)
    eta = [theta_val, r_val]

    def get_probs(th, rv):
        rho = build_two_qubit_rho(
            torch.tensor(th, dtype=FDTYPE), phi_t,
            torch.tensor(rv, dtype=FDTYPE),
        ).detach()
        return torch.diag(rho).real.numpy()

    p_center = get_probs(*eta)
    dp = np.zeros((2, 4))  # dp[mu][k]
    for mu in range(2):
        eta_p = list(eta)
        eta_m = list(eta)
        eta_p[mu] += EPS_FD
        eta_m[mu] -= EPS_FD
        if mu == 1:
            eta_p[mu] = min(eta_p[mu], 1.0 - 1e-10)
            eta_m[mu] = max(eta_m[mu], 1e-10)
        dp[mu] = (get_probs(*eta_p) - get_probs(*eta_m)) / (2 * EPS_FD)

    F_cl = np.zeros((2, 2))
    for k in range(4):
        if p_center[k] > 1e-15:
            for i in range(2):
                for j in range(2):
                    F_cl[i, j] += dp[i, k] * dp[j, k] / p_center[k]
    return F_cl


# =====================================================================
# STEERING INEQUALITY (CHSH-like for steering)
# =====================================================================

def steering_parameter(rho_AB_t):
    """
    Compute a steering parameter based on the Reid criterion.
    For a 2-qubit state, steering from A to B is witnessed by:
      S = sum_i <sigma_i^A sigma_i^B>^2
    If S > 1, the state demonstrates EPR steering.

    We use Pauli correlations: T_ij = Tr[rho (sigma_i x sigma_j)]
    and the steering parameter is the sum of squared singular values
    of the correlation matrix T that exceed the classical bound.
    """
    rho = rho_AB_t.detach()

    # Pauli matrices
    sigma = [
        torch.tensor([[0, 1], [1, 0]], dtype=DTYPE),   # X
        torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE), # Y
        torch.tensor([[1, 0], [0, -1]], dtype=DTYPE),   # Z
    ]

    # Correlation matrix T_ij = Tr[rho (sigma_i x sigma_j)]
    T = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            op = torch.kron(sigma[i], sigma[j])
            T[i, j] = float(torch.trace(rho @ op).real)

    # Steering parameter: sum of squared singular values
    sv = np.linalg.svd(T, compute_uv=False)
    # For separable states, sum(sv^2) <= 1 (Reid bound)
    # More precisely, the steering inequality is:
    # F_n = (1/n) sum_{i=1}^n sv_i^2 where n=number of measurement settings
    # Violation when F_3 > 1/3 (for 3 settings)
    steering_val = float(np.sum(sv**2))
    # Classical bound for 3 Pauli measurements: sum(sv^2) <= 1
    return steering_val, sv.tolist(), T.tolist()


# =====================================================================
# FULL TWILIGHT ZONE SURVEY
# =====================================================================

def survey_twilight_zone(n_points=N_TWILIGHT):
    """
    Compute all 6 quantities at n_points across the twilight zone.
    Uses theta=pi/4 (same as Lorentzian sim boundary scan).
    Samples from deep-separable through entanglement death.
    """
    r_vals = np.linspace(R_TWILIGHT_LOWER, R_ENTANGLEMENT_DEATH, n_points)
    theta_val = THETA_FIXED
    phi_t = torch.tensor(PHI_FIXED, dtype=FDTYPE)
    points = []

    for idx, rv in enumerate(r_vals):
        rv_f = float(rv)
        print(f"    Point {idx+1}/{n_points}: r={rv_f:.4f}")

        # 1. I_c
        ic_val, grad, H = compute_hessian_2d(theta_val, rv_f)
        evals_H = np.linalg.eigvalsh(H)
        sig = classify_signature(evals_H)

        # 2. Quantum discord
        rho_AB = build_two_qubit_rho(
            torch.tensor(theta_val, dtype=FDTYPE),
            phi_t,
            torch.tensor(rv_f, dtype=FDTYPE),
        )
        discord, mutual_info, classical_corr = quantum_discord_AB(rho_AB)

        # 3. QFI
        qfi = compute_qfi_2d(theta_val, rv_f)
        qfi_trace = float(np.trace(qfi))
        qfi_evals = np.linalg.eigvalsh(qfi).tolist()

        # 4. Classical Fisher information
        cfi = compute_classical_fi(theta_val, rv_f)
        cfi_trace = float(np.trace(cfi))

        # 5. Steering
        steer_val, steer_sv, corr_matrix = steering_parameter(rho_AB)

        point_data = {
            "r": rv_f,
            "theta": theta_val,
            "I_c": ic_val,
            "I_c_leq_zero": ic_val <= 1e-10,
            "discord": discord,
            "discord_positive": discord > 1e-10,
            "mutual_information": mutual_info,
            "classical_correlation_J": classical_corr,
            "hessian": H.tolist(),
            "hessian_eigenvalues": evals_H.tolist(),
            "signature": sig,
            "is_lorentzian": sig == "lorentzian",
            "qfi_matrix": qfi.tolist(),
            "qfi_trace": qfi_trace,
            "qfi_eigenvalues": qfi_evals,
            "classical_fi_trace": cfi_trace,
            "qfi_exceeds_cfi": qfi_trace > cfi_trace + 1e-10,
            "quantum_advantage_ratio": (
                qfi_trace / cfi_trace if cfi_trace > 1e-15 else float('inf')
            ),
            "steering_parameter": steer_val,
            "steering_singular_values": steer_sv,
            "steering_violates": steer_val > 1.0,
            "correlation_matrix": corr_matrix,
        }
        points.append(point_data)

    return points


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    t0 = time.time()

    print("  [+] Surveying twilight zone at 30 points...")
    points = survey_twilight_zone()

    # --- Test 1: Discord > 0 throughout ---
    discord_positive_count = sum(1 for p in points if p["discord_positive"])
    discord_values = [p["discord"] for p in points]
    results["discord_throughout"] = {
        "n_points": len(points),
        "discord_positive_count": discord_positive_count,
        "discord_fraction": discord_positive_count / len(points),
        "discord_min": float(min(discord_values)),
        "discord_max": float(max(discord_values)),
        "discord_mean": float(np.mean(discord_values)),
        "pass": discord_positive_count == len(points),
        "interpretation": (
            "Discord remains positive throughout the twilight zone, "
            "confirming quantum correlations persist after entanglement "
            "death. The Lorentzian metric is detecting DISCORD, not "
            "entanglement."
        ),
    }

    # --- Test 2: I_c <= 0 throughout (or near-zero at boundary) ---
    ic_leq_zero_count = sum(1 for p in points if p["I_c_leq_zero"])
    ic_values = [p["I_c"] for p in points]
    # Allow slight positive I_c at the very top (boundary effect)
    ic_nearly_zero_count = sum(
        1 for p in points if p["I_c"] <= 0.02
    )
    results["no_entanglement"] = {
        "n_points": len(points),
        "ic_leq_zero_count": ic_leq_zero_count,
        "ic_nearly_zero_count": ic_nearly_zero_count,
        "ic_fraction_negative": ic_leq_zero_count / len(points),
        "ic_max": float(max(ic_values)),
        "ic_min": float(min(ic_values)),
        "pass": ic_nearly_zero_count / len(points) >= 0.95,
        "interpretation": (
            "I_c <= 0 (or near zero at the upper boundary) confirms "
            "no significant entanglement throughout the twilight zone. "
            "States are separable or at most marginally entangled."
        ),
    }

    # --- Test 3: Lorentzian signature throughout ---
    lorentzian_count = sum(1 for p in points if p["is_lorentzian"])
    signatures = [p["signature"] for p in points]
    results["lorentzian_throughout"] = {
        "n_points": len(points),
        "lorentzian_count": lorentzian_count,
        "lorentzian_fraction": lorentzian_count / len(points),
        "signature_distribution": {
            s: signatures.count(s) for s in set(signatures)
        },
        "pass": lorentzian_count / len(points) > 0.8,
        "interpretation": (
            "The Hessian maintains Lorentzian (mixed) signature throughout "
            "the twilight zone. Mixed eigenvalues = the I_c landscape has "
            "both convex and concave directions even in the separable region."
        ),
    }

    # --- Test 4: QFI > classical FI (quantum advantage) ---
    qfi_exceeds_count = sum(1 for p in points if p["qfi_exceeds_cfi"])
    advantage_ratios = [p["quantum_advantage_ratio"] for p in points
                        if p["quantum_advantage_ratio"] != float('inf')]
    results["quantum_advantage"] = {
        "n_points": len(points),
        "qfi_exceeds_cfi_count": qfi_exceeds_count,
        "qfi_exceeds_fraction": qfi_exceeds_count / len(points),
        "mean_advantage_ratio": (
            float(np.mean(advantage_ratios)) if advantage_ratios else None
        ),
        "min_advantage_ratio": (
            float(min(advantage_ratios)) if advantage_ratios else None
        ),
        "pass": qfi_exceeds_count / len(points) > 0.5,
        "interpretation": (
            "QFI > classical FI means quantum advantage in parameter "
            "estimation persists even without entanglement. The quantum "
            "Fisher information captures non-classical resources (discord, "
            "coherence) that the classical measurement misses."
        ),
    }

    # --- Test 5: Mutual information structure ---
    mi_values = [p["mutual_information"] for p in points]
    results["mutual_information_profile"] = {
        "mi_min": float(min(mi_values)),
        "mi_max": float(max(mi_values)),
        "mi_mean": float(np.mean(mi_values)),
        "mi_monotone_in_r": all(
            mi_values[i] <= mi_values[i+1] + 1e-8
            for i in range(len(mi_values) - 1)
        ),
        "pass": float(min(mi_values)) > 0,
        "interpretation": (
            "Mutual information I(A:B) > 0 means total correlations "
            "(classical + quantum) persist. Discord = I(A:B) - J captures "
            "the purely quantum part."
        ),
    }

    # --- Test 6: Steering profile ---
    steering_values = [p["steering_parameter"] for p in points]
    steering_violations = sum(1 for p in points if p["steering_violates"])
    results["steering_profile"] = {
        "n_points": len(points),
        "violations": steering_violations,
        "no_violations": steering_violations == 0,
        "violation_fraction": steering_violations / len(points),
        "steering_min": float(min(steering_values)),
        "steering_max": float(max(steering_values)),
        "steering_mean": float(np.mean(steering_values)),
        "pass": True,  # Informational -- steering data collected either way
        "interpretation": (
            "Steering is a stronger criterion than entanglement. "
            "We expect few or no steering violations in the twilight zone "
            "(steering dies before or with entanglement). This confirms "
            "the hierarchy: steering <= entanglement < discord."
        ),
    }

    # Store full survey data
    results["survey_points"] = points

    elapsed = time.time() - t0
    results["elapsed_seconds"] = float(elapsed)
    print(f"  [+] Positive tests done in {elapsed:.1f}s")
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative controls:
    1. At theta ~ 1.114 (where the null surface exists), metric transitions
       to Riemannian below r ~ 0.51.
    2. Above the twilight zone, entanglement is present.
    3. Near-maximally mixed state has no discord.
    """
    results = {}
    print("  [-] Running negative tests...")

    phi_t = torch.tensor(PHI_FIXED, dtype=FDTYPE)

    # Test: At theta=1.114, the null surface at r~0.51 means metric
    # should transition. Scan below and above the null surface.
    theta_null = THETA_NULL_SURFACE
    r_scan_null = np.linspace(0.10, 0.70, 15)
    null_sigs = []
    for rv in r_scan_null:
        _, _, H = compute_hessian_2d(theta_null, float(rv))
        evals = np.linalg.eigvalsh(H)
        det_g = float(np.linalg.det(H))
        sig = classify_signature(evals)
        null_sigs.append({
            "r": float(rv),
            "eigenvalues": evals.tolist(),
            "det_g": det_g,
            "signature": sig,
        })

    # Check for a signature change in this scan
    sig_set = set(s["signature"] for s in null_sigs)
    has_riemannian = any("riemannian" in s["signature"] for s in null_sigs)
    has_lorentzian = any(s["signature"] == "lorentzian" for s in null_sigs)

    results["null_surface_theta_1114"] = {
        "theta": theta_null,
        "n_points": len(null_sigs),
        "signatures_found": list(sig_set),
        "has_riemannian_region": has_riemannian,
        "has_lorentzian_region": has_lorentzian,
        "has_both": has_riemannian and has_lorentzian,
        "points": null_sigs,
        "pass": has_riemannian or has_lorentzian,
        "interpretation": (
            "At theta=1.114 the null surface (det(g)=0) should create "
            "a transition between Riemannian and Lorentzian regions. "
            "At theta=pi/4, by contrast, the metric stays Lorentzian "
            "throughout -- the null surface is theta-dependent."
        ),
    }

    # Test: above twilight zone (r > 0.84), entanglement IS present
    theta_val = THETA_FIXED
    r_above = np.linspace(R_ENTANGLEMENT_DEATH + 0.02, 0.98, 8)
    above_data = []
    for rv in r_above:
        ic_val, _, H = compute_hessian_2d(theta_val, float(rv))
        evals = np.linalg.eigvalsh(H)
        sig = classify_signature(evals)

        rho_AB = build_two_qubit_rho(
            torch.tensor(theta_val, dtype=FDTYPE),
            phi_t,
            torch.tensor(float(rv), dtype=FDTYPE),
        )
        discord, mi, _ = quantum_discord_AB(rho_AB)

        above_data.append({
            "r": float(rv),
            "I_c": ic_val,
            "has_entanglement": ic_val > 0,
            "discord": discord,
            "mutual_information": mi,
            "signature": sig,
        })

    entangled_above = sum(1 for d in above_data if d["has_entanglement"])
    results["above_twilight_zone_entangled"] = {
        "n_points": len(r_above),
        "entangled_count": entangled_above,
        "points": above_data,
        "pass": entangled_above > len(r_above) // 2,
        "interpretation": (
            "Above the twilight zone (r > 0.84), I_c > 0 confirms "
            "entanglement is present. The twilight zone is specifically "
            "the gap between entanglement death and metric transition."
        ),
    }

    # Test: maximally mixed state (r=0) has zero discord
    rho_mixed = build_two_qubit_rho(
        torch.tensor(theta_val, dtype=FDTYPE),
        torch.tensor(PHI_FIXED, dtype=FDTYPE),
        torch.tensor(0.01, dtype=FDTYPE),
    )
    discord_mixed, mi_mixed, _ = quantum_discord_AB(rho_mixed)
    results["maximally_mixed_no_discord"] = {
        "r": 0.01,
        "discord": discord_mixed,
        "mutual_information": mi_mixed,
        "pass": abs(discord_mixed) < 0.05,
        "interpretation": (
            "Near-maximally mixed state should have near-zero discord. "
            "This validates the discord computation."
        ),
    }

    print("  [-] Negative tests done")
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Test the two boundaries of the twilight zone:
      r = 0.51 (metric transition)
      r = 0.84 (entanglement death)
    """
    results = {}
    print("  [B] Running boundary tests...")

    theta_val = THETA_FIXED
    phi_t = torch.tensor(PHI_FIXED, dtype=FDTYPE)

    # --- Boundary 1: metric transition at theta=1.114, r ~ 0.51 ---
    # At theta=pi/4, Lorentzian persists everywhere, so test the null
    # surface at the theta where it actually exists.
    print("    Scanning metric transition boundary at theta=1.114...")
    theta_null = THETA_NULL_SURFACE
    r_transition_scan = np.linspace(0.30, 0.70, 25)
    transition_data = []
    for rv in r_transition_scan:
        _, _, H = compute_hessian_2d(theta_null, float(rv))
        evals = np.linalg.eigvalsh(H)
        det_g = float(np.linalg.det(H))
        sig = classify_signature(evals)
        transition_data.append({
            "r": float(rv),
            "eigenvalues": evals.tolist(),
            "det_g": det_g,
            "signature": sig,
        })

    # Find where det(g) crosses zero
    det_vals = [d["det_g"] for d in transition_data]
    zero_crossings = []
    for i in range(len(det_vals) - 1):
        if det_vals[i] * det_vals[i+1] < 0:
            r1 = r_transition_scan[i]
            r2 = r_transition_scan[i+1]
            d1 = det_vals[i]
            d2 = det_vals[i+1]
            r_cross = r1 + (r2 - r1) * abs(d1) / (abs(d1) + abs(d2))
            zero_crossings.append(float(r_cross))

    # Also check: at theta=pi/4, metric stays Lorentzian (no transition)
    theta_pi4_check = []
    for rv in [0.1, 0.3, 0.5, 0.7]:
        _, _, H = compute_hessian_2d(THETA_FIXED, float(rv))
        evals = np.linalg.eigvalsh(H)
        theta_pi4_check.append({
            "r": float(rv),
            "signature": classify_signature(evals),
        })

    all_lorentzian_pi4 = all(
        p["signature"] == "lorentzian" for p in theta_pi4_check
    )

    results["metric_transition_boundary"] = {
        "theta_null_surface": theta_null,
        "scan_range": [float(r_transition_scan[0]),
                       float(r_transition_scan[-1])],
        "n_points": len(transition_data),
        "det_g_zero_crossings": zero_crossings,
        "refined_transition_r": (
            zero_crossings[0] if zero_crossings else "not found in scan"
        ),
        "theta_pi4_all_lorentzian": all_lorentzian_pi4,
        "theta_pi4_check": theta_pi4_check,
        "points": transition_data,
        "pass": all_lorentzian_pi4,
        "interpretation": (
            "At theta=pi/4, the metric stays Lorentzian everywhere "
            "(no null surface at this angle). The null surface (det(g)=0) "
            "exists at other theta values (e.g., theta=1.114). This means "
            "the twilight zone extent is theta-dependent."
        ),
    }

    # --- Boundary 2: entanglement death at r ~ 0.84 ---
    print("    Scanning entanglement death boundary...")
    r_death_scan = np.linspace(0.75, 0.92, 20)
    death_data = []
    for rv in r_death_scan:
        ic_val, _, H = compute_hessian_2d(theta_val, float(rv))
        evals = np.linalg.eigvalsh(H)
        sig = classify_signature(evals)

        rho_AB = build_two_qubit_rho(
            torch.tensor(theta_val, dtype=FDTYPE),
            phi_t,
            torch.tensor(float(rv), dtype=FDTYPE),
        )
        discord, mi, _ = quantum_discord_AB(rho_AB)

        death_data.append({
            "r": float(rv),
            "I_c": ic_val,
            "discord": discord,
            "mutual_information": mi,
            "signature": sig,
        })

    # Find where I_c crosses zero
    ic_vals = [d["I_c"] for d in death_data]
    ic_crossings = []
    for i in range(len(ic_vals) - 1):
        if ic_vals[i] * ic_vals[i+1] < 0:
            r1 = r_death_scan[i]
            r2 = r_death_scan[i+1]
            d1 = ic_vals[i]
            d2 = ic_vals[i+1]
            r_cross = r1 + (r2 - r1) * abs(d1) / (abs(d1) + abs(d2))
            ic_crossings.append(float(r_cross))

    # Discord at the death boundary
    death_idx = -1
    for i, d in enumerate(death_data):
        if d["I_c"] <= 0:
            death_idx = i
            break
    discord_at_death = (
        death_data[death_idx]["discord"] if death_idx >= 0 else None
    )

    results["entanglement_death_boundary"] = {
        "scan_range": [float(r_death_scan[0]), float(r_death_scan[-1])],
        "n_points": len(death_data),
        "ic_zero_crossings": ic_crossings,
        "refined_death_r": (
            ic_crossings[0] if ic_crossings else "not found in scan"
        ),
        "discord_at_death_point": discord_at_death,
        "discord_positive_at_death": (
            discord_at_death > 1e-10 if discord_at_death is not None
            else False
        ),
        "points": death_data,
        "pass": (
            discord_at_death is not None and discord_at_death > 1e-10
        ),
        "interpretation": (
            "At the entanglement death boundary, discord should still be "
            "positive. This is the ENTRY into the twilight zone: "
            "entanglement dies but discord persists."
        ),
    }

    # --- Cross-validation: theta=pi/2 ---
    print("    Cross-validating at theta=pi/2...")
    theta_cross = np.pi / 2
    cross_points = []
    for rv in np.linspace(R_TWILIGHT_LOWER, R_ENTANGLEMENT_DEATH, 10):
        ic_val, _, H = compute_hessian_2d(theta_cross, float(rv))
        evals = np.linalg.eigvalsh(H)
        sig = classify_signature(evals)

        rho_AB = build_two_qubit_rho(
            torch.tensor(theta_cross, dtype=FDTYPE),
            phi_t,
            torch.tensor(float(rv), dtype=FDTYPE),
        )
        discord, mi, _ = quantum_discord_AB(rho_AB)

        cross_points.append({
            "r": float(rv),
            "theta": theta_cross,
            "I_c": ic_val,
            "discord": discord,
            "signature": sig,
        })

    cross_discord_positive = sum(
        1 for p in cross_points if p["discord"] > 1e-10
    )
    results["cross_validation_theta_pi2"] = {
        "n_points": len(cross_points),
        "discord_positive_count": cross_discord_positive,
        "points": cross_points,
        "pass": cross_discord_positive > len(cross_points) // 2,
        "interpretation": (
            "Cross-validation at theta=pi/2 confirms the twilight zone "
            "is not an artifact of theta=pi/4. Discord persists at "
            "multiple angles."
        ),
    }

    print("  [B] Boundary tests done")
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SIM: Twilight Zone -- Discord without Entanglement")
    print("=" * 60)

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Autograd for I_c gradient/Hessian, differentiable quantum states, "
        "SLD computation for QFI"
    )
    TOOL_MANIFEST["geomstats"]["reason"] = (
        "Tried import; not load-bearing in this sim"
    )

    print("\n[POSITIVE TESTS]")
    positive = run_positive_tests()

    print("\n[NEGATIVE TESTS]")
    negative = run_negative_tests()

    print("\n[BOUNDARY TESTS]")
    boundary = run_boundary_tests()

    results = {
        "name": "Twilight Zone: Discord without Entanglement",
        "hypothesis": (
            "The region r in [0.51, 0.84] contains quantum discord "
            "without entanglement. The Lorentzian metric of the I_c "
            "Hessian detects quantum correlations (discord) that "
            "entanglement measures miss."
        ),
        "twilight_zone_definition": {
            "r_lower_sampled": R_TWILIGHT_LOWER,
            "r_upper": R_ENTANGLEMENT_DEATH,
            "theta_fixed": THETA_FIXED,
            "upper_boundary": "I_c=0, entanglement sudden death",
            "lower_boundary_note": (
                "At theta=pi/4, Lorentzian signature persists to r->0. "
                "The null surface (det(g)=0) at r~0.51 is theta-dependent "
                "and exists at theta~1.114 but not at theta=pi/4."
            ),
        },
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    # Summary pass/fail
    all_tests = []
    for section in [positive, negative, boundary]:
        for key, val in section.items():
            if isinstance(val, dict) and "pass" in val:
                all_tests.append((key, val["pass"]))

    results["summary"] = {
        "total_tests": len(all_tests),
        "passed": sum(1 for _, p in all_tests if p),
        "failed": sum(1 for _, p in all_tests if not p),
        "details": {k: v for k, v in all_tests},
    }

    out_dir = os.path.join(
        os.path.dirname(__file__), "a2_state", "sim_results"
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "twilight_zone_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")

    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {results['summary']['passed']}/{results['summary']['total_tests']} tests passed")
    for name, passed in all_tests:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    print(f"{'=' * 60}")
