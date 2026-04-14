#!/usr/bin/env python3
"""Classical baseline: Hellinger distance on categorical distributions.

H^2(p,q) = 1 - sum_i sqrt(p_i q_i). Satisfies 0 <= H <= 1, symmetry, triangle
inequality, and H^2 <= TV <= sqrt(2) * H.
"""
import json
import os

import numpy as np

classification = "classical_baseline"
divergence_log = (
    "Classical Hellinger uses commuting probability vectors on a fixed "
    "categorical alphabet. Quantum Hellinger (Bures) uses fidelity of density "
    "matrices with noncommuting spectra; this baseline drops operator "
    "structure."
)

try:
    import torch  # noqa: F401
    _torch_ok = True
except Exception:
    _torch_ok = False

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "Bhattacharyya coefficient"},
    "scipy": {"tried": False, "used": False, "reason": "not required"},
    "pytorch": {
        "tried": _torch_ok,
        "used": _torch_ok,
        "reason": "supportive import only",
    },
    "z3": {"tried": False, "used": False, "reason": "no SMT claim"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": "supportive" if _torch_ok else None,
    "scipy": None,
    "z3": None,
}


def hellinger(p, q):
    p = np.asarray(p, float)
    q = np.asarray(q, float)
    return float(np.sqrt(max(0.0, 1.0 - np.sum(np.sqrt(p * q)))))


def tv(p, q):
    return 0.5 * float(np.sum(np.abs(np.asarray(p) - np.asarray(q))))


def run_positive_tests():
    r = {}
    rng = np.random.default_rng(2)
    p = rng.dirichlet(np.ones(5))
    q = rng.dirichlet(np.ones(5))
    s = rng.dirichlet(np.ones(5))

    r["identity_zero"] = bool(hellinger(p, p) < 1e-9)
    r["symmetry"] = bool(np.isclose(hellinger(p, q), hellinger(q, p)))
    r["in_unit_interval"] = bool(0.0 <= hellinger(p, q) <= 1.0 + 1e-9)

    # TV bounds: H^2 <= TV <= sqrt(2) H
    H = hellinger(p, q)
    T = tv(p, q)
    r["tv_bounds"] = bool(H ** 2 <= T + 1e-9 and T <= np.sqrt(2) * H + 1e-9)

    # Triangle inequality
    r["triangle_inequality"] = bool(
        hellinger(p, s) <= hellinger(p, q) + hellinger(q, s) + 1e-9
    )
    return r


def run_negative_tests():
    r = {}
    # Orthogonal supports -> H = 1
    p = np.array([1.0, 0.0, 0.0])
    q = np.array([0.0, 1.0, 0.0])
    r["orthogonal_maximal"] = bool(np.isclose(hellinger(p, q), 1.0))

    # Different distributions -> nonzero
    p2 = np.array([0.5, 0.3, 0.2])
    q2 = np.array([0.2, 0.3, 0.5])
    r["different_nonzero"] = bool(hellinger(p2, q2) > 0.0)
    return r


def run_boundary_tests():
    r = {}
    # Point masses same: 0
    p = np.array([0.0, 1.0, 0.0, 0.0])
    r["point_mass_self"] = bool(hellinger(p, p) < 1e-12)

    # Nearly identical: small H
    eps = 1e-4
    p = np.array([0.5, 0.5])
    q = np.array([0.5 + eps, 0.5 - eps])
    r["small_perturbation_small"] = bool(hellinger(p, q) < 1e-2)

    # Large alphabet numerical stability
    rng = np.random.default_rng(3)
    N = 1000
    p = rng.dirichlet(np.ones(N))
    q = rng.dirichlet(np.ones(N))
    H = hellinger(p, q)
    r["large_alphabet_finite"] = bool(np.isfinite(H) and 0.0 <= H <= 1.0 + 1e-9)
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "hellinger_categorical_classical_results.json")
    payload = {
        "name": "hellinger_categorical_classical",
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
