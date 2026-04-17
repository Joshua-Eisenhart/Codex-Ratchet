#!/usr/bin/env python3
"""
Tier A A0x tool-capability probe for pennylane.

Thin capability scope only: pennylane is the only manifested tool, and every
admitted section depends on qnode construction, device execution, or operator
validation that becomes unavailable if the library is removed. If pennylane is
not importable on this machine, the probe stays self-contained and reports
import-gated skips so it can still be committed and enqueued under the overnight
pre-approved default.
"""

import json
import math
import os

classification = "canonical"
NAME = "tool_capability_pennylane"

TOOL_MANIFEST = {
    "pennylane": {
        "tried": False,
        "used": False,
        "reason": "pennylane is the sole quantum-toolkit dependency used for qnode execution, operator validation, and device-level boundary checks in every test section.",
    }
}

TOOL_INTEGRATION_DEPTH = {"pennylane": None}

try:
    import pennylane as qml

    TOOL_MANIFEST["pennylane"]["tried"] = True
    TOOL_INTEGRATION_DEPTH["pennylane"] = "load_bearing"
except ImportError:
    qml = None
    TOOL_MANIFEST["pennylane"]["reason"] = "pennylane import failed on this machine; queued runner execution will show whether the quantum toolkit is installed."


def _mark_pennylane_used() -> None:
    TOOL_MANIFEST["pennylane"]["used"] = True


def _clean_float(value: float, digits: int = 12) -> float:
    rounded = round(float(value), digits)
    return 0.0 if rounded == -0.0 else rounded


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["pennylane"]["tried"]:
        results["pennylane_import_gate"] = {
            "status": "skipped",
            "reason": "pennylane not importable",
        }
        return results

    single_qubit = qml.device("default.qubit", wires=1)

    @qml.qnode(single_qubit)
    def rotated_z_expectation(theta):
        qml.RX(theta, wires=0)
        return qml.expval(qml.PauliZ(0))

    theta = math.pi / 3
    z_value = rotated_z_expectation(theta)
    _mark_pennylane_used()
    results["single_qubit_rx_matches_cosine"] = {
        "theta": _clean_float(theta),
        "observed_z": _clean_float(z_value),
        "expected_z": _clean_float(math.cos(theta)),
        "pass": math.isclose(float(z_value), math.cos(theta), rel_tol=1e-9, abs_tol=1e-9),
    }

    bell_device = qml.device("default.qubit", wires=2)

    @qml.qnode(bell_device)
    def bell_probabilities_and_zz():
        qml.Hadamard(wires=0)
        qml.CNOT(wires=[0, 1])
        return qml.probs(wires=[0, 1]), qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))

    probabilities, zz_value = bell_probabilities_and_zz()
    probs_list = [_clean_float(entry) for entry in probabilities]
    _mark_pennylane_used()
    results["bell_state_survives_entangling_circuit"] = {
        "probabilities": probs_list,
        "expected_probabilities": [0.5, 0.0, 0.0, 0.5],
        "zz_expectation": _clean_float(zz_value),
        "expected_zz_expectation": 1.0,
        "pass": all(
            math.isclose(float(observed), expected, rel_tol=1e-9, abs_tol=1e-9)
            for observed, expected in zip(probabilities, [0.5, 0.0, 0.0, 0.5])
        ) and math.isclose(float(zz_value), 1.0, rel_tol=1e-9, abs_tol=1e-9),
    }

    @qml.qnode(single_qubit)
    def basis_sampling_probabilities():
        qml.PauliX(wires=0)
        return qml.probs(wires=[0])

    basis_probs = basis_sampling_probabilities()
    _mark_pennylane_used()
    results["basis_flip_admits_unit_probability_on_one"] = {
        "probabilities": [_clean_float(entry) for entry in basis_probs],
        "expected_probabilities": [0.0, 1.0],
        "pass": all(
            math.isclose(float(observed), expected, rel_tol=1e-9, abs_tol=1e-9)
            for observed, expected in zip(basis_probs, [0.0, 1.0])
        ),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["pennylane"]["tried"]:
        results["pennylane_import_gate"] = {
            "status": "skipped",
            "reason": "pennylane not importable",
        }
        return results

    one_wire_device = qml.device("default.qubit", wires=1)

    @qml.qnode(one_wire_device)
    def invalid_cnot_on_missing_wire():
        qml.CNOT(wires=[0, 1])
        return qml.expval(qml.PauliZ(0))

    try:
        invalid_cnot_on_missing_wire()
        wire_status = "unexpected_success"
        wire_detail = "CNOT on absent wire was admitted"
    except Exception as exc:
        _mark_pennylane_used()
        wire_status = type(exc).__name__
        wire_detail = str(exc)
    results["missing_wire_operation_excluded"] = {
        "status": wire_status,
        "detail": wire_detail,
        "claim_excluded": wire_status != "unexpected_success",
    }

    @qml.qnode(one_wire_device)
    def invalid_state_norm():
        qml.StatePrep([1.0, 1.0], wires=[0], validate_norm=True)
        return qml.expval(qml.PauliZ(0))

    try:
        invalid_state_norm()
        state_status = "unexpected_success"
        state_detail = "non-normalized state vector was admitted"
    except Exception as exc:
        _mark_pennylane_used()
        state_status = type(exc).__name__
        state_detail = str(exc)
    results["non_normalized_stateprep_excluded"] = {
        "status": state_status,
        "detail": state_detail,
        "claim_excluded": state_status != "unexpected_success",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["pennylane"]["tried"]:
        results["pennylane_import_gate"] = {
            "status": "skipped",
            "reason": "pennylane not importable",
        }
        return results

    device = qml.device("default.qubit", wires=1)

    @qml.qnode(device)
    def rotation_boundary(theta):
        qml.RX(theta, wires=0)
        return qml.expval(qml.PauliZ(0))

    zero_value = rotation_boundary(0.0)
    two_pi_value = rotation_boundary(2 * math.pi)
    _mark_pennylane_used()
    results["rotation_periodicity_boundary"] = {
        "theta_zero_z": _clean_float(zero_value),
        "theta_two_pi_z": _clean_float(two_pi_value),
        "pass": math.isclose(float(zero_value), 1.0, rel_tol=1e-9, abs_tol=1e-9)
        and math.isclose(float(two_pi_value), 1.0, rel_tol=1e-9, abs_tol=1e-9),
    }

    @qml.qnode(device)
    def identity_measurement_boundary():
        return qml.expval(qml.PauliZ(0))

    identity_value = identity_measurement_boundary()
    _mark_pennylane_used()
    results["empty_program_boundary"] = {
        "observed_z": _clean_float(identity_value),
        "expected_z": 1.0,
        "pass": math.isclose(float(identity_value), 1.0, rel_tol=1e-9, abs_tol=1e-9),
    }

    @qml.qnode(device)
    def basis_state_boundary():
        qml.BasisState([1], wires=[0])
        return qml.probs(wires=[0])

    basis_probs = basis_state_boundary()
    _mark_pennylane_used()
    results["basis_state_edge_case_boundary"] = {
        "probabilities": [_clean_float(entry) for entry in basis_probs],
        "expected_probabilities": [0.0, 1.0],
        "pass": all(
            math.isclose(float(observed), expected, rel_tol=1e-9, abs_tol=1e-9)
            for observed, expected in zip(basis_probs, [0.0, 1.0])
        ),
    }

    return results


if __name__ == "__main__":
    results = {
        "name": NAME,
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
        json.dump(results, handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
