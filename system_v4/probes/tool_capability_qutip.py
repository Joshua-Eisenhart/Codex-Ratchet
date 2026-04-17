#!/usr/bin/env python3
"""
Tier A A0x tool-capability probe for qutip.

Thin capability scope only: qutip is the only manifested tool, and every
non-skipped section depends on native Qobj construction, operator evolution,
expectation evaluation, or input validation. If qutip is absent on this
machine, the probe stays self-contained and records import-gated skipped
sections so it can still be committed and enqueued under the overnight
pre-approved default.
"""

import json
import math
import os

classification = "canonical"
NAME = "tool_capability_qutip"
SCOPE_NOTE = (
    "Tier A qutip capability probe: isolated state evolution, exclusion checks, "
    "and boundary behavior gated only by qutip availability."
)

TOOL_MANIFEST = {
    "qutip": {
        "tried": False,
        "used": False,
        "reason": "qutip is the sole quantum-toolkit dependency used here for Qobj construction, operator application, expectation evaluation, and capability-gated input validation.",
    }
}

TOOL_INTEGRATION_DEPTH = {"qutip": None}

try:
    import qutip

    TOOL_MANIFEST["qutip"]["tried"] = True
    TOOL_INTEGRATION_DEPTH["qutip"] = "load_bearing"
except ImportError:
    qutip = None
    TOOL_MANIFEST["qutip"]["reason"] = (
        "qutip import failed on this machine; this overnight capability probe "
        "remains self-contained and records skipped sections until the runner "
        "reaches a qutip-enabled environment."
    )


def _mark_qutip_used() -> None:
    TOOL_MANIFEST["qutip"]["used"] = True


def _clean_float(value: float, digits: int = 12) -> float:
    rounded = round(float(value), digits)
    return 0.0 if rounded == -0.0 else rounded


def _complex_pairs(matrix_like):
    rows = []
    for row in matrix_like:
        rows.append([[float(entry.real), float(entry.imag)] for entry in row])
    return rows


def _skipped_result(reason: str):
    return {"status": "skipped", "reason": reason}


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["qutip"]["tried"]:
        results["qutip_import_gate"] = _skipped_result("qutip not importable")
        return results

    plus_state = (qutip.basis(2, 0) + qutip.basis(2, 1)).unit()
    rho_plus = qutip.ket2dm(plus_state)
    hadamard = qutip.Qobj(
        [[1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0)], [1.0 / math.sqrt(2.0), -1.0 / math.sqrt(2.0)]],
        dims=[[2], [2]],
    )
    transformed = hadamard * plus_state
    overlap_zero = abs((qutip.basis(2, 0).dag() * transformed)[0, 0]) ** 2
    _mark_qutip_used()
    results["hadamard_maps_plus_to_zero_basis"] = {
        "transformed_state": _complex_pairs(transformed.full()),
        "basis_zero_overlap": _clean_float(overlap_zero),
        "expected_basis_zero_overlap": 1.0,
        "pass": math.isclose(overlap_zero, 1.0, rel_tol=1e-9, abs_tol=1e-9),
    }

    sz = qutip.sigmaz()
    expectation = qutip.expect(sz, rho_plus)
    _mark_qutip_used()
    results["plus_state_zero_z_expectation_survives"] = {
        "expectation": _clean_float(expectation),
        "expected_expectation": 0.0,
        "pass": math.isclose(expectation, 0.0, rel_tol=1e-9, abs_tol=1e-9),
    }

    gamma = 0.35
    e0 = qutip.Qobj([[1.0, 0.0], [0.0, math.sqrt(1.0 - gamma)]], dims=[[2], [2]])
    e1 = qutip.Qobj([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dims=[[2], [2]])
    damped = qutip.kraus_to_super([e0, e1]) * rho_plus
    coherence = abs(damped.full()[0][1])
    trace_value = damped.tr()
    _mark_qutip_used()
    results["amplitude_damping_channel_preserves_density_trace"] = {
        "gamma": _clean_float(gamma),
        "density_matrix": _complex_pairs(damped.full()),
        "trace": _clean_float(trace_value),
        "off_diagonal_magnitude": _clean_float(coherence),
        "pass": math.isclose(trace_value, 1.0, rel_tol=1e-9, abs_tol=1e-9) and 0.0 < coherence < 0.5,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["qutip"]["tried"]:
        results["qutip_import_gate"] = _skipped_result("qutip not importable")
        return results

    ket_zero = qutip.basis(2, 0)
    ket_one = qutip.basis(2, 1)
    overlap = abs((ket_one.dag() * ket_zero)[0, 0])
    _mark_qutip_used()
    results["orthogonal_basis_states_exclude_unit_overlap_claim"] = {
        "observed_overlap": _clean_float(overlap),
        "incorrect_claim": "|0> and |1> admit unit overlap.",
        "claim_excluded": math.isclose(overlap, 0.0, rel_tol=1e-9, abs_tol=1e-9),
    }

    try:
        qutip.Qobj([[1.0, 0.0, 0.0], [0.0, 1.0]], dims=[[2], [2]])
        invalid_status = "unexpected_success"
        invalid_detail = "ragged operator shape was admitted"
    except Exception as exc:
        _mark_qutip_used()
        invalid_status = type(exc).__name__
        invalid_detail = str(exc)
    results["invalid_operator_shape_excluded"] = {
        "status": invalid_status,
        "detail": invalid_detail,
        "claim_excluded": invalid_status != "unexpected_success",
    }

    sx = qutip.sigmax()
    sz = qutip.sigmaz()
    commutator_norm = (sx * sz - sz * sx).norm()
    _mark_qutip_used()
    results["pauli_x_commutes_with_pauli_z_claim_excluded"] = {
        "commutator_norm": _clean_float(commutator_norm),
        "incorrect_claim": "Pauli-X and Pauli-Z commute under qutip operator algebra.",
        "claim_excluded": commutator_norm > 0.0,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["qutip"]["tried"]:
        results["qutip_import_gate"] = _skipped_result("qutip not importable")
        return results

    identity = qutip.qeye(2)
    basis_zero = qutip.basis(2, 0)
    identity_state = identity * basis_zero
    identity_overlap = abs((basis_zero.dag() * identity_state)[0, 0]) ** 2
    _mark_qutip_used()
    results["identity_operator_boundary"] = {
        "state_after_identity": _complex_pairs(identity_state.full()),
        "basis_zero_overlap": _clean_float(identity_overlap),
        "pass": math.isclose(identity_overlap, 1.0, rel_tol=1e-9, abs_tol=1e-9),
    }

    rho_zero = qutip.ket2dm(basis_zero)
    entropy_zero = qutip.entropy_vn(rho_zero, base=2)
    _mark_qutip_used()
    results["pure_state_entropy_boundary"] = {
        "entropy_bits": _clean_float(entropy_zero),
        "expected_entropy_bits": 0.0,
        "pass": math.isclose(entropy_zero, 0.0, rel_tol=1e-9, abs_tol=1e-9),
    }

    thermal = qutip.thermal_dm(2, 0.0)
    thermal_diag = [complex(thermal.full()[idx][idx]) for idx in range(2)]
    _mark_qutip_used()
    results["zero_temperature_thermal_state_boundary"] = {
        "diagonal": [[_clean_float(value.real), _clean_float(value.imag)] for value in thermal_diag],
        "pass": math.isclose(thermal_diag[0].real, 1.0, rel_tol=1e-9, abs_tol=1e-9)
        and math.isclose(thermal_diag[1].real, 0.0, rel_tol=1e-9, abs_tol=1e-9),
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
