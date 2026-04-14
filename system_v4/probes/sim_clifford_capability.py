#!/usr/bin/env python3
"""
sim_clifford_capability.py -- Tool-capability isolation sim for `clifford`.

Governing rule (owner+Hermes 2026-04-13):
clifford (Cl(3), Cl(6) rotor sandwich) is load_bearing across the geometry stack
but had no bounded capability probe. This is the isolation probe.

Decorative = `import clifford` with no rotor sandwich used for a claim.
Load-bearing = the rotor-sandwich output IS the claim (rotation of a vector, grade
projection, reversion).
"""

classification = "canonical"

import json
import math
import os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed -- pure GA probe"},
    "pyg":       {"tried": False, "used": False, "reason": "not graph-relevant"},
    "z3":        {"tried": False, "used": False, "reason": "not SMT-relevant"},
    "cvc5":      {"tried": False, "used": False, "reason": "not SMT-relevant"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed -- numeric GA"},
    "clifford":  {"tried": False, "used": False, "reason": "under test"},
    "geomstats": {"tried": False, "used": False, "reason": "separate geomstats probe"},
    "e3nn":      {"tried": False, "used": False, "reason": "separate e3nn probe"},
    "rustworkx": {"tried": False, "used": False, "reason": "not graph-relevant"},
    "xgi":       {"tried": False, "used": False, "reason": "not graph-relevant"},
    "toponetx":  {"tried": False, "used": False, "reason": "not topology-relevant"},
    "gudhi":     {"tried": False, "used": False, "reason": "not topology-relevant"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": "load_bearing",
    "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import clifford as cf
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "capability under test -- Cl(3)/Cl(6) rotor sandwich, grade projection, reversion"
    CLIFFORD_OK = True
    CLIFFORD_VERSION = getattr(cf, "__version__", "unknown")
except Exception as exc:
    CLIFFORD_OK = False
    CLIFFORD_VERSION = None
    TOOL_MANIFEST["clifford"]["reason"] = f"not installed: {exc}"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    r = {}
    if not CLIFFORD_OK:
        r["clifford_available"] = {"pass": False, "detail": "clifford missing"}
        return r
    r["clifford_available"] = {"pass": True, "version": CLIFFORD_VERSION}

    # Cl(3,0).
    layout3, blades3 = cf.Cl(3)
    e1, e2, e3 = blades3["e1"], blades3["e2"], blades3["e3"]

    # 1. Rotor sandwich: rotate e1 by 90deg in the e1^e2 plane -> e2.
    B = e1 ^ e2                       # bivector
    theta = math.pi / 2
    R = math.cos(theta / 2) - math.sin(theta / 2) * B   # unit rotor
    v = 1.0 * e1
    v_rot = R * v * ~R                 # sandwich, ~R is reverse
    # Expected ~ e2.
    target = 1.0 * e2
    diff = (v_rot - target)
    err = float(abs(diff))
    r["rotor_sandwich_90deg"] = {
        "pass": err < 1e-9,
        "err": err,
        "result": str(v_rot),
        "expected": str(target),
    }

    # 2. Rotor composition associativity: (R2*R1)*v*~(R2*R1) == R2*(R1*v*~R1)*~R2.
    B12 = e1 ^ e2
    B23 = e2 ^ e3
    a1, a2 = math.pi / 3, math.pi / 5
    R1 = math.cos(a1 / 2) - math.sin(a1 / 2) * B12
    R2 = math.cos(a2 / 2) - math.sin(a2 / 2) * B23
    v = 1.0 * e1 + 2.0 * e2 - 0.5 * e3
    lhs = (R2 * R1) * v * ~(R2 * R1)
    rhs = R2 * (R1 * v * ~R1) * ~R2
    r["rotor_composition_associative"] = {
        "pass": float(abs(lhs - rhs)) < 1e-9,
        "err": float(abs(lhs - rhs)),
    }

    # 3. Cl(6) basis + grade projection: bivector squared gives scalar + grade-4.
    layout6, blades6 = cf.Cl(6)
    f1, f2 = blades6["e1"], blades6["e2"]
    Bf = f1 ^ f2
    Bsq = Bf * Bf
    grade0 = Bsq(0)
    grade2 = Bsq(2)
    r["cl6_bivector_square"] = {
        "pass": float(abs(grade0 - (-1.0))) < 1e-9 and float(abs(grade2)) < 1e-9,
        "grade0": float(grade0[0]) if hasattr(grade0, "__getitem__") else float(grade0),
        "grade2_norm": float(abs(grade2)),
    }

    # 4. Reversion identity: ~(A*B) == (~B)*(~A).
    A = 2.0 + 3.0 * e1 + 1.5 * (e1 ^ e2)
    B_mv = 1.0 - 0.5 * e2 + 2.0 * (e2 ^ e3)
    lhs2 = ~(A * B_mv)
    rhs2 = (~B_mv) * (~A)
    r["reversion_antihomomorphism"] = {
        "pass": float(abs(lhs2 - rhs2)) < 1e-9,
        "err": float(abs(lhs2 - rhs2)),
    }

    return r


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    r = {}
    if not CLIFFORD_OK:
        r["clifford_available"] = {"pass": False, "detail": "clifford missing"}
        return r

    layout3, blades3 = cf.Cl(3)
    e1, e2, e3 = blades3["e1"], blades3["e2"], blades3["e3"]

    # 1. Non-commutativity: e1*e2 != e2*e1 (they anticommute).
    lhs = e1 * e2
    rhs = e2 * e1
    r["basis_anticommute"] = {
        "pass": float(abs(lhs + rhs)) < 1e-9 and float(abs(lhs - rhs)) > 1e-6,
        "sum_norm": float(abs(lhs + rhs)),
        "diff_norm": float(abs(lhs - rhs)),
    }

    # 2. Bad blade name must raise KeyError.
    raised = False
    err = None
    try:
        _ = blades3["e99"]
    except Exception as exc:
        raised = True
        err = type(exc).__name__
    r["bad_blade_raises"] = {"pass": raised, "error_type": err}

    # 3. Non-rotor sandwich does NOT preserve vector grade in general.
    # A pure scalar multiplier leaves grade alone but a non-unit multivector
    # with mixed grades changes the grade content. Confirm: M*v*M != pure grade-1
    # when M has grade-0 + grade-2 mixing without unit normalization.
    M = 1.0 + 0.4 * (e1 ^ e2) + 0.3 * (e2 ^ e3)   # not a unit rotor
    v = 1.0 * e1
    out = M * v * M
    grade1 = out(1)
    # Expect nonzero non-grade-1 content (grade 3 trivector part).
    grade3 = out(3)
    r["non_rotor_breaks_grade_preservation"] = {
        "pass": float(abs(grade3)) > 1e-9,
        "grade3_norm": float(abs(grade3)),
        "grade1_norm": float(abs(grade1)),
    }

    return r


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    r = {}
    if not CLIFFORD_OK:
        r["clifford_available"] = {"pass": False, "detail": "clifford missing"}
        return r

    layout3, blades3 = cf.Cl(3)
    e1, e2, e3 = blades3["e1"], blades3["e2"], blades3["e3"]

    # 1. Scalar edge case: scalar * vector is still pure grade 1.
    s = 3.5 + 0 * e1
    v = 1.0 * e1 + 2.0 * e2
    out = s * v
    grade_other = out - out(1)
    r["scalar_vector_pure_grade1"] = {
        "pass": float(abs(grade_other)) < 1e-12,
        "other_grade_norm": float(abs(grade_other)),
    }

    # 2. Pseudo-scalar I = e1*e2*e3 in Cl(3) squares to -1.
    I = e1 * e2 * e3
    Isq = I * I
    val = float(Isq[0])
    r["pseudoscalar_square_minus_one"] = {
        "pass": abs(val + 1.0) < 1e-9,
        "value": val,
    }

    # 3. Identity rotor: theta=0 leaves vector unchanged.
    R0 = math.cos(0) - math.sin(0) * (e1 ^ e2)   # = 1
    v = 1.0 * e1 + 2.0 * e3
    r["identity_rotor_no_op"] = {
        "pass": float(abs(R0 * v * ~R0 - v)) < 1e-12,
    }

    # 4. 360deg rotor is -1 (double-cover): R(2pi)*v*~R(2pi) == v (but R != 1).
    theta = 2 * math.pi
    B = e1 ^ e2
    R2pi = math.cos(theta / 2) - math.sin(theta / 2) * B
    v = 1.0 * e1
    v_out = R2pi * v * ~R2pi
    # R(2pi) has scalar part approx -1.
    scalar_part = float(R2pi[0])
    r["double_cover_2pi"] = {
        "pass": float(abs(v_out - v)) < 1e-9 and abs(scalar_part + 1.0) < 1e-9,
        "scalar_part": scalar_part,
        "v_err": float(abs(v_out - v)),
    }

    return r


# =====================================================================
# MAIN
# =====================================================================

def _all_pass(section):
    return all(bool(v.get("pass", False)) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_clifford_capability",
        "purpose": "Tool-capability isolation probe for clifford -- Cl(3)/Cl(6) rotor sandwich, grade projection, reversion.",
        "clifford_version": CLIFFORD_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "witness_file": "system_v4/probes/sim_assoc_bundle_weyl_spinor_as_section.py",
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "clifford_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
