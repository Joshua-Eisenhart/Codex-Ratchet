#!/usr/bin/env python3
"""sim_em_classical_future_compression_future_from_external
Scope: doctrine 'future comes from external compression' (user_causality_fep_doctrine.md).
Classical baseline renormalization toy: coarse-grain a fine signal and check
compressed representation predicts macro evolution.
"""
import json, os, numpy as np
SCOPE_NOTE = "Doctrine 'future from external compression'. RG-block toy; compressed macro predicts evolution. user_entropic_monism_doctrine.md"
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing RG coarse-grain + prediction"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "no SMT"},
    "sympy": {"tried": False, "used": False, "reason": "numeric"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def block(x, k=4):
    n = (len(x)//k)*k
    return x[:n].reshape(-1, k).mean(axis=1)

def evolve(x, steps=10, alpha=0.9):
    for _ in range(steps):
        x = alpha*x + (1-alpha)*np.roll(x, 1)
    return x

def run_positive_tests():
    rng = np.random.default_rng(0)
    x = rng.standard_normal(1024)
    # full evolve then block  vs  block then evolve (should agree at macro scale)
    a = block(evolve(x))
    b = evolve(block(x))
    corr = float(np.corrcoef(a, b)[0,1])
    # RG+evolve approximately commute at macro scale (strong positive corr)
    return {"block_evolve_commute": {"pass": bool(corr > 0.5), "corr": corr}}

def run_negative_tests():
    rng = np.random.default_rng(1)
    x = rng.standard_normal(1024)
    y = rng.standard_normal(1024)
    corr = float(np.corrcoef(block(evolve(x)), block(evolve(y)))[0,1])
    return {"independent_signals_uncorrelated": {"pass": bool(abs(corr) < 0.3), "corr": corr}}

def run_boundary_tests():
    x = np.ones(16)
    a = block(evolve(x)); b = evolve(block(x))
    return {"constant_signal_fixed": {"pass": bool(np.allclose(a, b))}}

if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {"name": "sim_em_classical_future_compression_future_from_external", "scope_note": SCOPE_NOTE,
               "classification": "classical_baseline", "tool_manifest": TOOL_MANIFEST,
               "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_em_classical_future_compression_future_from_external_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
