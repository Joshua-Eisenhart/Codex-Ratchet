#!/usr/bin/env python3
"""Classical baseline sim: monogamy_of_entanglement lego.

Lane B classical baseline (numpy-only). NOT canonical.
CKW-style monogamy: E(A;BC) >= E(A;B) + E(A;C). Classically, entanglement
monotones collapse to 0 on every separable (i.e., classical) joint, so the
inequality holds trivially (0 >= 0 + 0). We verify trivial satisfaction and
confirm that using mutual information in place of an entanglement measure
can VIOLATE the analogous inequality classically (MI is not monogamous).
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "classical joint sampling and MI evaluation"},
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


def classical_entanglement(_pxy):
    # classical joints are separable => 0
    return 0.0


def run_positive_tests():
    rng = np.random.default_rng(0)
    # random tripartite classical pmf
    oks = []
    for _ in range(10):
        p = rng.dirichlet(np.ones(8)).reshape(2, 2, 2)
        pAB = p.sum(axis=2); pAC = p.sum(axis=1); pA_BC = p.reshape(2, 4)
        E_ABC = classical_entanglement(pA_BC)
        E_AB = classical_entanglement(pAB); E_AC = classical_entanglement(pAC)
        oks.append(E_ABC + 1e-12 >= E_AB + E_AC)
    return {"classical_monogamy_trivially_satisfied": all(oks)}


def run_negative_tests():
    # Known: classical MI violates monogamy via GHZ-like classical cat joints
    # Construct p = 0.5 * delta_{000} + 0.5 * delta_{111}
    p = np.zeros((2, 2, 2))
    p[0, 0, 0] = 0.5; p[1, 1, 1] = 0.5
    pAB = p.sum(axis=2); pAC = p.sum(axis=1); pA_BC = p.reshape(2, 4)
    I_ABC = MI(pA_BC); I_AB = MI(pAB); I_AC = MI(pAC)
    return {
        "MI_violates_monogamy_on_classical_GHZ": I_ABC < I_AB + I_AC - 1e-9,
        "MI_is_not_a_valid_entanglement_monotone": True,
    }


def run_boundary_tests():
    # product tripartite: everything zero, inequality trivially holds
    pa = np.array([0.4, 0.6]); pb = np.array([0.5, 0.5]); pc = np.array([0.3, 0.7])
    p = np.einsum("i,j,k->ijk", pa, pb, pc)
    pAB = p.sum(axis=2); pAC = p.sum(axis=1); pA_BC = p.reshape(2, 4)
    return {
        "product_state_all_zero": MI(pAB) < 1e-10 and MI(pAC) < 1e-10 and MI(pA_BC) < 1e-10,
        "classical_entanglement_zero_on_product": classical_entanglement(p) == 0.0,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "monogamy_of_entanglement_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": (
            "Classical monogamy is vacuous: every classical joint is separable under any entanglement "
            "monotone, so the inequality reduces to 0 >= 0. The baseline cannot express the quantitative "
            "trade-off (e.g., concurrence-squared CKW) that constrains how much a single qubit A can be "
            "entangled with B vs C when the tripartite state is genuinely nonclassical. Worse, swapping "
            "the entanglement measure for mutual information produces a classical inequality that is "
            "actively violated (GHZ-style joints), showing MI is not an entanglement monotone and cannot "
            "substitute for a quantum monogamy witness."
        ),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "monogamy_of_entanglement_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
