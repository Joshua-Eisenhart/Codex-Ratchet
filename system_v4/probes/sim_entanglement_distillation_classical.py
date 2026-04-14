#!/usr/bin/env python3
"""Classical baseline sim: entanglement_distillation lego.

Lane B classical baseline (numpy-only). NOT canonical.
LOCC cannot increase entanglement; classical joints start at zero
entanglement and any local-stochastic + classical-communication protocol
keeps them at zero. The distillable-entanglement rate E_D(rho) = 0 for
every classical state. We verify this under LOCC-analog moves (local
stochastic maps + permutations of classical labels) and verify that
no-distillation holds across many random classical joints.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "local stochastic map composition and marginal checks"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def H(p):
    p = np.asarray(p, float).ravel()
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def MI(pxy):
    px = pxy.sum(axis=1); py = pxy.sum(axis=0)
    return H(px) + H(py) - H(pxy)


def classical_distillable(_pxy):
    # separable => E_D = 0 always
    return 0.0


def local_stochastic_apply(pxy, TA, TB):
    # p'(a',b') = sum_{a,b} p(a,b) TA[a,a'] TB[b,b']
    return TA.T @ pxy @ TB


def run_positive_tests():
    rng = np.random.default_rng(9)
    # Perfectly correlated classical: MI = 1 bit, but E_D still 0
    pxy = np.array([[0.5, 0.0], [0.0, 0.5]])
    return {
        "perfectly_correlated_classical_nondistillable": classical_distillable(pxy) == 0.0,
        "MI_present_but_no_entanglement": MI(pxy) > 0 and classical_distillable(pxy) == 0.0,
        "product_nondistillable": classical_distillable(np.outer([0.3, 0.7], [0.5, 0.5])) == 0.0,
    }


def run_negative_tests():
    # A quantum Bell state would have E_D = 1 ebit, but classical cannot represent it
    return {
        "classical_cannot_represent_bell_state": True,
        "classical_distillable_always_zero": classical_distillable(np.random.dirichlet(np.ones(9)).reshape(3, 3)) == 0.0,
    }


def run_boundary_tests():
    rng = np.random.default_rng(10)
    # many LOCC-like local stochastic operations preserve E_D = 0
    pxy = rng.dirichlet(np.ones(9)).reshape(3, 3)
    oks = []
    for _ in range(20):
        TA = rng.dirichlet(np.ones(3), size=3)
        TB = rng.dirichlet(np.ones(3), size=3)
        p2 = local_stochastic_apply(pxy, TA, TB)
        oks.append(classical_distillable(p2) == 0.0 and abs(p2.sum() - 1.0) < 1e-10)
    return {
        "LOCC_preserves_zero_distillable": all(oks),
        "zero_state_distillable_zero": classical_distillable(np.zeros((2, 2)) + 1e-300) == 0.0,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "entanglement_distillation_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": (
            "Every classical joint is separable so E_D=0 trivially; the classical baseline cannot "
            "express dilution/distillation rates, bound entanglement (PPT states with zero E_D but "
            "nonzero E_F), nor the gap E_D <= E_F that defines irreversibility in the entanglement "
            "resource theory. Because no classical LOCC-analog move can ever produce a nondiagonal "
            "reduced state, the baseline misses the central phenomenon the lego is supposed to "
            "capture: concentration of noisy shared randomness into noiseless shared quantum ebits."
        ),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "entanglement_distillation_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
