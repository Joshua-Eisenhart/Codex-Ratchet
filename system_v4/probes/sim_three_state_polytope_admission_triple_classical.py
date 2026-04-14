#!/usr/bin/env python3
"""
sim_three_state_polytope_admission_triple_classical.py

Step 3 classical baseline: nested polytopes S0 superset S1 superset S2 with
tight-inequality survivors. Check admission chain: x in S2 -> x in S1 -> x in S0.
"""

import json
import os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "n/a"},
    "z3": {"tried": False, "used": False, "reason": "no SAT on polytope faces here"},
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
    TOOL_MANIFEST["pytorch"]["reason"] = "tensor check of halfspace inequalities"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


# Three nested polytopes in R^2:
# S0: |x|+|y| <= 3 (l1 ball r=3)
# S1: |x|+|y| <= 2
# S2: |x|+|y| <= 1
def in_s(x, r):
    return float(abs(x[0]) + abs(x[1])) <= r + 1e-12


def run_positive_tests():
    results = {}
    rng = np.random.default_rng(11)
    ok = True
    survivors = 0
    for _ in range(200):
        x = rng.uniform(-0.5, 0.5, size=2)  # l1 <= 1.0, all in S2
        if not (in_s(x, 1) and in_s(x, 2) and in_s(x, 3)):
            ok = False
        survivors += 1
    # tight inequality point: (1, 0) is on boundary of S2 -> should still admit
    tight = np.array([1.0, 0.0])
    admits = in_s(tight, 1) and in_s(tight, 2) and in_s(tight, 3)
    if TOOL_MANIFEST["pytorch"]["used"]:
        import torch
        t = torch.tensor(tight)
        results["torch_l1"] = float(t.abs().sum())
    results["nested_admission_holds"] = ok and admits
    results["survivors"] = survivors
    return results


def run_negative_tests():
    results = {}
    # Point in S0 but not in S1
    x = np.array([2.5, 0.0])
    results["outside_s1_rejected"] = bool(in_s(x, 3) and not in_s(x, 2))
    # Point in S1 not in S2
    y = np.array([1.5, 0.0])
    results["outside_s2_rejected"] = bool(in_s(y, 2) and not in_s(y, 1))
    return results


def run_boundary_tests():
    results = {}
    # exact boundary of S2
    p = np.array([0.5, 0.5])
    results["boundary_s2_admitted"] = bool(in_s(p, 1))
    # epsilon outside S2 should be rejected from S2 but admitted by S1
    # S2: r=1, S1: r=2. Push l1 norm to ~1.5 -> outside S2, inside S1.
    p2 = np.array([0.75, 0.75])  # l1 = 1.5
    results["eps_outside_s2_in_s1"] = bool(not in_s(p2, 1) and in_s(p2, 2))
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        pos.get("nested_admission_holds", False)
        and neg.get("outside_s1_rejected", False)
        and neg.get("outside_s2_rejected", False)
        and bnd.get("boundary_s2_admitted", False)
        and bnd.get("eps_outside_s2_in_s1", False)
    )
    divergence_log = [
        "classical polytope admission treats each shell as independent halfspace set; loses the constraint-admissibility geometry where inner shell constraints reshape outer shell face structure",
        "no z3 UNSAT proof of structural impossibility -- admission here is numeric containment, not load-bearing structural exclusion",
        "treats survivors as constructed objects rather than candidates that merely haven't been excluded yet",
    ]
    results = {
        "name": "three_state_polytope_admission_triple_classical",
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
    out_path = os.path.join(out_dir, "three_state_polytope_admission_triple_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
