#!/usr/bin/env python3
"""
Leviathan EXPLORE framing: cellular automaton.

Framing assumption:
  Civilization = 2D lattice of groups; each cell has potential level 0..K.
  Local rules: exchange flattens gradients (diversity), centralization rule
  routes potential to max-neighbor (authoritarian attractor).

Blind spot:
  - Local-only interactions; ignores long-range financial/media links.
  - Discrete state space — no continuous negotiation.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {"numpy": {"tried": True, "used": True, "reason": "CA lattice update"}}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def step_diffusive(grid):
    pad = np.pad(grid, 1, mode="wrap")
    nbrs = (pad[:-2,1:-1] + pad[2:,1:-1] + pad[1:-1,:-2] + pad[1:-1,2:]) / 4.0
    return 0.5 * grid + 0.5 * nbrs

def step_centralizing(grid):
    pad = np.pad(grid, 1, mode="wrap")
    nbr_max = np.maximum.reduce([pad[:-2,1:-1], pad[2:,1:-1], pad[1:-1,:-2], pad[1:-1,2:]])
    # each cell gives half potential to its max neighbor
    return 0.5 * grid + 0.5 * nbr_max * (nbr_max > grid)

def variance_trace(grid, step, T=40):
    vs = []
    g = grid.copy()
    for _ in range(T):
        g = step(g); vs.append(float(g.var()))
    return vs, g


def run_positive_tests():
    rng = np.random.default_rng(1)
    g0 = rng.random((12,12))
    vs, gf = variance_trace(g0, step_diffusive)
    return {"diffusive_final_var": vs[-1], "diffusive_initial_var": vs[0],
            "pass_variance_decreases": vs[-1] < vs[0]}

def run_negative_tests():
    rng = np.random.default_rng(2)
    g0 = rng.random((12,12))
    vs, gf = variance_trace(g0, step_centralizing)
    maxfrac = float(gf.max() / (gf.sum() + 1e-9))
    return {"central_final_maxfrac": maxfrac,
            "pass_concentrates": maxfrac > (1.0/(12*12)) * 3}

def run_boundary_tests():
    g = np.ones((4,4))
    vs, gf = variance_trace(g, step_diffusive, T=5)
    return {"uniform_stays_uniform": bool(vs[-1] < 1e-12), "pass": vs[-1] < 1e-12}


if __name__ == "__main__":
    results = {
        "name": "leviathan_explore_as_cellular_automaton",
        "framing_assumption": "civilization = local-rule lattice; diversity=diffusion, centralization=max-routing",
        "blind_spot": "no long-range coupling; discrete state",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "leviathan_explore_as_cellular_automaton_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({k: results[k] for k in ["name","positive","negative","boundary"]}, indent=2, default=str))
