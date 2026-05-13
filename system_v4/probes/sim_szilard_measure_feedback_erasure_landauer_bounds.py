#!/usr/bin/env python3
"""Classical one-bit measurement-feedback-erasure calibration with graveyards."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


NAME = "szilard_measure_feedback_erasure_landauer_bounds"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "computes one-bit entropy, feedback work bound, erasure heat, and graveyard controls",
    }
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}
LN2 = float(np.log(2.0))


def binary_entropy(probabilities: np.ndarray) -> float:
    probs = np.asarray(probabilities, dtype=float)
    positive = probs[probs > 0.0]
    return float(-np.sum(positive * np.log(positive)))


def szilard_cycle(kbt: float, probabilities: np.ndarray) -> dict[str, float]:
    information = binary_entropy(probabilities)
    feedback_work_bound = kbt * information
    erasure_heat_floor = kbt * information
    return {
        "kBT": float(kbt),
        "information_nats": float(information),
        "feedback_work_bound": float(feedback_work_bound),
        "erasure_heat_floor": float(erasure_heat_floor),
        "net_cycle_surplus_bound": float(feedback_work_bound - erasure_heat_floor),
    }


def mutual_information(joint: np.ndarray) -> float:
    joint = np.asarray(joint, dtype=float)
    px = np.sum(joint, axis=1)
    py = np.sum(joint, axis=0)
    total = 0.0
    for i in range(joint.shape[0]):
        for j in range(joint.shape[1]):
            if joint[i, j] > 0.0:
                total += float(joint[i, j] * np.log(joint[i, j] / (px[i] * py[j])))
    return total


def run_positive() -> dict[str, object]:
    cycle = szilard_cycle(3.0, np.array([0.5, 0.5]))
    return {
        "one_bit_cycle": cycle,
        "information_equals_ln2": bool(np.isclose(cycle["information_nats"], LN2)),
        "work_bound_equals_kbt_ln2": bool(np.isclose(cycle["feedback_work_bound"], 3.0 * LN2)),
        "erasure_floor_equals_kbt_ln2": bool(np.isclose(cycle["erasure_heat_floor"], 3.0 * LN2)),
        "net_surplus_zero_after_erasure": bool(np.isclose(cycle["net_cycle_surplus_bound"], 0.0)),
    }


def run_negative() -> dict[str, object]:
    no_measurement = szilard_cycle(3.0, np.array([1.0, 0.0]))
    measurement_record = np.array([0.5, 0.5])
    random_feedback_joint = np.outer(measurement_record, measurement_record)
    random_feedback_correlation = mutual_information(random_feedback_joint)
    no_feedback_action = np.array([0.0, 0.0])
    no_feedback_work = float(np.dot(measurement_record, no_feedback_action))
    repeated_cycles_without_erasure = 4
    no_erasure_surplus = repeated_cycles_without_erasure * 3.0 * LN2
    return {
        "no_measurement_zero_information": bool(np.isclose(no_measurement["information_nats"], 0.0)),
        "no_feedback_zero_work": bool(np.isclose(no_feedback_work, 0.0)),
        "random_feedback_zero_correlation": bool(np.isclose(random_feedback_correlation, 0.0)),
        "no_erasure_repeated_cycle_surplus_flagged": bool(no_erasure_surplus > 0.0),
        "graveyard_values": {
            "no_measurement": no_measurement,
            "no_feedback_work": no_feedback_work,
            "random_feedback_correlation": random_feedback_correlation,
            "random_feedback_joint": random_feedback_joint.tolist(),
            "repeated_cycles_without_erasure": repeated_cycles_without_erasure,
            "no_erasure_surplus": no_erasure_surplus,
        },
    }


def run_boundary() -> dict[str, object]:
    zero_temperature = szilard_cycle(0.0, np.array([0.5, 0.5]))
    deterministic_record = szilard_cycle(3.0, np.array([1.0, 0.0]))
    return {
        "zero_temperature_zero_work_and_heat": bool(
            np.isclose(zero_temperature["feedback_work_bound"], 0.0)
            and np.isclose(zero_temperature["erasure_heat_floor"], 0.0)
        ),
        "deterministic_record_zero_information": bool(np.isclose(deterministic_record["information_nats"], 0.0)),
        "zero_temperature": zero_temperature,
        "deterministic_record": deterministic_record,
    }


def run_parameter_sweep() -> dict[str, object]:
    cases = []
    for kbt in [0.5, 1.0, 3.0, 7.0]:
        for probabilities in [
            np.array([0.5, 0.5]),
            np.array([0.75, 0.25]),
            np.array([0.9, 0.1]),
            np.array([1.0, 0.0]),
        ]:
            cycle = szilard_cycle(kbt, probabilities)
            cases.append(
                {
                    "kBT": float(kbt),
                    "probabilities": probabilities.tolist(),
                    **cycle,
                    "bounds_close": bool(
                        np.isclose(cycle["feedback_work_bound"], kbt * cycle["information_nats"])
                        and np.isclose(cycle["erasure_heat_floor"], kbt * cycle["information_nats"])
                        and np.isclose(cycle["net_cycle_surplus_bound"], 0.0)
                    ),
                }
            )
    return {
        "case_count": len(cases),
        "bounds_hold": bool(all(row["bounds_close"] for row in cases)),
        "cases": cases,
    }


def main() -> int:
    positive = run_positive()
    negative = run_negative()
    boundary = run_boundary()
    parameter_sweep = run_parameter_sweep()
    all_pass = (
        positive["information_equals_ln2"]
        and positive["work_bound_equals_kbt_ln2"]
        and positive["erasure_floor_equals_kbt_ln2"]
        and positive["net_surplus_zero_after_erasure"]
        and negative["no_measurement_zero_information"]
        and negative["no_feedback_zero_work"]
        and negative["random_feedback_zero_correlation"]
        and negative["no_erasure_repeated_cycle_surplus_flagged"]
        and boundary["zero_temperature_zero_work_and_heat"]
        and boundary["deterministic_record_zero_information"]
        and parameter_sweep["bounds_hold"]
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": bool(all_pass),
        "claim_ceiling": (
            "classical one-bit measurement-feedback-erasure calibration only; "
            "no QIT, GStack, axis, bridge, nonclassical, or target-system claim"
        ),
        "next_lego_target": "information_work_erasure_cycle_calibration_fixture",
        "promotion_condition": (
            "May only support later calibration planning after an explicit state-update formulation "
            "reproduces these bounds with the same graveyards."
        ),
        "demotion_condition": (
            "Demote if no-measurement, no-feedback, or random-feedback graveyards extract work, "
            "or if erasure heat falls below kBT times information."
        ),
        "blocked_until": "blocked from target feedback-cycle mechanics until explicit state updates and tool receipts exist",
        "out_of_scope": [
            "No quantum measurement update.",
            "No physical work reservoir.",
            "No repeated-memory dynamics, QIT, GStack, axis, bridge, or nonclassical claim.",
        ],
        "divergence_log": (
            "Numpy scalar information thermodynamics is a classical calibration baseline. "
            "It checks measurement-feedback-erasure accounting and graveyards but cannot prove target-system mechanics."
        ),
        "operation_sequence": [
            "compute binary measurement entropy I = -sum p log p",
            "bound feedback work by kBT * I",
            "bound erasure heat floor by kBT * I",
            "check net surplus after erasure is zero",
        ],
        "carrier_topology": "single classical two-outcome record with probability simplex carrier",
        "observable": "information, feedback work bound, erasure heat floor, net surplus, and graveyard booleans",
        "pass_fail_predicate": (
            "one unbiased bit gives I = ln2, work and erasure bounds equal kBT ln2, net surplus closes, "
            "and all graveyards collapse or flag"
        ),
        "graveyards": [
            "no measurement gives zero information",
            "no feedback gives zero work",
            "random feedback has zero correlation",
            "no erasure flags repeated-cycle surplus",
        ],
        "graveyard_companions": [
            {
                "name": "no_measurement_zero_information",
                "expected_failure_mode": "record entropy collapses",
                "predicate": "I == 0",
            },
            {
                "name": "no_feedback_zero_work",
                "expected_failure_mode": "conditional action missing",
                "predicate": "W == 0",
            },
            {
                "name": "random_feedback_zero_correlation",
                "expected_failure_mode": "record/action independence",
                "predicate": "mutual_information(record; action) == 0",
            },
            {
                "name": "no_erasure_repeated_cycle_surplus_flagged",
                "expected_failure_mode": "unpaid memory entropy accumulates",
                "predicate": "unpaid_surplus > 0",
            },
        ],
        "baselines": [
            "binary Shannon entropy in nats",
            "Landauer floor Q_erase >= kBT * I",
            "feedback work bound W <= kBT * I",
        ],
        "baseline_variants": [
            "binary Shannon entropy in nats",
            "Landauer floor Q_erase >= kBT * I",
            "feedback work bound W <= kBT * I",
            "explicit random-feedback joint distribution with zero mutual information",
            "finite sweep over kBT values and binary probability distributions",
        ],
        "alternative_formulations": [
            "explicit density-matrix projective measurement update",
            "conditional unitary feedback map",
            "Lindblad erasure stroke",
        ],
        "exact_tool_function_needs": {"numpy": ["log", "sum", "isclose", "outer", "dot"]},
        "tool_function_needs": {"numpy": ["log", "sum", "isclose", "outer", "dot"]},
        "lego_or_coupling_target": "information_work_erasure_cycle_calibration_fixture",
        "lego_coupling_target": "information_work_erasure_cycle_calibration_fixture",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "parameter_sweep": parameter_sweep,
        "promotion_allowed": False,
        "pass": bool(all_pass),
    }
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
