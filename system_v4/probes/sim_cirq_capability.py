#!/usr/bin/env python3
"""
sim_cirq_capability.py -- Tool-capability isolation sim for cirq.
"""

from __future__ import annotations

import json
import os

import cirq
import numpy as np


classification = "canonical"
divergence_log = (
    "Capability isolation witness for cirq: single-qubit gate, simulator, and "
    "statevector surfaces are exercised here so broader bridge sims can treat "
    "cirq as an admitted circuit witness instead of an ad hoc import."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "supportive numeric checks for cirq capability"},
    "cirq": {"tried": True, "used": True, "reason": "capability under test -- gates, simulator, statevector"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "cirq": "load_bearing",
}

WITNESS_INFO = {
    "witness_use_cases": [
        "system_v4/probes/sim_integration_quantum_open_entangle_correlator_mega_stack.py",
        "system_v4/probes/sim_integration_cirq_pennylane_entanglement_bridge.py",
    ]
}


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def run_positive_tests() -> dict[str, dict[str, object]]:
    qubit = cirq.LineQubit(0)
    sim = cirq.Simulator()
    x_state = sim.simulate(cirq.Circuit(cirq.X(qubit))).final_state_vector
    h_state = sim.simulate(cirq.Circuit(cirq.H(qubit))).final_state_vector
    return {
        "x_gate_reaches_one": {
            "pass": np.allclose(np.abs(x_state) ** 2, np.array([0.0, 1.0]), atol=1e-7),
            "probabilities": (np.abs(x_state) ** 2).tolist(),
        },
        "hadamard_balanced": {
            "pass": np.allclose(np.abs(h_state) ** 2, np.array([0.5, 0.5]), atol=1e-7),
            "probabilities": (np.abs(h_state) ** 2).tolist(),
        },
    }


def run_negative_tests() -> dict[str, dict[str, object]]:
    qubit = cirq.LineQubit(0)
    sim = cirq.Simulator()
    state = sim.simulate(cirq.Circuit(cirq.X(qubit))).final_state_vector
    return {
        "x_gate_not_zero_state": {
            "pass": not np.allclose(np.abs(state) ** 2, np.array([1.0, 0.0]), atol=1e-7),
        }
    }


def run_boundary_tests() -> dict[str, dict[str, object]]:
    qubit = cirq.LineQubit(0)
    sim = cirq.Simulator()
    state = sim.simulate(cirq.Circuit(cirq.rx(1e-8)(qubit))).final_state_vector
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
        "name": "sim_cirq_capability",
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
    out_path = os.path.join(out_dir, "cirq_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
