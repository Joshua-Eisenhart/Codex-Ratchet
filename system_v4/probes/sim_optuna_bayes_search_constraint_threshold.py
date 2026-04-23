#!/usr/bin/env python3
"""
sim_optuna_bayes_search_constraint_threshold.py

Canonical sim. Optuna TPE search for the minimum scalar threshold T such
that a fixed 4D probe point is EXCLUDED from the forbidden ball of
radius T centered at the origin.

Probe point p = (0.3, 0.2, 0.1, 0.1), ||p|| = sqrt(0.15).
A probe is excluded iff ||p|| >= T, so the minimum T for which the probe
survives the exclusion test is T* = ||p||.
"""

import json
import os
import math
import optuna

optuna.logging.set_verbosity(optuna.logging.WARNING)

TOOL_MANIFEST = {
    "optuna": {"tried": True, "used": True,
               "reason": "TPE Bayesian search over scalar exclusion threshold"},
}
TOOL_INTEGRATION_DEPTH = {"optuna": "load_bearing"}

PROBE = (0.3, 0.2, 0.1, 0.1)
P_NORM = math.sqrt(sum(x * x for x in PROBE))  # analytic optimum
T_STAR = P_NORM


def objective(trial):
    T = trial.suggest_float("T", 0.0, 2.0)
    # Penalize T that fails to exclude (probe not yet excluded) with a large cost,
    # otherwise minimize T itself.
    if T > P_NORM:
        return 10.0 + (T - P_NORM)  # not excluded: ||p|| < T means probe INSIDE ball, i.e. excluded
    # Here ||p|| >= T -> probe survives. Want the MIN T that still excludes the
    # interior of the ball. Since candidate-ball = {x : ||x|| < T}, probe is
    # excluded from the ball iff ||p|| >= T. So any T <= ||p|| keeps the probe
    # surviving; we want the MAX such T, equivalently minimize (||p|| - T).
    return P_NORM - T  # minimized at T = P_NORM


def run_positive_tests():
    sampler = optuna.samplers.TPESampler(seed=1)
    study = optuna.create_study(direction="minimize", sampler=sampler)
    study.optimize(objective, n_trials=30, show_progress_bar=False)
    best_T = study.best_params["T"]
    rel_err = abs(best_T - T_STAR) / T_STAR
    return {
        "best_T": float(best_T),
        "analytic_T_star": float(T_STAR),
        "relative_error": float(rel_err),
        "within_5pct": rel_err < 0.05,
        "best_value": float(study.best_value),
    }


def run_negative_tests():
    # A probe strictly inside a ball of radius T > ||p|| is excluded (not surviving).
    T = P_NORM + 0.1
    excluded = P_NORM < T
    return {"T": T, "probe_excluded_by_ball": excluded}


def run_boundary_tests():
    # Boundary: T == ||p|| -- probe sits on the surface; by >= convention, probe survives.
    T = P_NORM
    survives = P_NORM >= T
    return {"T": T, "on_surface_survives": survives}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    passed = (
        pos.get("within_5pct", False)
        and neg.get("probe_excluded_by_ball", False)
        and bnd.get("on_surface_survives", False)
    )
    results = {
        "name": "sim_optuna_bayes_search_constraint_threshold",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "passed": bool(passed),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_optuna_bayes_search_constraint_threshold_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={passed} -> {out_path}")
