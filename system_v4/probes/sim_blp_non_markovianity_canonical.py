#!/usr/bin/env python3
"""
sim_blp_non_markovianity_canonical.py

Lane C nonclassical dynamics sim.

Claim (candidate, not theorem): the Breuer-Laine-Piilo (BLP) measure of
non-Markovianity is strictly positive for an amplitude-damping channel with
a time-dependent rate gamma(t) that goes negative (non-Markovian regime),
and vanishes (to numerical tolerance) when gamma(t) >= 0 for all t.

Measurable gap:  N_BLP(non_markov) - N_BLP(markov)  >  tolerance.

Load-bearing tool: pytorch (numerical density-matrix evolution + trace norm).
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================
TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Complex tensor ODE integration of Lindblad amplitude damping and "
        "trace-norm distinguishability D(t) = 0.5*||rho1(t)-rho2(t)||_1; "
        "the BLP derivative sign test is computed from torch tensors."
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


classification = "canonical"


# =====================================================================
# CORE EVOLUTION
# =====================================================================

def _evolve_amp_damping(gamma_fn, rho0, t_grid):
    """
    Time-dependent amplitude damping on a qubit via master equation
      drho/dt = gamma(t) [ sigma_- rho sigma_+ - 0.5 {sigma_+ sigma_-, rho} ].
    Returns list of density matrices (torch.complex128) on t_grid.
    """
    sm = torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=torch.complex128)
    sp = sm.conj().T
    spsm = sp @ sm
    rho = rho0.clone()
    out = [rho.clone()]
    for i in range(1, len(t_grid)):
        dt = float(t_grid[i] - t_grid[i - 1])
        g = float(gamma_fn(0.5 * (t_grid[i] + t_grid[i - 1])))
        drho = g * (sm @ rho @ sp - 0.5 * (spsm @ rho + rho @ spsm))
        rho = rho + dt * drho
        out.append(rho.clone())
    return out


def _trace_norm(A):
    # 0.5 * ||A||_1, but caller multiplies by 0.5 externally if needed.
    evals = torch.linalg.eigvalsh((A.conj().T @ A))
    evals = torch.clamp(evals.real, min=0.0)
    return torch.sum(torch.sqrt(evals))


def _blp_measure(gamma_fn, t_grid):
    rho1 = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=torch.complex128)
    rho2 = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=torch.complex128)
    traj1 = _evolve_amp_damping(gamma_fn, rho1, t_grid)
    traj2 = _evolve_amp_damping(gamma_fn, rho2, t_grid)
    d = [0.5 * float(_trace_norm(traj1[i] - traj2[i])) for i in range(len(t_grid))]
    total = 0.0
    for i in range(1, len(d)):
        delta = d[i] - d[i - 1]
        if delta > 0:
            total += delta
    return total, d


def _markov_gamma(t):
    return 0.5


def _non_markov_gamma(t):
    # Oscillating rate that goes negative -> revivals of distinguishability.
    return 0.5 * np.cos(2.0 * t)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    t_grid = np.linspace(0.0, 6.0, 1201)
    n_mark, _ = _blp_measure(_markov_gamma, t_grid)
    n_nonm, d_nonm = _blp_measure(_non_markov_gamma, t_grid)
    gap = n_nonm - n_mark
    results["N_BLP_markov"] = n_mark
    results["N_BLP_non_markov"] = n_nonm
    results["gap"] = gap
    # Positive: non-Markov strictly larger with meaningful margin.
    results["pass"] = bool(gap > 0.05 and n_nonm > 0.05)
    # Revival evidence: D(t) must increase at least once.
    revival = any(d_nonm[i] > d_nonm[i - 1] + 1e-6 for i in range(1, len(d_nonm)))
    results["revival_detected"] = revival
    results["pass"] = bool(results["pass"] and revival)
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    t_grid = np.linspace(0.0, 6.0, 1201)
    # Markovian case must be ~ 0 (CP-divisible channel).
    n_mark, d_mark = _blp_measure(_markov_gamma, t_grid)
    monotone = all(d_mark[i] <= d_mark[i - 1] + 1e-9 for i in range(1, len(d_mark)))
    results["N_BLP_markov"] = n_mark
    results["D_monotone_nonincreasing"] = monotone
    results["pass"] = bool(n_mark < 1e-6 and monotone)
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    # gamma identically 0 -> no evolution -> N_BLP = 0 exactly.
    t_grid = np.linspace(0.0, 2.0, 201)
    n_zero, d_zero = _blp_measure(lambda t: 0.0, t_grid)
    results["N_BLP_zero_rate"] = n_zero
    results["D_constant"] = bool(max(d_zero) - min(d_zero) < 1e-12)
    results["pass"] = bool(n_zero < 1e-12 and results["D_constant"])
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = bool(pos.get("pass") and neg.get("pass") and bnd.get("pass"))
    results = {
        "name": "sim_blp_non_markovianity_canonical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "gap": pos.get("gap"),
        "summary": {"all_pass": all_pass},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "blp_non_markovianity_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass={all_pass} gap={pos.get('gap')}")
    raise SystemExit(0 if all_pass else 1)
