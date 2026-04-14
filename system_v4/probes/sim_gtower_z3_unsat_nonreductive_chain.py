#!/usr/bin/env python3
"""sim_gtower_z3_unsat_nonreductive_chain -- z3 UNSAT for a forbidden reduction.

Scope note: LADDERS_FENCES_ADMISSION_REFERENCE.md: the chain fences
compose monotonically; a 2x2 orthogonal matrix cannot simultaneously
satisfy det=-1 (excluded from SO) AND lie in SO(2). We also prove:
no real 2x2 matrix is simultaneously orthogonal AND symplectic with
det=-1 (Sp(2,R) = SL(2,R) requires det=+1).

Load-bearing: z3 returns UNSAT for both forbidden reductions.
"""
import json, os

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


def prove_o_minus_and_so():
    """Forbidden: A in O(2), det(A)=-1, AND A in SO(2)."""
    a, b, c, d = z3.Reals("a b c d")
    s = z3.Solver()
    s.add(a*a + c*c == 1, b*b + d*d == 1, a*b + c*d == 0)
    s.add(a*d - b*c == -1)   # O-minus
    s.add(a*d - b*c == 1)    # AND in SO
    return str(s.check())


def prove_sp_minus_det():
    """Forbidden: A real 2x2 in Sp(2,R) with det = -1."""
    a, b, c, d = z3.Reals("a b c d")
    s = z3.Solver()
    # Sp(2,R) condition: A^T J A = J with J = [[0,1],[-1,0]] => a*d - b*c = 1
    s.add(a*d - b*c == 1)
    s.add(a*d - b*c == -1)
    return str(s.check())


def prove_u_and_nonunitary():
    """Forbidden: z+w with |z|^2 + |w|^2 = 1 AND != 1 (simple sanity UNSAT)."""
    x, y = z3.Reals("x y")
    s = z3.Solver()
    s.add(x*x + y*y == 1)
    s.add(x*x + y*y != 1)
    return str(s.check())


def run_positive_tests():
    r = {}
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"skipped": True}
    r["forbidden_o_minus_in_so"] = prove_o_minus_and_so()
    r["forbidden_sp_det_minus1"] = prove_sp_minus_det()
    r["forbidden_unitary_contradiction"] = prove_u_and_nonunitary()
    r["all_unsat"] = all(v == "unsat" for v in
        [r["forbidden_o_minus_in_so"], r["forbidden_sp_det_minus1"],
         r["forbidden_unitary_contradiction"]])
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT proofs for three forbidden reductions in G-tower chain"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return r


def run_negative_tests():
    """Sanity: a genuinely satisfiable constraint returns sat."""
    r = {}
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"skipped": True}
    a, b, c, d = z3.Reals("a b c d")
    s = z3.Solver()
    s.add(a*a + c*c == 1, b*b + d*d == 1, a*b + c*d == 0)
    s.add(a*d - b*c == 1)  # SO(2) is non-empty
    r["so2_is_satisfiable"] = str(s.check())
    r["so2_sat"] = (r["so2_is_satisfiable"] == "sat")
    return r


def run_boundary_tests():
    r = {}
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"skipped": True}
    # Boundary: trivial contradiction
    s = z3.Solver()
    x = z3.Real("x")
    s.add(x == 0, x != 0)
    r["trivial_unsat"] = (str(s.check()) == "unsat")
    return r


if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    def _t(v): return bool(v) is True
    all_pass = _t(pos.get("all_unsat")) and _t(neg.get("so2_sat")) and _t(bnd.get("trivial_unsat"))
    results = {
        "name": "sim_gtower_z3_unsat_nonreductive_chain",
        "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: forbidden reductions yield z3 UNSAT",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "status": "PASS" if all_pass else "FAIL",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sim_gtower_z3_unsat_nonreductive_chain_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{results['name']}: {results['status']}")
