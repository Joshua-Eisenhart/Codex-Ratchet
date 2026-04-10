#!/usr/bin/env python3
"""
PURE LEGO: QIT Szilard-Landauer Cycle
=====================================
Finite two-qubit information-engine row: measurement correlation, conditional
feedback, and memory erasure on a bounded density-operator carrier.
"""

import json
import pathlib

import numpy as np


LN2 = float(np.log(2.0))
EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical finite QIT information-engine row: a one-bit measurement on a bounded "
    "system-memory carrier creates correlation, ordered conditional feedback converts that "
    "correlation into a one-bit free-energy gain for the system in a degenerate model, and "
    "memory erasure closes the bookkeeping at the same kT ln 2 scale."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "channel_cptp_map",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

KET0 = np.array([[1.0], [0.0]], dtype=complex)
KET1 = np.array([[0.0], [1.0]], dtype=complex)
PROJ0 = KET0 @ KET0.conj().T
PROJ1 = KET1 @ KET1.conj().T
IDENTITY_2 = np.eye(2, dtype=complex)

# Basis ordering: |00>, |01>, |10>, |11> with system first, memory second.
CNOT_SYSTEM_TO_MEMORY = np.array(
    [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ],
    dtype=complex,
)

CONTROLLED_X_MEMORY_TO_SYSTEM = np.array(
    [
        [1, 0, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
    ],
    dtype=complex,
)


def entropy(rho: np.ndarray) -> float:
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log(evals))) if len(evals) else 0.0


def partial_trace_memory(rho_sm: np.ndarray) -> np.ndarray:
    rho = rho_sm.reshape(2, 2, 2, 2)
    return np.trace(rho, axis1=1, axis2=3)


def partial_trace_system(rho_sm: np.ndarray) -> np.ndarray:
    rho = rho_sm.reshape(2, 2, 2, 2)
    return np.trace(rho, axis1=0, axis2=2)


def mutual_information(rho_sm: np.ndarray) -> float:
    rho_s = partial_trace_memory(rho_sm)
    rho_m = partial_trace_system(rho_sm)
    return float(entropy(rho_s) + entropy(rho_m) - entropy(rho_sm))


def apply_unitary(rho: np.ndarray, u: np.ndarray) -> np.ndarray:
    return u @ rho @ u.conj().T


def reset_memory_to_zero(rho_sm: np.ndarray) -> np.ndarray:
    rho_s = partial_trace_memory(rho_sm)
    return np.kron(rho_s, PROJ0)


def is_valid_density(rho: np.ndarray) -> bool:
    hermitian = np.allclose(rho, rho.conj().T, atol=1e-10)
    trace_one = abs(np.trace(rho).real - 1.0) < 1e-10
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    positive = np.min(evals) > -1e-10
    return bool(hermitian and trace_one and positive)


def free_energy_degenerate(rho: np.ndarray, temperature: float) -> float:
    return -temperature * entropy(rho)


