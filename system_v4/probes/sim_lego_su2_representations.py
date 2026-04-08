#!/usr/bin/env python3
"""
LEGO: SU(2) Representation Theory -- Clebsch-Gordan & Wigner Symbols
=====================================================================
Canonical sim.  Tools: PyTorch (numeric tensors, autograd), sympy (symbolic CG).

Pure math -- no physics interpretation layered on top.

Sections
--------
1. Irreps of SU(2): spin-j, dimension 2j+1
2. Tensor product decomposition: j1 x j2 = |j1-j2| + ... + (j1+j2)
3. Clebsch-Gordan coefficients via sympy: <j1 m1; j2 m2 | J M>
4. Singlet/triplet verification for 1/2 x 1/2
5. Spin-1/2 x spin-1 = spin-1/2 + spin-3/2 decomposition
6. CG orthogonality (rows and columns)
7. Wigner 3j-symbols and relation to CG
8. Wigner-Eckart theorem: reduced matrix elements

Test states: product basis |j1 m1> x |j2 m2>, coupled basis |J M>.
Dimension check: (2j1+1)(2j2+1) = sum_{J} (2J+1).
"""

import json
import os
import time
import traceback
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed for this sim"},
    "z3":        {"tried": False, "used": False, "reason": "not needed; sympy handles symbolic proofs here"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed"},
}

# --- Tool imports ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Numeric tensor ops: rotation matrices, invariance checks, "
        "autograd for matrix element derivatives"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import sympy as sp
    from sympy.physics.quantum.cg import CG
    from sympy.physics.wigner import wigner_3j
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Symbolic CG coefficients, Wigner 3j-symbols, exact rational arithmetic"
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# HELPERS
# =====================================================================

TOL = 1e-12


def _cg_float(j1, m1, j2, m2, J, M):
    """Evaluate CG coefficient <j1 m1; j2 m2 | J M> as float."""
    val = CG(sp.Rational(j1), sp.Rational(m1),
             sp.Rational(j2), sp.Rational(m2),
             sp.Rational(J), sp.Rational(M)).doit()
    return float(val)


def _wigner3j_float(j1, j2, j3, m1, m2, m3):
    """Evaluate Wigner 3j-symbol as float."""
    val = wigner_3j(sp.Rational(j1), sp.Rational(j2), sp.Rational(j3),
                    sp.Rational(m1), sp.Rational(m2), sp.Rational(m3))
    return float(val)


def _all_m_values(j):
    """Return list of m values for spin j: -j, -j+1, ..., j."""
    j2 = int(2 * j)
    return [sp.Rational(-j2 + 2 * k, 2) for k in range(j2 + 1)]


def _su2_rotation_matrix(j, axis_angle):
    """
    Build (2j+1) x (2j+1) rotation matrix for spin-j rep.
    axis_angle: (theta, nx, ny, nz) -- angle and unit axis.
    Uses the angular momentum generators J_x, J_y, J_z.
    """
    dim = int(2 * j + 1)
    ms = [float(-j + k) for k in range(dim)]

    # Build J_z (diagonal), J_+ (raising), J_- (lowering)
    Jz = torch.diag(torch.tensor(ms, dtype=torch.float64))
    Jp = torch.zeros(dim, dim, dtype=torch.float64)
    Jm = torch.zeros(dim, dim, dtype=torch.float64)
    for i in range(dim - 1):
        m = ms[i]
        val = np.sqrt(j * (j + 1) - m * (m + 1))
        Jp[i + 1, i] = val  # J+ |j,m> = sqrt(...) |j,m+1>
        Jm[i, i + 1] = val  # J- |j,m+1> = sqrt(...) |j,m>

    Jx = 0.5 * (Jp + Jm)
    Jy = -0.5j * (Jp - Jm)
    # Jy is imaginary -- go complex
    Jx_c = Jx.to(torch.complex128)
    Jy_c = torch.zeros(dim, dim, dtype=torch.complex128)
    Jy_c.real = torch.zeros(dim, dim, dtype=torch.float64)
    Jy_c.imag = -0.5 * (Jp - Jm)
    Jz_c = Jz.to(torch.complex128)

    theta, nx, ny, nz = axis_angle
    gen = nx * Jx_c + ny * Jy_c + nz * Jz_c
    R = torch.matrix_exp(-1j * theta * gen)
    return R


