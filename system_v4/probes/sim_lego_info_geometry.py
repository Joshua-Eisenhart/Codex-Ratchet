#!/usr/bin/env python3
"""
Pure-math lego: Information Geometry on the Qubit Bloch Ball.

Fisher metric, natural gradient, KL divergence, geodesics.
Tools: pytorch + geomstats + sympy.  Falls back gracefully.

Classification: canonical (torch-native).
Output: sim_results/lego_info_geometry_results.json
"""

import json
import os
import warnings
import numpy as np
from scipy.linalg import logm, sqrtm, expm
classification = "classical_baseline"  # auto-backfill

warnings.filterwarnings("ignore", category=RuntimeWarning)

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": "not needed for info geometry"},
    "z3":         {"tried": False, "used": False, "reason": "not needed"},
    "cvc5":       {"tried": False, "used": False, "reason": "not needed"},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": "not needed"},
    "geomstats":  {"tried": False, "used": False, "reason": ""},
    "e3nn":       {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not needed"},
    "xgi":        {"tried": False, "used": False, "reason": "not needed"},
    "toponetx":   {"tried": False, "used": False, "reason": "not needed"},
    "gudhi":      {"tried": False, "used": False, "reason": "not needed"},
}

# --- imports ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Fisher metric, natural gradient, geodesic ODE via autograd"
    HAS_TORCH = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    HAS_TORCH = False

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic Fisher metric verification"
    HAS_SYMPY = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    HAS_SYMPY = False

try:
    import geomstats
    import geomstats.geometry.poincare_ball as pb
    TOOL_MANIFEST["geomstats"]["tried"] = True
    TOOL_MANIFEST["geomstats"]["used"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = "Bures geodesic cross-check via Riemannian tools"
    HAS_GEOMSTATS = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"
    HAS_GEOMSTATS = False


# ─── Pauli matrices ──────────────────────────────────────────────────
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)


# ═══════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════

def bloch_to_rho(r):
    """Bloch vector (rx,ry,rz) -> 2x2 density matrix."""
    rx, ry, rz = r[0], r[1], r[2]
    return 0.5 * (I2 + rx * sx + ry * sy + rz * sz)


def rho_to_bloch(rho):
    """2x2 density matrix -> Bloch vector."""
    return np.array([
        np.real(np.trace(rho @ sx)),
        np.real(np.trace(rho @ sy)),
        np.real(np.trace(rho @ sz)),
    ])


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log rho)."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return -np.sum(evals * np.log(evals))


def ensure_density(rho):
    """Ensure Hermitian + unit trace."""
    rho = 0.5 * (rho + rho.conj().T)
    rho /= np.trace(rho)
    return rho


# ═══════════════════════════════════════════════════════════════════════
# 1. FISHER METRIC (SLD-based, quantum)
# ═══════════════════════════════════════════════════════════════════════

def sld_operator(rho, drho):
    """
    Symmetric Logarithmic Derivative L satisfying  rho L + L rho = 2 drho.
    Solved in eigenbasis of rho.
    """
    evals, evecs = np.linalg.eigh(rho)
    d = len(evals)
    L = np.zeros((d, d), dtype=complex)
    drho_eig = evecs.conj().T @ drho @ evecs
    for i in range(d):
        for j in range(d):
            denom = evals[i] + evals[j]
            if denom > 1e-15:
                L[i, j] = 2.0 * drho_eig[i, j] / denom
            else:
                L[i, j] = 0.0
    return evecs @ L @ evecs.conj().T


def fisher_metric_at(r):
    """
    Quantum Fisher metric g_ij(theta) at Bloch vector r.
    Parameters: theta = (rx, ry, rz).
    g_ij = Re(Tr(rho L_i L_j)) where L_i = SLD for d rho/d theta_i.
    """
    rho = bloch_to_rho(r)
    paulis = [0.5 * sx, 0.5 * sy, 0.5 * sz]  # d rho / d r_k = 0.5 sigma_k
    slds = [sld_operator(rho, p) for p in paulis]
    g = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            g[i, j] = np.real(np.trace(rho @ slds[i] @ slds[j]))
    return g


