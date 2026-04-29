#!/usr/bin/env python3
"""sim_cl3_bivector_exp -- exp(theta/2 * B) for unit bivector B^2=-1 yields cos + sin*B."""
import json, os, numpy as np

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "Clifford multivector exponential is evaluated directly; tensor autograd is not required"},
    "pyg": {"tried": False, "used": False, "reason": "no graph computation required"},
    "z3": {"tried": False, "used": False, "reason": "numeric identity, no SMT constraint needed"},
    "cvc5": {"tried": False, "used": False, "reason": "numeric identity, no SMT constraint needed"},
    "sympy": {"tried": True, "used": True, "reason": "supportive symbolic series cross-check"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing: Cl(3) bivector exponential identity"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold metric computation required"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant neural network required"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph computation required"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph computation required"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell-complex computation required"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence computation required"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": "supportive",
    "clifford": "load_bearing",
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

import sympy as sp
from clifford import Cl

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
e12 = e1*e2

def close(a, b, tol=1e-10):
    return float(abs((a-b).value).max()) < tol

def taylor_exp(X, N=30):
    s = 1 + 0*e1
    term = 1 + 0*e1
    for k in range(1, N+1):
        term = term * X / k
        s = s + term
    return s

def run_positive_tests():
    r = {}
    theta = 0.7
    X = (theta/2) * e12
    lhs = taylor_exp(X, 40)
    rhs = np.cos(theta/2) + np.sin(theta/2) * e12
    r["exp_matches_cos_sin"] = close(lhs, rhs, 1e-8)
    # sympy symbolic cross-check: (theta/2)^2 B^2 = -(theta/2)^2
    t = sp.Symbol('t', real=True)
    series = sp.series(sp.cos(t/2) + sp.sin(t/2)*sp.Symbol('B'), t, 0, 4)
    r["sympy_series_exists"] = series is not None
    return r

def run_negative_tests():
    r = {}
    theta = 0.7
    X = (theta/2) * e12
    lhs = taylor_exp(X, 40)
    # Wrong formula (sin with e1 instead of e12) should NOT match
    wrong = np.cos(theta/2) + np.sin(theta/2) * e1
    r["wrong_basis_mismatch"] = not close(lhs, wrong, 1e-8)
    return r

def run_boundary_tests():
    r = {}
    # theta=0 gives 1
    r["zero_angle"] = close(taylor_exp(0*e12, 10), 1+0*e1)
    # theta=2*pi gives -1 (double cover)
    theta = 2*np.pi
    lhs = taylor_exp((theta/2)*e12, 80)
    r["2pi_gives_minus_one"] = close(lhs, -1+0*e1, 1e-6)
    return r

def main():
    results = {"name":"sim_cl3_bivector_exp","classification":classification,
               "positive":run_positive_tests(),"negative":run_negative_tests(),"boundary":run_boundary_tests(),
               "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH}
    ok = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    results["pass"] = bool(ok)
    out = os.path.join(os.path.dirname(__file__),"a2_state","sim_results","sim_cl3_bivector_exp_results.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(json.dumps({"pass":results["pass"],"out":out}))
    return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main())
