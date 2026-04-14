#!/usr/bin/env python3
"""Classical baseline sim: conditional_mutual_information (CMI) lego.

Lane B classical baseline (numpy-only). NOT canonical.
I(X;Y|Z) = H(X|Z) + H(Y|Z) - H(X,Y|Z) >= 0. Classically always nonnegative.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "joint-pmf marginalization and entropy computation"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def H(p):
    p = np.asarray(p, float).ravel()
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def CMI(pxyz):
    # I(X;Y|Z) = H(X,Z) + H(Y,Z) - H(X,Y,Z) - H(Z)
    pxz = pxyz.sum(axis=1); pyz = pxyz.sum(axis=0); pz = pxyz.sum(axis=(0, 1))
    return H(pxz) + H(pyz) - H(pxyz) - H(pz)


def run_positive_tests():
    rng = np.random.default_rng(7)
    oks = []
    for _ in range(50):
        p = rng.dirichlet(np.ones(27)).reshape(3, 3, 3)
        oks.append(CMI(p) >= -1e-10)
    # constructed markov chain saturates CMI=0
    pxz = rng.dirichlet(np.ones(9)).reshape(3, 3)
    Tzy = rng.dirichlet(np.ones(3), size=3)
    p = np.zeros((3, 3, 3))
    for z in range(3):
        p[:, :, z] = pxz[:, z:z+1] * Tzy[z:z+1, :]  # X-Z-Y markov => CMI(X;Y|Z)=0
    return {
        "CMI_nonneg_on_random": all(oks),
        "markov_chain_zero_CMI": abs(CMI(p)) < 1e-10,
    }


def run_negative_tests():
    # "common cause" Z => X,Y correlated only through Z: CMI=0
    # But if X,Y share info beyond Z, CMI > 0.
    # Construct joint where X,Y are directly correlated (not via Z):
    p = np.zeros((2, 2, 2))
    p[0, 0, 0] = 0.25; p[1, 1, 0] = 0.25; p[0, 0, 1] = 0.25; p[1, 1, 1] = 0.25
    return {
        "direct_correlation_has_positive_CMI": CMI(p) > 1e-6,
        "classical_CMI_cannot_be_negative": CMI(p) >= 0,
    }


def run_boundary_tests():
    # X independent of Y given Z regardless of absolute correlations
    px = np.array([0.3, 0.7])
    py = np.array([0.4, 0.6])
    pz = np.array([0.5, 0.5])
    # X-Z-Y: first draw Z uniform, then X and Y independent given Z (still product here)
    p = np.einsum("i,j,k->ikj", px, py, pz)  # X,Z,Y ordering
    # Actually set CMI for true product state:
    p2 = np.einsum("i,j,k->ijk", px, py, pz)
    return {
        "product_zero_CMI": abs(CMI(p2)) < 1e-10,
        "uniform_joint_zero_CMI": abs(CMI(np.ones((2, 2, 2)) / 8)) < 1e-10,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "conditional_mutual_information_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": (
            "Classical CMI is always nonneg by Gibbs' inequality applied pointwise in Z. The baseline "
            "cannot encode the fact that quantum CMI, while also nonneg (by SSA), fails to characterize "
            "approximate Markov chains via Bayes conditioning — the correct recovery is the Petz map, "
            "and small CMI does not force small distance from a Markov state in the classical-Bayes "
            "sense. Therefore any sim that uses classical CMI as a stand-in for quantum conditional "
            "independence will miss noncommuting side-information leakage."
        ),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "conditional_mutual_information_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
