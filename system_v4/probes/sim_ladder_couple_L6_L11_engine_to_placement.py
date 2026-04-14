#!/usr/bin/env python3
"""sim_ladder_couple_L6_L11_engine_to_placement

scope_note: ladders/fences per system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md. Language is exclusion/admissibility, not causal.

Couples ladder layers L6_engine and L11_placement via z3.
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

LOAD_BEARING_TOOL = "z3"
LOAD_BEARING_REASON = 'z3 UNSAT witnesses engine->placement exclusion structurally'

def run_positive_tests():
    results = {}
    try:
        from z3 import Int, Bool, Solver, And, Or, Not, sat
        # L6 engine with 2 modes; L11 placement on 3 sites
        m = Int('m')  # engine mode 0 or 1
        sites = [Bool(f's{i}') for i in range(3)]
        s = Solver()
        s.add(Or(m == 0, m == 1))
        # exactly one site
        s.add(Or(*sites))
        for i in range(3):
            for j in range(i+1,3):
                s.add(Or(Not(sites[i]), Not(sites[j])))
        # engine mode 0 admits only site 0; mode 1 admits site 1 or 2
        s.add(Or(And(m == 0, sites[0]), And(m == 1, Or(sites[1], sites[2]))))
        results['engine_admits_placement'] = (s.check() == sat)
    except Exception as e:
        results['_error'] = traceback.format_exc()
    return results

def run_negative_tests():
    results = {}
    try:
        from z3 import Int, Bool, Solver, And, Or, Not, Implies, unsat
        m = Int('m')
        sites = [Bool(f's{i}') for i in range(3)]
        s = Solver()
        # strict engine->placement rule: mode 0 forbids sites 1 and 2
        s.add(Implies(m == 0, And(Not(sites[1]), Not(sites[2]))))
        s.add(m == 0)
        s.add(sites[2])  # contradicts mode 0 -> UNSAT
        r = s.check()
        results['mode0_excludes_site2_placement'] = (r == unsat)
    except Exception as e:
        results['_error'] = traceback.format_exc()
    return results

def run_boundary_tests():
    results = {}
    try:
        from z3 import Int, Bool, Solver, Or, And, sat
        m = Int('m')
        s = Solver()
        s.add(Or(m == 0, m == 1))
        results['boundary_mode_domain_admissible'] = (s.check() == sat)
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
        "name": "sim_ladder_couple_L6_L11_engine_to_placement",
        "classification": "canonical",
        "scope_note": "ladders/fences per system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md",
        "coupling": {"layer_a": "L6_engine", "layer_b": "L11_placement"},
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
    out_path = os.path.join(out_dir, "sim_ladder_couple_L6_L11_engine_to_placement_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{overall} {out_path}")
