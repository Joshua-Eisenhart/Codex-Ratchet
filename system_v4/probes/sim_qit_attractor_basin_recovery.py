#!/usr/bin/env python3
"""
PURE LEGO: QIT Attractor Basin Recovery
=======================================
Finite density-operator row for order-sensitive recovery toward a persistent
 probe-equivalence class under noncommuting channels.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical finite-channel row for QIT-aligned attractor-basin recovery: bounded perturbations "
    "of nearby density states return under one ordered noncommuting schedule to the same persistent "
    "equivalence class, while the swapped order is weaker and a commuting control loses the order effect."
)

LEGO_IDS = [
    "channel_cptp_map",
    "viability_vs_attractor",
]

PRIMARY_LEGO_IDS = [
    "channel_cptp_map",
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

SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
HADAMARD = (1.0 / np.sqrt(2.0)) * np.array([[1, 1], [1, -1]], dtype=complex)


def amplitude_damping(rho: np.ndarray, gamma: float) -> np.ndarray:
    k0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    k1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    return k0 @ rho @ k0.conj().T + k1 @ rho @ k1.conj().T


def z_dephasing(rho: np.ndarray, lam: float) -> np.ndarray:
    k0 = np.array([[1, 0], [0, np.sqrt(1 - lam)]], dtype=complex)
    k1 = np.array([[0, 0], [0, np.sqrt(lam)]], dtype=complex)
    return k0 @ rho @ k0.conj().T + k1 @ rho @ k1.conj().T


def x_dephasing(rho: np.ndarray, lam: float) -> np.ndarray:
    rotated = HADAMARD @ rho @ HADAMARD
    return HADAMARD @ z_dephasing(rotated, lam) @ HADAMARD


def z_rotation(rho: np.ndarray, theta: float) -> np.ndarray:
    u = np.cos(theta / 2.0) * np.eye(2, dtype=complex) - 1j * np.sin(theta / 2.0) * SIGMA_Z
    return u @ rho @ u.conj().T


def trace_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    diff = 0.5 * ((rho - sigma) + (rho - sigma).conj().T)
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))


def coherence_magnitude(rho: np.ndarray) -> float:
    return float(abs(rho[0, 1]))


def excited_population(rho: np.ndarray) -> float:
    return float(np.real(rho[1, 1]))


def z_bias(rho: np.ndarray) -> float:
    return float(np.real(np.trace(SIGMA_Z @ rho)))


def equivalence_class_metrics(rho: np.ndarray) -> dict:
    return {
        "excited_population": excited_population(rho),
        "coherence_magnitude": coherence_magnitude(rho),
        "z_bias": z_bias(rho),
    }


def in_recovery_class(rho: np.ndarray) -> bool:
    metrics = equivalence_class_metrics(rho)
    return (
        metrics["excited_population"] < 0.2
        and metrics["coherence_magnitude"] < 0.02
        and metrics["z_bias"] > 0.6
    )


def is_valid_density(rho: np.ndarray) -> bool:
    hermitian = np.allclose(rho, rho.conj().T, atol=1e-10)
    trace_one = abs(np.trace(rho).real - 1.0) < 1e-10
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    positive = np.min(evals) > -1e-10
    return bool(hermitian and trace_one and positive)


def rollout(rho0: np.ndarray, schedule, rounds: int) -> list[np.ndarray]:
    states = [rho0.copy()]
    rho = rho0.copy()
    for _ in range(rounds):
        for channel in schedule:
            rho = channel(rho)
        states.append(rho)
    return states


def first_entry_round(states: list[np.ndarray]) -> int | None:
    for idx, rho in enumerate(states):
        if in_recovery_class(rho):
            return idx
    return None


def commuting_gap(witness: np.ndarray) -> float:
    left = amplitude_damping(amplitude_damping(witness, 0.3), 0.15)
    right = amplitude_damping(amplitude_damping(witness, 0.15), 0.3)
    return trace_distance(left, right)


def main():
    target_pole = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    plus_state = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)

    perturbed_a = 0.88 * target_pole + 0.12 * plus_state
    perturbed_b = 0.78 * target_pole + 0.22 * np.array(
        [[0.25, 0.12], [0.12, 0.75]],
        dtype=complex,
    )
    witness = np.array([[0.55, 0.32], [0.32, 0.45]], dtype=complex)

    chosen_schedule = [
        lambda rho: x_dephasing(rho, 0.35),
        lambda rho: amplitude_damping(rho, 0.30),
    ]
    swapped_schedule = [
        lambda rho: amplitude_damping(rho, 0.30),
        lambda rho: x_dephasing(rho, 0.35),
    ]
    mismatched_schedule = [
        lambda rho: x_dephasing(rho, 0.20),
        lambda rho: z_rotation(rho, np.pi / 3.0),
    ]

    chosen_a = rollout(perturbed_a, chosen_schedule, rounds=8)
    chosen_b = rollout(perturbed_b, chosen_schedule, rounds=8)
    swapped_a = rollout(perturbed_a, swapped_schedule, rounds=8)
    swapped_b = rollout(perturbed_b, swapped_schedule, rounds=8)
    mismatched_a = rollout(perturbed_a, mismatched_schedule, rounds=8)
    mismatched_b = rollout(perturbed_b, mismatched_schedule, rounds=8)

    chosen_terminal_a = chosen_a[-1]
    chosen_terminal_b = chosen_b[-1]
    swapped_terminal_a = swapped_a[-1]
    swapped_terminal_b = swapped_b[-1]
    mismatched_terminal_a = mismatched_a[-1]
    mismatched_terminal_b = mismatched_b[-1]

    chosen_mean_distance = np.mean(
        [trace_distance(chosen_terminal_a, target_pole), trace_distance(chosen_terminal_b, target_pole)]
    )
    swapped_mean_distance = np.mean(
        [trace_distance(swapped_terminal_a, target_pole), trace_distance(swapped_terminal_b, target_pole)]
    )

    one_cycle_order_gap = trace_distance(
        chosen_schedule[1](chosen_schedule[0](witness)),
        swapped_schedule[1](swapped_schedule[0](witness)),
    )
    comm_gap = commuting_gap(witness)

    positive = {
        "nearby_perturbations_return_to_the_same_recovery_class": {
            "state_a_entry_round": first_entry_round(chosen_a),
            "state_b_entry_round": first_entry_round(chosen_b),
            "state_a_terminal_metrics": equivalence_class_metrics(chosen_terminal_a),
            "state_b_terminal_metrics": equivalence_class_metrics(chosen_terminal_b),
            "terminal_trace_gap": trace_distance(chosen_terminal_a, chosen_terminal_b),
            "pass": in_recovery_class(chosen_terminal_a)
            and in_recovery_class(chosen_terminal_b)
            and trace_distance(chosen_terminal_a, chosen_terminal_b) > 1e-4,
        },
        "chosen_order_beats_the_swapped_order_on_class_return": {
            "chosen_mean_distance_to_pole": chosen_mean_distance,
            "swapped_mean_distance_to_pole": swapped_mean_distance,
            "one_cycle_order_gap": one_cycle_order_gap,
            "chosen_class_hits": int(in_recovery_class(chosen_terminal_a)) + int(in_recovery_class(chosen_terminal_b)),
            "swapped_class_hits": int(in_recovery_class(swapped_terminal_a)) + int(in_recovery_class(swapped_terminal_b)),
            "pass": chosen_mean_distance + 0.03 < swapped_mean_distance
            and one_cycle_order_gap > 1e-3
            and (int(in_recovery_class(chosen_terminal_a)) + int(in_recovery_class(chosen_terminal_b)))
            > (int(in_recovery_class(swapped_terminal_a)) + int(in_recovery_class(swapped_terminal_b))),
        },
    }

    negative = {
        "commuting_control_schedule_loses_the_order_effect": {
            "commuting_order_gap": comm_gap,
            "pass": comm_gap < 1e-10,
        },
        "mismatched_schedule_does_not_recover_the_same_class": {
            "state_a_terminal_metrics": equivalence_class_metrics(mismatched_terminal_a),
            "state_b_terminal_metrics": equivalence_class_metrics(mismatched_terminal_b),
            "class_hits": int(in_recovery_class(mismatched_terminal_a)) + int(in_recovery_class(mismatched_terminal_b)),
            "pass": not in_recovery_class(mismatched_terminal_a) and not in_recovery_class(mismatched_terminal_b),
        },
    }

    boundary = {
        "all_states_remain_valid_density_operators": {
            "pass": all(
                is_valid_density(rho)
                for rho in [
                    perturbed_a,
                    perturbed_b,
                    witness,
                    *chosen_a,
                    *chosen_b,
                    *swapped_a,
                    *swapped_b,
                    *mismatched_a,
                    *mismatched_b,
                ]
            ),
        },
        "claim_is_equivalence_class_recovery_not_exact_point_identity": {
            "target_class_rule": {
                "excited_population_lt": 0.2,
                "coherence_magnitude_lt": 0.02,
                "z_bias_gt": 0.6,
            },
            "terminal_gap": trace_distance(chosen_terminal_a, chosen_terminal_b),
            "pass": trace_distance(chosen_terminal_a, chosen_terminal_b) > 1e-4,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "qit_attractor_basin_recovery",
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
            "chosen_schedule": ["x_dephasing(0.35)", "amplitude_damping(0.30)"],
            "swapped_schedule": ["amplitude_damping(0.30)", "x_dephasing(0.35)"],
            "mismatched_schedule": ["x_dephasing(0.20)", "z_rotation(pi/3)"],
            "scope_note": (
                "Finite qubit row showing recovery to a persistent class under an ordered "
                "noncommuting schedule; no engine-runtime or universal basin taxonomy claims."
            ),
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "qit_attractor_basin_recovery_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
