#!/usr/bin/env python3
"""classical baseline fep gaussian vfe

classical_baseline, numpy-only. Non-canon. Lane_B-eligible.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "numpy":    {"tried": True,  "used": True,  "reason": "load-bearing linear algebra / rng for classical baseline"},
    "pytorch":  {"tried": False, "used": False, "reason": "classical_baseline sim; torch not required"},
    "pyg":      {"tried": False, "used": False, "reason": "no graph-NN step in this baseline"},
    "z3":       {"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"},
    "cvc5":     {"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"},
    "sympy":    {"tried": False, "used": False, "reason": "numerical identity sufficient; symbolic not needed here"},
    "clifford": {"tried": False, "used": False, "reason": "matrix rep baseline; Cl(n) algebra deferred to canonical lane"},
    "geomstats":{"tried": False, "used": False, "reason": "flat/discrete baseline; manifold tooling out of scope"},
    "e3nn":     {"tried": False, "used": False, "reason": "no equivariant NN in baseline"},
    "rustworkx":{"tried": False, "used": False, "reason": "small adjacency handled by numpy"},
    "xgi":      {"tried": False, "used": False, "reason": "no hypergraph structure in this sim"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex in this sim"},
    "gudhi":    {"tried": False, "used": False, "reason": "no persistent homology in this sim"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None, "rustworkx": None,
    "xgi": None, "toponetx": None, "gudhi": None,
}

NAME = "classical_baseline_fep_gaussian_vfe"

def vfe(mu, sigma2, obs, prior_mu=0.0, prior_sigma2=1.0):
    # Variational free energy (Gaussian q, Gaussian prior, Gaussian likelihood obs ~ N(mu,1))
    # Surprise + KL
    like = 0.5*((obs - mu)**2 + sigma2) + 0.5*np.log(2*np.pi)
    kl = 0.5*(sigma2/prior_sigma2 + (mu-prior_mu)**2/prior_sigma2 - 1 + np.log(prior_sigma2/sigma2))
    return like + kl

def run_positive_tests():
    out = {}
    obs = 1.5
    # analytic posterior mean for prior N(0,1), lik N(mu,1): (obs)/(1+1) = obs/2
    mu_star = obs/2.0
    sig2_star = 0.5
    F_star = vfe(mu_star, sig2_star, obs)
    # perturbing mu increases F
    F_off = vfe(mu_star+0.3, sig2_star, obs)
    out["mu_optimum"] = {"pass": bool(F_off > F_star - 1e-12)}
    # perturbing sigma increases F
    F_off2 = vfe(mu_star, sig2_star*1.5, obs)
    out["sigma_optimum"] = {"pass": bool(F_off2 > F_star - 1e-12)}
    return out

def run_negative_tests():
    obs = 1.5
    F0 = vfe(0.0, 1.0, obs)
    F_opt = vfe(obs/2.0, 0.5, obs)
    return {"prior_not_optimal": {"pass": bool(F0 > F_opt)}}

def run_boundary_tests():
    # Extreme: very concentrated q with wrong mean blows up F
    obs = 1.5
    F = vfe(5.0, 1e-3, obs)
    return {"wrong_concentrated_high_F": {"pass": bool(F > 1.0)}}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        all(v.get("pass") for v in pos.values()) and
        all(v.get("pass") for v in neg.values()) and
        all(v.get("pass") for v in bnd.values())
    )
    results = {
        "name": NAME,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, NAME + "_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{NAME}: all_pass={all_pass} -> {out_path}")
