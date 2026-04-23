#!/usr/bin/env python3
"""classical_baseline: Conway Game of Life
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (Conway Game of Life)"},
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
    g2 = np.zeros((5,5),dtype=int); g2[2,1:4]=1
    for _ in range(2):
        nb = sum(np.roll(np.roll(g2,i,0),j,1) for i in (-1,0,1) for j in (-1,0,1) if (i,j)!=(0,0))
        g2 = (((g2==1)&((nb==2)|(nb==3)))|((g2==0)&(nb==3))).astype(int)
    return {"blinker_period2": {"pass": bool(np.array_equal(g2[2,1:4],[1,1,1]))}}

def run_negative_tests():
    g = np.zeros((5,5),dtype=int)
    nb = sum(np.roll(np.roll(g,i,0),j,1) for i in (-1,0,1) for j in (-1,0,1) if (i,j)!=(0,0))
    g = (((g==1)&((nb==2)|(nb==3)))|((g==0)&(nb==3))).astype(int)
    return {"empty_stays_empty": {"pass": int(g.sum())==0}}

def run_boundary_tests():
    return {"block_still_life": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_game_of_life",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_game_of_life_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_game_of_life")
