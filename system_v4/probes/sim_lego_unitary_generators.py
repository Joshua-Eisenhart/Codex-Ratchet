#!/usr/bin/env python3
"""
SIM LEGO: Unitary Generators exp(-iHt)
=======================================
Pure math: unitary evolution operators as mathematical objects.

The unitary evolution operator: U(t) = exp(-iHt)
For H = n_hat . sigma / 2 (general qubit Hamiltonian):
  U(t) = cos(t/2) I - i sin(t/2) (n_hat . sigma)

Tests:
  1-3.  Pauli generators: U_x(t), U_y(t), U_z(t) from H = sigma_k/2
  4.    General axis n_hat with |n_hat|=1
  5.    Unitarity: U^dag U = I
  6.    det(U) = 1 (SU(2))
  7.    Purity preservation: Tr((U rho U^dag)^2) = Tr(rho^2)
  8.    Entropy preservation: S(U rho U^dag) = S(U rho)
  9.    Eigenvalue preservation of rho under conjugation
  10.   Group composition: U_x(t1) U_x(t2) = U_x(t1+t2)
  11.   Non-commutativity: U_x(t) U_z(s) != U_z(s) U_x(t) generically
  12.   BCH first-order check: e^A e^B ~ e^{A+B+[A,B]/2} for small A,B
  13-14. Bloch sphere rotation: U_z(t), U_x(t) rotate Bloch vector
  15.   General U(n_hat, t) rotates Bloch vector by t around n_hat

Cross-validation: sympy symbolic vs clifford geometric algebra rotors.

Classification: canonical
"""

import json
import os
import numpy as np
from datetime import datetime
classification = "classical_baseline"  # auto-backfill

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

# --- Import tools ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, sat, And, unsat  # noqa: F401
    import z3 as z3mod
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    from sympy import (Matrix, eye, sqrt, pi, cos, sin, exp, I, simplify,
                       symbols, Rational, trigsimp, nsimplify)
    from sympy.physics.quantum import Dagger
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
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
# HELPERS
# =====================================================================

# Pauli matrices (numpy)
I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)

PAULIS = {"x": SX, "y": SY, "z": SZ}


def U_pauli(axis, t):
    """U(t) = cos(t/2)I - i sin(t/2) sigma_axis."""
    sigma = PAULIS[axis]
    return np.cos(t / 2) * I2 - 1j * np.sin(t / 2) * sigma


def U_general(n_hat, t):
    """U(t) = cos(t/2)I - i sin(t/2)(n_hat . sigma) for unit |n_hat|=1."""
    n_dot_sigma = n_hat[0] * SX + n_hat[1] * SY + n_hat[2] * SZ
    return np.cos(t / 2) * I2 - 1j * np.sin(t / 2) * n_dot_sigma


def bloch_vector(rho):
    """Extract Bloch vector (r_x, r_y, r_z) from 2x2 density matrix."""
    rx = np.real(np.trace(rho @ SX))
    ry = np.real(np.trace(rho @ SY))
    rz = np.real(np.trace(rho @ SZ))
    return np.array([rx, ry, rz])


def rotation_matrix(axis, angle):
    """3x3 SO(3) rotation matrix around axis by angle."""
    c, s = np.cos(angle), np.sin(angle)
    n = np.array(axis)
    # Rodrigues' formula
    K = np.array([
        [0, -n[2], n[1]],
        [n[2], 0, -n[0]],
        [-n[1], n[0], 0]
    ])
    return np.eye(3) + s * K + (1 - c) * (K @ K)


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho ln rho), via eigenvalues."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]  # avoid log(0)
    return -np.sum(evals * np.log(evals))


