#!/usr/bin/env python3
"""sim_cl6_basis -- Cl(6,0) basis: 6 generators, 2^6=64 dim, grade multinomials."""
import json, os, numpy as np
from math import comb

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

classification = "classical_baseline"
divergence_log = (
    "Classical baseline: this probe uses bounded algebraic/numeric checks as "
    "a comparison control; it is not a canonical nonclassical claim."
)
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this Cl(6,0) basis baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed: no graph layer"},
    "z3": {"tried": False, "used": False, "reason": "not needed: no SMT claim"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed: no SMT claim"},
    "sympy": {"tried": False, "used": False, "reason": "not used: Clifford runtime constructs the algebra"},
    "clifford": {"tried": False, "used": False, "reason": "load-bearing Cl(6,0) construction"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed: no manifold-distance computation"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed: no equivariant neural layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed: no graph algorithm"},
    "xgi": {"tried": False, "used": False, "reason": "not needed: no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed: no cell-complex computation"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed: no persistence computation"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

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
               "divergence_log":divergence_log,
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
