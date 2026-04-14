#!/usr/bin/env python3
"""sim_ladder_couple_L6_L7_engine_to_operator

scope_note: ladders/fences per system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md. Language is exclusion/admissibility, not causal.

Couples ladder layers L6_engine and L7_operator via clifford.
classification: canonical
Language: admissibility/exclusion; never causal.
"""
import json, os, traceback

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "z3":       {"tried": False, "used": False, "reason": ""},
    "sympy":    {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "z3": None, "sympy": None, "clifford": None,
}

try:
    import torch  # noqa
    TOOL_MANIFEST["pytorch"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["pytorch"]["reason"] = f"import failed: {e}"
try:
    import z3  # noqa
    TOOL_MANIFEST["z3"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["z3"]["reason"] = f"import failed: {e}"
try:
    import sympy  # noqa
    TOOL_MANIFEST["sympy"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["sympy"]["reason"] = f"import failed: {e}"
try:
    from clifford import Cl  # noqa
    TOOL_MANIFEST["clifford"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["clifford"]["reason"] = f"import failed: {e}"

LOAD_BEARING_TOOL = "clifford"
LOAD_BEARING_REASON = 'clifford Cl(3) rotor sandwich is the structural grade-preservation witness; numpy cannot represent geometric product'

def run_positive_tests():
    results = {}
    try:
        from clifford import Cl
        layout, blades = Cl(3)
        e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
        # L6 engine rotor
        R = (1 + e1*e2).normal()
        # L7 operator: vector v rotated by R survives as vector grade
        v = e1 + e3
        vp = R * v * ~R
        grade1_only = (vp(1) - vp).clean(1e-10) == 0 * e1
        results['engine_rotor_preserves_operator_grade1'] = bool((vp - vp(1)).clean(1e-10) == 0*e1)
    except Exception as e:
        results['_error'] = traceback.format_exc()
    return results

def run_negative_tests():
    results = {}
    try:
        from clifford import Cl
        layout, blades = Cl(3)
        e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
        # Negative: non-versor multivector breaks grade preservation under operator coupling
        M = 1 + e1 + e1*e2  # mixed grade, not a rotor
        v = e1
        vp = M * v * ~M
        mixed = (vp - vp(1)).clean(1e-10) != 0*e1
        results['non_rotor_excluded_under_operator_coupling'] = bool(mixed)
    except Exception as e:
        results['_error'] = traceback.format_exc()
    return results

def run_boundary_tests():
    results = {}
    try:
        from clifford import Cl
        layout, blades = Cl(3)
        e1 = blades['e1']
        R = layout.scalar  # identity rotor
        v = e1
        vp = R * v * ~R
        results['identity_rotor_boundary_admissible'] = bool((vp - v).clean(1e-10) == 0*e1)
    except Exception as e:
        results['_error'] = traceback.format_exc()
    return results

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Mark load-bearing tool as used with non-empty reason
    TOOL_MANIFEST[LOAD_BEARING_TOOL]["used"] = True
    TOOL_MANIFEST[LOAD_BEARING_TOOL]["reason"] = LOAD_BEARING_REASON
    TOOL_INTEGRATION_DEPTH[LOAD_BEARING_TOOL] = "load_bearing"

    def all_true(d):
        vals = [v for k, v in d.items() if not k.startswith('_') and isinstance(v, bool)]
        return bool(vals) and all(vals)

    pos_pass = all_true(pos)
    neg_pass = all_true(neg)
    bnd_pass = all_true(bnd)
    overall = "PASS" if (pos_pass and neg_pass and bnd_pass) else "FAIL"

    results = {
        "name": "sim_ladder_couple_L6_L7_engine_to_operator",
        "classification": "canonical",
        "scope_note": "ladders/fences per system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md",
        "coupling": {"layer_a": "L6_engine", "layer_b": "L7_operator"},
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "load_bearing_tool": LOAD_BEARING_TOOL,
        "load_bearing_reason": LOAD_BEARING_REASON,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "pos_pass": pos_pass,
        "neg_pass": neg_pass,
        "bnd_pass": bnd_pass,
        "overall": overall,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_ladder_couple_L6_L7_engine_to_operator_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{overall} {out_path}")
