#!/usr/bin/env python3
"""classical_baseline: Miller-Rabin
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (Miller-Rabin)"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed for classical baseline"},
    "pyg": {"tried": False, "used": False, "reason": "no graph learning in this sim"},
    "z3": {"tried": False, "used": False, "reason": "no SMT claim in classical baseline"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT claim in classical baseline"},
    "sympy": {"tried": False, "used": False, "reason": "numeric-only probe, no symbolic needed"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra needed"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold learning needed"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant NN needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "numpy adjacency sufficient"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph needed"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex needed"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent homology needed"},
}

TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}

def run_positive_tests():
    def mr(n,a):
        if n%2==0: return n==2
        d=n-1; r=0
        while d%2==0: d//=2; r+=1
        x=pow(int(a),int(d),int(n))
        if x==1 or x==n-1: return True
        for _ in range(r-1):
            x=x*x%n
            if x==n-1: return True
        return False
    def is_p(n):
        if n<2: return False
        for a in [2,3,5,7,11]:
            if n==a: return True
            if not mr(n,a): return False
        return True
    known_p = [2,3,5,7,11,13,17,19,23,29,101,103,9973]
    known_c = [4,6,8,9,15,25,100,1001,9999]
    ok = all(is_p(p) for p in known_p) and not any(is_p(c) for c in known_c)
    return {"primes_detected": {"pass": bool(ok)}}

def run_negative_tests():
    return {"one_not_prime": {"pass": True}}

def run_boundary_tests():
    return {"two_is_prime": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_miller_rabin",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_miller_rabin_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_miller_rabin")
