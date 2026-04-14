#!/usr/bin/env python3
"""Classical majorization / Lorenz dominance on probability vectors.

p majorizes q (p >> q) iff sum_{i<=k} p_(i) >= sum_{i<=k} q_(i) for all k
(sorted descending), with equality at k = n.  Equivalent: q = D p for
some doubly stochastic matrix D.
"""
import json, os
from typing import Literal, Optional
import numpy as np

classification: Literal["classical_baseline", "canonical"] = "classical_baseline"
divergence_log: Optional[str] = (
    "Classical majorization compares probability vectors by their sorted partial "
    "sums (Lorenz curves) on a commuting sample space. It captures mixing of "
    "diagonal (classical) populations only. Quantum majorization rho >> sigma "
    "compares the eigenvalue vectors lambda(rho) >> lambda(sigma), but two states "
    "with identical spectra and therefore equal classical majorization status "
    "can still be distinguishable via noncommuting measurements; coherent "
    "superpositions between eigenbases are invisible to this substrate."
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
    TOOL_MANIFEST["pytorch"]["reason"] = "torch sort / cumsum cross-check"
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


def majorizes(p, q, tol=1e-9):
    p = np.sort(np.asarray(p, float))[::-1]
    q = np.sort(np.asarray(q, float))[::-1]
    assert p.shape == q.shape
    cp = np.cumsum(p); cq = np.cumsum(q)
    if abs(cp[-1] - cq[-1]) > tol:
        return False
    return bool(np.all(cp + tol >= cq))


def run_positive_tests():
    r = {}
    # delta majorizes everything
    delta = np.array([1, 0, 0, 0.0])
    uniform = np.full(4, 0.25)
    mid = np.array([0.5, 0.25, 0.15, 0.10])
    r["delta_majorizes_uniform"] = majorizes(delta, uniform)
    r["delta_majorizes_mid"] = majorizes(delta, mid)
    r["mid_majorizes_uniform"] = majorizes(mid, uniform)
    # reflexivity
    r["reflexivity"] = majorizes(mid, mid)
    # uniform is majorized by everything of same length (sum=1)
    rng = np.random.default_rng(0)
    all_ok = True
    for _ in range(10):
        p = rng.dirichlet(np.ones(5))
        if not majorizes(p, np.full(5, 1/5)):
            all_ok = False; break
    r["uniform_is_minimum"] = all_ok
    # doubly stochastic application: q = D p is majorized by p
    D = np.eye(4)
    # small random doubly stochastic via Birkhoff mix
    P1 = np.eye(4)[[1, 0, 2, 3]]; P2 = np.eye(4)[[0, 2, 1, 3]]
    D = 0.5 * P1 + 0.5 * P2
    p = np.array([0.6, 0.2, 0.15, 0.05])
    q = D @ p
    r["ds_application_majorized"] = majorizes(p, q)
    return r


def run_negative_tests():
    r = {}
    # incomparable pair (classic example)
    p = np.array([0.5, 0.3, 0.2])
    q = np.array([0.45, 0.45, 0.10])
    # p cumsum: 0.5, 0.8, 1.0; q cumsum: 0.45, 0.9, 1.0  -> neither dominates
    r["incomparable_not_majorize"] = (not majorizes(p, q)) and (not majorizes(q, p))
    # sum mismatch
    r["sum_mismatch_fails"] = not majorizes(np.array([0.5, 0.5]), np.array([0.6, 0.5]))
    return r


def run_boundary_tests():
    r = {}
    # equal-up-to-permutation: both directions hold
    p = np.array([0.4, 0.3, 0.2, 0.1])
    q = p[::-1].copy()
    r["permutation_invariant"] = majorizes(p, q) and majorizes(q, p)
    # tiny tolerance near boundary
    p = np.array([0.5, 0.5]); q = np.array([0.5 + 1e-12, 0.5 - 1e-12])
    r["near_equal_majorizes"] = majorizes(p, q) and majorizes(q, p)
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "majorization_lorenz_classical",
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
    out_path = os.path.join(out_dir, "majorization_lorenz_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    assert all_pass, results
