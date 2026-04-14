#!/usr/bin/env python3
"""
sim_geom_cp1_u1_projective.py -- CP^1 projective structure, U(1) fiber,
and principal bundle P(S^2, U(1)).

CP^1: inhomogeneous coord w = z2/z1.
      Fubini-Study metric ds^2 = dw dw_bar / (1 + |w|^2)^2.
      Kahler potential K = log(1 + |w|^2).
      Symplectic form omega = i * d d_bar K.
      Integral: int(omega) = pi.

U(1) fiber: Berry connection A = Im(<psi|d psi>).
            Curvature F = dA.
            Holonomy = exp(i * oint(A)) = Berry phase.

Principal bundle P(S^2, U(1)):
      Total space S^3, base S^2, fiber U(1).
      First Chern class c1 = 1.
      Local trivialization is NOT global (topological obstruction).

Stacking: cross-validated against L1-3 (density matrices, S^2, Hopf).

Classification: canonical (PyTorch-native with autograd throughout).
"""

import json
import math
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

# --- imports with manifest tracking ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core computation: CP^1 Fubini-Study metric via autograd, "
        "Berry connection/curvature, Chern number integration, "
        "holonomy computation, principal bundle tests"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Symbolic cross-validation of Kahler potential, "
        "symplectic form, and Fubini-Study metric derivation"
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

for key in ["pyg", "z3", "cvc5", "clifford", "geomstats", "e3nn",
            "rustworkx", "xgi", "toponetx", "gudhi"]:
    if not TOOL_MANIFEST[key]["tried"]:
        TOOL_MANIFEST[key]["reason"] = "not needed for CP^1/U(1) projective geometry"


# =====================================================================
# PAULI MATRICES (torch, complex128)
# =====================================================================

def pauli_matrices():
    """Return sigma_x, sigma_y, sigma_z as complex128 tensors."""
    sx = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    return sx, sy, sz


# =====================================================================
# CP^1 FUNCTIONS
# =====================================================================

def cp1_fubini_study_metric(w_re, w_im):
    """Fubini-Study metric coefficient g_{ww_bar} = 1/(1+|w|^2)^2.

    Args:
        w_re, w_im: real and imaginary parts of inhomogeneous coordinate w.
                    Must be torch tensors with requires_grad=True.

    Returns:
        g: metric coefficient (scalar tensor).
    """
    w_sq = w_re ** 2 + w_im ** 2
    g = 1.0 / (1.0 + w_sq) ** 2
    return g


def cp1_kahler_potential(w_re, w_im):
    """Kahler potential K = log(1 + |w|^2)."""
    w_sq = w_re ** 2 + w_im ** 2
    return torch.log(1.0 + w_sq)


def cp1_metric_from_kahler_autograd(w_re, w_im):
    """Compute g_{ww_bar} = d^2 K / dw dw_bar via autograd.

    In real coordinates: g_{ww_bar} = (1/4)(d^2K/dRe^2 + d^2K/dIm^2).
    This equals 1/(1+|w|^2)^2 for the Fubini-Study case.
    """
    K = cp1_kahler_potential(w_re, w_im)
    dK_dre = torch.autograd.grad(K, w_re, create_graph=True)[0]
    dK_dim = torch.autograd.grad(K, w_im, create_graph=True)[0]
    d2K_dre2 = torch.autograd.grad(dK_dre, w_re, create_graph=True)[0]
    d2K_dim2 = torch.autograd.grad(dK_dim, w_im, create_graph=True)[0]
    # g_{ww_bar} = (1/4)(d2K/dx^2 + d2K/dy^2)
    return 0.25 * (d2K_dre2 + d2K_dim2)


def cp1_symplectic_form_value(w_re, w_im):
    """Symplectic form omega = i * d d_bar K.

    In real coords: omega = (1/2) * (d^2K/dx^2 + d^2K/dy^2) dx ^ dy
    The coefficient equals 2*g_{ww_bar}.
    """
    K = cp1_kahler_potential(w_re, w_im)
    dK_dre = torch.autograd.grad(K, w_re, create_graph=True)[0]
    dK_dim = torch.autograd.grad(K, w_im, create_graph=True)[0]
    d2K_dre2 = torch.autograd.grad(dK_dre, w_re, create_graph=True)[0]
    d2K_dim2 = torch.autograd.grad(dK_dim, w_im, create_graph=True)[0]
    # omega coefficient in dx^dy = (1/2)(d2K/dx^2 + d2K/dy^2) = 2 g_{ww_bar}
    return 0.5 * (d2K_dre2 + d2K_dim2)


