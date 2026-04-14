#!/usr/bin/env python3
"""
Wilczek-Zee Non-Abelian Geometric Phase
=======================================

Pure math lego: non-abelian holonomy for a genuinely degenerate eigenspace.

Model:
  - Four-level Hamiltonian with a fixed spectral doublet {-1, -1, +1, +1}.
  - A parameter-dependent unitary rotates the degenerate doublet through the
    ambient space while preserving the two-fold eigenvalue degeneracy.
  - The degenerate-frame connection A_mu^{ab} = <a|d_mu b> is therefore a
    bona fide U(2) gauge field, and its traceless part produces SU(2)
    holonomy after closed-loop transport.

Tests:
  POSITIVE:
    - Abelian Berry-phase limit matches the solid-angle formula modulo 2*pi
    - Non-abelian loops generate off-diagonal holonomy
    - Path ordering matters when A_theta and A_phi do not commute
    - Closed-loop holonomy is unitary with determinant 1
    - Loop size changes the holonomy
    - Autograd differentiates through the Hamiltonian
  NEGATIVE:
    - Trivial loop gives identity holonomy
    - Explicit splitting removes the double degeneracy
    - Commuting surrogate connection removes ordering sensitivity
  BOUNDARY:
    - Small loops remain near identity
    - Fixed-latitude 2*pi loop yields a strong but diagonal SU(2) holonomy
    - Discretisation converges as step count increases

Mark pytorch=used, sympy=used. Classification: canonical.
Output: sim_results/lego_wilczek_zee_results.json
"""

import json
import math
import os
import time
import traceback

import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- finite-dimensional matrix transport only"},
    "z3":        {"tried": False, "used": False, "reason": "not needed for this sim"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed for this sim"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": "not needed for this sim"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- explicit matrix geometry suffices"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed for this sim"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this sim"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed for this sim"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed for this sim"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed for this sim"},
}

try:
    import torch

    torch.set_default_dtype(torch.float64)
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core: complex matrix exponentials, eigenspace transport, "
        "holonomy accumulation, and autograd validation"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Symbolic cross-check of the abelian Berry-phase solid-angle formula"
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# CORE: DEGENERATE DOUBLET MODEL
# =====================================================================

SIGMA_X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
SIGMA_Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)

GENERATOR_THETA = torch.zeros((4, 4), dtype=torch.complex128)
GENERATOR_THETA[:2, :2] = 0.5 * SIGMA_X

GENERATOR_PHI = torch.zeros((4, 4), dtype=torch.complex128)
GENERATOR_PHI[:2, :2] = 0.5 * SIGMA_Z
GENERATOR_PHI[0, 2] = 0.7
GENERATOR_PHI[2, 0] = 0.7

BASE_HAMILTONIAN = torch.diag(torch.tensor([-1.0, -1.0, 1.0, 1.0], dtype=torch.complex128))
DOUBLE_SPLITTING = torch.diag(torch.tensor([1.0, -1.0, 0.0, 0.0], dtype=torch.complex128))
DEGENERATE_FRAME = torch.eye(4, dtype=torch.complex128)[:, :2]


def collect_tools_used():
    return sorted([name for name, meta in TOOL_MANIFEST.items() if meta["used"]])


def principal_angle_difference(a, b):
    """Distance on the circle for phase comparisons."""
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


def rotation_unitary(theta, phi):
    """Parameter-dependent unitary that moves the degenerate doublet."""
    theta_tensor = theta.to(torch.float64) if isinstance(theta, torch.Tensor) else torch.tensor(theta, dtype=torch.float64)
    phi_tensor = phi.to(torch.float64) if isinstance(phi, torch.Tensor) else torch.tensor(phi, dtype=torch.float64)
    return (
        torch.matrix_exp(-1j * phi_tensor * GENERATOR_PHI)
        @ torch.matrix_exp(-1j * theta_tensor * GENERATOR_THETA)
    )


def build_hamiltonian(theta, phi, delta=0.0):
    """
    Four-level Hamiltonian with an exact doublet at energy -1.

    delta breaks the doublet inside the transported subspace while preserving
    the overall rotated-frame structure.
    """
    W = rotation_unitary(theta, phi)
    H = W @ BASE_HAMILTONIAN @ W.conj().T
    if delta != 0.0:
        H = H + delta * (W @ DOUBLE_SPLITTING @ W.conj().T)
    return H


