#!/usr/bin/env python3
"""Lego 07: composition order ABC vs ACB distinguishable iff [B,C]!=0 (N01).
sympy load-bearing.
"""
import json, os, sympy as sp

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["sympy"] = {"tried":True,"used":True,"reason":"symbolic operator ordering; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"sympy":"load_bearing"}

sx = sp.Matrix([[0,1],[1,0]]); sy = sp.Matrix([[0,-sp.I],[sp.I,0]]); sz = sp.Matrix([[1,0],[0,-1]]); I2 = sp.eye(2)

def run_positive_tests():
    A,B,C = sx, sy, sz
    abc = A*B*C; acb = A*C*B
    return {"noncommuting_BC_distinguishable": abc != acb, "BC_commutator_nonzero": (B*C - C*B) != sp.zeros(2)}

def run_negative_tests():
    A,B,C = sx, sy, I2
    abc = A*B*C; acb = A*C*B
    return {"commuting_BC_indistinguishable": abc == acb}

def run_boundary_tests():
    # B == C => trivially indistinguishable
    A,B,C = sx, sy, sy
    return {"B_eq_C_indistinguishable": A*B*C == A*C*B}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    checks = list(pos.values())+list(neg.values())+list(bnd.values())
    all_pass = all(bool(x) for x in checks)
    r = {"name":"lego_07_abc_vs_acb","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":{k:bool(v) for k,v in pos.items()},
         "negative":{k:bool(v) for k,v in neg.items()},
         "boundary":{k:bool(v) for k,v in bnd.items()},
         "overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"lego_07_abc_vs_acb_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
