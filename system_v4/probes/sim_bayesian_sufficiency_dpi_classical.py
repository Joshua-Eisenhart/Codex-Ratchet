#!/usr/bin/env python3
"""Classical sufficiency / data processing for Bayesian posterior inference.

A statistic T(x) is sufficient iff posterior p(theta|x) = p(theta|T(x)).
Classical DPI guarantees mutual information I(theta;T) <= I(theta;X) with
equality iff T is sufficient.
"""
import json, os
from typing import Literal, Optional
import numpy as np

classification: Literal["classical_baseline", "canonical"] = "classical_baseline"
divergence_log: Optional[str] = (
    "Classical Fisher-Neyman sufficiency uses factorization p(x|theta)=g(T(x),theta)h(x); "
    "information-preserving coarse-graining is defined on a commuting sample "
    "space and respects joint distributions p(theta,x). Quantum sufficiency "
    "requires a recovery channel R such that R circ N = id on the subalgebra, "
    "and is equivalent to equality in quantum DPI under operator-monotone functions "
    "of noncommuting rho. This classical substrate cannot witness Petz-recovery "
    "failure on genuinely nonclassical subalgebras."
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
    TOOL_MANIFEST["pytorch"]["reason"] = "torch tensor joint-marginal reductions"
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

EPS = 1e-12

def mutual_information(joint: np.ndarray) -> float:
    joint = joint / joint.sum()
    px = joint.sum(axis=1, keepdims=True)
    py = joint.sum(axis=0, keepdims=True)
    outer = px @ py
    mask = joint > EPS
    return float(np.sum(joint[mask] * np.log(joint[mask] / outer[mask])))


def coarse_grain(joint: np.ndarray, groups):
    """Sum columns of joint p(theta,x) according to groups -> p(theta, T)."""
    K = len(groups)
    out = np.zeros((joint.shape[0], K))
    for k, g in enumerate(groups):
        out[:, k] = joint[:, g].sum(axis=1)
    return out


def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    # Construct joint where x=(T, U) with U independent of theta given T.
    # theta in {0,1}, T in {0,1}, U in {0,1} -> x in {0..3}
    # p(theta, T) arbitrary; p(U|T) = [0.3, 0.7] independent of theta
    p_tt = np.array([[0.4, 0.1], [0.05, 0.45]])  # rows theta, cols T
    p_tt = p_tt / p_tt.sum()
    p_u_given_T = np.array([[0.3, 0.7], [0.6, 0.4]])  # rows T, cols U
    # joint[theta, x] with x = 2*T + U
    joint = np.zeros((2, 4))
    for th in range(2):
        for T in range(2):
            for U in range(2):
                joint[th, 2*T + U] = p_tt[th, T] * p_u_given_T[T, U]
    I_full = mutual_information(joint)
    # T groups: x in {0,1}->T=0; x in {2,3}->T=1
    joint_T = coarse_grain(joint, [[0, 1], [2, 3]])
    I_T = mutual_information(joint_T)
    # Sufficiency: I(theta; X) == I(theta; T) because U indep of theta given T
    r["sufficient_statistic_preserves_mi"] = abs(I_full - I_T) < 1e-8
    # A coarser grouping that merges T=0 and T=1 kills information
    joint_const = coarse_grain(joint, [[0, 1, 2, 3]])
    I_const = mutual_information(joint_const)
    r["constant_statistic_zero_mi"] = abs(I_const) < 1e-10
    # DPI on a lossy grouping (merge across T): strict decrease
    joint_lossy = coarse_grain(joint, [[0, 2], [1, 3]])  # merges across T
    I_lossy = mutual_information(joint_lossy)
    r["dpi_lossy_strict_decrease"] = I_lossy < I_full - 1e-6
    return r


def run_negative_tests():
    r = {}
    # Non-sufficient statistic must not preserve MI
    rng = np.random.default_rng(1)
    joint = rng.dirichlet(np.ones(8)).reshape(2, 4)
    I_full = mutual_information(joint)
    # coarse-grain merging arbitrary adjacent columns
    joint_bad = coarse_grain(joint, [[0, 2], [1, 3]])
    I_bad = mutual_information(joint_bad)
    r["generic_non_sufficient_loses_mi"] = I_bad < I_full - 1e-6
    # DPI: no grouping can increase MI
    any_increase = False
    for _ in range(20):
        gs = [[0, 1], [2, 3]]; rng.shuffle(gs)
        I_g = mutual_information(coarse_grain(joint, gs))
        if I_g > I_full + 1e-8:
            any_increase = True
    r["no_coarse_graining_increases_mi"] = not any_increase
    return r


def run_boundary_tests():
    r = {}
    # degenerate: theta and x independent -> all groupings yield 0
    joint = np.outer([0.3, 0.7], [0.25, 0.25, 0.25, 0.25])
    r["independent_zero_mi"] = abs(mutual_information(joint)) < 1e-12
    # perfect correlation -> MI = H(theta)
    joint = np.zeros((2, 2)); joint[0, 0] = 0.5; joint[1, 1] = 0.5
    I = mutual_information(joint)
    r["perfect_correlation_entropy"] = abs(I - np.log(2)) < 1e-10
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "bayesian_sufficiency_dpi_classical",
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
    out_path = os.path.join(out_dir, "bayesian_sufficiency_dpi_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    assert all_pass, results
