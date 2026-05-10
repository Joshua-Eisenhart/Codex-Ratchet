#!/usr/bin/env python3
"""Tool-capability isolation sim for Qiskit.

This proves only a tiny Qiskit API surface: construct a circuit, obtain a
statevector/density matrix, and compare an operator expectation against the
known one-qubit answer. It is not a QIT, bridge, axis, or engine admission.
"""

from __future__ import annotations

import json
import os

import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, Operator, Statevector


classification = "canonical"
divergence_log = (
    "Capability isolation witness for qiskit: one-qubit circuit, statevector, "
    "density-matrix, and operator-expectation surfaces are exercised so later "
    "bounded bridge sims can treat qiskit as an available quantum-circuit tool. "
    "No QIT, GStack, axis, bridge, or engine claim is admitted here."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "supportive numeric tolerances for Qiskit arrays"},
    "qiskit": {
        "tried": True,
        "used": True,
        "reason": "capability under test -- circuit, statevector, density matrix, operator expectation",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "qiskit": "load_bearing",
}


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def _json_default(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, complex):
        return {"real": obj.real, "imag": obj.imag}
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def run_positive_tests() -> dict[str, dict[str, object]]:
    qc = QuantumCircuit(1)
    qc.h(0)
    state = Statevector.from_instruction(qc)
    density = DensityMatrix(state)
    z = Operator([[1, 0], [0, -1]])
    x = Operator([[0, 1], [1, 0]])
    return {
        "statevector_plus_state": {
            "pass": np.allclose(state.data, np.array([1.0, 1.0]) / np.sqrt(2.0)),
            "statevector": state.data,
        },
        "density_trace_one": {
            "pass": abs(np.trace(density.data) - 1.0) < 1e-12,
            "trace": np.trace(density.data),
        },
        "plus_has_x_expectation_one": {
            "pass": abs(state.expectation_value(x) - 1.0) < 1e-12,
            "value": state.expectation_value(x),
        },
        "plus_has_z_expectation_zero": {
            "pass": abs(state.expectation_value(z)) < 1e-12,
            "value": state.expectation_value(z),
        },
    }


def run_negative_tests() -> dict[str, dict[str, object]]:
    qc = QuantumCircuit(1)
    qc.x(0)
    state = Statevector.from_instruction(qc)
    plus = np.array([1.0, 1.0]) / np.sqrt(2.0)
    return {
        "bit_flip_is_not_plus_state": {
            "pass": not np.allclose(state.data, plus),
            "statevector": state.data,
        }
    }


def run_boundary_tests() -> dict[str, dict[str, object]]:
    qc = QuantumCircuit(1)
    theta = 1e-8
    qc.ry(theta, 0)
    state = Statevector.from_instruction(qc)
    density = DensityMatrix(state)
    purity = np.trace(density.data @ density.data)
    return {
        "small_rotation_remains_normalized": {
            "pass": abs(np.linalg.norm(state.data) - 1.0) < 1e-12,
            "norm": float(np.linalg.norm(state.data)),
        },
        "pure_density_purity_stable": {
            "pass": abs(purity - 1.0) < 1e-12,
            "purity": purity,
        },
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
        "name": "sim_qiskit_capability",
        "classification": classification,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "qiskit_version": getattr(qiskit, "__version__", None),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "claim_ceiling": "tool_micro_qiskit_capability_only",
        "out_of_scope": [
            "no QIT admission",
            "no GStack admission",
            "no axis admission",
            "no bridge or engine claim",
            "no scientific lego coupling claim",
        ],
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "qiskit_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
