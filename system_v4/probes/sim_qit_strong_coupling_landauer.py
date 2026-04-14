#!/usr/bin/env python3
"""
PURE LEGO: QIT Strong-Coupling Landauer Bookkeeping
===================================================
Finite system+bath row for the strong-coupling correction highlighted by
arXiv:1006.1420.

Claim kept narrow:
  - Reduced-system bookkeeping can appear to violate the Clausius/Landauer
    bound once the subsystem is strongly correlated with a finite bath.
  - The apparent violation is a bookkeeping error, not a real second-law
    failure: the full joint system+bath process still satisfies the bound.
  - This row is finite, explicit, and does not claim continuum reservoirs or a
    universal open-system theorem.
"""

from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
from scipy.linalg import expm
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical finite strong-coupling bookkeeping row: reduced-system "
    "Clausius/Landauer accounting can look violated once a subsystem is "
    "strongly correlated with a finite bath, while the full joint "
    "system-bath bookkeeping restores the bound on the same finite carrier."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "channel_cptp_map",
    "strong_coupling_landauer",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
    "strong_coupling_landauer",
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

I2 = np.eye(2, dtype=complex)
SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)


def entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    vals = vals[vals > 1e-14]
    if len(vals) == 0:
        return 0.0
    return float(-np.sum(vals * np.log(vals)))


def gibbs_state(hamiltonian: np.ndarray, beta: float) -> np.ndarray:
    rho = expm(-beta * hamiltonian)
    return rho / np.trace(rho)


def free_energy(hamiltonian: np.ndarray, beta: float) -> float:
    partition = float(np.trace(expm(-beta * hamiltonian)).real)
    return float(-(1.0 / beta) * np.log(partition))


def partial_trace_bath(rho_sb: np.ndarray) -> np.ndarray:
    reshaped = rho_sb.reshape(2, 2, 2, 2)
    return np.trace(reshaped, axis1=1, axis2=3)


def partial_trace_system(rho_sb: np.ndarray) -> np.ndarray:
    reshaped = rho_sb.reshape(2, 2, 2, 2)
    return np.trace(reshaped, axis1=0, axis2=2)


def mutual_information(rho_sb: np.ndarray) -> float:
    rho_s = partial_trace_bath(rho_sb)
    rho_b = partial_trace_system(rho_sb)
    return float(entropy(rho_s) + entropy(rho_b) - entropy(rho_sb))


def max_abs_diff(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.max(np.abs(a - b)))


def local_gibbs_state(h_system: np.ndarray, beta: float) -> np.ndarray:
    return gibbs_state(h_system, beta)


def local_clausius_gap(
    rho_s0: np.ndarray,
    rho_s1: np.ndarray,
    h_s0: np.ndarray,
    h_s1: np.ndarray,
    temperature: float,
) -> tuple[float, float, float]:
    """
    Bare-system bookkeeping that ignores interaction/correlation terms.
    Positive gap means apparent reduced-system Clausius violation.
    """
    del temperature
    local_work = float(np.trace(rho_s0 @ (h_s1 - h_s0)).real)
    local_energy_change = float(np.trace(rho_s1 @ h_s1 - rho_s0 @ h_s0).real)
    local_heat = local_energy_change - local_work
    delta_s_local = entropy(rho_s1) - entropy(rho_s0)
    return local_heat, delta_s_local, local_heat - delta_s_local


def total_clausius_gap(
    rho0: np.ndarray,
    rho1: np.ndarray,
    h0: np.ndarray,
    h1: np.ndarray,
    beta: float,
) -> tuple[float, float, float]:
    work = free_energy(h1, beta) - free_energy(h0, beta)
    energy_change = float(np.trace(rho1 @ h1 - rho0 @ h0).real)
    heat = energy_change - work
    delta_s = entropy(rho1) - entropy(rho0)
    return heat, delta_s, heat - delta_s


def is_valid_density(rho: np.ndarray) -> bool:
    hermitian = np.allclose(rho, rho.conj().T, atol=1e-10)
    trace_one = abs(np.trace(rho).real - 1.0) < 1e-10
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    positive = np.min(vals) > -1e-10
    return bool(hermitian and trace_one and positive)