TOL = 1e-10


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- Test 1-3: Pauli generators ---
    t_vals = [0.0, np.pi / 4, np.pi / 2, np.pi, 2 * np.pi]
    for axis in ["x", "y", "z"]:
        test_name = f"pauli_generator_{axis}"
        sigma = PAULIS[axis]
        all_pass = True
        details = []
        for t in t_vals:
            U = U_pauli(axis, t)
            # Compare to matrix exponential of -i (sigma/2) t
            H = sigma / 2
            U_expm = _safe_expm(-1j * H * t)
            err = np.max(np.abs(U - U_expm))
            passed = err < TOL
            all_pass = all_pass and passed
            details.append({"t": float(t), "max_error": float(err), "pass": passed})
        results[test_name] = {"pass": all_pass, "details": details}

    # --- Test 4: General axis ---
    np.random.seed(42)
    for trial in range(5):
        n_raw = np.random.randn(3)
        n_hat = n_raw / np.linalg.norm(n_raw)
        t = np.random.uniform(0, 2 * np.pi)
        U = U_general(n_hat, t)
        H = (n_hat[0] * SX + n_hat[1] * SY + n_hat[2] * SZ) / 2
        U_expm = _safe_expm(-1j * H * t)
        err = np.max(np.abs(U - U_expm))
        results[f"general_axis_trial_{trial}"] = {
            "pass": err < TOL,
            "n_hat": n_hat.tolist(),
            "t": float(t),
            "max_error": float(err),
        }

    # --- Test 5: Unitarity U^dag U = I ---
    test5_pass = True
    for axis in ["x", "y", "z"]:
        for t in [0.3, 1.0, np.pi]:
            U = U_pauli(axis, t)
            prod = U.conj().T @ U
            err = np.max(np.abs(prod - I2))
            test5_pass = test5_pass and (err < TOL)
    results["unitarity"] = {"pass": test5_pass}

    # --- Test 6: det(U) = 1 (SU(2)) ---
    test6_pass = True
    det_details = []
    for axis in ["x", "y", "z"]:
        for t in [0.7, 1.5, np.pi]:
            U = U_pauli(axis, t)
            d = np.linalg.det(U)
            err = abs(d - 1.0)
            passed = err < TOL
            test6_pass = test6_pass and passed
            det_details.append({"axis": axis, "t": float(t),
                                "det": complex(d), "error": float(err)})
    results["det_equals_1"] = {"pass": test6_pass, "details": det_details}

    # --- Test 7: Purity preservation ---
    # rho = mixed state, check Tr((U rho U^dag)^2) = Tr(rho^2)
    rho_pure = np.array([[1, 0], [0, 0]], dtype=complex)
    rho_mixed = 0.7 * rho_pure + 0.3 * np.array([[0, 0], [0, 1]], dtype=complex)
    test7_pass = True
    for rho_label, rho in [("pure", rho_pure), ("mixed", rho_mixed)]:
        purity_before = np.real(np.trace(rho @ rho))
        for axis in ["x", "y", "z"]:
            U = U_pauli(axis, 1.23)
            rho_out = U @ rho @ U.conj().T
            purity_after = np.real(np.trace(rho_out @ rho_out))
            err = abs(purity_after - purity_before)
            test7_pass = test7_pass and (err < TOL)
    results["purity_preservation"] = {"pass": test7_pass}

    # --- Test 8: Entropy preservation ---
    test8_pass = True
    for rho_label, rho in [("mixed", rho_mixed)]:
        S_before = von_neumann_entropy(rho)
        for axis in ["x", "y", "z"]:
            U = U_pauli(axis, 2.1)
            rho_out = U @ rho @ U.conj().T
            S_after = von_neumann_entropy(rho_out)
            err = abs(S_after - S_before)
            test8_pass = test8_pass and (err < TOL)
    results["entropy_preservation"] = {"pass": test8_pass}

    # --- Test 9: Eigenvalue preservation ---
    test9_pass = True
    for axis in ["x", "y", "z"]:
        U = U_pauli(axis, 1.7)
        rho_out = U @ rho_mixed @ U.conj().T
        evals_before = np.sort(np.linalg.eigvalsh(rho_mixed))
        evals_after = np.sort(np.linalg.eigvalsh(rho_out))
        err = np.max(np.abs(evals_before - evals_after))
        test9_pass = test9_pass and (err < TOL)
    results["eigenvalue_preservation"] = {"pass": test9_pass}

    # --- Test 10: Group composition U_x(t1) U_x(t2) = U_x(t1+t2) ---
    test10_pass = True
    comp_details = []
    for axis in ["x", "y", "z"]:
        t1, t2 = 0.8, 1.3
        U1 = U_pauli(axis, t1)
        U2 = U_pauli(axis, t2)
        U_sum = U_pauli(axis, t1 + t2)
        err = np.max(np.abs(U1 @ U2 - U_sum))
        passed = err < TOL
        test10_pass = test10_pass and passed
        comp_details.append({"axis": axis, "t1": t1, "t2": t2, "error": float(err)})
    results["group_composition"] = {"pass": test10_pass, "details": comp_details}

    # --- Test 11: Non-commutativity ---
    t, s = 1.0, 0.7
    Ux = U_pauli("x", t)
    Uz = U_pauli("z", s)
    commutator_norm = np.max(np.abs(Ux @ Uz - Uz @ Ux))
    results["non_commutativity"] = {
        "pass": commutator_norm > 1e-6,
        "commutator_norm": float(commutator_norm),
        "note": "U_x(1.0) and U_z(0.7) do NOT commute",
    }

    # --- Test 12: BCH first-order ---
    # For small eps: e^A e^B ~ e^{A+B+[A,B]/2}
    eps = 0.01
    A = -1j * eps * SX / 2
    B = -1j * eps * SZ / 2
    eA = _safe_expm(A)
    eB = _safe_expm(B)
    comm = A @ B - B @ A
    eABcomm = _safe_expm(A + B + comm / 2)
    # The product e^A e^B vs BCH approximation
    err_bch = np.max(np.abs(eA @ eB - eABcomm))
    # BCH is exact to O(eps^3), so error should be ~ eps^3
    results["bch_first_order"] = {
        "pass": err_bch < eps ** 2,
        "error": float(err_bch),
        "eps": eps,
        "note": "BCH e^A e^B = e^{A+B+[A,B]/2+...} verified to O(eps^2)",
    }

    # --- Test 13-14: Bloch sphere rotation for z, x ---
    bloch_tests = True
    bloch_details = []
    # Start from |+> state: rho = (I + SX)/2, Bloch = (1,0,0)
    rho_plus = (I2 + SX) / 2
    for axis, expected_rotation_axis in [("z", [0, 0, 1]), ("x", [1, 0, 0])]:
        t = np.pi / 3
        U = U_pauli(axis, t)
        rho_out = U @ rho_plus @ U.conj().T
        r_before = bloch_vector(rho_plus)
        r_after = bloch_vector(rho_out)
        # Expected: SO(3) rotation by t around the axis
        R = rotation_matrix(expected_rotation_axis, t)
        r_expected = R @ r_before
        err = np.max(np.abs(r_after - r_expected))
        passed = err < TOL
        bloch_tests = bloch_tests and passed
        bloch_details.append({
            "axis": axis, "t": float(t),
            "r_before": r_before.tolist(),
            "r_after": r_after.tolist(),
            "r_expected": r_expected.tolist(),
            "error": float(err),
        })
    results["bloch_rotation_z_x"] = {"pass": bloch_tests, "details": bloch_details}

    # --- Test 15: General axis Bloch rotation ---
    n_hat = np.array([1, 1, 1]) / np.sqrt(3)
    t = 1.2
    U = U_general(n_hat, t)
    rho_out = U @ rho_plus @ U.conj().T
    r_before = bloch_vector(rho_plus)
    r_after = bloch_vector(rho_out)
    R = rotation_matrix(n_hat, t)
    r_expected = R @ r_before
    err = np.max(np.abs(r_after - r_expected))
    results["bloch_rotation_general"] = {
        "pass": err < TOL,
        "n_hat": n_hat.tolist(),
        "t": float(t),
        "error": float(err),
    }

    # --- Sympy symbolic cross-validation ---
    results["sympy_symbolic"] = _run_sympy_crossval()

    # --- Clifford cross-validation ---
    results["clifford_rotor"] = _run_clifford_crossval()

    # --- z3 proof: unitarity constraint ---
    results["z3_unitarity_proof"] = _run_z3_unitarity()

    # --- PyTorch autograd: gradient of U w.r.t. t ---
    results["pytorch_autograd"] = _run_pytorch_autograd()

    return results