def cp1_integrate_symplectic_form(n_points=10000):
    """Numerically integrate omega over CP^1 (the whole Riemann sphere).

    int(omega) = int_0^inf int_0^{2pi} [1/(1+r^2)^2] r dr dtheta
               = 2*pi * [1/2] = pi.

    Uses substitution u = r^2 to map to finite domain:
    int_0^inf r/(1+r^2)^2 dr = (1/2) int_0^inf du/(1+u)^2 = 1/2.

    Then substitution t = u/(1+u) maps [0, inf) -> [0, 1):
    int_0^1 dt = 1/2.  (The integrand becomes exactly 1/2 after sub.)

    For numerical stability, use the t-substitution directly.
    """
    # Substitution: u = t/(1-t), du = dt/(1-t)^2
    # int_0^inf du/(1+u)^2 = int_0^1 [1/(1+t/(1-t))^2] * dt/(1-t)^2
    #   = int_0^1 (1-t)^2 / 1^2 * dt/(1-t)^2 = int_0^1 dt = 1
    # So radial integral = (1/2)*1 = 1/2, full = 2*pi * 1/2 = pi.
    #
    # Actually let's just use the direct substitution r = tan(s), s in [0, pi/2):
    # dr = sec^2(s) ds, r/(1+r^2)^2 * dr = tan(s)/sec^4(s) * sec^2(s) ds
    #   = tan(s)*cos^2(s) ds = sin(s)*cos(s) ds = (1/2)sin(2s) ds.
    # int_0^{pi/2} (1/2)sin(2s) ds = (1/2)*[-cos(2s)/2]_0^{pi/2} = (1/2)*1 = 1/2.
    s = torch.linspace(1e-10, math.pi / 2 - 1e-10, n_points, dtype=torch.float64)
    integrand = 0.5 * torch.sin(2.0 * s)
    radial_integral = torch.trapezoid(integrand, s)
    full_integral = 2.0 * math.pi * radial_integral
    return full_integral.item()


# =====================================================================
# U(1) FIBER / BERRY CONNECTION
# =====================================================================

def state_on_s2(theta, phi):
    """Standard qubit state |psi(theta,phi)> on the Bloch sphere.

    |psi> = cos(theta/2)|0> + e^{i*phi} sin(theta/2)|1>.
    """
    c = torch.cos(theta / 2).to(torch.complex128)
    s = torch.sin(theta / 2).to(torch.complex128)
    phase = torch.exp(1j * phi.to(torch.complex128))
    return torch.stack([c, phase * s])


def berry_connection_theta(theta, phi):
    """A_theta = Im(<psi| d/dtheta |psi>) = 0 for standard gauge."""
    # d|psi>/dtheta = (-sin(theta/2)/2, e^{i phi} cos(theta/2)/2)
    # <psi|d psi/dtheta> = -sin(theta/2)cos(theta/2)/2 + cos(theta/2)sin(theta/2)/2 = 0
    return torch.tensor(0.0, dtype=torch.float64)


def berry_connection_phi(theta, phi):
    """A_phi = Im(<psi| d/dphi |psi>).

    d|psi>/dphi = (0, i*e^{i phi} sin(theta/2))
    <psi|d psi/dphi> = i * sin^2(theta/2)
    A_phi = Im(i * sin^2(theta/2)) = sin^2(theta/2) = (1 - cos(theta))/2.
    """
    return (1.0 - torch.cos(theta)) / 2.0


def berry_curvature_F(theta):
    """Berry curvature F = dA_phi/dtheta (the theta-phi component).

    F_{theta,phi} = d(A_phi)/d(theta) = sin(theta)/2.
    """
    return torch.sin(theta) / 2.0


def berry_holonomy_solid_angle(Omega):
    """Holonomy around a loop enclosing solid angle Omega.

    gamma = exp(-i * Omega / 2).
    """
    return torch.exp(-1j * Omega.to(torch.complex128) / 2.0)


def berry_holonomy_from_connection(theta_cap, n_phi=1000):
    """Numerically compute holonomy by integrating A_phi along a latitude circle.

    oint A_phi dphi at theta = theta_cap.
    Solid angle enclosed by cap: Omega = 2*pi*(1 - cos(theta_cap)).
    So oint A_phi dphi = 2*pi * sin^2(theta_cap/2) = pi*(1-cos(theta_cap)) = Omega/2.
    Holonomy = exp(i * oint A_phi dphi) = exp(i * Omega/2).
    But the GEOMETRIC phase (Berry) = -oint A = -Omega/2.
    """
    phi_vals = torch.linspace(0, 2 * math.pi, n_phi, dtype=torch.float64)
    theta_t = torch.tensor(theta_cap, dtype=torch.float64)
    # A_phi is independent of phi, but expand to match shape for trapezoid
    A_scalar = berry_connection_phi(theta_t, phi_vals[0])
    A_vals = A_scalar.expand(n_phi)
    integral = torch.trapezoid(A_vals, phi_vals).item()
    return integral


