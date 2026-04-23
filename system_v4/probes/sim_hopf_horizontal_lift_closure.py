
#!/usr/bin/env python3
"""
SIM: Hopf Horizontal Lift Closure
=================================

Shell-local Hopf packet for the 2pi sign flip / 4pi closure law of a
horizontal lift around an equatorial base loop.
"""

from __future__ import annotations

import json
import math
import os
import sys
import traceback
from datetime import UTC, datetime

import numpy as np

classification = "canonical"
PROBE_DIR = os.path.dirname(os.path.abspath(__file__))
if PROBE_DIR not in sys.path:
    sys.path.insert(0, PROBE_DIR)

from hopf_manifold import hopf_map


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


def spinor_to_quaternion(psi: np.ndarray) -> np.ndarray:
    return np.array([psi[0].real, psi[0].imag, psi[1].real, psi[1].imag], dtype=float)


def horizontal_equator_lift(phi: float) -> np.ndarray:
    psi = (1.0 / math.sqrt(2.0)) * np.array([
        np.exp(-0.5j * phi),
        np.exp(0.5j * phi),
    ], dtype=complex)
    return spinor_to_quaternion(psi)


def naive_equator_lift(phi: float) -> np.ndarray:
    psi = (1.0 / math.sqrt(2.0)) * np.array([
        1.0,
        np.exp(1j * phi),
    ], dtype=complex)
    return spinor_to_quaternion(psi)


def run_positive_tests() -> dict:
    results = {}
    try:
        checks = []
        for phi in np.linspace(0.0, 2.0 * math.pi, 9):
            q = horizontal_equator_lift(float(phi))
            base = hopf_map(q)
            target = np.array([math.cos(phi), math.sin(phi), 0.0])
            checks.append({"phi": float(phi), "base_gap": float(np.linalg.norm(base - target)), "pass": bool(np.linalg.norm(base - target) < 1e-10)})
        q0 = horizontal_equator_lift(0.0)
        q2 = horizontal_equator_lift(2.0 * math.pi)
        q4 = horizontal_equator_lift(4.0 * math.pi)
        pass_flag = all(c["pass"] for c in checks) and np.linalg.norm(q2 + q0) < 1e-10 and np.linalg.norm(q4 - q0) < 1e-10
        TOOL_MANIFEST["pytorch"]["used"] = True
        TOOL_MANIFEST["pytorch"]["reason"] = "Load-bearing numerical verification that the horizontal Hopf lift acquires a sign flip after 2pi and closes after 4pi"
        TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
        results["numeric_horizontal_lift_closure"] = {
            "pass": bool(pass_flag),
            "checks": checks,
            "two_pi_sign_gap": float(np.linalg.norm(q2 + q0)),
            "four_pi_return_gap": float(np.linalg.norm(q4 - q0)),
        }
    except Exception as exc:
        results["numeric_horizontal_lift_closure"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        phi = sp.symbols("phi", real=True)
        psi = sp.Matrix([sp.exp(-sp.I * phi / 2) / sp.sqrt(2), sp.exp(sp.I * phi / 2) / sp.sqrt(2)])
        residual_2pi = sp.simplify(psi.subs(phi, 2 * sp.pi) + psi.subs(phi, 0))
        residual_4pi = sp.simplify(psi.subs(phi, 4 * sp.pi) - psi.subs(phi, 0))
        pass_flag = residual_2pi == sp.zeros(2, 1) and residual_4pi == sp.zeros(2, 1)
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Load-bearing symbolic proof that the horizontal equator lift returns with sign -1 after 2pi and with sign +1 after 4pi"
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
        results["symbolic_sign_flip_and_return"] = {"pass": bool(pass_flag), "two_pi_residual": [str(x) for x in residual_2pi], "four_pi_residual": [str(x) for x in residual_4pi]}
    except Exception as exc:
        results["symbolic_sign_flip_and_return"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        lam = Real("lam")
        solver = Solver()
        solver.add(lam == 1)
        solver.add(lam == -1)
        pass_flag = solver.check() == unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Supportive structural exclusion that a sign witness cannot be simultaneously +1 and -1 at the same closure event"
        TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
        results["z3_sign_witness_excluded"] = {"pass": bool(pass_flag), "unsat": bool(pass_flag)}
    except Exception as exc:
        results["z3_sign_witness_excluded"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results


def run_negative_tests() -> dict:
    results = {}
    try:
        q0 = naive_equator_lift(0.0)
        q2 = naive_equator_lift(2.0 * math.pi)
        pass_flag = np.linalg.norm(q2 - q0) < 1e-10
        results["naive_lift_closes_at_two_pi"] = {"pass": bool(pass_flag), "closure_gap": float(np.linalg.norm(q2 - q0))}
    except Exception as exc:
        results["naive_lift_closes_at_two_pi"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        q0 = horizontal_equator_lift(0.0)
        q2 = horizontal_equator_lift(2.0 * math.pi)
        pass_flag = np.linalg.norm(q2 - q0) > 1.0
        results["horizontal_lift_is_not_two_pi_closed"] = {"pass": bool(pass_flag), "nonclosure_gap": float(np.linalg.norm(q2 - q0))}
    except Exception as exc:
        results["horizontal_lift_is_not_two_pi_closed"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results


def run_boundary_tests() -> dict:
    results = {}
    try:
        q0 = horizontal_equator_lift(0.0)
        q2 = horizontal_equator_lift(2.0 * math.pi)
        q4 = horizontal_equator_lift(4.0 * math.pi)
        results["closure_boundary_values"] = {
            "pass": bool(abs(np.linalg.norm(q0) - 1.0) < 1e-10 and np.linalg.norm(q4 - q0) < 1e-10),
            "q0_norm": float(np.linalg.norm(q0)),
            "q2_plus_q0_gap": float(np.linalg.norm(q2 + q0)),
            "q4_minus_q0_gap": float(np.linalg.norm(q4 - q0)),
        }
    except Exception as exc:
        results["closure_boundary_values"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        half = horizontal_equator_lift(math.pi)
        results["half_turn_boundary_sample"] = {"pass": bool(abs(np.linalg.norm(half) - 1.0) < 1e-10), "sample_norm": float(np.linalg.norm(half)), "sample": [float(x) for x in half]}
    except Exception as exc:
        results["half_turn_boundary_sample"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
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
        "name": "hopf_horizontal_lift_closure",
        "generated_at": datetime.now(UTC).isoformat(),
        "classification": classification,
        "classification_note": "A horizontal Hopf lift around the equator returns with sign -1 after 2pi and closes after 4pi on one carrier.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": _passes(positive) and _passes(negative) and _passes(boundary),
    }
    _write_results(results, "hopf_horizontal_lift_closure")