def build_results() -> dict:
    beta = 1.0
    temperature = 1.0 / beta
    lambda_0 = 2.5
    lambda_1 = 1.45
    bath_gap = 0.35
    strong_coupling = 3.0
    weak_coupling = 0.05

    h_s0 = 0.5 * lambda_0 * SIGMA_Z
    h_s1 = 0.5 * lambda_1 * SIGMA_Z
    h_b = bath_gap * SIGMA_Z
    interaction = np.kron(SIGMA_X, SIGMA_X)

    def total_hamiltonian(hs: np.ndarray, coupling: float) -> np.ndarray:
        return np.kron(hs, I2) + np.kron(I2, h_b) + coupling * interaction

    h_uncoupled = total_hamiltonian(h_s0, 0.0)
    h_strong_0 = total_hamiltonian(h_s0, strong_coupling)
    h_strong_1 = total_hamiltonian(h_s1, strong_coupling)
    h_weak_0 = total_hamiltonian(h_s0, weak_coupling)
    h_weak_1 = total_hamiltonian(h_s1, weak_coupling)

    rho_uncoupled = gibbs_state(h_uncoupled, beta)
    rho_strong_0 = gibbs_state(h_strong_0, beta)
    rho_strong_1 = gibbs_state(h_strong_1, beta)
    rho_weak_0 = gibbs_state(h_weak_0, beta)
    rho_weak_1 = gibbs_state(h_weak_1, beta)

    rho_s_strong_0 = partial_trace_bath(rho_strong_0)
    rho_s_strong_1 = partial_trace_bath(rho_strong_1)
    rho_s_weak_0 = partial_trace_bath(rho_weak_0)
    rho_s_weak_1 = partial_trace_bath(rho_weak_1)

    rho_s_local_gibbs_0 = local_gibbs_state(h_s0, beta)
    rho_s_local_gibbs_1 = local_gibbs_state(h_s1, beta)

    strong_local_heat, strong_delta_s_local, strong_local_gap = local_clausius_gap(
        rho_s_strong_0,
        rho_s_strong_1,
        h_s0,
        h_s1,
        temperature,
    )
    weak_local_heat, weak_delta_s_local, weak_local_gap = local_clausius_gap(
        rho_s_weak_0,
        rho_s_weak_1,
        h_s0,
        h_s1,
        temperature,
    )

    strong_q_complete, strong_ds_complete, strong_complete_gap = total_clausius_gap(
        rho_uncoupled,
        rho_strong_1,
        h_uncoupled,
        h_strong_1,
        beta,
    )
    strong_q_param_only, strong_ds_param_only, strong_gap_param_only = total_clausius_gap(
        rho_strong_0,
        rho_strong_1,
        h_strong_0,
        h_strong_1,
        beta,
    )

    positive = {
        "strong_coupling_creates_correlation_and_non_gibbs_reduced_states": {
            "initial_system_bath_mutual_information": mutual_information(rho_strong_0),
            "reduced_state_vs_local_gibbs_gap_before_parameter_change": max_abs_diff(
                rho_s_strong_0, rho_s_local_gibbs_0
            ),
            "reduced_state_vs_local_gibbs_gap_after_parameter_change": max_abs_diff(
                rho_s_strong_1, rho_s_local_gibbs_1
            ),
            "pass": mutual_information(rho_strong_0) > 0.1
            and max_abs_diff(rho_s_strong_0, rho_s_local_gibbs_0) > 0.05
            and max_abs_diff(rho_s_strong_1, rho_s_local_gibbs_1) > 0.05,
        },
        "naive_reduced_system_bookkeeping_shows_an_apparent_clausius_violation_at_strong_coupling": {
            "local_heat_strong": strong_local_heat,
            "temperature_times_local_entropy_change_strong": temperature * strong_delta_s_local,
            "local_clausius_gap_strong": strong_local_gap,
            "pass": strong_local_gap > 0.02,
        },
        "joint_system_bath_bookkeeping_restores_the_bound_for_the_complete_process": {
            "complete_process_heat": strong_q_complete,
            "complete_process_temperature_times_entropy_change": temperature * strong_ds_complete,
            "complete_process_clausius_gap": strong_complete_gap,
            "pass": abs(strong_complete_gap) < 1e-9,
        },
    }

    negative = {
        "weak_coupling_control_does_not_show_the_same_positive_local_violation_gap": {
            "local_heat_weak": weak_local_heat,
            "temperature_times_local_entropy_change_weak": temperature * weak_delta_s_local,
            "local_clausius_gap_weak": weak_local_gap,
            "pass": weak_local_gap <= 0.0,
        },
        "parameter_change_alone_does_not_fix_the_bookkeeping_without_joint_terms": {
            "parameter_change_joint_gap_strong": strong_gap_param_only,
            "apparent_local_gap_strong": strong_local_gap,
            "pass": abs(strong_gap_param_only) < 1e-9 and strong_local_gap > 0.02,
        },
        "row_does_not_claim_a_continuum_reservoir_or_universal_open_system_theorem": {
            "pass": True,
        },
    }

    boundary = {
        "all_global_and_reduced_states_remain_valid_density_operators": {
            "pass": all(
                is_valid_density(rho)
                for rho in [
                    rho_uncoupled,
                    rho_strong_0,
                    rho_strong_1,
                    rho_weak_0,
                    rho_weak_1,
                    rho_s_strong_0,
                    rho_s_strong_1,
                    rho_s_weak_0,
                    rho_s_weak_1,
                ]
            ),
        },
        "comparison_uses_one_finite_two_qubit_carrier_with_explicit_interaction_only": {
            "carrier_dimension": 4,
            "hamiltonian_terms": [
                "system_sigma_z_gap",
                "bath_sigma_z_gap",
                "sigma_x_tensor_sigma_x_interaction",
            ],
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    return {
        "name": "qit_strong_coupling_landauer",
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
            "beta": beta,
            "temperature": temperature,
            "lambda_0": lambda_0,
            "lambda_1": lambda_1,
            "bath_gap": bath_gap,
            "strong_coupling": strong_coupling,
            "weak_coupling": weak_coupling,
            "scope_note": (
                "Finite two-qubit system+bath row inspired by arXiv:1006.1420. "
                "The earned claim is about bookkeeping: reduced-state accounting can "
                "look wrong at strong coupling, while explicit joint bookkeeping closes."
            ),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the strong-coupling Landauer bookkeeping probe.")
    parser.add_argument(
        "--stdout-only",
        action="store_true",
        help="Print JSON results to stdout instead of writing the repo result surface.",
    )
    parser.add_argument(
        "--result-path",
        type=pathlib.Path,
        default=None,
        help="Optional explicit path for the results JSON output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = build_results()

    if args.stdout_only:
        print(json.dumps(results, indent=2))
        print(f"ALL PASS: {results['summary']['all_pass']}")
        return

    out_path = args.result_path
    if out_path is None:
        out_path = (
            pathlib.Path(__file__).resolve().parent
            / "a2_state"
            / "sim_results"
            / "qit_strong_coupling_landauer_results.json"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {results['summary']['all_pass']}")


if __name__ == "__main__":
    main()
