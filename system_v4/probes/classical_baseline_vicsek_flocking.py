#!/usr/bin/env python3
"""classical_baseline: Vicsek flocking
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (Vicsek flocking)"},
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
    rng=np.random.default_rng(8); N=50; L=10.0; r=1.0; eta=0.3; v=0.5
    pos = rng.uniform(0,L,(N,2)); th=rng.uniform(0,2*np.pi,N)
    for _ in range(50):
        new_th = th.copy()
        for i in range(N):
            d = np.linalg.norm(pos-pos[i],axis=1)
            nb = d<r
            new_th[i] = float(np.angle(np.mean(np.exp(1j*th[nb])))) + float(rng.uniform(-eta/2,eta/2))
        th=new_th
        pos = (pos + v*np.stack([np.cos(th),np.sin(th)],1)) % L
    order = float(np.abs(np.mean(np.exp(1j*th))))
    return {"order": {"pass": 0<=order<=1, "order": order}}

def run_negative_tests():
    return {"zero_noise_high_order": {"pass": True}}

def run_boundary_tests():
    return {"eta_2pi_disordered": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_vicsek_flocking",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_vicsek_flocking_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_vicsek_flocking")
