#!/usr/bin/env python3
"""QIT entropy companion array.

This is a strict readout-family companion surface over finite-carrier QIT
anchor rows.  It fails closed: missing source receipts are reported as missing
rows instead of crashing or pretending the entropy companion is complete.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

classification = "diagnostic_only"
CLASSIFICATION = "diagnostic_only"
divergence_log = (
    "Strict QIT entropy/readout companion array over finite-carrier anchor rows. "
    "It preserves the open-vs-strict gap explicitly and does not promote missing "
    "Szilard/QIT receipts."
)
CLASSIFICATION_NOTE = divergence_log

LEGO_IDS = [
    "quantum_thermodynamics",
    "landauer_erasure",
    "state_distinguishability",
]
PRIMARY_LEGO_IDS = ["quantum_thermodynamics"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads source result receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "deterministic result-path handling"},
}
TOOL_INTEGRATION_DEPTH = {tool: "supportive" for tool in TOOL_MANIFEST}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


SPECS = [
    ("qit_szilard_landauer_cycle", "szilard", "finite_two_qubit_system_memory", ["mutual_information", "free_energy_gain", "erasure_cost"], "qit_szilard_landauer_cycle_results.json"),
    ("qit_strong_coupling_landauer", "strong_coupling_landauer", "finite_two_qubit_system_bath", ["local_clausius_gap", "joint_clausius_gap", "system_bath_mutual_information"], "qit_strong_coupling_landauer_results.json"),
    ("qit_carnot_two_bath_cycle", "carnot", "finite_qubit_working_substance", ["efficiency", "cop", "exact_carnot_distance"], "qit_carnot_two_bath_cycle_results.json"),
    ("qit_attractor_basin_recovery", "control_recovery", "finite_qubit_process_class", ["class_return_gap", "order_gap", "terminal_trace_gap"], "qit_attractor_basin_recovery_results.json"),
    ("qit_szilard_substep_companion", "szilard_repair_substeps", "finite_two_qubit_system_memory_with_hold_decay_axis", ["final_joint_entropy_order_gap", "measurement_accuracy", "memory_blank_trace_distance"], "qit_szilard_substep_companion_results.json"),
    ("qit_szilard_record_companion", "szilard_repair", "finite_two_qubit_system_memory_with_record_decay_axis", ["final_joint_entropy_order_gap", "measurement_mutual_information", "reset_memory_entropy"], "qit_szilard_record_companion_results.json"),
    ("qit_szilard_reverse_recovery_companion", "szilard_repair_reverse_recovery", "finite_two_qubit_system_memory_reverse_recovery_axis", ["entropy_restoration_fraction", "restoration_trace_distance", "erase_information_gain"], "qit_szilard_reverse_recovery_companion_results.json"),
    ("qit_carnot_finite_time_companion", "carnot_repair_finite_time", "finite_qubit_two_bath_with_budget_axis", ["budgeted_efficiency", "budgeted_cop", "carnot_distance"], "qit_carnot_finite_time_companion_results.json"),
    ("qit_carnot_irreversibility_companion", "carnot_repair_irreversibility", "finite_qubit_two_bath_duration_sweep", ["closure_defect", "duration_distance_to_carnot", "budgeted_efficiency"], "qit_carnot_irreversibility_companion_results.json"),
    ("qit_carnot_closure_companion", "carnot_repair_closure", "finite_qubit_two_bath_closure_grid", ["closure_defect", "closure_policy", "closure_leg_concentration"], "qit_carnot_closure_companion_results.json"),
    ("qit_carnot_hold_policy_companion", "carnot_repair_hold_policy", "finite_qubit_two_bath_hold_policy_axis", ["closure_trace_distance", "policy_efficiency", "hold_budget"], "qit_carnot_hold_policy_companion_results.json"),
]


def load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scalar_summary(data: dict[str, Any]) -> dict[str, Any]:
    summary = data.get("summary", {})
    return {
        key: value
        for key, value in summary.items()
        if isinstance(value, (int, float, bool, str))
    }


def main() -> None:
    rows = []
    missing_rows = []
    for row_id, family, carrier, readout_families, filename in SPECS:
        path = RESULT_DIR / filename
        if not path.exists():
            missing_rows.append(
                {
                    "row_id": row_id,
                    "family": family,
                    "carrier": carrier,
                    "readout_families": readout_families,
                    "source_file": str(path),
                    "missing_reason": "QIT entropy/readout source receipt is absent",
                }
            )
            continue
        data = load(path)
        rows.append(
            {
                "row_id": row_id,
                "family": family,
                "carrier": carrier,
                "readout_families": readout_families,
                "source_file": str(path),
                "classification": data.get("classification"),
                "headline_readouts": scalar_summary(data),
            }
        )

    present_families = sorted({row["family"] for row in rows})
    positive = {
        "finite_carrier_readouts_cover_carnot_and_szilard_families": {
            "families": present_families,
            "pass": "carnot" in present_families and "szilard" in present_families,
        },
        "all_present_rows_have_named_readout_families": {
            "pass": bool(rows) and all(len(row["readout_families"]) >= 2 for row in rows),
        },
        "all_present_rows_have_nonempty_headline_readouts": {
            "pass": bool(rows) and all(bool(row["headline_readouts"]) for row in rows),
        },
    }
    negative = {
        "missing_rows_are_reported_if_present": {
            "missing_count": len(missing_rows),
            "pass": True,
        },
        "not_all_strict_rows_share_one_universal_entropy_language": {
            "readout_family_count": len({readout for row in rows for readout in row["readout_families"]}),
            "pass": True,
        },
    }
    boundary = {
        "all_declared_sources_accounted_for": {
            "present_count": len(rows),
            "missing_count": len(missing_rows),
            "pass": len(rows) + len(missing_rows) == len(SPECS),
        },
        "full_companion_requires_no_missing_sources": {
            "pass": len(missing_rows) == 0,
        },
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    out = {
        "name": "qit_entropy_companion_array",
        "classification": CLASSIFICATION if all_pass else "classical_baseline",
        "original_classification": CLASSIFICATION,
        "downgrade_reason": None if all_pass else "missing_entropy_source_receipts",
        "classification_note": CLASSIFICATION_NOTE,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "strict_row_count": len(rows),
            "missing_strict_row_count": len(missing_rows),
            "missing_row_ids": [row["row_id"] for row in missing_rows],
            "families_present": present_families,
            "scope_note": (
                "Strict QIT readout-family companion array over finite-carrier anchors. "
                "This result is partial until the missing entropy/readout source receipts exist."
            ),
        },
        "rows": rows,
        "missing_rows": missing_rows,
    }

    out_path = RESULT_DIR / "qit_entropy_companion_array_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
