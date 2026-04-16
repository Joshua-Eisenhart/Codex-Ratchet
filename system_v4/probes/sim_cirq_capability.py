#!/usr/bin/env python3
"""
sim_cirq_capability.py -- Cirq capability isolation probe.

This exists solely to establish a bounded passing evidence surface for the
load-bearing Cirq integration used by the bridge probe.
"""

classification = "canonical"
divergence_log = (
    "Capability witness: this probe establishes Cirq simulator availability "
    "and a bounded Bell-preparation surface so the bridge probe can treat "
    "Cirq as a genuine load-bearing integration."
)

import json
import os

import cirq
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": False, "used": False, "reason": "supporting vector arithmetic for the capability check"},
    "cirq": {"tried": False, "used": False, "reason": "under test"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "cirq": "load_bearing",
}

RESULTS = {}

Q0, Q1 = cirq.LineQubit.range(2)


def _all_pass(section):
    return all(bool(v.get("pass", False)) for v in section.values())


def run_positive_tests():
    circuit = cirq.Circuit(cirq.H(Q0), cirq.CNOT(Q0, Q1))
    sim = cirq.Simulator(seed=42)
    result = sim.simulate(circuit)
    state = np.asarray(result.final_state_vector, dtype=complex)
    bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    overlap = float(abs(np.vdot(state, bell)) ** 2)
    return {
        "bell_prep": {
            "pass": bool(overlap > 0.999999),
            "overlap": overlap,
            "statevector": state.tolist(),
        }
    }


def run_negative_tests():
    circuit = cirq.Circuit(cirq.CNOT(Q0, Q1), cirq.H(Q0))
    sim = cirq.Simulator(seed=42)
    result = sim.simulate(circuit)
    state = np.asarray(result.final_state_vector, dtype=complex)
    bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    overlap = float(abs(np.vdot(state, bell)) ** 2)
    return {
        "wrong_order_not_bell": {
            "pass": bool(overlap < 0.95),
            "overlap": overlap,
            "statevector": state.tolist(),
        }
    }


def run_boundary_tests():
    circuit = cirq.Circuit(cirq.I(Q0))
    sim = cirq.Simulator(seed=42)
    result = sim.simulate(circuit, qubit_order=[Q0], initial_state=np.array([1, 0], dtype=complex))
    state = np.asarray(result.final_state_vector, dtype=complex)
    return {
        "identity_circuit": {
            "pass": bool(np.allclose(state, np.array([1, 0], dtype=complex))),
            "statevector": state.tolist(),
        }
    }


def main():
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _all_pass(positive),
        "negative_all_pass": _all_pass(negative),
        "boundary_all_pass": _all_pass(boundary),
    }
    summary["all_pass"] = all(summary.values())
    results = {
        "name": "sim_cirq_capability",
        "purpose": "Cirq capability isolation probe for circuit simulation and statevector readout.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "overall_pass": bool(summary["all_pass"]),
        "classification": classification,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cirq_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
    return results


if __name__ == "__main__":
    main()
