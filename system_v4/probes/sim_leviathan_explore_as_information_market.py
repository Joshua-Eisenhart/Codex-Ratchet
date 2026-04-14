#!/usr/bin/env python3
"""
Leviathan EXPLORE framing: information market.

Framing assumption:
  Human potential = mutual information I(G_i ; G_j) between group distributions.
  Wealth = sum of pairwise MI. Centralization = one group dominates all MI channels.

Blind spot:
  - Treats potential as fully fungible bits; ignores embodiment, meaning.
  - Assumes stationarity of group distributions.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {"numpy": {"tried": True, "used": True, "reason": "joint distributions, MI"},
                 "sympy": {"tried": False, "used": False, "reason": ""}}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "sympy": None}
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def mutual_information(P):
    P = P / P.sum()
    Px = P.sum(axis=1, keepdims=True)
    Py = P.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(P > 0, P / (Px * Py), 1.0)
        return float((P * np.log(ratio + 1e-15)).sum())


def diverse_joint(n=6, rng=None):
    rng = rng or np.random.default_rng(0)
    P = rng.dirichlet(np.ones(n*n)).reshape(n,n)
    # inject correlation
    P += 0.3 * np.eye(n)
    return P / P.sum()


def monoculture_joint(n=6):
    P = np.full((n,n), 1e-6)
    P[0,0] = 1.0
    return P / P.sum()


def run_positive_tests():
    MI = mutual_information(diverse_joint())
    return {"diverse_MI": MI, "pass": MI > 0}

def run_negative_tests():
    MI_mono = mutual_information(monoculture_joint())
    MI_div = mutual_information(diverse_joint())
    return {"mono_MI": MI_mono, "div_MI": MI_div, "pass_mono_lower": MI_mono < MI_div}

def run_boundary_tests():
    # independent = zero MI
    P = np.outer(np.ones(4)/4, np.ones(4)/4)
    return {"indep_MI": mutual_information(P), "pass": abs(mutual_information(P)) < 1e-9}


if __name__ == "__main__":
    results = {
        "name": "leviathan_explore_as_information_market",
        "framing_assumption": "potential = mutual information between group distributions",
        "blind_spot": "bits are fungible; ignores meaning/embodiment",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "leviathan_explore_as_information_market_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({k: results[k] for k in ["name","positive","negative","boundary"]}, indent=2, default=str))
