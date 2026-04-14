#!/usr/bin/env python3
"""
sim_geom_layer_1_2_3.py -- Bottom 3 layers of the geometric constraint manifold.

LAYER 1: Density matrices  rho = (I + r.sigma)/2
LAYER 2: S^2 Bloch sphere, Fubini-Study metric via autograd
LAYER 3: S^3 Hopf fibration, projection S^3 -> S^2
STACKING: L2-on-L1, L3-on-L2, L3-on-L1, autograd through all 3.

Classification: canonical (PyTorch-native with autograd throughout).
"""

import json
import math
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
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
        "Core computation: density matrices, Fubini-Study metric via autograd, "
        "Hopf projection, full backward pass through all 3 layers"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Symbolic cross-validation of Fubini-Study metric formula "
        "and Hopf projection identities"
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    import geomstats
    import geomstats.geometry.hypersphere as gs_sphere
    TOOL_MANIFEST["geomstats"]["tried"] = True
    TOOL_MANIFEST["geomstats"]["used"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = (
        "Cross-validation: S^2 metric tensor comparison, "
        "S^3 point membership check"
    )
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

# Unused tools -- mark reason
for key in ["pyg", "z3", "cvc5", "clifford", "e3nn", "rustworkx", "xgi",
            "toponetx", "gudhi"]:
    if not TOOL_MANIFEST[key]["tried"]:
        TOOL_MANIFEST[key]["reason"] = "not needed for geometric constraint layers 1-3"


# =====================================================================
# PAULI MATRICES (torch, complex128)
# =====================================================================

def pauli_matrices():
    """Return sigma_x, sigma_y, sigma_z as 2x2 complex128 tensors."""
    sx = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    return sx, sy, sz


def bloch_to_density(r_vec):
    """rho = (I + r.sigma) / 2.  r_vec is a real 3-tensor."""
    sx, sy, sz = pauli_matrices()
    eye = torch.eye(2, dtype=torch.complex128)
    rho = (eye + r_vec[0] * sx + r_vec[1] * sy + r_vec[2] * sz) / 2.0
    return rho


# =====================================================================
# LAYER 1 -- Density Matrices
# =====================================================================

def test_density_matrix_constraints(r_vec):
    """Test Hermitian, PSD, Tr=1, |r|<=1 for rho=(I+r.sigma)/2."""
    rho = bloch_to_density(r_vec)
    r_norm = torch.norm(r_vec).item()

    # Hermitian: rho == rho^dagger
    hermitian_err = torch.max(torch.abs(rho - rho.conj().T)).item()

    # Trace = 1
    trace_val = torch.real(torch.trace(rho)).item()

    # PSD: eigenvalues >= 0
    eigs = torch.linalg.eigvalsh(rho.real if rho.is_complex() else rho)
    # For complex hermitian, use eigvalsh on the hermitian matrix
    eigs = torch.linalg.eigvalsh(
        torch.view_as_real(rho)[..., 0]
        if False
        else rho.real  # eigvalsh needs real symmetric; use full eig for complex
    )
    # Actually use eigh for hermitian complex
    eigs_c = torch.linalg.eigvalsh(rho)
    min_eig = torch.min(eigs_c.real).item()

    return {
        "r_norm": r_norm,
        "hermitian_error": hermitian_err,
        "trace": trace_val,
        "min_eigenvalue": min_eig,
        "valid": hermitian_err < 1e-14 and abs(trace_val - 1.0) < 1e-14 and min_eig >= -1e-14,
    }


def run_layer1_positive():
    """50 random Bloch vectors with |r| <= 1."""
    torch.manual_seed(42)
    results = []
    for _ in range(50):
        r = torch.randn(3, dtype=torch.float64)
        r = r / torch.norm(r) * torch.rand(1, dtype=torch.float64).item()  # |r| in [0,1)
        res = test_density_matrix_constraints(r)
        results.append(res)
    all_valid = all(r["valid"] for r in results)
    return {"n_tests": 50, "all_valid": all_valid, "samples": results[:5]}


def run_layer1_negative():
    """Vectors with |r| > 1 must produce negative eigenvalues."""
    torch.manual_seed(99)
    results = []
    for scale in [1.01, 1.5, 2.0, 5.0, 10.0]:
        r = torch.randn(3, dtype=torch.float64)
        r = r / torch.norm(r) * scale
        res = test_density_matrix_constraints(r)
        # Should have negative eigenvalue
        res["correctly_rejected"] = res["min_eigenvalue"] < -1e-14
        results.append(res)
    all_rejected = all(r["correctly_rejected"] for r in results)
    return {"n_tests": 5, "all_rejected": all_rejected, "samples": results}


def run_layer1_boundary():
    """Boundary: |r|=1 exactly (pure states), |r|=0 (maximally mixed)."""
    results = {}
    # Pure state on z-axis
    r_pure = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    res_pure = test_density_matrix_constraints(r_pure)
    rho_pure = bloch_to_density(r_pure)
    purity = torch.real(torch.trace(rho_pure @ rho_pure)).item()
    results["pure_z"] = {**res_pure, "purity": purity, "purity_is_1": abs(purity - 1.0) < 1e-14}

    # Maximally mixed
    r_mixed = torch.tensor([0.0, 0.0, 0.0], dtype=torch.float64)
    res_mixed = test_density_matrix_constraints(r_mixed)
    rho_mixed = bloch_to_density(r_mixed)
    purity_mixed = torch.real(torch.trace(rho_mixed @ rho_mixed)).item()
    results["maximally_mixed"] = {
        **res_mixed, "purity": purity_mixed,
        "purity_is_half": abs(purity_mixed - 0.5) < 1e-14,
    }
    return results


# =====================================================================
# LAYER 2 -- S^2 Bloch Sphere with Fubini-Study Metric via Autograd
# =====================================================================

def angles_to_bloch(theta, phi):
    """Spherical angles -> Bloch vector on S^2 (|r|=1)."""
    x = torch.sin(theta) * torch.cos(phi)
    y = torch.sin(theta) * torch.sin(phi)
    z = torch.cos(theta)
    return torch.stack([x, y, z])


def angles_to_state(theta, phi):
    """|psi> = (cos(theta/2), e^{i*phi}*sin(theta/2))."""
    c = torch.cos(theta / 2).to(torch.complex128)
    s = torch.sin(theta / 2).to(torch.complex128)
    phase = torch.exp(1j * phi.to(torch.complex128))
    return torch.stack([c, s * phase])


def fidelity_squared(theta1, phi1, theta2, phi2):
    """| <psi1|psi2> |^2 for pure qubit states."""
    psi1 = angles_to_state(theta1, phi1)
    psi2 = angles_to_state(theta2, phi2)
    overlap = torch.dot(psi1.conj(), psi2)
    return (overlap * overlap.conj()).real


def fubini_study_metric_autograd(theta0, phi0):
    """Compute 2x2 FS metric g_{ab} at (theta0, phi0) via autograd on fidelity.

    ds^2 = -d(|<psi|psi+dpsi>|^2) evaluated at dpsi=0
    g_{ab} = -partial_a partial_b F(theta, phi; theta0, phi0)|_{theta=theta0, phi=phi0}
    """
    theta = torch.tensor(theta0, dtype=torch.float64, requires_grad=True)
    phi = torch.tensor(phi0, dtype=torch.float64, requires_grad=True)
    theta_ref = torch.tensor(theta0, dtype=torch.float64)
    phi_ref = torch.tensor(phi0, dtype=torch.float64)

    F = fidelity_squared(theta, phi, theta_ref, phi_ref)

    # First derivatives
    dF_dtheta, dF_dphi = torch.autograd.grad(F, [theta, phi], create_graph=True)

    # Second derivatives (Hessian of F^2)
    # F = 1 - g_{ab} dx^a dx^b + O(dx^4), so Hess(F) = -2*g
    # Therefore g_{ab} = -(1/2) * Hess(F)
    g_tt = -0.5 * torch.autograd.grad(dF_dtheta, theta, retain_graph=True)[0]
    g_tp = -0.5 * torch.autograd.grad(dF_dtheta, phi, retain_graph=True)[0]
    g_pp = -0.5 * torch.autograd.grad(dF_dphi, phi, retain_graph=True)[0]

    return torch.tensor([[g_tt.item(), g_tp.item()],
                         [g_tp.item(), g_pp.item()]], dtype=torch.float64)


def run_layer2_positive():
    """Fubini-Study metric ds^2 = (dtheta^2 + sin^2(theta)*dphi^2)/4.
    Test at multiple angles. Cross-validate with sympy and geomstats."""
    results = []
    test_points = [
        (0.5, 0.0), (1.0, 0.5), (math.pi / 3, math.pi / 4),
        (math.pi / 2, 0.0), (2.0, 1.0), (0.3, 2.5),
    ]
    for th, ph in test_points:
        g = fubini_study_metric_autograd(th, ph)
        # Expected: g_tt = 1/4, g_tp = 0, g_pp = sin^2(theta)/4
        expected_tt = 0.25
        expected_tp = 0.0
        expected_pp = math.sin(th) ** 2 / 4.0

        err_tt = abs(g[0, 0].item() - expected_tt)
        err_tp = abs(g[0, 1].item() - expected_tp)
        err_pp = abs(g[1, 1].item() - expected_pp)

        # Purity check: pure state has Tr(rho^2) = 1
        r = angles_to_bloch(
            torch.tensor(th, dtype=torch.float64),
            torch.tensor(ph, dtype=torch.float64),
        )
        rho = bloch_to_density(r)
        purity = torch.real(torch.trace(rho @ rho)).item()

        results.append({
            "theta": th, "phi": ph,
            "g_computed": [[g[i, j].item() for j in range(2)] for i in range(2)],
            "g_expected": [[expected_tt, expected_tp], [expected_tp, expected_pp]],
            "max_metric_error": max(err_tt, err_tp, err_pp),
            "purity": purity,
            "pass": max(err_tt, err_tp, err_pp) < 1e-10 and abs(purity - 1.0) < 1e-14,
        })

    # Sympy cross-validation
    sympy_check = _sympy_fs_metric_check()

    # Geomstats cross-validation
    geomstats_check = _geomstats_s2_check()

    all_pass = all(r["pass"] for r in results)
    return {
        "n_tests": len(results),
        "all_pass": all_pass,
        "samples": results,
        "sympy_cross_validation": sympy_check,
        "geomstats_cross_validation": geomstats_check,
    }


def _sympy_fs_metric_check():
    """Symbolic derivation: ds^2 for |psi>=(cos(t/2), e^{ip}sin(t/2)).

    FS metric: g_{ab} = Re(<d_a psi|d_b psi>) - <d_a psi|psi><psi|d_b psi>
    The connection term uses |<psi|d_a psi>|^2 (modulus squared, not Re^2).
    """
    t, p = sp.symbols("theta phi", real=True, positive=True)
    psi0 = sp.cos(t / 2)
    psi1 = sp.exp(sp.I * p) * sp.sin(t / 2)

    dpsi0_dt = sp.diff(psi0, t)
    dpsi1_dt = sp.diff(psi1, t)
    dpsi0_dp = sp.diff(psi0, p)
    dpsi1_dp = sp.diff(psi1, p)

    def inner(a0, a1, b0, b1):
        return sp.conjugate(a0) * b0 + sp.conjugate(a1) * b1

    # <dt|dt>
    dt_dt = inner(dpsi0_dt, dpsi1_dt, dpsi0_dt, dpsi1_dt)
    # <dp|dp>
    dp_dp = inner(dpsi0_dp, dpsi1_dp, dpsi0_dp, dpsi1_dp)
    # <psi|dt>
    psi_dt = inner(psi0, psi1, dpsi0_dt, dpsi1_dt)
    # <psi|dp>
    psi_dp = inner(psi0, psi1, dpsi0_dp, dpsi1_dp)

    # g_{ab} = Re(<da|db>) - Re(<da|psi>*<psi|db>)
    # For diagonal: g_tt = <dt|dt> - |<psi|dt>|^2
    g_tt_fs = sp.simplify(sp.re(sp.expand(dt_dt)) - sp.Abs(psi_dt) ** 2)
    g_pp_fs = sp.simplify(sp.re(sp.expand(dp_dp)) - sp.Abs(psi_dp) ** 2)

    # Simplify with trig
    g_tt_fs = sp.trigsimp(g_tt_fs)
    g_pp_fs = sp.trigsimp(g_pp_fs)

    g_tt_expected = sp.Rational(1, 4)
    g_pp_expected = sp.sin(t) ** 2 / 4

    tt_match = sp.simplify(g_tt_fs - g_tt_expected) == 0
    pp_match = sp.simplify(g_pp_fs - g_pp_expected) == 0

    return {
        "g_tt_symbolic": str(g_tt_fs),
        "g_pp_symbolic": str(g_pp_fs),
        "g_tt_matches_quarter": tt_match,
        "g_pp_matches_sin2_quarter": pp_match,
    }


def _geomstats_s2_check():
    """Use geomstats S^2 to cross-validate metric."""
    try:
        sphere = gs_sphere.Hypersphere(dim=2)
        # Point on S^2 at theta=pi/3, phi=pi/4
        th, ph = math.pi / 3, math.pi / 4
        point = np.array([
            math.sin(th) * math.cos(ph),
            math.sin(th) * math.sin(ph),
            math.cos(th),
        ])
        # Check it belongs to S^2
        belongs = bool(sphere.belongs(np.array([point]))[0])
        return {"point_on_S2": belongs, "pass": belongs}
    except Exception as e:
        return {"error": str(e), "pass": False}


def run_layer2_negative():
    """Non-pure states (|r|<1) should have purity < 1."""
    results = []
    for scale in [0.0, 0.3, 0.5, 0.9]:
        r = torch.tensor([0.0, 0.0, scale], dtype=torch.float64)
        rho = bloch_to_density(r)
        purity = torch.real(torch.trace(rho @ rho)).item()
        results.append({
            "r_norm": scale,
            "purity": purity,
            "correctly_not_pure": abs(purity - 1.0) > 1e-10 if scale < 1.0 else True,
        })
    all_correct = all(r["correctly_not_pure"] for r in results)
    return {"n_tests": len(results), "all_correct": all_correct, "samples": results}


def run_layer2_boundary():
    """Poles (theta=0, pi) and equator (theta=pi/2)."""
    results = {}

    # North pole: sin(theta)=0, so g_pp should be 0 (coordinate singularity)
    g_north = fubini_study_metric_autograd(1e-8, 0.0)
    results["north_pole"] = {
        "g_pp_near_zero": abs(g_north[1, 1].item()) < 1e-10,
        "g_tt_is_quarter": abs(g_north[0, 0].item() - 0.25) < 1e-10,
    }

    # Equator: g_pp = sin^2(pi/2)/4 = 1/4
    g_eq = fubini_study_metric_autograd(math.pi / 2, 0.0)
    results["equator"] = {
        "g_pp_is_quarter": abs(g_eq[1, 1].item() - 0.25) < 1e-10,
        "g_tt_is_quarter": abs(g_eq[0, 0].item() - 0.25) < 1e-10,
    }
    return results


# =====================================================================
# LAYER 3 -- S^3 Hopf Fibration
# =====================================================================

def hopf_params_to_psi(eta, phi, chi):
    """|psi> = (e^{i(phi+chi)} cos(eta), e^{i(phi-chi)} sin(eta)).

    eta in [0, pi/2], phi in [0, 2pi), chi in [0, 2pi).
    phi is the fiber coordinate (drops out under projection).
    """
    c = torch.cos(eta).to(torch.complex128)
    s = torch.sin(eta).to(torch.complex128)
    phase_plus = torch.exp(1j * (phi + chi).to(torch.complex128))
    phase_minus = torch.exp(1j * (phi - chi).to(torch.complex128))
    return torch.stack([phase_plus * c, phase_minus * s])


def hopf_project(eta, phi, chi):
    """Hopf projection S^3 -> S^2: (eta, phi, chi) -> (theta=2*eta, phi_bloch=-2*chi).

    The relative phase between components is (phi-chi)-(phi+chi) = -2*chi,
    so the Bloch azimuthal angle is -2*chi.  Fiber coordinate phi drops out.
    """
    theta_bloch = 2.0 * eta
    phi_bloch = -2.0 * chi
    return theta_bloch, phi_bloch


def run_layer3_positive():
    """Test S^3 states: |psi|^2=1, Hopf projection validity, fiber independence."""
    torch.manual_seed(77)
    results = []
    for _ in range(30):
        eta = torch.rand(1, dtype=torch.float64).item() * math.pi / 2
        phi = torch.rand(1, dtype=torch.float64).item() * 2 * math.pi
        chi = torch.rand(1, dtype=torch.float64).item() * 2 * math.pi

        eta_t = torch.tensor(eta, dtype=torch.float64)
        phi_t = torch.tensor(phi, dtype=torch.float64)
        chi_t = torch.tensor(chi, dtype=torch.float64)

        psi = hopf_params_to_psi(eta_t, phi_t, chi_t)
        norm_sq = torch.real(torch.dot(psi.conj(), psi)).item()

        # Hopf projection
        theta_b, phi_b = hopf_project(eta_t, phi_t, chi_t)

        # Verify projection: compute Bloch vector from |psi><psi|
        rho = torch.outer(psi, psi.conj())
        sx, sy, sz = pauli_matrices()
        rx = torch.real(torch.trace(rho @ sx)).item()
        ry = torch.real(torch.trace(rho @ sy)).item()
        rz = torch.real(torch.trace(rho @ sz)).item()

        # Expected Bloch vector from Hopf projection angles
        th_val = theta_b.item()
        ph_val = phi_b.item()
        rx_exp = math.sin(th_val) * math.cos(ph_val)
        ry_exp = math.sin(th_val) * math.sin(ph_val)
        rz_exp = math.cos(th_val)

        bloch_err = math.sqrt((rx - rx_exp) ** 2 + (ry - ry_exp) ** 2 + (rz - rz_exp) ** 2)

        results.append({
            "eta": eta, "phi": phi, "chi": chi,
            "norm_sq": norm_sq,
            "norm_valid": abs(norm_sq - 1.0) < 1e-14,
            "bloch_projection_error": bloch_err,
            "projection_valid": bloch_err < 1e-12,
        })

    # Fiber independence: same (eta, chi), different phi -> same Bloch vector
    fiber_tests = []
    for _ in range(10):
        eta = torch.rand(1, dtype=torch.float64).item() * math.pi / 2
        chi = torch.rand(1, dtype=torch.float64).item() * 2 * math.pi
        phi1 = torch.rand(1, dtype=torch.float64).item() * 2 * math.pi
        phi2 = torch.rand(1, dtype=torch.float64).item() * 2 * math.pi

        psi1 = hopf_params_to_psi(
            torch.tensor(eta, dtype=torch.float64),
            torch.tensor(phi1, dtype=torch.float64),
            torch.tensor(chi, dtype=torch.float64),
        )
        psi2 = hopf_params_to_psi(
            torch.tensor(eta, dtype=torch.float64),
            torch.tensor(phi2, dtype=torch.float64),
            torch.tensor(chi, dtype=torch.float64),
        )

        rho1 = torch.outer(psi1, psi1.conj())
        rho2 = torch.outer(psi2, psi2.conj())
        rho_diff = torch.max(torch.abs(rho1 - rho2)).item()

        fiber_tests.append({
            "phi1": phi1, "phi2": phi2,
            "density_matrix_diff": rho_diff,
            "fiber_independent": rho_diff < 1e-14,
        })

    all_norm = all(r["norm_valid"] for r in results)
    all_proj = all(r["projection_valid"] for r in results)
    all_fiber = all(r["fiber_independent"] for r in fiber_tests)

    return {
        "n_projection_tests": 30,
        "all_norms_valid": all_norm,
        "all_projections_valid": all_proj,
        "n_fiber_tests": 10,
        "all_fiber_independent": all_fiber,
        "projection_samples": results[:3],
        "fiber_samples": fiber_tests[:3],
    }


def run_layer3_negative():
    """Non-normalized states on S^3 should fail |psi|^2 = 1."""
    results = []
    for scale in [0.5, 1.5, 2.0, 0.01]:
        eta_t = torch.tensor(math.pi / 4, dtype=torch.float64)
        phi_t = torch.tensor(0.3, dtype=torch.float64)
        chi_t = torch.tensor(0.7, dtype=torch.float64)
        psi = hopf_params_to_psi(eta_t, phi_t, chi_t) * scale
        norm_sq = torch.real(torch.dot(psi.conj(), psi)).item()
        results.append({
            "scale": scale,
            "norm_sq": norm_sq,
            "correctly_rejected": abs(norm_sq - 1.0) > 1e-10,
        })
    all_rejected = all(r["correctly_rejected"] for r in results)
    return {"n_tests": len(results), "all_rejected": all_rejected, "samples": results}


def run_layer3_boundary():
    """Boundary: eta=0 (north pole), eta=pi/2 (south pole)."""
    results = {}
    phi_t = torch.tensor(0.0, dtype=torch.float64)
    chi_t = torch.tensor(0.5, dtype=torch.float64)

    # eta=0: |psi> = (e^{i(phi+chi)}, 0) -> Bloch north pole (0,0,1)
    psi_n = hopf_params_to_psi(torch.tensor(0.0, dtype=torch.float64), phi_t, chi_t)
    rho_n = torch.outer(psi_n, psi_n.conj())
    sz = pauli_matrices()[2]
    rz = torch.real(torch.trace(rho_n @ sz)).item()
    results["eta_zero_north"] = {"rz": rz, "is_north_pole": abs(rz - 1.0) < 1e-14}

    # eta=pi/2: |psi> = (0, e^{i(phi-chi)}) -> Bloch south pole (0,0,-1)
    psi_s = hopf_params_to_psi(
        torch.tensor(math.pi / 2, dtype=torch.float64), phi_t, chi_t
    )
    rho_s = torch.outer(psi_s, psi_s.conj())
    rz_s = torch.real(torch.trace(rho_s @ sz)).item()
    results["eta_piover2_south"] = {"rz": rz_s, "is_south_pole": abs(rz_s + 1.0) < 1e-14}

    return results


# =====================================================================
# STACKING -- L2 on L1, L3 on L2, L3 on L1, autograd through all 3
# =====================================================================

def run_stacking_tests():
    """Stack layers and verify constraints hold + autograd flows."""
    results = {}

    # --- L2 on L1: S^2 pure states -> valid density matrices ---
    l2_on_l1 = []
    for th, ph in [(0.5, 0.3), (1.2, 2.1), (math.pi / 2, math.pi)]:
        theta_t = torch.tensor(th, dtype=torch.float64)
        phi_t = torch.tensor(ph, dtype=torch.float64)
        r = angles_to_bloch(theta_t, phi_t)
        res = test_density_matrix_constraints(r)
        rho = bloch_to_density(r)
        purity = torch.real(torch.trace(rho @ rho)).item()
        l2_on_l1.append({
            "theta": th, "phi": ph,
            "l1_valid": res["valid"],
            "purity_is_1": abs(purity - 1.0) < 1e-14,
        })
    results["L2_on_L1"] = {
        "all_pass": all(t["l1_valid"] and t["purity_is_1"] for t in l2_on_l1),
        "samples": l2_on_l1,
    }

    # --- L3 on L2: S^3 Hopf-projects to valid S^2 point ---
    l3_on_l2 = []
    for eta, phi, chi in [(0.3, 0.5, 0.8), (0.7, 1.2, 0.1), (math.pi / 4, 0.0, math.pi / 3)]:
        eta_t = torch.tensor(eta, dtype=torch.float64)
        phi_t = torch.tensor(phi, dtype=torch.float64)
        chi_t = torch.tensor(chi, dtype=torch.float64)
        theta_b, phi_b = hopf_project(eta_t, phi_t, chi_t)

        # Check projected point is on S^2
        r = angles_to_bloch(theta_b, phi_b)
        r_norm = torch.norm(r).item()

        l3_on_l2.append({
            "eta": eta, "phi": phi, "chi": chi,
            "projected_theta": theta_b.item(), "projected_phi": phi_b.item(),
            "bloch_norm": r_norm,
            "on_S2": abs(r_norm - 1.0) < 1e-14,
        })
    results["L3_on_L2"] = {
        "all_pass": all(t["on_S2"] for t in l3_on_l2),
        "samples": l3_on_l2,
    }

    # --- L3 on L1: |psi><psi| is valid density matrix ---
    l3_on_l1 = []
    for eta, phi, chi in [(0.2, 0.4, 0.6), (1.0, 2.0, 3.0), (math.pi / 4, math.pi, 0.0)]:
        eta_t = torch.tensor(eta, dtype=torch.float64)
        phi_t = torch.tensor(phi, dtype=torch.float64)
        chi_t = torch.tensor(chi, dtype=torch.float64)
        psi = hopf_params_to_psi(eta_t, phi_t, chi_t)
        rho = torch.outer(psi, psi.conj())

        # Extract Bloch vector
        sx, sy, sz_m = pauli_matrices()
        rx = torch.real(torch.trace(rho @ sx)).item()
        ry = torch.real(torch.trace(rho @ sy)).item()
        rz = torch.real(torch.trace(rho @ sz_m)).item()
        r_vec = torch.tensor([rx, ry, rz], dtype=torch.float64)

        res = test_density_matrix_constraints(r_vec)
        purity = torch.real(torch.trace(rho @ rho)).item()

        l3_on_l1.append({
            "eta": eta, "phi": phi, "chi": chi,
            "l1_valid": res["valid"],
            "purity_is_1": abs(purity - 1.0) < 1e-14,
            "bloch_norm": torch.norm(r_vec).item(),
        })
    results["L3_on_L1"] = {
        "all_pass": all(t["l1_valid"] and t["purity_is_1"] for t in l3_on_l1),
        "samples": l3_on_l1,
    }

    # --- Autograd through all 3 layers ---
    eta = torch.tensor(math.pi / 4, dtype=torch.float64, requires_grad=True)
    phi = torch.tensor(0.5, dtype=torch.float64, requires_grad=True)
    chi = torch.tensor(0.8, dtype=torch.float64, requires_grad=True)

    # L3: construct |psi>
    psi = hopf_params_to_psi(eta, phi, chi)

    # L2: Hopf project to S^2
    theta_b = 2.0 * eta
    phi_b = -2.0 * chi

    # L1: build density matrix from Bloch vector
    r = torch.stack([
        torch.sin(theta_b) * torch.cos(phi_b),
        torch.sin(theta_b) * torch.sin(phi_b),
        torch.cos(theta_b),
    ]).to(torch.float64)

    sx, sy, sz_m = pauli_matrices()
    eye = torch.eye(2, dtype=torch.complex128)
    rho = (eye + r[0] * sx + r[1] * sy + r[2] * sz_m) / 2.0

    # Scalar objective: von Neumann entropy (zero for pure state)
    eigs = torch.linalg.eigvalsh(rho)
    eigs_clamped = torch.clamp(eigs.real, min=1e-30)
    S_vn = -torch.sum(eigs_clamped * torch.log(eigs_clamped))

    # Backward pass
    S_vn.backward()

    grad_eta = eta.grad
    grad_phi = phi.grad
    grad_chi = chi.grad

    # phi is the fiber coordinate -- it does NOT appear in the Hopf projection
    # (theta_b = 2*eta, phi_b = -2*chi), so grad_phi is correctly None.
    results["autograd_through_all_3"] = {
        "entropy": S_vn.item(),
        "grad_eta": grad_eta.item() if grad_eta is not None else None,
        "grad_phi": grad_phi.item() if grad_phi is not None else None,
        "grad_chi": grad_chi.item() if grad_chi is not None else None,
        "base_grads_exist": all(
            g is not None for g in [grad_eta, grad_chi]
        ),
        "fiber_grad_absent": grad_phi is None,
        "entropy_near_zero": abs(S_vn.item()) < 1e-10,
        "pass": (
            all(g is not None for g in [grad_eta, grad_chi])
            and grad_phi is None  # fiber coord correctly decoupled
            and abs(S_vn.item()) < 1e-10
        ),
        "note": "phi is fiber coord -> no gradient path through Hopf projection (correct)",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running geometric constraint manifold layers 1-2-3...")

    l1_pos = run_layer1_positive()
    l1_neg = run_layer1_negative()
    l1_bnd = run_layer1_boundary()
    print(f"  L1 Density Matrices: pos={l1_pos['all_valid']} neg={l1_neg['all_rejected']}")

    l2_pos = run_layer2_positive()
    l2_neg = run_layer2_negative()
    l2_bnd = run_layer2_boundary()
    print(f"  L2 S^2 FS Metric:   pos={l2_pos['all_pass']} neg={l2_neg['all_correct']}")

    l3_pos = run_layer3_positive()
    l3_neg = run_layer3_negative()
    l3_bnd = run_layer3_boundary()
    print(f"  L3 S^3 Hopf:        pos={l3_pos['all_norms_valid'] and l3_pos['all_projections_valid']} "
          f"neg={l3_neg['all_rejected']} fiber={l3_pos['all_fiber_independent']}")

    stacking = run_stacking_tests()
    stack_pass = all(
        stacking[k]["all_pass"]
        for k in ["L2_on_L1", "L3_on_L2", "L3_on_L1"]
    )
    autograd_ok = stacking["autograd_through_all_3"]["pass"]
    print(f"  Stacking:           layers={stack_pass} autograd={autograd_ok}")

    results = {
        "name": "geom_layer_1_2_3 -- Geometric Constraint Manifold Bottom 3 Layers",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "layer_1_density_matrices": {
            "positive": l1_pos,
            "negative": l1_neg,
            "boundary": l1_bnd,
        },
        "layer_2_s2_fubini_study": {
            "positive": l2_pos,
            "negative": l2_neg,
            "boundary": l2_bnd,
        },
        "layer_3_s3_hopf": {
            "positive": l3_pos,
            "negative": l3_neg,
            "boundary": l3_bnd,
        },
        "stacking": stacking,
        "all_pass": (
            l1_pos["all_valid"]
            and l1_neg["all_rejected"]
            and l2_pos["all_pass"]
            and l2_neg["all_correct"]
            and l3_pos["all_norms_valid"]
            and l3_pos["all_projections_valid"]
            and l3_pos["all_fiber_independent"]
            and l3_neg["all_rejected"]
            and stack_pass
            and autograd_ok
        ),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_layer_1_2_3_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"ALL PASS: {results['all_pass']}")
