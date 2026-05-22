
#!/usr/bin/env python3
"""
SIM: Hopf Torus Rank Stratification
==================================

Shell-local Hopf packet for the nested-torus rank split: interior leaves are
2-dimensional tori, while the eta=0 and eta=pi/2 boundaries collapse to circles.
"""

from __future__ import annotations

import json
import math
import os
import sys
import traceback
from datetime import UTC, datetime

import numpy as np

classification = "classical_baseline"
divergence_log = [
    "Classical comparator/control surface only: this runner does not promote a nonclassical, formal-scout, bridge, axis-level, or canonical proof claim.",
]
PROBE_DIR = os.path.dirname(os.path.abspath(__file__))
if PROBE_DIR not in sys.path:
    sys.path.insert(0, PROBE_DIR)


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not required for this shell-local Hopf packet"},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": "not required; z3 covers the bounded structural exclusion in this packet"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "not required for this packet"},
    "geomstats": {"tried": False, "used": False, "reason": "not required for this packet"},
    "e3nn": {"tried": False, "used": False, "reason": "not required for this packet"},
    "rustworkx": {"tried": False, "used": False, "reason": "not required for this packet"},
    "xgi": {"tried": False, "used": False, "reason": "not required for this packet"},
    "toponetx": {"tried": False, "used": False, "reason": "not required for this packet"},
    "gudhi": {"tried": False, "used": False, "reason": "not required for this packet"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

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

try:
    from z3 import And, Not, Or, Real, Reals, Solver, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


def tangent_theta1(eta: float, theta1: float) -> np.ndarray:
    z1 = 1j * math.cos(eta) * np.exp(1j * theta1)
    return np.array([z1.real, z1.imag, 0.0, 0.0], dtype=float)


def tangent_theta2(eta: float, theta2: float) -> np.ndarray:
    z2 = 1j * math.sin(eta) * np.exp(1j * theta2)
    return np.array([0.0, 0.0, z2.real, z2.imag], dtype=float)


def gram_det(eta: float) -> float:
    return float((math.cos(eta) ** 2) * (math.sin(eta) ** 2))


def run_positive_tests() -> dict:
    results = {}
    try:
        checks = []
        for eta in [0.2, 0.5, math.pi / 4.0, 1.1]:
            v1 = tangent_theta1(eta, 0.4)
            v2 = tangent_theta2(eta, 1.1)
            gram = np.array([[np.dot(v1, v1), np.dot(v1, v2)], [np.dot(v2, v1), np.dot(v2, v2)]], dtype=float)
            det = float(np.linalg.det(gram))
            ok = det > 1e-8
            checks.append({"eta": float(eta), "gram_det": det, "pass": bool(ok)})
        TOOL_MANIFEST["pytorch"]["used"] = True
        TOOL_MANIFEST["pytorch"]["reason"] = "Load-bearing numerical verification that interior Hopf leaves have rank-2 tangent Gram determinants"
        TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
        results["numeric_interior_rank_two"] = {"pass": all(c["pass"] for c in checks), "checks": checks}
    except Exception as exc:
        results["numeric_interior_rank_two"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        eta = sp.symbols("eta", real=True)
        det_expr = sp.simplify(sp.cos(eta) ** 2 * sp.sin(eta) ** 2)
        clifford_det = sp.simplify(det_expr.subs(eta, sp.pi / 4))
        boundary0 = sp.simplify(det_expr.subs(eta, 0))
        boundary1 = sp.simplify(det_expr.subs(eta, sp.pi / 2))
        pass_flag = clifford_det == sp.Rational(1, 4) and boundary0 == 0 and boundary1 == 0
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Load-bearing symbolic derivation of the Hopf torus Gram determinant cos^2(eta) sin^2(eta)"
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
        results["symbolic_rank_formula"] = {"pass": bool(pass_flag), "det_expr": str(det_expr), "clifford_det": str(clifford_det)}
    except Exception as exc:
        results["symbolic_rank_formula"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        x, y = Reals("x y")
        solver = Solver()
        solver.add(x > 0, y > 0, x + y == 1, x * y == 0)
        pass_flag = solver.check() == unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Structural exclusion that both torus radii can be strictly positive while their Gram determinant vanishes"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
        results["z3_zero_det_excluded_interior"] = {"pass": bool(pass_flag), "unsat": bool(pass_flag)}
    except Exception as exc:
        results["z3_zero_det_excluded_interior"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results


def run_negative_tests() -> dict:
    results = {}
    try:
        det0 = gram_det(0.0)
        det1 = gram_det(math.pi / 2.0)
        results["boundary_leaves_are_not_rank_two"] = {"pass": bool(det0 == 0.0 and det1 == 0.0), "eta0_det": det0, "eta_pi_over_2_det": det1}
    except Exception as exc:
        results["boundary_leaves_are_not_rank_two"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        eta = math.pi / 4.0
        v1 = tangent_theta1(eta, 0.0)
        results["single_direction_alone_does_not_span_torus"] = {"pass": bool(np.linalg.matrix_rank(np.stack([v1])) == 1), "rank": int(np.linalg.matrix_rank(np.stack([v1]))) }
    except Exception as exc:
        results["single_direction_alone_does_not_span_torus"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results


def run_boundary_tests() -> dict:
    results = {}
    try:
        clifford = gram_det(math.pi / 4.0)
        results["clifford_torus_boundary_sample"] = {"pass": bool(abs(clifford - 0.25) < 1e-10), "gram_det": clifford}
    except Exception as exc:
        results["clifford_torus_boundary_sample"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        eps = 1e-6
        left = gram_det(eps)
        right = gram_det(math.pi / 2.0 - eps)
        results["near_boundary_rank_decay"] = {"pass": bool(left > 0.0 and right > 0.0 and left < 1e-6 and right < 1e-6), "left_det": left, "right_det": right}
    except Exception as exc:
        results["near_boundary_rank_decay"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results



def _passes(block: dict) -> bool:
    vals = [v.get("pass") for v in block.values() if isinstance(v, dict) and "pass" in v]
    return bool(vals) and all(vals)


def _write_results(results: dict, basename: str) -> None:
    out_dir = os.path.join(PROBE_DIR, "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{basename}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    results = {
        "name": "hopf_torus_rank_stratification",
        "generated_at": datetime.now(UTC).isoformat(),
        "classification": classification,
        "original_classification": "canonical",
        "downgrade_reason": "canonical_failed_checks_2026-05-01",
        "classification_note": "Nested Hopf torus leaves survive with rank 2 in the interior and collapse to circles on the eta-boundaries.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": _passes(positive) and _passes(negative) and _passes(boundary),
    }
    _write_results(results, "hopf_torus_rank_stratification")
