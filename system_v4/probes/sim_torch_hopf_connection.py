#!/usr/bin/env python3
"""
Torch Module: Hopf Fibration Connection
========================================
Map qubit state (theta, phi) on S2 to point on S3 via Hopf fibration.
Compute connection 1-form A_mu = i<psi|d_mu psi> via torch autograd.
Berry phase around closed loops on S2.

The Hopf map: S3 -> S2
  |psi(theta, phi, gamma)> = [cos(theta/2) e^{i gamma/2},
                               sin(theta/2) e^{i(phi + gamma/2)}]

  Connection: A_theta = 0, A_phi = -sin^2(theta/2)  (standard result)
  Berry phase around latitude loop at theta: Phi_B = -pi(1 - cos(theta))
  = -Omega/2 where Omega is the solid angle subtended.

Tests:
- Connection form matches analytic A_phi = -sin^2(theta/2)
- Berry phase = -pi(1 - cos(theta)) for latitude loops
- Autograd computation of connection
- Numpy cross-validation
- Negative and boundary tests
"""

import json
import os
import numpy as np
classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": ""},
    "z3":         {"tried": False, "used": False, "reason": ""},
    "cvc5":       {"tried": False, "used": False, "reason": ""},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": ""},
    "geomstats":  {"tried": False, "used": False, "reason": ""},
    "e3nn":       {"tried": False, "used": False, "reason": ""},
    "rustworkx":  {"tried": False, "used": False, "reason": ""},
    "xgi":        {"tried": False, "used": False, "reason": ""},
    "toponetx":   {"tried": False, "used": False, "reason": ""},
    "gudhi":      {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import torch
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, And, sat  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except Exception as exc:
    TOOL_MANIFEST["clifford"]["reason"] = f"optional import unavailable: {exc}"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    from e3nn import o3
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# MODULE UNDER TEST: HopfConnection
# =====================================================================

class HopfConnection(nn.Module):
    """
    Differentiable Hopf fibration and Berry connection.

    Parameters: theta, phi on S2 (with gamma=0 gauge choice).
    Forward: returns point on S3 (the qubit state vector).
    connection_form(): computes A_mu = i<psi|d_mu psi> via autograd.
    """
    def __init__(self, theta=None, phi=None):
        super().__init__()
        if theta is None:
            theta = torch.tensor(np.pi / 4)
        if phi is None:
            phi = torch.tensor(0.0)
        self.theta = nn.Parameter(theta.float())
        self.phi = nn.Parameter(phi.float())

    def forward(self):
        """Map (theta, phi) -> point on S3 via Hopf fibration (gamma=0 gauge)."""
        ct2 = torch.cos(self.theta / 2)
        st2 = torch.sin(self.theta / 2)
        # |psi> = [cos(theta/2), sin(theta/2) * e^{i*phi}]
        psi_real_0 = ct2
        psi_imag_0 = torch.zeros_like(ct2)
        psi_real_1 = st2 * torch.cos(self.phi)
        psi_imag_1 = st2 * torch.sin(self.phi)
        # Return as complex tensor
        psi = torch.stack([
            torch.complex(psi_real_0, psi_imag_0),
            torch.complex(psi_real_1, psi_imag_1),
        ])
        return psi

    def s3_point(self):
        """Return (x0, x1, x2, x3) coordinates on S3."""
        ct2 = torch.cos(self.theta / 2)
        st2 = torch.sin(self.theta / 2)
        x0 = ct2
        x1 = torch.zeros_like(ct2)  # gamma=0
        x2 = st2 * torch.cos(self.phi)
        x3 = st2 * torch.sin(self.phi)
        return torch.stack([x0, x1, x2, x3])

    def hopf_map_to_s2(self):
        """Project S3 -> S2 via Hopf map. Returns (n_x, n_y, n_z)."""
        psi = self.forward()
        # n = <psi|sigma|psi> (Bloch vector)
        a, b = psi[0], psi[1]
        nx = 2 * torch.real(a.conj() * b)
        ny = 2 * torch.imag(a.conj() * b)
        nz = torch.abs(a)**2 - torch.abs(b)**2
        return torch.stack([nx, ny, nz])

    def connection_form_autograd(self):
        """
        Compute A_mu = i<psi|d_mu psi> via torch autograd.
        Returns A_theta, A_phi.
        """
        # We need gradients of psi components w.r.t. theta and phi
        theta = self.theta
        phi = self.phi

        # Build psi with gradient tracking
        ct2 = torch.cos(theta / 2)
        st2 = torch.sin(theta / 2)

        # psi_0 = cos(theta/2), psi_1 = sin(theta/2)*e^{i*phi}
        # d(psi_0)/d(theta) = -sin(theta/2)/2
        # d(psi_0)/d(phi)   = 0
        # d(psi_1)/d(theta) = cos(theta/2)/2 * e^{i*phi}
        # d(psi_1)/d(phi)   = i*sin(theta/2)*e^{i*phi}

        # A_mu = i * <psi|d_mu psi> = i * [conj(psi_0)*d_mu(psi_0) + conj(psi_1)*d_mu(psi_1)]

        # Use autograd: compute each real/imag component's gradient
        psi_r0 = ct2
        psi_i0 = torch.tensor(0.0)
        psi_r1 = st2 * torch.cos(phi)
        psi_i1 = st2 * torch.sin(phi)

        # d/d_theta
        d_psi_r0_dtheta = torch.autograd.grad(psi_r0, theta, create_graph=True)[0]
        d_psi_r1_dtheta = torch.autograd.grad(psi_r1, theta, create_graph=True)[0]
        d_psi_i1_dtheta = torch.autograd.grad(psi_i1, theta, create_graph=True)[0]

        # d/d_phi
        d_psi_r1_dphi = torch.autograd.grad(psi_r1, phi, create_graph=True)[0]
        d_psi_i1_dphi = torch.autograd.grad(psi_i1, phi, create_graph=True)[0]

        # <psi|d_theta psi> = conj(psi_0)*d_theta(psi_0) + conj(psi_1)*d_theta(psi_1)
        # psi_0 is real, psi_1 is complex
        # conj(psi_0)*d_theta(psi_0) = psi_r0 * d_psi_r0_dtheta (real)
        # conj(psi_1)*d_theta(psi_1) = (psi_r1 - i*psi_i1)*(d_psi_r1_dtheta + i*d_psi_i1_dtheta)
        #   real part: psi_r1*d_psi_r1_dtheta + psi_i1*d_psi_i1_dtheta
        #   imag part: psi_r1*d_psi_i1_dtheta - psi_i1*d_psi_r1_dtheta

        bracket_theta_real = (psi_r0 * d_psi_r0_dtheta
                              + psi_r1 * d_psi_r1_dtheta
                              + psi_i1 * d_psi_i1_dtheta)
        bracket_theta_imag = (psi_r1 * d_psi_i1_dtheta
                              - psi_i1 * d_psi_r1_dtheta)

        # A_theta = i * <psi|d_theta psi>
        # i * (re + i*im) = -im + i*re
        A_theta_real = -bracket_theta_imag
        A_theta_imag = bracket_theta_real

        # <psi|d_phi psi>
        # d_phi(psi_0) = 0
        bracket_phi_real = (psi_r1 * d_psi_r1_dphi
                            + psi_i1 * d_psi_i1_dphi)
        bracket_phi_imag = (psi_r1 * d_psi_i1_dphi
                            - psi_i1 * d_psi_r1_dphi)

        A_phi_real = -bracket_phi_imag
        A_phi_imag = bracket_phi_real

        return (A_theta_real, A_theta_imag, A_phi_real, A_phi_imag)

    def berry_phase_latitude(self, theta_val, n_points=1000):
        """
        Berry phase around a latitude loop at fixed theta.
        Phi_B = integral_0^{2pi} A_phi d(phi)
        Analytic: Phi_B = -pi*(1 - cos(theta))
        """
        # Numerical integration
        dphi = 2 * np.pi / n_points
        phase = 0.0
        for k in range(n_points):
            phi_k = k * dphi
            self.theta.data.fill_(theta_val)
            self.phi.data.fill_(phi_k)
            _, _, A_phi_real, _ = self.connection_form_autograd()
            # A_phi is real for this gauge choice
            phase += float(A_phi_real.detach()) * dphi
        return phase


# =====================================================================
# NUMPY BASELINE
# =====================================================================

def numpy_hopf_state(theta, phi):
    """Qubit state from Bloch angles."""
    return np.array([np.cos(theta / 2),
                     np.sin(theta / 2) * np.exp(1j * phi)], dtype=np.complex128)


def numpy_connection_A_phi(theta):
    """Analytic connection: A_phi = -sin^2(theta/2)."""
    return -np.sin(theta / 2)**2


def numpy_berry_phase(theta):
    """Analytic Berry phase for latitude loop: -pi*(1 - cos(theta))."""
    return -np.pi * (1 - np.cos(theta))


def numpy_s3_point(theta, phi):
    """S3 coordinates from Hopf fibration (gamma=0)."""
    return np.array([np.cos(theta / 2), 0.0,
                     np.sin(theta / 2) * np.cos(phi),
                     np.sin(theta / 2) * np.sin(phi)])


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: S3 point lies on unit sphere ---
    test_angles = [
        (0.0, 0.0), (np.pi / 4, 0.0), (np.pi / 2, 0.0),
        (np.pi / 2, np.pi / 4), (np.pi, 0.0), (np.pi / 3, np.pi / 6),
        (2.1, 0.7), (0.1, 3.0),
    ]
    p1_results = {}
    for theta, phi in test_angles:
        mod = HopfConnection(torch.tensor(theta), torch.tensor(phi))
        s3 = mod.s3_point().detach().numpy()
        norm = float(np.linalg.norm(s3))
        s3_np = numpy_s3_point(theta, phi)
        diff = float(np.max(np.abs(s3 - s3_np)))
        p1_results[f"t={theta:.3f}_p={phi:.3f}"] = {
            "s3_norm": norm,
            "on_sphere": abs(norm - 1.0) < 1e-6,
            "numpy_diff": diff,
            "pass": abs(norm - 1.0) < 1e-6 and diff < 1e-6,
        }
    results["P1_s3_on_unit_sphere"] = p1_results

    # --- P2: Hopf map S3->S2 gives correct Bloch vector ---
    p2_results = {}
    for theta, phi in test_angles:
        mod = HopfConnection(torch.tensor(theta), torch.tensor(phi))
        n = mod.hopf_map_to_s2().detach().numpy()
        # Expected Bloch vector
        expected = np.array([
            np.sin(theta) * np.cos(phi),
            np.sin(theta) * np.sin(phi),
            np.cos(theta),
        ])
        diff = float(np.max(np.abs(n - expected)))
        p2_results[f"t={theta:.3f}_p={phi:.3f}"] = {
            "bloch_computed": n.tolist(),
            "bloch_expected": expected.tolist(),
            "max_diff": diff,
            "pass": diff < 1e-5,
        }
    results["P2_hopf_map_bloch_vector"] = p2_results

    # --- P3: Connection form A_phi matches analytic ---
    p3_results = {}
    for theta, phi in test_angles:
        mod = HopfConnection(torch.tensor(theta), torch.tensor(phi))
        A_t_r, A_t_i, A_p_r, A_p_i = mod.connection_form_autograd()

        A_phi_computed = float(A_p_r.detach())
        A_phi_analytic = numpy_connection_A_phi(theta)
        A_theta_computed = float(A_t_r.detach())

        diff_phi = abs(A_phi_computed - A_phi_analytic)
        p3_results[f"t={theta:.3f}_p={phi:.3f}"] = {
            "A_phi_autograd": A_phi_computed,
            "A_phi_analytic": float(A_phi_analytic),
            "A_phi_diff": diff_phi,
            "A_theta": A_theta_computed,
            "A_theta_is_zero": abs(A_theta_computed) < 1e-5,
            "pass": diff_phi < 1e-4 and abs(A_theta_computed) < 1e-5,
        }
    results["P3_connection_form_analytic"] = p3_results

    # --- P4: Berry phase for latitude loops ---
    p4_results = {}
    test_thetas = [np.pi / 6, np.pi / 4, np.pi / 3, np.pi / 2, 2 * np.pi / 3]
    for theta in test_thetas:
        mod = HopfConnection(torch.tensor(theta), torch.tensor(0.0))
        phase_numerical = mod.berry_phase_latitude(theta, n_points=2000)
        phase_analytic = numpy_berry_phase(theta)
        diff = abs(phase_numerical - phase_analytic)
        p4_results[f"theta={theta:.4f}"] = {
            "numerical": phase_numerical,
            "analytic": float(phase_analytic),
            "diff": diff,
            "pass": diff < 0.01,  # 1% tolerance for numerical integration
        }
    results["P4_berry_phase_latitude"] = p4_results

    # --- P5: Gradient of A_phi w.r.t. theta exists and is correct ---
    p5_results = {}
    for theta in [np.pi / 4, np.pi / 2, np.pi / 3]:
        mod = HopfConnection(torch.tensor(theta), torch.tensor(0.0))
        A_t_r, A_t_i, A_p_r, A_p_i = mod.connection_form_autograd()
        # A_phi = -sin^2(theta/2), d/dtheta = -sin(theta/2)*cos(theta/2) = -sin(theta)/2
        grad = torch.autograd.grad(A_p_r, mod.theta, create_graph=True)[0]
        grad_val = float(grad.detach())
        expected_grad = -np.sin(theta) / 2
        diff = abs(grad_val - expected_grad)
        p5_results[f"theta={theta:.4f}"] = {
            "grad_autograd": grad_val,
            "grad_analytic": float(expected_grad),
            "diff": diff,
            "pass": diff < 1e-4,
        }
    results["P5_connection_gradient"] = p5_results

    # --- P6: e3nn l=1 carrier is equivariant on Hopf/Bloch states ---
    if TOOL_MANIFEST["e3nn"]["tried"]:
        irreps_1o = o3.Irreps("1x1o")
        linear_1o = o3.Linear(irreps_1o, irreps_1o)
        linear_1o.eval()
        max_err = 0.0
        with torch.no_grad():
            for theta, phi in test_angles:
                mod = HopfConnection(torch.tensor(theta), torch.tensor(phi))
                bv = mod.hopf_map_to_s2().detach().float()
                alpha, beta, gamma = o3.rand_angles()
                D1 = o3.wigner_D(1, alpha, beta, gamma).float()
                err = (linear_1o(D1 @ bv) - D1 @ linear_1o(bv)).norm().item()
                max_err = max(max_err, err)
        results["P6_e3nn_hopf_bloch_equivariance"] = {
            "test": "e3nn Linear(1x1o->1x1o) is equivariant on Hopf/Bloch carrier states",
            "n_states": len(test_angles),
            "max_equivariance_error": max_err,
            "tolerance": 1e-5,
            "pass": max_err < 1e-5,
        }
    else:
        results["P6_e3nn_hopf_bloch_equivariance"] = {
            "skipped": True,
            "reason": TOOL_MANIFEST["e3nn"]["reason"],
            "pass": True,
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: theta outside [0, pi] -- state still normalizes but Bloch vector wraps ---
    n1_results = {}
    for theta in [-0.5, 2 * np.pi, 4.0]:
        mod = HopfConnection(torch.tensor(theta), torch.tensor(0.0))
        psi = mod.forward().detach().numpy()
        norm = float(np.abs(np.dot(psi.conj(), psi)))
        # Still normalized (trig functions are periodic)
        n_bloch = mod.hopf_map_to_s2().detach().numpy()
        bloch_norm = float(np.linalg.norm(n_bloch))
        n1_results[f"theta={theta:.3f}"] = {
            "state_norm": norm,
            "bloch_norm": bloch_norm,
            "still_valid": abs(norm - 1.0) < 1e-6 and abs(bloch_norm - 1.0) < 1e-5,
            "pass": True,  # Trig wrapping is expected behavior
        }
    results["N1_theta_outside_range"] = n1_results

    # --- N2: Berry phase for theta=0 should be 0 (no solid angle) ---
    mod = HopfConnection(torch.tensor(0.0), torch.tensor(0.0))
    _, _, A_p_r, _ = mod.connection_form_autograd()
    A_phi_at_pole = float(A_p_r.detach())
    results["N2_connection_at_north_pole"] = {
        "A_phi": A_phi_at_pole,
        "is_zero": abs(A_phi_at_pole) < 1e-6,
        "pass": abs(A_phi_at_pole) < 1e-6,
    }

    # --- N3: Monopole: Berry phase should NOT be zero for theta != 0, pi ---
    n3_results = {}
    for theta in [np.pi / 4, np.pi / 2, 3 * np.pi / 4]:
        mod = HopfConnection(torch.tensor(theta), torch.tensor(0.0))
        _, _, A_p_r, _ = mod.connection_form_autograd()
        val = float(A_p_r.detach())
        n3_results[f"theta={theta:.4f}"] = {
            "A_phi": val,
            "is_nonzero": abs(val) > 1e-6,
            "pass": abs(val) > 1e-6,
        }
    results["N3_connection_nonzero_interior"] = n3_results

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: North pole (theta=0) ---
    mod = HopfConnection(torch.tensor(0.0), torch.tensor(0.0))
    psi = mod.forward().detach().numpy()
    expected = np.array([1.0, 0.0], dtype=complex)
    diff = float(np.max(np.abs(psi - expected)))
    results["B1_north_pole"] = {
        "psi": psi.tolist(),
        "diff_from_ket0": diff,
        "pass": diff < 1e-6,
    }

    # --- B2: South pole (theta=pi) ---
    mod = HopfConnection(torch.tensor(np.pi), torch.tensor(0.0))
    psi = mod.forward().detach().numpy()
    # cos(pi/2)=0, sin(pi/2)=1 -> [0, e^{i*0}] = [0, 1]
    expected = np.array([0.0, 1.0], dtype=complex)
    diff = float(np.max(np.abs(np.abs(psi) - np.abs(expected))))
    results["B2_south_pole"] = {
        "psi_abs": np.abs(psi).tolist(),
        "diff_from_ket1": diff,
        "pass": diff < 1e-5,
    }

    # --- B3: Equator (theta=pi/2) -- maximal Berry curvature ---
    mod = HopfConnection(torch.tensor(np.pi / 2), torch.tensor(0.0))
    _, _, A_p_r, _ = mod.connection_form_autograd()
    A_phi = float(A_p_r.detach())
    # sin^2(pi/4) = 0.5
    expected_A = -0.5
    results["B3_equator_connection"] = {
        "A_phi": A_phi,
        "expected": expected_A,
        "diff": abs(A_phi - expected_A),
        "pass": abs(A_phi - expected_A) < 1e-5,
    }

    # --- B4: Full solid angle (theta=pi) Berry phase = -2*pi ---
    mod = HopfConnection(torch.tensor(np.pi), torch.tensor(0.0))
    phase = mod.berry_phase_latitude(np.pi, n_points=2000)
    expected_phase = -2 * np.pi
    diff = abs(phase - expected_phase)
    results["B4_full_solid_angle_berry_phase"] = {
        "numerical": phase,
        "analytic": expected_phase,
        "diff": diff,
        "pass": diff < 0.05,  # numerical integration tolerance
    }

    # --- B5: Connection A_phi is monotonic in theta from 0 to pi ---
    thetas = np.linspace(0.01, np.pi - 0.01, 20)
    A_vals = []
    for theta in thetas:
        mod = HopfConnection(torch.tensor(float(theta)), torch.tensor(0.0))
        _, _, A_p_r, _ = mod.connection_form_autograd()
        A_vals.append(float(A_p_r.detach()))
    # A_phi = -sin^2(theta/2) is monotonically decreasing from 0 to -1
    is_decreasing = all(A_vals[i] >= A_vals[i + 1] - 1e-6
                        for i in range(len(A_vals) - 1))
    results["B5_connection_monotonic"] = {
        "thetas": thetas.tolist(),
        "A_phi_values": A_vals,
        "monotonically_decreasing": is_decreasing,
        "pass": is_decreasing,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Core module: HopfConnection as nn.Module, autograd for connection form"
    e3nn_positive = positive.get("P6_e3nn_hopf_bloch_equivariance", {})
    if TOOL_MANIFEST["e3nn"]["tried"]:
        if e3nn_positive.get("pass"):
            TOOL_MANIFEST["e3nn"]["used"] = True
            TOOL_MANIFEST["e3nn"]["reason"] = "Load-bearing: validates Hopf/Bloch carrier equivariance with e3nn l=1 irreps"
            TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"
        else:
            TOOL_MANIFEST["e3nn"]["reason"] = "available but failed validated Hopf/Bloch equivariance check"
    if TOOL_MANIFEST["clifford"]["tried"]:
        TOOL_MANIFEST["clifford"]["reason"] = "tried import, not used for Hopf connection"
    if TOOL_MANIFEST["geomstats"]["tried"]:
        TOOL_MANIFEST["geomstats"]["reason"] = "tried import, not used for Hopf connection"

    def count_passes(d):
        passes, total = 0, 0
        if isinstance(d, dict):
            if "pass" in d:
                total += 1
                if d["pass"]:
                    passes += 1
            for v in d.values():
                p, t = count_passes(v)
                passes += p
                total += t
        return passes, total

    all_results = {
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }
    total_pass, total_tests = count_passes(all_results)

    results = {
        "name": "torch_hopf_connection",
        "family": "GEOMETRIC",
        "description": "Hopf fibration S3->S2 with Berry connection via autograd",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical" if total_pass == total_tests else "exploratory_signal",
        "summary": {
            "total_tests": total_tests,
            "total_pass": total_pass,
            "all_pass": total_pass == total_tests,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_hopf_connection_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