def _build_cg_matrix(j1, j2):
    """
    Build the full CG unitary matrix transforming product basis to coupled basis.
    Rows: coupled |J, M>.  Columns: product |j1, m1> x |j2, m2>.
    """
    d1 = int(2 * j1 + 1)
    d2 = int(2 * j2 + 1)
    dim = d1 * d2

    m1_vals = [float(-j1 + k) for k in range(d1)]
    m2_vals = [float(-j2 + k) for k in range(d2)]

    # Product basis ordering: (m1, m2) with m1 varying fastest
    product_index = {}
    idx = 0
    for m1 in m1_vals:
        for m2 in m2_vals:
            product_index[(m1, m2)] = idx
            idx += 1

    # Coupled basis: J from |j1-j2| to j1+j2, M from -J to J
    J_min = abs(j1 - j2)
    J_max = j1 + j2
    coupled_states = []
    J_val = J_min
    while J_val <= J_max + 1e-10:
        d = int(2 * J_val + 1)
        for k in range(d):
            M = -J_val + k
            coupled_states.append((J_val, M))
        J_val += 1

    U = np.zeros((dim, dim))
    for row, (J, M) in enumerate(coupled_states):
        for m1 in m1_vals:
            for m2 in m2_vals:
                if abs(m1 + m2 - M) > 1e-10:
                    continue
                col = product_index[(m1, m2)]
                U[row, col] = _cg_float(j1, m1, j2, m2, J, M)

    return U, coupled_states, product_index


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    t0 = time.time()

    # ------------------------------------------------------------------
    # TEST 1: Dimension check for tensor products
    # ------------------------------------------------------------------
    try:
        test_cases = [
            (sp.Rational(1, 2), sp.Rational(1, 2)),  # 2*2 = 4 = 1+3
            (sp.Rational(1, 2), 1),                    # 2*3 = 6 = 2+4
            (1, 1),                                     # 3*3 = 9 = 1+3+5
            (sp.Rational(3, 2), sp.Rational(1, 2)),   # 4*2 = 8 = 3+5
            (2, 1),                                     # 5*3 = 15 = 3+5+7
        ]
        all_pass = True
        dim_details = []
        for j1, j2 in test_cases:
            j1f, j2f = float(j1), float(j2)
            lhs = int((2 * j1f + 1) * (2 * j2f + 1))
            J_min = abs(j1f - j2f)
            J_max = j1f + j2f
            rhs = 0
            J_val = J_min
            decomp = []
            while J_val <= J_max + 1e-10:
                d = int(2 * J_val + 1)
                rhs += d
                decomp.append(f"j={J_val}(d={d})")
                J_val += 1
            ok = (lhs == rhs)
            all_pass &= ok
            dim_details.append({
                "j1": str(j1), "j2": str(j2),
                "product_dim": lhs, "sum_dim": rhs,
                "decomposition": decomp, "pass": ok,
            })
        results["dimension_check"] = {
            "pass": all_pass, "details": dim_details,
        }
    except Exception as e:
        results["dimension_check"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # TEST 2: CG coefficients for 1/2 x 1/2 -- singlet + triplet
    # ------------------------------------------------------------------
    try:
        j1 = j2 = sp.Rational(1, 2)
        # Enumerate all CG for this product
        cg_table = {}
        for m1 in [sp.Rational(-1, 2), sp.Rational(1, 2)]:
            for m2 in [sp.Rational(-1, 2), sp.Rational(1, 2)]:
                for J in [0, 1]:
                    M = m1 + m2
                    if abs(M) > J:
                        continue
                    val = CG(j1, m1, j2, m2, J, M).doit()
                    key = f"<{j1},{m1};{j2},{m2}|{J},{M}>"
                    cg_table[key] = str(val)

        # Verify singlet: J=0, M=0
        # |singlet> = CG(1/2,1/2,1/2,-1/2|0,0)|up,down> + CG(1/2,-1/2,1/2,1/2|0,0)|down,up>
        c_ud = float(CG(j1, sp.Rational(1, 2), j2, sp.Rational(-1, 2), 0, 0).doit())
        c_du = float(CG(j1, sp.Rational(-1, 2), j2, sp.Rational(1, 2), 0, 0).doit())
        # Expected: 1/sqrt(2) and -1/sqrt(2) (or vice versa)
        singlet_ok = (
            abs(abs(c_ud) - 1 / np.sqrt(2)) < TOL
            and abs(abs(c_du) - 1 / np.sqrt(2)) < TOL
            and abs(c_ud + c_du) < TOL  # opposite signs
        )

        # Verify triplet M=0: (|ud> + |du>)/sqrt(2)
        t_ud = float(CG(j1, sp.Rational(1, 2), j2, sp.Rational(-1, 2), 1, 0).doit())
        t_du = float(CG(j1, sp.Rational(-1, 2), j2, sp.Rational(1, 2), 1, 0).doit())
        triplet_m0_ok = (
            abs(abs(t_ud) - 1 / np.sqrt(2)) < TOL
            and abs(abs(t_du) - 1 / np.sqrt(2)) < TOL
            and abs(t_ud - t_du) < TOL  # same sign
        )

        # Triplet M=+1: |uu>, M=-1: |dd>
        t_uu = float(CG(j1, sp.Rational(1, 2), j2, sp.Rational(1, 2), 1, 1).doit())
        t_dd = float(CG(j1, sp.Rational(-1, 2), j2, sp.Rational(-1, 2), 1, -1).doit())
        triplet_extremal_ok = abs(t_uu - 1.0) < TOL and abs(t_dd - 1.0) < TOL

        results["half_x_half_cg"] = {
            "pass": singlet_ok and triplet_m0_ok and triplet_extremal_ok,
            "cg_table": cg_table,
            "singlet_coeffs": {"c_ud": c_ud, "c_du": c_du, "opposite_sign": singlet_ok},
            "triplet_m0_coeffs": {"t_ud": t_ud, "t_du": t_du, "same_sign": triplet_m0_ok},
            "triplet_extremal": {"t_uu": t_uu, "t_dd": t_dd, "both_one": triplet_extremal_ok},
        }
    except Exception as e:
        results["half_x_half_cg"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # TEST 3: CG matrix unitarity for 1/2 x 1/2
    # ------------------------------------------------------------------
    try:
        U, coupled, prod_idx = _build_cg_matrix(0.5, 0.5)
        U_t = torch.tensor(U, dtype=torch.float64)
        eye = torch.eye(4, dtype=torch.float64)
        # U U^T = I (rows orthonormal)
        row_orth = torch.max(torch.abs(U_t @ U_t.T - eye)).item()
        # U^T U = I (columns orthonormal)
        col_orth = torch.max(torch.abs(U_t.T @ U_t - eye)).item()
        results["cg_unitarity_half_x_half"] = {
            "pass": row_orth < TOL and col_orth < TOL,
            "max_row_deviation": row_orth,
            "max_col_deviation": col_orth,
        }
    except Exception as e:
        results["cg_unitarity_half_x_half"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # TEST 4: CG orthogonality for 1/2 x 1
    # ------------------------------------------------------------------
    try:
        U, coupled, prod_idx = _build_cg_matrix(0.5, 1.0)
        U_t = torch.tensor(U, dtype=torch.float64)
        dim = U_t.shape[0]
        eye = torch.eye(dim, dtype=torch.float64)
        row_orth = torch.max(torch.abs(U_t @ U_t.T - eye)).item()
        col_orth = torch.max(torch.abs(U_t.T @ U_t - eye)).item()

        # Check decomposition: j=1/2 (d=2) + j=3/2 (d=4) = 6 = 2*3
        J_vals = sorted(set(J for J, M in coupled))
        expected_Js = [0.5, 1.5]
        decomp_ok = (J_vals == expected_Js)

        results["cg_orthogonality_half_x_one"] = {
            "pass": row_orth < TOL and col_orth < TOL and decomp_ok,
            "max_row_deviation": row_orth,
            "max_col_deviation": col_orth,
            "J_values": J_vals,
            "expected_Js": expected_Js,
            "decomposition_correct": decomp_ok,
        }
    except Exception as e:
        results["cg_orthogonality_half_x_one"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # TEST 5: Singlet rotational invariance
    # ------------------------------------------------------------------
    try:
        # Build singlet state vector in product basis |m1, m2>
        # Basis order: (-1/2,-1/2), (-1/2,1/2), (1/2,-1/2), (1/2,1/2)
        singlet = torch.zeros(4, dtype=torch.complex128)
        # |singlet> = (|+-> - |-+>)/sqrt(2)
        # index: (-1/2,-1/2)=0, (-1/2,+1/2)=1, (+1/2,-1/2)=2, (+1/2,+1/2)=3
        singlet[1] = -1.0 / np.sqrt(2)  # |-1/2, +1/2>
        singlet[2] = 1.0 / np.sqrt(2)   # |+1/2, -1/2>

        # Rotate both spins by same angle
        all_invariant = True
        angles = [(0.5, 0, 0, 1), (1.2, 1, 0, 0), (0.7, 0, 1, 0),
                  (2.1, 1/np.sqrt(3), 1/np.sqrt(3), 1/np.sqrt(3))]
        angle_results = []
        for axis_angle in angles:
            R_half = _su2_rotation_matrix(0.5, axis_angle)
            R_total = torch.kron(R_half, R_half)
            rotated = R_total @ singlet
            overlap = torch.abs(torch.dot(rotated.conj(), singlet)).item()
            inv_ok = abs(overlap - 1.0) < 1e-10
            all_invariant &= inv_ok
            angle_results.append({
                "axis_angle": list(axis_angle),
                "overlap": overlap,
                "invariant": inv_ok,
            })

        results["singlet_rotational_invariance"] = {
            "pass": all_invariant,
            "rotations_tested": len(angles),
            "details": angle_results,
        }
    except Exception as e:
        results["singlet_rotational_invariance"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # TEST 6: Wigner 3j-symbol relation to CG
    # ------------------------------------------------------------------
    try:
        # <j1 m1; j2 m2 | J M> = (-1)^(j1-j2+M) * sqrt(2J+1) * (j1 j2 J; m1 m2 -M)
        test_params = [
            (sp.Rational(1, 2), sp.Rational(1, 2), sp.Rational(1, 2), sp.Rational(-1, 2), 0, 0),
            (sp.Rational(1, 2), sp.Rational(1, 2), sp.Rational(1, 2), sp.Rational(-1, 2), 1, 0),
            (sp.Rational(1, 2), sp.Rational(1, 2), sp.Rational(1, 2), sp.Rational(1, 2), 1, 1),
            (1, 0, 1, 0, 0, 0),
            (1, 1, 1, -1, 0, 0),
            (1, 0, 1, 0, 2, 0),
            (sp.Rational(1, 2), sp.Rational(1, 2), 1, 0, sp.Rational(3, 2), sp.Rational(1, 2)),
        ]
        all_ok = True
        w3j_details = []
        for j1, m1, j2, m2, J, M in test_params:
            cg_val = float(CG(j1, m1, j2, m2, J, M).doit())
            w3j_val = _wigner3j_float(j1, j2, J, m1, m2, -M)
            phase = float((-1) ** (j1 - j2 + M))
            factor = np.sqrt(float(2 * J + 1))
            reconstructed = phase * factor * w3j_val
            err = abs(cg_val - reconstructed)
            ok = err < TOL
            all_ok &= ok
            w3j_details.append({
                "j1": str(j1), "m1": str(m1), "j2": str(j2), "m2": str(m2),
                "J": str(J), "M": str(M),
                "cg": cg_val, "w3j": w3j_val,
                "reconstructed_from_w3j": reconstructed, "error": err, "pass": ok,
            })
        results["wigner_3j_cg_relation"] = {"pass": all_ok, "details": w3j_details}
    except Exception as e:
        results["wigner_3j_cg_relation"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # TEST 7: Wigner-Eckart theorem -- J_z matrix elements
    # ------------------------------------------------------------------
    try:
        # For a rank-1 tensor operator T^(1)_q = J_q (spherical components),
        # <j m' | T^(1)_0 | j m> = <j m; 1 0 | j m'> * <j || T^(1) || j> / sqrt(2j+1)
        # T^(1)_0 = J_z, so <j m'|J_z|j m> = m * delta_{m,m'}
        # The reduced matrix element: <j || J || j> = sqrt(j(j+1)(2j+1))
        test_js = [sp.Rational(1, 2), 1, sp.Rational(3, 2), 2]
        all_ok = True
        we_details = []
        for j in test_js:
            jf = float(j)
            reduced_me = np.sqrt(jf * (jf + 1) * (2 * jf + 1))
            ms = _all_m_values(j)
            for m in ms:
                mf = float(m)
                # Direct: <j m|J_z|j m> = m
                direct = mf
                # Via Wigner-Eckart: CG(j,m,1,0|j,m) * reduced / sqrt(2j+1)
                cg_val = float(CG(j, m, 1, 0, j, m).doit())
                via_we = cg_val * reduced_me / np.sqrt(2 * jf + 1)
                err = abs(direct - via_we)
                ok = err < TOL
                all_ok &= ok
                we_details.append({
                    "j": str(j), "m": str(m),
                    "direct": direct, "wigner_eckart": via_we,
                    "error": err, "pass": ok,
                })
        results["wigner_eckart_jz"] = {"pass": all_ok, "tests": len(we_details), "details": we_details}
    except Exception as e:
        results["wigner_eckart_jz"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # TEST 8: CG unitarity for 1 x 1 (larger decomposition)
    # ------------------------------------------------------------------
    try:
        U, coupled, prod_idx = _build_cg_matrix(1.0, 1.0)
        U_t = torch.tensor(U, dtype=torch.float64)
        dim = U_t.shape[0]
        eye = torch.eye(dim, dtype=torch.float64)
        row_orth = torch.max(torch.abs(U_t @ U_t.T - eye)).item()
        col_orth = torch.max(torch.abs(U_t.T @ U_t - eye)).item()

        J_vals = sorted(set(J for J, M in coupled))
        expected_Js = [0.0, 1.0, 2.0]
        decomp_ok = (J_vals == expected_Js)

        results["cg_unitarity_one_x_one"] = {
            "pass": row_orth < TOL and col_orth < TOL and decomp_ok,
            "dimension": dim,
            "max_row_deviation": row_orth,
            "max_col_deviation": col_orth,
            "J_values": J_vals,
            "decomposition_correct": decomp_ok,
        }
    except Exception as e:
        results["cg_unitarity_one_x_one"] = {"pass": False, "error": traceback.format_exc()}

    results["_elapsed_s"] = round(time.time() - t0, 3)
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ------------------------------------------------------------------
    # NEG 1: CG is zero when M != m1 + m2
    # ------------------------------------------------------------------
    try:
        # <1/2, 1/2; 1/2, 1/2 | 1, 0> should be zero (M=0 but m1+m2=1)
        val = float(CG(sp.Rational(1, 2), sp.Rational(1, 2),
                        sp.Rational(1, 2), sp.Rational(1, 2),
                        1, 0).doit())
        results["cg_zero_wrong_M"] = {
            "pass": abs(val) < TOL,
            "value": val,
            "note": "CG must vanish when M != m1+m2",
        }
    except Exception as e:
        results["cg_zero_wrong_M"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # NEG 2: CG is zero when J is outside allowed range
    # ------------------------------------------------------------------
    try:
        # <1/2, 1/2; 1/2, -1/2 | 2, 0> -- J=2 not in {0,1} for 1/2 x 1/2
        val = float(CG(sp.Rational(1, 2), sp.Rational(1, 2),
                        sp.Rational(1, 2), sp.Rational(-1, 2),
                        2, 0).doit())
        results["cg_zero_invalid_J"] = {
            "pass": abs(val) < TOL,
            "value": val,
            "note": "CG must vanish when J outside |j1-j2|..j1+j2",
        }
    except Exception as e:
        results["cg_zero_invalid_J"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # NEG 3: Triplet state is NOT rotationally invariant
    # ------------------------------------------------------------------
    try:
        # Triplet M=0: (|+-> + |-+>)/sqrt(2)
        triplet_m0 = torch.zeros(4, dtype=torch.complex128)
        triplet_m0[1] = 1.0 / np.sqrt(2)   # |-1/2, +1/2>
        triplet_m0[2] = 1.0 / np.sqrt(2)   # |+1/2, -1/2>

        R_half = _su2_rotation_matrix(0.5, (1.0, 1, 0, 0))
        R_total = torch.kron(R_half, R_half)
        rotated = R_total @ triplet_m0
        overlap = torch.abs(torch.dot(rotated.conj(), triplet_m0)).item()
        not_invariant = (abs(overlap - 1.0) > 1e-6)

        results["triplet_not_invariant"] = {
            "pass": not_invariant,
            "overlap": overlap,
            "note": "Triplet M=0 should NOT be invariant under arbitrary rotation",
        }
    except Exception as e:
        results["triplet_not_invariant"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # NEG 4: Broken CG matrix (perturbed) is NOT unitary
    # ------------------------------------------------------------------
    try:
        U, _, _ = _build_cg_matrix(0.5, 0.5)
        U_broken = U.copy()
        U_broken[0, 0] += 0.1  # perturb
        U_bt = torch.tensor(U_broken, dtype=torch.float64)
        eye = torch.eye(4, dtype=torch.float64)
        dev = torch.max(torch.abs(U_bt @ U_bt.T - eye)).item()
        results["broken_cg_not_unitary"] = {
            "pass": dev > 0.01,
            "max_deviation": dev,
            "note": "Perturbed CG matrix must fail unitarity",
        }
    except Exception as e:
        results["broken_cg_not_unitary"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # NEG 5: Wrong dimension formula should fail
    # ------------------------------------------------------------------
    try:
        j1, j2 = 1.0, 1.0
        wrong_sum = int(2 * 0 + 1) + int(2 * 1 + 1)  # skip J=2 -> 1+3=4, not 9
        correct = int((2 * j1 + 1) * (2 * j2 + 1))
        results["wrong_dimension_sum"] = {
            "pass": wrong_sum != correct,
            "wrong_sum": wrong_sum,
            "correct": correct,
            "note": "Omitting J=2 from 1x1 decomposition gives wrong dimension",
        }
    except Exception as e:
        results["wrong_dimension_sum"] = {"pass": False, "error": traceback.format_exc()}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ------------------------------------------------------------------
    # BOUND 1: j=0 (trivial rep) -- tensor product j x 0 = j
    # ------------------------------------------------------------------
    try:
        j_vals = [sp.Rational(1, 2), 1, sp.Rational(3, 2), 2]
        all_ok = True
        for j in j_vals:
            jf = float(j)
            dim_prod = int(2 * jf + 1) * 1
            dim_sum = int(2 * jf + 1)
            ok = (dim_prod == dim_sum)
            # CG coefficient: <j,m; 0,0 | j,m> = 1 for all m
            for m in _all_m_values(j):
                cg_val = float(CG(j, m, 0, 0, j, m).doit())
                ok &= (abs(cg_val - 1.0) < TOL)
            all_ok &= ok
        results["tensor_with_trivial_rep"] = {
            "pass": all_ok,
            "note": "j x 0 = j with all CG = 1",
        }
    except Exception as e:
        results["tensor_with_trivial_rep"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # BOUND 2: Maximum CG coefficient magnitude is 1
    # ------------------------------------------------------------------
    try:
        pairs = [
            (sp.Rational(1, 2), sp.Rational(1, 2)),
            (sp.Rational(1, 2), 1),
            (1, 1),
        ]
        all_ok = True
        for j1, j2 in pairs:
            j1f, j2f = float(j1), float(j2)
            J_min = abs(j1f - j2f)
            J_max = j1f + j2f
            for m1 in _all_m_values(j1):
                for m2 in _all_m_values(j2):
                    J_val = J_min
                    while J_val <= J_max + 1e-10:
                        M = float(m1 + m2)
                        if abs(M) <= J_val + 1e-10:
                            val = abs(_cg_float(j1, m1, j2, m2, J_val, M))
                            if val > 1.0 + TOL:
                                all_ok = False
                        J_val += 1
        results["cg_magnitude_bound"] = {
            "pass": all_ok,
            "note": "|CG| <= 1 for all tested coefficients",
        }
    except Exception as e:
        results["cg_magnitude_bound"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # BOUND 3: High spin -- 5/2 x 5/2 dimension and unitarity
    # ------------------------------------------------------------------
    try:
        j1 = j2 = 2.5
        dim = int((2 * j1 + 1) * (2 * j2 + 1))  # 6*6 = 36
        J_min = 0.0
        J_max = 5.0
        dim_sum = 0
        J_val = J_min
        while J_val <= J_max + 1e-10:
            dim_sum += int(2 * J_val + 1)
            J_val += 1
        dim_ok = (dim == dim_sum)  # 36 = 1+3+5+7+9+11

        U, _, _ = _build_cg_matrix(j1, j2)
        U_t = torch.tensor(U, dtype=torch.float64)
        eye = torch.eye(dim, dtype=torch.float64)
        dev = torch.max(torch.abs(U_t @ U_t.T - eye)).item()

        results["high_spin_5half_x_5half"] = {
            "pass": dim_ok and dev < 1e-8,
            "product_dim": dim,
            "sum_dim": dim_sum,
            "unitarity_deviation": dev,
        }
    except Exception as e:
        results["high_spin_5half_x_5half"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # BOUND 4: Wigner 3j symmetry under column permutation
    # ------------------------------------------------------------------
    try:
        # (j1 j2 j3; m1 m2 m3) is invariant under even permutations,
        # picks up (-1)^(j1+j2+j3) under odd permutations
        j1, j2, j3 = sp.Rational(1, 2), sp.Rational(1, 2), 1
        m1, m2, m3 = sp.Rational(1, 2), sp.Rational(-1, 2), 0

        w_123 = _wigner3j_float(j1, j2, j3, m1, m2, m3)
        # Even permutation: (2,3,1)
        w_231 = _wigner3j_float(j2, j3, j1, m2, m3, m1)
        # Odd permutation: (2,1,3) -> factor (-1)^(j1+j2+j3) = (-1)^2 = 1
        w_213 = _wigner3j_float(j2, j1, j3, m2, m1, m3)
        phase = float((-1) ** (j1 + j2 + j3))

        even_ok = abs(w_123 - w_231) < TOL
        odd_ok = abs(w_123 - phase * w_213) < TOL

        results["wigner_3j_permutation_symmetry"] = {
            "pass": even_ok and odd_ok,
            "w_123": w_123, "w_231": w_231, "w_213": w_213,
            "phase": phase,
            "even_perm_ok": even_ok, "odd_perm_ok": odd_ok,
        }
    except Exception as e:
        results["wigner_3j_permutation_symmetry"] = {"pass": False, "error": traceback.format_exc()}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("SU(2) Representation Theory -- Clebsch-Gordan & Wigner Lego")
    print("=" * 60)

    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    results = {
        "name": "lego_su2_representations",
        "tool_manifest": TOOL_MANIFEST,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "canonical",
    }

    # Summary
    all_tests = {}
    all_tests.update(pos)
    all_tests.update(neg)
    all_tests.update(bnd)
    passed = sum(1 for v in all_tests.values() if isinstance(v, dict) and v.get("pass"))
    failed = sum(1 for v in all_tests.values() if isinstance(v, dict) and v.get("pass") is False)
    total = passed + failed
    results["summary"] = {"total": total, "passed": passed, "failed": failed}

    print(f"\nResults: {passed}/{total} passed")
    for k, v in all_tests.items():
        if isinstance(v, dict) and "pass" in v:
            status = "PASS" if v["pass"] else "FAIL"
            print(f"  [{status}] {k}")

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_su2_representations_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
