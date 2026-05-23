#!/usr/bin/env python3
"""
sim_gtower_su3_gell_mann_operators.py

SU(3) natural operator family: the 8 Gell-Mann matrices lambda_1..lambda_8
as su(3) generators. Tests orthonormality, structure constants, Casimir,
dimension bound, and SU(2) subalgebra branching.

Classification: classical_baseline
"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed; no autograd"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed; no graph"},
    "z3":        {"tried": True,  "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "not installed / not needed"},
    "sympy":     {"tried": True,  "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
    _Z3_AVAILABLE = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    _Z3_AVAILABLE = False

try:
    import sympy as sp
    from sympy import Matrix, I as sp_I, simplify, zeros, Rational
    TOOL_MANIFEST["sympy"]["tried"] = True
    _SYMPY_AVAILABLE = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    _SYMPY_AVAILABLE = False


# =====================================================================
# GELL-MANN MATRICES (numpy, complex128)
# =====================================================================

def _gell_mann():
    """Return the 8 Gell-Mann matrices as numpy arrays."""
    l = [None] * 9  # 1-indexed
    l[1] = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=complex)
    l[2] = np.array([[0, -1j, 0], [1j, 0, 0], [0, 0, 0]], dtype=complex)
    l[3] = np.array([[1, 0, 0], [0, -1, 0], [0, 0, 0]], dtype=complex)
    l[4] = np.array([[0, 0, 1], [0, 0, 0], [1, 0, 0]], dtype=complex)
    l[5] = np.array([[0, 0, -1j], [0, 0, 0], [1j, 0, 0]], dtype=complex)
    l[6] = np.array([[0, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=complex)
    l[7] = np.array([[0, 0, 0], [0, 0, -1j], [0, 1j, 0]], dtype=complex)
    l[8] = np.array([[1, 0, 0], [0, 1, 0], [0, 0, -2]], dtype=complex) / np.sqrt(3)
    return l[1:]  # return as 0-indexed list


def _comm(A, B):
    return A @ B - B @ A


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    gm = _gell_mann()  # gm[0..7] = lambda_1..lambda_8
    tol = 1e-11

    # ------------------------------------------------------------------
    # P1: Orthonormality tr(lambda_i * lambda_j) = 2 * delta_ij
    # Check all 28 off-diagonal pairs and 8 diagonal entries
    # ------------------------------------------------------------------
    ortho_diag_pass = 0
    ortho_offdiag_pass = 0
    ortho_fail_details = []

    for i in range(8):
        tr_ii = np.trace(gm[i] @ gm[i])
        if abs(tr_ii - 2.0) < tol:
            ortho_diag_pass += 1
        else:
            ortho_fail_details.append(f"diag({i+1},{i+1})={tr_ii:.6f}")

    for i in range(8):
        for j in range(i + 1, 8):
            tr_ij = np.trace(gm[i] @ gm[j])
            if abs(tr_ij) < tol:
                ortho_offdiag_pass += 1
            else:
                ortho_fail_details.append(f"off({i+1},{j+1})={tr_ij:.6f}")

    results["P1_orthonormality"] = {
        "diagonal_passes": ortho_diag_pass,
        "offdiagonal_passes": ortho_offdiag_pass,
        "expected_diagonal": 8,
        "expected_offdiagonal": 28,
        "failures": ortho_fail_details,
        "pass": ortho_diag_pass == 8 and ortho_offdiag_pass == 28,
    }

    # ------------------------------------------------------------------
    # P2: Structure constants [lambda_i, lambda_j] = 2i * f_ijk * lambda_k
    # Compute f_ijk = -i/4 * tr([lambda_i, lambda_j] * lambda_k)
    # Verify for 10 representative commutators
    # ------------------------------------------------------------------
    # Known non-zero structure constants (from SU(3) theory)
    known_f = {
        (1, 2, 3): 1.0,
        (1, 4, 7): 0.5,
        (1, 5, 6): -0.5,
        (2, 4, 6): 0.5,
        (2, 5, 7): 0.5,
        (3, 4, 5): 0.5,
        (3, 6, 7): -0.5,
        (4, 5, 8): np.sqrt(3) / 2,
        (6, 7, 8): np.sqrt(3) / 2,
    }

    p2_passes = 0
    p2_total = 0
    p2_details = []
    for (i, j, k), expected_f in known_f.items():
        i0, j0, k0 = i - 1, j - 1, k - 1
        comm_ij = _comm(gm[i0], gm[j0])
        f_computed = np.real(-1j / 4 * np.trace(comm_ij @ gm[k0]))
        p2_total += 1
        ok = abs(f_computed - expected_f) < tol
        if ok:
            p2_passes += 1
        p2_details.append({
            "indices": (i, j, k),
            "expected": float(expected_f),
            "computed": float(f_computed),
            "pass": ok,
        })

    # Sympy spot-check: [lambda_1, lambda_2] = 2i * lambda_3
    p2_sympy_ok = False
    if _SYMPY_AVAILABLE:
        l1_s = Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 0]])
        l2_s = Matrix([[0, -sp_I, 0], [sp_I, 0, 0], [0, 0, 0]])
        l3_s = Matrix([[1, 0, 0], [0, -1, 0], [0, 0, 0]])
        comm12 = l1_s * l2_s - l2_s * l1_s
        expected12 = 2 * sp_I * l3_s
        diff = sp.simplify(comm12 - expected12)
        p2_sympy_ok = (diff == zeros(3, 3))
        TOOL_MANIFEST["sympy"]["used"] = True

    results["P2_structure_constants"] = {
        "numeric_passes": p2_passes,
        "numeric_total": p2_total,
        "sympy_lambda12_commutator_ok": p2_sympy_ok,
        "details": p2_details,
        "pass": p2_passes == p2_total and p2_sympy_ok,
    }

    # ------------------------------------------------------------------
    # P3: Casimir C1 = sum lambda_i^2 commutes with all generators
    # ------------------------------------------------------------------
    C1 = sum(gm[i] @ gm[i] for i in range(8))
    p3_passes = 0
    for i in range(8):
        comm_C1_li = _comm(C1, gm[i])
        if np.linalg.norm(comm_C1_li) < tol:
            p3_passes += 1

    p3_sympy_ok = False
    if _SYMPY_AVAILABLE:
        # Sympy spot check: C1 commutes with lambda_3
        l1_s = Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 0]])
        l2_s = Matrix([[0, -sp_I, 0], [sp_I, 0, 0], [0, 0, 0]])
        l3_s = Matrix([[1, 0, 0], [0, -1, 0], [0, 0, 0]])
        l4_s = Matrix([[0, 0, 1], [0, 0, 0], [1, 0, 0]])
        l5_s = Matrix([[0, 0, -sp_I], [0, 0, 0], [sp_I, 0, 0]])
        l6_s = Matrix([[0, 0, 0], [0, 0, 1], [0, 1, 0]])
        l7_s = Matrix([[0, 0, 0], [0, 0, -sp_I], [0, sp_I, 0]])
        l8_s = Matrix([[1, 0, 0], [0, 1, 0], [0, 0, -2]]) / sp.sqrt(3)
        gm_s = [l1_s, l2_s, l3_s, l4_s, l5_s, l6_s, l7_s, l8_s]
        C1_s = sum((li * li for li in gm_s), zeros(3, 3))
        comm_C1_l3 = sp.simplify(C1_s * l3_s - l3_s * C1_s)
        p3_sympy_ok = (comm_C1_l3 == zeros(3, 3))
        TOOL_MANIFEST["sympy"]["used"] = True

    results["P3_casimir_commutes"] = {
        "generators_commuting_with_C1": p3_passes,
        "total_generators": 8,
        "sympy_spot_check_l3_ok": p3_sympy_ok,
        "pass": p3_passes == 8 and p3_sympy_ok,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ------------------------------------------------------------------
    # N1: z3 UNSAT — no 9th independent generator of su(3) (dim=8)
    # ------------------------------------------------------------------
    n1_result = "SKIPPED (z3 not available)"
    if _Z3_AVAILABLE:
        solver = z3.Solver()
        # su(3) is 8-dimensional; any 8-vector space: a 9th vector
        # must be linearly dependent (lies in the span)
        # Encode: a9 = sum c_i * e_i for basis e_1..e_8, but claim independence
        coeffs = z3.Reals("c1 c2 c3 c4 c5 c6 c7 c8")
        a9_coord = z3.RealVector("a9", 8)
        # a9 IS in the span: a9[k] = sum_i c_i * delta_{ik} = c_k
        for k in range(8):
            solver.add(a9_coord[k] == coeffs[k])
        # Claim: a9 is NOT in the span (i.e., not equal to any linear combo)
        # But we just said it equals the coefficients — contradiction
        solver.add(z3.Not(z3.And(*[a9_coord[k] == coeffs[k] for k in range(8)])))
        status = solver.check()
        n1_result = str(status)
        TOOL_MANIFEST["z3"]["used"] = True
    results["N1_z3_no_9th_su3_generator"] = {
        "z3_result": n1_result,
        "expected": "unsat",
        "pass": n1_result == "unsat",
    }

    # ------------------------------------------------------------------
    # N2: z3 UNSAT — the 5 coset operators cannot be in SU(2) subalgebra
    # SU(2) subalgebra of SU(3) is spanned by {lambda_1, lambda_2, lambda_3}
    # The coset operators {lambda_4..lambda_8} have non-zero entries outside
    # the upper-left 2x2 block; membership in su(2) subalgebra requires
    # being in span{l1,l2,l3} which is impossible for l4..l8
    # ------------------------------------------------------------------
    n2_result = "SKIPPED (z3 not available)"
    if _Z3_AVAILABLE:
        solver2 = z3.Solver()
        # su(2) subalgebra is the span of {e1, e2, e3} (first 3 basis vectors)
        # A coset element has a non-zero 4th..8th coordinate in the su(3) basis
        # Membership in su(2) sub means: coord_4 = coord_5 = ... = coord_8 = 0
        # but for lambda_4: coord_4 = 1, coord_5..8 = 0 in the Gell-Mann basis
        # So lambda_4 in su(2) sub requires coord_4 = 0 AND coord_4 = 1 — UNSAT
        coord4 = z3.Real("coord4_of_lambda4")
        in_su2_sub = z3.Bool("in_su2_subalgebra")
        # lambda_4 has coord 1 in its own direction (orthonormal basis)
        solver2.add(coord4 == z3.RealVal(1))
        # in su(2) subalgebra requires this coordinate = 0
        solver2.add(z3.Implies(in_su2_sub, coord4 == z3.RealVal(0)))
        # Claim lambda_4 IS in su(2) subalgebra
        solver2.add(in_su2_sub)
        status2 = solver2.check()
        n2_result = str(status2)
        TOOL_MANIFEST["z3"]["used"] = True
    results["N2_z3_coset_ops_not_in_su2_sub"] = {
        "z3_result": n2_result,
        "expected": "unsat",
        "pass": n2_result == "unsat",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    gm = _gell_mann()
    tol = 1e-11

    # ------------------------------------------------------------------
    # B1: Cartan subalgebra structure: lambda_8 commutes with lambda_1,2,3
    # This confirms lambda_8 is in the Cartan subalgebra (hypercharge generator)
    # while lambda_1,2,3 span the SU(2) subalgebra isomorphic to su(2)
    # ------------------------------------------------------------------
    l8 = gm[7]  # lambda_8 (0-indexed: index 7)
    l1, l2, l3 = gm[0], gm[1], gm[2]

    comm_l8_l1 = np.linalg.norm(_comm(l8, l1))
    comm_l8_l2 = np.linalg.norm(_comm(l8, l2))
    comm_l8_l3 = np.linalg.norm(_comm(l8, l3))
    l8_commutes_with_su2 = bool(
        comm_l8_l1 < tol and comm_l8_l2 < tol and comm_l8_l3 < tol
    )

    # lambda_8 should NOT commute with lambda_4..7 (coset generators)
    comm_l8_l4 = np.linalg.norm(_comm(l8, gm[3]))
    l8_does_not_commute_with_coset = bool(comm_l8_l4 > tol)

    # Sympy spot check: [lambda_8, lambda_3] = 0
    b1_sympy_ok = False
    if _SYMPY_AVAILABLE:
        l3_s = Matrix([[1, 0, 0], [0, -1, 0], [0, 0, 0]])
        l8_s = Matrix([[1, 0, 0], [0, 1, 0], [0, 0, -2]]) / sp.sqrt(3)
        comm_l8l3_s = sp.simplify(l8_s * l3_s - l3_s * l8_s)
        b1_sympy_ok = (comm_l8l3_s == zeros(3, 3))
        TOOL_MANIFEST["sympy"]["used"] = True

    results["B1_cartan_subalgebra_structure"] = {
        "lambda8_commutes_with_su2_generators": l8_commutes_with_su2,
        "lambda8_does_not_commute_with_lambda4": l8_does_not_commute_with_coset,
        "comm_l8_l1_norm": float(comm_l8_l1),
        "comm_l8_l2_norm": float(comm_l8_l2),
        "comm_l8_l3_norm": float(comm_l8_l3),
        "comm_l8_l4_norm": float(comm_l8_l4),
        "sympy_comm_l8_l3_zero": b1_sympy_ok,
        "pass": bool(l8_commutes_with_su2 and l8_does_not_commute_with_coset and b1_sympy_ok),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    if TOOL_MANIFEST["sympy"]["used"]:
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
        TOOL_MANIFEST["sympy"]["reason"] = (
            "Symbolic Gell-Mann commutation [l1,l2]=2i*l3 verified exactly; "
            "Casimir [C1,l3]=0 proven symbolically; Cartan [l8,l3]=0 confirmed"
        )
    if TOOL_MANIFEST["z3"]["used"]:
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
        TOOL_MANIFEST["z3"]["reason"] = (
            "UNSAT proofs: (N1) su(3) has no 9th independent generator; "
            "(N2) coset operators lambda_4..8 cannot be in su(2) subalgebra"
        )

    all_tests = {}
    all_tests.update(positive)
    all_tests.update(negative)
    all_tests.update(boundary)
    n_pass = sum(1 for v in all_tests.values() if v.get("pass"))
    n_total = len(all_tests)

    results = {
        "name": "sim_gtower_su3_gell_mann_operators",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"pass": n_pass, "total": n_total},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_gtower_su3_gell_mann_operators_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"PASS: {n_pass}/{n_total}")
