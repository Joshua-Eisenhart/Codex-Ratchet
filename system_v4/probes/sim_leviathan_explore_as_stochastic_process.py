#!/usr/bin/env python3
"""
Leviathan EXPLORE framing: Markov chain of group emergence / collapse.

Framing assumption:
  States = which groups are alive. Transition matrix encodes emergence
  (birth) and collapse (death) rates. Stationary distribution reveals
  whether diversity persists or monoculture dominates.

Blind spot:
  - Memoryless assumption (no path dependence).
  - Fixed transition rates; real societies have regime shifts.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {"numpy": {"tried": True, "used": True, "reason": "stationary via eigen-decomp"}}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def stationary(P):
    vals, vecs = np.linalg.eig(P.T)
    idx = int(np.argmin(np.abs(vals - 1.0)))
    v = np.real(vecs[:, idx])
    v = v / v.sum()
    return v


def run_positive_tests():
    # diverse regime: balanced transitions
    P = np.array([[0.7,0.2,0.1],[0.2,0.6,0.2],[0.15,0.25,0.6]])
    pi = stationary(P)
    H = float(-(pi[pi>0]*np.log(pi[pi>0])).sum())
    return {"pi": pi.tolist(), "entropy": H, "pass_diverse": H > 0.9}

def run_negative_tests():
    # absorbing centralized state
    P = np.array([[1.0,0.0,0.0],[0.8,0.2,0.0],[0.7,0.1,0.2]])
    pi = stationary(P)
    return {"pi": pi.tolist(), "pass_absorbing": pi[0] > 0.95}

def run_boundary_tests():
    P = np.eye(3)  # all states absorbing
    pi = stationary(P)
    return {"pi": pi.tolist(), "pass": abs(pi.sum()-1) < 1e-6}


if __name__ == "__main__":
    results = {
        "name": "leviathan_explore_as_stochastic_process",
        "framing_assumption": "group emergence/collapse = Markov chain; stationary dist = long-run regime",
        "blind_spot": "memoryless; no regime shifts",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "leviathan_explore_as_stochastic_process_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({k: results[k] for k in ["name","positive","negative","boundary"]}, indent=2, default=str))
