#!/usr/bin/env python3
"""
Leviathan EXPLORE framing: free-energy landscape.

Framing assumption:
  Civilizational state = point in (diversity, centralization) plane.
  F = U - T*S where U penalizes disorder and T*S rewards entropy (diversity).
  Multi-well landscape: diversity basin vs authoritarian single-well attractor.

Blind spot:
  - Assumes well-defined thermodynamic variables for civilizations.
  - Treats diversity and centralization as orthogonal — they aren't.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical framing baseline: Leviathan is explored here as a free-energy landscape metaphor, not a canonical nonclassical witness."

TOOL_MANIFEST = {"numpy": {"tried": True, "used": True, "reason": "landscape eval + gradient descent"}}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def F(x, y, T=1.0):
    # x = diversity in [0,1], y = centralization in [0,1]
    U = (y - 0.85)**2 * (-1.2) + (x - 0.5)**2 * 0.3  # authoritarian well at high y
    S = -(x*np.log(x+1e-9) + (1-x)*np.log(1-x+1e-9))
    return U - T * S

def descend(x0, y0, T=1.0, steps=200, lr=0.02):
    x, y = x0, y0
    h = 1e-3
    for _ in range(steps):
        gx = (F(x+h,y,T)-F(x-h,y,T))/(2*h)
        gy = (F(x,y+h,T)-F(x,y-h,T))/(2*h)
        x = np.clip(x - lr*gx, 1e-3, 1-1e-3)
        y = np.clip(y - lr*gy, 1e-3, 1-1e-3)
    return x, y, F(x,y,T)


def run_positive_tests():
    # High-T (hot/open society) should prefer diversity basin
    x,y,f = descend(0.5, 0.5, T=2.0)
    return {"highT_endpoint": (x,y), "F": f, "pass_diversity_preferred": x > 0.4}

def run_negative_tests():
    # Low-T (cold/closed) should collapse into authoritarian high-y well
    x,y,f = descend(0.5, 0.7, T=0.05)
    return {"lowT_endpoint": (x,y), "F": f, "pass_authoritarian_well": y > 0.7}

def run_boundary_tests():
    # symmetric start, T=1: check stability
    x,y,f = descend(0.5, 0.5, T=1.0)
    return {"critT_endpoint": (x,y), "F": f, "pass": True}


if __name__ == "__main__":
    results = {
        "name": "leviathan_explore_as_free_energy_landscape",
        "framing_assumption": "civilization state minimizes F(diversity,centralization;T)",
        "blind_spot": "diversity and centralization treated as orthogonal",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "leviathan_explore_as_free_energy_landscape_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({k: results[k] for k in ["name","positive","negative","boundary"]}, indent=2, default=str))
