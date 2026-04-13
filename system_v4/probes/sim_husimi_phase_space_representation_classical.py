#!/usr/bin/env python3
"""Classical baseline: husimi_phase_space_representation.
Classical Gaussian phase-space density Q(q,p) on a discretized grid; checks
non-negativity, normalization, and concentration around (q0,p0). Innately misses
quantum coherent-state overcompleteness / noncommutative phase space structure."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"
NAME = "husimi_phase_space_representation"

def husimi_gaussian(q, p, q0, p0, sigma=1.0):
    return (1.0 / (2 * np.pi * sigma**2)) * np.exp(-((q - q0)**2 + (p - p0)**2) / (2 * sigma**2))

def grid():
    q = np.linspace(-6, 6, 121); p = np.linspace(-6, 6, 121)
    Q, P = np.meshgrid(q, p); return q, p, Q, P

def run_positive_tests():
    r = {}; q, p, Q, P = grid()
    for (q0, p0) in [(0, 0), (1.5, -0.5), (-2, 2)]:
        H = husimi_gaussian(Q, P, q0, p0)
        r[f"nonneg_{q0}_{p0}"] = bool(np.all(H >= 0))
        norm = np.trapz(np.trapz(H, q, axis=1), p)
        r[f"normalized_{q0}_{p0}"] = bool(abs(norm - 1.0) < 5e-3)
        # centroid
        cq = np.trapz(np.trapz(H * Q, q, axis=1), p)
        cp = np.trapz(np.trapz(H * P, q, axis=1), p)
        r[f"centroid_{q0}_{p0}"] = bool(abs(cq - q0) < 5e-2 and abs(cp - p0) < 5e-2)
    return r

def run_negative_tests():
    r = {}; q, p, Q, P = grid()
    # a signed "quasi-distribution" must violate non-negativity
    W = husimi_gaussian(Q, P, 0, 0) - husimi_gaussian(Q, P, 1.5, 1.5) * 0.9
    r["signed_violates_nonneg"] = bool(np.any(W < 0))
    # unnormalized should not integrate to 1
    H = 2.5 * husimi_gaussian(Q, P, 0, 0)
    norm = np.trapz(np.trapz(H, q, axis=1), p)
    r["unnormalized_detected"] = bool(abs(norm - 1.0) > 0.1)
    return r

def run_boundary_tests():
    r = {}; q, p, Q, P = grid()
    # very narrow sigma -> concentrated
    H = husimi_gaussian(Q, P, 0, 0, sigma=0.3)
    r["narrow_max_at_origin"] = bool(np.unravel_index(np.argmax(H), H.shape) == (60, 60))
    # very broad
    H = husimi_gaussian(Q, P, 0, 0, sigma=3.0)
    r["broad_smooth"] = bool(H.max() / H.min() < 1e3)
    return r

if __name__ == "__main__":
    results = {"name": NAME, "classification": "classical_baseline",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(),
               "boundary": run_boundary_tests(),
               "classical_captured": "non-negative Gaussian phase-space density, normalization, centroid",
               "innately_missing": "coherent-state overcompleteness, quantum smoothing of Wigner->Husimi, noncommuting q,p"}
    results["all_pass"] = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", f"{NAME}_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={results['all_pass']} -> {out}")
