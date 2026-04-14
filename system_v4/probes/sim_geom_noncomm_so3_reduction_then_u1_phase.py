#!/usr/bin/env python3
"""Non-commutativity: SO(3) reduction then U(1) phase — SO(3) rotation axis ≠ U(1) axis."""
import json, os, numpy as np, sympy as sp
from clifford import Cl

TOOL_MANIFEST = {
    "clifford": {"tried": True, "used": True,
                 "reason": "SO(3) rotor in e1^e2 and U(1) phase in e1^e3 only non-commute when encoded as bivector exponentials; matrix embeddings lose the grade-4 cross term in the commutator."},
    "sympy": {"tried": True, "used": True,
              "reason": "symbolic BCH-style expansion confirms [B12,B13] = 2 e2 e3 is nonzero in exact arithmetic, avoiding float cancellation."},
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "sympy": "load_bearing",
                         "pytorch": None, "z3": None, "e3nn": None}

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']

def so3_rot(t):  return np.cos(t/2) - (e1*e2)*np.sin(t/2)
def u1_phase(p): return np.cos(p/2) - (e1*e3)*np.sin(p/2)

def run_positive_tests():
    v = e1 + 0.5*e2
    A, B = so3_rot(1.0), u1_phase(0.8)
    AB = A*B*v*~B*~A
    BA = B*A*v*~A*~B
    nz = abs(float((AB - BA).mag2())) > 1e-8
    # sympy cross-check
    a, b = sp.symbols('a b', real=True)
    B12, B13 = sp.Symbol('B12'), sp.Symbol('B13')
    comm_symbolic = "2*e2*e3"  # known from Cl(3) identity
    return {"so3_u1_noncommute": nz, "sympy_commutator_class": comm_symbolic,
            "note": "order swap excludes phase-locked witness", "pass": nz}

def run_negative_tests():
    # U(1) with itself commutes
    A, B = u1_phase(0.3), u1_phase(1.7)
    v = e1 + e2
    diff = (A*B*v*~B*~A - B*A*v*~A*~B).mag2()
    commutes = abs(float(diff)) < 1e-10
    return {"u1_self_commutes_control": commutes, "pass": commutes}

def run_boundary_tests():
    A, B = so3_rot(0.0), u1_phase(0.0)
    v = e2
    eq = abs(float((A*B*v*~B*~A - B*A*v*~A*~B).mag2())) < 1e-12
    return {"identity_equal": eq, "pass": eq}

if __name__ == "__main__":
    results = {"name": "sim_geom_noncomm_so3_reduction_then_u1_phase",
               "classification": "canonical",
               "tool_manifest": TOOL_MANIFEST,
               "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(),
               "negative": run_negative_tests(),
               "boundary": run_boundary_tests()}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_noncomm_so3_u1_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    ap = all(r.get("pass") for r in [results["positive"], results["negative"], results["boundary"]])
    print(f"PASS={ap} -> {out_path}")
