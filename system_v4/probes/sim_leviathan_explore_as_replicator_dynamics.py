#!/usr/bin/env python3
"""
Leviathan EXPLORE framing: replicator dynamics.

Framing assumption:
  Groups = strategies; population shares evolve by replicator eq with payoff
  matrix A. Diversity-rewarding A sustains mixed equilibrium; centralizing A
  drives fixation of one strategy.

Blind spot:
  - Assumes well-defined payoff matrix (strategic rationality).
  - No innovation / mutation (closed strategy set).
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {"numpy": {"tried": True, "used": True, "reason": "replicator ODE"}}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def replicator(x, A, T=500, dt=0.01):
    for _ in range(T):
        fit = A @ x
        avg = x @ fit
        x = x + dt * x * (fit - avg)
        x = np.clip(x, 0, None); x /= x.sum()
    return x

def shannon(x):
    x = x[x > 0]
    return float(-(x*np.log(x)).sum())


def run_positive_tests():
    # rock-paper-scissors-like: mixed equilibrium
    A = np.array([[0,-1,1],[1,0,-1],[-1,1,0]], float)
    x0 = np.array([0.4,0.35,0.25])
    xf = replicator(x0, A)
    return {"entropy": shannon(xf), "pass_mixed": shannon(xf) > 0.8}

def run_negative_tests():
    # centralizing: one dominant strategy
    A = np.diag([2.0, 0.1, 0.1])
    x0 = np.array([0.34,0.33,0.33])
    xf = replicator(x0, A)
    return {"entropy": shannon(xf), "pass_fixation": shannon(xf) < 0.3}

def run_boundary_tests():
    # uniform payoff: drift only
    A = np.ones((3,3))
    x0 = np.array([0.5,0.3,0.2])
    xf = replicator(x0, A)
    return {"final": xf.tolist(), "pass": abs(xf.sum()-1) < 1e-6}


if __name__ == "__main__":
    results = {
        "name": "leviathan_explore_as_replicator_dynamics",
        "framing_assumption": "group shares evolve by replicator eq over payoff matrix",
        "blind_spot": "closed strategy set; no innovation/mutation",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "leviathan_explore_as_replicator_dynamics_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({k: results[k] for k in ["name","positive","negative","boundary"]}, indent=2, default=str))
