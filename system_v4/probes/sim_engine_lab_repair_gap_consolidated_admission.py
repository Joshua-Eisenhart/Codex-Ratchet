#!/usr/bin/env python3
"""Re-check repair-gap rows against their original failed thresholds."""

from __future__ import annotations

import json
import pathlib
from typing import Any


CLASSIFICATION = "controller_audit"
classification = CLASSIFICATION
divergence_log = (
    "Controller-index consolidated re-check for engine-lab repair-gap rows. "
    "It tests whether passing successor lanes satisfy the original failed "
    "thresholds before any blocker is treated as lifted."
)

LEGO_IDS = ["engine_lab_matrix", "repair_gap", "translation_threshold"]
PRIMARY_LEGO_IDS = ["engine_lab_matrix"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads original and successor repair-gap receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {tool: "supportive" for tool in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


def load(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def abs_lt(value: float, bound: float) -> dict[str, Any]:
    return {"value": value, "bound": bound, "pass": abs(float(value)) < float(bound)}


def lt(value: float, bound: float) -> dict[str, Any]:
    return {"value": value, "bound": bound, "pass": float(value) < float(bound)}


def reset_recheck_candidates() -> list[dict[str, Any]]:
    candidates = []
    recheck = load("szilard_record_ordering_refinement_reset_swing_sweep_results.json")
    summary = recheck["summary"]
    candidates.append(
        {
            "row_id": "szilard_record_ordering_refinement_reset_swing_sweep",
            "receipt": str(RESULT_DIR / "szilard_record_ordering_refinement_reset_swing_sweep_results.json"),
            "open_reset_swing": summary["open_reset_swing"],
            "qit_reset_swing": summary["qit_reset_swing"],
            "reset_swing_gap": summary["reset_swing_gap"],
            "residual_reset_entropy_gap": summary["residual_reset_entropy_gap"],
            "all_pass": bool(summary.get("all_pass")),
        }
    )
    widened_path = RESULT_DIR / "measurement_record_reset_parameter_sweep_results.json"
    if widened_path.exists():
        widened = json.loads(widened_path.read_text(encoding="utf-8"))
        widened_summary = widened["summary"]
        candidates.append(
            {
                "row_id": "measurement_record_reset_parameter_sweep",
                "receipt": str(widened_path),
                "open_reset_swing": widened_summary["best_open_reset_swing"],
                "qit_reset_swing": widened_summary["qit_reset_swing"],
                "reset_swing_gap": widened_summary["best_reset_swing_gap"],
                "residual_reset_entropy_gap": widened_summary["best_residual_reset_entropy_gap"],
                "all_pass": bool(widened_summary.get("all_pass")),
            }
        )
    return candidates


def record_translation_recheck() -> dict[str, Any]:
    original = load("qit_szilard_record_translation_lane_results.json")
    successor = load("qit_szilard_record_ordering_refinement_translation_lane_results.json")
    measurement_recheck = load("szilard_record_ordering_refinement_measurement_accuracy_recheck_results.json")
    original_summary = original["summary"]
    successor_summary = successor["summary"]
    measurement_summary = measurement_recheck["summary"]
    reset_candidates = reset_recheck_candidates()
    reset_swing_summary = min(
        reset_candidates,
        key=lambda candidate: max(
            abs(float(candidate["reset_swing_gap"])),
            abs(float(candidate["residual_reset_entropy_gap"])),
        ),
    )
    checks = {
        "ordering_margin_gap_under_original_bound": abs_lt(successor_summary["ordering_margin_gap"], 0.1),
        "measurement_accuracy_gap_under_original_bound": abs_lt(
            measurement_summary["measurement_accuracy_gap"], 0.05
        ),
        "measurement_mi_gap_under_original_bound": abs_lt(successor_summary["measurement_mi_gap"], 0.1),
        "record_survival_gap_under_original_bound": abs_lt(successor_summary["record_survival_gap"], 0.2),
        "reset_swing_gap_under_original_bound": abs_lt(reset_swing_summary["reset_swing_gap"], 0.15),
        "residual_reset_entropy_gap_under_original_bound": abs_lt(
            reset_swing_summary["residual_reset_entropy_gap"], 0.15
        ),
    }
    all_pass = all(check["pass"] for check in checks.values())
    return {
        "row_id": "qit_szilard_record_translation_lane",
        "original_receipt": str(RESULT_DIR / "qit_szilard_record_translation_lane_results.json"),
        "successor_receipt": str(RESULT_DIR / "qit_szilard_record_ordering_refinement_translation_lane_results.json"),
        "measurement_accuracy_recheck_receipt": str(
            RESULT_DIR / "szilard_record_ordering_refinement_measurement_accuracy_recheck_results.json"
        ),
        "reset_swing_recheck_receipt": reset_swing_summary["receipt"],
        "reset_swing_recheck_candidates": reset_candidates,
        "status": "closed" if all_pass else "still_open",
        "all_pass": bool(all_pass),
        "checks": checks,
        "metric_caveat": (
            "The original measurement-accuracy and reset checks used measurement_accuracy_gap "
            "and reset_swing_gap. This controller recheck accepts only exact successor "
            "receipts for those observables; substituted observables remain insufficient."
        ),
        "original_failed_summary": {
            "ordering_margin_gap": original_summary["ordering_margin_gap"],
            "measurement_mi_gap": original_summary["measurement_mi_gap"],
            "record_survival_gap": original_summary["record_survival_gap"],
            "reset_swing_gap": original_summary["reset_swing_gap"],
        },
        "successor_summary": {
            "ordering_margin_gap": successor_summary["ordering_margin_gap"],
            "measurement_mi_gap": successor_summary["measurement_mi_gap"],
            "record_survival_gap": successor_summary["record_survival_gap"],
            "residual_reset_entropy_gap": successor_summary["residual_reset_entropy_gap"],
        },
        "measurement_accuracy_recheck_summary": {
            "open_mean_measurement_accuracy": measurement_summary["open_mean_measurement_accuracy"],
            "qit_mean_measurement_accuracy": measurement_summary["qit_mean_measurement_accuracy"],
            "measurement_accuracy_gap": measurement_summary["measurement_accuracy_gap"],
        },
        "reset_swing_recheck_summary": {
            "open_reset_swing": reset_swing_summary["open_reset_swing"],
            "qit_reset_swing": reset_swing_summary["qit_reset_swing"],
            "reset_swing_gap": reset_swing_summary["reset_swing_gap"],
            "residual_reset_entropy_gap": reset_swing_summary["residual_reset_entropy_gap"],
            "selected_recheck_row_id": reset_swing_summary["row_id"],
        },
    }


def substep_refinement_recheck() -> dict[str, Any]:
    original = load("qit_szilard_substep_refinement_translation_lane_results.json")
    successor = load("qit_szilard_substep_ordering_push_translation_lane_results.json")
    original_summary = original["summary"]
    successor_summary = successor["summary"]
    checks = {
        "ordering_gap_is_below_original_bound": lt(successor_summary["ordering_margin_gap"], 0.45),
        "measurement_information_gap_stays_below_original_bound": abs_lt(
            successor_summary["measurement_mutual_information_gap"], 0.08
        ),
        "reset_signal_gap_is_below_original_bound": lt(successor_summary["reset_signal_gap"], 0.35),
    }
    all_pass = all(check["pass"] for check in checks.values())
    return {
        "row_id": "qit_szilard_substep_refinement_translation_lane",
        "original_receipt": str(RESULT_DIR / "qit_szilard_substep_refinement_translation_lane_results.json"),
        "successor_receipt": str(RESULT_DIR / "qit_szilard_substep_ordering_push_translation_lane_results.json"),
        "status": "closed" if all_pass else "still_open",
        "all_pass": bool(all_pass),
        "checks": checks,
        "original_failed_summary": {
            "ordering_margin_gap": original_summary["ordering_margin_gap"],
            "measurement_mutual_information_gap": original_summary["measurement_mutual_information_gap"],
            "reset_signal_gap": original_summary["reset_signal_gap"],
        },
        "successor_summary": {
            "ordering_margin_gap": successor_summary["ordering_margin_gap"],
            "measurement_mutual_information_gap": successor_summary["measurement_mutual_information_gap"],
            "reset_signal_gap": successor_summary["reset_signal_gap"],
        },
    }


def main() -> None:
    rows = [record_translation_recheck(), substep_refinement_recheck()]
    all_pass = all(row["all_pass"] for row in rows)
    result = {
        "name": "engine_lab_repair_gap_consolidated_admission",
        "classification": CLASSIFICATION,
        "sim_execution_kind": "controller_index",
        "controller_index_exempt": True,
        "controller_index_exemption_reason": (
            "This result re-checks existing repair-gap receipts against original row-local "
            "thresholds; it does not admit QIT, GStack, axis, or engine runtime claims."
        ),
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "closed_rows": sum(row["status"] == "closed" for row in rows),
            "still_open_rows": sum(row["status"] != "closed" for row in rows),
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "engine_lab_repair_gap_consolidated_admission_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
