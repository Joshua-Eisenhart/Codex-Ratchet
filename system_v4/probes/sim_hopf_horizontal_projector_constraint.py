
#!/usr/bin/env python3
"""
SIM: Hopf Horizontal Projector Constraint
========================================

Shell-local Hopf packet for the principal connection projector. It checks that
vertical motion is removed, horizontal motion survives, and the projector is
idempotent on one Hopf carrier.
"""

from __future__ import annotations

import json
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

from hopf_manifold import random_s3_point


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
    TOOL_MANIFEST["pytorch"]["reason"] = "available but not used; numpy carries this local numerical fixture"
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


def connection_form(q: np.ndarray, v: np.ndarray) -> float:
    return float(q[0] * v[1] - q[1] * v[0] + q[2] * v[3] - q[3] * v[2])


def tangentize(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    return v - np.dot(q, v) * q


def horizontal_project(v: np.ndarray, q: np.ndarray) -> np.ndarray:
    xi = vertical_tangent(q)
    return v - connection_form(q, v) * xi


def run_positive_tests() -> dict:
    results = {}
    try:
        rng = np.random.default_rng(0)
        checks = []
        for _ in range(8):
            q = random_s3_point(rng)
            v = tangentize(q, rng.normal(size=4))
            xi = vertical_tangent(q)
            h = horizontal_project(v, q)
            hh = horizontal_project(h, q)
            ok = abs(connection_form(q, xi) - 1.0) < 1e-10 and abs(connection_form(q, h)) < 1e-10 and np.linalg.norm(hh - h) < 1e-10
            checks.append({
                "connection_on_vertical": float(connection_form(q, xi)),
                "connection_on_horizontal": float(connection_form(q, h)),
                "idempotence_gap": float(np.linalg.norm(hh - h)),
                "pass": bool(ok),
            })
        results["numeric_projector_properties"] = {"pass": all(c["pass"] for c in checks), "checks": checks}
    except Exception as exc:
        results["numeric_projector_properties"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        q0, q1, q2, q3, v0, v1, v2, v3 = sp.symbols("q0 q1 q2 q3 v0 v1 v2 v3", real=True)
        q = sp.Matrix([q0, q1, q2, q3])
        v = sp.Matrix([v0, v1, v2, v3])
        xi = sp.Matrix([-q1, q0, -q3, q2])
        A = q0 * v1 - q1 * v0 + q2 * v3 - q3 * v2
        h = v - A * xi
        Ah = sp.expand(q0 * h[1] - q1 * h[0] + q2 * h[3] - q3 * h[2])
        unit_norm = q0**2 + q1**2 + q2**2 + q3**2
        residual = sp.factor(Ah - A * (1 - unit_norm))
        pass_flag = residual == 0
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Load-bearing symbolic proof that the Hopf projector produces a horizontal vector with A(H(v)) = 0"
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
        results["symbolic_horizontal_annihilation"] = {
            "pass": bool(pass_flag),
            "residual": str(residual),
            "unit_sphere_factor": str(sp.factor(Ah)),
        }
    except Exception as exc:
        results["symbolic_horizontal_annihilation"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        q0, q1, q2, q3, lam = Reals("q0 q1 q2 q3 lam")
        v0, v1, v2, v3 = Reals("v0 v1 v2 v3")
        connection = q0 * v1 - q1 * v0 + q2 * v3 - q3 * v2
        solver = Solver()
        solver.add(q0 == 1, q1 == 0, q2 == 0, q3 == 0)
        solver.add(v0 == 0, v1 == lam, v2 == 0, v3 == 0)
        solver.add(lam != 0)
        solver.add(connection == 0)
        pass_flag = solver.check() == unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Structural exclusion witness that a nonzero pure vertical Hopf tangent at q=(1,0,0,0) cannot have zero connection value"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
        results["z3_nonzero_vertical_zero_connection_excluded"] = {
            "pass": bool(pass_flag),
            "unsat": bool(pass_flag),
            "function_surface": "z3.Solver.check",
        }
    except Exception as exc:
        results["z3_nonzero_vertical_zero_connection_excluded"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results


def run_negative_tests() -> dict:
    results = {}
    try:
        q = np.array([1.0, 0.0, 0.0, 0.0])
        v = np.array([0.0, 0.8, 0.3, 0.0])
        pass_flag = abs(connection_form(q, v)) > 1e-8
        results["raw_vector_with_vertical_component_is_not_horizontal"] = {"pass": bool(pass_flag), "connection_value": float(connection_form(q, v))}
    except Exception as exc:
        results["raw_vector_with_vertical_component_is_not_horizontal"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        q = np.array([1.0, 0.0, 0.0, 0.0])
        bad = np.array([0.4, 0.0, 0.0, 0.0])
        pass_flag = abs(np.dot(q, bad)) > 1e-8
        results["radial_vector_is_not_tangent"] = {"pass": bool(pass_flag), "radial_overlap": float(np.dot(q, bad))}
    except Exception as exc:
        results["radial_vector_is_not_tangent"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
    return results


def run_boundary_tests() -> dict:
    results = {}
    try:
        q = np.array([1.0, 0.0, 0.0, 0.0])
        xi = vertical_tangent(q)
        h = horizontal_project(xi, q)
        results["pure_vertical_boundary_collapses"] = {"pass": bool(np.linalg.norm(h) < 1e-10), "projected_norm": float(np.linalg.norm(h))}
    except Exception as exc:
        results["pure_vertical_boundary_collapses"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        q = np.array([1.0, 0.0, 0.0, 0.0])
        h0 = np.array([0.0, 0.0, 1.0, 0.0])
        h1 = horizontal_project(h0, q)
        results["pure_horizontal_boundary_fixed"] = {"pass": bool(np.linalg.norm(h1 - h0) < 1e-10), "fix_gap": float(np.linalg.norm(h1 - h0))}
    except Exception as exc:
        results["pure_horizontal_boundary_fixed"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}
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
        "name": "hopf_horizontal_projector_constraint",
        "generated_at": datetime.now(UTC).isoformat(),
        "classification": classification,
        "classification_note": "The Hopf horizontal projector is retained only as a local principal-bundle constraint baseline on one carrier.",
        "divergence_log": "Classical baseline only: this packet checks a local Hopf horizontal projector carrier and does not promote QIT, engine, coupling, bridge, axis, or nonclassical claims.",
        "demotion_condition": "Demote if the numeric projector properties, symbolic horizontal annihilation, z3 exclusion, negative controls, or boundary controls fail.",
        "out_of_scope": [
            "QIT engine promotion",
            "scientific coupling promotion",
            "bridge or axis claims",
            "mega-sim evidence",
            "nonclassical interpretation beyond the local Hopf projector carrier",
        ],
        "claim_ceiling": "hopf_horizontal_projector_micro_only",
        "next_lego_target": "tool-lego fit packet for one named Hopf carrier only after independent Wizard admission",
        "promotion_condition": "Requires a separate admitted tool-lego packet with exact prior receipt hash before any lego, coupling, engine, bridge, or axis claim.",
        "blocked_until": "Wizard sim admission, controller-read artifact, and QIT evidence index acceptance all cite this exact result path and hash.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": _passes(positive) and _passes(negative) and _passes(boundary),
    }
    _write_results(results, "sim_hopf_horizontal_projector_constraint")
