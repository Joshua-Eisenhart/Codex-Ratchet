#!/usr/bin/env python3
"""Classical Chernoff bound for symmetric binary hypothesis testing.

Lane B classical_baseline: error exponent for i.i.d. classical distributions.
"""
import json
import os
from typing import Literal, Optional
import numpy as np
from scipy.optimize import minimize_scalar

classification: Literal["classical_baseline", "canonical"] = "classical_baseline"
divergence_log: Optional[str] = (
    "Classical Chernoff exponent C(p,q) = -min_s log sum p^s q^(1-s) assumes "
    "commuting distributions on the same sample space. Quantum Chernoff "
    "bound -log min_s tr(rho^s sigma^(1-s)) requires noncommuting operator "
    "powers and cannot be reduced to pointwise probability ratios when "
    "[rho, sigma] != 0. This classical substrate captures diagonal cases "
    "only; it cannot encode interference in off-diagonal hypothesis tests."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not_attempted"},
    "pyg": {"tried": False, "used": False, "reason": "not_attempted"},
    "z3": {"tried": False, "used": False, "reason": "not_attempted"},
    "cvc5": {"tried": False, "used": False, "reason": "not_attempted"},
    "sympy": {"tried": False, "used": False, "reason": "not_attempted"},
    "clifford": {"tried": False, "used": False, "reason": "not_attempted"},
    "geomstats": {"tried": False, "used": False, "reason": "not_attempted"},
    "e3nn": {"tried": False, "used": False, "reason": "not_attempted"},
    "rustworkx": {"tried": False, "used": False, "reason": "not_attempted"},
    "xgi": {"tried": False, "used": False, "reason": "not_attempted"},
    "toponetx": {"tried": False, "used": False, "reason": "not_attempted"},
    "gudhi": {"tried": False, "used": False, "reason": "not_attempted"},
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "cross-check of classical Chernoff exponent with torch tensor reductions"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "supportive",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

_VALID_CLASSIFICATIONS = {"classical_baseline", "canonical"}
_VALID_DEPTHS = {"load_bearing", "supportive", "decorative", None}
assert classification in _VALID_CLASSIFICATIONS
assert isinstance(divergence_log, str) and divergence_log.strip()
for _t, _e in TOOL_MANIFEST.items():
    assert isinstance(_e["reason"], str) and _e["reason"].strip()
for _t, _d in TOOL_INTEGRATION_DEPTH.items():
    assert _d in _VALID_DEPTHS


def chernoff_exponent(p: np.ndarray, q: np.ndarray) -> float:
    p = np.asarray(p, dtype=float); q = np.asarray(q, dtype=float)
    p = p / p.sum(); q = q / q.sum()
    def obj(s):
        s = float(s)
        # sum p^s q^(1-s), mask zeros safely
        mask = (p > 0) & (q > 0)
        return float(np.sum(p[mask]**s * q[mask]**(1 - s)))
    res = minimize_scalar(obj, bounds=(1e-6, 1 - 1e-6), method="bounded")
    return float(-np.log(res.fun))


def run_positive_tests():
    r = {}
    # identical distributions -> exponent 0
    p = np.array([0.5, 0.5])
    r["identical_zero"] = abs(chernoff_exponent(p, p)) < 1e-8
    # two-point distributions with known Bhattacharyya bound
    p = np.array([0.9, 0.1]); q = np.array([0.1, 0.9])
    c = chernoff_exponent(p, q)
    # symmetric by construction, c must be positive and <= log 2
    r["symmetric_positive"] = (c > 0) and (c <= np.log(2) + 1e-9)
    # symmetry C(p,q)==C(q,p)
    r["symmetry"] = abs(chernoff_exponent(p, q) - chernoff_exponent(q, p)) < 1e-6
    # torch cross-check on Bhattacharyya coefficient (s=0.5)
    import torch as _t
    bc = float(_t.sum(_t.sqrt(_t.tensor(p)) * _t.sqrt(_t.tensor(q))))
    r["bhattacharyya_bound"] = c >= -np.log(bc) - 1e-6
    return r


def run_negative_tests():
    r = {}
    # orthogonal-support distributions should give exponent = +inf (here large)
    p = np.array([1.0, 0.0]); q = np.array([0.0, 1.0])
    try:
        c = chernoff_exponent(p, q)
        r["orthogonal_infinite"] = not np.isfinite(c) or c > 10
    except Exception:
        r["orthogonal_infinite"] = True
    # malformed distribution (negative) should be caught upstream; here just check
    # that normalization prevents garbage: shifted but renormalizable
    p = np.array([0.3, 0.7]); q = np.array([0.7, 0.3])
    c = chernoff_exponent(p, q)
    r["not_identical_positive"] = c > 0
    return r


def run_boundary_tests():
    r = {}
    # near-identical tiny perturbation -> small but nonneg exponent
    p = np.array([0.5, 0.5]); q = np.array([0.5 + 1e-6, 0.5 - 1e-6])
    c = chernoff_exponent(p, q)
    r["small_perturbation_nonneg"] = c >= -1e-10
    r["small_perturbation_small"] = c < 1e-6
    # high-dim uniform vs. slightly peaked
    n = 64
    p = np.ones(n) / n
    q = p.copy(); q[0] += 0.1; q = q / q.sum()
    c = chernoff_exponent(p, q)
    r["highdim_finite_positive"] = np.isfinite(c) and c > 0
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "chernoff_bound_classical",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "chernoff_bound_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    assert all_pass, results
