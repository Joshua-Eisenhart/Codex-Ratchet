#!/usr/bin/env python3
"""
PURE LEGO: QIT Predictive World Model
=====================================
Finite predictive-world-model row on a single qubit carrier.

Claim kept narrow:
  - An internal density-state model can reduce prediction error against a finite
    environment when it updates on an adequate probe set.
  - The same update loop can re-adapt after an environment shift.
  - Limited or absent observation controls do not recover the same full-state
    alignment.
"""

from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical finite predictive-world-model row: an internal qubit density "
    "state updated from noncommuting probe errors reduces full-state mismatch "
    "to a finite environment and re-adapts after a shift, while limited or "
    "absent observation controls fail to recover the same alignment."
)

LEGO_IDS = [
    "predictive_world_model",
    "channel_cptp_map",
]

PRIMARY_LEGO_IDS = [
    "predictive_world_model",
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

SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SIGMA_Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
I2 = np.eye(2, dtype=complex)


def density_from_bloch(vector: np.ndarray) -> np.ndarray:
    vx, vy, vz = np.asarray(vector, dtype=float)
    rho = 0.5 * (I2 + vx * SIGMA_X + vy * SIGMA_Y + vz * SIGMA_Z)
    return ensure_valid_density(rho)


def bloch_from_density(rho: np.ndarray) -> np.ndarray:
    return np.array(
        [
            np.trace(rho @ SIGMA_X).real,
            np.trace(rho @ SIGMA_Y).real,
            np.trace(rho @ SIGMA_Z).real,
        ],
        dtype=float,
    )


def ensure_valid_density(rho: np.ndarray) -> np.ndarray:
    hermitian = 0.5 * (rho + rho.conj().T)
    vals, vecs = np.linalg.eigh(hermitian)
    vals = np.maximum(vals, 0.0)
    if vals.sum() <= 0:
        return I2 / 2.0
    fixed = vecs @ np.diag(vals.astype(complex)) @ vecs.conj().T
    return fixed / np.trace(fixed)


def trace_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    diff = 0.5 * ((rho - sigma) + (rho - sigma).conj().T)
    vals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(vals)))


def relative_entropy(rho: np.ndarray, sigma: np.ndarray) -> float:
    vals_r, vecs_r = np.linalg.eigh(0.5 * (rho + rho.conj().T))
    vals_s, vecs_s = np.linalg.eigh(0.5 * (sigma + sigma.conj().T))
    vals_r = np.maximum(vals_r, 1e-12)
    vals_s = np.maximum(vals_s, 1e-12)
    log_r = vecs_r @ np.diag(np.log(vals_r).astype(complex)) @ vecs_r.conj().T
    log_s = vecs_s @ np.diag(np.log(vals_s).astype(complex)) @ vecs_s.conj().T
    return float(np.trace(rho @ (log_r - log_s)).real)


def predictive_update(
    rho_model: np.ndarray,
    rho_env: np.ndarray,
    *,
    eta: float,
    probe_ops: list[np.ndarray],
) -> np.ndarray:
    delta = np.zeros((2, 2), dtype=complex)
    for op in probe_ops:
        error = np.trace(rho_env @ op).real - np.trace(rho_model @ op).real
        delta = delta + 0.5 * error * op
    return ensure_valid_density(rho_model + eta * delta)


def run_update_loop(
    rho_init: np.ndarray,
    rho_env: np.ndarray,
    *,
    rounds: int,
    eta: float,
    probe_ops: list[np.ndarray],
) -> dict:
    rho = rho_init.copy()
    trace_history = [trace_distance(rho, rho_env)]
    relent_history = [relative_entropy(rho, rho_env)]

    for _ in range(rounds):
        rho = predictive_update(rho, rho_env, eta=eta, probe_ops=probe_ops)
        trace_history.append(trace_distance(rho, rho_env))
        relent_history.append(relative_entropy(rho, rho_env))

    return {
        "rho_final": rho,
        "trace_history": trace_history,
        "relative_entropy_history": relent_history,
    }


