#!/usr/bin/env python3
"""Classical baseline sim: helstrom_guess_bound lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: Helstrom bound for two equiprobable states
  p_success_max = 1/2 + 1/4 * || rho_0 - rho_1 ||_1
numerically verified against an optimal projective measurement on the
eigenbasis of (rho_0 - rho_1).
Innately missing: POVM-level admissibility under constraint geometry;
coupling-dependent bound violations. Classical baseline assumes the observer
has full operator freedom — useful failure data where shell constraints
forbid the optimal projector.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "trace norm + eigendecomp"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def trace_norm(A):
    return float(np.sum(np.abs(np.linalg.eigvalsh((A + A.conj().T) / 2))))

def helstrom_bound(rho0, rho1):
    return 0.5 + 0.25 * trace_norm(rho0 - rho1)

def helstrom_optimal_success(rho0, rho1):
    D = (rho0 - rho1) / 2
    w, V = np.linalg.eigh(D)
    Pp = V[:, w > 0] @ V[:, w > 0].conj().T if np.any(w > 0) else np.zeros_like(D)
    Pm = np.eye(D.shape[0]) - Pp
    return 0.5 * (np.real(np.trace(Pp @ rho0)) + np.real(np.trace(Pm @ rho1)))

def run_positive_tests():
    rho0 = np.diag([1.0, 0.0]); rho1 = np.diag([0.0, 1.0])
    p_bound = helstrom_bound(rho0, rho1)
    p_opt = helstrom_optimal_success(rho0, rho1)
    return {
        "orthogonal_bound_is_one": abs(p_bound - 1.0) < 1e-9,
        "optimal_matches_bound": abs(p_opt - p_bound) < 1e-9,
    }

def run_negative_tests():
    # identical states -> bound = 0.5, and random measurement can't beat it
    rho = np.diag([0.6, 0.4])
    p_bound = helstrom_bound(rho, rho)
    return {
        "identical_states_bound_half": abs(p_bound - 0.5) < 1e-9,
        "no_better_than_guess": p_bound <= 0.5 + 1e-9,
    }

def run_boundary_tests():
    # slightly different states: bound in (0.5, 1)
    rho0 = np.diag([0.6, 0.4]); rho1 = np.diag([0.4, 0.6])
    p = helstrom_bound(rho0, rho1)
    return {
        "in_range": 0.5 < p < 1.0,
        "optimal_le_bound": helstrom_optimal_success(rho0, rho1) <= p + 1e-9,
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "helstrom_guess_bound_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "summary": {"all_pass": all_pass},
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "helstrom_guess_bound_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