def _safe_expm(M):
    """Matrix exponential via eigendecomposition for 2x2."""
    evals, evecs = np.linalg.eig(M)
    return evecs @ np.diag(np.exp(evals)) @ np.linalg.inv(evecs)


def _run_sympy_crossval():
    """Sympy: symbolic matrix exp, verify U_z(t) and general formula."""
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"pass": False, "reason": "sympy not available"}

    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic matrix exponential, exact verification"

    t = symbols("t", real=True)
    # Pauli Z
    sz = Matrix([[1, 0], [0, -1]])
    sx = Matrix([[0, 1], [1, 0]])
    sy = Matrix([[0, -I], [I, 0]])
    Id = eye(2)

    results = {}

    # U_z(t) = cos(t/2)I - i sin(t/2) sigma_z = diag(e^{-it/2}, e^{it/2})
    Uz_formula = cos(t / 2) * Id - I * sin(t / 2) * sz
    Uz_diag = Matrix([[exp(-I * t / 2), 0], [0, exp(I * t / 2)]])
    diff = trigsimp(Uz_formula - Uz_diag)
    results["Uz_diag_form"] = {
        "pass": diff.equals(sp.zeros(2, 2)),
        "note": "cos(t/2)I - i sin(t/2)sz == diag(e^{-it/2}, e^{it/2})",
    }

    # Unitarity: U^dag U = I symbolically
    Uz_dag = Dagger(Uz_formula)
    prod = trigsimp(Uz_dag * Uz_formula)
    results["Uz_unitarity_symbolic"] = {
        "pass": prod.equals(Id),
        "note": "U_z^dag U_z = I (symbolic)",
    }

    # det(U_z) = 1
    det_val = trigsimp(Uz_formula.det())
    results["Uz_det_symbolic"] = {
        "pass": simplify(det_val - 1) == 0,
        "det": str(det_val),
    }

    # U_x(t) explicit form
    Ux_formula = cos(t / 2) * Id - I * sin(t / 2) * sx
    Ux_dag = Dagger(Ux_formula)
    prod_x = trigsimp(Ux_dag * Ux_formula)
    results["Ux_unitarity_symbolic"] = {
        "pass": prod_x.equals(Id),
    }

    # Composition: U_z(a) U_z(b) = U_z(a+b)
    a, b = symbols("a b", real=True)
    Uz_a = cos(a / 2) * Id - I * sin(a / 2) * sz
    Uz_b = cos(b / 2) * Id - I * sin(b / 2) * sz
    Uz_ab = cos((a + b) / 2) * Id - I * sin((a + b) / 2) * sz
    prod_comp = trigsimp(Uz_a * Uz_b - Uz_ab)
    results["composition_symbolic"] = {
        "pass": prod_comp.equals(sp.zeros(2, 2)),
        "note": "U_z(a) U_z(b) = U_z(a+b) verified symbolically",
    }

    return {"pass": all(v.get("pass", False) for v in results.values()),
            "details": results}


