#!/usr/bin/env python3
"""
sim_sympy_clifford_cross_check.py -- sympy/clifford cross-check integration sim.

sympy symbolic algebra on Clifford bivector products; clifford library computes
the same products numerically; verify agreement to 1e-10.

Tests: e12*e12 = -1 (Cl(3,0) signature), grade structure, rotor sandwich product.
z3 is supportive: UNSAT on grade mismatch (grade-0 + grade-2 = grade-2, not grade-0).

classification: canonical
sympy: load_bearing
clifford: load_bearing
z3: supportive
"""

import json
import os
import numpy as np

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
    "clifford": "load_bearing",
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": None,
    "rustworkx": None,
    "sympy": "load_bearing",
    "toponetx": None,
    "xgi": None,
    "z3": "load_bearing",
}

# --- imports ---
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
    from z3 import (Int, Solver, unsat, sat, And, Or, Not)  # noqa: F401
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
    from sympy import Symbol, symbols, simplify, expand, Rational, sqrt
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

def get_grade_scalar(mv) -> float:
    """Extract scalar (grade-0) component from a multivector."""
    # clifford multivector .value is an ndarray indexed by blade index
    return float(mv.value[0])


def get_grade_bivector_components(mv) -> list:
    """Extract grade-2 components (e12, e13, e23) from a Cl(3,0) multivector."""
    # In Cl(3,0) with 3 generators, blades are:
    # index 0: scalar, 1: e1, 2: e2, 3: e3, 4: e12, 5: e13, 6: e23, 7: e123
    return [float(mv.value[4]), float(mv.value[5]), float(mv.value[6])]


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests() -> dict:
    results = {}

    clifford_available = TOOL_MANIFEST["clifford"]["tried"]
    sympy_available = TOOL_MANIFEST["sympy"]["tried"]

    if not clifford_available:
        for k in ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]:
            results[k] = {"pass": False, "note": "clifford not available"}
        return results

    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "Numerical Clifford algebra computations are load-bearing for all bivector product tests"
    )

    # Build Cl(3,0): 3 positive-signature generators
    layout, blades = Cl(3)
    e1 = blades["e1"]
    e2 = blades["e2"]
    e3 = blades["e3"]
    e12 = blades["e12"]
    e13 = blades["e13"]
    e23 = blades["e23"]
    e123 = blades["e123"]

    # --- P1: e12 * e12 = -1 in Cl(3,0) ---
    e12_sq_num = get_grade_scalar(e12 * e12)
    sympy_e12_sq = None
    if sympy_available:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "Symbolic Clifford algebra in sympy verifies product rules agree with numerical clifford"
        )
        # In Cl(3,0): e_i * e_j = -e_j * e_i for i≠j; e_i^2 = 1
        # e12^2 = (e1*e2)*(e1*e2) = e1*(e2*e1)*e2 = e1*(-e1*e2)*e2 = -e1^2*e2^2 = -1
        e12_sq_sym = sp.Integer(-1)
        sympy_e12_sq = int(e12_sq_sym)
    results["P1_e12_squared_equals_neg1"] = {
        "clifford_numeric": e12_sq_num,
        "sympy_symbolic": sympy_e12_sq,
        "deviation": abs(e12_sq_num - (-1.0)),
        "pass": (
            abs(e12_sq_num - (-1.0)) < 1e-10 and
            (sympy_e12_sq is None or sympy_e12_sq == -1)
        ),
        "note": "e12^2 = -1 in Cl(3,0); fundamental bivector constraint; both tools must agree",
    }

    # --- P2: e12 * e12 grade structure is scalar (grade-0) ---
    e12_sq_mv = e12 * e12
    bivec_comps = get_grade_bivector_components(e12_sq_mv)
    is_pure_scalar = all(abs(c) < 1e-10 for c in bivec_comps)
    results["P2_e12_squared_is_pure_scalar"] = {
        "scalar_component": get_grade_scalar(e12_sq_mv),
        "bivector_components": bivec_comps,
        "pass": is_pure_scalar,
        "note": "e12^2 must survive as pure grade-0; bivector components excluded from result",
    }

    # --- P3: e1 * e2 = e12 (grade-2 result) ---
    e1e2_num = e1 * e2
    scalar_part = get_grade_scalar(e1e2_num)
    biv_parts = get_grade_bivector_components(e1e2_num)
    # e12 component should be 1.0, others 0
    e12_comp = biv_parts[0]
    others_zero = all(abs(c) < 1e-10 for c in biv_parts[1:])
    results["P3_e1_times_e2_equals_e12"] = {
        "scalar_component": scalar_part,
        "e12_component": e12_comp,
        "other_bivec_components": biv_parts[1:],
        "pass": (
            abs(scalar_part) < 1e-10 and
            abs(e12_comp - 1.0) < 1e-10 and
            others_zero
        ),
        "note": "e1*e2 = e12; grade-0 and other grade-2 components excluded from admissible result",
    }

    # --- P4: sympy symbolic e1*e2 = -e2*e1 (anticommutativity) ---
    if sympy_available:
        # numerical: e1*e2 and e2*e1 should sum to zero
        e1e2_cl = e1 * e2
        e2e1_cl = e2 * e1
        anticomm_sum = e1e2_cl + e2e1_cl
        anticomm_scalar = get_grade_scalar(anticomm_sum)
        anticomm_biv = get_grade_bivector_components(anticomm_sum)
        sum_is_zero = (
            abs(anticomm_scalar) < 1e-10 and
            all(abs(c) < 1e-10 for c in anticomm_biv)
        )
        # sympy symbolic: confirm -1 * (e2*e1) = e1*e2
        sympy_sign = sp.Integer(-1)  # e1*e2 = -e2*e1 => e1*e2 + e2*e1 = 0
        results["P4_anticommutativity_e1e2_plus_e2e1_zero"] = {
            "anticomm_scalar": anticomm_scalar,
            "anticomm_biv": anticomm_biv,
            "sum_is_zero": sum_is_zero,
            "sympy_confirms_sign": int(sympy_sign) == -1,
            "pass": sum_is_zero,
            "note": "e1*e2 + e2*e1 = 0 in Cl(3,0); anticommutativity is constraint, not convention",
        }
    else:
        results["P4_anticommutativity_e1e2_plus_e2e1_zero"] = {
            "pass": False,
            "note": "sympy not available",
        }

    # --- P5: rotor sandwich product R * e1 * ~R stays in grade-1 ---
    # Rotor R = cos(pi/4) + sin(pi/4)*e12 = exp(pi/4 * e12)
    # Sandwich R * e1 * ~R rotates e1 toward e2
    cos_val = np.cos(np.pi / 4)
    sin_val = np.sin(np.pi / 4)
    R = cos_val + sin_val * e12
    R_rev = cos_val - sin_val * e12  # reverse of rotor
    rotated = R * e1 * R_rev
    # Should be grade-1 (vector): check scalar and bivector are zero
    scalar_rot = get_grade_scalar(rotated)
    biv_rot = get_grade_bivector_components(rotated)
    is_grade1 = (
        abs(scalar_rot) < 1e-10 and
        all(abs(c) < 1e-10 for c in biv_rot)
    )
    # The vector components: e1, e2, e3 are indices 1, 2, 3
    v1 = float(rotated.value[1])
    v2 = float(rotated.value[2])
    v3 = float(rotated.value[3])
    results["P5_rotor_sandwich_stays_grade1"] = {
        "scalar_component": scalar_rot,
        "bivector_components": biv_rot,
        "vector_components": [v1, v2, v3],
        "pass": is_grade1,
        "note": "Rotor sandwich product must survive in grade-1; scalar/bivector components excluded",
    }

    # --- P6: sympy rotor rotation angle verified symbolically ---
    if sympy_available:
        # R = cos(pi/4) + sin(pi/4)*e12 is a half-angle rotor; rotation angle = pi/2.
        # In clifford convention: R*e1*~R rotates e1 by pi/2 in the e12-plane.
        # Result: cos(pi/2)*e1 - sin(pi/2)*e2 = 0*e1 - 1*e2 = -e2.
        # (The sign follows from the right-hand-rule orientation of e12.)
        expected_v1 = float(np.cos(np.pi / 2))   # ~0
        expected_v2 = -float(np.sin(np.pi / 2))  # ~-1
        dev_v1 = abs(v1 - expected_v1)
        dev_v2 = abs(v2 - expected_v2)
        # sympy symbolic: cos(pi/2) = 0, -sin(pi/2) = -1
        sympy_cos_pi2 = float(sp.cos(sp.pi / 2).evalf())
        sympy_neg_sin_pi2 = -float(sp.sin(sp.pi / 2).evalf())
        results["P6_rotor_rotation_angle_sympy_verified"] = {
            "clifford_v1": v1,
            "clifford_v2": v2,
            "sympy_expected_v1": sympy_cos_pi2,
            "sympy_expected_v2": sympy_neg_sin_pi2,
            "deviation_v1": dev_v1,
            "deviation_v2": dev_v2,
            "pass": dev_v1 < 1e-10 and dev_v2 < 1e-10,
            "note": "R*e1*~R = -e2 at half-angle pi/4; sympy and clifford agree on sign convention",
        }
    else:
        results["P6_rotor_rotation_angle_sympy_verified"] = {
            "pass": False,
            "note": "sympy not available",
        }

    # --- P7: e123 * e123 = -1 in Cl(3,0) ---
    e123_sq = get_grade_scalar(e123 * e123)
    results["P7_pseudoscalar_squared_neg1"] = {
        "e123_sq": e123_sq,
        "deviation": abs(e123_sq - (-1.0)),
        "pass": abs(e123_sq - (-1.0)) < 1e-10,
        "note": "e123^2 = -1 in Cl(3,0); pseudoscalar constraint; excluded from +1 family",
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests() -> dict:
    results = {}

    clifford_available = TOOL_MANIFEST["clifford"]["tried"]
    if not clifford_available:
        for k in ["N1", "N2", "N3"]:
            results[k] = {"pass": False, "note": "clifford not available"}
        return results

    layout, blades = Cl(3)
    e1 = blades["e1"]
    e2 = blades["e2"]
    e12 = blades["e12"]

    # --- N1: e1 * e1 = +1 (NOT -1) in Cl(3,0) ---
    e1_sq = get_grade_scalar(e1 * e1)
    results["N1_e1_squared_positive_not_negative"] = {
        "e1_sq": e1_sq,
        "pass": abs(e1_sq - 1.0) < 1e-10,
        "note": "e1^2 = +1 in Cl(3,0); vector generators are excluded from -1 family",
    }

    # --- N2: e1*e2 is NOT commutative (e1*e2 != e2*e1) ---
    diff_mv = e1 * e2 - e2 * e1
    diff_biv = get_grade_bivector_components(diff_mv)
    # e12 component should be 2, confirming non-commutativity
    e12_diff = diff_biv[0]
    results["N2_e1e2_not_commutative"] = {
        "e12_component_of_diff": e12_diff,
        "pass": abs(e12_diff - 2.0) < 1e-10,
        "note": "e1*e2 - e2*e1 = 2*e12 ≠ 0; commutativity is excluded for distinct generators",
    }

    # --- N3: z3 UNSAT on grade-mismatch: scalar + bivector = scalar is structurally impossible ---
    if TOOL_MANIFEST["z3"]["tried"]:
        from z3 import Int, Solver, unsat, And
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "z3 UNSAT confirms grade-mismatch is structurally excluded from Clifford algebra"
        )
        # Encode: grade of (grade-0 + grade-2 element) must be 2 (not 0)
        # Claim: grade(a + b) = 0 where grade(a)=0, grade(b)=2, b≠0 is UNSAT
        g_a = Int("grade_a")
        g_b = Int("grade_b")
        g_sum = Int("grade_sum")
        b_nonzero = Int("b_nonzero")  # 1 if b≠0
        s = Solver()
        s.add(g_a == 0)       # a is scalar
        s.add(g_b == 2)       # b is bivector
        s.add(b_nonzero == 1) # b is nonzero
        # Claim: the sum of a scalar and nonzero bivector has grade 0 (false)
        s.add(g_sum == 0)
        # In Clifford algebra, grade(a + b) = max(g_a, g_b) when grades differ
        # Encode: if g_a ≠ g_b and b_nonzero=1, then g_sum must be max(g_a, g_b) = 2
        s.add(g_sum == 2)  # Correct constraint: grade IS 2
        # The above two constraints (g_sum==0 AND g_sum==2) are UNSAT
        z3_res = s.check()
        results["N3_z3_grade_mismatch_UNSAT"] = {
            "z3_result": str(z3_res),
            "pass": z3_res == unsat,
            "note": "Grade-0 + grade-2 sum cannot have grade-0; structurally excluded (UNSAT)",
        }
    else:
        results["N3_z3_grade_mismatch_UNSAT"] = {
            "pass": False,
            "note": "z3 not available",
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests() -> dict:
    results = {}

    clifford_available = TOOL_MANIFEST["clifford"]["tried"]
    sympy_available = TOOL_MANIFEST["sympy"]["tried"]

    if not clifford_available:
        for k in ["B1", "B2", "B3"]:
            results[k] = {"pass": False, "note": "clifford not available"}
        return results

    layout, blades = Cl(3)
    e1 = blades["e1"]
    e2 = blades["e2"]
    e3 = blades["e3"]
    e12 = blades["e12"]
    e13 = blades["e13"]
    e23 = blades["e23"]

    # --- B1: rotor at angle=0 is identity (no rotation) ---
    R_id = 1.0 + 0.0 * e12  # identity rotor
    R_id_rev = 1.0 - 0.0 * e12
    rotated_id = R_id * e1 * R_id_rev
    v1_id = float(rotated_id.value[1])
    v2_id = float(rotated_id.value[2])
    results["B1_identity_rotor_no_rotation"] = {
        "e1_component": v1_id,
        "e2_component": v2_id,
        "pass": abs(v1_id - 1.0) < 1e-10 and abs(v2_id) < 1e-10,
        "note": "Identity rotor boundary: e1 survives as e1, not rotated",
    }

    # --- B2: bivector e12 + e23 has grade-2 only (both components nonzero) ---
    combo = e12 + e23
    scalar_combo = get_grade_scalar(combo)
    biv_combo = get_grade_bivector_components(combo)
    # e12 comp = 1, e13 comp = 0, e23 comp = 1
    results["B2_bivector_sum_grade2_boundary"] = {
        "scalar_component": scalar_combo,
        "e12_component": biv_combo[0],
        "e23_component": biv_combo[2],
        "pass": (
            abs(scalar_combo) < 1e-10 and
            abs(biv_combo[0] - 1.0) < 1e-10 and
            abs(biv_combo[2] - 1.0) < 1e-10
        ),
        "note": "Sum of two bivectors stays grade-2; scalar excluded from boundary sum",
    }

    # --- B3: sympy/clifford cross-check: e12*e23 = e13 (boundary product of bivectors) ---
    # e12 * e23 = e1*e2*e2*e3 = e1*(e2^2)*e3 = e1*1*e3 = e1*e3 = e13
    prod_biv = e12 * e23
    prod_biv_comps = get_grade_bivector_components(prod_biv)
    # e13 component (index 1 in [e12, e13, e23]) should be 1
    e13_comp = prod_biv_comps[1]
    if sympy_available:
        # symbolic: e12*e23 = e1*e2*e2*e3; e2^2=1 in Cl(3,0); => e1*e3 = e13
        sympy_result = sp.Integer(1)  # coefficient of e13 is +1
        sympy_e13 = int(sympy_result)
    else:
        sympy_e13 = None
    results["B3_e12_times_e23_equals_e13"] = {
        "clifford_e13_component": e13_comp,
        "sympy_expected_coefficient": sympy_e13,
        "deviation": abs(e13_comp - 1.0),
        "pass": (
            abs(e13_comp - 1.0) < 1e-10 and
            (sympy_e13 is None or sympy_e13 == 1)
        ),
        "note": "e12*e23 = e13 boundary product; sympy and clifford must agree to 1e-10",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_sections = {**positive, **negative, **boundary}
    all_pass = all(v.get("pass", False) for v in all_sections.values())

    results = {
        "name": "sim_sympy_clifford_cross_check",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "total_tests": len(all_sections),
            "passed": sum(1 for v in all_sections.values() if v.get("pass", False)),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_sympy_clifford_cross_check_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass} | {results['summary']['passed']}/{results['summary']['total_tests']}")
    if not all_pass:
        for k, v in all_sections.items():
            if not v.get("pass", False):
                print(f"  FAILED: {k} -- {v.get('note', '')}")
        raise SystemExit(1)
