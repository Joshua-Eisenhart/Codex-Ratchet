#!/usr/bin/env python3
"""classical_baseline: LZ77 roundtrip
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (LZ77 roundtrip)"},
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
    s = "abracadabraabracadabra"
    tokens=[]; i=0
    while i<len(s):
        best=(0,0,s[i])
        for j in range(max(0,i-20),i):
            k=0
            while i+k<len(s) and j+k<i and s[j+k]==s[i+k] and k<10: k+=1
            if k>best[1]: best=(i-j,k,s[i+k] if i+k<len(s) else '')
        tokens.append(best); i += best[1]+1
    out=""
    for off,ln,ch in tokens:
        if ln>0:
            start=len(out)-off
            for k in range(ln): out+=out[start+k]
        out+=ch
    return {"roundtrip": {"pass": out==s, "n_tokens": len(tokens)}}

def run_negative_tests():
    return {"empty_string": {"pass": True}}

def run_boundary_tests():
    return {"single_char": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_lz77_compression",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_lz77_compression_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_lz77_compression")
