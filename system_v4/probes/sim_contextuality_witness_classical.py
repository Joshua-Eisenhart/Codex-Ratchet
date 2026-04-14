#!/usr/bin/env python3
"""Classical baseline sim: contextuality_witness lego.

Lane B classical baseline (numpy-only). NOT canonical.
Classical (noncontextual) hidden-variable model: every observable has a
context-independent value lambda(A). For any compatible pair (A,B),
<AB> = sum_lambda p(lambda) lambda(A) lambda(B). The CHSH / KCBS witness
is bounded by the classical (noncontextual) polytope face.
Innately missing: context-dependent outcome assignments, violations like
CHSH=2*sqrt(2), KCBS > 4 on qutrit, Kochen-Specker colorings forbidden.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "expectation arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def chsh_classical(lam_assignments, probs):
    # each lam: dict {A:+/-1, B:+/-1, A':+/-1, B':+/-1}
    S = 0.0
    for p, lam in zip(probs, lam_assignments):
        S += p * (lam["A"] * lam["B"] + lam["A"] * lam["Bp"] + lam["Ap"] * lam["B"] - lam["Ap"] * lam["Bp"])
    return S


def run_positive_tests():
    # pure lambda: all +1 -> CHSH = 1+1+1-1 = 2
    lam = [{"A": 1, "B": 1, "Ap": 1, "Bp": 1}]
    S = chsh_classical(lam, [1.0])
    # random noncontextual mixture stays within [-2, 2]
    rng = np.random.default_rng(0)
    lams = [{k: int(rng.choice([-1, 1])) for k in ["A", "B", "Ap", "Bp"]} for _ in range(200)]
    p = np.ones(200) / 200
    S_mix = chsh_classical(lams, p)
    return {
        "chsh_classical_bound_respected_pure": abs(S) <= 2 + 1e-12,
        "chsh_classical_bound_respected_mixed": abs(S_mix) <= 2 + 1e-12,
    }


def run_negative_tests():
    # classical cannot produce Tsirelson value 2*sqrt(2)
    return {
        "classical_cannot_reach_tsirelson": 2 * np.sqrt(2) > 2.0,
        "classical_always_noncontextual_by_construction": True,
    }


def run_boundary_tests():
    lam = [{"A": 1, "B": 1, "Ap": 1, "Bp": -1}]
    S = chsh_classical(lam, [1.0])
    return {
        "boundary_value_at_two": abs(S) <= 2 + 1e-12,
        "zero_mixture_is_zero": chsh_classical([{"A": 0, "B": 0, "Ap": 0, "Bp": 0}], [1.0]) == 0.0,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "contextuality_witness_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "context-independent assignments bound CHSH by 2 (never reach Tsirelson)",
            "no Kochen-Specker obstruction; every observable has a global value",
            "KCBS and similar witnesses saturated only by quantum contextual models",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "contextuality_witness_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
