#!/usr/bin/env python3
"""
PURE LEGO: Lindblad Dissipator D[L](rho) as Mathematical Object
=================================================================
The dissipator superoperator:
  D[L](rho) = L rho L^dag - 1/2 (L^dag L rho + rho L^dag L)

Tests every Pauli matrix + sigma_pm as jump operator L:
  1-3.  D[sigma_x/y/z](rho): effect on Bloch vector for 10 states
  4-5.  D[sigma_-/+](rho): amplitude damping/pumping
  6.    Trace preservation: Tr(D[L](rho)) = 0 for all rho, all L
  7.    CPTP evolution: rho(t) = exp(t*D[L])(rho_0) >= 0, Tr=1
  8-10. Steady states: D[L](rho_ss) = 0 for each L
  11.   Spectral gap of D as 4x4 superoperator
  12.   D[sx]+D[sy]+D[sz] = depolarizing channel (verify)
  13.   Commutativity: D[sz]+D[sx] vs D[sx]+D[sz] as superoperators

Tools: sympy (symbolic), z3 (formal trace preservation proof),
       pytorch (numerical cross-validation), numpy+scipy (eigenvalues/expm).

Classification: canonical
"""

import json
import os
import time
import traceback
import numpy as np
from scipy.linalg import expm, eigvals

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

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "supporting",
    "pyg": None,
    "z3": "supporting",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

LEGO_IDS = [
    "lindbladian_evolution",
    "channel_cptp_map",
]

PRIMARY_LEGO_IDS = [
    "lindbladian_evolution",
]

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
    from z3 import (
        Reals, Real, Solver, sat, unsat, And, Or, Not, ForAll,
        Implies, RealVal, simplify, If
    )
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
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
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
# PAULI MATRICES AND HELPERS
# =====================================================================

I2 = np.eye(2, dtype=complex)
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
SIGMA_MINUS = np.array([[0, 1], [0, 0]], dtype=complex)  # |0><1|
SIGMA_PLUS = np.array([[0, 0], [1, 0]], dtype=complex)   # |1><0|

JUMP_OPS = {
    "sigma_x": SIGMA_X,
    "sigma_y": SIGMA_Y,
    "sigma_z": SIGMA_Z,
    "sigma_minus": SIGMA_MINUS,
    "sigma_plus": SIGMA_PLUS,
}


def bloch_to_rho(r):
    """Bloch vector (rx, ry, rz) -> 2x2 density matrix."""
    rx, ry, rz = r
    return 0.5 * (I2 + rx * SIGMA_X + ry * SIGMA_Y + rz * SIGMA_Z)


def rho_to_bloch(rho):
    """2x2 density matrix -> Bloch vector (rx, ry, rz)."""
    rx = np.real(np.trace(SIGMA_X @ rho))
    ry = np.real(np.trace(SIGMA_Y @ rho))
    rz = np.real(np.trace(SIGMA_Z @ rho))
    return np.array([rx, ry, rz])


def dissipator(L, rho):
    """D[L](rho) = L rho L^dag - 1/2 (L^dag L rho + rho L^dag L)."""
    Ld = L.conj().T
    LdL = Ld @ L
    return L @ rho @ Ld - 0.5 * (LdL @ rho + rho @ LdL)


def dissipator_superop(L):
    """Build 4x4 superoperator matrix for D[L] in column-stacking basis.
    vec(rho) is column-stacked: rho -> [rho_00, rho_10, rho_01, rho_11].
    D[L] vec(rho) = (L kron L*) - 1/2 (I kron L^dag L) - 1/2 (L^T L* kron I).
    """
    Ld = L.conj().T
    LdL = Ld @ L
    Lstar = L.conj()
    LT = L.T
    term1 = np.kron(L, Lstar)
    term2 = 0.5 * np.kron(I2, LdL.T)  # (I kron (L^dag L)^T) in col-stack = I kron L^T L*
    term3 = 0.5 * np.kron(LdL, I2)
    # Correct form: D = L kron L* - 1/2 (L^dag L kron I) - 1/2 (I kron (L^dag L)^T)
    # In column-stacking convention: vec(A X B) = (B^T kron A) vec(X)
    # D[L](rho) = L rho L^dag - 1/2 L^dag L rho - 1/2 rho L^dag L
    # vec(L rho L^dag) = (L^dag)^T kron L) vec(rho) = (L* kron L) vec(rho)
    # vec(L^dag L rho) = (I kron L^dag L) vec(rho)
    # vec(rho L^dag L) = ((L^dag L)^T kron I) vec(rho)
    return np.kron(Lstar, L) - 0.5 * np.kron(I2, LdL) - 0.5 * np.kron(LdL.T, I2)


