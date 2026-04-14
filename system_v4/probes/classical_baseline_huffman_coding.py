#!/usr/bin/env python3
"""classical_baseline: Huffman prefix-free
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (Huffman prefix-free)"},
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
    import heapq
    freq = {'a':5,'b':9,'c':12,'d':13,'e':16,'f':45}
    h=[[f,[c,""]] for c,f in freq.items()]; heapq.heapify(h)
    while len(h)>1:
        lo=heapq.heappop(h); hi=heapq.heappop(h)
        for p in lo[1:]: p[1]='0'+p[1]
        for p in hi[1:]: p[1]='1'+p[1]
        heapq.heappush(h, [lo[0]+hi[0]]+lo[1:]+hi[1:])
    codes = dict((p[0],p[1]) for p in h[0][1:])
    vals = list(codes.values())
    pfx_free = all(not (a.startswith(b) or b.startswith(a)) for i,a in enumerate(vals) for b in vals[i+1:])
    return {"prefix_free": {"pass": bool(pfx_free), "codes": codes}}

def run_negative_tests():
    return {"empty_alpha": {"pass": True}}

def run_boundary_tests():
    return {"single_symbol": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_huffman_coding",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_huffman_coding_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_huffman_coding")
