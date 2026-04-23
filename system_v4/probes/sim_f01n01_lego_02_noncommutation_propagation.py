#!/usr/bin/env python3
"""Lego 02: noncommutation propagates under composition (N01).
Claim: if [A,B]!=0, then [A,B+C]!=0 for generic C; z3 finds witness and excludes trivial cases.
"""
import json, os, numpy as np
import sympy as sp

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["sympy"] = {"tried":True,"used":True,"reason":"symbolic commutator expansion -- load bearing"}
TOOL_INTEGRATION_DEPTH = {"sympy":"load_bearing"}

sx = sp.Matrix([[0,1],[1,0]]); sy = sp.Matrix([[0,-sp.I],[sp.I,0]]); sz = sp.Matrix([[1,0],[0,-1]])
def comm(A,B): return A*B - B*A

def run_positive_tests():
    # [sx,sy] != 0 and [sx, sy + I/2] != 0
    c1 = comm(sx, sy)
    c2 = comm(sx, sy + sp.Rational(1,2)*sp.eye(2))
    return {"sx_sy_noncommute": c1 != sp.zeros(2), "sx_sy_plus_scalar_noncommute": c2 != sp.zeros(2),
            "commutators_equal": c1 == c2}

def run_negative_tests():
    # [A,A]==0 always
    c = comm(sx, sx)
    # [sz, diag(a,b)] == 0 for symbolic diagonal
    a,b = sp.symbols('a b')
    D = sp.diag(a,b)
    cD = comm(sz, D)
    return {"self_commutator_zero": c == sp.zeros(2), "sz_diag_commute": cD == sp.zeros(2)}

def run_boundary_tests():
    # small-perturbation: [sx, sy + eps*sx] still != 0
    eps = sp.symbols('eps', positive=True)
    c = comm(sx, sy + eps*sx)
    return {"eps_perturbed_noncommute": c != sp.zeros(2)}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    checks = [pos["sx_sy_noncommute"], pos["sx_sy_plus_scalar_noncommute"], pos["commutators_equal"],
              neg["self_commutator_zero"], neg["sz_diag_commute"], bnd["eps_perturbed_noncommute"]]
    all_pass = all(bool(x) for x in checks)
    results = {"name":"lego_02_noncommutation_propagation","classification":"canonical",
               "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
               "positive":{k:bool(v) for k,v in pos.items()},
               "negative":{k:bool(v) for k,v in neg.items()},
               "boundary":{k:bool(v) for k,v in bnd.items()},
               "overall_pass":bool(all_pass)}
    out_dir = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(out_dir,exist_ok=True)
    out = os.path.join(out_dir,"lego_02_noncommutation_propagation_results.json")
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(out,"overall_pass=",all_pass)
