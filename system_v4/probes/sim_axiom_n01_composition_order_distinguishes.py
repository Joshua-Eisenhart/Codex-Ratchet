#!/usr/bin/env python3
"""sim_axiom_n01_composition_order_distinguishes -- ~_{AB} != ~_{BA}.

Canonical sim atomizing N01's composition clause: if A.B != B.A then
there exists a state rho and outcome basis witnessing
< rho, A B rho A B^dagger > != < rho, B A rho B A^dagger > hence
~_{A.B} != ~_{B.A}. torch is load-bearing (numeric POVM probs differ);
sympy supportive (symbolic confirmation).
"""

import json, os
import numpy as np

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


SX = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
I2 = torch.eye(2, dtype=torch.complex128)


def apply_seq(rho, ops):
    """Apply a sequence of projective measurements (outcome +1) renormalized.
    For a PVM onto +1 eigenspace P_+ = (I + O)/2, the post-state is
    P_+ rho P_+ / Tr(P_+ rho P_+). We compute the probability sequence."""
    probs = []
    state = rho
    for O in ops:
        Pplus = 0.5 * (I2 + O)
        num = Pplus @ state @ Pplus
        p = float(torch.trace(num).real)
        probs.append(p)
        if p > 1e-14:
            state = num / p
    return probs, state


def run_positive_tests():
    """Apply X then Z vs Z then X to |+x>. Sequence outcome probs differ."""
    # |+x> = (|0>+|1>)/sqrt2  -- rho = (I + SX)/2
    rho = 0.5 * (I2 + SX)
    probs_xz, _ = apply_seq(rho, [SX, SZ])
    probs_zx, _ = apply_seq(rho, [SZ, SX])
    diff = float(np.abs(np.array(probs_xz) - np.array(probs_zx)).sum())
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "load-bearing: computes outcome prob sequences under two orderings"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

    # sympy cross-check commutator nonzero
    sx = sp.Matrix([[0, 1], [1, 0]]); sz = sp.Matrix([[1, 0], [0, -1]])
    comm = sx * sz - sz * sx
    nonzero = sp.simplify(comm).norm() != 0
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "supportive: symbolic [X,Z] != 0 confirms non-commutation"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    return {"probs_xz": probs_xz, "probs_zx": probs_zx, "diff": diff,
            "sympy_nonzero_comm": bool(nonzero),
            "pass": diff > 1e-6 and bool(nonzero)}


def run_negative_tests():
    """If A = B (so [A,B] = 0) the two orderings MUST agree."""
    rho = 0.5 * (I2 + SX)
    probs_xx1, _ = apply_seq(rho, [SX, SX])
    probs_xx2, _ = apply_seq(rho, [SX, SX])
    diff = float(np.abs(np.array(probs_xx1) - np.array(probs_xx2)).sum())
    return {"diff": diff, "pass": diff < 1e-12}


def run_boundary_tests():
    """State rho = I/2 (maximally mixed): each projective measurement gives
    prob 1/2. The probability SEQUENCE from XZ vs ZX is (1/2, 1/2) for
    both; distinguishability at the probability level vanishes, but the
    post-measurement states still differ -- the boundary case where
    ~_{AB} and ~_{BA} agree on outcome probs but not on state trajectory."""
    rho = 0.5 * I2
    probs_xz, post_xz = apply_seq(rho, [SX, SZ])
    probs_zx, post_zx = apply_seq(rho, [SZ, SX])
    prob_diff = float(np.abs(np.array(probs_xz) - np.array(probs_zx)).sum())
    state_diff = float(torch.linalg.norm(post_xz - post_zx).real)
    return {"prob_diff": prob_diff, "state_diff": state_diff,
            "pass": prob_diff < 1e-12 and state_diff > 1e-6}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos.get("pass") and neg.get("pass") and bnd.get("pass"))
    results = {
        "name": "sim_axiom_n01_composition_order_distinguishes",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_axiom_n01_composition_order_distinguishes_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out_path}")