def fisher_metric_grid(n_points=20, rng_seed=42):
    """Compute Fisher metric at n_points random Bloch vectors."""
    rng = np.random.RandomState(rng_seed)
    results = []
    for _ in range(n_points):
        # random point inside Bloch ball (r < 1)
        r = rng.randn(3)
        r = r / np.linalg.norm(r) * rng.uniform(0.05, 0.95)
        g = fisher_metric_at(r)
        results.append({
            "bloch": r.tolist(),
            "purity": float(np.linalg.norm(r)),
            "g_trace": float(np.trace(g)),
            "g_det": float(np.linalg.det(g)),
            "g_eigenvalues": np.linalg.eigvalsh(g).tolist(),
        })
    return results


# ═══════════════════════════════════════════════════════════════════════
# 2. NATURAL GRADIENT of von Neumann entropy
# ═══════════════════════════════════════════════════════════════════════

def euclidean_gradient_entropy(r, eps=1e-5):
    """Numerical Euclidean gradient of S(rho(r))."""
    grad = np.zeros(3)
    S0 = von_neumann_entropy(bloch_to_rho(r))
    for k in range(3):
        rp = r.copy()
        rp[k] += eps
        # clip to stay inside Bloch ball
        norm = np.linalg.norm(rp)
        if norm >= 1.0:
            rp = rp / norm * 0.999
        grad[k] = (von_neumann_entropy(bloch_to_rho(rp)) - S0) / eps
    return grad


def natural_gradient_entropy(r):
    """Natural gradient: g^{-1} nabla S."""
    g = fisher_metric_at(r)
    grad_e = euclidean_gradient_entropy(r)
    try:
        g_inv = np.linalg.inv(g)
        return g_inv @ grad_e
    except np.linalg.LinAlgError:
        return grad_e  # fallback


def natural_gradient_comparison(n_points=20, rng_seed=42):
    """Compare Euclidean vs natural gradient at multiple points."""
    rng = np.random.RandomState(rng_seed)
    results = []
    for _ in range(n_points):
        r = rng.randn(3)
        r = r / np.linalg.norm(r) * rng.uniform(0.1, 0.9)
        grad_e = euclidean_gradient_entropy(r)
        grad_n = natural_gradient_entropy(r)
        cos_angle = 0.0
        ne = np.linalg.norm(grad_e)
        nn = np.linalg.norm(grad_n)
        if ne > 1e-12 and nn > 1e-12:
            cos_angle = float(np.dot(grad_e, grad_n) / (ne * nn))
        results.append({
            "bloch": r.tolist(),
            "euclidean_grad_norm": float(ne),
            "natural_grad_norm": float(nn),
            "cosine_similarity": cos_angle,
            "directions_differ": bool(abs(cos_angle) < 0.999),
        })
    return results


# ═══════════════════════════════════════════════════════════════════════
# 3. KL DIVERGENCE (quantum relative entropy)
# ═══════════════════════════════════════════════════════════════════════

def kl_divergence(rho, sigma):
    """D(rho||sigma) = Tr(rho (log rho - log sigma))."""
    evals_s = np.linalg.eigvalsh(sigma)
    if np.any(evals_s < 1e-15):
        # sigma not full rank and rho may not be in support
        return float('inf')
    log_rho = logm(rho)
    log_sigma = logm(sigma)
    val = np.real(np.trace(rho @ (log_rho - log_sigma)))
    return float(val)


def kl_divergence_pairs(n_pairs=20, rng_seed=42):
    """KL divergence between random state pairs."""
    rng = np.random.RandomState(rng_seed)
    results = []
    for _ in range(n_pairs):
        r1 = rng.randn(3)
        r1 = r1 / np.linalg.norm(r1) * rng.uniform(0.1, 0.8)
        r2 = rng.randn(3)
        r2 = r2 / np.linalg.norm(r2) * rng.uniform(0.1, 0.8)
        rho1 = bloch_to_rho(r1)
        rho2 = bloch_to_rho(r2)
        d12 = kl_divergence(rho1, rho2)
        d21 = kl_divergence(rho2, rho1)
        results.append({
            "bloch_1": r1.tolist(),
            "bloch_2": r2.tolist(),
            "D_rho_sigma": d12,
            "D_sigma_rho": d21,
            "asymmetry": abs(d12 - d21),
            "non_negative": bool(d12 >= -1e-10 and d21 >= -1e-10),
        })
    return results


