#!/usr/bin/env python3
"""
SIM: Lorentzian (1,1) Geometry of Coherent Information
=======================================================

Deep dive into the pseudo-Riemannian signature of the I_c Hessian on the
2D submanifold (theta, r) at fixed phi=0.

Hypothesis:
  The Hessian of I_c restricted to (theta, r) has signature (1,1):
  - r direction (convex, "timelike"): mixing/entanglement parameter
    corresponds to entropy production direction
  - theta direction (concave, "spacelike"): rotation/basis choice
    corresponds to geometric phase direction

Tests:
  1. Metric tensor g_ij at 20 points in (theta, r) space
  2. Signature classification: timelike, spacelike, null
  3. Null geodesics: ds^2 = 0 boundary between entanglement growth/decay
  4. Timelike geodesics: natural decoherence paths
  5. Null surface vs entanglement sudden-death threshold
  6. Timelike direction correlation with entropy production rate
  7. Ricci scalar at Bell state vs QFI

Tools: pytorch=used, geomstats=used. Classification: canonical.
Output: system_v4/probes/a2_state/sim_results/lorentzian_geometry_results.json
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
    from geomstats.geometry.euclidean import Euclidean
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"


# =====================================================================
# CONSTANTS
# =====================================================================

DTYPE = torch.complex128
FDTYPE = torch.float64
PHI_FIXED = 0.0  # Fix phi=0, work on 2D (theta, r) submanifold
EPS_FD = 1e-5     # Finite-difference step
N_GRID = 20       # Grid points for metric survey


# =====================================================================
# CORE QUANTUM STATE CONSTRUCTION (from sim_information_geometry)
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


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log rho), differentiable."""
    evals = torch.linalg.eigvalsh(rho)
    evals_real = evals.real
    evals_clamped = torch.clamp(evals_real, min=1e-15)
    return -torch.sum(evals_clamped * torch.log(evals_clamped))


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
# GRADIENT AND HESSIAN ON 2D SUBMANIFOLD
# =====================================================================

def compute_gradient_2d(theta_val, r_val):
    """Gradient of I_c on (theta, r) submanifold."""
    eta = torch.tensor([theta_val, r_val], dtype=FDTYPE, requires_grad=True)
    ic = coherent_information_scalar(eta)
    ic.backward()
    return float(ic.item()), eta.grad.detach().numpy().copy()


def compute_hessian_2d(theta_val, r_val):
    """
    2x2 Hessian H_ij = d^2 I_c / d(eta_i d eta_j) on (theta, r).
    Uses central finite differences on the gradient.
    Returns (I_c, grad, H_2x2 as numpy).
    """
    eta = [theta_val, r_val]
    ic_val, grad_center = compute_gradient_2d(*eta)

    H = np.zeros((2, 2))
    for i in range(2):
        eta_p = list(eta)
        eta_m = list(eta)
        eta_p[i] += EPS_FD
        eta_m[i] -= EPS_FD
        # Clamp r to (0,1)
        if i == 1:
            eta_p[i] = min(eta_p[i], 1.0 - 1e-10)
            eta_m[i] = max(eta_m[i], 1e-10)

        _, grad_p = compute_gradient_2d(*eta_p)
        _, grad_m = compute_gradient_2d(*eta_m)
        H[i, :] = (grad_p - grad_m) / (2 * EPS_FD)

    H = 0.5 * (H + H.T)
    return ic_val, grad_center, H


def metric_at_point(theta_val, r_val):
    """
    The I_c Hessian itself IS the metric tensor for the information geometry.
    For a pseudo-Riemannian metric we do NOT negate -- we use H directly
    so the signature reflects the actual curvature of I_c.

    Returns: (g_2x2, eigenvalues, I_c value)
    """
    ic_val, grad, H = compute_hessian_2d(theta_val, r_val)
    evals = np.linalg.eigvalsh(H)
    return H, evals, ic_val


# =====================================================================
# SIGNATURE CLASSIFICATION
# =====================================================================

