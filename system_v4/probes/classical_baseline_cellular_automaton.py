#!/usr/bin/env python3
"""classical_baseline_cellular_automaton.py -- non-canon, lane_B-eligible
Generated classical baseline. numpy load_bearing. pos/neg/boundary all required PASS.
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for classical baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not a proof sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not a proof sim"},
    "sympy": {"tried": False, "used": False, "reason": "numeric only"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra here"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold here"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "numpy sufficient"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for cellular_automaton"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _ca(rule, N=101, T=50, seed_center=True):
    row=np.zeros(N,dtype=int)
    if seed_center: row[N//2]=1
    rules=np.array([(rule>>i)&1 for i in range(8)])
    hist=[row.copy()]
    for _ in range(T):
        left=np.roll(row,1); right=np.roll(row,-1)
        idx=4*left+2*row+right
        row=rules[idx]
        hist.append(row.copy())
    return np.array(hist)

def run_positive_tests():
    h30=_ca(30); h110=_ca(110)
    return {"rule30_nontrivial": bool(h30.sum()>10), "rule110_nontrivial": bool(h110.sum()>10)}

def run_negative_tests():
    h0=_ca(0)  # rule 0: everything dies
    return {"rule0_dies": bool(h0[-1].sum()==0)}

def run_boundary_tests():
    h=_ca(30, T=0)
    return {"T0_one_row": bool(h.shape[0]==1)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_cellular_automaton",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_cellular_automaton_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} cellular_automaton -> {out_path}")