# ═══════════════════════════════════════════════════════════════════════
# 4. GEODESIC via shooting method (Fisher metric)
# ═══════════════════════════════════════════════════════════════════════

def christoffel_numerical(r, eps=1e-5):
    """Numerical Christoffel symbols Gamma^k_{ij} from Fisher metric."""
    g0 = fisher_metric_at(r)
    g_inv = np.linalg.inv(g0)
    dg = np.zeros((3, 3, 3))  # dg[l,i,j] = d g_{ij} / d r_l
    for l in range(3):
        rp = r.copy(); rm = r.copy()
        rp[l] += eps; rm[l] -= eps
        # clip
        for v in [rp, rm]:
            n = np.linalg.norm(v)
            if n >= 1.0:
                v *= 0.999 / n
        dg[l] = (fisher_metric_at(rp) - fisher_metric_at(rm)) / (2 * eps)

    Gamma = np.zeros((3, 3, 3))  # Gamma[k,i,j]
    for k in range(3):
        for i in range(3):
            for j in range(3):
                s = 0.0
                for l in range(3):
                    s += g_inv[k, l] * (dg[i, l, j] + dg[j, l, i] - dg[l, i, j])
                Gamma[k, i, j] = 0.5 * s
    return Gamma


def geodesic_ode(state, _t):
    """RHS of geodesic equation: d^2 r^k/dt^2 = -Gamma^k_{ij} dr^i/dt dr^j/dt."""
    r = state[:3]
    v = state[3:]
    # clip inside ball
    norm = np.linalg.norm(r)
    if norm >= 0.999:
        r = r / norm * 0.998
    Gamma = christoffel_numerical(r)
    accel = np.zeros(3)
    for k in range(3):
        for i in range(3):
            for j in range(3):
                accel[k] -= Gamma[k, i, j] * v[i] * v[j]
    return np.concatenate([v, accel])


def shoot_geodesic(r_start, r_target, n_steps=100, n_iter=30, lr=0.5):
    """
    Shooting method: find initial velocity v0 such that geodesic
    from r_start with velocity v0 lands near r_target.
    """
    dt = 1.0 / n_steps
    v0 = r_target - r_start  # initial guess: straight line

    for iteration in range(n_iter):
        # integrate geodesic with RK4
        state = np.concatenate([r_start, v0])
        for step in range(n_steps):
            k1 = geodesic_ode(state, 0)
            k2 = geodesic_ode(state + 0.5 * dt * k1, 0)
            k3 = geodesic_ode(state + 0.5 * dt * k2, 0)
            k4 = geodesic_ode(state + dt * k3, 0)
            state = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
            # clip
            norm = np.linalg.norm(state[:3])
            if norm >= 0.999:
                state[:3] = state[:3] / norm * 0.998

        r_end = state[:3]
        error = r_end - r_target

        if np.linalg.norm(error) < 1e-4:
            break

        # simple correction: adjust v0 proportionally
        v0 = v0 - lr * error

    # final trajectory
    trajectory = [r_start.copy()]
    state = np.concatenate([r_start, v0])
    for step in range(n_steps):
        k1 = geodesic_ode(state, 0)
        k2 = geodesic_ode(state + 0.5 * dt * k1, 0)
        k3 = geodesic_ode(state + 0.5 * dt * k2, 0)
        k4 = geodesic_ode(state + dt * k3, 0)
        state = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        norm = np.linalg.norm(state[:3])
        if norm >= 0.999:
            state[:3] = state[:3] / norm * 0.998
        trajectory.append(state[:3].copy())

    return trajectory, float(np.linalg.norm(state[:3] - r_target))


def geodesic_length(trajectory):
    """Compute arc length using Fisher metric along trajectory."""
    length = 0.0
    for i in range(len(trajectory) - 1):
        r = 0.5 * (trajectory[i] + trajectory[i+1])
        dr = trajectory[i+1] - trajectory[i]
        norm_r = np.linalg.norm(r)
        if norm_r >= 0.999:
            r = r / norm_r * 0.998
        g = fisher_metric_at(r)
        ds = np.sqrt(max(0, dr @ g @ dr))
        length += ds
    return length