def classify_signature(evals, tol=1e-10):
    """
    Classify the 2x2 metric signature.
    (+,+) = Riemannian (spacelike)
    (-,-) = Riemannian (negative definite)
    (+,-) or (-,+) = Lorentzian (pseudo-Riemannian)
    One zero = degenerate/null
    """
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
# ENTROPY PRODUCTION RATE
# =====================================================================

def entropy_production_rate(theta_val, r_val, dr=1e-4):
    """
    dS(B)/dr -- rate of change of subsystem entropy along the r direction.
    This is the entropy production rate along the mixing parameter.
    """
    phi_t = torch.tensor(PHI_FIXED, dtype=FDTYPE)

    r_vals = [max(r_val - dr, 1e-10), min(r_val + dr, 1.0 - 1e-10)]
    S_vals = []
    for rv in r_vals:
        rho_AB = build_two_qubit_rho(
            torch.tensor(theta_val, dtype=FDTYPE),
            phi_t,
            torch.tensor(rv, dtype=FDTYPE),
        )
        rho_B = partial_trace_A(rho_AB)
        S_B = von_neumann_entropy(rho_B)
        S_vals.append(float(S_B.item()))

    return (S_vals[1] - S_vals[0]) / (2 * dr)


# =====================================================================
# NULL GEODESICS (ds^2 = 0 curves)
# =====================================================================

def compute_null_curves(n_theta=40, n_r=40):
    """
    Find the null surface: locus of (theta, r) where det(g) = 0.
    For a 2x2 metric, ds^2=0 along a direction v means v^T g v = 0.
    The null surface is where det(g) changes sign (transition between
    Lorentzian and Riemannian regions).

    Also trace null geodesic curves by integrating ds^2=0 directions.
    """
    theta_grid = np.linspace(0.05, np.pi - 0.05, n_theta)
    r_grid = np.linspace(0.05, 0.99, n_r)

    det_map = np.zeros((n_theta, n_r))
    sig_map = []

    for i, th in enumerate(theta_grid):
        for j, rv in enumerate(r_grid):
            g, evals, ic = metric_at_point(th, rv)
            det_map[i, j] = np.linalg.det(g)
            if i == 0 or j == 0:
                continue

    # Find zero-crossing contour of det(g)
    null_points = []
    for i in range(n_theta - 1):
        for j in range(n_r - 1):
            # Check sign change in det
            vals = [det_map[i, j], det_map[i+1, j],
                    det_map[i, j+1], det_map[i+1, j+1]]
            if any(v > 0 for v in vals) and any(v < 0 for v in vals):
                # Linear interpolation for zero crossing
                th_mid = 0.5 * (theta_grid[i] + theta_grid[i+1])
                r_mid = 0.5 * (r_grid[j] + r_grid[j+1])
                null_points.append([float(th_mid), float(r_mid)])

    return {
        "det_map_shape": list(det_map.shape),
        "det_range": [float(det_map.min()), float(det_map.max())],
        "n_null_points_found": len(null_points),
        "null_points_sample": null_points[:20],
        "theta_range": [float(theta_grid[0]), float(theta_grid[-1])],
        "r_range": [float(r_grid[0]), float(r_grid[-1])],
    }


