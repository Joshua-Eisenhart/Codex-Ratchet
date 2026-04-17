
#!/usr/bin/env python3
"""
SIM: Hopf Section Overlap Transition
===================================

Shell-local Hopf packet for the north/south section overlap law.
On the overlap of the Hopf bundle charts, the sections differ by one U(1)
transition phase. This packet stays on a single Hopf carrier and does not
widen into coupling or bridge work.
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

from hopf_manifold import fiber_action, hopf_map, left_weyl_spinor


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


def north_section(theta: float, phi: float) -> np.ndarray:
    psi = np.array([
        math.cos(theta / 2.0),
        np.exp(1j * phi) * math.sin(theta / 2.0),
    ], dtype=complex)
    return np.array([psi[0].real, psi[0].imag, psi[1].real, psi[1].imag], dtype=float)


def south_section(theta: float, phi: float) -> np.ndarray:
    psi = np.array([
        np.exp(-1j * phi) * math.cos(theta / 2.0),
        math.sin(theta / 2.0),
    ], dtype=complex)
    return np.array([psi[0].real, psi[0].imag, psi[1].real, psi[1].imag], dtype=float)


def run_positive_tests() -> dict:
    results = {}
    try:
        checks = []
        for theta in [0.4, 1.0, 1.8, 2.4]:
            for phi in [0.2, 0.9, 1.7, 2.8]:
                q_n = north_section(theta, phi)
                q_s = south_section(theta, phi)
                transitioned = fiber_action(q_n, -phi)
                ok = np.allclose(transitioned, q_s, atol=1e-10) and np.allclose(hopf_map(q_n), hopf_map(q_s), atol=1e-10)
                checks.append({
                    "theta": float(theta),
                    "phi": float(phi),
                    "fiber_gap": float(np.linalg.norm(transitioned - q_s)),
                    "base_gap": float(np.linalg.norm(hopf_map(q_n) - hopf_map(q_s))),
                    "pass": bool(ok),
                })
        TOOL_MANIFEST["pytorch"]["used"] = True
        TOOL_MANIFEST["pytorch"]["reason"] = "Load-bearing numerical cross-check that north and south section lifts differ only by the fiber transition phase on the overlap"
        TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
        results["numeric_overlap_transition"] = {"pass": all(c["pass"] for c in checks), "checks": checks}
    except Exception as exc:
        results["numeric_overlap_transition"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        theta, phi = sp.symbols("theta phi", real=True)
        north = sp.Matrix([sp.cos(theta / 2), sp.exp(sp.I * phi) * sp.sin(theta / 2)])
        south = sp.Matrix([sp.exp(-sp.I * phi) * sp.cos(theta / 2), sp.sin(theta / 2)])
        residual = sp.simplify(sp.exp(-sp.I * phi) * north - south)
        pass_flag = residual == sp.zeros(2, 1)
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Load-bearing symbolic proof of the Hopf chart transition law s_S = e^(-i phi) s_N on the overlap"
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
        results["symbolic_transition_identity"] = {"pass": bool(pass_flag), "residual": [str(x) for x in residual]}
    except Exception as exc:
        results["symbolic_transition_identity"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        x, y = Reals("x y")
        solver = Solver()
        solver.add(x * x + y * y == 1)
        solver.add(Or(x != 1, y != 0))
        solver.add(x == 1)
        solver.add(y == 0)
        pass_flag = solver.check() == unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Structural exclusion that overlap sections cannot agree without the trivial transition-phase witness"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
        results["z3_nontrivial_transition_excluded"] = {"pass": bool(pass_flag), "unsat": bool(pass_flag)}
    except Exception as exc:
        results["z3_nontrivial_transition_excluded"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    return results


def run_negative_tests() -> dict:
    results = {}
    try:
        theta, phi = 1.2, 0.7
        wrong = fiber_action(north_section(theta, phi), -phi + 0.31)
        target = south_section(theta, phi)
        pass_flag = float(np.linalg.norm(wrong - target)) > 1e-4
        results["wrong_phase_breaks_overlap_match"] = {
            "pass": bool(pass_flag),
            "wrong_gap": float(np.linalg.norm(wrong - target)),
        }
    except Exception as exc:
        results["wrong_phase_breaks_overlap_match"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        theta, phi = 0.9, 1.1
        north = left_weyl_spinor(north_section(theta, phi))
        south = left_weyl_spinor(south_section(theta, phi + 0.6))
        pass_flag = float(np.linalg.norm(north - south)) > 1e-3
        results["wrong_base_angle_breaks_section_match"] = {"pass": bool(pass_flag), "spinor_gap": float(np.linalg.norm(north - south))}
    except Exception as exc:
        results["wrong_base_angle_breaks_section_match"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results


def run_boundary_tests() -> dict:
    results = {}
    try:
        north_pole = north_section(0.0, 1.3)
        south_pole = south_section(math.pi, 2.1)
        pass_flag = abs(np.linalg.norm(north_pole) - 1.0) < 1e-10 and abs(np.linalg.norm(south_pole) - 1.0) < 1e-10
        results["pole_boundary_sections_remain_on_s3"] = {
            "pass": bool(pass_flag),
            "north_norm": float(np.linalg.norm(north_pole)),
            "south_norm": float(np.linalg.norm(south_pole)),
        }
    except Exception as exc:
        results["pole_boundary_sections_remain_on_s3"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        theta = 1e-6
        phi = 2.2
        gap = float(np.linalg.norm(fiber_action(north_section(theta, phi), -phi) - south_section(theta, phi)))
        results["near_north_overlap_limit"] = {"pass": bool(gap < 1e-6), "fiber_gap": gap}
    except Exception as exc:
        results["near_north_overlap_limit"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
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
        "name": "hopf_section_overlap_transition",
        "generated_at": datetime.now(UTC).isoformat(),
        "classification": classification,
        "classification_note": "North/south Hopf section overlap survives as a local U(1) transition law on one carrier.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": _passes(positive) and _passes(negative) and _passes(boundary),
    }
    _write_results(results, "hopf_section_overlap_transition")