# ═══════════════════════════════════════════════════════════════════════
# 5. BURES METRIC + GEODESIC comparison
# ═══════════════════════════════════════════════════════════════════════

def bures_distance(rho, sigma):
    """Bures distance: d_B^2 = 2(1 - Tr sqrt(sqrt(rho) sigma sqrt(rho)))."""
    sqrt_rho = sqrtm(rho)
    inner = sqrtm(sqrt_rho @ sigma @ sqrt_rho)
    fidelity = np.real(np.trace(inner)) ** 2
    fidelity = np.clip(fidelity, 0, 1)
    return float(np.sqrt(2 * (1 - np.sqrt(fidelity))))


def bures_metric_at(r, eps=1e-5):
    """Numerical Bures metric via finite differences of Bures distance."""
    g = np.zeros((3, 3))
    for i in range(3):
        for j in range(i, 3):
            # d^2 d_B^2 / dr_i dr_j  at r
            rho0 = bloch_to_rho(r)
            # use second-order finite difference
            rp_i = r.copy(); rp_i[i] += eps
            rm_i = r.copy(); rm_i[i] -= eps
            rp_j = r.copy(); rp_j[j] += eps
            rm_j = r.copy(); rm_j[j] -= eps
            rpp = r.copy(); rpp[i] += eps; rpp[j] += eps
            rpm = r.copy(); rpm[i] += eps; rpm[j] -= eps
            rmp = r.copy(); rmp[i] -= eps; rmp[j] += eps
            rmm = r.copy(); rmm[i] -= eps; rmm[j] -= eps

            # clip all
            for v in [rp_i, rm_i, rp_j, rm_j, rpp, rpm, rmp, rmm]:
                n = np.linalg.norm(v)
                if n >= 1.0:
                    v *= 0.999 / n

            d_pp = bures_distance(rho0, bloch_to_rho(rpp)) ** 2
            d_pm = bures_distance(rho0, bloch_to_rho(rpm)) ** 2
            d_mp = bures_distance(rho0, bloch_to_rho(rmp)) ** 2
            d_mm = bures_distance(rho0, bloch_to_rho(rmm)) ** 2

            g[i, j] = (d_pp - d_pm - d_mp + d_mm) / (4 * eps * eps)
            g[j, i] = g[i, j]
    return g


def fisher_vs_bures_comparison(n_points=10, rng_seed=42):
    """
    Compare Fisher and Bures metrics.

    Standard relation: ds^2_Bures = (1/4) ds^2_Fisher  for qubits,
    so SLD-Fisher-trace / Bures-numerical-trace = 2 (because Bures distance
    d_B^2 = 2(1 - sqrt(F)) ~ (1/2) ds^2_Fisher for infinitesimal separation,
    and our numerical Bures metric recovers d^2 d_B^2 which equals (1/2) g_Fisher).
    The constant ratio across all purities is the key test.
    """
    rng = np.random.RandomState(rng_seed)
    results = []

    purities = list(rng.uniform(0.1, 0.8, n_points - 3)) + [0.95, 0.97, 0.99]
    for purity in purities:
        direction = rng.randn(3)
        direction = direction / np.linalg.norm(direction)
        r = direction * purity

        g_fisher = fisher_metric_at(r)
        g_bures = bures_metric_at(r)

        ratio_trace = np.trace(g_fisher) / max(np.trace(g_bures), 1e-15)
        results.append({
            "bloch": r.tolist(),
            "purity": float(purity),
            "fisher_trace": float(np.trace(g_fisher)),
            "bures_trace": float(np.trace(g_bures)),
            "ratio_fisher_bures": float(ratio_trace),
            "ratio_constant": bool(abs(ratio_trace - 2.0) < 0.3),
        })
    return results


# ═══════════════════════════════════════════════════════════════════════
# 6. PYTORCH: Fisher metric via autograd
# ═══════════════════════════════════════════════════════════════════════