def make_test_states():
    """10 test states spanning the Bloch sphere + boundary."""
    states = []
    labels = []
    # Pure states along axes
    for name, r in [
        ("|0>", [0, 0, 1]),
        ("|1>", [0, 0, -1]),
        ("|+>", [1, 0, 0]),
        ("|->", [-1, 0, 0]),
        ("|+i>", [0, 1, 0]),
        ("|-i>", [0, -1, 0]),
    ]:
        states.append(bloch_to_rho(r))
        labels.append(name)
    # Mixed states
    for name, r in [
        ("maximally_mixed", [0, 0, 0]),
        ("r=0.5_along_z", [0, 0, 0.5]),
        ("r=0.5_along_x", [0.5, 0, 0]),
        ("off_axis", [0.3, 0.4, 0.5]),
    ]:
        states.append(bloch_to_rho(r))
        labels.append(name)
    return states, labels


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    t0 = time.time()

    states, labels = make_test_states()

    # --- Tests 1-5: Bloch vector action of each dissipator ---
    for op_name, L in JUMP_OPS.items():
        test_key = f"bloch_action_{op_name}"
        entries = []
        for rho, label in zip(states, labels):
            r_in = rho_to_bloch(rho)
            d_rho = dissipator(L, rho)
            r_out = rho_to_bloch(d_rho)  # This is dr/dt direction

            # Cross-validate with superoperator
            D_sup = dissipator_superop(L)
            vec_rho = rho.flatten(order='F')
            d_vec = D_sup @ vec_rho
            d_rho_sup = d_vec.reshape(2, 2, order='F')
            r_out_sup = rho_to_bloch(d_rho_sup)
            match = np.allclose(r_out, r_out_sup, atol=1e-12)

            entries.append({
                "state": label,
                "bloch_in": [float(x) for x in r_in],
                "dbloch_dt": [float(x) for x in r_out],
                "superop_cross_check": bool(match),
            })
        results[test_key] = {"pass": all(e["superop_cross_check"] for e in entries),
                             "states": entries}

    # Annotate Bloch vector behavior
    # sigma_z dephasing: kills x,y components, preserves z
    # sigma_x: kills y,z, preserves x
    # sigma_y: kills x,z, preserves y
    # sigma_minus: drives toward |0> (rz -> +1)
    # sigma_plus: drives toward |1> (rz -> -1)
    behavior = {}
    for op_name, L in JUMP_OPS.items():
        # Check what happens to unit Bloch vectors
        actions = {}
        for axis, r in [("x", [1, 0, 0]), ("y", [0, 1, 0]), ("z", [0, 0, 1])]:
            rho = bloch_to_rho(r)
            dr = rho_to_bloch(dissipator(L, rho))
            actions[axis] = [float(x) for x in dr]
        behavior[op_name] = actions
    results["bloch_behavior_summary"] = behavior

    # --- Test 6: Trace preservation ---
    trace_results = []
    for op_name, L in JUMP_OPS.items():
        for rho, label in zip(states, labels):
            d_rho = dissipator(L, rho)
            tr = np.real(np.trace(d_rho))
            trace_results.append({
                "operator": op_name,
                "state": label,
                "trace_of_D": float(tr),
                "pass": abs(tr) < 1e-14,
            })
    results["trace_preservation"] = {
        "pass": all(t["pass"] for t in trace_results),
        "details": trace_results,
    }

    # --- Test 7: CPTP evolution ---
    cptp_results = []
    for op_name, L in JUMP_OPS.items():
        D_sup = dissipator_superop(L)
        # Test with a few initial states at t = 0.1, 1.0, 10.0
        for t_val in [0.1, 1.0, 10.0]:
            exp_tD = expm(t_val * D_sup)
            for rho0, label in zip(states[:4], labels[:4]):
                vec0 = rho0.flatten(order='F')
                vec_t = exp_tD @ vec0
                rho_t = vec_t.reshape(2, 2, order='F')
                tr = np.real(np.trace(rho_t))
                eigs = np.real(np.linalg.eigvalsh(rho_t))
                is_positive = bool(np.all(eigs > -1e-10))
                tr_ok = bool(abs(tr - 1.0) < 1e-10)
                cptp_results.append({
                    "operator": op_name,
                    "state": label,
                    "t": t_val,
                    "trace": float(tr),
                    "min_eigenvalue": float(min(eigs)),
                    "positive": is_positive,
                    "trace_one": tr_ok,
                    "pass": is_positive and tr_ok,
                })
    results["cptp_evolution"] = {
        "pass": all(c["pass"] for c in cptp_results),
        "details": cptp_results,
    }

    # --- Tests 8-10: Steady states ---
    steady_results = {}
    for op_name, L in JUMP_OPS.items():
        D_sup = dissipator_superop(L)
        evals, evecs = np.linalg.eig(D_sup)
        # Find eigenvectors with eigenvalue ~ 0
        zero_mask = np.abs(evals) < 1e-10
        n_steady = int(np.sum(zero_mask))
        steady_vecs = evecs[:, zero_mask]

        # Reconstruct steady-state density matrices
        ss_rhos = []
        for j in range(steady_vecs.shape[1]):
            rho_ss = steady_vecs[:, j].reshape(2, 2, order='F')
            # Normalize to trace 1
            tr = np.trace(rho_ss)
            if abs(tr) > 1e-14:
                rho_ss = rho_ss / tr
            # Verify hermiticity
            herm = np.allclose(rho_ss, rho_ss.conj().T, atol=1e-10)
            # Verify D[L](rho_ss) ~ 0
            d_check = dissipator(L, rho_ss)
            is_zero = bool(np.linalg.norm(d_check) < 1e-10)
            ss_rhos.append({
                "rho_ss": [[str(complex(x)) for x in row] for row in rho_ss],
                "bloch": [float(x) for x in rho_to_bloch(rho_ss)],
                "hermitian": bool(herm),
                "D_is_zero": is_zero,
            })

        steady_results[op_name] = {
            "n_steady_states": n_steady,
            "steady_states": ss_rhos,
        }

    # Specific checks for tests 9-10
    # Test 9: sigma_z steady state is diagonal (any diagonal state)
    sz_ss = steady_results["sigma_z"]
    sz_diag_check = sz_ss["n_steady_states"] == 2  # 2D kernel: span of |0><0| and |1><1|
    steady_results["sigma_z"]["diagonal_kernel"] = sz_diag_check

    # Test 10: sigma_minus steady state is |0><0|
    sm_ss = steady_results["sigma_minus"]
    sm_ground = False
    for ss in sm_ss["steady_states"]:
        b = ss["bloch"]
        if abs(b[0]) < 0.1 and abs(b[1]) < 0.1 and abs(b[2] - 1.0) < 0.1:
            sm_ground = True
    steady_results["sigma_minus"]["ground_state_is_steady"] = sm_ground

    results["steady_states"] = steady_results

    # --- Test 11: Spectral gap ---
    spectral_results = {}
    for op_name, L in JUMP_OPS.items():
        D_sup = dissipator_superop(L)
        evals = eigvals(D_sup)
        real_parts = np.real(evals)
        # Spectral gap = smallest |Re(lambda)| among nonzero eigenvalues
        nonzero = [abs(r) for r in real_parts if abs(r) > 1e-10]
        gap = min(nonzero) if nonzero else 0.0
        spectral_results[op_name] = {
            "eigenvalues": [str(complex(e)) for e in evals],
            "real_parts": [float(r) for r in real_parts],
            "spectral_gap": float(gap),
            "decoherence_time": float(1.0 / gap) if gap > 0 else float('inf'),
        }
    results["spectral_gap"] = spectral_results

    # --- Test 12: Depolarizing channel ---
    D_x = dissipator_superop(SIGMA_X)
    D_y = dissipator_superop(SIGMA_Y)
    D_z = dissipator_superop(SIGMA_Z)
    D_sum = D_x + D_y + D_z

    # Depolarizing: sum of all three Pauli dissipators gives isotropic shrinkage.
    # Each D[sigma_i] zeros the two transverse Bloch components at rate 2.
    # Summing: each component hit by 2 of 3 dissipators => rate -4 per component.
    # D[sx]+D[sy]+D[sz](rho) maps Bloch r -> -4r (uniform depolarization).
    depol_checks = []
    for rho, label in zip(states, labels):
        r_in = rho_to_bloch(rho)
        d_rho = dissipator(SIGMA_X, rho) + dissipator(SIGMA_Y, rho) + dissipator(SIGMA_Z, rho)
        r_out = rho_to_bloch(d_rho)
        expected = -4.0 * r_in  # D[sx]+D[sy]+D[sz] gives uniform -4r
        match = bool(np.allclose(r_out, expected, atol=1e-12))
        depol_checks.append({
            "state": label,
            "bloch_in": [float(x) for x in r_in],
            "dbloch_dt": [float(x) for x in r_out],
            "expected_minus4r": [float(x) for x in expected],
            "match": match,
        })
    results["depolarizing_channel"] = {
        "pass": all(d["match"] for d in depol_checks),
        "details": depol_checks,
    }

    # --- Test 13: Commutativity of D[sz] and D[sx] as superoperators ---
    comm = D_z @ D_x - D_x @ D_z
    comm_norm = float(np.linalg.norm(comm))
    commutes = bool(comm_norm < 1e-12)
    results["superop_commutativity_Dz_Dx"] = {
        "commutator_norm": comm_norm,
        "commutes": commutes,
        "note": "D[sz] and D[sx] commute as superoperators" if commutes
                else "D[sz] and D[sx] do NOT commute as superoperators",
    }

    # --- Sympy symbolic verification ---
    if TOOL_MANIFEST["sympy"]["tried"]:
        try:
            sym_results = _sympy_symbolic_dissipator()
            results["sympy_symbolic"] = sym_results
            TOOL_MANIFEST["sympy"]["used"] = True
            TOOL_MANIFEST["sympy"]["reason"] = "Symbolic dissipator computation and trace proof"
        except Exception as e:
            results["sympy_symbolic"] = {"error": str(e), "traceback": traceback.format_exc()}
            TOOL_MANIFEST["sympy"]["reason"] = f"tried but failed: {e}"

    # --- z3 formal trace preservation proof ---
    if TOOL_MANIFEST["z3"]["tried"]:
        try:
            z3_results = _z3_trace_preservation()
            results["z3_trace_proof"] = z3_results
            TOOL_MANIFEST["z3"]["used"] = True
            TOOL_MANIFEST["z3"]["reason"] = "Formal proof that Tr(D[L](rho))=0 for arbitrary rho"
        except Exception as e:
            results["z3_trace_proof"] = {"error": str(e), "traceback": traceback.format_exc()}
            TOOL_MANIFEST["z3"]["reason"] = f"tried but failed: {e}"

    # --- PyTorch cross-validation ---
    if TOOL_MANIFEST["pytorch"]["tried"]:
        try:
            torch_results = _pytorch_cross_validate()
            results["pytorch_cross_validation"] = torch_results
            TOOL_MANIFEST["pytorch"]["used"] = True
            TOOL_MANIFEST["pytorch"]["reason"] = "Numerical cross-validation of dissipator"
        except Exception as e:
            results["pytorch_cross_validation"] = {"error": str(e),
                                                   "traceback": traceback.format_exc()}
            TOOL_MANIFEST["pytorch"]["reason"] = f"tried but failed: {e}"

    results["_time_positive"] = time.time() - t0
    return results


