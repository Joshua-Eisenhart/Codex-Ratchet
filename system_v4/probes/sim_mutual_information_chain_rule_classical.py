#!/usr/bin/env python3
"""Classical baseline sim: mutual_information_chain_rule lego.

Lane B classical baseline (numpy-only). NOT canonical.
Chain rule: I(X;Y,Z) = I(X;Y) + I(X;Z|Y). Holds for any classical joint pmf.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "pmf arithmetic and Shannon entropy evaluation"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def H(p):
    p = np.asarray(p, float).ravel()
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def I(pxy):
    px = pxy.sum(axis=1); py = pxy.sum(axis=0)
    return H(px) + H(py) - H(pxy)


def I_cond(pxyz):  # I(X;Y|Z)
    # pxyz indexed [x,y,z]
    pz = pxyz.sum(axis=(0, 1))
    total = 0.0
    for k, pz_k in enumerate(pz):
        if pz_k <= 0: continue
        pxy_given_z = pxyz[:, :, k] / pz_k
        total += pz_k * I(pxy_given_z)
    return total


def I_joint_yz(pxyz):  # I(X; Y,Z)
    # collapse (y,z) into joint
    nx, ny, nz = pxyz.shape
    pxw = pxyz.reshape(nx, ny * nz)
    return I(pxw)


def random_joint(shape=(3, 3, 3)):
    p = np.random.dirichlet(np.ones(int(np.prod(shape))))
    return p.reshape(shape)


def run_positive_tests():
    results = {}
    oks = []
    for _ in range(20):
        p = random_joint()
        lhs = I_joint_yz(p)
        # rhs: I(X;Y) + I(X;Z|Y)  -- marginalize out z for I(X;Y)
        pxy = p.sum(axis=2)
        rhs = I(pxy) + I_cond(p.transpose(0, 2, 1))  # I(X;Z|Y): Y is conditioning
        oks.append(abs(lhs - rhs) < 1e-9)
    results["chain_rule_holds_on_random_joints"] = all(oks)
    # symmetry: I(X;Y)=I(Y;X)
    p = random_joint((4, 4, 1))[:, :, 0]
    results["MI_symmetry"] = abs(I(p) - I(p.T)) < 1e-12
    return results


def run_negative_tests():
    # dropping a term violates the chain rule
    p = random_joint()
    lhs = I_joint_yz(p)
    rhs_broken = I(p.sum(axis=2))  # missing conditional term
    return {
        "chain_rule_broken_without_conditional_term": abs(lhs - rhs_broken) > 1e-6 or I_cond(p.transpose(0, 2, 1)) < 1e-12,
    }


def run_boundary_tests():
    # independent X of (Y,Z): both sides = 0
    px = np.array([0.3, 0.7]); pyz = np.random.dirichlet(np.ones(9)).reshape(3, 3)
    pxyz = np.einsum("i,jk->ijk", px, pyz)
    return {
        "independence_gives_zero_MI": abs(I_joint_yz(pxyz)) < 1e-10,
        "conditional_nonneg_classical": I_cond(pxyz.transpose(0, 2, 1)) >= -1e-12,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "mutual_information_chain_rule_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": (
            "Classical Shannon chain rule is exact because pmfs factor via Bayes' rule and conditional "
            "entropy is always nonneg. Quantum mutual information I(A;B)=S(A)+S(B)-S(AB) satisfies an "
            "analogous chain rule but via strong subadditivity, not Bayes. The classical baseline cannot "
            "capture that the quantum conditional I(A;B|C) can fail to reduce to a weighted average of "
            "projected subsystem MIs (no joint distribution exists over noncommuting observables), so any "
            "construction that silently assumes a classical joint over all three parties cannot witness "
            "genuinely quantum tripartite correlations."
        ),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "mutual_information_chain_rule_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