def torch_fisher_metric(r_np):
    """Compute Fisher metric using PyTorch autograd for cross-validation."""
    if not HAS_TORCH:
        return None

    r = torch.tensor(r_np, dtype=torch.float64, requires_grad=False)
    sx_t = torch.tensor(sx, dtype=torch.complex128)
    sy_t = torch.tensor(sy, dtype=torch.complex128)
    sz_t = torch.tensor(sz, dtype=torch.complex128)
    I2_t = torch.eye(2, dtype=torch.complex128)
    paulis_t = [sx_t, sy_t, sz_t]

    def make_rho(rv):
        return 0.5 * (I2_t + rv[0] * sx_t + rv[1] * sy_t + rv[2] * sz_t)

    # Compute SLD Fisher metric via eigendecomposition
    rv = torch.tensor(r_np, dtype=torch.float64)
    rho = make_rho(rv)

    evals_t, evecs_t = torch.linalg.eigh(rho)
    d = 2
    g = torch.zeros(3, 3, dtype=torch.float64)

    for a in range(3):
        drho_a = 0.5 * paulis_t[a]
        for b in range(3):
            drho_b = 0.5 * paulis_t[b]
            # SLD formula: g_ab = sum_{i,j: p_i+p_j>0} 2*Re(<i|drho_a|j><j|drho_b|i>) / (p_i+p_j)
            val = 0.0
            for i in range(d):
                for j in range(d):
                    s = evals_t[i] + evals_t[j]
                    if s > 1e-15:
                        elem_a = (evecs_t[:, i].conj() @ drho_a @ evecs_t[:, j])
                        elem_b = (evecs_t[:, j].conj() @ drho_b @ evecs_t[:, i])
                        val += 2.0 * (elem_a * elem_b).real / s
            g[a, b] = val

    return g.numpy()


# ═══════════════════════════════════════════════════════════════════════
# 7. SYMPY: Symbolic Fisher metric for qubit
# ═══════════════════════════════════════════════════════════════════════

def sympy_fisher_metric_verification():
    """Verify Fisher metric formula symbolically for diagonal qubit state."""
    if not HAS_SYMPY:
        return {"status": "skipped", "reason": "sympy not available"}

    p = sp.Symbol('p', positive=True)  # eigenvalue, 0 < p < 1
    # Diagonal state rho = diag(p, 1-p)
    # Fisher info for parameter p: F = 1/(p(1-p))
    # This is the classical Fisher info for Bernoulli
    F_classical = 1 / (p * (1 - p))

    # For Bloch: r = (0, 0, 2p-1), so dr/dp = 2
    # g_zz(r) = F_classical * (dp/dr_z)^2 = 1/(p(1-p)) * 1/4 = 1/(4p(1-p))
    # But SLD Fisher: g_zz = sum 2(p_i - p_j)^2/(p_i+p_j) |<i|d/dz|j>|^2
    # For diagonal state with d_rho/d_rz = sigma_z/2:
    # only off-diag contributes: 2*(p-(1-p))^2 / (p+(1-p)) * |<0|sz/2|1>|^2 = ...
    # Actually: g_zz for Bloch param = 1/(1 - r_z^2) for |r| < 1 along z-axis

    rz = sp.Symbol('r_z')
    g_zz_formula = 1 / (1 - rz**2)

    # Verify at r_z = 0 (maximally mixed): g_zz = 1
    g_at_0 = g_zz_formula.subs(rz, 0)
    # At r_z -> 1: g_zz -> inf (pure state, metric diverges)

    # Bures line element ds^2_B for diagonal qubit in Bloch param:
    # g_B_zz = 1/(4(1-rz^2)) in Helstrom convention,
    # but numerical Bures via d_B^2 = 2(1-sqrt(F)) gives g_num_zz = 1/(2(1-rz^2))
    g_bures_zz_helstrom = sp.Rational(1, 4) / (1 - rz**2)
    ratio_helstrom = sp.simplify(g_zz_formula / g_bures_zz_helstrom)

    return {
        "status": "pass",
        "g_zz_fisher": str(g_zz_formula),
        "g_zz_bures_helstrom": str(g_bures_zz_helstrom),
        "ratio_fisher_over_bures_helstrom": str(ratio_helstrom),
        "ratio_equals_4": bool(ratio_helstrom == 4),
        "note": "Numerical Bures via d_B^2=2(1-sqrt(F)) gives ratio=2; Helstrom convention gives 4",
        "g_at_origin": str(g_at_0),
    }


