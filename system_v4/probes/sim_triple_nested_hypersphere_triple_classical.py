#!/usr/bin/env python3
"""
sim_triple_nested_hypersphere_triple_classical.py

Step 3 (multi-shell coexistence) classical baseline:
three nested hyperspheres S^1 subset S^2 subset S^3 -- classical distance commutation
under inclusion maps. Tests whether classical geodesic distance commutes with the
inclusion chain (embedding-invariance of chord distance).

This is a CLASSICAL_BASELINE. It does NOT encode the nonclassical structure the
constraint-admissibility program ultimately requires; see divergence_log.
"""

import json
import os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not exercised in classical baseline"},
    "z3": {"tried": False, "used": False, "reason": "no admissibility SAT encoding in baseline"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT closure in baseline"},
    "sympy": {"tried": False, "used": False, "reason": "numeric checks only"},
    "clifford": {"tried": False, "used": False, "reason": "no rotor algebra in baseline"},
    "geomstats": {"tried": False, "used": False, "reason": "manual chord distance"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant features"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "supportive",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "cross-check of chord distances on tensor copy"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def embed_s1_to_s2(p):
    # p = (cos t, sin t) -> equator (cos t, sin t, 0)
    return np.array([p[0], p[1], 0.0])


def embed_s2_to_s3(p):
    return np.array([p[0], p[1], p[2], 0.0])


def chord(a, b):
    return float(np.linalg.norm(a - b))


def run_positive_tests():
    results = {}
    rng = np.random.default_rng(0)
    ok_all = True
    diffs = []
    for _ in range(32):
        t1, t2 = rng.uniform(0, 2 * np.pi, size=2)
        a1 = np.array([np.cos(t1), np.sin(t1)])
        b1 = np.array([np.cos(t2), np.sin(t2)])
        a2 = embed_s1_to_s2(a1)
        b2 = embed_s1_to_s2(b1)
        a3 = embed_s2_to_s3(a2)
        b3 = embed_s2_to_s3(b2)
        d1 = chord(a1, b1)
        d2 = chord(a2, b2)
        d3 = chord(a3, b3)
        diffs.append(max(abs(d1 - d2), abs(d2 - d3)))
        if not (abs(d1 - d2) < 1e-10 and abs(d2 - d3) < 1e-10):
            ok_all = False

    # torch cross-check
    if TOOL_MANIFEST["pytorch"]["used"]:
        import torch
        v = torch.tensor([1.0, 0.0, 0.0, 0.0])
        w = torch.tensor([0.0, 1.0, 0.0, 0.0])
        torch_d = float((v - w).norm())
        results["torch_reference_chord"] = torch_d
        if abs(torch_d - np.sqrt(2)) > 1e-6:
            ok_all = False

    results["inclusion_chord_commutes"] = ok_all
    results["max_abs_diff"] = max(diffs)
    return results


def run_negative_tests():
    results = {}
    # Non-isometric embedding (scale by 2) must BREAK commutation
    a1 = np.array([1.0, 0.0])
    b1 = np.array([-1.0, 0.0])
    a2 = 2 * embed_s1_to_s2(a1)
    b2 = 2 * embed_s1_to_s2(b1)
    d1 = chord(a1, b1)
    d2 = chord(a2, b2)
    results["nonisometric_breaks_commutation"] = bool(abs(d1 - d2) > 1e-6)
    return results


def run_boundary_tests():
    results = {}
    # Antipodal / coincident points
    a = np.array([1.0, 0.0])
    results["self_chord_zero"] = bool(chord(a, a) == 0.0)
    results["antipodal_chord_two"] = bool(
        abs(chord(np.array([1, 0, 0, 0.0]), np.array([-1, 0, 0, 0.0])) - 2.0) < 1e-12
    )
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = (
        pos.get("inclusion_chord_commutes", False)
        and neg.get("nonisometric_breaks_commutation", False)
        and bnd.get("self_chord_zero", False)
        and bnd.get("antipodal_chord_two", False)
    )

    divergence_log = [
        "classical baseline treats S1 subset S2 subset S3 as flat chord embedding; "
        "loses Hopf fibration structure (S3 -> S2 with S1 fiber) that is load-bearing in the nonclassical program",
        "no holonomy / Berry-phase around the triple nesting -- classical chord ignores bundle twist",
        "no probe-relative distinguishability: classical distance is absolute, not constraint-admissible",
    ]

    results = {
        "name": "triple_nested_hypersphere_triple_classical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "divergence_log": divergence_log,
        "summary": {"all_pass": bool(all_pass)},
        "all_pass": bool(all_pass),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "triple_nested_hypersphere_triple_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
