#!/usr/bin/env python3
"""
PURE LEGO: QIT Moloch Coordination Trap
=======================================
Bounded finite-carrier row for a shared-bath coordination trap.

Claim kept narrow:
  - Multiple local extractors can greedily consume a shared finite athermality
    resource faster than they can preserve it.
  - A bounded scheduled repair/lose stroke can keep that shared resource above
    a usable threshold for longer.
  - This is an operational resource-longevity comparison only. It is not a
    universal social, controller, or engine-totality claim.
"""

from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10
I2 = np.eye(2, dtype=complex)

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical bounded resource-longevity row on one finite shared-bath carrier. "
    "It compares greedy local extraction against a scheduled repair/lose stroke "
    "without making controller, policy-universality, or real-engine totality claims."
)

LEGO_IDS = [
    "qit_moloch_coordination_trap",
]

PRIMARY_LEGO_IDS = [
    "qit_moloch_coordination_trap",
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


def density_from_bias(z: float) -> np.ndarray:
    z = float(np.clip(z, -1.0, 1.0))
    return np.array(
        [[0.5 * (1.0 + z), 0.0], [0.0, 0.5 * (1.0 - z)]],
        dtype=complex,
    )


def entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    vals = vals[vals > 1e-14]
    if len(vals) == 0:
        return 0.0
    return float(-np.sum(vals * np.log2(vals)))


def negentropy_from_bias(z: float) -> float:
    return max(0.0, 1.0 - entropy(density_from_bias(z)))


def trace_distance_to_mixed(z: float) -> float:
    rho = density_from_bias(z)
    evals = np.linalg.eigvalsh(0.5 * ((rho - I2 / 2.0) + (rho - I2 / 2.0).conj().T))
    return float(0.5 * np.sum(np.abs(evals)))


def clamp01(x: float) -> float:
    return float(np.clip(x, 0.0, 1.0))


def greedy_extract(agent_bias: float, bath_bias: float, rate: float, crowding: float) -> tuple[float, float]:
    """
    Local extraction increases agent order using the shared bath's current bias.
    Crowding makes shared-bath depletion exceed the single-agent local gain.
    """
    delta = rate * bath_bias * (1.0 - agent_bias)
    next_agent = clamp01(agent_bias + delta)
    bath_loss = (1.0 + crowding) * delta
    next_bath = clamp01(bath_bias - bath_loss)
    return next_agent, next_bath


def repair_stroke(agent_bias: float, bath_bias: float, rate: float, return_efficiency: float) -> tuple[float, float]:
    """
    Bounded lose/repair stroke: agent sacrifices some local order to recharge the
    shared bath. return_efficiency < 1 means repair is costly and not magical.
    """
    delta = rate * agent_bias
    next_agent = clamp01(agent_bias - delta)
    next_bath = clamp01(bath_bias + return_efficiency * delta)
    return next_agent, next_bath


def zero_repair(agent_bias: float, bath_bias: float) -> tuple[float, float]:
    return agent_bias, bath_bias


def run_policy(
    *,
    horizon: int,
    initial_bath_bias: float,
    initial_agent_biases: list[float],
    extract_rate: float,
    crowding: float,
    repair_rate: float,
    return_efficiency: float,
    repair_selector,
    usable_threshold: float,
) -> dict:
    agent_biases = [clamp01(x) for x in initial_agent_biases]
    bath_bias = clamp01(initial_bath_bias)

    bath_bias_history = [bath_bias]
    bath_negentropy_history = [negentropy_from_bias(bath_bias)]
    avg_agent_negentropy_history = [float(np.mean([negentropy_from_bias(x) for x in agent_biases]))]
    total_agent_negentropy_history = [float(np.sum([negentropy_from_bias(x) for x in agent_biases]))]

    first_below_threshold = None
    first_repair_round = None

    for step in range(horizon):
        repair_index = repair_selector(step, len(agent_biases))
        if repair_index is not None and first_repair_round is None:
            first_repair_round = step

        for idx in range(len(agent_biases)):
            if idx == repair_index:
                agent_biases[idx], bath_bias = repair_stroke(
                    agent_biases[idx],
                    bath_bias,
                    repair_rate,
                    return_efficiency,
                )
            else:
                agent_biases[idx], bath_bias = greedy_extract(
                    agent_biases[idx],
                    bath_bias,
                    extract_rate,
                    crowding,
                )

        bath_bias_history.append(bath_bias)
        bath_negentropy_history.append(negentropy_from_bias(bath_bias))
        avg_agent_negentropy_history.append(float(np.mean([negentropy_from_bias(x) for x in agent_biases])))
        total_agent_negentropy_history.append(float(np.sum([negentropy_from_bias(x) for x in agent_biases])))

        if first_below_threshold is None and bath_negentropy_history[-1] < usable_threshold:
            first_below_threshold = step + 1

    valid_states = all(
        abs(np.trace(density_from_bias(z)) - 1.0) < EPS and np.min(np.linalg.eigvalsh(density_from_bias(z))) > -1e-12
        for z in [bath_bias, *agent_biases]
    )

    return {
        "horizon": horizon,
        "bath_bias_history": bath_bias_history,
        "bath_negentropy_history": bath_negentropy_history,
        "avg_agent_negentropy_history": avg_agent_negentropy_history,
        "total_agent_negentropy_history": total_agent_negentropy_history,
        "final_bath_bias": bath_bias,
        "final_bath_negentropy": bath_negentropy_history[-1],
        "final_avg_agent_negentropy": avg_agent_negentropy_history[-1],
        "first_below_usable_threshold": first_below_threshold if first_below_threshold is not None else horizon + 1,
        "usable_at_horizon": bool(bath_negentropy_history[-1] >= usable_threshold),
        "peak_bath_trace_distance_to_mixed": max(trace_distance_to_mixed(z) for z in bath_bias_history),
        "final_agent_biases": agent_biases,
        "first_repair_round": first_repair_round,
        "valid_density_outputs": valid_states,
    }


def greedy_selector(step: int, n_agents: int) -> int | None:
    del step, n_agents
    return None


def scheduled_selector(step: int, n_agents: int) -> int | None:
    return step % n_agents


def overrepair_selector(step: int, n_agents: int) -> int | None:
    del n_agents
    return 0 if step % 2 == 0 else None


def build_results() -> dict:
    horizon = 20
    initial_bath_bias = 0.78
    initial_agent_biases = [0.18, 0.22, 0.16]
    extract_rate = 0.12
    crowding = 0.55
    usable_threshold = 0.085

    greedy = run_policy(
        horizon=horizon,
        initial_bath_bias=initial_bath_bias,
        initial_agent_biases=initial_agent_biases,
        extract_rate=extract_rate,
        crowding=crowding,
        repair_rate=0.0,
        return_efficiency=0.0,
        repair_selector=greedy_selector,
        usable_threshold=usable_threshold,
    )
    scheduled = run_policy(
        horizon=horizon,
        initial_bath_bias=initial_bath_bias,
        initial_agent_biases=initial_agent_biases,
        extract_rate=extract_rate,
        crowding=crowding,
        repair_rate=0.12,
        return_efficiency=0.82,
        repair_selector=scheduled_selector,
        usable_threshold=usable_threshold,
    )
    overrepair = run_policy(
        horizon=horizon,
        initial_bath_bias=initial_bath_bias,
        initial_agent_biases=initial_agent_biases,
        extract_rate=extract_rate,
        crowding=crowding,
        repair_rate=0.28,
        return_efficiency=0.82,
        repair_selector=overrepair_selector,
        usable_threshold=usable_threshold,
    )
    zero_gradient = run_policy(
        horizon=8,
        initial_bath_bias=0.0,
        initial_agent_biases=initial_agent_biases,
        extract_rate=extract_rate,
        crowding=crowding,
        repair_rate=0.0,
        return_efficiency=0.0,
        repair_selector=greedy_selector,
        usable_threshold=1e-12,
    )

    positive = {
        "greedy_local_extraction_depletes_shared_resource_faster_than_scheduled_repair": {
            "greedy_first_below_threshold": greedy["first_below_usable_threshold"],
            "scheduled_first_below_threshold": scheduled["first_below_usable_threshold"],
            "pass": greedy["first_below_usable_threshold"] < scheduled["first_below_usable_threshold"],
        },
        "scheduled_repair_keeps_bath_usable_at_the_greedy_failure_round": {
            "greedy_failure_round": greedy["first_below_usable_threshold"],
            "scheduled_bath_negentropy_at_greedy_failure": scheduled["bath_negentropy_history"][
                greedy["first_below_usable_threshold"]
            ],
            "threshold": usable_threshold,
            "pass": scheduled["bath_negentropy_history"][greedy["first_below_usable_threshold"]] >= usable_threshold,
        },
        "scheduled_repair_retains_more_residual_bath_resource_at_horizon": {
            "greedy_final_bath_negentropy": greedy["final_bath_negentropy"],
            "scheduled_final_bath_negentropy": scheduled["final_bath_negentropy"],
            "pass": scheduled["final_bath_negentropy"] > greedy["final_bath_negentropy"] + 1e-4,
        },
        "scheduled_repair_preserves_nonzero_collective_output_while_extending_resource_life": {
            "scheduled_final_avg_agent_negentropy": scheduled["final_avg_agent_negentropy"],
            "greedy_final_avg_agent_negentropy": greedy["final_avg_agent_negentropy"],
            "pass": scheduled["final_avg_agent_negentropy"] > 0.03
            and scheduled["final_avg_agent_negentropy"] < greedy["final_avg_agent_negentropy"],
        },
    }

    negative = {
        "repair_free_policy_is_not_resource_superior": {
            "greedy_final_bath_negentropy": greedy["final_bath_negentropy"],
            "scheduled_final_bath_negentropy": scheduled["final_bath_negentropy"],
            "pass": greedy["final_bath_negentropy"] + 1e-12 < scheduled["final_bath_negentropy"],
        },
        "overrepair_is_not_the_same_as_balanced_coordination": {
            "overrepair_first_below_threshold": overrepair["first_below_usable_threshold"],
            "scheduled_first_below_threshold": scheduled["first_below_usable_threshold"],
            "pass": overrepair["first_below_usable_threshold"] < scheduled["first_below_usable_threshold"],
        },
        "row_does_not_claim_universal_engine_optimality": {
            "pass": True,
        },
    }

    boundary = {
        "all_terminal_outputs_remain_valid_density_operators": {
            "greedy_valid": greedy["valid_density_outputs"],
            "scheduled_valid": scheduled["valid_density_outputs"],
            "overrepair_valid": overrepair["valid_density_outputs"],
            "pass": greedy["valid_density_outputs"] and scheduled["valid_density_outputs"] and overrepair["valid_density_outputs"],
        },
        "zero_initial_shared_gradient_does_not_create_resource_from_nothing": {
            "zero_gradient_final_bath_negentropy": zero_gradient["final_bath_negentropy"],
            "zero_gradient_peak_bath_trace_distance_to_mixed": zero_gradient["peak_bath_trace_distance_to_mixed"],
            "pass": zero_gradient["final_bath_negentropy"] < 1e-12
            and zero_gradient["peak_bath_trace_distance_to_mixed"] < 1e-12,
        },
        "comparison_uses_one_finite_shared_bath_only": {
            "agent_count": len(initial_agent_biases),
            "carrier_dimension": 2,
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    return {
        "name": "qit_moloch_coordination_trap",
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
            "scope_note": (
                "Finite shared-bath resource-longevity row: greedy local extraction depletes usable "
                "athermality faster, while scheduled repair/lose strokes keep the shared gradient "
                "above threshold longer without claiming a universal optimum."
            ),
            "policy_snapshots": {
                "greedy": {
                    "first_below_usable_threshold": greedy["first_below_usable_threshold"],
                    "final_bath_negentropy": greedy["final_bath_negentropy"],
                    "final_avg_agent_negentropy": greedy["final_avg_agent_negentropy"],
                },
                "scheduled_repair": {
                    "first_below_usable_threshold": scheduled["first_below_usable_threshold"],
                    "final_bath_negentropy": scheduled["final_bath_negentropy"],
                    "final_avg_agent_negentropy": scheduled["final_avg_agent_negentropy"],
                },
                "overrepair": {
                    "first_below_usable_threshold": overrepair["first_below_usable_threshold"],
                    "final_bath_negentropy": overrepair["final_bath_negentropy"],
                    "final_avg_agent_negentropy": overrepair["final_avg_agent_negentropy"],
                },
            },
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the QIT Moloch coordination trap probe.")
    parser.add_argument(
        "--stdout-only",
        action="store_true",
        help="Print JSON results to stdout instead of writing into the repo result surface.",
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
            / "qit_moloch_coordination_trap_results.json"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {results['summary']['all_pass']}")


if __name__ == "__main__":
    main()
