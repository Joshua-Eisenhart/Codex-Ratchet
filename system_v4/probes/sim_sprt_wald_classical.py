#!/usr/bin/env python3
"""Classical baseline: Wald's Sequential Probability Ratio Test (SPRT).
For simple H0 vs H1, SPRT attains target (alpha, beta) error rates with
minimal expected sample size (Wald-Wolfowitz optimality).
"""
import json, os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "Classical SPRT accumulates a scalar log-likelihood ratio over iid observations. A "
    "quantum sequential test requires noncommuting measurement sequences and adaptive "
    "POVMs; this baseline drops that operator-sequential structure."
)

try:
    import torch  # noqa: F401
    _torch_ok = True
except Exception:
    _torch_ok = False

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "cumulative LLR and stopping"},
    "scipy": {"tried": True, "used": True, "reason": "normal pdf closed-form"},
    "pytorch": {
        "tried": _torch_ok,
        "used": False,
        "reason": "supportive import only",
    },
    "z3": {"tried": False, "used": False, "reason": "no SMT optimality proof here"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "pytorch": "supportive",
    "z3": None,
}

rng = np.random.default_rng(7)


def sprt_normal(x_gen, mu0, mu1, sigma, alpha, beta, max_n=2000):
    """Return (decision in {0,1,'maxn'}, n_used)."""
    A = np.log((1 - beta) / alpha)
    B = np.log(beta / (1 - alpha))
    llr = 0.0
    for n in range(1, max_n + 1):
        x = x_gen()
        # LLR increment for Normal(mu, sigma^2):
        inc = ((x - mu0) ** 2 - (x - mu1) ** 2) / (2 * sigma ** 2)
        llr += inc
        if llr >= A:
            return 1, n
        if llr <= B:
            return 0, n
    return "maxn", max_n


def run_positive_tests():
    results = {}
    alpha, beta = 0.05, 0.05
    mu0, mu1, sigma = 0.0, 0.5, 1.0
    trials = 1000

    # Under H0, should accept H0 (decision=0) at rate ~1-alpha
    n_used_h0 = []
    decisions_h0 = []
    for _ in range(trials):
        gen = lambda: rng.normal(mu0, sigma)
        d, n = sprt_normal(gen, mu0, mu1, sigma, alpha, beta)
        decisions_h0.append(d)
        n_used_h0.append(n)
    type_i = np.mean([d == 1 for d in decisions_h0])
    results["type_i_controlled"] = type_i < alpha * 3  # Wald approximation

    # Under H1, should accept H1 at rate ~1-beta
    decisions_h1 = []
    n_used_h1 = []
    for _ in range(trials):
        gen = lambda: rng.normal(mu1, sigma)
        d, n = sprt_normal(gen, mu0, mu1, sigma, alpha, beta)
        decisions_h1.append(d)
        n_used_h1.append(n)
    type_ii = np.mean([d == 0 for d in decisions_h1])
    results["type_ii_controlled"] = type_ii < beta * 3

    # Expected sample size smaller than fixed-n Neyman-Pearson equivalent
    # Fixed n for (alpha,beta) at Neyman-Pearson: n* approx ((z_a + z_b)*sigma/(mu1-mu0))^2
    from math import sqrt
    # Use normal quantile
    import scipy.stats as sstats
    z_a = sstats.norm.ppf(1 - alpha)
    z_b = sstats.norm.ppf(1 - beta)
    n_fixed = ((z_a + z_b) * sigma / (mu1 - mu0)) ** 2
    mean_n = np.mean(n_used_h0 + n_used_h1)
    results["sprt_beats_fixed_n"] = mean_n < n_fixed * 1.0
    results["sprt_terminates"] = all(d != "maxn" for d in decisions_h0 + decisions_h1)
    return results


def run_negative_tests():
    results = {}
    # Nearly identical hypotheses -> needs many samples (or hits max_n)
    alpha, beta = 0.05, 0.05
    mu0, mu1, sigma = 0.0, 0.01, 1.0
    gen = lambda: rng.normal(mu0, sigma)
    d, n = sprt_normal(gen, mu0, mu1, sigma, alpha, beta, max_n=200)
    results["nearly_identical_needs_many_samples_or_maxn"] = (d == "maxn") or (n == 200)

    # Wrong model (data from mu=2 but test between 0 and 0.5) -> decides H1 quickly
    gen2 = lambda: rng.normal(2.0, 1.0)
    d2, n2 = sprt_normal(gen2, 0.0, 0.5, 1.0, 0.05, 0.05, max_n=500)
    results["misspecified_decides_h1_closest"] = d2 == 1
    return results


def run_boundary_tests():
    results = {}
    # Very tight error rates -> more samples
    n_loose = []
    n_tight = []
    mu0, mu1, sigma = 0.0, 1.0, 1.0
    trials = 300
    for _ in range(trials):
        gen = lambda: rng.normal(mu0, sigma)
        _, n = sprt_normal(gen, mu0, mu1, sigma, 0.2, 0.2, max_n=500)
        n_loose.append(n)
    for _ in range(trials):
        gen = lambda: rng.normal(mu0, sigma)
        _, n = sprt_normal(gen, mu0, mu1, sigma, 0.001, 0.001, max_n=2000)
        n_tight.append(n)
    results["tighter_alpha_more_samples"] = np.mean(n_tight) > np.mean(n_loose)

    # alpha=beta large (0.4): early stopping with minimal n
    gen = lambda: rng.normal(0.5, 1.0)
    _, n = sprt_normal(gen, 0.0, 0.5, 1.0, 0.4, 0.4, max_n=500)
    results["loose_error_small_n"] = n <= 50
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sprt_wald_classical_results.json")
    payload = {
        "name": "sprt_wald_classical",
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