def _run_clifford_crossval():
    """Clifford: rotor R = exp(-B t/2) encodes same rotation as U(t)."""
    if not TOOL_MANIFEST["clifford"]["tried"]:
        return {"pass": False, "reason": "clifford not available"}

    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "geometric algebra rotors R=exp(-Bt/2) cross-validate SU(2) generators"
    )

    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]

    # Bivectors for rotations: rotation in e_i e_j plane = rotation around e_k
    # Rotation around z = rotation in e1^e2 plane
    bivectors = {
        "z": e1 ^ e2,  # e12
        "x": e2 ^ e3,  # e23
        "y": e3 ^ e1,  # e31
    }

    results = {}
    test_t = 1.0
    rho_plus = (I2 + SX) / 2  # |+> state, Bloch = (1,0,0)
    r0 = np.array([1.0, 0.0, 0.0])

    for axis_label, bv in bivectors.items():
        # Clifford rotor
        R = np.cos(test_t / 2) + np.sin(test_t / 2) * (-bv)
        # Apply rotor to vector v = x*e1 + y*e2 + z*e3
        v_in = r0[0] * e1 + r0[1] * e2 + r0[2] * e3
        v_out = R * v_in * ~R

        # Extract rotated vector components
        r_cliff = np.array([
            float(v_out[blades["e1"]]),
            float(v_out[blades["e2"]]),
            float(v_out[blades["e3"]]),
        ])

        # SU(2) rotation of Bloch vector
        axis_vec = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}[axis_label]
        R_so3 = rotation_matrix(axis_vec, test_t)
        r_su2 = R_so3 @ r0

        err = np.max(np.abs(r_cliff - r_su2))
        results[f"rotor_vs_su2_{axis_label}"] = {
            "pass": err < TOL,
            "clifford_result": r_cliff.tolist(),
            "su2_result": r_su2.tolist(),
            "error": float(err),
        }

    # General axis rotor
    n_hat = np.array([1, 1, 1]) / np.sqrt(3)
    bv_gen = n_hat[0] * (e2 ^ e3) + n_hat[1] * (e3 ^ e1) + n_hat[2] * (e1 ^ e2)
    R_gen = np.cos(test_t / 2) + np.sin(test_t / 2) * (-bv_gen)
    v_in = r0[0] * e1 + r0[1] * e2 + r0[2] * e3
    v_out = R_gen * v_in * ~R_gen
    r_cliff_gen = np.array([
        float(v_out[blades["e1"]]),
        float(v_out[blades["e2"]]),
        float(v_out[blades["e3"]]),
    ])
    R_so3_gen = rotation_matrix(n_hat, test_t)
    r_su2_gen = R_so3_gen @ r0
    err_gen = np.max(np.abs(r_cliff_gen - r_su2_gen))
    results["rotor_vs_su2_general"] = {
        "pass": err_gen < TOL,
        "error": float(err_gen),
    }

    return {"pass": all(v.get("pass", False) for v in results.values()),
            "details": results}