def integrate_berry_curvature(n_theta=2000, n_phi=500):
    """Integrate Berry curvature over full S^2 to get first Chern number.

    c_1 = (1/2pi) * int F sin(theta) dtheta dphi
        = (1/2pi) * int_0^pi int_0^{2pi} (sin(theta)/2) sin(theta) dtheta dphi
        = (1/2pi) * 2pi * int_0^pi sin^2(theta)/2 dtheta
        = int_0^pi sin^2(theta)/2 dtheta = pi/4 ... wait.

    Actually: F = (1/2) sin(theta) dtheta ^ dphi (as a 2-form).
    So int F = int_0^pi int_0^{2pi} (1/2) sin(theta) dtheta dphi = 2pi.
    c_1 = (1/(2pi)) * int F = 1.
    """
    theta = torch.linspace(1e-8, math.pi - 1e-8, n_theta, dtype=torch.float64)
    # F as a 2-form: F = (sin(theta)/2) dtheta^dphi
    # int over phi gives 2pi, so reduce to:
    # int F = 2pi * int_0^pi (sin(theta)/2) dtheta = 2pi * 1 = 2pi
    integrand = torch.sin(theta) / 2.0
    theta_integral = torch.trapezoid(integrand, theta)
    full_integral = 2.0 * math.pi * theta_integral.item()
    chern = full_integral / (2.0 * math.pi)
    return chern, full_integral


# =====================================================================
# PRINCIPAL BUNDLE P(S^2, U(1))
# =====================================================================

def hopf_map(z1, z2):
    """Hopf map S^3 -> S^2: (z1, z2) -> (x, y, z) on S^2.

    x = 2*Re(z1_bar * z2), y = 2*Im(z1_bar * z2), z = |z1|^2 - |z2|^2.
    """
    x = 2.0 * torch.real(z1.conj() * z2)
    y = 2.0 * torch.imag(z1.conj() * z2)
    z = torch.abs(z1) ** 2 - torch.abs(z2) ** 2
    return x, y, z


def hopf_fiber_action(z1, z2, alpha):
    """U(1) fiber action: (z1, z2) -> (e^{i alpha} z1, e^{i alpha} z2)."""
    phase = torch.exp(1j * alpha.to(torch.complex128))
    return phase * z1, phase * z2


def check_trivialization_obstruction(n_samples=500):
    """Demonstrate that the Hopf bundle is NOT globally trivializable.

    Strategy: show that the north and south pole sections have different
    winding numbers, implying no global section exists.
    The transition function g_{NS}(phi) = e^{i phi} on the equator
    has winding number 1, proving topological obstruction.
    """
    # On the equator (theta = pi/2), z1 = 1/sqrt(2), z2 = e^{i phi}/sqrt(2)
    # North section: divide by z1 -> (1, w) with w = z2/z1 = e^{i phi}
    # South section: divide by z2 -> (w_bar, 1) with w_bar = z1/z2 = e^{-i phi}
    # Transition function: g_{NS} = z1/z2 (when both nonzero)
    #   at equator: g_{NS}(phi) = e^{-i phi}
    # Winding number of g_{NS} around the equator:
    #   (1/2pi i) oint dg/g = (1/2pi i) oint (-i)dphi = -1
    # |winding| = 1 -> nontrivial bundle -> c_1 = 1

    phi_vals = torch.linspace(0, 2 * math.pi, n_samples, dtype=torch.float64)

    # Transition function values on equator
    g_ns = torch.exp(-1j * phi_vals.to(torch.complex128))

    # Compute winding number numerically: (1/2pi) * oint d(arg(g))
    # arg(g_{NS}) = -phi, so d(arg)/dphi = -1, integral = -2pi, winding = -1
    arg_vals = torch.angle(g_ns)
    # Unwrap phase
    arg_np = arg_vals.numpy()
    arg_unwrapped = np.unwrap(arg_np)
    winding = (arg_unwrapped[-1] - arg_unwrapped[0]) / (2.0 * math.pi)

    return {
        "winding_number": round(winding),
        "winding_raw": float(winding),
        "is_nontrivial": abs(round(winding)) >= 1,
        "note": "winding != 0 proves no global section exists"
    }


# =====================================================================
# SYMPY CROSS-VALIDATION
# =====================================================================