# =====================================================================
# SYMPY: SYMBOLIC DISSIPATOR
# =====================================================================

def _sympy_symbolic_dissipator():
    """Symbolic computation of D[L](rho) for generic 2x2 rho."""
    a, b, c, d = sp.symbols('a b c d')
    rho = sp.Matrix([[a, b], [c, d]])

    results = {}
    pauli = {
        "sigma_x": sp.Matrix([[0, 1], [1, 0]]),
        "sigma_y": sp.Matrix([[0, -sp.I], [sp.I, 0]]),
        "sigma_z": sp.Matrix([[1, 0], [0, -1]]),
        "sigma_minus": sp.Matrix([[0, 1], [0, 0]]),
        "sigma_plus": sp.Matrix([[0, 0], [1, 0]]),
    }

    for name, L in pauli.items():
        Ld = L.adjoint()
        LdL = Ld * L
        D_rho = L * rho * Ld - sp.Rational(1, 2) * (LdL * rho + rho * LdL)
        D_rho_simplified = sp.simplify(D_rho)

        # Trace preservation: Tr(D[L](rho)) should be 0
        tr = sp.simplify(sp.trace(D_rho))

        # For hermitian rho (c = b*), constrain
        D_herm = D_rho_simplified.subs(c, sp.conjugate(b))

        results[name] = {
            "D_rho": str(D_rho_simplified),
            "trace": str(tr),
            "trace_is_zero": tr == 0,
        }

    return results


