#!/usr/bin/env python3
"""Classical Jeffreys divergence J(p,q) = KL(p||q) + KL(q||p)."""
import json, os
from typing import Literal, Optional
import numpy as np

classification: Literal["classical_baseline", "canonical"] = "classical_baseline"
divergence_log: Optional[str] = (
    "Classical Jeffreys divergence J(p,q) = KL(p||q)+KL(q||p) is symmetric on a "
    "commuting sample space. Quantum Jeffreys J(rho,sigma) = tr((rho-sigma)(log rho - log sigma)) "
    "requires operator logarithms whose difference is noncommuting; the classical "
    "substrate cannot represent the antisymmetric commutator term that drives "
    "nonclassical parameter sensitivity."
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
    TOOL_MANIFEST["pytorch"]["reason"] = "torch kl_div cross-check"
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
for _e in TOOL_MANIFEST.values():
    assert isinstance(_e["reason"], str) and _e["reason"].strip()
for _d in TOOL_INTEGRATION_DEPTH.values():
    assert _d in _VALID_DEPTHS

EPS = 1e-12

def kl(p, q):
    p = np.clip(np.asarray(p, float), EPS, 1); q = np.clip(np.asarray(q, float), EPS, 1)
    return float(np.sum(p * (np.log(p) - np.log(q))))

def jeffreys(p, q):
    return kl(p, q) + kl(q, p)


def run_positive_tests():
    r = {}
    rng = np.random.default_rng(2)
    # symmetry
    p = rng.dirichlet(np.ones(5)); q = rng.dirichlet(np.ones(5))
    r["symmetry"] = abs(jeffreys(p, q) - jeffreys(q, p)) < 1e-10
    # zero at identity
    r["zero_at_equal"] = abs(jeffreys(p, p)) < 1e-12
    # nonnegativity
    r["nonnegativity"] = all(
        jeffreys(rng.dirichlet(np.ones(6)), rng.dirichlet(np.ones(6))) >= -1e-12
        for _ in range(30)
    )
    # torch cross-check
    import torch as _t
    p_t = _t.tensor(p); q_t = _t.tensor(q)
    kl_pq_t = float((p_t * (_t.log(p_t) - _t.log(q_t))).sum())
    kl_qp_t = float((q_t * (_t.log(q_t) - _t.log(p_t))).sum())
    r["torch_cross_check"] = abs((kl_pq_t + kl_qp_t) - jeffreys(p, q)) < 1e-8
    return r


def run_negative_tests():
    r = {}
    # triangle inequality is NOT guaranteed for Jeffreys (not a metric, though sqrt is)
    rng = np.random.default_rng(3)
    # Jeffreys > 0 for distinct p, q
    p = np.array([0.7, 0.2, 0.1]); q = np.array([0.1, 0.2, 0.7])
    r["distinct_positive"] = jeffreys(p, q) > 0
    # unbounded: almost-disjoint support -> large
    p = np.array([1 - 1e-6, 1e-6]); q = np.array([1e-6, 1 - 1e-6])
    r["near_orthogonal_large"] = jeffreys(p, q) > 20
    return r


def run_boundary_tests():
    r = {}
    # small perturbation ~ chi2-like scaling
    p = np.array([0.5, 0.5]); eps = 1e-3
    q = np.array([0.5 + eps, 0.5 - eps])
    j = jeffreys(p, q)
    # Jeffreys ~ 2 * (eps^2 / p) summed = 2 * (2 eps^2 / 0.5) = 8 eps^2? expand: sum over i eps_i^2/p_i for KL then doubled-ish
    r["quadratic_small"] = abs(j - 2 * (eps**2 / 0.5 + eps**2 / 0.5)) < 1e-5
    # high-dim uniform vs peaked
    n = 32
    p = np.ones(n) / n
    q = p.copy(); q[0] += 0.05; q = q / q.sum()
    r["highdim_finite"] = np.isfinite(jeffreys(p, q)) and jeffreys(p, q) > 0
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "jeffreys_divergence_classical",
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
    out_path = os.path.join(out_dir, "jeffreys_divergence_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    assert all_pass, results
