#!/usr/bin/env python3
"""
Leviathan EXPLORE framing: thermodynamic work-extraction.

Framing assumption:
  Groups = thermal reservoirs at temperatures T_i (value-diversities).
  Work extractable ~ temperature gradient. Monoculture = all T_i equal =
  heat death, zero work. Leviathan mines potential BY maintaining gradient.

Blind spot:
  - Equilibrium/quasi-static assumption.
  - Reservoirs independent; ignores cross-group feedback.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {"numpy": {"tried": True, "used": True, "reason": "carnot-style work calc"}}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def max_work(Ts, Q=1.0):
    Ts = np.asarray(Ts, float)
    Th, Tc = Ts.max(), Ts.min()
    if Th <= 0: return 0.0
    eta = 1 - Tc/Th
    return float(max(0.0, eta * Q))

def gradient_entropy(Ts):
    Ts = np.asarray(Ts, float)
    p = Ts / Ts.sum()
    return float(-(p*np.log(p+1e-12)).sum())


def run_positive_tests():
    Ts = [1.0, 2.0, 3.5, 5.0]
    W = max_work(Ts)
    return {"work": W, "pass_positive_work": W > 0.5}

def run_negative_tests():
    Ts = [2.0, 2.0, 2.0, 2.0]  # monoculture / heat death
    W = max_work(Ts)
    return {"work": W, "pass_zero_work": W < 1e-9}

def run_boundary_tests():
    Ts = [1e-6, 5.0]  # huge gradient, efficiency → 1
    return {"eta_limit_work": max_work(Ts), "pass": max_work(Ts) > 0.99}


if __name__ == "__main__":
    results = {
        "name": "leviathan_explore_as_thermodynamic_engine",
        "framing_assumption": "group value-diversities act as thermal reservoirs; work = temperature gradient",
        "blind_spot": "quasi-static; reservoirs independent",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "leviathan_explore_as_thermodynamic_engine_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({k: results[k] for k in ["name","positive","negative","boundary"]}, indent=2, default=str))