# =====================================================================
# Z3: FORMAL TRACE PRESERVATION PROOF
# =====================================================================

def _z3_trace_preservation():
    """Use z3 to prove Tr(D[L](rho)) = 0 for all rho, all Pauli L.

    We encode rho as a 2x2 matrix with real and imaginary parts,
    compute D[L](rho) symbolically, and prove trace = 0.
    """
    results = {}

    # Represent rho entries as real+imag
    ar, ai = Reals('ar ai')
    br, bi = Reals('br bi')
    cr, ci = Reals('cr ci')
    dr, di = Reals('dr di')

    # rho = [[a, b], [c, d]] where a = ar+i*ai etc.
    # For trace preservation we need Tr(D[L](rho)) = 0
    # which means the (0,0) + (1,1) entries of D[L](rho) sum to zero.
    # We compute this for each L using explicit matrix multiplication.

    def z3_dissipator_trace(L_entries):
        """Compute Tr(D[L](rho)) symbolically with z3 reals.
        L_entries: ((L00r,L00i),(L01r,L01i),(L10r,L10i),(L11r,L11i))
        Returns (trace_real, trace_imag) as z3 expressions.
        """
        # Complex multiply helper: (a+bi)(c+di) = (ac-bd) + (ad+bc)i
        def cmul(a, b):
            return (a[0]*b[0] - a[1]*b[1], a[0]*b[1] + a[1]*b[0])

        def cadd(a, b):
            return (a[0]+b[0], a[1]+b[1])

        def csub(a, b):
            return (a[0]-b[0], a[1]-b[1])

        def cconj(a):
            return (a[0], -a[1])

        L = [[L_entries[0], L_entries[1]],
             [L_entries[2], L_entries[3]]]
        Ld = [[cconj(L[0][0]), cconj(L[1][0])],
              [cconj(L[0][1]), cconj(L[1][1])]]
        rho_z3 = [[(ar, ai), (br, bi)],
                  [(cr, ci), (dr, di)]]

        # Compute L @ rho @ Ld
        def mat_mul_2x2(A, B):
            C = [[None, None], [None, None]]
            for i in range(2):
                for j in range(2):
                    C[i][j] = cadd(cmul(A[i][0], B[0][j]),
                                   cmul(A[i][1], B[1][j]))
            return C

        LrLd = mat_mul_2x2(mat_mul_2x2(L, rho_z3), Ld)

        # Compute LdL
        LdL = mat_mul_2x2(Ld, L)

        # Compute LdL @ rho
        LdLr = mat_mul_2x2(LdL, rho_z3)
        # Compute rho @ LdL
        rLdL = mat_mul_2x2(rho_z3, LdL)

        # D[L](rho) = LrLd - 0.5*(LdLr + rLdL)
        # Trace = D[0][0] + D[1][1]
        def half(a):
            return (a[0] / 2, a[1] / 2)

        d00 = csub(LrLd[0][0], half(cadd(LdLr[0][0], rLdL[0][0])))
        d11 = csub(LrLd[1][1], half(cadd(LdLr[1][1], rLdL[1][1])))
        tr = cadd(d00, d11)
        return tr

    # Pauli matrices as (real, imag) entries
    pauli_z3 = {
        "sigma_x": ((0, 0), (1, 0), (1, 0), (0, 0)),
        "sigma_y": ((0, 0), (0, -1), (0, 1), (0, 0)),
        "sigma_z": ((1, 0), (0, 0), (0, 0), (-1, 0)),
        "sigma_minus": ((0, 0), (1, 0), (0, 0), (0, 0)),
        "sigma_plus": ((0, 0), (0, 0), (1, 0), (0, 0)),
    }

    for name, L_entries in pauli_z3.items():
        tr = z3_dissipator_trace(L_entries)
        s = Solver()
        # Try to find rho where trace is nonzero
        s.add(Or(tr[0] != 0, tr[1] != 0))
        result = s.check()
        # If unsat, no such rho exists => trace always 0
        proven = (result == unsat)
        results[name] = {
            "trace_always_zero": proven,
            "z3_result": str(result),
        }

    return results


