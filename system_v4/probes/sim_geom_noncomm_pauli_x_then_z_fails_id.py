#!/usr/bin/env python3
"""Non-commutativity: Pauli X then Z vs Z then X; commutator = 2i Y ≠ 0."""
import json, os, sympy as sp

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True,
              "reason": "exact symbolic verification that [X,Z] = -2iY ≠ 0; floating-point matrix algebra could hide degeneracies at exact zero, sympy's exact arithmetic is load-bearing for the UNSAT-style exclusion claim."},
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing", "pytorch": None, "clifford": None, "z3": None, "e3nn": None}

I = sp.I
X = sp.Matrix([[0,1],[1,0]])
Y = sp.Matrix([[0,-I],[I,0]])
Z = sp.Matrix([[1,0],[0,-1]])

def run_positive_tests():
    comm = X*Z - Z*X
    expected = -2*I*Y
    matches = sp.simplify(comm - expected) == sp.zeros(2,2)
    nonzero = comm != sp.zeros(2,2)
    psi = sp.Matrix([1, 1])/sp.sqrt(2)
    xz = X*Z*psi; zx = Z*X*psi
    witness = sp.simplify(xz - zx) != sp.zeros(2,1)
    return {"commutator_equals_neg_2iY": bool(matches),
            "commutator_nonzero": bool(nonzero),
            "witness_state_differs": bool(witness),
            "note": "order XZ admits |+> rotation Z then flip; ZX excludes same final state",
            "pass": bool(matches and nonzero and witness)}

def run_negative_tests():
    # Z with itself commutes
    comm = Z*Z - Z*Z
    commutes = comm == sp.zeros(2,2)
    return {"Z_self_commutes_control": bool(commutes), "pass": bool(commutes)}

def run_boundary_tests():
    # Scalar multiple of identity: X and alpha*I commute
    alpha = sp.Symbol('a')
    aI = alpha*sp.eye(2)
    comm = X*aI - aI*X
    eq = sp.simplify(comm) == sp.zeros(2,2)
    return {"identity_scalar_commutes": bool(eq), "pass": bool(eq)}

if __name__ == "__main__":
    results = {"name": "sim_geom_noncomm_pauli_x_then_z_fails_id",
               "classification": "canonical",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(), "boundary": run_boundary_tests()}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_noncomm_pauli_xz_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    ap = all(r.get("pass") for r in [results["positive"], results["negative"], results["boundary"]])
    print(f"PASS={ap} -> {out_path}")