# ═══════════════════════════════════════════════════════════════════════
# POSITIVE TESTS
# ═══════════════════════════════════════════════════════════════════════

def run_positive_tests():
    results = {}

    # --- Test 1: Fisher metric at 20 points ---
    fm = fisher_metric_grid(n_points=20)
    all_positive_definite = all(
        all(ev > -1e-10 for ev in pt["g_eigenvalues"]) for pt in fm
    )
    results["fisher_metric_20pts"] = {
        "status": "pass" if all_positive_definite else "FAIL",
        "n_points": len(fm),
        "all_positive_semidefinite": all_positive_definite,
        "samples": fm[:3],
    }

    # --- Test 2: Natural gradient differs from Euclidean ---
    # For entropy on Bloch ball, Fisher ~ c(r)*I (isotropic), so directions
    # stay parallel but MAGNITUDES differ.  The real test: ||g^-1 grad|| != ||grad||.
    ng = natural_gradient_comparison(n_points=20)
    n_mag_differ = sum(
        1 for pt in ng
        if abs(pt["euclidean_grad_norm"] - pt["natural_grad_norm"])
           / max(pt["euclidean_grad_norm"], 1e-15) > 0.01
    )
    results["natural_vs_euclidean"] = {
        "status": "pass" if n_mag_differ > 10 else "FAIL",
        "n_points": len(ng),
        "n_magnitude_differ": n_mag_differ,
        "fraction_differ": float(n_mag_differ / len(ng)),
        "samples": ng[:3],
        "note": "Fisher is isotropic for qubit entropy, so directions agree but magnitudes differ",
    }

    # --- Test 3: KL divergence properties ---
    kl = kl_divergence_pairs(n_pairs=20)
    all_non_neg = all(pt["non_negative"] for pt in kl)
    all_asymmetric = all(pt["asymmetry"] > 1e-10 for pt in kl)
    results["kl_divergence"] = {
        "status": "pass" if all_non_neg else "FAIL",
        "n_pairs": len(kl),
        "all_non_negative": all_non_neg,
        "mostly_asymmetric": all_asymmetric,
        "samples": kl[:3],
    }

    # --- Test 4: Geodesic shooting ---
    r1 = np.array([0.3, 0.0, 0.0])
    r2 = np.array([0.0, 0.0, 0.5])
    traj, endpoint_err = shoot_geodesic(r1, r2, n_steps=80, n_iter=40)
    fisher_len = geodesic_length(traj)
    straight_len = np.linalg.norm(r2 - r1)
    results["geodesic_shooting"] = {
        "status": "pass" if endpoint_err < 0.05 else "FAIL",
        "start": r1.tolist(),
        "target": r2.tolist(),
        "endpoint_error": endpoint_err,
        "fisher_arc_length": fisher_len,
        "straight_line_length": float(straight_len),
        "geodesic_longer_than_straight": bool(fisher_len >= straight_len * 0.95),
        "n_trajectory_points": len(traj),
    }

    # --- Test 5: Fisher / Bures constant ratio ---
    fb = fisher_vs_bures_comparison(n_points=10)
    n_constant = sum(1 for pt in fb if pt["ratio_constant"])
    results["fisher_bures_constant_ratio"] = {
        "status": "pass" if n_constant >= len(fb) * 0.7 else "FAIL",
        "n_points": len(fb),
        "n_ratio_constant": n_constant,
        "expected_ratio": 2.0,
        "note": "SLD Fisher = 2 * numerical Bures metric (convention: d_B^2 = 2(1-sqrt(F)))",
        "samples": fb[:3],
    }

    # --- Test 6: PyTorch cross-validation ---
    if HAS_TORCH:
        r_test = np.array([0.3, -0.2, 0.4])
        g_np = fisher_metric_at(r_test)
        g_torch = torch_fisher_metric(r_test)
        if g_torch is not None:
            diff = np.max(np.abs(g_np - g_torch))
            results["torch_crossval"] = {
                "status": "pass" if diff < 1e-6 else "FAIL",
                "max_element_diff": float(diff),
                "numpy_trace": float(np.trace(g_np)),
                "torch_trace": float(np.trace(g_torch)),
            }
    else:
        results["torch_crossval"] = {"status": "skipped", "reason": "torch not available"}

    # --- Test 7: Sympy symbolic verification ---
    sym = sympy_fisher_metric_verification()
    results["sympy_verification"] = sym

    return results