def build_results() -> dict:
    rho_env_0 = density_from_bloch(np.array([0.52, -0.28, 0.31]))
    rho_env_1 = density_from_bloch(np.array([-0.33, 0.46, 0.24]))
    rho_model_0 = density_from_bloch(np.array([-0.18, 0.12, -0.26]))

    full_probe_ops = [SIGMA_X, SIGMA_Y, SIGMA_Z]
    z_only_probe_ops = [SIGMA_Z]

    rounds_pre = 9
    rounds_post = 11
    eta = 0.32

    pre_full = run_update_loop(
        rho_model_0,
        rho_env_0,
        rounds=rounds_pre,
        eta=eta,
        probe_ops=full_probe_ops,
    )
    rho_model_pre = pre_full["rho_final"]

    post_full = run_update_loop(
        rho_model_pre,
        rho_env_1,
        rounds=rounds_post,
        eta=eta,
        probe_ops=full_probe_ops,
    )

    post_frozen = {
        "rho_final": rho_model_pre.copy(),
        "trace_history": [trace_distance(rho_model_pre, rho_env_1)] * (rounds_post + 1),
        "relative_entropy_history": [relative_entropy(rho_model_pre, rho_env_1)] * (rounds_post + 1),
    }
    post_z_only = run_update_loop(
        rho_model_pre,
        rho_env_1,
        rounds=rounds_post,
        eta=eta,
        probe_ops=z_only_probe_ops,
    )
    post_stale_target = run_update_loop(
        rho_model_pre,
        rho_env_0,
        rounds=rounds_post,
        eta=eta,
        probe_ops=full_probe_ops,
    )

    model_obs_pre = bloch_from_density(rho_model_pre)
    env_obs_1 = bloch_from_density(rho_env_1)
    full_final = post_full["rho_final"]
    z_only_final = post_z_only["rho_final"]

    positive = {
        "full_probe_predictive_updates_reduce_pre_shift_model_error": {
            "initial_trace_distance": pre_full["trace_history"][0],
            "final_trace_distance": pre_full["trace_history"][-1],
            "initial_relative_entropy": pre_full["relative_entropy_history"][0],
            "final_relative_entropy": pre_full["relative_entropy_history"][-1],
            "pass": bool(pre_full["trace_history"][-1] < 0.35 * pre_full["trace_history"][0]
            and pre_full["relative_entropy_history"][-1] < 0.2 * pre_full["relative_entropy_history"][0],
            ),
        },
        "full_probe_model_re_adapts_after_environment_shift": {
            "trace_distance_immediately_after_shift": post_full["trace_history"][0],
            "trace_distance_after_readaptation": post_full["trace_history"][-1],
            "relative_entropy_immediately_after_shift": post_full["relative_entropy_history"][0],
            "relative_entropy_after_readaptation": post_full["relative_entropy_history"][-1],
            "pass": bool(post_full["trace_history"][-1] < 0.45 * post_full["trace_history"][0]
            and post_full["relative_entropy_history"][-1] < 0.25 * post_full["relative_entropy_history"][0],
            ),
        },
        "full_noncommuting_probe_set_recovers_observables_better_than_partial_probe_control": {
            "environment_observables_after_shift": env_obs_1.tolist(),
            "full_probe_final_observables": bloch_from_density(full_final).tolist(),
            "z_only_final_observables": bloch_from_density(z_only_final).tolist(),
            "full_probe_observable_error": float(np.linalg.norm(bloch_from_density(full_final) - env_obs_1)),
            "z_only_observable_error": float(np.linalg.norm(bloch_from_density(z_only_final) - env_obs_1)),
            "pass": bool(
                np.linalg.norm(bloch_from_density(full_final) - env_obs_1)
                < 0.55 * np.linalg.norm(bloch_from_density(z_only_final) - env_obs_1)
            ),
        },
    }

    negative = {
        "frozen_model_without_observation_does_not_recover_after_shift": {
            "frozen_trace_distance": post_frozen["trace_history"][-1],
            "adaptive_trace_distance": post_full["trace_history"][-1],
            "pass": bool(post_frozen["trace_history"][-1] > 1.8 * post_full["trace_history"][-1]),
        },
        "tracking_the_stale_pre_shift_target_does_not_match_the_new_environment": {
            "stale_target_trace_distance_to_new_env": trace_distance(post_stale_target["rho_final"], rho_env_1),
            "adaptive_trace_distance_to_new_env": post_full["trace_history"][-1],
            "pass": bool(
                trace_distance(post_stale_target["rho_final"], rho_env_1)
                > 1.8 * post_full["trace_history"][-1]
            ),
        },
        "row_does_not_claim_general_agency_or_alignment_solution": {
            "pass": True,
        },
    }

    boundary = {
        "all_world_model_states_remain_valid_density_operators": {
            "pass": bool(all(
                np.min(np.linalg.eigvalsh(rho)) > -1e-10 and abs(np.trace(rho).real - 1.0) < 1e-10
                for rho in [
                    rho_env_0,
                    rho_env_1,
                    rho_model_0,
                    rho_model_pre,
                    full_final,
                    z_only_final,
                    post_stale_target["rho_final"],
                ]
            )),
        },
        "comparison_uses_one_finite_qubit_carrier_and_explicit_probe_updates_only": {
            "carrier_dimension": 2,
            "full_probe_set": ["sigma_x", "sigma_y", "sigma_z"],
            "partial_probe_control": ["sigma_z"],
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    return {
        "name": "qit_predictive_world_model",
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
            "pre_shift_final_trace_distance": pre_full["trace_history"][-1],
            "post_shift_final_trace_distance": post_full["trace_history"][-1],
            "frozen_post_shift_trace_distance": post_frozen["trace_history"][-1],
            "scope_note": (
                "Finite predictive-world-model row only. It shows bounded probe-driven "
                "state estimation and re-adaptation on a qubit carrier, not a general "
                "world-engine or alignment theorem."
            ),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the QIT predictive world-model probe.")
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
            / "qit_predictive_world_model_results.json"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {results['summary']['all_pass']}")


if __name__ == "__main__":
    main()