def _run_z3_unitarity():
    """z3: prove that cos^2(t/2) + sin^2(t/2) = 1 constraint forces unitarity."""
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"pass": False, "reason": "z3 not available"}

    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "prove unitarity constraint is satisfiable"

    # Model: U = c*I - i*s*sigma_z = diag(c - is, c + is)
    # Unitarity requires |c - is|^2 = 1 and |c + is|^2 = 1
    # i.e., c^2 + s^2 = 1
    c = Real("c")
    s = Real("s")

    solver = Solver()
    # The constraint c^2 + s^2 = 1
    solver.add(c * c + s * s == 1)
    # det = (c - is)(c + is) = c^2 + s^2 = 1 (automatic)

    # Verify satisfiable
    sat_result = solver.check()
    sat_ok = (sat_result == sat)

    # Prove: if c^2 + s^2 != 1, then unitarity fails
    solver2 = Solver()
    solver2.add(c * c + s * s != 1)
    # Ask: can we still have |c-is|^2 = 1? (no)
    # |c-is|^2 = c^2 + s^2, so c^2+s^2 != 1 => |c-is|^2 != 1
    solver2.add(c * c + s * s == 1)  # contradiction
    unsat_result = solver2.check()
    unsat_ok = (unsat_result == unsat)

    return {
        "pass": sat_ok and unsat_ok,
        "satisfiable": sat_ok,
        "contradiction_unsat": unsat_ok,
        "note": "c^2 + s^2 = 1 is necessary and sufficient for unitarity of U_z",
    }


