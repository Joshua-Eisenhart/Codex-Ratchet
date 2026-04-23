#!/usr/bin/env python3
"""sim_cl6_basis -- Cl(6,0) basis: 6 generators, 2^6=64 dim, grade multinomials."""
import json, os, numpy as np
from math import comb

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": r} for k,r in {
    "pytorch":"not needed","pyg":"no graph","z3":"numeric","cvc5":"numeric",
    "sympy":"not used","clifford":"load_bearing: Cl(6,0) construction","geomstats":"not used",
    "e3nn":"not used","rustworkx":"no graph","xgi":"no hypergraph","toponetx":"no cells","gudhi":"no persistence",
}.items()}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from clifford import Cl
TOOL_MANIFEST["clifford"].update(tried=True, used=True); TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

layout, blades = Cl(6)
E = [blades[f'e{i}'] for i in range(1,7)]

def run_positive_tests():
    r = {}
    r["dim_64"] = layout.gaDims == 64
    r["all_square_plus_one"] = all(float((e*e).value[0]) == 1.0 for e in E)
    # anticommutation
    r["all_anticommute"] = all((E[i]*E[j] + E[j]*E[i]) == 0 for i in range(6) for j in range(i+1,6))
    # grade dimensions: C(6,k)
    grade_counts = [layout.gradeList.count(k) for k in range(7)]
    expected = [comb(6,k) for k in range(7)]
    r["grade_multinomials"] = grade_counts == expected
    return r

def run_negative_tests():
    r = {}
    r["e1_ne_e6"] = (E[0] - E[5]) != 0
    r["distinct_vectors_noncommute"] = (E[0]*E[1] - E[1]*E[0]) != 0
    # scalar part of e1*e2 is zero
    r["e1e2_no_scalar"] = float((E[0]*E[1]).value[0]) == 0.0
    return r

def run_boundary_tests():
    r = {}
    # Pseudoscalar I = e1..e6; in Cl(6,0), I^2 = (-1)^{6(6-1)/2} = (-1)^15 = -1
    I = E[0]
    for e in E[1:]: I = I * e
    r["I_sq_minus_one"] = float((I*I).value[0]) == -1.0
    # I anticommutes with vectors in Cl(6,0) since n=6 is even -> I anticommutes with grade-1
    # Actually for even n, I anticommutes with odd grades. Check:
    r["I_anticommutes_e1"] = (I*E[0] + E[0]*I) == 0
    return r

def main():
    results = {"name":"sim_cl6_basis","classification":classification,
               "positive":run_positive_tests(),"negative":run_negative_tests(),"boundary":run_boundary_tests(),
               "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH}
    ok = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    results["pass"] = bool(ok)
    out = os.path.join(os.path.dirname(__file__),"results","sim_cl6_basis.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(json.dumps({"pass":results["pass"],"out":out}))
    return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main())
