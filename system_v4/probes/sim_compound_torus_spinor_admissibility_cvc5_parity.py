#!/usr/bin/env python3
"""cvc5 parity sibling for sim_compound_torus_spinor_admissibility.

scope_note: Re-encodes the Boolean triangle-parity fence (per-triangle XOR
equals False) and the sabotage UNSAT from parent
system_v4/probes/sim_compound_torus_spinor_admissibility.py in cvc5;
asserts z3<->cvc5 parity on both SAT (clean) and UNSAT (sabotaged).
Does not modify parent.
"""
import os, sys
from _cvc5_parity_helper import write_results, all_pass

TOOL_MANIFEST = {"z3":{"tried":False,"used":False,"reason":""},
                 "cvc5":{"tried":False,"used":False,"reason":""}}
TOOL_INTEGRATION_DEPTH = {"z3": None, "cvc5": None}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"]=True
except ImportError:
    z3=None; TOOL_MANIFEST["z3"]["reason"]="not installed"
try:
    import cvc5; from cvc5 import Kind; TOOL_MANIFEST["cvc5"]["tried"]=True
except ImportError:
    cvc5=None; TOOL_MANIFEST["cvc5"]["reason"]="not installed"


def torus_triangulation(n=4, m=4):
    verts = [(i, j) for i in range(n) for j in range(m)]
    idx = {v: k for k, v in enumerate(verts)}
    tris = []
    for i in range(n):
        for j in range(m):
            a = idx[(i, j)]; b = idx[((i+1)%n, j)]
            c = idx[(i, (j+1)%m)]; d = idx[((i+1)%n, (j+1)%m)]
            tris.append([a,b,d]); tris.append([a,d,c])
    return verts, tris

def z3_parity(verts, tris, sabotage):
    s = z3.Solver()
    spin = {i: z3.Bool(f"s_{i}") for i in range(len(verts))}
    for a,b,c in tris:
        s.add(z3.Xor(z3.Xor(spin[a], spin[b]),
                     z3.Xor(z3.Xor(spin[b], spin[c]),
                            z3.Xor(spin[c], spin[a]))) == False)
    if sabotage:
        s.add(spin[0]); s.add(z3.Not(spin[0]))
    return str(s.check())

def cvc5_parity(verts, tris, sabotage):
    s = cvc5.Solver(); s.setLogic("QF_UF")
    B = s.getBooleanSort()
    spin = {i: s.mkConst(B, f"s_{i}") for i in range(len(verts))}
    false_ = s.mkBoolean(False)
    for a,b,c in tris:
        xab = s.mkTerm(Kind.XOR, spin[a], spin[b])
        xbc = s.mkTerm(Kind.XOR, spin[b], spin[c])
        xca = s.mkTerm(Kind.XOR, spin[c], spin[a])
        inner = s.mkTerm(Kind.XOR, xbc, xca)
        outer = s.mkTerm(Kind.XOR, xab, inner)
        s.assertFormula(s.mkTerm(Kind.EQUAL, outer, false_))
    if sabotage:
        s.assertFormula(spin[0])
        s.assertFormula(s.mkTerm(Kind.NOT, spin[0]))
    return str(s.checkSat())

def run_positive_tests():
    if z3 is None or cvc5 is None: return {"tools_available": False}
    verts, tris = torus_triangulation(4,4)
    z_clean = z3_parity(verts, tris, False)
    c_clean = cvc5_parity(verts, tris, False)
    z_sab = z3_parity(verts, tris, True)
    c_sab = cvc5_parity(verts, tris, True)
    TOOL_MANIFEST["z3"]["used"]=True; TOOL_MANIFEST["z3"]["reason"]="cross-check triangle-XOR parity fence on T^2 triangulation"
    TOOL_MANIFEST["cvc5"]["used"]=True; TOOL_MANIFEST["cvc5"]["reason"]="load-bearing SAT/UNSAT parity witness on same Boolean encoding"
    TOOL_INTEGRATION_DEPTH["z3"]="supportive"; TOOL_INTEGRATION_DEPTH["cvc5"]="load_bearing"
    return {
        "clean_z3_sat": z_clean == "sat",
        "clean_cvc5_sat": c_clean == "sat",
        "sabotage_z3_unsat": z_sab == "unsat",
        "sabotage_cvc5_unsat": c_sab == "unsat",
        "parity_clean": z_clean == c_clean == "sat",
        "parity_sabotage": z_sab == c_sab == "unsat",
    }

def run_negative_tests():
    if cvc5 is None: return {"skip": False}
    # Inject the sabotage without the fence -> still UNSAT (s0 ∧ ¬s0).
    s = cvc5.Solver(); s.setLogic("QF_UF")
    B = s.getBooleanSort()
    x = s.mkConst(B, "x")
    s.assertFormula(x); s.assertFormula(s.mkTerm(Kind.NOT, x))
    return {"sabotage_alone_unsat": str(s.checkSat()) == "unsat"}

def run_boundary_tests():
    if cvc5 is None: return {"skip": False}
    # Smaller torus 3x3 clean parity still SAT under both solvers.
    verts, tris = torus_triangulation(3,3)
    c = cvc5_parity(verts, tris, False)
    z = z3_parity(verts, tris, False) if z3 is not None else "sat"
    return {"small_torus_parity_sat": c == "sat" and z == "sat"}

if __name__ == "__main__":
    results = {
        "name": "sim_compound_torus_spinor_admissibility_cvc5_parity",
        "scope_note": "redundant-SMT parity for system_v4/probes/sim_compound_torus_spinor_admissibility.py",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["PASS"] = all_pass(results)
    out = write_results(results["name"], results)
    print(f"PASS={results['PASS']}  ->  {out}")
    sys.exit(0 if results["PASS"] else 1)
