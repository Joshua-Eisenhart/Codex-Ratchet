#!/usr/bin/env python3
"""
Tier A A0x tool-capability probe for cirq.

Thin capability scope only: cirq is the only manifested tool, and every
non-skipped test section depends on native circuit, simulator, measurement, or
unitary APIs. If cirq is absent on this machine, the probe stays self-contained
and reports import-gated skipped sections until the overnight runner reaches a
machine state where cirq is importable.
"""

import json
import os

classification = "canonical"
NAME = "tool_capability_cirq"
SCOPE_NOTE = "Tier A cirq capability probe: isolated circuit simulation, contradiction-style exclusions, and edge-boundary behavior."

TOOL_MANIFEST = {
    "cirq": {
        "tried": False,
        "used": False,
        "reason": "cirq is the sole quantum-circuit library used to build circuits, simulate state vectors, and inspect measurement behavior in this capability probe.",
    }
}

TOOL_INTEGRATION_DEPTH = {"cirq": None}

try:
    import cirq

    TOOL_MANIFEST["cirq"]["tried"] = True
    TOOL_INTEGRATION_DEPTH["cirq"] = "load_bearing"
except ImportError:
    cirq = None
    TOOL_MANIFEST["cirq"]["reason"] = "cirq import failed on this machine; the probe stays import-gated and is still queued for the overnight runner."


def _mark_cirq_used() -> None:
    TOOL_MANIFEST["cirq"]["used"] = True


def _complex_list(values):
    return [[float(value.real), float(value.imag)] for value in values]


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["cirq"]["tried"]:
        results["cirq_import_gate"] = {
            "status": "skipped",
            "reason": "cirq not importable",
        }
        return results

    q0, q1 = cirq.LineQubit.range(2)
    simulator = cirq.Simulator()

    bell_circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    bell_state = simulator.simulate(bell_circuit).final_state_vector
    expected_bell = [1.0 / (2.0 ** 0.5), 0.0, 0.0, 1.0 / (2.0 ** 0.5)]
    _mark_cirq_used()
    results["bell_pair_state_vector_survives"] = {
        "circuit": str(bell_circuit),
        "final_state_vector": _complex_list(bell_state),
        "expected_state_vector": _complex_list(expected_bell),
        "pass": all(abs(actual - expected) < 1e-6 for actual, expected in zip(bell_state, expected_bell)),
    }

    bit_flip = cirq.Circuit(cirq.X(q0), cirq.measure(q0, key="m"))
    measurement = simulator.run(bit_flip, repetitions=8)
    ones = measurement.measurements["m"].flatten().tolist()
    _mark_cirq_used()
    results["bit_flip_measurement_survives"] = {
        "circuit": str(bit_flip),
        "repetitions": 8,
        "measurements": ones,
        "expected": [1] * 8,
        "pass": ones == [1] * 8,
    }

    phase_gate = cirq.Circuit(cirq.S(q0))
    phase_unitary = cirq.unitary(phase_gate)
    expected_unitary = [[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 0.0 + 1.0j]]
    _mark_cirq_used()
    results["single_qubit_unitary_survives"] = {
        "circuit": str(phase_gate),
        "unitary": [_complex_list(row) for row in phase_unitary],
        "expected_unitary": [_complex_list(row) for row in expected_unitary],
        "pass": all(abs(phase_unitary[row][col] - expected_unitary[row][col]) < 1e-6 for row in range(2) for col in range(2)),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["cirq"]["tried"]:
        results["cirq_import_gate"] = {
            "status": "skipped",
            "reason": "cirq not importable",
        }
        return results

    q0, q1 = cirq.LineQubit.range(2)
    simulator = cirq.Simulator()

    no_superposition = cirq.Circuit(cirq.CNOT(q0, q1))
    no_superposition_state = simulator.simulate(no_superposition).final_state_vector
    incorrect_bell = [1.0 / (2.0 ** 0.5), 0.0, 0.0, 1.0 / (2.0 ** 0.5)]
    _mark_cirq_used()
    results["bell_claim_without_hadamard_excluded"] = {
        "circuit": str(no_superposition),
        "final_state_vector": _complex_list(no_superposition_state),
        "incorrect_claim": "CNOT on |00> alone admits the Bell-state amplitudes.",
        "claim_excluded": any(abs(actual - expected) > 1e-6 for actual, expected in zip(no_superposition_state, incorrect_bell)),
    }

    identity_measurement = cirq.Circuit(cirq.measure(q0, key="m"))
    identity_results = simulator.run(identity_measurement, repetitions=8).measurements["m"].flatten().tolist()
    _mark_cirq_used()
    results["identity_circuit_excludes_spurious_one_bits"] = {
        "circuit": str(identity_measurement),
        "measurements": identity_results,
        "incorrect_claim": "measuring |0> without a preceding gate admits one-bits.",
        "claim_excluded": identity_results == [0] * 8,
    }

    x_unitary = cirq.unitary(cirq.Circuit(cirq.X(q0)))
    incorrect_identity = [[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]]
    _mark_cirq_used()
    results["pauli_x_excludes_identity_unitary_claim"] = {
        "unitary": [_complex_list(row) for row in x_unitary],
        "incorrect_claim": "Pauli-X admits the identity matrix.",
        "claim_excluded": any(abs(x_unitary[row][col] - incorrect_identity[row][col]) > 1e-6 for row in range(2) for col in range(2)),
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["cirq"]["tried"]:
        results["cirq_import_gate"] = {
            "status": "skipped",
            "reason": "cirq not importable",
        }
        return results

    q0 = cirq.LineQubit(0)
    simulator = cirq.Simulator()

    empty = cirq.Circuit()
    empty_state = simulator.simulate(empty).final_state_vector
    _mark_cirq_used()
    results["empty_circuit_boundary"] = {
        "circuit": str(empty),
        "final_state_vector": _complex_list(empty_state),
        "expected_state_vector": _complex_list([1.0 + 0.0j]),
        "pass": len(empty_state) == 1 and abs(empty_state[0] - (1.0 + 0.0j)) < 1e-6,
    }

    zero_repetition = cirq.Circuit(cirq.measure(q0, key="m"))
    zero_result = simulator.run(zero_repetition, repetitions=0).measurements["m"].tolist()
    _mark_cirq_used()
    results["zero_repetition_measurement_boundary"] = {
        "circuit": str(zero_repetition),
        "repetitions": 0,
        "measurements": zero_result,
        "pass": zero_result == [],
    }

    line_qid = cirq.LineQid(3, dimension=3)
    qutrit_identity = cirq.Circuit(cirq.I(line_qid))
    qutrit_unitary = cirq.unitary(qutrit_identity)
    _mark_cirq_used()
    results["qutrit_identity_boundary"] = {
        "circuit": str(qutrit_identity),
        "qid_dimension": line_qid.dimension,
        "unitary": [_complex_list(row) for row in qutrit_unitary],
        "pass": line_qid.dimension == 3 and len(qutrit_unitary) == 3 and all(abs(qutrit_unitary[row][col] - (1.0 if row == col else 0.0)) < 1e-6 for row in range(3) for col in range(3)),
    }

    return results


if __name__ == "__main__":
    results = {
        "name": NAME,
        "scope_note": SCOPE_NOTE,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True, default=str)
    print(f"Results written to {out_path}")