def degenerate_basis(theta, phi):
    """Smooth orthonormal frame for the transported two-dimensional eigenspace."""
    return rotation_unitary(theta, phi) @ DEGENERATE_FRAME


def get_degenerate_subspace(H, target_energy=-1.0, tol=1e-8):
    """Return the eigenspace near target_energy."""
    evals, evecs = torch.linalg.eigh(H)
    mask = torch.abs(evals - target_energy) < tol
    indices = torch.where(mask)[0]
    return evecs[:, indices], target_energy, int(indices.numel())


def compute_connection(theta, phi, dtheta=1e-6, dphi=1e-6):
    """
    Compute the non-abelian connection A_theta, A_phi for the degenerate frame.

    Central differences keep the connection anti-Hermitian to numerical
    precision after explicit projection.
    """
    basis0 = degenerate_basis(theta, phi)
    dbasis_dtheta = (
        degenerate_basis(theta + dtheta, phi) - degenerate_basis(theta - dtheta, phi)
    ) / (2.0 * dtheta)
    dbasis_dphi = (
        degenerate_basis(theta, phi + dphi) - degenerate_basis(theta, phi - dphi)
    ) / (2.0 * dphi)

    A_theta = basis0.conj().T @ dbasis_dtheta
    A_phi = basis0.conj().T @ dbasis_dphi

    # Numerical projection back to the Lie algebra u(2).
    A_theta = 0.5 * (A_theta - A_theta.conj().T)
    A_phi = 0.5 * (A_phi - A_phi.conj().T)
    return A_theta, A_phi, 2


def compute_commuting_connection(theta, phi, dtheta=1e-6, dphi=1e-6):
    """
    Diagonal surrogate of the full connection.

    This removes the non-abelian mixing and gives a commuting reference.
    """
    A_theta, A_phi, g = compute_connection(theta, phi, dtheta=dtheta, dphi=dphi)
    A_theta_diag = torch.diag(torch.diagonal(A_theta))
    A_phi_diag = torch.diag(torch.diagonal(A_phi))
    return A_theta_diag, A_phi_diag, g


def path_ordered_transport(theta_path, phi_path, connection_fn=compute_connection):
    """Path-ordered exponential along a discretised closed path."""
    N = len(theta_path)
    assert N == len(phi_path)

    U = torch.eye(2, dtype=torch.complex128)
    connections = []

    for i in range(N - 1):
        th = theta_path[i]
        ph = phi_path[i]
        dth = theta_path[i + 1] - theta_path[i]
        dph = phi_path[i + 1] - phi_path[i]

        A_theta, A_phi, _ = connection_fn(th, ph)
        connections.append((A_theta.clone(), A_phi.clone()))

        U = torch.matrix_exp(A_theta * dth + A_phi * dph) @ U

    return U, connections, 2


def rectangular_loop(theta0, theta1, phi0, phi1):
    """Axis-aligned closed loop in parameter space."""
    points = [
        (theta0, phi0),
        (theta1, phi0),
        (theta1, phi1),
        (theta0, phi1),
        (theta0, phi0),
    ]
    return [p[0] for p in points], [p[1] for p in points]


def circular_loop(theta_center, phi_center, radius_theta, radius_phi, steps):
    """Smooth closed loop used for transport and convergence tests."""
    t_vals = np.linspace(0.0, 2.0 * np.pi, steps + 1)
    theta_path = [theta_center + radius_theta * math.cos(t) for t in t_vals]
    phi_path = [phi_center + radius_phi * math.sin(t) for t in t_vals]
    return theta_path, phi_path


# =====================================================================
# ABELIAN (BERRY PHASE) REFERENCE
# =====================================================================

def berry_phase_single_qubit(theta_half_angle):
    """Closed-form Berry phase for a spin-1/2 cone loop."""
    omega = 2.0 * math.pi * (1.0 - math.cos(theta_half_angle))
    return -omega / 2.0


def compute_berry_phase_numerically(theta_fix, n_steps=600):
    """Parallel-transport computation of the abelian Berry phase."""
    phases = np.linspace(0.0, 2.0 * np.pi, n_steps + 1)

    sx = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)

    st = math.sin(theta_fix)
    ct = math.cos(theta_fix)

    vecs = []
    for phi in phases:
        H = st * math.cos(phi) * sx + st * math.sin(phi) * sy + ct * sz
        evals, evecs = torch.linalg.eigh(H)
        vecs.append(evecs[:, 0])

    accumulated = 1.0 + 0.0j
    for i in range(n_steps):
        overlap = (vecs[i].conj() @ vecs[i + 1]).item()
        accumulated *= overlap / abs(overlap)

    return -math.atan2(accumulated.imag, accumulated.real)