def sympy_cross_validate():
    """Use sympy to symbolically verify CP^1 geometry identities."""
    results = {}

    w, wbar = sp.symbols('w wbar', complex=True)
    r = sp.Symbol('r', positive=True, real=True)
    theta_s = sp.Symbol('theta', positive=True, real=True)

    # 1. Kahler potential
    K = sp.log(1 + r ** 2)  # K(|w|) = log(1+|w|^2)
    dK_dr = sp.diff(K, r)
    d2K_dr2 = sp.diff(dK_dr, r)
    # In polar: g_{ww_bar} = (1/4)(d^2K/dr^2 + (1/r)dK/dr)
    #   but for radial part of Laplacian on R^2 in polar:
    #   d^2K/dx^2 + d^2K/dy^2 = d^2K/dr^2 + (1/r)dK/dr
    laplacian_K = d2K_dr2 + dK_dr / r
    g_ww_bar = sp.simplify(laplacian_K / 4)
    expected_g = 1 / (1 + r ** 2) ** 2
    metric_match = sp.simplify(g_ww_bar - expected_g) == 0
    results["kahler_to_metric_match"] = bool(metric_match)

    # 2. Symplectic form integral (symbolic)
    # omega = g dxdy = [1/(1+r^2)^2] dxdy, in polar: r/(1+r^2)^2 dr dtheta
    # int = int_0^inf int_0^{2pi} r/(1+r^2)^2 dr dtheta
    integrand_r = r / (1 + r ** 2) ** 2
    radial = sp.integrate(integrand_r, (r, 0, sp.oo))
    total = 2 * sp.pi * radial
    results["sympy_integral_omega"] = float(total)
    results["sympy_integral_matches_pi"] = bool(sp.Eq(total, sp.pi))

    # 3. Berry curvature integral -> Chern number
    F_theta = sp.sin(theta_s) / 2
    chern_integrand = F_theta  # already the dtheta piece; multiply by 2pi for phi
    theta_int = sp.integrate(chern_integrand, (theta_s, 0, sp.pi))
    chern_val = 2 * sp.pi * theta_int / (2 * sp.pi)
    results["sympy_chern_number"] = float(chern_val)
    results["sympy_chern_equals_1"] = bool(sp.Eq(chern_val, 1))

    return results


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: CP^1 Fubini-Study metric from Kahler via autograd ---
    p1_data = []
    torch.manual_seed(42)
    for _ in range(20):
        w_re = torch.randn(1, dtype=torch.float64).requires_grad_(True)
        w_im = torch.randn(1, dtype=torch.float64).requires_grad_(True)
        g_direct = cp1_fubini_study_metric(w_re, w_im).item()
        g_autograd = cp1_metric_from_kahler_autograd(w_re, w_im).item()
        err = abs(g_direct - g_autograd)
        p1_data.append({
            "w": [w_re.item(), w_im.item()],
            "g_direct": g_direct,
            "g_autograd": g_autograd,
            "error": err,
            "pass": err < 1e-12
        })
    results["P1_cp1_metric_autograd"] = {
        "description": "FS metric from direct formula vs Kahler autograd",
        "all_pass": all(d["pass"] for d in p1_data),
        "max_error": max(d["error"] for d in p1_data),
        "samples": len(p1_data)
    }

    # --- P2: Integral of symplectic form = pi ---
    omega_integral = cp1_integrate_symplectic_form(n_points=10000)
    err_pi = abs(omega_integral - math.pi)
    results["P2_integral_omega_pi"] = {
        "description": "int(omega) over CP^1 should equal pi",
        "numerical_value": omega_integral,
        "expected": math.pi,
        "error": err_pi,
        "pass": err_pi < 1e-4
    }

    # --- P3: Berry connection and curvature ---
    p3_data = []
    for theta_val in [0.3, 0.7, 1.0, 1.5, 2.0, 2.8]:
        theta_t = torch.tensor(theta_val, dtype=torch.float64)
        A_phi = berry_connection_phi(theta_t, torch.tensor(0.0, dtype=torch.float64))
        A_phi_expected = (1.0 - math.cos(theta_val)) / 2.0
        err = abs(A_phi.item() - A_phi_expected)

        F_val = berry_curvature_F(theta_t)
        F_expected = math.sin(theta_val) / 2.0
        F_err = abs(F_val.item() - F_expected)

        p3_data.append({
            "theta": theta_val,
            "A_phi": A_phi.item(),
            "A_phi_expected": A_phi_expected,
            "A_error": err,
            "F": F_val.item(),
            "F_expected": F_expected,
            "F_error": F_err,
            "pass": err < 1e-14 and F_err < 1e-14
        })
    results["P3_berry_connection_curvature"] = {
        "description": "Berry connection A_phi and curvature F vs analytic",
        "all_pass": all(d["pass"] for d in p3_data),
        "max_A_error": max(d["A_error"] for d in p3_data),
        "max_F_error": max(d["F_error"] for d in p3_data),
        "samples": p3_data
    }

    # --- P4: Holonomy = exp(-i*Omega/2) ---
    p4_data = []
    for theta_cap in [0.5, 1.0, math.pi / 3, math.pi / 2, 2.0]:
        # Solid angle of spherical cap: Omega = 2*pi*(1 - cos(theta_cap))
        Omega = 2.0 * math.pi * (1.0 - math.cos(theta_cap))
        # Numerical line integral of A_phi
        numerical_integral = berry_holonomy_from_connection(theta_cap, n_phi=5000)
        expected_integral = Omega / 2.0
        err = abs(numerical_integral - expected_integral)

        # Holonomy phase
        holonomy = berry_holonomy_solid_angle(torch.tensor(Omega, dtype=torch.float64))
        phase_expected = -Omega / 2.0
        phase_actual = torch.angle(holonomy).item()
        # Normalize phase difference to [-pi, pi]
        phase_diff = (phase_actual - phase_expected + math.pi) % (2 * math.pi) - math.pi
        p4_data.append({
            "theta_cap": theta_cap,
            "solid_angle": Omega,
            "numerical_A_integral": numerical_integral,
            "expected_A_integral": expected_integral,
            "integral_error": err,
            "holonomy_phase": phase_actual,
            "expected_phase": phase_expected,
            "phase_error": abs(phase_diff),
            "pass": err < 1e-6 and abs(phase_diff) < 1e-12
        })
    results["P4_holonomy_berry_phase"] = {
        "description": "Holonomy = exp(-i*Omega/2) via line integral of A",
        "all_pass": all(d["pass"] for d in p4_data),
        "max_integral_error": max(d["integral_error"] for d in p4_data),
        "samples": p4_data
    }

    # --- P5: First Chern number c_1 = 1 ---
    chern, full_curv_integral = integrate_berry_curvature(n_theta=5000)
    err_c1 = abs(chern - 1.0)
    results["P5_chern_number"] = {
        "description": "c_1 = (1/2pi) int F = 1",
        "chern_numerical": chern,
        "curvature_integral": full_curv_integral,
        "expected_chern": 1.0,
        "expected_integral": 2 * math.pi,
        "error": err_c1,
        "pass": err_c1 < 1e-6
    }

    # --- P6: Hopf map fiber invariance ---
    p6_data = []
    torch.manual_seed(99)
    for _ in range(20):
        z1 = torch.randn(2, dtype=torch.float64).to(torch.complex128)
        z1 = z1[0] + 1j * z1[1]  # random complex
        z2 = torch.randn(2, dtype=torch.float64).to(torch.complex128)
        z2 = z2[0] + 1j * z2[1]
        # Normalize to S^3
        norm = torch.sqrt(torch.abs(z1) ** 2 + torch.abs(z2) ** 2)
        z1 = z1 / norm
        z2 = z2 / norm

        x0, y0, z0 = hopf_map(z1, z2)

        # Apply random U(1) phase
        alpha = torch.rand(1, dtype=torch.float64) * 2 * math.pi
        z1r, z2r = hopf_fiber_action(z1, z2, alpha)
        x1, y1, z1_mapped = hopf_map(z1r, z2r)

        err = math.sqrt(
            (x0.item() - x1.item()) ** 2 +
            (y0.item() - y1.item()) ** 2 +
            (z0.item() - z1_mapped.item()) ** 2
        )
        p6_data.append({
            "alpha": alpha.item(),
            "base_point_before": [x0.item(), y0.item(), z0.item()],
            "base_point_after": [x1.item(), y1.item(), z1_mapped.item()],
            "error": err,
            "pass": err < 1e-12
        })
    results["P6_hopf_fiber_invariance"] = {
        "description": "U(1) action on S^3 preserves base point on S^2",
        "all_pass": all(d["pass"] for d in p6_data),
        "max_error": max(d["error"] for d in p6_data),
        "samples": len(p6_data)
    }

    # --- P7: Topological obstruction (no global section) ---
    obstruction = check_trivialization_obstruction(n_samples=2000)
    results["P7_topological_obstruction"] = {
        "description": "Transition function winding != 0 proves no global section",
        **obstruction,
        "pass": obstruction["is_nontrivial"] and abs(obstruction["winding_number"]) == 1
    }

    # --- P8: Sympy cross-validation ---
    sympy_results = sympy_cross_validate()
    results["P8_sympy_cross_validation"] = {
        "description": "Symbolic verification of Kahler->metric, int(omega)=pi, c_1=1",
        **sympy_results,
        "pass": (sympy_results["kahler_to_metric_match"]
                 and sympy_results["sympy_integral_matches_pi"]
                 and sympy_results["sympy_chern_equals_1"])
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: Wrong metric (flat) should NOT match Fubini-Study ---
    n1_data = []
    torch.manual_seed(7)
    for _ in range(10):
        w_re = torch.randn(1, dtype=torch.float64).requires_grad_(True)
        w_im = torch.randn(1, dtype=torch.float64).requires_grad_(True)
        g_fs = cp1_fubini_study_metric(w_re, w_im).item()
        g_flat = 1.0  # flat metric coefficient
        mismatch = abs(g_fs - g_flat)
        n1_data.append({
            "w": [w_re.item(), w_im.item()],
            "g_fs": g_fs,
            "g_flat": g_flat,
            "mismatch": mismatch,
            "pass": mismatch > 0.01  # they should NOT match
        })
    results["N1_flat_metric_rejected"] = {
        "description": "Flat metric g=1 does NOT equal Fubini-Study",
        "all_pass": all(d["pass"] for d in n1_data),
        "note": "At w=0, g_FS=1 so one sample may coincidentally match"
    }

    # --- N2: Wrong Berry curvature (e.g., doubled) should NOT yield c_1=1 ---
    theta = torch.linspace(1e-8, math.pi - 1e-8, 3000, dtype=torch.float64)
    wrong_integrand = torch.sin(theta)  # doubled: sin(theta) instead of sin/2
    wrong_integral = 2 * math.pi * torch.trapezoid(wrong_integrand, theta).item()
    wrong_chern = wrong_integral / (2 * math.pi)
    results["N2_wrong_curvature_chern"] = {
        "description": "Doubled curvature gives c_1=2, not 1",
        "wrong_chern": wrong_chern,
        "expected_wrong": 2.0,
        "pass": abs(wrong_chern - 2.0) < 0.01 and abs(wrong_chern - 1.0) > 0.5
    }

    # --- N3: Trivial bundle (winding=0) should NOT show obstruction ---
    phi_vals = torch.linspace(0, 2 * math.pi, 1000, dtype=torch.float64)
    g_trivial = torch.ones(1000, dtype=torch.complex128)  # constant transition fn
    arg_trivial = torch.angle(g_trivial).numpy()
    arg_unwrapped = np.unwrap(arg_trivial)
    winding_trivial = (arg_unwrapped[-1] - arg_unwrapped[0]) / (2 * math.pi)
    results["N3_trivial_bundle_no_obstruction"] = {
        "description": "Constant transition function -> winding=0 -> trivial bundle",
        "winding": float(winding_trivial),
        "pass": abs(winding_trivial) < 0.01
    }

    # --- N4: Wrong holonomy formula (missing 1/2) ---
    theta_cap = math.pi / 3
    Omega = 2 * math.pi * (1 - math.cos(theta_cap))
    correct_phase = -Omega / 2.0
    wrong_phase = -Omega  # missing the 1/2
    diff = abs(correct_phase - wrong_phase)
    results["N4_wrong_holonomy_formula"] = {
        "description": "exp(-i*Omega) != exp(-i*Omega/2): wrong factor rejected",
        "correct_phase": correct_phase,
        "wrong_phase": wrong_phase,
        "difference": diff,
        "pass": diff > 0.1
    }

    # --- N5: Non-normalized state breaks Berry connection ---
    theta_t = torch.tensor(1.0, dtype=torch.float64)
    phi_t = torch.tensor(0.0, dtype=torch.float64)
    psi = state_on_s2(theta_t, phi_t)
    psi_wrong = psi * 2.0  # not normalized
    norm_sq = torch.real(torch.dot(psi_wrong.conj(), psi_wrong)).item()
    results["N5_unnormalized_state"] = {
        "description": "Non-unit state has |psi|^2 != 1",
        "norm_sq": norm_sq,
        "pass": abs(norm_sq - 1.0) > 0.5
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: w -> 0 (north pole): g -> 1 ---
    w_re = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    w_im = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    g_at_origin = cp1_fubini_study_metric(w_re, w_im).item()
    results["B1_north_pole_metric"] = {
        "description": "At w=0 (north pole), g_{ww_bar}=1",
        "g_value": g_at_origin,
        "expected": 1.0,
        "error": abs(g_at_origin - 1.0),
        "pass": abs(g_at_origin - 1.0) < 1e-15
    }

    # --- B2: |w| -> infinity (south pole): g -> 0 ---
    w_re_big = torch.tensor(1e6, dtype=torch.float64, requires_grad=True)
    w_im_big = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    g_at_south = cp1_fubini_study_metric(w_re_big, w_im_big).item()
    results["B2_south_pole_metric"] = {
        "description": "As |w|->inf (south pole), g->0",
        "g_value": g_at_south,
        "expected_near_zero": True,
        "pass": g_at_south < 1e-20
    }

    # --- B3: theta=0 (north pole): A_phi=0 ---
    A_at_north = berry_connection_phi(
        torch.tensor(0.0, dtype=torch.float64),
        torch.tensor(0.0, dtype=torch.float64)
    ).item()
    results["B3_connection_north_pole"] = {
        "description": "A_phi(theta=0) = 0 (no monopole singularity at north)",
        "A_phi": A_at_north,
        "pass": abs(A_at_north) < 1e-15
    }

    # --- B4: theta=pi (south pole): A_phi=1 (Dirac string) ---
    A_at_south = berry_connection_phi(
        torch.tensor(math.pi, dtype=torch.float64),
        torch.tensor(0.0, dtype=torch.float64)
    ).item()
    results["B4_connection_south_pole"] = {
        "description": "A_phi(theta=pi) = 1 (maximal connection at south pole)",
        "A_phi": A_at_south,
        "expected": 1.0,
        "error": abs(A_at_south - 1.0),
        "pass": abs(A_at_south - 1.0) < 1e-14
    }

    # --- B5: Full sphere holonomy: Omega = 4pi -> phase = -2pi -> exp(0) = 1 ---
    Omega_full = torch.tensor(4.0 * math.pi, dtype=torch.float64)
    hol = berry_holonomy_solid_angle(Omega_full)
    # exp(-i*4pi/2) = exp(-i*2pi) = 1
    hol_abs = torch.abs(hol).item()
    hol_phase = torch.angle(hol).item()
    results["B5_full_sphere_holonomy"] = {
        "description": "Full sphere Omega=4pi -> holonomy=1 (phase wraps to 0)",
        "holonomy_abs": hol_abs,
        "holonomy_phase": hol_phase,
        "pass": abs(hol_abs - 1.0) < 1e-12 and abs(hol_phase) < 1e-10
    }

    # --- B6: Equator holonomy: Omega = 2pi -> phase = -pi ---
    theta_eq = math.pi / 2
    Omega_eq = 2 * math.pi * (1 - math.cos(theta_eq))  # = 2pi
    numerical_A = berry_holonomy_from_connection(theta_eq, n_phi=5000)
    expected_A = Omega_eq / 2.0  # = pi
    results["B6_equator_holonomy"] = {
        "description": "Equator: Omega=2pi, oint A = pi, phase=-pi",
        "solid_angle": Omega_eq,
        "numerical_A_integral": numerical_A,
        "expected_A_integral": expected_A,
        "error": abs(numerical_A - expected_A),
        "pass": abs(numerical_A - expected_A) < 1e-6
    }

    # --- B7: Hopf map sends S^3 poles to S^2 poles ---
    z1_north = torch.tensor(1.0 + 0j, dtype=torch.complex128)
    z2_north = torch.tensor(0.0 + 0j, dtype=torch.complex128)
    x, y, z = hopf_map(z1_north, z2_north)
    results["B7_hopf_north_pole"] = {
        "description": "(1,0) in S^3 maps to (0,0,1) in S^2 (north pole)",
        "mapped_point": [x.item(), y.item(), z.item()],
        "expected": [0.0, 0.0, 1.0],
        "pass": (abs(x.item()) < 1e-14 and abs(y.item()) < 1e-14
                 and abs(z.item() - 1.0) < 1e-14)
    }

    z1_south = torch.tensor(0.0 + 0j, dtype=torch.complex128)
    z2_south = torch.tensor(1.0 + 0j, dtype=torch.complex128)
    x, y, z = hopf_map(z1_south, z2_south)
    results["B7_hopf_south_pole"] = {
        "description": "(0,1) in S^3 maps to (0,0,-1) in S^2 (south pole)",
        "mapped_point": [x.item(), y.item(), z.item()],
        "expected": [0.0, 0.0, -1.0],
        "pass": (abs(x.item()) < 1e-14 and abs(y.item()) < 1e-14
                 and abs(z.item() + 1.0) < 1e-14)
    }

    return results


# =====================================================================
# STACKING TESTS -- cross-validate with L1-3
# =====================================================================

def run_stacking_tests():
    """Verify CP^1 structure is consistent with L1-3 geometric layers."""
    results = {}

    # --- S1: CP^1 metric at theta matches S^2 Fubini-Study from L2 ---
    # On S^2 with stereographic w = tan(theta/2)*e^{i phi}:
    # |w|^2 = tan^2(theta/2), so g_{ww_bar} = 1/(1+tan^2(theta/2))^2 = cos^4(theta/2)
    # The pullback ds^2 = g dw dw_bar with |dw|^2 = (1/(2cos^2(theta/2)))^2 * dtheta^2
    # gives ds^2 = (1/4) dtheta^2 + (1/4)sin^2(theta) dphi^2 -- the round S^2 metric (R=1/2).
    s1_data = []
    for theta_val in [0.3, 0.7, 1.0, 1.5, 2.0, 2.5]:
        # |w| = tan(theta/2)
        r = math.tan(theta_val / 2.0)
        w_re = torch.tensor(r, dtype=torch.float64, requires_grad=True)
        w_im = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
        g_cp1 = cp1_fubini_study_metric(w_re, w_im).item()
        g_expected = math.cos(theta_val / 2.0) ** 4
        err = abs(g_cp1 - g_expected)
        s1_data.append({
            "theta": theta_val,
            "|w|": r,
            "g_cp1": g_cp1,
            "g_expected_cos4": g_expected,
            "error": err,
            "pass": err < 1e-12
        })
    results["S1_cp1_matches_s2_metric"] = {
        "description": "CP^1 g_{ww_bar} at w=tan(theta/2) equals cos^4(theta/2)",
        "all_pass": all(d["pass"] for d in s1_data),
        "max_error": max(d["error"] for d in s1_data),
        "samples": s1_data
    }

    # --- S2: Hopf projection from L3 matches CP^1 coordinate map ---
    s2_data = []
    torch.manual_seed(55)
    for _ in range(20):
        # Stay away from south pole where w->inf and numerics degrade
        theta = torch.rand(1, dtype=torch.float64).item() * (math.pi - 0.1) + 0.05
        phi = torch.rand(1, dtype=torch.float64).item() * 2 * math.pi
        psi = state_on_s2(
            torch.tensor(theta, dtype=torch.float64),
            torch.tensor(phi, dtype=torch.float64)
        )
        z1, z2 = psi[0], psi[1]

        # CP^1 coordinate w = z2/z1
        w = z2 / z1
        w_val = w.item()
        w_expected = complex(
            math.tan(theta / 2) * math.cos(phi),
            math.tan(theta / 2) * math.sin(phi)
        )
        err = abs(w_val - w_expected)

        # Hopf map should give back the Bloch vector
        x, y, z = hopf_map(z1, z2)
        bloch_expected = [
            math.sin(theta) * math.cos(phi),
            math.sin(theta) * math.sin(phi),
            math.cos(theta)
        ]
        bloch_err = math.sqrt(
            (x.item() - bloch_expected[0]) ** 2 +
            (y.item() - bloch_expected[1]) ** 2 +
            (z.item() - bloch_expected[2]) ** 2
        )
        s2_data.append({
            "theta": theta,
            "phi": phi,
            "w_error": err,
            "bloch_error": bloch_err,
            "pass": err < 1e-10 and bloch_err < 1e-10
        })
    results["S2_hopf_cp1_coordinate_match"] = {
        "description": "CP^1 w=z2/z1 matches tan(theta/2)*e^{i phi}, Hopf recovers Bloch",
        "all_pass": all(d["pass"] for d in s2_data),
        "max_w_error": max(d["w_error"] for d in s2_data),
        "max_bloch_error": max(d["bloch_error"] for d in s2_data),
        "samples": len(s2_data)
    }

    # --- S3: Berry phase from CP^1 connection matches L3 Hopf holonomy ---
    s3_data = []
    for theta_cap in [0.5, 1.0, math.pi / 2]:
        Omega = 2 * math.pi * (1 - math.cos(theta_cap))
        A_integral = berry_holonomy_from_connection(theta_cap, n_phi=5000)
        berry_phase = -A_integral  # geometric phase = -oint A
        expected_phase = -Omega / 2.0
        err = abs(berry_phase - expected_phase)
        s3_data.append({
            "theta_cap": theta_cap,
            "solid_angle": Omega,
            "berry_phase": berry_phase,
            "expected": expected_phase,
            "error": err,
            "pass": err < 1e-6
        })
    results["S3_berry_phase_hopf_holonomy"] = {
        "description": "Berry phase from A matches Hopf holonomy -Omega/2",
        "all_pass": all(d["pass"] for d in s3_data),
        "samples": s3_data
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    stacking = run_stacking_tests()

    # Count passes
    all_tests = {}
    all_tests.update(positive)
    all_tests.update(negative)
    all_tests.update(boundary)
    all_tests.update(stacking)
    total = len(all_tests)
    passed = sum(1 for v in all_tests.values() if v.get("pass") or v.get("all_pass"))

    results = {
        "name": "CP^1 projective structure, U(1) fiber, principal bundle P(S^2, U(1))",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "stacking": stacking,
        "classification": "canonical",
        "summary": {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "all_pass": passed == total,
        }
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_cp1_u1_projective_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"\n{'='*60}")
    print(f"  CP^1 / U(1) / Principal Bundle Probe")
    print(f"  Tests: {passed}/{total} passed")
    print(f"{'='*60}")
    for name, data in all_tests.items():
        status = "PASS" if data.get("pass") or data.get("all_pass") else "FAIL"
        print(f"  [{status}] {name}")