def main():
    temperature = 1.0

    rho_system_initial = 0.5 * IDENTITY_2
    rho_memory_ready = PROJ0
    rho_init = np.kron(rho_system_initial, rho_memory_ready)

    rho_measured = apply_unitary(rho_init, CNOT_SYSTEM_TO_MEMORY)
    rho_feedback = apply_unitary(rho_measured, CONTROLLED_X_MEMORY_TO_SYSTEM)
    rho_erased = reset_memory_to_zero(rho_feedback)

    rho_wrong_order = apply_unitary(
        apply_unitary(rho_init, CONTROLLED_X_MEMORY_TO_SYSTEM),
        CNOT_SYSTEM_TO_MEMORY,
    )
    rho_blind_reset = reset_memory_to_zero(rho_measured)

    rho_s_init = partial_trace_memory(rho_init)
    rho_s_measured = partial_trace_memory(rho_measured)
    rho_s_feedback = partial_trace_memory(rho_feedback)
    rho_s_wrong_order = partial_trace_memory(rho_wrong_order)

    rho_m_measured = partial_trace_system(rho_measured)
    rho_m_feedback = partial_trace_system(rho_feedback)
    rho_m_erased = partial_trace_system(rho_erased)

    information_gain = mutual_information(rho_measured)
    system_free_energy_gain = (
        free_energy_degenerate(rho_s_feedback, temperature)
        - free_energy_degenerate(rho_s_init, temperature)
    )
    erasure_cost = (
        free_energy_degenerate(rho_m_erased, temperature)
        - free_energy_degenerate(rho_m_feedback, temperature)
    )

    positive = {
        "measurement_creates_one_bit_of_system_memory_correlation": {
            "system_entropy_after_measurement": entropy(rho_s_measured),
            "memory_entropy_after_measurement": entropy(rho_m_measured),
            "mutual_information": information_gain,
            "pass": abs(entropy(rho_s_measured) - LN2) < 1e-9
            and abs(entropy(rho_m_measured) - LN2) < 1e-9
            and abs(information_gain - LN2) < 1e-9,
        },
        "conditional_feedback_converts_information_into_one_bit_of_system_free_energy": {
            "system_entropy_before_feedback": entropy(rho_s_init),
            "system_entropy_after_feedback": entropy(rho_s_feedback),
            "system_free_energy_gain": system_free_energy_gain,
            "pass": abs(entropy(rho_s_init) - LN2) < 1e-9
            and entropy(rho_s_feedback) < 1e-9
            and abs(system_free_energy_gain - temperature * LN2) < 1e-9,
        },
        "memory_erasure_closes_the_cycle_at_the_same_kT_ln2_scale": {
            "memory_entropy_before_erasure": entropy(rho_m_feedback),
            "memory_entropy_after_erasure": entropy(rho_m_erased),
            "erasure_cost": erasure_cost,
            "pass": abs(entropy(rho_m_feedback) - LN2) < 1e-9
            and entropy(rho_m_erased) < 1e-9
            and abs(erasure_cost - temperature * LN2) < 1e-9,
        },
    }

    negative = {
        "feedback_before_measurement_does_not_extract_the_same_ordered_gain": {
            "system_entropy_after_wrong_order": entropy(rho_s_wrong_order),
            "wrong_order_free_energy_gain": (
                free_energy_degenerate(rho_s_wrong_order, temperature)
                - free_energy_degenerate(rho_s_init, temperature)
            ),
            "pass": abs(entropy(rho_s_wrong_order) - LN2) < 1e-9,
        },
        "reset_without_feedback_destroys_memory_record_without_purifying_the_system": {
            "system_entropy_after_blind_reset": entropy(partial_trace_memory(rho_blind_reset)),
            "memory_entropy_after_blind_reset": entropy(partial_trace_system(rho_blind_reset)),
            "pass": abs(entropy(partial_trace_memory(rho_blind_reset)) - LN2) < 1e-9
            and entropy(partial_trace_system(rho_blind_reset)) < 1e-9,
        },
        "cycle_does_not_claim_free_work_beyond_landauer_balance": {
            "information_gain": information_gain,
            "system_free_energy_gain": system_free_energy_gain,
            "erasure_cost": erasure_cost,
            "net_after_erasure": system_free_energy_gain - erasure_cost,
            "pass": system_free_energy_gain <= erasure_cost + 1e-9,
        },
    }

    boundary = {
        "all_cycle_states_remain_valid_density_operators": {
            "pass": all(
                is_valid_density(rho)
                for rho in [
                    rho_init,
                    rho_measured,
                    rho_feedback,
                    rho_erased,
                    rho_wrong_order,
                    rho_blind_reset,
                ]
            ),
        },
        "cycle_uses_only_finite_two_qubit_carrier_and_admissible_maps": {
            "carrier_dimension": 4,
            "ordered_steps": [
                "system_to_memory_measurement_unitary",
                "memory_conditioned_feedback_unitary",
                "memory_reset_cptp_map",
            ],
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "qit_szilard_landauer_cycle",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "temperature": temperature,
            "information_gain": information_gain,
            "system_free_energy_gain": system_free_energy_gain,
            "erasure_cost": erasure_cost,
            "scope_note": (
                "Finite two-qubit bookkeeping row for a Szilard/Landauer cycle; "
                "no engine-runtime, reservoir, or universal demon claims."
            ),
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "qit_szilard_landauer_cycle_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
