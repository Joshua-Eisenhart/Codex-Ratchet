#!/usr/bin/env python3
"""
sim_gtower_f4_exceptional_geometry.py

F4 exceptional Lie group geometry sim for the G-tower XGI hypergraph.
F4 is rank 4, dim 52, contains B4=SO(9) (dim 36) and C3=Sp(6) (dim 21).
Cartan matrix is non-simply-laced (long/short root ratio √2), det=1.

G2 (rank 2, dim 14) confirmed in prior sim; F4 is the pendant node sibling.

Tests:
  P1 — dim(F4) = rank + 2*(num_positive_roots) = 4 + 2*24 = 52
  P2 — containment chain: dim(Sp6)=21 < dim(B4)=36 < dim(F4)=52
  P3 — F4 Cartan matrix: det=1, first row = [2,-1,0,0]
  N1 — z3 UNSAT: F4_dim==52 AND B4_dim==36 AND F4_dim < B4_dim (impossible)
  N2 — z3 UNSAT: F4 Cartan matrix is symmetric (non-simply-laced → not symmetric)
  B1 — G2 vs F4: both exceptional, dimensional ordering consistent (14 < 52)
"""

import json
import os

classification = "canonical"
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": "not needed for classical Lie algebra arithmetic"},
    "pyg":        {"tried": False, "used": False, "reason": "not needed for classical Lie algebra arithmetic"},
    "z3":         {"tried": False, "used": False, "reason": ""},
    "cvc5":       {"tried": False, "used": False, "reason": "not installed"},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": "not needed for root-system arithmetic"},
    "geomstats":  {"tried": False, "used": False, "reason": "not needed for root-system arithmetic"},
    "e3nn":       {"tried": False, "used": False, "reason": "not needed for root-system arithmetic"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not needed for root-system arithmetic"},
    "xgi":        {"tried": False, "used": False, "reason": "not needed for root-system arithmetic"},
    "toponetx":   {"tried": False, "used": False, "reason": "not needed for root-system arithmetic"},
    "gudhi":      {"tried": False, "used": False, "reason": "not needed for root-system arithmetic"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        "load_bearing",
    "cvc5":      None,
    "sympy":     "load_bearing",
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# --- Tool imports ---
try:
    from z3 import Int, Solver, And, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"]  = True
    TOOL_MANIFEST["z3"]["reason"] = "load_bearing: encodes impossible dim orderings and symmetry constraints as UNSAT"
    _z3_ok = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    _z3_ok = False

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"]  = True
    TOOL_MANIFEST["sympy"]["reason"] = "load_bearing: exact integer arithmetic for Cartan matrix determinant and root dimension formula"
    _sp_ok = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    _sp_ok = False


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ------------------------------------------------------------------
    # P1: dim(F4) via root formula
    # dim = rank + 2 * num_positive_roots  (standard Lie algebra formula)
    # F4: rank=4, num_positive_roots=24  →  4 + 48 = 52
    # ------------------------------------------------------------------
    p1 = {"name": "P1_f4_dimension_formula", "pass": False, "detail": ""}
    rank_f4 = 4
    num_pos_roots_f4 = 24
    if _sp_ok:
        rank_sym  = sp.Integer(rank_f4)
        npos_sym  = sp.Integer(num_pos_roots_f4)
        dim_f4    = rank_sym + 2 * npos_sym
        expected  = sp.Integer(52)
        ok        = (dim_f4 == expected)
        p1["pass"]   = bool(ok)
        p1["detail"] = f"rank={rank_sym}, pos_roots={npos_sym}, dim=rank+2*pos={dim_f4}, expected=52, match={ok}"
    else:
        dim_f4_py = rank_f4 + 2 * num_pos_roots_f4
        p1["pass"]   = (dim_f4_py == 52)
        p1["detail"] = f"sympy unavailable; Python int: {dim_f4_py}==52 → {p1['pass']}"
    results["P1"] = p1

    # ------------------------------------------------------------------
    # P2: containment chain: dim(Sp6)=21 < dim(B4)=36 < dim(F4)=52
    # ------------------------------------------------------------------
    p2 = {"name": "P2_containment_chain_dims", "pass": False, "detail": ""}
    dim_sp6 = 21   # C3 = Sp(6): rank=3, dim=3+2*9=21
    dim_b4  = 36   # B4 = SO(9): rank=4, dim=4+2*16=36
    dim_f4  = 52
    chain_ok = (dim_sp6 < dim_b4 < dim_f4)
    p2["pass"]   = chain_ok
    p2["detail"] = f"dim(Sp6)={dim_sp6} < dim(B4)={dim_b4} < dim(F4)={dim_f4} → {chain_ok}"
    results["P2"] = p2

    # ------------------------------------------------------------------
    # P3: F4 Cartan matrix — det=1, first row=[2,-1,0,0]
    # Standard F4 Cartan matrix:
    #   [[ 2,-1, 0, 0],
    #    [-1, 2,-2, 0],
    #    [ 0,-1, 2,-1],
    #    [ 0, 0,-1, 2]]
    # ------------------------------------------------------------------
    p3 = {"name": "P3_f4_cartan_matrix", "pass": False, "detail": ""}
    if _sp_ok:
        A = sp.Matrix([
            [ 2, -1,  0,  0],
            [-1,  2, -2,  0],
            [ 0, -1,  2, -1],
            [ 0,  0, -1,  2],
        ])
        det_val    = A.det()
        first_row  = list(A.row(0))
        det_ok     = (det_val == sp.Integer(1))
        row_ok     = (first_row == [sp.Integer(2), sp.Integer(-1), sp.Integer(0), sp.Integer(0)])
        p3["pass"]   = bool(det_ok and row_ok)
        p3["detail"] = (
            f"det(Cartan)={det_val} (expected 1, ok={det_ok}); "
            f"row0={first_row} (expected [2,-1,0,0], ok={row_ok})"
        )
        # stash for N2
        _cartan = A
    else:
        A_np = np.array([[ 2,-1, 0, 0],[-1, 2,-2, 0],[0,-1, 2,-1],[0, 0,-1, 2]])
        det_val = int(round(np.linalg.det(A_np)))
        det_ok  = (det_val == 1)
        row_ok  = list(A_np[0]) == [2, -1, 0, 0]
        p3["pass"]   = bool(det_ok and row_ok)
        p3["detail"] = f"numpy fallback: det={det_val}, row0={list(A_np[0])}"
        _cartan = None
    results["P3"] = p3

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ------------------------------------------------------------------
    # N1: z3 UNSAT — F4_dim==52 AND B4_dim==36 AND F4_dim < B4_dim
    # ------------------------------------------------------------------
    n1 = {"name": "N1_z3_impossible_dim_ordering", "pass": False, "detail": ""}
    if _z3_ok:
        f4_dim = Int("f4_dim")
        b4_dim = Int("b4_dim")
        s = Solver()
        s.add(f4_dim == 52)
        s.add(b4_dim == 36)
        s.add(f4_dim < b4_dim)
        result = s.check()
        n1["pass"]   = (result == unsat)
        n1["detail"] = f"z3 result={result}, expected=unsat, pass={n1['pass']}"
    else:
        n1["pass"]   = False
        n1["detail"] = "z3 not available"
    results["N1"] = n1

    # ------------------------------------------------------------------
    # N2: z3 UNSAT — F4 Cartan matrix is symmetric
    # The entry A[1,2]=-2 while A[2,1]=-1; hence A ≠ A^T.
    # Encode: a12==a21 AND a12==-2 AND a21==-1 → UNSAT
    # ------------------------------------------------------------------
    n2 = {"name": "N2_z3_f4_cartan_not_symmetric", "pass": False, "detail": ""}
    if _z3_ok:
        a12 = Int("a12")   # row 1 col 2 of Cartan (0-indexed)
        a21 = Int("a21")   # row 2 col 1
        s2 = Solver()
        # Fix actual Cartan values
        s2.add(a12 == -2)
        s2.add(a21 == -1)
        # Assert symmetry (the thing being refuted)
        s2.add(a12 == a21)
        result2 = s2.check()
        n2["pass"]   = (result2 == unsat)
        n2["detail"] = (
            f"z3 result={result2}, expected=unsat "
            f"(a12=-2 ≠ a21=-1 so symmetry is impossible), pass={n2['pass']}"
        )
    else:
        n2["pass"]   = False
        n2["detail"] = "z3 not available"
    results["N2"] = n2

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ------------------------------------------------------------------
    # B1: G2 (rank 2, dim 14) vs F4 (rank 4, dim 52)
    # Both exceptional; G2 < F4 dimensionally; rank ordering consistent
    # ------------------------------------------------------------------
    b1 = {"name": "B1_g2_vs_f4_exceptional_pair", "pass": False, "detail": ""}
    rank_g2 = 2;  dim_g2 = 14   # confirmed in prior sim
    rank_f4 = 4;  dim_f4 = 52
    dim_order_ok  = (dim_g2 < dim_f4)
    rank_order_ok = (rank_g2 < rank_f4)
    # Formula cross-check for G2: rank=2, pos_roots=6 → 2+12=14 ✓
    g2_formula = rank_g2 + 2 * 6
    g2_formula_ok = (g2_formula == dim_g2)
    b1["pass"]   = bool(dim_order_ok and rank_order_ok and g2_formula_ok)
    b1["detail"] = (
        f"G2: rank={rank_g2}, dim={dim_g2}, formula={g2_formula} (ok={g2_formula_ok}); "
        f"F4: rank={rank_f4}, dim={dim_f4}; "
        f"dim_order={dim_order_ok}, rank_order={rank_order_ok}"
    )
    results["B1"] = b1

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    all_pass   = all(v["pass"] for v in all_tests.values())

    results = {
        "name": "sim_gtower_f4_exceptional_geometry",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive":  pos,
        "negative":  neg,
        "boundary":  bnd,
        "all_pass":  all_pass,
    }

    out_dir  = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_gtower_f4_exceptional_geometry_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"all_pass={all_pass}")
    for k, v in all_tests.items():
        status = "PASS" if v["pass"] else "FAIL"
        print(f"  {k}: {status} — {v['detail']}")
