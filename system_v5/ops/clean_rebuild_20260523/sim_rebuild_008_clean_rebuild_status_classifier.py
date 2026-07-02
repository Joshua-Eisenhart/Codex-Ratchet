#!/usr/bin/env python3
"""Clean-room rebuild 008: status classifier for rebuild receipts.

This classifier reads only clean_rebuild_20260523 result receipts and classifies
the current rebuilt stack state. It is not a formal-scout classifier and does
not read the contaminated formal estate.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "rebuild_008_clean_rebuild_status_classifier_results.json"

classification = "clean_rebuild_classifier"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "receipt_native_clean_rebuild"
SOURCE_ALIGNMENT_CATEGORY = "clean_rebuild_status_classifier"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Clean rebuild classifier only. Reads clean rebuild receipts to summarize "
    "current rebuilt state. It does not admit formal evidence, Axis0, Xi, Phi0, "
    "or canonical promotion."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing clean rebuild receipt ingestion and classification"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "load_bearing",
    "pathlib": "supportive",
    "time": "supportive",
}

REQUIRED = {
    "rebuild_001_source_engine_chart_from_readonly_results.json": "source_engine_chart_rebuilt",
    "rebuild_002_flux_preaxis_weyl_hopf_from_readonly_results.json": "preaxis_flux_rebuilt",
    "rebuild_003_spinor_entropy_carrier_from_readonly_results.json": "spinor_entropy_carrier_rebuilt",
    "rebuild_004_xi_rho_ab_bridge_family_from_readonly_results.json": "xi_bridge_family_rebuilt",
    "rebuild_005_qit_fep_axis0_batch_from_clean_xi_results.json": "axis0_candidate_batch_rebuilt",
    "rebuild_006_matched_control_ensemble_from_clean_axis0_batch_results.json": "matched_control_ensemble_ran",
    "rebuild_007_point_reference_survivor_stress_results.json": "point_reference_survivor_stressed",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    return value


def read_result(name: str) -> dict[str, Any]:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def main() -> int:
    started = time.time()
    receipt_rows = {}
    missing = []
    failed = []
    for filename, label in REQUIRED.items():
        path = RESULT_DIR / filename
        if not path.exists():
            missing.append(filename)
            continue
        data = read_result(filename)
        row = {
            "filename": filename,
            "label": label,
            "all_pass": bool(data.get("all_pass")),
            "classification": data.get("classification"),
            "promotion_allowed": data.get("promotion_allowed"),
        }
        receipt_rows[label] = row
        if not row["all_pass"]:
            failed.append(filename)

    r6 = read_result("rebuild_006_matched_control_ensemble_from_clean_axis0_batch_results.json")
    r7 = read_result("rebuild_007_point_reference_survivor_stress_results.json")

    initial_survivors = {
        "point_reference": r6["sections"]["matched_control_gate"]["point_reference"]["admitted_positive_readouts"],
        "history_window": r6["sections"]["matched_control_gate"]["history_window"]["admitted_positive_readouts"],
    }
    final_survivors = r7["sections"]["survivor_stress_gate"]["survived_all_controls"]
    amplitude_mi = next(
        row
        for row in r7["sections"]["survivor_stress_gate"]["ensemble_controls"]
        if row["control"] == "amplitude_scrambled"
    )["stats"]["MI"]

    terminal = {
        "source_engine_chart_rebuilt": "source_engine_chart_rebuilt" in receipt_rows,
        "preaxis_flux_rebuilt": "preaxis_flux_rebuilt" in receipt_rows,
        "spinor_entropy_carrier_rebuilt": "spinor_entropy_carrier_rebuilt" in receipt_rows,
        "xi_bridge_family_rebuilt": "xi_bridge_family_rebuilt" in receipt_rows,
        "axis0_candidate_batch_rebuilt": "axis0_candidate_batch_rebuilt" in receipt_rows,
        "matched_controls_ran": "matched_control_ensemble_ran" in receipt_rows,
        "point_reference_initial_survivor": initial_survivors["point_reference"],
        "history_window_initial_survivor": initial_survivors["history_window"],
        "final_survivors_after_rebuild_007": final_survivors,
        "point_reference_mi_killed_by_amplitude_scramble": not bool(final_survivors)
        and amplitude_mi["mean_diff"] < 0.01,
        "formal_admission_blocked": True,
    }
    all_required_pass = not missing and not failed and all(row["all_pass"] for row in receipt_rows.values())
    clean_axis0_closed_for_current_candidate = all_required_pass and terminal["point_reference_mi_killed_by_amplitude_scramble"]
    result = {
        "schema": "clean_rebuild_result_v1",
        "name": "rebuild_008_clean_rebuild_status_classifier",
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "all_pass": all_required_pass,
        "receipt_rows": receipt_rows,
        "missing": missing,
        "failed": failed,
        "terminal_status": terminal,
        "classification_summary": {
            "clean_rebuild_stack_base": "rebuilt" if all_required_pass else "incomplete",
            "current_axis0_survivor": "killed_or_nonrobust" if clean_axis0_closed_for_current_candidate else "open",
            "done_for_current_clean_candidate": clean_axis0_closed_for_current_candidate,
            "next_allowed_work": (
                "formal estate reset and isolated rerun, or a genuinely new Xi/Axis0 candidate from read-only sources"
            ),
        },
        "source_boundary": {
            "reads_formal_scout_results": False,
            "reads_grok_sim": False,
            "reads_external_audits": False,
            "reads_cross_lane_synthesis_docs": False,
            "reads_clean_rebuild_results": True,
        },
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT_PATH)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