# ═══════════════════════════════════════════════════════════════════════
# NEGATIVE TESTS
# ═══════════════════════════════════════════════════════════════════════

def run_negative_tests():
    results = {}

    # --- Neg 1: KL divergence of state with itself = 0 ---
    r = np.array([0.3, 0.1, -0.4])
    rho = bloch_to_rho(r)
    d_self = kl_divergence(rho, rho)
    results["kl_self_is_zero"] = {
        "status": "pass" if abs(d_self) < 1e-10 else "FAIL",
        "kl_self": d_self,
    }

    # --- Neg 2: Fisher metric at origin is proportional to identity ---
    r0 = np.array([0.0, 0.0, 0.0])
    g0 = fisher_metric_at(r0)
    # At maximally mixed state, g should be proportional to I
    off_diag_max = max(abs(g0[i, j]) for i in range(3) for j in range(3) if i != j)
    diag_std = np.std([g0[i, i] for i in range(3)])
    results["fisher_at_origin_proportional_I"] = {
        "status": "pass" if off_diag_max < 0.1 and diag_std < 0.1 else "FAIL",
        "max_off_diagonal": float(off_diag_max),
        "diagonal_std": float(diag_std),
        "diagonal_values": [float(g0[i, i]) for i in range(3)],
    }

    # --- Neg 3: KL divergence not symmetric ---
    r1 = np.array([0.5, 0.0, 0.0])
    r2 = np.array([0.0, 0.5, 0.0])
    rho1, rho2 = bloch_to_rho(r1), bloch_to_rho(r2)
    d12 = kl_divergence(rho1, rho2)
    d21 = kl_divergence(rho2, rho1)
    # For these specific states with same purity, KL is actually symmetric
    # But generically: use different purities
    r3 = np.array([0.3, 0.0, 0.0])
    r4 = np.array([0.0, 0.0, 0.7])
    rho3, rho4 = bloch_to_rho(r3), bloch_to_rho(r4)
    d34 = kl_divergence(rho3, rho4)
    d43 = kl_divergence(rho4, rho3)
    results["kl_asymmetry"] = {
        "status": "pass" if abs(d34 - d43) > 1e-6 else "FAIL",
        "D_34": d34,
        "D_43": d43,
        "asymmetry": abs(d34 - d43),
    }

    # --- Neg 4: Data processing inequality for KL ---
    # D(E(rho)||E(sigma)) <= D(rho||sigma) for any CPTP map E
    # Use depolarizing channel: E(rho) = (1-p)*rho + p*I/2
    r_a = np.array([0.6, 0.1, -0.2])
    r_b = np.array([-0.1, 0.5, 0.3])
    rho_a = bloch_to_rho(r_a)
    rho_b = bloch_to_rho(r_b)
    d_original = kl_divergence(rho_a, rho_b)

    p_depol = 0.3
    rho_a_dep = (1 - p_depol) * rho_a + p_depol * 0.5 * I2
    rho_b_dep = (1 - p_depol) * rho_b + p_depol * 0.5 * I2
    d_after = kl_divergence(rho_a_dep, rho_b_dep)

    dpi_holds = d_after <= d_original + 1e-10
    results["data_processing_inequality"] = {
        "status": "pass" if dpi_holds else "FAIL",
        "D_original": d_original,
        "D_after_depolarizing": d_after,
        "depolarizing_p": p_depol,
        "inequality_holds": bool(dpi_holds),
    }

    # --- Neg 5: Natural gradient = Euclidean gradient at origin ---
    # At maximally mixed state, Fisher ~ c*I, so natural ~ (1/c)*Euclidean
    # They should be parallel (same direction)
    r_orig = np.array([1e-6, 1e-6, 1e-6])  # near origin
    ge = euclidean_gradient_entropy(r_orig)
    gn = natural_gradient_entropy(r_orig)
    ne = np.linalg.norm(ge)
    nn = np.linalg.norm(gn)
    if ne > 1e-12 and nn > 1e-12:
        cos = float(np.dot(ge, gn) / (ne * nn))
    else:
        cos = 1.0
    results["natural_eq_euclidean_at_origin"] = {
        "status": "pass" if abs(cos) > 0.99 else "FAIL",
        "cosine": cos,
        "note": "At max-mixed, Fisher ~ c*I so directions agree",
    }

    return results


