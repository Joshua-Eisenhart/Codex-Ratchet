#!/usr/bin/env python3
"""
sim_numpy_capability.py -- Tool-capability isolation sim for numpy.
"""

from __future__ import annotations

import json
import os

import numpy as np

from receipt_boundary import apply_default_receipt_boundary

classification = "classical_baseline"
divergence_log = (
    "Classical numpy dense-array capability baseline only; it checks local array algebra behavior "
    "and cannot prove nonclassical, bridge, axis, GStack, or QIT claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "capability under test -- dense array algebra"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
}

WITNESS_INFO = {
    "witness_use_cases": [
        "system_v4/probes/sim_axis0_orbit_phase_alignment.py",
        "system_v4/probes/sim_integration_thermo_open_system_bridge_stack.py",
    ]
}


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def run_positive_tests() -> dict[str, dict[str, object]]:
    vec = np.array([1.0, -2.0, 3.0], dtype=np.float64)
    mat = np.array([[2.0, 0.0, 1.0], [0.0, 3.0, -1.0], [1.0, -1.0, 4.0]], dtype=np.float64)
    eigvals = np.linalg.eigvalsh(mat)
    solved = np.linalg.solve(mat, vec)
    return {
        "matvec_shape": {
            "pass": np.allclose(mat @ vec, np.array([5.0, -9.0, 15.0])),
        },
        "solve_residual": {
            "pass": np.linalg.norm(mat @ solved - vec) < 1e-10,
            "residual": float(np.linalg.norm(mat @ solved - vec)),
        },
        "eigenvalues_real": {
            "pass": bool(np.all(np.isreal(eigvals))),
            "eigenvalues": eigvals.tolist(),
        },
    }


def run_negative_tests() -> dict[str, dict[str, object]]:
    raised = False
    err = None
    try:
        np.matmul(np.ones((2, 3)), np.ones((4, 2)))
    except Exception as exc:  # pragma: no cover - exercised at runtime
        raised = True
        err = type(exc).__name__
    return {
        "shape_mismatch_raises": {
            "pass": raised,
            "error_type": err,
        }
    }


def run_boundary_tests() -> dict[str, dict[str, object]]:
    small = np.array([1e-12, -1e-12, 2e-12], dtype=np.float64)
    norm = np.linalg.norm(small)
    return {
        "small_norm_stable": {
            "pass": np.isfinite(norm) and norm > 0.0,
            "norm": float(norm),
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
        "name": "sim_numpy_capability",
        "classification": classification,
        "classification_note": "Numpy is admitted only as a classical baseline/supportive numerical tool, not as load-bearing evidence for QIT, bridge, axis, GStack, or nonclassical claims.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": divergence_log,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_numpy_capability",
        target=(
            "Use only as bounded classical numpy capability baseline before "
            "tool-lego rows that require separate non-numpy receipts."
        ),
    )
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_numpy_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
