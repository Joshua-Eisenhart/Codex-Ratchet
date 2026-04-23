#!/usr/bin/env python3
"""classical_baseline_ising2d_metropolis.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for ising2d_metropolis"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _ising_E(s, J=1.0):
    return -J*(np.sum(s*np.roll(s,1,0)) + np.sum(s*np.roll(s,1,1)))

def _metropolis(L=12, T=2.27, steps=2000, seed=0, cold_start=False):
    rng = np.random.default_rng(seed)
    s = np.ones((L,L),dtype=int) if cold_start else rng.choice([-1,1], size=(L,L))
    mags=[]
    for _ in range(steps):
        i,j = rng.integers(0,L,2)
        dE = 2*s[i,j]*(s[(i+1)%L,j]+s[(i-1)%L,j]+s[i,(j+1)%L]+s[i,(j-1)%L])
        if dE<=0 or rng.random()<np.exp(-dE/T):
            s[i,j]*=-1
        mags.append(abs(s.mean()))
    return np.mean(mags[-500:])

def run_positive_tests():
    m_lowT = _metropolis(T=1.0, seed=1, steps=5000, cold_start=True)
    m_highT = _metropolis(T=5.0, seed=2)
    return {"ordered_low_T": bool(m_lowT > 0.5), "disordered_high_T": bool(m_highT < 0.4)}

def run_negative_tests():
    # negation: high-T should NOT be ordered
    m = _metropolis(T=5.0, seed=3)
    return {"highT_not_ordered": bool(m < 0.5)}

def run_boundary_tests():
    # tiny lattice runs without crash, magnetization in [0,1]
    m = _metropolis(L=4, T=2.27, steps=300, seed=4)
    return {"tiny_lattice_bounded": bool(0.0 <= m <= 1.0)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_ising2d_metropolis",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_ising2d_metropolis_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} ising2d_metropolis -> {out_path}")
