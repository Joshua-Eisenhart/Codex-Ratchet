#!/usr/bin/env python3
"""sim_cl6_chirality -- Chirality operator gamma = I (pseudoscalar) splits Cl(6) into +/- eigenspaces.

In Cl(6,0): I = e1..e6, I^2 = -1, so chirality operator is chosen as i*I or equivalently
acts by I with eigenvalues +/- i on full space. We use the real structure: I anticommutes
with grade-1, commutes with grade-0,2,4,6 appropriately (even n). Concretely:
- I commutes with even grades, anticommutes with odd grades for n=6 (since n even => I in center
  of even subalgebra, and I anticommutes with odd grades).
"""
import json, os, numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": r} for k,r in {
    "pytorch":"not needed","pyg":"no graph","z3":"numeric","cvc5":"numeric",
    "sympy":"not used","clifford":"load_bearing: pseudoscalar and grade projections","geomstats":"not used",
    "e3nn":"not used","rustworkx":"no graph","xgi":"no hypergraph","toponetx":"no cells","gudhi":"no persistence",
}.items()}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from clifford import Cl
TOOL_MANIFEST["clifford"].update(tried=True, used=True); TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

layout, blades = Cl(6)
E = [blades[f'e{i}'] for i in range(1,7)]
I = E[0]
for e in E[1:]: I = I*e

def close(a, b, tol=1e-10):
    return float(abs((a-b).value).max()) < tol

def run_positive_tests():
    r = {}
    # I^2 = -1
    r["I_sq_minus_one"] = float((I*I).value[0]) == -1.0
    # Even grades: I commutes (for n=6 even, I is in center of Cl+)
    even = E[0]*E[1] + E[2]*E[3]
    r["I_commutes_with_even_grade2"] = close(I*even, even*I)
    # grade-4 also even
    g4 = E[0]*E[1]*E[2]*E[3]
    r["I_commutes_with_grade4"] = close(I*g4, g4*I)
    # Odd grades: I anticommutes
    r["I_anticommutes_grade1"] = close(I*E[0], -E[0]*I)
    g3 = E[0]*E[1]*E[2]
    r["I_anticommutes_grade3"] = close(I*g3, -g3*I)
    return r

def run_negative_tests():
    r = {}
    # I does NOT commute with grade-1
    r["I_noncommute_grade1"] = not close(I*E[0], E[0]*I)
    # I does NOT anticommute with grade-2
    r["I_nonanticommute_grade2"] = not close(I*E[0]*E[1], -E[0]*E[1]*I)
    return r

def run_boundary_tests():
    r = {}
    # I acting on the pseudoscalar itself: I*I = -1 (scalar), so it "rotates" into scalar
    r["I_times_I_is_scalar"] = float(abs((I*I - (-1+0*E[0])).value).max()) < 1e-12
    # Grade projection via (1 + sign*...) is out of scope here; validate center containment:
    # I is in center of even subalgebra: I*B = B*I for any pure even B
    B = E[0]*E[1]*E[2]*E[3]*E[4]*E[5]  # grade 6 = I itself (trivial) -> use another
    B = E[0]*E[1]*E[4]*E[5]  # grade 4 (even)
    r["I_center_of_even"] = close(I*B, B*I)
    return r

def main():
    results = {"name":"sim_cl6_chirality","classification":classification,
               "positive":run_positive_tests(),"negative":run_negative_tests(),"boundary":run_boundary_tests(),
               "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH}
    ok = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    results["pass"] = bool(ok)
    out = os.path.join(os.path.dirname(__file__),"results","sim_cl6_chirality.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(json.dumps({"pass":results["pass"],"out":out}))
    return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main())
