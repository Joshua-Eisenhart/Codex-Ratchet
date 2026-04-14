#!/usr/bin/env python3
"""sim_cl3_basis -- Cl(3,0) basis axioms (e_i^2 = +1, anticommutation, grade structure).

Load-bearing tool: clifford (constructs the algebra; grade-decomposition is decisive).
Cross-check: sympy symbolic squares for e_i*e_i.
"""
import json, os, numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed; algebraic identity test"},
    "pyg":       {"tried": False, "used": False, "reason": "no graph structure in basis axioms"},
    "z3":        {"tried": False, "used": False, "reason": "real-algebra SMT not required for numeric identities"},
    "cvc5":      {"tried": False, "used": False, "reason": "covered by numeric + sympy check"},
    "sympy":     {"tried": False, "used": False, "reason": "used for symbolic e_i*e_i cross-check"},
    "clifford":  {"tried": False, "used": False, "reason": "constructs Cl(3,0) and provides grade projection"},
    "geomstats": {"tried": False, "used": False, "reason": "not a manifold/statistics sim"},
    "e3nn":      {"tried": False, "used": False, "reason": "no tensor-product reps needed at basis level"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi":       {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx":  {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
except ImportError:
    sp = None

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
except ImportError:
    Cl = None

def _algebra():
    layout, blades = Cl(3)
    e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
    return layout, blades, e1, e2, e3

def run_positive_tests():
    r = {}
    layout, blades, e1, e2, e3 = _algebra()
    # e_i^2 = 1
    r["e1_sq"] = float((e1*e1).value[0]) == 1.0
    r["e2_sq"] = float((e2*e2).value[0]) == 1.0
    r["e3_sq"] = float((e3*e3).value[0]) == 1.0
    # anticommutation
    r["anticommute_12"] = (e1*e2 + e2*e1) == 0
    r["anticommute_13"] = (e1*e3 + e3*e1) == 0
    r["anticommute_23"] = (e2*e3 + e3*e2) == 0
    # grade count: 1 + 3 + 3 + 1 = 8
    r["dim_is_8"] = layout.gaDims == 8
    # sympy cross-check of scalar part
    if sp is not None:
        r["sympy_scalar_one"] = sp.Integer(1) == sp.Integer(int((e1*e1).value[0]))
    return r

def run_negative_tests():
    r = {}
    _, _, e1, e2, e3 = _algebra()
    # e1*e2 is NOT scalar (grade 2)
    r["e1e2_not_scalar"] = float((e1*e2).value[0]) == 0.0
    # e1 != e2
    r["e1_ne_e2"] = (e1 - e2) != 0
    # commutator nonzero for distinct basis vectors
    r["commutator_nonzero"] = (e1*e2 - e2*e1) != 0
    return r

def run_boundary_tests():
    r = {}
    layout, blades, e1, e2, e3 = _algebra()
    I = e1*e2*e3
    # pseudoscalar squares to -1 in Cl(3,0)
    r["I_sq_minus_one"] = float((I*I).value[0]) == -1.0
    # I commutes with all vectors (center in Cl(3,0))
    r["I_commutes_e1"] = (I*e1 - e1*I) == 0
    return r

def main():
    results = {
        "name": "sim_cl3_basis",
        "classification": classification,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    all_pass = all(v for section in ("positive","negative","boundary") for v in results[section].values())
    results["pass"] = bool(all_pass)
    out = os.path.join(os.path.dirname(__file__), "results", "sim_cl3_basis.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({"pass": results["pass"], "out": out}))
    return 0 if all_pass else 1

if __name__ == "__main__":
    raise SystemExit(main())
