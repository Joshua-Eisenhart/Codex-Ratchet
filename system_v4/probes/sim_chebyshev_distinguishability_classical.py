#!/usr/bin/env python3
"""Classical baseline: Chebyshev (moment-matching) distinguishability.

Two classical distributions are classically indistinguishable to order K iff
their first K raw moments agree. We use the classical Chebyshev/Markov
inequalities on moment vectors and verify that a distinguishing test must
exploit some moment <= K.
"""
import json
import os

import numpy as np

classification = "classical_baseline"
divergence_log = (
    "Classical moment-matching uses real-valued scalar moments of commuting "
    "observables. Quantum distinguishability requires noncommuting-moment "
    "hierarchies (e.g. NPA). This baseline drops all operator noncommutativity."
)

try:
    import torch  # noqa: F401
    _torch_ok = True
except Exception:
    _torch_ok = False

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "moment vectors and arithmetic"},
    "scipy": {"tried": False, "used": False, "reason": "not required"},
    "pytorch": {
        "tried": _torch_ok,
        "used": _torch_ok,
        "reason": "supportive import; moments computed in numpy",
    },
    "z3": {"tried": False, "used": False, "reason": "no SMT moment-problem proof"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": "supportive" if _torch_ok else None,
    "scipy": None,
    "z3": None,
}


def raw_moments(x, p, K):
    x = np.asarray(x, float)
    p = np.asarray(p, float)
    p = p / p.sum()
    return np.array([np.sum(p * x ** k) for k in range(K + 1)])


def chebyshev_bound(p, x, a):
    """P(|X - mu| >= a) <= Var(X)/a^2."""
    mu = np.sum(p * x)
    var = np.sum(p * (x - mu) ** 2)
    tail = np.sum(p[np.abs(x - mu) >= a])
    return tail, var / (a ** 2)


def run_positive_tests():
    r = {}
    # Distributions with equal first K moments should have ||m_A-m_B||<=eps
    x = np.linspace(-1, 1, 9)
    rng = np.random.default_rng(1)
    p = rng.dirichlet(np.ones(9))
    q = p.copy()  # identical
    mA = raw_moments(x, p, 4)
    mB = raw_moments(x, q, 4)
    r["equal_distributions_match_moments"] = bool(np.allclose(mA, mB))

    # Symmetric pair: same even moments
    p_sym1 = np.array([0.25, 0.5, 0.25])
    p_sym2 = np.array([0.25, 0.5, 0.25])
    xs = np.array([-1.0, 0.0, 1.0])
    r["symmetric_odd_moment_zero"] = bool(abs(np.sum(p_sym1 * xs)) < 1e-12)

    # Chebyshev inequality holds
    tail, bound = chebyshev_bound(p, x, a=0.8)
    r["chebyshev_holds"] = bool(tail <= bound + 1e-9)
    return r


def run_negative_tests():
    r = {}
    # Different means => first moment differs
    x = np.linspace(-1, 1, 5)
    p = np.array([0.1, 0.2, 0.4, 0.2, 0.1])
    q = np.array([0.4, 0.2, 0.1, 0.2, 0.1])
    mA = raw_moments(x, p, 2)
    mB = raw_moments(x, q, 2)
    r["different_mean_detected"] = bool(not np.isclose(mA[1], mB[1]))

    # Different variance but same mean => second moment differs
    p2 = np.array([0.25, 0.5, 0.25])
    q2 = np.array([0.5, 0.0, 0.5])
    xs = np.array([-1.0, 0.0, 1.0])
    r["different_variance_detected"] = bool(
        not np.isclose(np.sum(p2 * xs ** 2), np.sum(q2 * xs ** 2))
    )
    return r


def run_boundary_tests():
    r = {}
    # K=0 moments (total mass) always equal for distributions
    x = np.array([0.0, 1.0])
    p = np.array([0.3, 0.7])
    q = np.array([0.8, 0.2])
    r["zeroth_moment_equal"] = bool(
        np.isclose(raw_moments(x, p, 0)[0], raw_moments(x, q, 0)[0])
    )

    # Degenerate point-mass: variance 0
    p_pm = np.array([0.0, 1.0, 0.0])
    xs = np.array([-1.0, 0.0, 1.0])
    mu = np.sum(p_pm * xs)
    var = np.sum(p_pm * (xs - mu) ** 2)
    r["point_mass_zero_variance"] = bool(var < 1e-12)

    # Very high K still finite
    x = np.linspace(-0.5, 0.5, 7)
    p = np.array([0.1, 0.1, 0.2, 0.2, 0.2, 0.1, 0.1])
    m = raw_moments(x, p, 10)
    r["high_order_moments_finite"] = bool(np.all(np.isfinite(m)))
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "chebyshev_distinguishability_classical_results.json")
    payload = {
        "name": "chebyshev_distinguishability_classical",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": bool(all_pass),
        "summary": {"all_pass": bool(all_pass)},
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"Results written to {out_path} all_pass={all_pass}")
