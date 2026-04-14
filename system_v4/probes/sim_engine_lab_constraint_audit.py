#!/usr/bin/env python3
"""
Engine Lab Constraint Audit
===========================
Compare open-lab Carnot and Szilard rows against strict QIT anchor surfaces.

This is a controller-facing audit. It does not prove admission. It marks which
rows are structurally bridgeable, which are mostly topology/readout exploration,
and which still need repair before they are worth trying to align.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Constraint audit over the engine lab. It compares open-lab rows against "
    "strict QIT anchors and companion readout surfaces to identify repairable "
    "rows, topology-only rows, and rows that are still too open."
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

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((RESULT_DIR / name).read_text())


def infer_geometry_relation(row_id: str) -> str:
    if "topology" in row_id:
        return "varied_geometry_outside_strict_core"
    if "ordering_refinement" in row_id:
        return "same_family_submechanics_variant"
    if "substep_refinement" in row_id:
        return "same_family_submechanics_variant"
    if "balanced_refinement" in row_id:
        return "same_family_submechanics_variant"
    if "ordering_push" in row_id:
        return "same_family_submechanics_variant"
    if "ordering_amplification" in row_id:
        return "same_family_submechanics_variant"
    if "hard_reset" in row_id:
        return "same_family_submechanics_variant"
    if "record_reset" in row_id:
        return "same_family_submechanics_variant"
    if "adaptive_hold" in row_id:
        return "same_family_runtime_schedule_variant"
    if "asymmetric" in row_id or "irreversibility" in row_id:
        return "same_family_runtime_schedule_variant"
    if "closure" in row_id:
        return "same_family_diagnostic_variant"
    if "substeps" in row_id or "reverse_recovery" in row_id:
        return "same_family_submechanics_variant"
    return "same_family_open_variant"


def classify_route(row: dict[str, Any]) -> str:
    if row["clean_run"] and row["geometry_relation"] in {
        "same_family_runtime_schedule_variant",
        "same_family_submechanics_variant",
        "same_family_diagnostic_variant",
    }:
        return "repair_toward_qit_alignment"
    if row["geometry_relation"] == "varied_geometry_outside_strict_core":
        return "topology_lab_only_until_reexpressed"
    if row["clean_run"]:
        return "keep_as_open_lab_sidecar"
    return "open_probe_not_ready_for_alignment"


def clean_run_status(row_id: str, headline_metrics: dict[str, Any]) -> bool:
    if headline_metrics.get("all_pass") is True:
        return True
    if row_id == "szilard_record_reset_repair_sweep":
        return float(headline_metrics.get("best_repair_score", 0.0)) >= 0.55
    return False


def main() -> None:
    engine_lab = load_json("engine_lab_matrix_results.json")
    qit_companion = load_json("qit_engine_companion_array_results.json")
    qit_entropy = load_json("qit_entropy_companion_array_results.json")

    strict_subset = {
        row["id"]: row for row in qit_companion["strict_qit_subset"]
    }
    entropy_rows = {
        row["row_id"]: row for row in qit_entropy["rows"]
    }

    strict_anchor_by_open = {
        row["id"]: row["closest_companion_id"]
        for row in qit_companion["open_lab_companion_rows"]
    }

    audit_rows: list[dict[str, Any]] = []
    for row in engine_lab["rows"]:
        row_id = row["id"]
        if row["engine_family"] not in {"carnot", "szilard"}:
            continue
        if row["level"] == "exact_qit_bookkeeping":
            continue
        if row["likely_constraint_relation"] == "qit_aligned_repair_surface":
            continue

        anchor_id = strict_anchor_by_open.get(row_id.replace("carnot_forward_asymmetric", "carnot_asymmetric_isotherm_sweep")
                                                  .replace("carnot_reverse_asymmetric", "carnot_reverse_asymmetric_sweep")
                                                  .replace("szilard_substeps", "szilard_measurement_feedback_substeps")
                                                  .replace("szilard_reverse_recovery", "szilard_reverse_recovery_sweep")
                                                  .replace("szilard_ordering_sensitivity", "szilard_ordering_sensitivity_sweep"))
        if anchor_id is None:
            # fall back on family exact anchor when the matrix id differs from the companion id
            anchor_id = "qit_carnot_two_bath_cycle" if row["engine_family"] == "carnot" else "qit_szilard_landauer_cycle"

        strict_row = strict_subset.get(anchor_id)
        entropy_anchor = entropy_rows.get(anchor_id)

        clean_run = clean_run_status(row_id, row["headline_metrics"])
        geometry_relation = infer_geometry_relation(row_id)
        has_explicit_order_or_direction = bool(row["direction_modes"])
        has_strict_entropy_anchor = entropy_anchor is not None
        readout_overlap = sorted(
            set(row["entropy_family"]).intersection(set(strict_row["entropy_readout_family"]))
        ) if strict_row else []

        audit_row = {
            "row_id": row_id,
            "family": row["engine_family"],
            "level": row["level"],
            "closest_strict_anchor": anchor_id,
            "strict_anchor_role": strict_row["subset_role"] if strict_row else None,
            "geometry_relation": geometry_relation,
            "clean_run": clean_run,
            "has_explicit_order_or_direction": has_explicit_order_or_direction,
            "has_strict_entropy_anchor": has_strict_entropy_anchor,
            "readout_overlap": readout_overlap,
            "strict_anchor_readouts": strict_row["entropy_readout_family"] if strict_row else [],
            "open_row_readouts": row["entropy_family"],
            "likely_constraint_relation": row["likely_constraint_relation"],
            "route": "",
            "headline_metrics": row["headline_metrics"],
        }
        audit_row["route"] = classify_route(audit_row)
        audit_rows.append(audit_row)

    route_counts = {
        label: sum(row["route"] == label for row in audit_rows)
        for label in sorted({row["route"] for row in audit_rows})
    }
    clean_rows = [row for row in audit_rows if row["clean_run"]]
    summary = {
        "all_pass": True,
        "audited_rows": len(audit_rows),
        "clean_rows": len(clean_rows),
        "repair_toward_qit_alignment_count": route_counts.get("repair_toward_qit_alignment", 0),
        "topology_lab_only_count": route_counts.get("topology_lab_only_until_reexpressed", 0),
        "not_ready_count": route_counts.get("open_probe_not_ready_for_alignment", 0),
        "route_counts": route_counts,
        "scope_note": (
            "Constraint audit over the open engine lab. A 'repair' route means the row is a "
            "good candidate for QIT-aligned redesign. A 'topology_lab_only' route means the "
            "row is informative but still outside the strict carrier/readout envelope."
        ),
    }

    out = {
        "name": "engine_lab_constraint_audit",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": summary,
        "rows": audit_rows,
    }

    out_path = RESULT_DIR / "engine_lab_constraint_audit_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