def sympy_solid_angle_check(theta_val):
    """Symbolic verification of the solid-angle formula."""
    theta = sp.Symbol("theta", positive=True)
    omega = 2 * sp.pi * (1 - sp.cos(theta))
    berry_exact = -omega / 2
    return float(berry_exact.subs(theta, theta_val))


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    t0 = time.time()

    # --- P1: Abelian limit (Berry phase modulo 2*pi) ---
    try:
        theta_test = math.pi / 3
        berry_exact = berry_phase_single_qubit(theta_test)
        berry_numeric = compute_berry_phase_numerically(theta_test, n_steps=1000)
        berry_sympy = sympy_solid_angle_check(theta_test)

        err_numeric = principal_angle_difference(berry_numeric, berry_exact)
        err_sympy = abs(berry_sympy - berry_exact)

        results["P1_abelian_berry_phase"] = {
            "pass": err_numeric < 0.02 and err_sympy < 1e-12,
            "theta": theta_test,
            "berry_exact": berry_exact,
            "berry_numeric": berry_numeric,
            "berry_sympy": berry_sympy,
            "error_numeric_mod_2pi": err_numeric,
            "error_sympy": err_sympy,
        }
    except Exception:
        results["P1_abelian_berry_phase"] = {"pass": False, "error": traceback.format_exc()}

    # --- P2: Non-abelian holonomy has off-diagonal elements ---
    try:
        theta_path, phi_path = circular_loop(0.7, 0.8, 0.3, 0.3, steps=320)
        U, _, g = path_ordered_transport(theta_path, phi_path)

        off_diag_norm = (torch.abs(U[0, 1]) + torch.abs(U[1, 0])).item()
        is_unitary = torch.allclose(U @ U.conj().T, torch.eye(g, dtype=torch.complex128), atol=1e-10)
        det_U = torch.linalg.det(U)
        det_is_one = abs(det_U.item() - 1.0) < 1e-9

        results["P2_nonabelian_offdiag"] = {
            "pass": g == 2 and off_diag_norm > 0.3 and is_unitary and det_is_one,
            "holonomy_real": U.real.tolist(),
            "holonomy_imag": U.imag.tolist(),
            "off_diagonal_norm": off_diag_norm,
            "is_unitary": is_unitary,
            "det_real": det_U.real.item(),
            "det_imag": det_U.imag.item(),
            "degeneracy": g,
        }
    except Exception:
        results["P2_nonabelian_offdiag"] = {"pass": False, "error": traceback.format_exc()}

    # --- P3: Path ordering matters ---
    try:
        th_test = 0.7
        ph_test = 0.5
        A_th, A_ph, _ = compute_connection(th_test, ph_test)
        commutator = A_th @ A_ph - A_ph @ A_th
        comm_norm = torch.norm(commutator).item()

        theta_fwd, phi_fwd = rectangular_loop(0.5, 0.8, 0.2, 0.8)
        U_fwd, _, _ = path_ordered_transport(theta_fwd, phi_fwd)

        theta_rev, phi_rev = rectangular_loop(0.5, 0.8, 0.2, 0.8)
        # Swap edge ordering.
        theta_rev = [0.5, 0.5, 0.8, 0.8, 0.5]
        phi_rev = [0.2, 0.8, 0.8, 0.2, 0.2]
        U_rev, _, _ = path_ordered_transport(theta_rev, phi_rev)

        diff_norm = torch.norm(U_fwd - U_rev).item()

        results["P3_path_ordering_matters"] = {
            "pass": comm_norm > 0.1 and diff_norm > 0.1,
            "commutator_norm": comm_norm,
            "fwd_rev_diff_norm": diff_norm,
            "A_theta_real": A_th.real.tolist(),
            "A_theta_imag": A_th.imag.tolist(),
            "A_phi_real": A_ph.real.tolist(),
            "A_phi_imag": A_ph.imag.tolist(),
        }
    except Exception:
        results["P3_path_ordering_matters"] = {"pass": False, "error": traceback.format_exc()}

    # --- P4: Holonomy lies in SU(2) ---
    try:
        theta_path, phi_path = circular_loop(0.7, 0.8, 0.3, 0.3, steps=320)
        U, _, g = path_ordered_transport(theta_path, phi_path)
        is_unitary = torch.allclose(U @ U.conj().T, torch.eye(g, dtype=torch.complex128), atol=1e-10)
        det_val = torch.linalg.det(U)
        det_is_plus_one = abs(det_val.item() - 1.0) < 1e-9

        results["P4_su2_holonomy"] = {
            "pass": is_unitary and det_is_plus_one,
            "is_unitary": is_unitary,
            "det_real": det_val.real.item(),
            "det_imag": det_val.imag.item(),
            "half_trace_real": (torch.trace(U) / 2.0).real.item(),
        }
    except Exception:
        results["P4_su2_holonomy"] = {"pass": False, "error": traceback.format_exc()}

    # --- P5: Loop size changes the holonomy ---
    try:
        radii = [0.1, 0.2, 0.3, 0.4]
        traces = []
        off_diags = []
        for radius in radii:
            theta_path, phi_path = circular_loop(0.7, 0.8, radius, radius, steps=360)
            U, _, _ = path_ordered_transport(theta_path, phi_path)
            traces.append(torch.trace(U).real.item())
            off_diags.append((torch.abs(U[0, 1]) + torch.abs(U[1, 0])).item())

        is_monotone = all(off_diags[i] < off_diags[i + 1] for i in range(len(off_diags) - 1))
        results["P5_solid_angle_dependence"] = {
            "pass": (max(traces) - min(traces)) > 0.15 and is_monotone,
            "loop_radii": radii,
            "holonomy_traces": traces,
            "off_diagonal_norms": off_diags,
            "trace_spread": max(traces) - min(traces),
            "off_diag_monotone": is_monotone,
        }
    except Exception:
        results["P5_solid_angle_dependence"] = {"pass": False, "error": traceback.format_exc()}

    # --- P6: Autograd through the parameterised Hamiltonian ---
    try:
        phi_param = torch.tensor(0.4, dtype=torch.float64, requires_grad=True)
        H = build_hamiltonian(0.7, phi_param)
        loss = H[0, 2].real
        loss.backward()
        grad_val = phi_param.grad.item()

        results["P6_autograd"] = {
            "pass": abs(grad_val) > 1e-6,
            "grad_value": grad_val,
        }
    except Exception:
        results["P6_autograd"] = {"pass": False, "error": traceback.format_exc()}

    results["elapsed_s"] = time.time() - t0
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    t0 = time.time()

    # --- N1: Trivial loop -> identity holonomy ---
    try:
        theta_path = [0.7, 0.7]
        phi_path = [0.8, 0.8]
        U, _, g = path_ordered_transport(theta_path, phi_path)
        diff_from_identity = torch.norm(U - torch.eye(g, dtype=torch.complex128)).item()

        results["N1_trivial_loop"] = {
            "pass": diff_from_identity < 1e-12,
            "diff_from_identity": diff_from_identity,
        }
    except Exception:
        results["N1_trivial_loop"] = {"pass": False, "error": traceback.format_exc()}

    # --- N2: Broken degeneracy -> transport no longer has a doublet ---
    try:
        delta = 0.3
        H = build_hamiltonian(0.7, 0.4, delta=delta)
        evals, _ = torch.linalg.eigh(H)
        gaps = [(evals[i + 1] - evals[i]).item() for i in range(len(evals) - 1)]
        split_gap = abs((evals[1] - evals[0]).item())

        results["N2_broken_degeneracy"] = {
            "pass": split_gap > 0.2,
            "eigenvalues": [complex(x.item()) for x in evals],
            "gaps": gaps,
            "doublet_split_gap": split_gap,
        }
    except Exception:
        results["N2_broken_degeneracy"] = {"pass": False, "error": traceback.format_exc()}

    # --- N3: Commuting surrogate -> path ordering becomes irrelevant ---
    try:
        A_th, A_ph, _ = compute_commuting_connection(0.7, 0.5)
        comm_norm = torch.norm(A_th @ A_ph - A_ph @ A_th).item()

        dtheta = 0.3
        dphi = 0.4
        U_theta = torch.matrix_exp(A_th * dtheta)
        U_phi = torch.matrix_exp(A_ph * dphi)
        order_diff = torch.norm(U_theta @ U_phi - U_phi @ U_theta).item()

        results["N3_commuting_surrogate"] = {
            "pass": comm_norm < 1e-12 and order_diff < 1e-12,
            "commutator_norm": comm_norm,
            "order_diff_norm": order_diff,
        }
    except Exception:
        results["N3_commuting_surrogate"] = {"pass": False, "error": traceback.format_exc()}

    results["elapsed_s"] = time.time() - t0
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    t0 = time.time()

    # --- B1: Small loops stay near identity ---
    try:
        epsilons = [0.02, 0.05, 0.1, 0.2]
        deviations = []

        for eps in epsilons:
            theta_path, phi_path = circular_loop(0.7, 0.8, eps, eps, steps=240)
            U, _, g = path_ordered_transport(theta_path, phi_path)
            deviations.append(torch.norm(U - torch.eye(g, dtype=torch.complex128)).item())

        is_monotone = all(deviations[i] < deviations[i + 1] for i in range(len(deviations) - 1))
        results["B1_small_loop_linear"] = {
            "pass": is_monotone and deviations[0] < 0.01,
            "epsilons": epsilons,
            "deviations": deviations,
            "is_monotone": is_monotone,
        }
    except Exception:
        results["B1_small_loop_linear"] = {"pass": False, "error": traceback.format_exc()}

    # --- B2: Fixed-latitude 2*pi loop -> strong diagonal SU(2) holonomy ---
    try:
        steps = 360
        phi_path = np.linspace(0.0, 2.0 * np.pi, steps + 1).tolist()
        theta_path = [math.pi / 2] * (steps + 1)
        U, _, _ = path_ordered_transport(theta_path, phi_path)
        trace_val = torch.trace(U).real.item()
        off_diag = (torch.abs(U[0, 1]) + torch.abs(U[1, 0])).item()

        results["B2_fixed_latitude_loop"] = {
            "pass": abs(trace_val + 2.0) < 1e-6 and off_diag < 1e-6,
            "holonomy_trace": trace_val,
            "off_diagonal_magnitude": off_diag,
            "holonomy_real": U.real.tolist(),
            "holonomy_imag": U.imag.tolist(),
        }
    except Exception:
        results["B2_fixed_latitude_loop"] = {"pass": False, "error": traceback.format_exc()}

    # --- B3: Step count convergence on a nontrivial loop ---
    try:
        step_counts = [50, 100, 200, 400]
        traces = []

        for steps in step_counts:
            theta_path, phi_path = circular_loop(0.7, 0.8, 0.3, 0.3, steps=steps)
            U, _, _ = path_ordered_transport(theta_path, phi_path)
            traces.append(torch.trace(U).real.item())

        diffs = [abs(traces[i + 1] - traces[i]) for i in range(len(traces) - 1)]
        is_converging = diffs[-1] < diffs[0]

        results["B3_step_convergence"] = {
            "pass": is_converging,
            "step_counts": step_counts,
            "holonomy_traces": traces,
            "successive_diffs": diffs,
        }
    except Exception:
        results["B3_step_convergence"] = {"pass": False, "error": traceback.format_exc()}

    results["elapsed_s"] = time.time() - t0
    return results


def build_summary(results):
    total = 0
    passed = 0
    failed_tests = []

    for section in ["positive", "negative", "boundary"]:
        for test_name, payload in results[section].items():
            if test_name == "elapsed_s":
                continue
            total += 1
            if payload.get("pass", False):
                passed += 1
            else:
                failed_tests.append(test_name)

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "failed_tests": failed_tests,
    }


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Wilczek-Zee Non-Abelian Geometric Phase")
    print("=" * 60)

    results = {
        "name": "Wilczek-Zee Non-Abelian Geometric Phase",
        "probe": "lego_wilczek_zee",
        "purpose": "Verify non-abelian holonomy for a transported two-dimensional degenerate eigenspace",
        "tool_manifest": TOOL_MANIFEST,
        "tools_used": collect_tools_used(),
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    results["summary"] = build_summary(results)

    for section in ["positive", "negative", "boundary"]:
        for key, value in results[section].items():
            if key == "elapsed_s":
                continue
            print(f"  {'PASS' if value.get('pass', False) else 'FAIL'}  {key}")

    print(
        f"\n{results['summary']['passed']}/{results['summary']['total']} tests passed"
    )

    out_dir = os.path.join(os.path.dirname(__file__), "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_wilczek_zee_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
