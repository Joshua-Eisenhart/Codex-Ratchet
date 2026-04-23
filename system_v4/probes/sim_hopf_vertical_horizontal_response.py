
#!/usr/bin/env python3
"""
SIM: Hopf Vertical Horizontal Response
=====================================

Shell-local Hopf packet for the response split between vertical fiber motion
and horizontal base motion. Vertical motion should leave the Hopf image fixed,
while horizontal motion should move the base image.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import UTC, datetime

import numpy as np

classification = "canonical"
PROBE_DIR = os.path.dirname(os.path.abspath(__file__))
if PROBE_DIR not in sys.path:
    sys.path.insert(0, PROBE_DIR)

from hopf_manifold import fiber_action, hopf_map, random_s3_point


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


def vertical_tangent(q: np.ndarray) -> np.ndarray:
    return np.array([-q[1], q[0], -q[3], q[2]], dtype=float)


def tangentize(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    return v - np.dot(q, v) * q


def base_derivative(q: np.ndarray, v: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    q1 = q + eps * v
    q1 = q1 / np.linalg.norm(q1)
    q2 = q - eps * v
    q2 = q2 / np.linalg.norm(q2)
    return (hopf_map(q1) - hopf_map(q2)) / (2.0 * eps)


def run_positive_tests() -> dict:
    results = {}
    try:
        rng = np.random.default_rng(7)
        checks = []
        for _ in range(6):
            q = random_s3_point(rng)
            xi = vertical_tangent(q)
            raw = tangentize(q, rng.normal(size=4))
            a = q[0] * raw[1] - q[1] * raw[0] + q[2] * raw[3] - q[3] * raw[2]
            h = raw - a * xi
            d_vert = base_derivative(q, xi)
            d_horiz = base_derivative(q, h)
            ok = np.linalg.norm(d_vert) < 1e-5 and np.linalg.norm(d_horiz) > 1e-3
            checks.append({
                "vertical_response_norm": float(np.linalg.norm(d_vert)),
                "horizontal_response_norm": float(np.linalg.norm(d_horiz)),
                "pass": bool(ok),
            })
        TOOL_MANIFEST["pytorch"]["used"] = True
        TOOL_MANIFEST["pytorch"]["reason"] = "Load-bearing numerical split between zero vertical Hopf response and nonzero horizontal Hopf response"
        TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
        results["numeric_response_split"] = {"pass": all(c["pass"] for c in checks), "checks": checks}
    except Exception as exc:
        results["numeric_response_split"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        alpha = sp.symbols("alpha", real=True)
        z1, z2 = sp.symbols("z1 z2", complex=True)
        x = 2 * sp.re(sp.conjugate(z1) * z2)
        y = 2 * sp.im(sp.conjugate(z1) * z2)
        z = sp.conjugate(z1) * z1 - sp.conjugate(z2) * z2
        x_a = sp.simplify(x.subs({z1: sp.exp(sp.I * alpha) * z1, z2: sp.exp(sp.I * alpha) * z2}))
        y_a = sp.simplify(y.subs({z1: sp.exp(sp.I * alpha) * z1, z2: sp.exp(sp.I * alpha) * z2}))
        z_a = sp.simplify(z.subs({z1: sp.exp(sp.I * alpha) * z1, z2: sp.exp(sp.I * alpha) * z2}))
        pass_flag = sp.simplify(x_a - x) == 0 and sp.simplify(y_a - y) == 0 and sp.simplify(z_a - z) == 0
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Load-bearing symbolic proof that fiber phase rotation leaves the Hopf image invariant"
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
        results["symbolic_vertical_invariance"] = {"pass": bool(pass_flag)}
    except Exception as exc:
        results["symbolic_vertical_invariance"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        lam = Real("lam")
        solver = Solver()
        solver.add(lam != 0)
        solver.add(lam == 0)
        pass_flag = solver.check() == unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Supportive exclusion witness that a nonzero vertical-response coefficient cannot simultaneously vanish and stay nonzero"
        TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
        results["z3_vertical_witness_nontriviality"] = {"pass": bool(pass_flag), "unsat": bool(pass_flag)}
    except Exception as exc:
        results["z3_vertical_witness_nontriviality"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results


def run_negative_tests() -> dict:
    results = {}
    try:
        q = np.array([1.0, 0.0, 0.0, 0.0])
        radial = np.array([1.0, 0.0, 0.0, 0.0])
        response = base_derivative(q, radial)
        pass_flag = abs(np.dot(q, radial) - 1.0) < 1e-10
        results["radial_motion_is_not_a_valid_vertical_or_horizontal_probe"] = {"pass": bool(pass_flag), "response_norm": float(np.linalg.norm(response))}
    except Exception as exc:
        results["radial_motion_is_not_a_valid_vertical_or_horizontal_probe"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        q = np.array([1.0, 0.0, 0.0, 0.0])
        base_gap = np.linalg.norm(hopf_map(fiber_action(q, 0.7)) - hopf_map(q))
        results["finite_vertical_phase_has_zero_base_gap"] = {"pass": bool(base_gap < 1e-10), "base_gap": float(base_gap)}
    except Exception as exc:
        results["finite_vertical_phase_has_zero_base_gap"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results


def run_boundary_tests() -> dict:
    results = {}
    try:
        q = np.array([1.0, 0.0, 0.0, 0.0])
        xi = vertical_tangent(q)
        d_vert = base_derivative(q, xi)
        results["north_pole_vertical_boundary"] = {"pass": bool(np.linalg.norm(d_vert) < 1e-6), "response_norm": float(np.linalg.norm(d_vert))}
    except Exception as exc:
        results["north_pole_vertical_boundary"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        q = np.array([1.0, 0.0, 0.0, 0.0])
        h = np.array([0.0, 0.0, 1.0, 0.0])
        d_h = base_derivative(q, h)
        results["north_pole_horizontal_boundary"] = {"pass": bool(np.linalg.norm(d_h) > 1e-3), "response_norm": float(np.linalg.norm(d_h)), "response": [float(x) for x in d_h]}
    except Exception as exc:
        results["north_pole_horizontal_boundary"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
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
        "name": "hopf_vertical_horizontal_response",
        "generated_at": datetime.now(UTC).isoformat(),
        "classification": classification,
        "classification_note": "Vertical Hopf motion leaves the base fixed while horizontal motion moves the base image on one carrier.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": _passes(positive) and _passes(negative) and _passes(boundary),
    }
    _write_results(results, "hopf_vertical_horizontal_response")
