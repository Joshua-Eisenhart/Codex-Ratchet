#!/usr/bin/env python3
"""Szilard measurement/feedback/reset substep baseline.

This row supplies the missing open-lab substep receipt used by the QIT repair
comparison surface.  It is intentionally small: a binary memory/system model
with four protocol orderings, Shannon entropy bookkeeping, and explicit
negative controls for wrong order.
"""

from __future__ import annotations

import json
import math
import pathlib

import numpy as np


CLASSIFICATION = "classical_baseline"
classification = CLASSIFICATION
divergence_log = (
    "Open-lab Szilard substep baseline for measurement, feedback, and reset "
    "ordering. It is a classical binary-control baseline, not a QIT carrier "
    "or feedback-engine admission."
)

LEGO_IDS = ["szilard_cycle", "landauer_erasure", "stochastic_thermodynamics"]
PRIMARY_LEGO_IDS = ["szilard_cycle"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "binary probability and entropy bookkeeping"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


def h2(p: float) -> float:
    p = min(max(float(p), 1e-12), 1.0 - 1e-12)
    return float(-(p * math.log(p) + (1.0 - p) * math.log(1.0 - p)))


def run_protocol(order: list[str], measurement_accuracy: float = 0.88, reset_strength: float = 0.82) -> dict:
    system_bias = 0.5
    record_quality = 0.0
    feedback_quality = 0.0
    reset_done = False
    stage_trace = []
    for step in order:
        if step == "measurement":
            record_quality = measurement_accuracy
        elif step == "feedback":
            feedback_quality = record_quality
            system_bias = max(system_bias, feedback_quality)
        elif step == "reset":
            reset_done = record_quality > 0.0
            record_quality *= 1.0 - reset_strength
        stage_trace.append(
            {
                "step": step,
                "system_entropy": h2(system_bias),
                "record_entropy": h2(record_quality) if record_quality > 0.0 else 0.0,
                "record_quality": record_quality,
                "feedback_quality": feedback_quality,
            }
        )
    final_entropy = h2(system_bias) + (h2(record_quality) if not reset_done and record_quality > 0.0 else 0.0)
    measurement_mi = math.log(2.0) - h2(measurement_accuracy)
    mean_work = max(0.0, math.log(2.0) - h2(system_bias))
    return {
        "order": order,
        "measurement_accuracy": measurement_accuracy if "measurement" in order else 0.5,
        "measurement_mutual_information": max(0.0, measurement_mi if "measurement" in order else 0.0),
        "mean_work": mean_work,
        "final_entropy": final_entropy,
        "system_bias": system_bias,
        "record_quality": record_quality,
        "reset_done": reset_done,
        "stage_trace": stage_trace,
    }


def main() -> None:
    protocols = {
        "ordered": ["measurement", "feedback", "reset"],
        "feedback_first": ["feedback", "measurement", "reset"],
        "reset_first": ["reset", "measurement", "feedback"],
        "measurement_then_reset_then_feedback": ["measurement", "reset", "feedback"],
    }
    rows = {name: run_protocol(order) for name, order in protocols.items()}
    ordered_entropy = rows["ordered"]["final_entropy"]
    scrambled_min_entropy = min(
        rows["feedback_first"]["final_entropy"],
        rows["reset_first"]["final_entropy"],
        rows["measurement_then_reset_then_feedback"]["final_entropy"],
    )
    positive = {
        "measurement_creates_useful_record": {
            "measurement_accuracy": rows["ordered"]["measurement_accuracy"],
            "measurement_mutual_information": rows["ordered"]["measurement_mutual_information"],
            "pass": rows["ordered"]["measurement_accuracy"] > 0.8 and rows["ordered"]["measurement_mutual_information"] > 0.1,
        },
        "ordered_protocol_beats_scrambled_controls": {
            "ordered_final_entropy": ordered_entropy,
            "best_scrambled_final_entropy": scrambled_min_entropy,
            "pass": ordered_entropy < scrambled_min_entropy,
        },
    }
    negative = {
        "feedback_before_measurement_loses_signal": {
            "feedback_first_entropy": rows["feedback_first"]["final_entropy"],
            "ordered_entropy": ordered_entropy,
            "pass": rows["feedback_first"]["final_entropy"] > ordered_entropy,
        },
        "reset_before_feedback_erases_record_utility": {
            "measurement_reset_feedback_entropy": rows["measurement_then_reset_then_feedback"]["final_entropy"],
            "ordered_entropy": ordered_entropy,
            "pass": rows["measurement_then_reset_then_feedback"]["final_entropy"] > ordered_entropy,
        },
    }
    boundary = {
        "probability_values_are_finite": {
            "pass": all(np.isfinite(row["final_entropy"]) for row in rows.values()),
        },
        "protocols_cover_three_substeps": {
            "pass": all(set(row["order"]) == {"measurement", "feedback", "reset"} for row in rows.values()),
        },
    }
    all_pass = all(v["pass"] for v in positive.values()) and all(v["pass"] for v in negative.values()) and all(v["pass"] for v in boundary.values())
    result = {
        "name": "szilard_measurement_feedback_substeps",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "all_pass": bool(all_pass),
        "divergence_log": divergence_log,
        "claim_ceiling": (
            "classical binary measurement-feedback-reset ordering calibration only; "
            "no QIT, GStack, bridge, axis, nonclassical, or runtime-engine admission"
        ),
        "next_lego_target": (
            "explicit measurement-feedback-erasure calibration with work and erasure-cost observables "
            "plus no-measurement, no-feedback, no-erasure, and random-feedback companions"
        ),
        "promotion_condition": (
            "No promotion from this receipt; downstream calibration must couple ordering, work extraction, "
            "and erasure cost with independent graveyard controls."
        ),
        "demotion_condition": (
            "Demote if scrambled orderings are not worse than ordered measurement-feedback-reset, "
            "or if this receipt is used as QIT/GStack/axis/nonclassical evidence."
        ),
        "blocked_until": (
            "blocked from engine, QIT, GStack, bridge, axis, nonclassical, or feedback-cycle claims "
            "until separate exact calibration receipts close those gates"
        ),
        "out_of_scope": [
            "No quantum carrier.",
            "No erasure heat integral.",
            "No QIT, GStack, bridge, axis, engine, or nonclassical claim.",
        ],
        "operation_sequence": [
            "measurement updates record quality",
            "feedback reads record quality into system bias",
            "reset decays record quality",
            "scrambled order controls compare final entropy",
        ],
        "carrier_topology": "classical binary system plus classical binary record",
        "observable": "measurement mutual information, mean work proxy, final entropy, record quality, and scrambled-order entropy",
        "pass_fail_predicate": "ordered measurement-feedback-reset creates useful record and beats feedback-first, reset-first, and measurement-reset-feedback controls",
        "graveyards": [
            "feedback before measurement",
            "reset before feedback",
            "measurement then reset then feedback",
        ],
        "baselines": [
            "classical binary entropy bookkeeping",
            "zero-record feedback control",
        ],
        "alternative_formulations": [
            "explicit Landauer erasure heat stage",
            "random-feedback companion",
            "repeated-cycle no-erasure companion",
        ],
        "exact_tool_function_needs": {"numpy": ["isfinite"]},
        "lego_or_coupling_target": "classical measurement-feedback-reset ordering calibration support",
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"all_pass": all_pass, **rows},
        "rows": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "szilard_measurement_feedback_substeps_results.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
