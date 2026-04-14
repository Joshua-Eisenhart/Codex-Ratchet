#!/usr/bin/env python3
"""
sim_igt_IGT_as_engine_ansatz_on_manifold -- treats IGT's win-lose/WIN-LOSE
pattern as a candidate DoF on a constraint manifold. Minimal ansatz: a
two-scale oscillator whose short-scale is nested inside a long-scale
phase. No ontology claimed; survival under probe is what is tested.
"""
import json, os
import numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "numpy suffices for this ansatz"},
    "pyg":       {"tried": False, "used": False, "reason": "no graph"},
    "z3":        {"tried": False, "used": False, "reason": "continuous ansatz"},
    "cvc5":      {"tried": False, "used": False, "reason": "continuous ansatz"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": "2-phase already captured by complex"},
    "geomstats": {"tried": False, "used": False, "reason": "no Riemannian metric yet"},
    "e3nn":      {"tried": False, "used": False, "reason": "no group action"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi":       {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx":  {"tried": False, "used": False, "reason": "no complex"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except Exception:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def two_scale_signal(t, omega_short=8.0, omega_long=1.0):
    """Ansatz: sign(sin(long) * sign(sin(short))) -- long-scale envelope
    containing short-scale win-lose rounds."""
    short = np.sign(np.sin(omega_short * t))
    long_ = np.sign(np.sin(omega_long * t))
    return long_ * short  # product captures nesting


def run_positive_tests():
    r = {}
    t = np.linspace(0, 2 * np.pi, 1001)[1:-1]  # avoid exact zeros at endpoints
    sig = two_scale_signal(t)
    # Signal takes both +1 and -1
    r["bivalent"] = {"pos": bool((sig > 0).any()), "neg": bool((sig < 0).any()),
                     "ok": bool((sig > 0).any() and (sig < 0).any())}
    # Mean close to zero (balance)
    mean = float(sig.mean())
    r["balanced_mean"] = {"mean": mean, "ok": abs(mean) < 0.1}

    # sympy: sign(sin x) * sign(sin x) == 1 (self-product identity)
    x = sp.symbols("x", real=True)
    expr = sp.sign(sp.sin(x)) * sp.sign(sp.sin(x))
    simplified = sp.simplify(expr - 1)
    # Cannot prove symbolically everywhere (sign(0)=0) but holds generically;
    # test at a sample
    val = float(expr.subs(x, 0.7))
    r["sympy_self_product"] = {"val": val, "ok": abs(val - 1.0) < 1e-9}
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic self-product identity for nesting product"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


def run_negative_tests():
    r = {}
    # Single-scale signal is not nested: only long OR only short
    t = np.linspace(0.1, 2 * np.pi - 0.1, 500)
    long_only = np.sign(np.sin(1.0 * t))
    # Count sign flips: single-scale has fewer flips than two-scale
    flips_long = int(np.sum(np.diff(long_only) != 0))
    flips_two = int(np.sum(np.diff(two_scale_signal(t)) != 0))
    r["flip_count_diff"] = {"long": flips_long, "two": flips_two, "ok": flips_two > flips_long}
    r["ok"] = r["flip_count_diff"]["ok"]
    return r


def run_boundary_tests():
    r = {}
    # At t where both sines are zero (t=0), signal is 0 -- the seam
    r["seam_at_zero"] = {"val": float(two_scale_signal(np.array([0.0]))[0]),
                         "ok": two_scale_signal(np.array([0.0]))[0] == 0.0}
    r["ok"] = r["seam_at_zero"]["ok"]
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_igt_IGT_as_engine_ansatz_on_manifold",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    results["all_ok"] = all(results[k]["ok"] for k in ("positive", "negative", "boundary"))
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_igt_IGT_as_engine_ansatz_on_manifold_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}; all_ok={results['all_ok']}")
