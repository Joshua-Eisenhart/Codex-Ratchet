#!/usr/bin/env python3
"""Non-commutativity: BCH expansion exp(A)exp(B) != exp(A+B) when [A,B]!=0."""
import json, os, sympy as sp

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True,
              "reason": "Baker-Campbell-Hausdorff must be expanded symbolically to witness the [A,B]/2 second-order term; any float truncation collapses the commutator into roundoff — sympy exact arithmetic is the only way to prove exp(A)exp(B) - exp(A+B) has nonzero leading term."},
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing", "pytorch": None, "clifford": None, "z3": None, "e3nn": None}

def run_positive_tests():
    I = sp.I
    X = sp.Matrix([[0,1],[1,0]])
    Z = sp.Matrix([[1,0],[0,-1]])
    t = sp.Symbol('t', real=True)
    # Expand to 2nd order
    A = I*t*X; B = I*t*Z
    expA = sp.eye(2) + A + A*A/2
    expB = sp.eye(2) + B + B*B/2
    lhs = sp.expand(expA*expB)
    rhs = sp.eye(2) + (A+B) + (A+B)*(A+B)/2
    diff = sp.expand(lhs - rhs)
    # Leading term should be (1/2)[A,B] = (1/2)(AB - BA)
    comm_half = sp.expand((A*B - B*A)/2)
    # Compare t^2 coefficients
    d_t2 = diff.applyfunc(lambda x: x.coeff(t,2))
    c_t2 = comm_half.applyfunc(lambda x: x.coeff(t,2))
    matches = sp.simplify(d_t2 - c_t2) == sp.zeros(2,2)
    nonzero = d_t2 != sp.zeros(2,2)
    return {"bch_second_order_equals_half_commutator": bool(matches),
            "bch_leading_term_nonzero": bool(nonzero),
            "note": "order swap excludes identical-exponent admissibility", "pass": bool(matches and nonzero)}

def run_negative_tests():
    # [A,A] = 0 -> BCH trivial
    t = sp.Symbol('t')
    X = sp.Matrix([[0,1],[1,0]])
    A = sp.I*t*X
    comm = A*A - A*A
    return {"self_commutator_zero_control": comm == sp.zeros(2,2), "pass": comm == sp.zeros(2,2)}

def run_boundary_tests():
    # scalar generators commute
    a, b, t = sp.symbols('a b t')
    A = a*t*sp.eye(2); B = b*t*sp.eye(2)
    comm = A*B - B*A
    return {"scalar_generators_commute": comm == sp.zeros(2,2), "pass": comm == sp.zeros(2,2)}

if __name__ == "__main__":
    results = {"name": "sim_geom_noncomm_bch_nonzero_commutator",
               "classification": "canonical",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(), "boundary": run_boundary_tests()}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_noncomm_bch_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    ap = all(r.get("pass") for r in [results["positive"], results["negative"], results["boundary"]])
    print(f"PASS={ap} -> {out_path}")
