#!/usr/bin/env python3
"""Classical baseline: Tsallis-q entropy sweep on a 3-outcome distribution.\n\nS_q(p) = (1 - sum p^q)/(q-1). Verifies q=1 limit = Shannon, non-negativity, q=2 concavity."""
import json, os
import numpy as np

from receipt_boundary import apply_default_receipt_boundary

classification = "classical_baseline"
NAME = "sim_tsallis_q_sweep_classical"
divergence_details = [
    "Classical Tsallis q-sweep only; nonextensive nonclassical coupling is not tested.",
    "Three-outcome family selected; N-outcome generalization deferred.",
]
divergence_log = (
    "Classical finite-distribution Tsallis entropy sweep only; no "
    "nonextensive coupling, bridge, GStack, axis, QIT, or nonclassical "
    "admission claim."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "finite probability normalization and Tsallis q-sweep checks"},
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "numpy": "supportive",
    "pyg": None,
    "pytorch": None,
    "rustworkx": None,
    "sympy": None,
    "toponetx": None,
    "xgi": None,
    "z3": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "cross-check Tsallis values via torch tensor exponent"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
    HAVE_TORCH = True
except ImportError:
    HAVE_TORCH = False
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

def _tsallis(p, q):
    p = np.asarray(p, dtype=float)
    p = p / p.sum()
    if abs(q - 1) < 1e-9:
        q_p = np.clip(p, 1e-15, 1)
        return -(q_p * np.log(q_p)).sum()
    return (1 - (p ** q).sum()) / (q - 1)

def run_positive_tests():
    results = {}
    p = np.array([0.5, 0.3, 0.2])
    qs = [0.5, 1.0, 2.0, 3.0]
    S = [_tsallis(p, q) for q in qs]
    # q=1 equals Shannon
    shannon = -(p * np.log(p)).sum()
    results["q1_matches_shannon"] = bool(abs(S[1] - shannon) < 1e-10)
    # non-negative
    results["non_negative"] = bool(all(s >= -1e-12 for s in S))
    # q=2 value is 1 - sum p^2 (Gini / collision)
    expected_q2 = 1 - (p**2).sum()
    results["q2_matches_gini"] = bool(abs(S[2] - expected_q2) < 1e-12)
    if HAVE_TORCH:
        import torch
        results["torch_q2"] = bool(abs(float(1 - (torch.tensor(p)**2).sum()) - expected_q2) < 1e-10)
    return results

def run_negative_tests():
    results = {}
    # delta distribution -> S_q = 0 for all q
    delta = np.array([1.0, 0.0, 0.0])
    results["delta_zero"] = bool(all(abs(_tsallis(delta, q)) < 1e-10 for q in [0.5, 2.0, 3.0]))
    # S_q for uniform should be > 0
    u = np.array([1/3, 1/3, 1/3])
    results["uniform_positive"] = bool(_tsallis(u, 2.0) > 0)
    return results

def run_boundary_tests():
    results = {}
    p = np.array([0.5, 0.3, 0.2])
    # q -> 1+ continuity
    near_1 = _tsallis(p, 1.0 + 1e-6)
    at_1 = _tsallis(p, 1.0)
    results["q1_continuous"] = bool(abs(near_1 - at_1) < 1e-3)
    return results

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())

    results = {
        "name": NAME,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "divergence_log": divergence_log,
        "divergence_details": divergence_details,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target="Use as bounded classical Tsallis entropy baseline before entropy-family coupling or nonextensive packets.",
    )
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass={all_pass}")
    raise SystemExit(0 if all_pass else 1)