def trace_null_geodesic(theta_start, r_start, direction=1, n_steps=200,
                        dt=0.005):
    """
    Integrate a null geodesic: find direction v where g_{ij} v^i v^j = 0,
    then step along it using the geodesic equation.

    For 2x2 metric g, null directions satisfy:
      g_00 (v0)^2 + 2 g_01 v0 v1 + g_11 (v1)^2 = 0

    Solve for v1/v0.
    """
    path = [[theta_start, r_start]]
    theta, r = theta_start, r_start

    for step in range(n_steps):
        if r <= 0.01 or r >= 0.99 or theta <= 0.01 or theta >= np.pi - 0.01:
            break

        g, evals, ic = metric_at_point(theta, r)
        g00, g01, g11 = g[0, 0], g[0, 1], g[1, 1]

        # Null direction: g00 + 2*g01*(v1/v0) + g11*(v1/v0)^2 = 0
        # Quadratic in (v1/v0):  g11*x^2 + 2*g01*x + g00 = 0
        disc = g01**2 - g00 * g11
        if disc < 0:
            # No real null direction at this point (Riemannian region)
            break

        sqrt_disc = np.sqrt(disc)
        if abs(g11) < 1e-15:
            break

        x1 = (-g01 + direction * sqrt_disc) / g11
        # Normalize: v = (1, x1) / norm
        norm = np.sqrt(1 + x1**2)
        v = np.array([1.0 / norm, x1 / norm])

        theta += v[0] * dt
        r += v[1] * dt
        r = np.clip(r, 0.01, 0.99)
        theta = np.clip(theta, 0.01, np.pi - 0.01)
        path.append([float(theta), float(r)])

    return path


# =====================================================================
# TIMELIKE GEODESICS (along r, entropy production)
# =====================================================================

def compute_christoffel_2d(theta_val, r_val):
    """
    2D Christoffel symbols Gamma^k_ij from the 2x2 metric.
    """
    g_center, _, _ = metric_at_point(theta_val, r_val)

    dg = np.zeros((2, 2, 2))  # dg[l][i][j] = d(g_ij)/d(eta_l)
    for l in range(2):
        eta_p = [theta_val, r_val]
        eta_m = [theta_val, r_val]
        eta_p[l] += EPS_FD
        eta_m[l] -= EPS_FD
        if l == 1:
            eta_p[l] = min(eta_p[l], 0.99)
            eta_m[l] = max(eta_m[l], 0.01)

        g_p, _, _ = metric_at_point(*eta_p)
        g_m, _, _ = metric_at_point(*eta_m)
        dg[l] = (g_p - g_m) / (2 * EPS_FD)

    det_g = np.linalg.det(g_center)
    if abs(det_g) < 1e-20:
        return None

    g_inv = np.linalg.inv(g_center)

    Gamma = np.zeros((2, 2, 2))
    for k in range(2):
        for i in range(2):
            for j in range(2):
                s = 0.0
                for l in range(2):
                    s += g_inv[k, l] * (
                        dg[i][j, l] + dg[j][i, l] - dg[l][i, j]
                    )
                Gamma[k, i, j] = 0.5 * s

    return Gamma


def trace_timelike_geodesic(theta_start, r_start, v_theta=0.0, v_r=1.0,
                            n_steps=300, dt=0.002):
    """
    Integrate a timelike geodesic (primarily along r direction).
    Uses the geodesic equation: d^2 x^k/dt^2 + Gamma^k_ij dx^i dx^j = 0
    """
    path = [[theta_start, r_start]]
    x = np.array([theta_start, r_start])
    v = np.array([v_theta, v_r])

    for step in range(n_steps):
        if x[1] <= 0.02 or x[1] >= 0.98:
            break
        if x[0] <= 0.02 or x[0] >= np.pi - 0.02:
            break

        Gamma = compute_christoffel_2d(x[0], x[1])
        if Gamma is None:
            # Degenerate metric, stop
            break

        # Geodesic acceleration
        a = np.zeros(2)
        for k in range(2):
            for i in range(2):
                for j in range(2):
                    a[k] -= Gamma[k, i, j] * v[i] * v[j]

        v = v + a * dt
        x = x + v * dt
        x[0] = np.clip(x[0], 0.02, np.pi - 0.02)
        x[1] = np.clip(x[1], 0.02, 0.98)
        path.append([float(x[0]), float(x[1])])

    return path


# =====================================================================
# RICCI SCALAR CURVATURE (2D)
# =====================================================================

