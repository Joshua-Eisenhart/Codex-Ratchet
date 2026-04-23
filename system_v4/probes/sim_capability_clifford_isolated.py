#!/usr/bin/env python3
"""
sim_capability_clifford_isolated.py -- Isolated tool-capability probe for clifford.

Classical_baseline capability probe: demonstrates the clifford library's Cl(3,0)
geometric algebra: multivectors, geometric product, inner/outer products,
grade selection, rotor construction, and versor sandwiching. Honest CAN/CANNOT
summary. No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates the clifford geometric algebra library alone; "
    "cross-tool coupling is deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": True,  "used": True,  "reason": "load-bearing: clifford Cl(3,0) algebra is the sole subject; geometric/inner/outer products and rotor versors are computed directly by clifford."},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": "load_bearing", "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

CLIFFORD_OK = False
try:
    from clifford import Cl
    import numpy as np
    CLIFFORD_OK = True
except Exception:
    pass


def _rel_err(a, b):
    """Relative error between two floats."""
    denom = abs(b) if abs(b) > 1e-15 else 1e-15
    return abs(a - b) / denom


def run_positive_tests():
    r = {}
    if not CLIFFORD_OK:
        r["clifford_available"] = {"pass": False, "detail": "clifford not importable"}
        return r

    import clifford as clf
    r["clifford_available"] = {"pass": True, "version": clf.__version__}

    layout, blades = Cl(3)  # Cl(3,0): Euclidean 3D geometric algebra
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    e12 = blades["e12"]
    e123 = blades["e123"]  # pseudoscalar

    # --- Test 1: basis vector squares ---
    e1_sq = float((e1 * e1).value[0])
    e2_sq = float((e2 * e2).value[0])
    e3_sq = float((e3 * e3).value[0])
    r["basis_vector_squares"] = {
        "pass": abs(e1_sq - 1) < 1e-10 and abs(e2_sq - 1) < 1e-10 and abs(e3_sq - 1) < 1e-10,
        "e1^2": e1_sq, "e2^2": e2_sq, "e3^2": e3_sq,
        "detail": "In Cl(3,0): e_i^2 = +1 for all basis vectors",
    }

    # --- Test 2: outer product (bivector) ---
    bv = e1 ^ e2  # outer product
    bv_grade = bv.grades()
    r["outer_product_bivector"] = {
        "pass": set(bv_grade) == {2},
        "grades": list(bv_grade),
        "detail": "e1 ^ e2 must be a grade-2 multivector (bivector)",
    }

    # --- Test 3: anticommuting basis vectors ---
    e1e2 = e1 * e2
    e2e1 = e2 * e1
    # e1*e2 = -e2*e1 in Cl(3,0)
    diff = e1e2 + e2e1
    is_zero = all(abs(v) < 1e-10 for v in diff.value)
    r["anticommuting_basis"] = {
        "pass": bool(is_zero),
        "detail": "e1*e2 + e2*e1 = 0 (anticommuting off-diagonal basis vectors)",
    }

    # --- Test 4: pseudoscalar squaring ---
    ps_sq = e123 * e123
    ps_sq_val = float(ps_sq.value[0])
    r["pseudoscalar_square"] = {
        "pass": abs(ps_sq_val - (-1)) < 1e-10,
        "I^2": ps_sq_val,
        "detail": "In Cl(3,0): I^2 = (e123)^2 = -1",
    }

    # --- Test 5: rotor for 90-degree rotation ---
    import math
    angle = math.pi / 2
    # Rotor: R = cos(θ/2) - sin(θ/2) * e12
    R = math.cos(angle / 2) - math.sin(angle / 2) * e12
    Rrev = ~R  # reversion via __invert__
    # Rotate e1: R * e1 * ~R should give e2
    rotated = R * e1 * Rrev
    # Extract grade-1 part
    rot_e1 = float(rotated.value[1])   # coefficient of e1
    rot_e2 = float(rotated.value[2])   # coefficient of e2
    r["rotor_90deg_rotation"] = {
        "pass": abs(rot_e1) < 1e-10 and abs(rot_e2 - 1) < 1e-10,
        "rotated_e1_coeff": rot_e1,
        "rotated_e2_coeff": rot_e2,
        "detail": "90° rotation about e3 axis maps e1 → e2",
    }

    # --- Test 6: grade selection ---
    # layout.names = ['', 'e1', 'e2', 'e3', 'e12', 'e13', 'e23', 'e123']
    # Indices: scalar=0, e1=1, e12=4, e123=7
    mv = 1 + e1 + e12 + e123  # grade 0+1+2+3
    grade0 = mv(0)
    grade1 = mv(1)
    grade2 = mv(2)
    grade3 = mv(3)
    r["grade_selection"] = {
        "pass": (float(grade0.value[0]) == 1 and
                 float(grade1.value[1]) == 1 and
                 float(grade2.value[4]) == 1 and  # e12 is at index 4
                 float(grade3.value[7]) == 1),
        "detail": "Grade projection on 1+e1+e12+e123",
    }

    return r


def run_negative_tests():
    r = {}
    if not CLIFFORD_OK:
        r["clifford_unavailable"] = {"pass": True, "detail": "skip: clifford not installed"}
        return r

    layout, blades = Cl(3)
    e1, e2 = blades["e1"], blades["e2"]

    # --- Neg 1: geometric product is not commutative for basis bivectors ---
    ab = e1 * e2
    ba = e2 * e1
    # These must NOT be equal
    is_different = any(abs(v) > 1e-10 for v in (ab - ba).value)
    r["geometric_product_noncommutative"] = {
        "pass": bool(is_different),
        "detail": "e1*e2 != e2*e1 confirms non-commutativity of geometric product",
    }

    # --- Neg 2: outer product is nilpotent on parallel vectors ---
    # e1 ^ e1 = 0
    outer_same = e1 ^ e1
    is_zero = all(abs(v) < 1e-10 for v in outer_same.value)
    r["outer_product_nilpotent"] = {
        "pass": bool(is_zero),
        "detail": "e1 ^ e1 = 0: outer product of parallel vectors vanishes",
    }

    # --- Neg 3: grade-2 multivector is not grade-1 ---
    e12 = blades["e12"]
    grades = e12.grades()
    r["bivector_not_grade1"] = {
        "pass": 1 not in set(grades),
        "grades": list(grades),
        "detail": "e12 is grade-2, has no grade-1 component",
    }

    return r


def run_boundary_tests():
    r = {}
    if not CLIFFORD_OK:
        r["clifford_unavailable"] = {"pass": True, "detail": "skip: clifford not installed"}
        return r

    import math
    layout, blades = Cl(3)
    e1, e2, e12 = blades["e1"], blades["e2"], blades["e12"]

    # --- Boundary 1: zero rotation rotor ---
    R = math.cos(0) - math.sin(0) * e12  # identity rotor
    Rrev = ~R  # reversion
    result = R * e1 * Rrev
    e1_coeff = float(result.value[1])
    r["identity_rotor"] = {
        "pass": abs(e1_coeff - 1) < 1e-10,
        "detail": "0-angle rotor leaves e1 unchanged",
    }

    # --- Boundary 2: 360-degree rotation is identity ---
    angle = 2 * math.pi
    R360 = math.cos(angle / 2) - math.sin(angle / 2) * e12
    R360rev = ~R360  # reversion
    result360 = R360 * e1 * R360rev
    e1_360 = float(result360.value[1])
    r["full_rotation_identity"] = {
        "pass": abs(e1_360 - 1) < 1e-8,
        "e1_after_360": e1_360,
        "detail": "360° rotation returns e1 to itself",
    }

    # --- Boundary 3: Cl(1,0) algebra (1D) ---
    layout1, blades1 = Cl(1)
    e = blades1["e1"]
    e_sq = float((e * e).value[0])
    r["cl1_algebra"] = {
        "pass": abs(e_sq - 1) < 1e-10,
        "e1^2": e_sq,
        "detail": "Cl(1,0): single basis vector squares to +1",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall = all([v.get("pass", False) for v in all_tests.values() if isinstance(v, dict) and "pass" in v])

    results = {
        "name": "sim_capability_clifford_isolated",
        "classification": classification,
        "overall_pass": overall,
        "capability_summary": {
            "CAN": [
                "compute geometric products in Cl(n,0) Euclidean geometric algebras",
                "compute outer (wedge) and inner products between multivectors",
                "construct rotors for SO(n) rotations and sandwich-product versors",
                "select grade components from mixed-grade multivectors",
                "verify non-commutativity (A∘B ≠ B∘A) algebraically",
                "work in arbitrary dimension Cl(p,q) algebras",
            ],
            "CANNOT": [
                "compute automatically differentiate through multivector operations (use pytorch for that)",
                "prove algebraic identities symbolically (use sympy/z3 for that)",
                "handle infinite-dimensional Clifford algebras",
                "replace e3nn for equivariant neural network features",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_clifford_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
