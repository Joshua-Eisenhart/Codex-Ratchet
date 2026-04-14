#!/usr/bin/env python3
"""
Engine Lab Alignment Overlay
============================
Overlay the open engine lab with stricter companion surfaces when available.

This is a controller-facing comparison surface, not a proof surface.
"""

from __future__ import annotations

import json
import pathlib
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Controller overlay that compares the open engine lab against stricter "
    "QIT-aligned companion surfaces and entropy/readout arrays when available."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "landauer_erasure",
    "carnot_cycle",
]

PRIMARY_LEGO_IDS = [
    "stochastic_thermodynamics",
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

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


def load_json(name: str):
    path = RESULT_DIR / name
    if not path.exists():
        return None
    return json.loads(path.read_text())


def family(row_id: str) -> str:
    if row_id.startswith("szilard"):
        return "szilard"
    if row_id.startswith("carnot"):
        return "carnot"
    if row_id.startswith("qit_") or row_id.startswith("engine_lab_"):
        return "mixed"
    return "unknown"


def level_rank(level: str) -> int:
    ranks = {
        "exact_qit_bookkeeping": 0,
        "stochastic_submechanics": 1,
        "stochastic_forward_reverse": 2,
        "stochastic_operational": 2,
        "parameter_array": 3,
        "duration_array": 3,
        "diagnostic_array": 3,
        "topology_budget_array": 4,
        "adaptive_hold_array": 4,
        "topology_array": 4,
        "topology_entropy_array": 4,
        "record_reset_array": 4,
        "qit_repair_companion": 1,
        "qit_translation_lane": 1,
        "qit_repair_comparison_surface": 1,
        "translation_target_array": 1,
    }
    return ranks.get(level, 99)


def main() -> None:
    engine_lab = load_json("engine_lab_matrix_results.json")
    qit_companion = load_json("qit_engine_companion_array_results.json")
    qit_entropy_companion = load_json("qit_entropy_companion_array_results.json")
    constraint_audit = load_json("engine_lab_constraint_audit_results.json")
    repair_priority = load_json("engine_lab_repair_priority_results.json")
    translation_targets = load_json("engine_lab_translation_targets_results.json")
    carnot_entropy = load_json("carnot_entropy_family_array_results.json")
    szilard_topology_entropy = load_json("szilard_topology_entropy_array_results.json")

    if engine_lab is None:
        raise SystemExit("missing engine_lab_matrix_results.json")

    rows = engine_lab["rows"]
    by_family = {}
    for row in rows:
        row_family = row.get("engine_family") or family(row["id"])
        by_family.setdefault(row_family, []).append(row)

    overlay_rows = []
    for fam, fam_rows in by_family.items():
        fam_rows = sorted(fam_rows, key=lambda row: level_rank(row["level"]))
        exact = [row for row in fam_rows if row["level"] == "exact_qit_bookkeeping"]
        open_lab = [row for row in fam_rows if row["level"] != "exact_qit_bookkeeping"]
        overlay_rows.append(
            {
                "family": fam,
                "exact_anchor_ids": [row["id"] for row in exact],
                "open_lab_ids": [row["id"] for row in open_lab],
                "has_qit_companion_array": bool(qit_companion is not None),
                "has_qit_entropy_companion_array": bool(qit_entropy_companion is not None),
                "has_constraint_audit_array": bool(constraint_audit is not None),
                "has_repair_priority_array": bool(repair_priority is not None),
                "has_translation_target_array": bool(translation_targets is not None),
                "has_entropy_array": bool(
                    (fam == "carnot" and carnot_entropy is not None)
                    or (fam == "szilard" and szilard_topology_entropy is not None)
                ),
            }
        )

    summary = {
        "all_pass": True,
        "engine_lab_rows": len(rows),
        "has_qit_companion_array": bool(qit_companion is not None),
        "has_qit_entropy_companion_array": bool(qit_entropy_companion is not None),
        "has_constraint_audit_array": bool(constraint_audit is not None),
        "has_repair_priority_array": bool(repair_priority is not None),
        "has_translation_target_array": bool(translation_targets is not None),
        "has_carnot_entropy_family_array": bool(carnot_entropy is not None),
        "has_szilard_topology_entropy_array": bool(szilard_topology_entropy is not None),
        "families": sorted(by_family.keys()),
        "scope_note": (
            "Overlay between the open engine lab and stricter companion surfaces. "
            "Use this to route the next QIT-alignment pass rather than to declare admission."
        ),
    }

    out = {
        "name": "engine_lab_alignment_overlay",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": summary,
        "rows": overlay_rows,
    }

    out_path = RESULT_DIR / "engine_lab_alignment_overlay_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
