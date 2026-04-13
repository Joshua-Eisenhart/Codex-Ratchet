#!/usr/bin/env python3
"""Classical baseline: admissibility_manifold_mc.
MC sampler over a classical feasible region (box + linear constraints). By design
this SUBSTRATE cannot represent probe-dependent indistinguishability — divergence
from nonclassical admissibility is logged as `innately_missing`, not as a failure."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"
NAME = "admissibility_manifold_mc"

def sample_box(n, d, rng): return rng.uniform(-1, 1, size=(n, d))

def admissible(x):
    # classical region: L1 ball intersect halfspace sum>=0
    return (np.sum(np.abs(x), axis=-1) <= 1.0) & (np.sum(x, axis=-1) >= -0.25)

def run_positive_tests():
    r = {}; rng = np.random.default_rng(0)
    for d in (2, 3, 5):
        X = sample_box(200000, d, rng)
        m = admissible(X)
        frac = m.mean()
        r[f"nonempty_d{d}"] = bool(frac > 1e-3)
        r[f"bounded_d{d}"] = bool(np.all(np.abs(X[m]).max(axis=1) <= 1.0 + 1e-12))
        # monotone under tightening L1 radius
        m2 = (np.sum(np.abs(X), axis=-1) <= 0.5) & (np.sum(X, axis=-1) >= -0.25)
        r[f"monotone_tighten_d{d}"] = bool(m2.sum() <= m.sum())
    return r

def run_negative_tests():
    r = {}; rng = np.random.default_rng(1)
    X = sample_box(5000, 3, rng)
    # infeasible constraint
    infeas = (np.sum(np.abs(X), axis=-1) <= 1.0) & (np.sum(X, axis=-1) >= 10.0)
    r["infeasible_empty"] = bool(infeas.sum() == 0)
    # point outside L1 ball rejected
    r["outside_rejected"] = bool(not admissible(np.array([2.0, 0, 0])))
    return r

def run_boundary_tests():
    r = {}
    # boundary of L1 ball
    r["boundary_point_in"] = bool(admissible(np.array([1.0, 0, 0])))
    # zero always admissible
    r["origin_in"] = bool(admissible(np.zeros(4)))
    return r

if __name__ == "__main__":
    divergence = {
        "note": "classical substrate cannot encode probe-relative indistinguishability",
        "missing_axes": ["context-dependent admissibility", "coupling-induced exclusion",
                         "nonclassical constraint interference"],
    }
    results = {"name": NAME, "classification": "classical_baseline",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(),
               "boundary": run_boundary_tests(),
               "classical_captured": "deterministic MC feasibility fraction on linear+L1 constraints",
               "innately_missing": "probe-relative admissibility, nonclassical exclusion under coupling",
               "divergence_log": divergence}
    results["all_pass"] = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", f"{NAME}_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={results['all_pass']} -> {out}")
