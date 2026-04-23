#!/usr/bin/env python3
"""
Engine Lab Translation Targets
==============================
Turn repair-priority rows into explicit next translation targets with matched
companions, key deltas, and action labels.
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Controller surface that converts the repair-priority queue into explicit "
    "translation targets. It is not a theorem surface."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "stochastic_thermodynamics",
    "state_distinguishability",
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


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text())


def priority_action(bucket: str, score: float, has_pair: bool) -> str:
    if bucket == "p0_translate_now":
        return "translate_now"
    if bucket == "p1_good_candidate":
        return "tighten_metrics_then_translate"
    if has_pair:
        return "strengthen_open_row_or_companion"
    if score == 0.0:
        return "build_new_companion"
    return "reassess"


def main() -> None:
    priority = load("engine_lab_repair_priority_results.json")
    compare = load("qit_repair_comparison_surface_results.json")

    pair_by_id = {row["pair_id"]: row for row in compare["rows"]}

    rows = []
    for item in priority["rows"]:
        pair = pair_by_id.get(item["pair_id"]) if item["pair_id"] else None
        rows.append(
            {
                "row_id": item["row_id"],
                "family": item["family"],
                "priority_bucket": item["priority_bucket"],
                "translation_closeness_score": item["translation_closeness_score"],
                "pair_id": item["pair_id"],
                "target_qit_row_id": pair["qit_row_id"] if pair else None,
                "action_label": priority_action(
                    item["priority_bucket"],
                    item["translation_closeness_score"],
                    item["has_direct_qit_pair"],
                ),
                "headline_metrics": item["headline_metrics"],
                "delta_summary": pair["delta"] if pair else {},
            }
        )

    translate_now = [row for row in rows if row["action_label"] == "translate_now"]
    tighten_then_translate = [row for row in rows if row["action_label"] == "tighten_metrics_then_translate"]
    build_companion = [row for row in rows if row["action_label"] == "build_new_companion"]

    out = {
        "name": "engine_lab_translation_targets",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": True,
            "target_rows": len(rows),
            "translate_now_count": len(translate_now),
            "tighten_then_translate_count": len(tighten_then_translate),
            "build_companion_count": len(build_companion),
            "top_translate_now_row": translate_now[0]["row_id"] if translate_now else None,
            "scope_note": (
                "Action surface over repair-priority rows. It names which rows are ready to "
                "translate, which need tighter metrics first, and which still need a new strict companion."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "engine_lab_translation_targets_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
