#!/usr/bin/env python3
"""
sim_triple_markov_dpi_triple_classical.py

Step 3 (multi-shell coexistence) classical baseline:
three-stage Markov chain X -> Y -> Z, classical Data Processing Inequality
I(X;Z) <= I(X;Y) and I(X;Z) <= I(Y;Z).
"""

import json
import os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "no graph nn"},
    "z3": {"tried": False, "used": False, "reason": "numeric DPI only"},
    "cvc5": {"tried": False, "used": False, "reason": "n/a"},
    "sympy": {"tried": False, "used": False, "reason": "n/a"},
    "clifford": {"tried": False, "used": False, "reason": "n/a"},
    "geomstats": {"tried": False, "used": False, "reason": "n/a"},
    "e3nn": {"tried": False, "used": False, "reason": "n/a"},
    "rustworkx": {"tried": False, "used": False, "reason": "n/a"},
    "xgi": {"tried": False, "used": False, "reason": "n/a"},
    "toponetx": {"tried": False, "used": False, "reason": "n/a"},
    "gudhi": {"tried": False, "used": False, "reason": "n/a"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "tensor-space cross-check of joint distribution sums"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def mutual_information(p_xy):
    p_x = p_xy.sum(axis=1, keepdims=True)
    p_y = p_xy.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        logterm = np.where(p_xy > 0, np.log(p_xy / (p_x * p_y + 1e-300) + 1e-300), 0.0)
    return float(np.sum(p_xy * logterm))


def chain_joint(p_x, T_yx, T_zy):
    # p_xyz[i,j,k] = p_x[i] * T_yx[j,i] * T_zy[k,j]
    p_xy = p_x[:, None] * T_yx.T  # (X, Y)
    p_xyz = p_xy[:, :, None] * T_zy.T[None, :, :]
    return p_xyz


def run_positive_tests():
    results = {}
    rng = np.random.default_rng(7)
    ok = True
    for _ in range(16):
        n = 4
        p_x = rng.dirichlet(np.ones(n))
        T_yx = rng.dirichlet(np.ones(n), size=n).T  # columns sum to 1; T_yx[j,i]=p(y=j|x=i)
        T_yx = T_yx / T_yx.sum(axis=0, keepdims=True)
        T_zy = rng.dirichlet(np.ones(n), size=n).T
        T_zy = T_zy / T_zy.sum(axis=0, keepdims=True)

        pxyz = chain_joint(p_x, T_yx, T_zy)
        p_xy = pxyz.sum(axis=2)
        p_yz = pxyz.sum(axis=0)
        p_xz = pxyz.sum(axis=1)

        I_xy = mutual_information(p_xy)
        I_yz = mutual_information(p_yz)
        I_xz = mutual_information(p_xz)

        if not (I_xz <= I_xy + 1e-10 and I_xz <= I_yz + 1e-10):
            ok = False

    if TOOL_MANIFEST["pytorch"]["used"]:
        import torch
        t = torch.tensor(pxyz)
        results["torch_joint_sum"] = float(t.sum())
        if abs(results["torch_joint_sum"] - 1.0) > 1e-6:
            ok = False

    results["dpi_holds_across_triples"] = ok
    return results


def run_negative_tests():
    results = {}
    # Violate DPI by using NON-Markov joint (X and Z directly coupled).
    # Build a joint where I(X;Z) > I(X;Y).
    n = 3
    # Y independent of X, Z copy of X
    p_x = np.array([1/3, 1/3, 1/3])
    T_yx = np.full((n, n), 1/n)  # Y independent -> I(X;Y)=0
    p_xy = p_x[:, None] * T_yx.T
    p_xz_direct = np.eye(n) / n  # Z = X perfect copy
    I_xy = mutual_information(p_xy)
    I_xz = mutual_information(p_xz_direct)
    results["direct_xz_beats_indirect_xy"] = bool(I_xz > I_xy + 1e-9)
    return results


def run_boundary_tests():
    results = {}
    # All deterministic identity channels => I(X;Y)=I(Y;Z)=I(X;Z)=H(X)
    n = 3
    p_x = np.array([0.5, 0.3, 0.2])
    T = np.eye(n)
    pxyz = chain_joint(p_x, T, T)
    I_xy = mutual_information(pxyz.sum(axis=2))
    I_xz = mutual_information(pxyz.sum(axis=1))
    H_x = -float(np.sum(p_x * np.log(p_x)))
    results["identity_chain_equalities"] = bool(
        abs(I_xy - H_x) < 1e-10 and abs(I_xz - H_x) < 1e-10
    )
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = (
        pos.get("dpi_holds_across_triples", False)
        and neg.get("direct_xz_beats_indirect_xy", False)
        and bnd.get("identity_chain_equalities", False)
    )

    divergence_log = [
        "classical DPI assumes well-defined joint p(x,y,z); nonclassical triple-nesting lacks a commutative joint (conditional distributions need not lift)",
        "loses the contextuality witness visible only when X-Y-Z are distinguishability-constrained, not probabilistically coupled",
        "entropy-based I(.;.) used as organizing variable violates 'constraints prior to entropy' discipline",
    ]

    results = {
        "name": "triple_markov_dpi_triple_classical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "divergence_log": divergence_log,
        "summary": {"all_pass": bool(all_pass)},
        "all_pass": bool(all_pass),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "triple_markov_dpi_triple_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
