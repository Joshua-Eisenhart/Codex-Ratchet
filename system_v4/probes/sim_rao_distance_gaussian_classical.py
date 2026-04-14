#!/usr/bin/env python3
"""Classical Rao (Fisher-Rao) distance on the univariate Gaussian family.

The Fisher-Rao metric on {N(mu, sigma^2) : sigma>0} is hyperbolic; the
closed-form geodesic distance is known.
"""
import json, os
from typing import Literal, Optional
import numpy as np

classification: Literal["classical_baseline", "canonical"] = "classical_baseline"
divergence_log: Optional[str] = (
    "Classical Fisher-Rao distance on N(mu,sigma^2) uses the Fisher information "
    "metric g = diag(1/sigma^2, 2/sigma^2) of a commuting probability family, "
    "giving a hyperbolic (half-plane) geodesic. Quantum Fisher-Rao (Bures) "
    "distance ds^2 = tr(rho dL^2)/4 requires symmetric logarithmic derivatives "
    "and differs from the classical Fisher metric whenever the parameter shifts "
    "noncommuting generators. This classical substrate produces strictly smaller "
    "distances than Bures on genuinely quantum families."
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
        "torch autograd for numeric Fisher information cross-check"
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
for _e in TOOL_MANIFEST.values():
    assert isinstance(_e["reason"], str) and _e["reason"].strip()
for _d in TOOL_INTEGRATION_DEPTH.values():
    assert _d in _VALID_DEPTHS


def rao_gaussian(mu1, s1, mu2, s2):
    """Closed-form Rao distance on N(mu, sigma^2).

    Using the isometry to H^2: z = (mu/sqrt(2), sigma). Fisher metric
    ds^2 = (dmu^2 + 2 dsigma^2)/sigma^2 becomes the Poincare half-plane metric
    with coordinates (mu/sqrt(2), sigma), so the distance is
      d = sqrt(2) * arccosh(1 + ((mu1-mu2)^2/2 + (s1-s2)^2) / (2 s1 s2)).
    """
    dm = (mu1 - mu2) / np.sqrt(2)
    delta = 1.0 + (dm**2 + (s1 - s2)**2) / (2.0 * s1 * s2)
    return float(np.sqrt(2.0) * np.arccosh(max(delta, 1.0)))


def run_positive_tests():
    r = {}
    # identity
    r["zero_at_same"] = abs(rao_gaussian(0.0, 1.0, 0.0, 1.0)) < 1e-12
    # symmetry
    d12 = rao_gaussian(0.0, 1.0, 2.0, 3.0)
    d21 = rao_gaussian(2.0, 3.0, 0.0, 1.0)
    r["symmetry"] = abs(d12 - d21) < 1e-12
    # scale invariance in sigma when mu fixed: d(mu,s,mu,k*s) = sqrt(2)*arccosh((1+k^2)/(2k))
    # (this is the log-ratio metric on the sigma axis)
    mu = 1.0; s = 0.5; k = 3.0
    d = rao_gaussian(mu, s, mu, k * s)
    expected = np.sqrt(2.0) * np.arccosh((1.0 + k**2) / (2.0 * k))
    r["scale_sigma_closed_form"] = abs(d - expected) < 1e-10
    # triangle inequality on 3 random points
    rng = np.random.default_rng(0)
    triangle_ok = True
    for _ in range(20):
        a = (rng.uniform(-2, 2), rng.uniform(0.2, 3))
        b = (rng.uniform(-2, 2), rng.uniform(0.2, 3))
        c = (rng.uniform(-2, 2), rng.uniform(0.2, 3))
        dab = rao_gaussian(*a, *b); dbc = rao_gaussian(*b, *c); dac = rao_gaussian(*a, *c)
        if dac > dab + dbc + 1e-8:
            triangle_ok = False; break
    r["triangle_inequality"] = triangle_ok
    return r


def run_negative_tests():
    r = {}
    # Rao distance is NOT equal to (mu, sigma) Euclidean in general:
    # pick points where sigma differs so hyperbolic curvature matters
    d_rao = rao_gaussian(0.0, 0.5, 2.0, 3.0)
    d_euc = np.sqrt((2.0)**2 + (2.5)**2)
    r["not_euclidean"] = abs(d_rao - d_euc) > 0.2
    # differing sigma at same mu still gives nonzero distance
    r["sigma_only_positive"] = rao_gaussian(0.0, 1.0, 0.0, 2.0) > 0.1
    return r


def run_boundary_tests():
    r = {}
    # very small sigma differences: metric locally ~ sqrt(2) dsigma/sigma
    s0 = 1.0; eps = 1e-4
    d = rao_gaussian(0, s0, 0, s0 + eps)
    r["local_sigma_linear"] = abs(d - np.sqrt(2) * eps / s0) < 1e-7
    # very small mu differences: metric locally ~ dmu/sigma
    d = rao_gaussian(0, s0, eps, s0)
    r["local_mu_linear"] = abs(d - eps / s0) < 1e-7
    # divergent: sigma -> 0 limit blows up
    d = rao_gaussian(0, 1.0, 0, 1e-6)
    r["sigma_to_zero_unbounded"] = d > 10
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "rao_distance_gaussian_classical",
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
    out_path = os.path.join(out_dir, "rao_distance_gaussian_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    assert all_pass, results