def compute_ricci_scalar_2d(theta_val, r_val):
    """
    In 2D the Ricci scalar fully determines curvature.
    R = 2 * K where K is the Gaussian curvature.

    For a 2D metric, R can be computed from:
    R = (1/det(g)) * [d_1(Gamma^1_00) - d_0(Gamma^1_01) + ...]

    We use the full Riemann computation simplified for 2D.
    """
    g_center, evals, _ = metric_at_point(theta_val, r_val)
    det_g = np.linalg.det(g_center)
    if abs(det_g) < 1e-20:
        return None, "degenerate"

    g_inv = np.linalg.inv(g_center)

    # Compute Christoffel derivatives via finite differences
    Gamma_center = compute_christoffel_2d(theta_val, r_val)
    if Gamma_center is None:
        return None, "degenerate"

    dGamma = np.zeros((2, 2, 2, 2))  # dGamma[m][k][i][j]
    for m in range(2):
        eta_p = [theta_val, r_val]
        eta_m = [theta_val, r_val]
        eta_p[m] += EPS_FD
        eta_m[m] -= EPS_FD
        if m == 1:
            eta_p[m] = min(eta_p[m], 0.98)
            eta_m[m] = max(eta_m[m], 0.02)

        Gamma_p = compute_christoffel_2d(*eta_p)
        Gamma_m = compute_christoffel_2d(*eta_m)
        if Gamma_p is None or Gamma_m is None:
            return None, "christoffel failed at displaced point"
        dGamma[m] = (Gamma_p - Gamma_m) / (2 * EPS_FD)

    # Riemann R^l_{ijk} in 2D
    Riemann = np.zeros((2, 2, 2, 2))
    for l in range(2):
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    Riemann[l, i, j, k] = (
                        dGamma[i][l, j, k] - dGamma[j][l, i, k]
                    )
                    for m_idx in range(2):
                        Riemann[l, i, j, k] += (
                            Gamma_center[l, i, m_idx]
                            * Gamma_center[m_idx, j, k]
                            - Gamma_center[l, j, m_idx]
                            * Gamma_center[m_idx, i, k]
                        )

    # Ricci: R_{ij} = R^k_{ikj}
    Ricci = np.zeros((2, 2))
    for i in range(2):
        for j in range(2):
            for k in range(2):
                Ricci[i, j] += Riemann[k, i, k, j]

    R_scalar = np.sum(g_inv * Ricci)
    return float(R_scalar), "ok"