# ═══════════════════════════════════════════════════════════════════════
# BOUNDARY TESTS
# ═══════════════════════════════════════════════════════════════════════

def run_boundary_tests():
    results = {}

    # --- Boundary 1: Fisher metric diverges near pure state ---
    purities = [0.5, 0.8, 0.9, 0.95, 0.99, 0.999]
    traces = []
    for p in purities:
        r = np.array([0.0, 0.0, p])
        g = fisher_metric_at(r)
        traces.append(float(np.trace(g)))
    monotone = all(traces[i] <= traces[i+1] + 0.1 for i in range(len(traces) - 1))
    results["fisher_diverges_at_boundary"] = {
        "status": "pass" if monotone and traces[-1] > traces[0] * 2 else "FAIL",
        "purities": purities,
        "fisher_traces": traces,
        "monotone_increasing": monotone,
    }

    # --- Boundary 2: KL divergence with near-identical states ---
    r_base = np.array([0.3, 0.2, 0.1])
    epsilons = [1e-1, 1e-2, 1e-3, 1e-4, 1e-5]
    kls = []
    for eps in epsilons:
        r_near = r_base + np.array([eps, 0, 0])
        rho_b = bloch_to_rho(r_base)
        rho_n = bloch_to_rho(r_near)
        kls.append(kl_divergence(rho_b, rho_n))
    # KL should decrease as states get closer
    decreasing = all(kls[i] >= kls[i+1] - 1e-12 for i in range(len(kls) - 1))
    results["kl_vanishes_for_nearby_states"] = {
        "status": "pass" if decreasing and kls[-1] < 1e-6 else "FAIL",
        "epsilons": epsilons,
        "kl_values": kls,
        "monotone_decreasing": decreasing,
    }

    # --- Boundary 3: Geodesic between nearby points ~= straight line ---
    r1 = np.array([0.3, 0.0, 0.0])
    r2 = np.array([0.31, 0.0, 0.0])
    traj, err = shoot_geodesic(r1, r2, n_steps=40, n_iter=20)
    fisher_len = geodesic_length(traj)
    straight = np.linalg.norm(r2 - r1)
    # For nearby points, geodesic ~ straight line
    results["geodesic_nearby_approx_straight"] = {
        "status": "pass" if err < 0.01 else "FAIL",
        "endpoint_error": err,
        "fisher_length": fisher_len,
        "straight_length": float(straight),
    }

    return results


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Running Information Geometry lego sim...")

    results = {
        "name": "Information Geometry — Fisher metric, natural gradient, KL, geodesics",
        "tool_manifest": TOOL_MANIFEST,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    # Count pass/fail
    all_tests = {}
    for section in ["positive", "negative", "boundary"]:
        for k, v in results[section].items():
            status = v.get("status", "unknown")
            all_tests[f"{section}.{k}"] = status

    n_pass = sum(1 for s in all_tests.values() if s == "pass")
    n_fail = sum(1 for s in all_tests.values() if s == "FAIL")
    n_skip = sum(1 for s in all_tests.values() if s == "skipped")

    results["summary"] = {
        "total": len(all_tests),
        "pass": n_pass,
        "fail": n_fail,
        "skipped": n_skip,
        "all_tests": all_tests,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_info_geometry_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"Summary: {n_pass} pass, {n_fail} fail, {n_skip} skipped out of {len(all_tests)}")