# =====================================================================
# PYTORCH: NUMERICAL CROSS-VALIDATION
# =====================================================================

def _pytorch_cross_validate():
    """Cross-validate numpy dissipator with PyTorch implementation."""
    results = {}

    pauli_torch = {
        "sigma_x": torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128),
        "sigma_y": torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128),
        "sigma_z": torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128),
        "sigma_minus": torch.tensor([[0, 1], [0, 0]], dtype=torch.complex128),
        "sigma_plus": torch.tensor([[0, 0], [1, 0]], dtype=torch.complex128),
    }

    def torch_dissipator(L, rho):
        Ld = L.conj().T
        LdL = Ld @ L
        return L @ rho @ Ld - 0.5 * (LdL @ rho + rho @ LdL)

    states, labels = make_test_states()
    all_match = True
    details = []

    for op_name, L_t in pauli_torch.items():
        L_np = JUMP_OPS[op_name]
        for rho_np, label in zip(states, labels):
            rho_t = torch.tensor(rho_np, dtype=torch.complex128)
            d_np = dissipator(L_np, rho_np)
            d_t = torch_dissipator(L_t, rho_t).numpy()
            match = bool(np.allclose(d_np, d_t, atol=1e-14))
            if not match:
                all_match = False
            details.append({
                "operator": op_name,
                "state": label,
                "match": match,
                "max_diff": float(np.max(np.abs(d_np - d_t))),
            })

    results["all_match"] = all_match
    results["n_tests"] = len(details)
    results["details"] = details
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # Negative 1: Non-physical density matrix (trace != 1) still gives trace-preserving D
    rho_bad_trace = np.array([[2, 0], [0, 1]], dtype=complex)  # Tr = 3
    for op_name, L in JUMP_OPS.items():
        d_rho = dissipator(L, rho_bad_trace)
        tr = np.real(np.trace(d_rho))
        results[f"bad_trace_rho_{op_name}"] = {
            "input_trace": 3.0,
            "D_trace": float(tr),
            "still_zero": abs(tr) < 1e-14,
            "note": "D[L] is trace-preserving even for unnormalized matrices",
        }

    # Negative 2: Non-hermitian "rho" -- D[L] applied to non-hermitian matrix
    rho_non_herm = np.array([[1, 1], [0, 0]], dtype=complex)
    for op_name, L in JUMP_OPS.items():
        d_rho = dissipator(L, rho_non_herm)
        tr = np.real(np.trace(d_rho))
        results[f"non_hermitian_{op_name}"] = {
            "D_trace": float(tr),
            "trace_still_zero": abs(tr) < 1e-14,
        }

    # Negative 3: Zero operator -- D[0](rho) should be zero
    L_zero = np.zeros((2, 2), dtype=complex)
    for rho, label in zip(*make_test_states()):
        d_rho = dissipator(L_zero, rho)
        results[f"zero_operator_{label}"] = {
            "D_norm": float(np.linalg.norm(d_rho)),
            "is_zero": bool(np.linalg.norm(d_rho) < 1e-14),
        }

    # Negative 4: Identity operator as L -- D[I](rho) should be zero
    # D[I](rho) = I rho I - 1/2(I rho + rho I) = rho - rho = 0
    for rho, label in zip(*make_test_states()):
        d_rho = dissipator(I2, rho)
        results[f"identity_operator_{label}"] = {
            "D_norm": float(np.linalg.norm(d_rho)),
            "is_zero": bool(np.linalg.norm(d_rho) < 1e-14),
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # Boundary 1: Pure state idempotency -- rho^2 = rho
    pure_states = [
        ("|0>", bloch_to_rho([0, 0, 1])),
        ("|1>", bloch_to_rho([0, 0, -1])),
        ("|+>", bloch_to_rho([1, 0, 0])),
    ]
    for label, rho in pure_states:
        for op_name, L in JUMP_OPS.items():
            d_rho = dissipator(L, rho)
            # After small dt evolution, is rho still positive?
            for dt in [1e-6, 1e-3, 0.1]:
                rho_t = rho + dt * d_rho
                eigs = np.real(np.linalg.eigvalsh(rho_t))
                results[f"pure_evolution_{label}_{op_name}_dt{dt}"] = {
                    "min_eig": float(min(eigs)),
                    "trace": float(np.real(np.trace(rho_t))),
                    "positive": bool(min(eigs) > -1e-10),
                    "trace_one": bool(abs(np.real(np.trace(rho_t)) - 1.0) < 1e-10),
                }

    # Boundary 2: Maximally mixed state -- D[L](I/2) for each L
    rho_mm = 0.5 * I2
    for op_name, L in JUMP_OPS.items():
        d_rho = dissipator(L, rho_mm)
        results[f"maximally_mixed_{op_name}"] = {
            "D_rho": [[str(complex(x)) for x in row] for row in d_rho],
            "norm": float(np.linalg.norm(d_rho)),
            "is_zero": bool(np.linalg.norm(d_rho) < 1e-14),
            "note": "For Pauli L, D[L](I/2)=0. For sigma_pm, D[L](I/2)!=0.",
        }

    # Boundary 3: Very large number of time steps for convergence to steady state
    for op_name, L in [("sigma_minus", SIGMA_MINUS), ("sigma_z", SIGMA_Z)]:
        D_sup = dissipator_superop(L)
        rho0 = bloch_to_rho([0.9, 0.3, -0.2])
        vec0 = rho0.flatten(order='F')
        t_vals = [0.1, 1.0, 10.0, 100.0]
        trajectory = []
        for t in t_vals:
            vec_t = expm(t * D_sup) @ vec0
            rho_t = vec_t.reshape(2, 2, order='F')
            trajectory.append({
                "t": t,
                "bloch": [float(x) for x in rho_to_bloch(rho_t)],
                "trace": float(np.real(np.trace(rho_t))),
            })
        results[f"convergence_{op_name}"] = trajectory

    # Boundary 4: Numerical precision at very small coupling
    eps = 1e-15
    L_tiny = eps * SIGMA_X
    rho = bloch_to_rho([1, 0, 0])
    d_rho = dissipator(L_tiny, rho)
    results["tiny_coupling"] = {
        "L_scale": eps,
        "D_norm": float(np.linalg.norm(d_rho)),
        "expected_order": float(eps**2),
        "ratio": float(np.linalg.norm(d_rho) / eps**2) if eps > 0 else 0,
        "note": "D[eps*L] scales as eps^2 (quadratic in L)",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running Lindblad dissipator lego sim...")
    t_start = time.time()

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    results = {
        "name": "PURE LEGO: Lindblad Dissipator D[L](rho)",
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "summary": {
            "scope_note": (
                "Local open-system dynamics lego for infinitesimal Lindblad evolution, "
                "steady states, and dissipator spectra on bounded carriers."
            ),
        },
        "total_time_s": time.time() - t_start,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_lindblad_dissipator_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    # Summary
    pos_tests = [k for k in positive if isinstance(positive[k], dict) and "pass" in positive[k]]
    pos_pass = sum(1 for k in pos_tests if positive[k]["pass"])
    print(f"\nPositive tests: {pos_pass}/{len(pos_tests)} passed")
    print(f"Negative tests: {len(negative)} run")
    print(f"Boundary tests: {len(boundary)} run")
    print(f"Total time: {results['total_time_s']:.3f}s")