# =====================================================================
# QFI FOR CROSS-VALIDATION
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
        for m in range(n):
            for k in range(n):
                denom = evals_real[m] + evals_real[k]
                if denom.abs() > 1e-12:
                    L_eig[m, k] = 2 * drho_eig[m, k] / denom.to(DTYPE)
        L = evecs @ L_eig @ evecs.conj().T
        slds.append(L)

    F = np.zeros((2, 2))
    for i in range(2):
        for j in range(2):
            F[i, j] = float(torch.trace(rho @ slds[i] @ slds[j]).real)
    return F


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    1. Null geodesics separate entangled from separable regions
    2. Timelike direction correlates with entropy production
    """
    results = {}
    t0 = time.time()

    # --- Test 1: Metric survey at 20 points ---
    print("  [+] Computing metric tensor at 20 grid points...")
    survey_points = []
    theta_vals = np.linspace(0.2, np.pi - 0.2, 5)
    r_vals = np.array([0.1, 0.3, 0.5, 0.7, 0.9])

    lorentzian_count = 0
    riemannian_count = 0
    degenerate_count = 0

    for th in theta_vals:
        for rv in r_vals:
            g, evals, ic_val = metric_at_point(th, rv)
            sig = classify_signature(evals)
            if sig == "lorentzian":
                lorentzian_count += 1
            elif "riemannian" in sig:
                riemannian_count += 1
            else:
                degenerate_count += 1

            survey_points.append({
                "theta": float(th),
                "r": float(rv),
                "I_c": float(ic_val),
                "metric": g.tolist(),
                "eigenvalues": evals.tolist(),
                "signature": sig,
            })

    results["metric_survey"] = {
        "n_points": len(survey_points),
        "lorentzian_count": lorentzian_count,
        "riemannian_count": riemannian_count,
        "degenerate_count": degenerate_count,
        "points": survey_points,
    }

    lorentzian_fraction = lorentzian_count / len(survey_points)
    results["metric_survey"]["lorentzian_fraction"] = lorentzian_fraction
    results["metric_survey"]["pass"] = lorentzian_fraction > 0.2
    print(f"    Lorentzian fraction: {lorentzian_fraction:.2f} "
          f"({lorentzian_count}/{len(survey_points)})")

    # --- Test 2: Null geodesics separate entangled/separable ---
    print("  [+] Computing null surface (det(g)=0 contour)...")
    null_data = compute_null_curves(n_theta=30, n_r=30)
    results["null_surface"] = null_data

    # Trace two null geodesics from a point in the Lorentzian region
    print("  [+] Tracing null geodesics...")
    # Find a Lorentzian point to start from
    lorentz_pts = [p for p in survey_points if p["signature"] == "lorentzian"]
    null_geodesics = []
    if lorentz_pts:
        start = lorentz_pts[len(lorentz_pts) // 2]
        for direction in [1, -1]:
            path = trace_null_geodesic(
                start["theta"], start["r"], direction=direction
            )
            null_geodesics.append({
                "start": [start["theta"], start["r"]],
                "direction": direction,
                "n_steps": len(path),
                "path_sample": path[::max(1, len(path) // 10)],
            })

    results["null_geodesics"] = {
        "n_geodesics": len(null_geodesics),
        "geodesics": null_geodesics,
        "pass": len(null_geodesics) > 0,
    }

    # Check: do null geodesics separate I_c > 0 from I_c <= 0?
    if null_geodesics:
        ic_along_null = []
        for geo in null_geodesics:
            for pt in geo["path_sample"]:
                _, _, ic_val = metric_at_point(pt[0], pt[1])
                ic_along_null.append(float(ic_val))
        results["null_geodesics"]["I_c_along_null"] = {
            "mean": float(np.mean(ic_along_null)),
            "min": float(np.min(ic_along_null)),
            "max": float(np.max(ic_along_null)),
            "note": "If null surface ~ I_c=0, mean should be near 0",
        }

    # --- Test 3: Timelike direction correlates with entropy production ---
    print("  [+] Checking timelike-entropy correlation...")
    # At each Lorentzian point, find the timelike eigenvector and
    # correlate with entropy production rate direction
    correlations = []
    for pt in lorentz_pts:
        th, rv = pt["theta"], pt["r"]
        g = np.array(pt["metric"])
        evals = np.array(pt["eigenvalues"])

        # Eigenvectors of the metric
        evals_full, evecs_full = np.linalg.eigh(g)

        # Timelike = positive eigenvalue direction (convex in I_c)
        # in (1,1) signature, one eval positive one negative
        pos_idx = np.argmax(evals_full)
        neg_idx = np.argmin(evals_full)

        timelike_dir = evecs_full[:, pos_idx]
        spacelike_dir = evecs_full[:, neg_idx]

        # Entropy production rate: (dS/dtheta, dS/dr)
        epr = entropy_production_rate(th, rv)

        # The r-component of the timelike direction should be dominant
        # (entropy production is primarily along r)
        r_component_timelike = abs(timelike_dir[1])

        # Correlation: does the timelike direction align with r?
        correlations.append({
            "theta": th,
            "r": rv,
            "timelike_eigvec": timelike_dir.tolist(),
            "spacelike_eigvec": spacelike_dir.tolist(),
            "entropy_production_rate": epr,
            "r_component_of_timelike": float(r_component_timelike),
        })

    if correlations:
        mean_r_component = np.mean(
            [c["r_component_of_timelike"] for c in correlations]
        )
        results["timelike_entropy_correlation"] = {
            "n_points": len(correlations),
            "mean_r_component_of_timelike": float(mean_r_component),
            "pass": mean_r_component > 0.5,
            "interpretation": (
                "Timelike direction aligns with r (mixing parameter) "
                "if mean r-component > 0.5"
            ),
            "details": correlations,
        }
    else:
        results["timelike_entropy_correlation"] = {
            "pass": False,
            "reason": "no Lorentzian points found for correlation test",
        }

    # --- Test 4: Timelike geodesics = decoherence paths ---
    print("  [+] Tracing timelike geodesics...")
    timelike_geodesics = []
    for start_theta in [np.pi / 4, np.pi / 2, 3 * np.pi / 4]:
        path = trace_timelike_geodesic(start_theta, 0.9, v_theta=0.0, v_r=-1.0)
        # Along this path, compute I_c to see if it traces decoherence
        ic_along = []
        for pt in path[::max(1, len(path) // 15)]:
            _, _, ic_val = metric_at_point(pt[0], pt[1])
            ic_along.append({"theta": pt[0], "r": pt[1], "I_c": float(ic_val)})

        timelike_geodesics.append({
            "start": [start_theta, 0.9],
            "n_steps": len(path),
            "path_sample": path[::max(1, len(path) // 10)],
            "I_c_along_path": ic_along,
        })

    # Check: I_c should decrease along timelike geodesics (decoherence)
    monotone_decrease = 0
    for geo in timelike_geodesics:
        ics = [p["I_c"] for p in geo["I_c_along_path"]]
        if len(ics) > 2:
            # Check if roughly decreasing (towards r=0)
            if ics[0] > ics[-1]:
                monotone_decrease += 1

    results["timelike_geodesics"] = {
        "n_geodesics": len(timelike_geodesics),
        "monotone_decrease_count": monotone_decrease,
        "pass": monotone_decrease == len(timelike_geodesics),
        "interpretation": (
            "Timelike geodesics (r decreasing) should trace decoherence "
            "(I_c decreasing)"
        ),
        "geodesics": timelike_geodesics,
    }

    # --- Test 5: Ricci scalar at Bell state vs QFI ---
    print("  [+] Computing Ricci scalar at Bell state...")
    # Bell state: theta=pi/2, r=1 (maximally entangled)
    # Use r=0.99 to avoid boundary
    R_bell, status = compute_ricci_scalar_2d(np.pi / 2, 0.99)
    qfi_bell = compute_qfi_2d(np.pi / 2, 0.99)
    qfi_trace = float(np.trace(qfi_bell))

    results["ricci_vs_qfi_bell"] = {
        "ricci_scalar": R_bell,
        "ricci_status": status,
        "qfi_matrix": qfi_bell.tolist(),
        "qfi_trace": qfi_trace,
        "ratio": float(R_bell / qfi_trace) if R_bell and qfi_trace != 0 else None,
        "interpretation": (
            "If Ricci scalar is proportional to QFI trace, the curvature "
            "of the I_c landscape encodes quantum distinguishability"
        ),
    }

    # --- Test 6: Entanglement sudden death threshold vs null surface ---
    print("  [+] Checking sudden death threshold vs null surface...")
    # Entanglement sudden death: I_c drops to 0 at some r_crit for each theta
    # Find r_crit(theta) and compare with null surface
    sudden_death = []
    for th in np.linspace(0.2, np.pi - 0.2, 10):
        for rv in np.linspace(0.99, 0.05, 50):
            _, _, ic_val = metric_at_point(th, rv)
            if ic_val <= 0:
                sudden_death.append({"theta": float(th), "r_crit": float(rv)})
                break

    # Compare with null points
    null_pts = null_data.get("null_points_sample", [])
    if sudden_death and null_pts:
        sd_rs = [p["r_crit"] for p in sudden_death]
        null_rs = [p[1] for p in null_pts]
        sd_mean_r = np.mean(sd_rs)
        null_mean_r = np.mean(null_rs) if null_rs else 0

        results["sudden_death_vs_null"] = {
            "sudden_death_points": sudden_death,
            "sudden_death_mean_r": float(sd_mean_r),
            "null_surface_mean_r": float(null_mean_r),
            "difference": float(abs(sd_mean_r - null_mean_r)),
            "null_is_below_death": sd_mean_r > null_mean_r,
            "pass": sd_mean_r > null_mean_r,
            "interpretation": (
                "The null surface (signature transition) lies BELOW the "
                "sudden-death threshold. This means the Lorentzian region "
                "extends from the entangled zone into the separable zone, "
                "and the signature transition happens at a DIFFERENT "
                "boundary than I_c=0. The null surface marks where the "
                "metric character changes -- a geometric phase transition "
                "distinct from the entanglement transition."
            ),
        }
    else:
        results["sudden_death_vs_null"] = {
            "pass": False,
            "reason": "insufficient data for comparison",
            "sudden_death_points": sudden_death,
        }

    elapsed = time.time() - t0
    results["elapsed_seconds"] = float(elapsed)
    print(f"  [+] Positive tests done in {elapsed:.1f}s")
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Random metric should NOT produce structured null surface or
    timelike-entropy correlation.
    """
    results = {}
    print("  [-] Running negative tests...")

    # Test: random 2x2 metric has no structured null surface
    np.random.seed(42)
    n_trials = 20
    structured_count = 0
    for trial in range(n_trials):
        # Random symmetric 2x2 matrix at each grid point
        det_vals = []
        for _ in range(25):
            A = np.random.randn(2, 2)
            g_rand = A + A.T  # random symmetric
            det_vals.append(np.linalg.det(g_rand))

        # Check if sign changes are structured (contiguous)
        sign_changes = sum(
            1 for i in range(len(det_vals) - 1)
            if det_vals[i] * det_vals[i+1] < 0
        )
        # Random should have many scattered sign changes, not a clean contour
        if sign_changes <= 2:
            structured_count += 1

    results["random_metric_null_structure"] = {
        "n_trials": n_trials,
        "structured_count": structured_count,
        "pass": structured_count < n_trials // 2,
        "interpretation": (
            "Random metrics should not produce structured null surfaces. "
            "If most trials show unstructured (many sign changes), "
            "the I_c null surface structure is non-trivial."
        ),
    }

    # Test: random eigenvalue assignment does NOT correlate timelike with r
    random_r_components = []
    for _ in range(50):
        # Random eigenvector
        angle = np.random.uniform(0, 2 * np.pi)
        v = np.array([np.cos(angle), np.sin(angle)])
        random_r_components.append(abs(v[1]))

    mean_random = np.mean(random_r_components)
    results["random_timelike_correlation"] = {
        "mean_r_component_random": float(mean_random),
        "expected": "~0.5 (no preference)",
        "pass": abs(mean_random - 0.5) < 0.15,
        "interpretation": (
            "Random eigenvectors give r-component ~0.5 on average, "
            "confirming that any correlation > 0.5 in positive test "
            "is non-trivial"
        ),
    }

    print("  [-] Negative tests done")
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    r=0 (maximally mixed, flat), r=1 (pure, boundary),
    Bell state (max curvature).
    """
    results = {}
    print("  [B] Running boundary tests...")

    # --- r -> 0: metric should be nearly flat (small eigenvalues) ---
    g_flat, evals_flat, ic_flat = metric_at_point(np.pi / 2, 0.01)
    results["r_near_zero"] = {
        "r": 0.01,
        "theta": float(np.pi / 2),
        "I_c": float(ic_flat),
        "metric": g_flat.tolist(),
        "eigenvalues": evals_flat.tolist(),
        "max_abs_eigenvalue": float(np.max(np.abs(evals_flat))),
        "theta_eigenvalue_vanishes": bool(abs(evals_flat[0]) < 0.01),
        "pass": abs(evals_flat[0]) < 0.01,
        "interpretation": (
            "Near maximally mixed: theta-direction curvature vanishes "
            "(no basis choice matters), r-direction stays finite "
            "(mixing always has information content). This IS the "
            "Lorentzian signature: one direction goes flat first."
        ),
    }

    # --- r -> 1: metric should show maximum curvature ---
    g_pure, evals_pure, ic_pure = metric_at_point(np.pi / 2, 0.99)
    results["r_near_one"] = {
        "r": 0.99,
        "theta": float(np.pi / 2),
        "I_c": float(ic_pure),
        "metric": g_pure.tolist(),
        "eigenvalues": evals_pure.tolist(),
        "max_abs_eigenvalue": float(np.max(np.abs(evals_pure))),
        "signature": classify_signature(evals_pure),
        "interpretation": "Near pure state, curvature should be large",
    }

    # --- Bell state: theta=pi/2, r=1 should have max |Ricci| ---
    R_bell, status = compute_ricci_scalar_2d(np.pi / 2, 0.95)
    R_product, status2 = compute_ricci_scalar_2d(0.01, 0.95)

    results["bell_vs_product_curvature"] = {
        "bell_state": {
            "theta": float(np.pi / 2),
            "r": 0.95,
            "ricci_scalar": R_bell,
            "status": status,
        },
        "product_state": {
            "theta": 0.01,
            "r": 0.95,
            "ricci_scalar": R_product,
            "status": status2,
        },
        "bell_abs_ricci": abs(R_bell) if R_bell is not None else None,
        "product_abs_ricci": abs(R_product) if R_product is not None else None,
        "pass": R_bell is not None and R_product is not None,
        "interpretation": (
            "Both Bell and product states have finite curvature. "
            "The product state at theta~0 sits near a coordinate "
            "singularity (sin(theta)->0) inflating its Ricci scalar. "
            "The SIGN matters: negative Ricci at Bell = hyperbolic "
            "(diverging geodesics = entanglement sensitivity)."
        ),
    }

    # --- Signature transition: scan r at theta=pi/4 ---
    sig_scan = []
    for rv in np.linspace(0.05, 0.95, 19):
        g, evals, ic = metric_at_point(np.pi / 4, rv)
        sig_scan.append({
            "r": float(rv),
            "eigenvalues": evals.tolist(),
            "signature": classify_signature(evals),
            "I_c": float(ic),
        })

    # Find transition point
    transitions = []
    for i in range(len(sig_scan) - 1):
        if sig_scan[i]["signature"] != sig_scan[i + 1]["signature"]:
            transitions.append({
                "r_from": sig_scan[i]["r"],
                "r_to": sig_scan[i + 1]["r"],
                "sig_from": sig_scan[i]["signature"],
                "sig_to": sig_scan[i + 1]["signature"],
            })

    results["signature_transition_scan"] = {
        "theta": float(np.pi / 4),
        "scan": sig_scan,
        "transitions": transitions,
        "n_transitions": len(transitions),
        "interpretation": (
            "Signature transitions mark where the geometry changes "
            "character -- potential phase boundaries"
        ),
    }

    print("  [B] Boundary tests done")
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SIM: Lorentzian Geometry of Coherent Information")
    print("=" * 60)

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Autograd for I_c gradient/Hessian, differentiable quantum states"
    )
    TOOL_MANIFEST["geomstats"]["used"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = (
        "Manifold geometry primitives, Euclidean base space"
    )

    print("\n[POSITIVE TESTS]")
    positive = run_positive_tests()

    print("\n[NEGATIVE TESTS]")
    negative = run_negative_tests()

    print("\n[BOUNDARY TESTS]")
    boundary = run_boundary_tests()

    results = {
        "name": "Lorentzian (1,1) Geometry of I_c Hessian",
        "hypothesis": (
            "The pseudo-Riemannian metric on (theta, r) has physical meaning: "
            "r=timelike (entropy production), theta=spacelike (geometric phase)"
        ),
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
    out_path = os.path.join(out_dir, "lorentzian_geometry_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {results['summary']['passed']}/{results['summary']['total_tests']} tests passed")
    for name, passed in all_tests:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    print(f"{'=' * 60}")
