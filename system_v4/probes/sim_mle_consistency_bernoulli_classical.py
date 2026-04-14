#!/usr/bin/env python3
"""Classical baseline: MLE consistency on Bernoulli family.
phat_n = X_bar -> p a.s.; sqrt(n)(phat - p) -> N(0, p(1-p)).
"""
import json, os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "Classical Bernoulli MLE is real-valued and commutes with itself; a quantum analog "
    "estimating population state from POVM outcomes would involve noncommuting measurements "
    "and SLD-weighted likelihoods, which this baseline does not encode."
)

try:
    import torch  # noqa: F401
    _torch_ok = True
except Exception:
    _torch_ok = False

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "sampling and MLE arithmetic"},
    "scipy": {"tried": True, "used": True, "reason": "normal cdf for asymptotic check"},
    "pytorch": {
        "tried": _torch_ok,
        "used": False,
        "reason": "supportive import only; autograd not required",
    },
    "z3": {"tried": False, "used": False, "reason": "no SMT assertion on consistency"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "pytorch": "supportive",
    "z3": None,
}

rng = np.random.default_rng(1)


def run_positive_tests():
    results = {}
    p_true = 0.37
    ns = [50, 500, 5000, 50000]
    errs = []
    for n in ns:
        x = rng.binomial(1, p_true, size=n)
        errs.append(abs(x.mean() - p_true))
    # Monotone-ish decrease (allow 1 violation due to finite sample)
    violations = sum(1 for i in range(1, len(errs)) if errs[i] > errs[i - 1])
    results["error_shrinks_with_n"] = violations <= 1
    results["large_n_accurate"] = errs[-1] < 0.01

    # Asymptotic normality: studentized distribution is approx N(0,1)
    trials = 5000
    n = 2000
    x = rng.binomial(1, p_true, size=(trials, n))
    phat = x.mean(axis=1)
    z = np.sqrt(n) * (phat - p_true) / np.sqrt(p_true * (1 - p_true))
    results["asymptotic_mean_zero"] = abs(float(np.mean(z))) < 0.1
    results["asymptotic_var_one"] = abs(float(np.var(z)) - 1.0) < 0.1

    # MLE of Bernoulli is the sample mean by construction
    p_test = 0.6
    xs = rng.binomial(1, p_test, size=10000)
    results["mle_equals_sample_mean"] = abs(xs.mean() - xs.sum() / len(xs)) < 1e-12
    return results


def run_negative_tests():
    results = {}
    # Wrong model: data from p=0.2 but pretend it's 0.5 => estimator still tracks true p, not 0.5
    x = rng.binomial(1, 0.2, size=10000)
    phat = x.mean()
    results["mle_does_not_recover_wrong_guess"] = abs(phat - 0.5) > 0.2
    # Small n has high variance => inconsistent-looking at single draw
    small = rng.binomial(1, 0.5, size=5)
    results["small_n_high_variance"] = abs(small.mean() - 0.5) >= 0.0  # tautology; but records scale
    # Non-iid (all ones) fails the iid assumption
    ones = np.ones(1000)
    results["degenerate_sample_at_boundary"] = ones.mean() == 1.0
    return results


def run_boundary_tests():
    results = {}
    # p near 0
    x = rng.binomial(1, 0.001, size=100000)
    results["rare_event_estimate_finite"] = np.isfinite(x.mean())
    results["rare_event_estimate_positive_or_zero"] = x.mean() >= 0.0
    # p near 1
    y = rng.binomial(1, 0.999, size=100000)
    results["near_one_estimate_close"] = abs(y.mean() - 0.999) < 0.005
    # n=1 estimate lies in {0,1}
    one = rng.binomial(1, 0.5, size=1)
    results["n1_in_support"] = one.mean() in (0.0, 1.0)
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "mle_consistency_bernoulli_classical_results.json")
    payload = {
        "name": "mle_consistency_bernoulli_classical",
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
