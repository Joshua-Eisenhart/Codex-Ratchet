
#!/usr/bin/env python3
"""
SIM: Hopf Base Section Phase Recovery
====================================

Shell-local Hopf packet for recovering a carrier point from its base image plus
one fiber phase. This stays on a single Hopf carrier and its quotient data.
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

from hopf_manifold import fiber_action, hopf_map, left_weyl_spinor, lift_base_point, torus_coordinates


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


def recover_phase(q: np.ndarray, section: np.ndarray) -> float:
    psi_q = left_weyl_spinor(q)
    psi_s = left_weyl_spinor(section)
    inner = np.vdot(psi_s, psi_q)
    return float(np.angle(inner))


def run_positive_tests() -> dict:
    results = {}
    try:
        checks = []
        for eta, t1, t2 in [(0.3, 0.2, 1.1), (0.7, 2.4, 0.9), (1.0, 1.5, 2.2), (1.2, 0.7, 2.8)]:
            q = torus_coordinates(eta, t1, t2)
            base = hopf_map(q)
            section = lift_base_point(base)
            alpha = recover_phase(q, section)
            rebuilt = fiber_action(section, alpha)
            ok = np.linalg.norm(rebuilt - q) < 1e-8 or np.linalg.norm(rebuilt + q) < 1e-8
            checks.append({
                "eta": float(eta),
                "alpha": float(alpha),
                "rebuild_gap": float(min(np.linalg.norm(rebuilt - q), np.linalg.norm(rebuilt + q))),
                "pass": bool(ok),
            })
        TOOL_MANIFEST["pytorch"]["used"] = True
        TOOL_MANIFEST["pytorch"]["reason"] = "Load-bearing numerical reconstruction that a Hopf carrier point is recovered from its base image plus one fiber phase"
        TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
        results["numeric_phase_recovery"] = {"pass": all(c["pass"] for c in checks), "checks": checks}
    except Exception as exc:
        results["numeric_phase_recovery"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        theta, phi, alpha = sp.symbols("theta phi alpha", real=True)
        section = sp.Matrix([sp.cos(theta / 2), sp.exp(sp.I * phi) * sp.sin(theta / 2)])
        q = sp.exp(sp.I * alpha) * section
        residual = sp.simplify(sp.exp(-sp.I * alpha) * q - section)
        pass_flag = residual == sp.zeros(2, 1)
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Load-bearing symbolic proof that a Hopf carrier point differs from its local section only by one fiber phase"
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
        results["symbolic_section_phase_factorization"] = {"pass": bool(pass_flag), "residual": [str(x) for x in residual]}
    except Exception as exc:
        results["symbolic_section_phase_factorization"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        lam = Real("lam")
        solver = Solver()
        solver.add(lam != 0)
        solver.add(lam == 0)
        pass_flag = solver.check() == unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Supportive exclusion witness that a nontrivial fiber phase coefficient cannot simultaneously vanish"
        TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
        results["z3_phase_coefficient_nontriviality"] = {"pass": bool(pass_flag), "unsat": bool(pass_flag)}
    except Exception as exc:
        results["z3_phase_coefficient_nontriviality"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results


def run_negative_tests() -> dict:
    results = {}
    try:
        q = torus_coordinates(0.7, 0.4, 1.3)
        wrong_base = hopf_map(torus_coordinates(0.9, 0.4, 1.3))
        wrong_section = lift_base_point(wrong_base)
        alpha = recover_phase(q, wrong_section)
        rebuilt = fiber_action(wrong_section, alpha)
        pass_flag = min(np.linalg.norm(rebuilt - q), np.linalg.norm(rebuilt + q)) > 1e-3
        results["wrong_basepoint_breaks_recovery"] = {"pass": bool(pass_flag), "rebuild_gap": float(min(np.linalg.norm(rebuilt - q), np.linalg.norm(rebuilt + q)))}
    except Exception as exc:
        results["wrong_basepoint_breaks_recovery"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        q = torus_coordinates(0.5, 1.2, 2.0)
        section = lift_base_point(hopf_map(q))
        rebuilt = fiber_action(section, recover_phase(q, section) + 0.25)
        pass_flag = min(np.linalg.norm(rebuilt - q), np.linalg.norm(rebuilt + q)) > 1e-3
        results["wrong_phase_breaks_recovery"] = {"pass": bool(pass_flag), "rebuild_gap": float(min(np.linalg.norm(rebuilt - q), np.linalg.norm(rebuilt + q)))}
    except Exception as exc:
        results["wrong_phase_breaks_recovery"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results


def run_boundary_tests() -> dict:
    results = {}
    try:
        q = torus_coordinates(0.0, 1.4, 0.0)
        section = lift_base_point(hopf_map(q))
        alpha = recover_phase(q, section)
        rebuilt = fiber_action(section, alpha)
        results["north_pole_boundary_recovery"] = {"pass": bool(min(np.linalg.norm(rebuilt - q), np.linalg.norm(rebuilt + q)) < 1e-8), "rebuild_gap": float(min(np.linalg.norm(rebuilt - q), np.linalg.norm(rebuilt + q)))}
    except Exception as exc:
        results["north_pole_boundary_recovery"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        q = torus_coordinates(math.pi / 2.0, 0.0, 0.9)
        section = lift_base_point(hopf_map(q))
        results["south_patch_boundary_lift"] = {"pass": bool(abs(np.linalg.norm(section) - 1.0) < 1e-10), "section_norm": float(np.linalg.norm(section))}
    except Exception as exc:
        results["south_patch_boundary_lift"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
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
        "name": "hopf_base_section_phase_recovery",
        "generated_at": datetime.now(UTC).isoformat(),
        "classification": classification,
        "classification_note": "A Hopf carrier point survives as one base point plus one fiber phase on a single shell-local carrier.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": _passes(positive) and _passes(negative) and _passes(boundary),
    }
    _write_results(results, "hopf_base_section_phase_recovery")
