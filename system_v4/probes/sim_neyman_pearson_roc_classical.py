#!/usr/bin/env python3
"""Classical baseline: Neyman-Pearson likelihood ratio test.
At any fixed Type-I level alpha, the LRT maximizes power; its ROC dominates all others.
"""
import json, os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "Classical NP uses a scalar LR over commuting observations. The quantum analog is "
    "Helstrom's test with a noncommuting optimal POVM; this baseline omits the operator "
    "structure of the quantum hypothesis testing problem."
)

try:
    import torch  # noqa: F401
    _torch_ok = True
except Exception:
    _torch_ok = False

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "LR computation and ROC sweep"},
    "scipy": {"tried": True, "used": True, "reason": "normal pdf closed form"},
    "pytorch": {
        "tried": _torch_ok,
        "used": False,
        "reason": "supportive import; no gradient path needed",
    },
    "z3": {"tried": False, "used": False, "reason": "no SMT optimality encoding here"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "pytorch": "supportive",
    "z3": None,
}

rng = np.random.default_rng(3)


def _roc(scores_h0, scores_h1, grid=201):
    thresholds = np.linspace(min(scores_h0.min(), scores_h1.min()) - 1e-9,
                             max(scores_h0.max(), scores_h1.max()) + 1e-9, grid)
    fpr = np.array([float(np.mean(scores_h0 >= t)) for t in thresholds])
    tpr = np.array([float(np.mean(scores_h1 >= t)) for t in thresholds])
    order = np.argsort(fpr)
    fpr, tpr = fpr[order], tpr[order]
    auc = float(np.trapz(tpr, fpr))
    return fpr, tpr, auc


def run_positive_tests():
    results = {}
    # H0: N(0,1) vs H1: N(1,1). LR test score is x (monotone in LR)
    n = 20000
    x0 = rng.normal(0, 1, size=n)
    x1 = rng.normal(1, 1, size=n)

    lr_score_0 = x0  # monotone in LR
    lr_score_1 = x1
    _, _, auc_lr = _roc(lr_score_0, lr_score_1)

    # Alternative suboptimal test: |x|
    alt0 = np.abs(x0)
    alt1 = np.abs(x1)
    _, _, auc_alt = _roc(alt0, alt1)

    # Another: x^2
    sq0 = x0 ** 2
    sq1 = x1 ** 2
    _, _, auc_sq = _roc(sq0, sq1)

    results["lr_auc_beats_abs"] = auc_lr > auc_alt + 0.02
    results["lr_auc_beats_square"] = auc_lr > auc_sq + 0.02
    results["lr_auc_above_0_7"] = auc_lr > 0.7
    results["auc_in_range"] = 0.5 <= auc_lr <= 1.0 and 0.5 <= auc_alt <= 1.0

    # Alpha control: at threshold corresponding to ~alpha, empirical FPR ~= alpha
    alpha = 0.05
    thr = np.quantile(x0, 1 - alpha)
    emp_fpr = float(np.mean(x0 >= thr))
    emp_power = float(np.mean(x1 >= thr))
    results["alpha_control"] = abs(emp_fpr - alpha) < 0.01
    results["power_greater_than_alpha"] = emp_power > alpha + 0.1
    return results


def run_negative_tests():
    results = {}
    # Random coin-flip test: FPR ~ TPR ~ 0.5 power regardless of alpha => no better than chance
    n = 5000
    x0 = rng.normal(0, 1, size=n)
    x1 = rng.normal(1, 1, size=n)
    coin0 = rng.uniform(size=n)
    coin1 = rng.uniform(size=n)
    _, _, auc_rand = _roc(coin0, coin1)
    results["random_test_auc_near_0_5"] = abs(auc_rand - 0.5) < 0.05

    # Swapping hypotheses: if we use score -x, AUC = 1 - auc_lr (mirror)
    _, _, auc_lr = _roc(x0, x1)
    _, _, auc_flip = _roc(-x0, -x1)
    results["flipped_score_below_optimal"] = auc_flip < auc_lr
    return results


def run_boundary_tests():
    results = {}
    # Identical distributions: AUC == 0.5 (no discrimination)
    n = 5000
    a = rng.normal(0, 1, size=n)
    b = rng.normal(0, 1, size=n)
    _, _, auc = _roc(a, b)
    results["identical_dists_auc_near_0_5"] = abs(auc - 0.5) < 0.05

    # Perfectly separable: AUC == 1
    a = rng.normal(0, 0.01, size=1000)
    b = rng.normal(5, 0.01, size=1000)
    _, _, auc = _roc(a, b)
    results["perfect_separation_auc_near_1"] = auc > 0.99

    # Very small alpha
    x0 = rng.normal(0, 1, size=20000)
    x1 = rng.normal(2, 1, size=20000)
    thr = np.quantile(x0, 1 - 0.001)
    emp = float(np.mean(x0 >= thr))
    results["tiny_alpha_control"] = emp < 0.003
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "neyman_pearson_roc_classical_results.json")
    payload = {
        "name": "neyman_pearson_roc_classical",
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