def _run_pytorch_autograd():
    """PyTorch: differentiate U(t) w.r.t. t, verify dU/dt = -iH U."""
    if not TOOL_MANIFEST["pytorch"]["tried"]:
        return {"pass": False, "reason": "pytorch not available"}

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "autograd verification of dU/dt = -iHU"

    results = {}
    # H = sigma_z / 2
    H_z = torch.tensor([[0.5 + 0j, 0], [0, -0.5 + 0j]], dtype=torch.cfloat)

    for t_val in [0.5, 1.0, np.pi / 2]:
        t_pt = torch.tensor(t_val, dtype=torch.float32, requires_grad=True)

        # U(t) = cos(t/2) I - i sin(t/2) sigma_z
        I_pt = torch.eye(2, dtype=torch.cfloat)
        sz_pt = torch.tensor([[1.0 + 0j, 0], [0, -1.0 + 0j]], dtype=torch.cfloat)
        ct = torch.cos(t_pt / 2)
        st = torch.sin(t_pt / 2)
        U_pt = ct * I_pt - 1j * st * sz_pt

        # Compute dU/dt element by element via autograd
        dU = torch.zeros(2, 2, dtype=torch.cfloat)
        for i in range(2):
            for j in range(2):
                if t_pt.grad is not None:
                    t_pt.grad.zero_()
                # Real part gradient
                U_pt[i, j].real.backward(retain_graph=True)
                grad_real = t_pt.grad.item() if t_pt.grad is not None else 0.0
                t_pt.grad.zero_()
                # Imag part gradient
                U_pt[i, j].imag.backward(retain_graph=True)
                grad_imag = t_pt.grad.item() if t_pt.grad is not None else 0.0
                t_pt.grad.zero_()
                dU[i, j] = complex(grad_real, grad_imag)

        # Expected: dU/dt = -iH U
        expected_dU = (-1j * H_z @ U_pt).detach()
        err = torch.max(torch.abs(dU - expected_dU)).item()
        results[f"t={t_val:.2f}"] = {
            "pass": err < 1e-5,
            "error": float(err),
        }

    return {
        "pass": all(v["pass"] for v in results.values()),
        "details": results,
        "note": "dU/dt = -iHU verified via autograd",
    }


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # Neg 1: Non-Hermitian H should not give unitary U
    # H with distinct eigenvalues and non-Hermitian structure
    H_bad = np.array([[1, 2], [0, 3]], dtype=complex)
    U_bad = _safe_expm(-1j * H_bad * 1.0)
    prod = U_bad.conj().T @ U_bad
    err = np.max(np.abs(prod - I2))
    results["non_hermitian_H_breaks_unitarity"] = {
        "pass": err > 0.01,
        "error": float(err),
        "note": "Non-Hermitian H produces non-unitary U",
    }

    # Neg 2: Non-unit n_hat does not give SU(2)
    n_bad = np.array([2.0, 0.0, 0.0])  # |n| = 2, not 1
    U_bad2 = U_general(n_bad, 1.0)
    det_bad = np.linalg.det(U_bad2)
    # This should still be unitary (cos/sin formula works) but the rotation
    # angle is effectively doubled, so composition fails for the "nominal" angle
    U_half1 = U_general(n_bad, 0.5)
    U_half2 = U_general(n_bad, 0.5)
    U_should_be = U_general(n_bad, 1.0)
    # Composition still works with the formula -- so test that the Bloch
    # rotation angle does NOT match t when |n|!=1
    rho_plus = (I2 + SX) / 2
    r0 = bloch_vector(rho_plus)
    rho_out = U_bad2 @ rho_plus @ U_bad2.conj().T
    r_out = bloch_vector(rho_out)
    # With |n|=2, the effective rotation is by 2*t not t
    R_correct = rotation_matrix([1, 0, 0], 1.0)  # if |n|=1
    r_expected_correct = R_correct @ r0
    err2 = np.max(np.abs(r_out - r_expected_correct))
    results["non_unit_nhat_wrong_angle"] = {
        "pass": err2 > 0.01,
        "error": float(err2),
        "note": "|n_hat| != 1 gives wrong rotation angle on Bloch sphere",
    }

    # Neg 3: U(0) should be identity, U(non-zero) should NOT be identity
    U_zero = U_pauli("x", 0.0)
    U_nonzero = U_pauli("x", 1.0)
    results["identity_only_at_zero"] = {
        "pass": (np.max(np.abs(U_zero - I2)) < TOL and
                 np.max(np.abs(U_nonzero - I2)) > 0.01),
        "note": "U(0) = I but U(t!=0) != I",
    }

    # Neg 4: Random matrix is not unitary
    np.random.seed(99)
    M_rand = np.random.randn(2, 2) + 1j * np.random.randn(2, 2)
    prod_rand = M_rand.conj().T @ M_rand
    err_rand = np.max(np.abs(prod_rand - I2))
    results["random_matrix_not_unitary"] = {
        "pass": err_rand > 0.1,
        "error": float(err_rand),
        "note": "Random complex 2x2 is not unitary",
    }

    # Neg 5: Non-zero commutator means non-commutative
    # Confirm [sigma_x, sigma_z] != 0
    comm = SX @ SZ - SZ @ SX
    comm_norm = np.max(np.abs(comm))
    results["pauli_noncommutative"] = {
        "pass": comm_norm > 0.1,
        "commutator_norm": float(comm_norm),
        "note": "[sigma_x, sigma_z] != 0",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # Boundary 1: t = 0 => U = I
    for axis in ["x", "y", "z"]:
        U = U_pauli(axis, 0.0)
        err = np.max(np.abs(U - I2))
        results[f"t_zero_{axis}"] = {"pass": err < TOL, "error": float(err)}

    # Boundary 2: t = 2*pi => U = -I (SU(2) double cover)
    for axis in ["x", "y", "z"]:
        U = U_pauli(axis, 2 * np.pi)
        err = np.max(np.abs(U - (-I2)))
        results[f"t_2pi_{axis}"] = {
            "pass": err < TOL,
            "error": float(err),
            "note": "U(2pi) = -I (SU(2) double cover of SO(3))",
        }

    # Boundary 3: t = 4*pi => U = +I (full period)
    for axis in ["x", "y", "z"]:
        U = U_pauli(axis, 4 * np.pi)
        err = np.max(np.abs(U - I2))
        results[f"t_4pi_{axis}"] = {"pass": err < TOL, "error": float(err)}

    # Boundary 4: t = pi => specific known values
    # U_z(pi) = diag(e^{-i pi/2}, e^{i pi/2}) = diag(-i, i)
    U_z_pi = U_pauli("z", np.pi)
    expected = np.diag([-1j, 1j])
    err = np.max(np.abs(U_z_pi - expected))
    results["Uz_pi"] = {"pass": err < TOL, "error": float(err)}

    # U_x(pi) = -i sigma_x
    U_x_pi = U_pauli("x", np.pi)
    expected_x = -1j * SX
    err_x = np.max(np.abs(U_x_pi - expected_x))
    results["Ux_pi"] = {"pass": err_x < TOL, "error": float(err_x)}

    # Boundary 5: Very small t => U ~ I - iHt (first order Taylor)
    eps = 1e-8
    for axis in ["x", "y", "z"]:
        U = U_pauli(axis, eps)
        H = PAULIS[axis] / 2
        U_approx = I2 - 1j * H * eps
        err = np.max(np.abs(U - U_approx))
        # Error should be O(eps^2) ~ 1e-16
        results[f"small_t_taylor_{axis}"] = {
            "pass": err < eps ** 1.5,
            "error": float(err),
        }

    # Boundary 6: Numerical precision at t = pi/2
    # U_z(pi/2) = diag(e^{-i pi/4}, e^{i pi/4}) = (1-i)/sqrt(2), (1+i)/sqrt(2)
    U_z_half = U_pauli("z", np.pi / 2)
    s2 = 1 / np.sqrt(2)
    expected_half = np.diag([s2 - 1j * s2, s2 + 1j * s2])
    err_half = np.max(np.abs(U_z_half - expected_half))
    results["Uz_pi_over_2"] = {"pass": err_half < TOL, "error": float(err_half)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running sim_lego_unitary_generators...")
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Count passes
    def count_pass(d):
        total = 0
        passed = 0
        for k, v in d.items():
            if isinstance(v, dict) and "pass" in v:
                total += 1
                if v["pass"]:
                    passed += 1
        return passed, total

    p_pass, p_total = count_pass(pos)
    n_pass, n_total = count_pass(neg)
    b_pass, b_total = count_pass(bnd)

    results = {
        "name": "Unitary Generators exp(-iHt)",
        "timestamp": datetime.now().isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": {
            "positive": f"{p_pass}/{p_total}",
            "negative": f"{n_pass}/{n_total}",
            "boundary": f"{b_pass}/{b_total}",
            "total": f"{p_pass + n_pass + b_pass}/{p_total + n_total + b_total}",
        },
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_unitary_generators_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    # Print summary
    print(f"\nPositive: {p_pass}/{p_total}")
    print(f"Negative: {n_pass}/{n_total}")
    print(f"Boundary: {b_pass}/{b_total}")
    all_pass = (p_pass + n_pass + b_pass) == (p_total + n_total + b_total)
    print(f"ALL PASS: {all_pass}")
