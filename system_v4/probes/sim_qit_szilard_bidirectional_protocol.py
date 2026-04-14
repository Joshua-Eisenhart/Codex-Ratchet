#!/usr/bin/env python3
"""
Deep Szilard protocol lane: explicit forward and reverse bookkeeping on a
bounded system-memory carrier, with ideal and noisy substep sweeps.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


LN2 = float(np.log(2.0))
EPS = 1e-10

CLASSIFICATION = "exploratory_signal"
CLASSIFICATION_NOTE = (
    "Deep operational Szilard/Landauer probe on a finite two-qubit carrier. "
    "It expands the narrow canonical row into explicit forward and reverse "
    "substep bookkeeping, plus inductive sweeps over measurement, feedback, "
    "and erasure/randomization imperfections. It is still a bounded information-"
    "thermodynamics lane, not a reservoir-runtime or universal demon claim."
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
IDENTITY_4 = np.eye(4, dtype=complex)

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

X_MEMORY = np.kron(IDENTITY_2, np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex))


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


def apply_unitary(rho: np.ndarray, unitary: np.ndarray) -> np.ndarray:
    return unitary @ rho @ unitary.conj().T


def trace_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho - sigma + (rho - sigma).conj().T) / 2)
    return float(0.5 * np.sum(np.abs(vals)))


def is_valid_density(rho: np.ndarray) -> bool:
    hermitian = np.allclose(rho, rho.conj().T, atol=1e-10)
    trace_one = abs(np.trace(rho).real - 1.0) < 1e-10
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    positive = np.min(evals) > -1e-10
    return bool(hermitian and trace_one and positive)


def free_energy_degenerate(rho: np.ndarray, temperature: float) -> float:
    return -temperature * entropy(rho)


def memory_flip_channel(rho: np.ndarray, error: float) -> np.ndarray:
    if error <= 0.0:
        return rho
    return (1.0 - error) * rho + error * apply_unitary(rho, X_MEMORY)


def imperfect_controlled_x(rho: np.ndarray, error: float) -> np.ndarray:
    if error <= 0.0:
        return apply_unitary(rho, CONTROLLED_X_MEMORY_TO_SYSTEM)
    return (1.0 - error) * apply_unitary(rho, CONTROLLED_X_MEMORY_TO_SYSTEM) + error * rho


def reset_memory_to_zero(rho_sm: np.ndarray, strength: float) -> np.ndarray:
    rho_s = partial_trace_memory(rho_sm)
    reset = np.kron(rho_s, PROJ0)
    return (1.0 - strength) * rho_sm + strength * reset


def randomize_memory(rho_sm: np.ndarray, strength: float) -> np.ndarray:
    rho_s = partial_trace_memory(rho_sm)
    randomized = np.kron(rho_s, 0.5 * IDENTITY_2)
    return (1.0 - strength) * rho_sm + strength * randomized


def make_initial_state() -> np.ndarray:
    rho_system_initial = 0.5 * IDENTITY_2
    rho_memory_ready = PROJ0
    return np.kron(rho_system_initial, rho_memory_ready)


def make_ground_state() -> np.ndarray:
    return np.kron(PROJ0, PROJ0)


def state_snapshot(rho_sm: np.ndarray, temperature: float) -> dict:
    rho_s = partial_trace_memory(rho_sm)
    rho_m = partial_trace_system(rho_sm)
    return {
        "system_entropy": entropy(rho_s),
        "memory_entropy": entropy(rho_m),
        "joint_entropy": entropy(rho_sm),
        "mutual_information": mutual_information(rho_sm),
        "system_free_energy": free_energy_degenerate(rho_s, temperature),
        "memory_free_energy": free_energy_degenerate(rho_m, temperature),
        "valid_density": is_valid_density(rho_sm),
    }


def run_forward_cycle(
    temperature: float,
    measurement_error: float = 0.0,
    feedback_error: float = 0.0,
    erasure_strength: float = 1.0,
) -> dict:
    rho_init = make_initial_state()
    rho_measured = memory_flip_channel(
        apply_unitary(rho_init, CNOT_SYSTEM_TO_MEMORY),
        measurement_error,
    )
    rho_feedback = imperfect_controlled_x(rho_measured, feedback_error)
    rho_erased = reset_memory_to_zero(rho_feedback, erasure_strength)
    rho_wrong_order = memory_flip_channel(
        apply_unitary(imperfect_controlled_x(rho_init, feedback_error), CNOT_SYSTEM_TO_MEMORY),
        measurement_error,
    )

    init_snapshot = state_snapshot(rho_init, temperature)
    measured_snapshot = state_snapshot(rho_measured, temperature)
    feedback_snapshot = state_snapshot(rho_feedback, temperature)
    erased_snapshot = state_snapshot(rho_erased, temperature)
    wrong_order_snapshot = state_snapshot(rho_wrong_order, temperature)

    system_gain = feedback_snapshot["system_free_energy"] - init_snapshot["system_free_energy"]
    erasure_cost = erased_snapshot["memory_free_energy"] - feedback_snapshot["memory_free_energy"]
    net_balance = system_gain - erasure_cost

    return {
        "temperature": temperature,
        "parameters": {
            "measurement_error": measurement_error,
            "feedback_error": feedback_error,
            "erasure_strength": erasure_strength,
        },
        "states": {
            "initial": init_snapshot,
            "measured": measured_snapshot,
            "feedback": feedback_snapshot,
            "erased": erased_snapshot,
            "wrong_order": wrong_order_snapshot,
        },
        "metrics": {
            "system_free_energy_gain": system_gain,
            "erasure_cost": erasure_cost,
            "net_after_erasure": net_balance,
            "reconstruction_trace_distance_from_ground": trace_distance(
                rho_erased, make_ground_state()
            ),
        },
    }


def run_reverse_cycle(
    temperature: float,
    randomization_strength: float = 1.0,
    anti_feedback_error: float = 0.0,
    anti_measurement_error: float = 0.0,
) -> dict:
    rho_start = make_ground_state()
    rho_randomized = randomize_memory(rho_start, randomization_strength)
    rho_after_anti_feedback = imperfect_controlled_x(rho_randomized, anti_feedback_error)
    rho_restored = memory_flip_channel(
        apply_unitary(rho_after_anti_feedback, CNOT_SYSTEM_TO_MEMORY),
        anti_measurement_error,
    )
    rho_no_randomization = memory_flip_channel(
        apply_unitary(imperfect_controlled_x(rho_start, anti_feedback_error), CNOT_SYSTEM_TO_MEMORY),
        anti_measurement_error,
    )

    start_snapshot = state_snapshot(rho_start, temperature)
    randomized_snapshot = state_snapshot(rho_randomized, temperature)
    anti_feedback_snapshot = state_snapshot(rho_after_anti_feedback, temperature)
    restored_snapshot = state_snapshot(rho_restored, temperature)
    no_randomization_snapshot = state_snapshot(rho_no_randomization, temperature)
    target_snapshot = state_snapshot(make_initial_state(), temperature)

    randomization_cost = randomized_snapshot["memory_free_energy"] - start_snapshot["memory_free_energy"]
    system_free_energy_drop = (
        restored_snapshot["system_free_energy"] - start_snapshot["system_free_energy"]
    )

    return {
        "temperature": temperature,
        "parameters": {
            "randomization_strength": randomization_strength,
            "anti_feedback_error": anti_feedback_error,
            "anti_measurement_error": anti_measurement_error,
        },
        "states": {
            "start_ground": start_snapshot,
            "randomized": randomized_snapshot,
            "after_anti_feedback": anti_feedback_snapshot,
            "restored_initial": restored_snapshot,
            "no_randomization_control": no_randomization_snapshot,
            "target_initial_state": target_snapshot,
        },
        "metrics": {
            "randomization_cost": randomization_cost,
            "system_free_energy_drop": system_free_energy_drop,
            "restoration_trace_distance": trace_distance(rho_restored, make_initial_state()),
            "no_randomization_trace_distance": trace_distance(
                rho_no_randomization, make_initial_state()
            ),
        },
    }


def build_sweep_grid(temperature: float) -> list[dict]:
    sweep = []
    for meas_err in (0.0, 0.1, 0.2, 0.3):
        for fb_err in (0.0, 0.1, 0.2, 0.3):
            forward = run_forward_cycle(
                temperature=temperature,
                measurement_error=meas_err,
                feedback_error=fb_err,
                erasure_strength=1.0,
            )
            reverse = run_reverse_cycle(
                temperature=temperature,
                randomization_strength=1.0,
                anti_feedback_error=fb_err,
                anti_measurement_error=meas_err,
            )
            sweep.append(
                {
                    "measurement_error": meas_err,
                    "feedback_error": fb_err,
                    "forward_information_gain": forward["states"]["measured"]["mutual_information"],
                    "forward_system_gain": forward["metrics"]["system_free_energy_gain"],
                    "forward_net_after_erasure": forward["metrics"]["net_after_erasure"],
                    "reverse_randomization_cost": reverse["metrics"]["randomization_cost"],
                    "reverse_restoration_trace_distance": reverse["metrics"]["restoration_trace_distance"],
                }
            )
    return sweep


def main() -> None:
    temperature = 1.0

    forward_ideal = run_forward_cycle(temperature)
    reverse_ideal = run_reverse_cycle(temperature)
    forward_blind = run_forward_cycle(
        temperature,
        measurement_error=0.25,
        feedback_error=0.25,
        erasure_strength=1.0,
    )
    sweep = build_sweep_grid(temperature)

    positive = {
        "forward_measurement_creates_one_bit_of_correlation_in_the_ideal_limit": {
            "mutual_information": forward_ideal["states"]["measured"]["mutual_information"],
            "pass": abs(forward_ideal["states"]["measured"]["mutual_information"] - LN2) < 1e-9,
        },
        "forward_feedback_purifies_the_system_in_the_ideal_limit": {
            "system_entropy_after_feedback": forward_ideal["states"]["feedback"]["system_entropy"],
            "system_free_energy_gain": forward_ideal["metrics"]["system_free_energy_gain"],
            "pass": (
                forward_ideal["states"]["feedback"]["system_entropy"] < 1e-9
                and abs(forward_ideal["metrics"]["system_free_energy_gain"] - LN2) < 1e-9
            ),
        },
        "reverse_protocol_restores_the_initial_mixed_system_in_the_ideal_limit": {
            "restoration_trace_distance": reverse_ideal["metrics"]["restoration_trace_distance"],
            "restored_system_entropy": reverse_ideal["states"]["restored_initial"]["system_entropy"],
            "pass": (
                reverse_ideal["metrics"]["restoration_trace_distance"] < 1e-9
                and abs(reverse_ideal["states"]["restored_initial"]["system_entropy"] - LN2) < 1e-9
            ),
        },
        "forward_and_reverse_bookkeeping_close_at_the_same_kT_ln2_scale_in_the_ideal_limit": {
            "forward_erasure_cost": forward_ideal["metrics"]["erasure_cost"],
            "reverse_randomization_cost": reverse_ideal["metrics"]["randomization_cost"],
            "pass": (
                abs(forward_ideal["metrics"]["erasure_cost"] - LN2) < 1e-9
                and abs(abs(reverse_ideal["metrics"]["randomization_cost"]) - LN2) < 1e-9
            ),
        },
    }

    negative = {
        "forward_wrong_order_does_not_recover_the_same_gain": {
            "wrong_order_system_entropy": forward_ideal["states"]["wrong_order"]["system_entropy"],
            "pass": abs(forward_ideal["states"]["wrong_order"]["system_entropy"] - LN2) < 1e-9,
        },
        "reverse_without_randomization_does_not_restore_the_initial_state": {
            "no_randomization_trace_distance": reverse_ideal["metrics"]["no_randomization_trace_distance"],
            "pass": reverse_ideal["metrics"]["no_randomization_trace_distance"] > 0.25,
        },
        "noise_degrades_forward_gain_and_reverse_restoration": {
            "ideal_forward_gain": forward_ideal["metrics"]["system_free_energy_gain"],
            "noisy_forward_gain": forward_blind["metrics"]["system_free_energy_gain"],
            "ideal_reverse_trace_distance": reverse_ideal["metrics"]["restoration_trace_distance"],
            "noisy_reverse_trace_distance": run_reverse_cycle(
                temperature,
                randomization_strength=1.0,
                anti_feedback_error=0.25,
                anti_measurement_error=0.25,
            )["metrics"]["restoration_trace_distance"],
            "pass": (
                forward_blind["metrics"]["system_free_energy_gain"]
                < forward_ideal["metrics"]["system_free_energy_gain"] - 0.05
                and run_reverse_cycle(
                    temperature,
                    randomization_strength=1.0,
                    anti_feedback_error=0.25,
                    anti_measurement_error=0.25,
                )["metrics"]["restoration_trace_distance"]
                > reverse_ideal["metrics"]["restoration_trace_distance"] + 0.05
            ),
        },
    }

    boundary = {
        "all_ideal_forward_and_reverse_states_remain_valid_density_operators": {
            "pass": all(
                snapshot["valid_density"]
                for cycle in (forward_ideal, reverse_ideal)
                for snapshot in cycle["states"].values()
            ),
        },
        "parameter_sweep_covers_bidirectional_noise_grid": {
            "n_points": len(sweep),
            "measurement_error_values": [0.0, 0.1, 0.2, 0.3],
            "feedback_error_values": [0.0, 0.1, 0.2, 0.3],
            "pass": len(sweep) == 16,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "qit_szilard_bidirectional_protocol",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "ideal_forward": forward_ideal,
        "ideal_reverse": reverse_ideal,
        "error_sweep": sweep,
        "summary": {
            "all_pass": all_pass,
            "temperature": temperature,
            "ideal_forward_information_gain": forward_ideal["states"]["measured"]["mutual_information"],
            "ideal_forward_system_gain": forward_ideal["metrics"]["system_free_energy_gain"],
            "ideal_forward_erasure_cost": forward_ideal["metrics"]["erasure_cost"],
            "ideal_reverse_randomization_cost": reverse_ideal["metrics"]["randomization_cost"],
            "ideal_reverse_restoration_trace_distance": reverse_ideal["metrics"]["restoration_trace_distance"],
            "scope_note": (
                "Finite two-qubit forward/reverse Szilard bookkeeping lane with explicit "
                "substep mechanics and noise sweeps; still no reservoir-runtime or universal "
                "demon claim."
            ),
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "qit_szilard_bidirectional_protocol_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
