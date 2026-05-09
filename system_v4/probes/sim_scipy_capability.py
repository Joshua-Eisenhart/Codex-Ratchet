#!/usr/bin/env python3
"""
sim_scipy_capability.py -- Tool-capability isolation sim for scipy.
"""

from __future__ import annotations

import json
import os

import numpy as np
from scipy import linalg


classification = "canonical"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "supportive array surface for scipy capability checks"},
    "scipy": {"tried": True, "used": True, "reason": "capability under test -- matrix exponential and linear solve"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "load_bearing",
}

WITNESS_INFO = {
    "witness_use_cases": [
        "system_v4/probes/sim_integration_thermo_open_system_bridge_stack.py",
        "system_v4/probes/sim_integration_scipy_spectral_eigenvalues.py",
    ]
}


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def run_positive_tests() -> dict[str, dict[str, object]]:
    skew = np.array([[0.0, -1.0], [1.0, 0.0]], dtype=np.float64)
    rot = linalg.expm(0.4 * skew)
    vec = np.array([1.0, 0.0], dtype=np.float64)
    rotated = rot @ vec
    mat = np.array([[3.0, 1.0], [1.0, 2.0]], dtype=np.float64)
    rhs = np.array([1.0, -1.0], dtype=np.float64)
    solved = linalg.solve(mat, rhs)
    return {
        "rotation_orthogonal": {
            "pass": np.allclose(rot.T @ rot, np.eye(2), atol=1e-10),
        },
        "rotation_norm_preserved": {
            "pass": abs(np.linalg.norm(rotated) - 1.0) < 1e-10,
            "rotated": rotated.tolist(),
        },
        "solve_residual": {
            "pass": np.linalg.norm(mat @ solved - rhs) < 1e-10,
            "residual": float(np.linalg.norm(mat @ solved - rhs)),
        },
    }


def run_negative_tests() -> dict[str, dict[str, object]]:
    singular = np.array([[1.0, 1.0], [1.0, 1.0]], dtype=np.float64)
    rhs = np.array([1.0, 2.0], dtype=np.float64)
    raised = False
    err = None
    try:
        linalg.solve(singular, rhs)
    except Exception as exc:  # pragma: no cover - exercised at runtime
        raised = True
        err = type(exc).__name__
    return {
        "singular_solve_raises": {
            "pass": raised,
            "error_type": err,
        }
    }


def run_boundary_tests() -> dict[str, dict[str, object]]:
    skew = np.array([[0.0, -1.0], [1.0, 0.0]], dtype=np.float64)
    rot = linalg.expm(1e-8 * skew)
    return {
        "small_rotation_finite": {
            "pass": np.all(np.isfinite(rot)),
            "trace": float(np.trace(rot)),
        }
    }


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = all(summary.values())
    results = {
        "name": "sim_scipy_capability",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "claim_ceiling": "tool_micro_scipy_capability_only",
        "out_of_scope": [
            "no nonclassical claim",
            "no lego admission",
            "no tool-tool coupling claim",
            "no bridge, axis, engine, or scientific coupling claim",
        ],
        "demotion_condition": "Demote to blocked tool capability if scipy is unavailable, any numerical check fails, or strict receipt lint fails.",
        "promotion_condition": "May only support later classical scipy baseline packets after those packets provide their own admitted receipts.",
        "next_lego_target": "Use as a prerequisite receipt for bounded scipy classical baseline micro packets.",
        "blocked_until": "No broader claim until a downstream packet cites this receipt and passes its own stage gate.",
        "prior_function_receipts": [],
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "scipy_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
