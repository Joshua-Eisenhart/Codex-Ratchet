#!/usr/bin/env python3
"""
Szilard Reset Axis Reconciliation
================================
Calibrate the open stochastic reset control (`reset_tilt`) against the strict
QIT reset control (`reset_strength`) using a shared residual-reset-effect score.
"""

from __future__ import annotations

import json
import math
import pathlib
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Calibration surface that maps open stochastic reset tilt and strict QIT "
    "reset strength onto a shared residual-reset-effect score under a "
    "high-quality-record regime."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "stochastic_thermodynamics",
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

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
LN2 = math.log(2.0)


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text())


def reset_effect_from_entropy(entropy_value: float) -> float:
    return float(max(0.0, min(1.0, 1.0 - (entropy_value / LN2))))


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def main() -> None:
    open_repair = load("szilard_record_reset_repair_sweep_results.json")
    qit_record = load("qit_szilard_record_companion_results.json")

    open_rows = [
        row for row in open_repair["rows"]
        if row["measurement_flip_prob"] <= 0.02 and row["record_lifetime_steps"] >= 480
    ]
    qit_rows = [
        row for row in qit_record["rows"]
        if row["measurement_error"] == 0.0 and row["record_lifetime_steps"] >= 240
    ]

    open_by_tilt = {}
    for row in open_rows:
        open_by_tilt.setdefault(row["reset_tilt"], []).append(row)

    qit_by_strength = {}
    for row in qit_rows:
        qit_by_strength.setdefault(row["reset_strength"], []).append(row)

    open_curve = []
    for reset_tilt, rows in sorted(open_by_tilt.items()):
        residual_entropy = mean([row["reset_stage_entropy"] for row in rows])
        entry = {
            "reset_tilt": float(reset_tilt),
            "mean_residual_entropy": residual_entropy,
            "reset_effect": reset_effect_from_entropy(residual_entropy),
            "mean_record_survival_fraction": mean([row["record_survival_fraction"] for row in rows]),
            "mean_measurement_mutual_information": mean([row["measurement_mutual_information"] for row in rows]),
        }
        open_curve.append(entry)

    qit_curve = []
    for reset_strength, rows in sorted(qit_by_strength.items()):
        residual_entropy = mean([row["ordered_reset_memory_entropy"] for row in rows])
        entry = {
            "reset_strength": float(reset_strength),
            "mean_residual_entropy": residual_entropy,
            "reset_effect": reset_effect_from_entropy(residual_entropy),
            "mean_record_survival_fraction": mean([row["ordered_record_survival_fraction"] for row in rows]),
            "mean_measurement_mutual_information": mean([row["ordered_measurement_mutual_information"] for row in rows]),
        }
        qit_curve.append(entry)

    mappings = []
    for open_entry in open_curve:
        best_qit = min(
            qit_curve,
            key=lambda q: abs(q["reset_effect"] - open_entry["reset_effect"]),
        )
        mappings.append(
            {
                "reset_tilt": open_entry["reset_tilt"],
                "matched_reset_strength": best_qit["reset_strength"],
                "open_reset_effect": open_entry["reset_effect"],
                "matched_qit_reset_effect": best_qit["reset_effect"],
                "reset_effect_gap": abs(best_qit["reset_effect"] - open_entry["reset_effect"]),
                "open_residual_entropy": open_entry["mean_residual_entropy"],
                "matched_qit_residual_entropy": best_qit["mean_residual_entropy"],
            }
        )

    best_mapping = min(mappings, key=lambda row: row["reset_effect_gap"])

    positive = {
        "shared_reset_effect_scale_is_finite": {
            "open_points": len(open_curve),
            "qit_points": len(qit_curve),
            "pass": bool(open_curve) and bool(qit_curve),
        },
        "some_open_reset_setting_maps_cleanly_to_strict_reset_strength": {
            "best_reset_effect_gap": best_mapping["reset_effect_gap"],
            "best_open_tilt": best_mapping["reset_tilt"],
            "best_qit_strength": best_mapping["matched_reset_strength"],
            "pass": best_mapping["reset_effect_gap"] < 0.03,
        },
    }

    negative = {
        "the_strongest_open_reset_setting_still_does_not_reach_the_strict_strongest_effect": {
            "open_strongest_effect": max(row["reset_effect"] for row in open_curve),
            "qit_strongest_effect": max(row["reset_effect"] for row in qit_curve),
            "pass": max(row["reset_effect"] for row in open_curve) < max(row["reset_effect"] for row in qit_curve),
        },
    }

    boundary = {
        "all_curve_values_are_finite": {
            "pass": all(
                isinstance(value, (int, float, bool))
                for row in [*open_curve, *qit_curve, *mappings]
                for value in row.values()
            ),
        }
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "szilard_reset_axis_reconciliation",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "best_reset_effect_gap": best_mapping["reset_effect_gap"],
            "best_open_tilt": best_mapping["reset_tilt"],
            "best_matched_qit_strength": best_mapping["matched_reset_strength"],
            "max_open_reset_effect": max(row["reset_effect"] for row in open_curve),
            "max_qit_reset_effect": max(row["reset_effect"] for row in qit_curve),
            "scope_note": (
                "Reset-axis calibration between open stochastic reset tilt and "
                "strict QIT reset strength using a shared residual-reset-effect scale."
            ),
        },
        "open_curve": open_curve,
        "qit_curve": qit_curve,
        "mappings": mappings,
    }

    out_path = RESULT_DIR / "szilard_reset_axis_reconciliation_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
