#!/usr/bin/env python3
"""
sim_pennylane_capability.py -- Tool-capability isolation sim for pennylane.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pennylane as qml


classification = "canonical"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "supportive numeric checks for pennylane capability"},
    "pennylane": {"tried": True, "used": True, "reason": "capability under test -- qnode, state, gradient"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pennylane": "load_bearing",
}

DEV = qml.device("default.qubit", wires=1)


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


@qml.qnode(DEV)
def _state_qnode(theta: float) -> np.ndarray:
    qml.RY(theta, wires=0)
    return qml.state()


@qml.qnode(DEV)
def _z_qnode(theta):
    qml.RY(theta, wires=0)
    return qml.expval(qml.PauliZ(0))


def run_positive_tests() -> dict[str, dict[str, object]]:
    state = _state_qnode(np.pi / 2)
    theta = qml.numpy.array(0.3, requires_grad=True)
    grad = float(qml.grad(_z_qnode)(theta))
    return {
        "balanced_probabilities": {
            "pass": np.allclose(np.abs(state) ** 2, np.array([0.5, 0.5]), atol=1e-7),
            "probabilities": (np.abs(state) ** 2).tolist(),
        },
        "gradient_matches_analytic": {
            "pass": abs(grad + np.sin(0.3)) < 1e-7,
            "gradient": grad,
            "expected": float(-np.sin(0.3)),
        },
    }


def run_negative_tests() -> dict[str, dict[str, object]]:
    state = _state_qnode(np.pi)
    return {
        "pi_rotation_not_ground": {
            "pass": not np.allclose(np.abs(state) ** 2, np.array([1.0, 0.0]), atol=1e-7),
        }
    }


def run_boundary_tests() -> dict[str, dict[str, object]]:
    state = _state_qnode(1e-8)
    return {
        "tiny_rotation_finite": {
            "pass": np.all(np.isfinite(state)),
            "norm": float(np.linalg.norm(state)),
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
        "name": "sim_pennylane_capability",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pennylane_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
