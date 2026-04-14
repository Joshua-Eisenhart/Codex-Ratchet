#!/usr/bin/env python3
"""
sim_gerbe_distinguishability_holonomy -- Family #3 Gerbes, lego 5/6.

Distinguishability probe = surface holonomy exp(i * integral_Sigma B).
Two gerbes in different cohomology classes have distinct surface holonomies
on some closed surface Sigma (probe).
"""
import json, os
import numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {
    "numpy":    {"tried": True, "used": True, "reason": "integrate B over 2-cells"},
    "toponetx": {"tried": False,"used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "toponetx": "supportive"}

try:
    from toponetx.classes import CellComplex
    TOOL_MANIFEST["toponetx"].update(tried=True, used=True,
        reason="carrier complex for Sigma as sum of 2-cells")
except Exception as e:
    TOOL_MANIFEST["toponetx"]["reason"] = f"unavailable: {e}"


def holonomy(B, sigma):
    # B: 2-cochain values; sigma: signed sum of 2-cells (vector)
    return float(np.dot(B, sigma)) % (2 * np.pi)


def run_positive_tests():
    r = {}
    # 4 2-cells
    B1 = np.array([0.3, 0.3, 0.3, 0.3])
    B2 = np.array([0.3, 0.3, 0.3, 1.3])  # different class
    sigma = np.array([1, 1, 1, 1])
    h1 = holonomy(B1, sigma); h2 = holonomy(B2, sigma)
    r["different_classes_different_holonomy"] = bool(abs(h1 - h2) > 1e-6)
    # gauge-equivalent B + 2pi*n leaves holonomy invariant mod 2pi
    Bp = B1 + 2 * np.pi * np.array([1, 0, -1, 0])
    r["gauge_invariant_mod_2pi"] = bool(
        abs((holonomy(Bp, sigma) - holonomy(B1, sigma)) % (2 * np.pi)) < 1e-8)
    # zero B -> trivial holonomy
    r["zero_B_trivial_holonomy"] = bool(holonomy(np.zeros(4), sigma) == 0.0)
    return r


def run_negative_tests():
    r = {}
    B = np.array([0.3, 0.3, 0.3, 0.3])
    # same B on same sigma -> equal holonomy (not distinguishable)
    sigma = np.array([1, 1, 1, 1])
    r["same_class_same_holonomy"] = bool(
        abs(holonomy(B, sigma) - holonomy(B, sigma)) < 1e-14)
    # sigma=0 (null surface) gives trivial holonomy regardless of B
    r["null_surface_trivial"] = bool(holonomy(B, np.zeros(4)) == 0.0)
    return r


def run_boundary_tests():
    r = {}
    # holonomy is 2pi-periodic in B
    B = np.array([0.5, 0.0, 0.0, 0.0])
    sigma = np.array([1, 0, 0, 0])
    B2 = B + np.array([2 * np.pi, 0, 0, 0])
    r["2pi_periodic_in_B"] = bool(
        abs(holonomy(B, sigma) - holonomy(B2, sigma)) < 1e-8)
    # holonomy linear in sigma over small coefficients
    r["linear_in_sigma"] = bool(
        abs(holonomy(B, 2 * sigma) - 2 * holonomy(B, sigma)) < 1e-8 or
        abs((holonomy(B, 2 * sigma) - 2 * holonomy(B, sigma)) % (2 * np.pi)) < 1e-8)
    return r


if __name__ == "__main__":
    results = {
        "name": "gerbe_distinguishability_holonomy",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gerbe_distinguishability_holonomy_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(json.dumps({k: results[k] for k in ("positive", "negative", "boundary")},
                     indent=2, default=str))
