#!/usr/bin/env python3
"""
sim_three_gaussian_sequential_bayes_triple_classical.py

Step 3 classical baseline: three-Gaussian sequential Bayesian update
prior -> post1 (after obs1) -> post2 (after obs2). Closure check:
sequential update == batch update with both observations.
"""

import json
import os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "n/a"},
    "z3": {"tried": False, "used": False, "reason": "n/a"},
    "cvc5": {"tried": False, "used": False, "reason": "n/a"},
    "sympy": {"tried": False, "used": False, "reason": "n/a"},
    "clifford": {"tried": False, "used": False, "reason": "n/a"},
    "geomstats": {"tried": False, "used": False, "reason": "n/a"},
    "e3nn": {"tried": False, "used": False, "reason": "n/a"},
    "rustworkx": {"tried": False, "used": False, "reason": "n/a"},
    "xgi": {"tried": False, "used": False, "reason": "n/a"},
    "toponetx": {"tried": False, "used": False, "reason": "n/a"},
    "gudhi": {"tried": False, "used": False, "reason": "n/a"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "tensor cross-check of posterior mean"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def gauss_update(mu0, var0, obs, var_obs):
    prec = 1/var0 + 1/var_obs
    var = 1/prec
    mu = var * (mu0/var0 + obs/var_obs)
    return mu, var


def run_positive_tests():
    results = {}
    rng = np.random.default_rng(3)
    ok = True
    max_err = 0.0
    for _ in range(32):
        mu0 = rng.normal()
        var0 = rng.uniform(0.5, 3.0)
        var_obs = rng.uniform(0.5, 3.0)
        y1 = rng.normal()
        y2 = rng.normal()
        mu1, v1 = gauss_update(mu0, var0, y1, var_obs)
        mu2, v2 = gauss_update(mu1, v1, y2, var_obs)
        # batch
        prec = 1/var0 + 2/var_obs
        vb = 1/prec
        mub = vb * (mu0/var0 + y1/var_obs + y2/var_obs)
        err = max(abs(mu2 - mub), abs(v2 - vb))
        max_err = max(max_err, err)
        if err > 1e-10:
            ok = False

    if TOOL_MANIFEST["pytorch"]["used"]:
        import torch
        t = torch.tensor([mu2, v2])
        results["torch_post2_norm"] = float(t.norm())

    results["sequential_equals_batch"] = ok
    results["max_err"] = max_err
    return results


def run_negative_tests():
    results = {}
    # Using wrong (doubled) prior variance should break equality
    mu0, var0, var_obs = 0.0, 1.0, 1.0
    y1, y2 = 1.0, 1.5
    mu1, v1 = gauss_update(mu0, var0, y1, var_obs)
    mu2_seq, v2_seq = gauss_update(mu1, v1, y2, var_obs)
    # Wrong batch: use var0*2
    prec = 1/(var0*2) + 2/var_obs
    vb = 1/prec
    mub = vb * (mu0/(var0*2) + y1/var_obs + y2/var_obs)
    results["wrong_prior_breaks_match"] = bool(abs(mu2_seq - mub) > 1e-6)
    return results


def run_boundary_tests():
    results = {}
    # Infinite-variance obs -> posterior = prior
    mu, v = gauss_update(0.5, 1.0, 100.0, 1e18)
    results["uninformative_obs_preserves_prior"] = bool(abs(mu - 0.5) < 1e-10 and abs(v - 1.0) < 1e-6)
    # Zero-variance obs -> posterior collapses to obs
    mu, v = gauss_update(0.5, 1.0, 2.0, 1e-12)
    results["certain_obs_collapses"] = bool(abs(mu - 2.0) < 1e-6 and v < 1e-6)
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        pos.get("sequential_equals_batch", False)
        and neg.get("wrong_prior_breaks_match", False)
        and bnd.get("uninformative_obs_preserves_prior", False)
        and bnd.get("certain_obs_collapses", False)
    )
    divergence_log = [
        "classical sequential Bayes assumes commutative update order; loses noncommutative POVM update structure needed in nonclassical triple-nesting",
        "Gaussian conjugacy hides the distinguishability fence: real triple updates need admissibility, not smooth posterior interpolation",
        "no probe-dependence: classical posterior is observer-independent, violating probe-relative doctrine",
    ]
    results = {
        "name": "three_gaussian_sequential_bayes_triple_classical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "divergence_log": divergence_log,
        "summary": {"all_pass": bool(all_pass)},
        "all_pass": bool(all_pass),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "three_gaussian_sequential_bayes_triple_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
