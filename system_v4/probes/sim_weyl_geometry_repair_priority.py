#!/usr/bin/env python3
"""
Weyl Geometry Repair Priority
=============================
Rank Weyl/Hopf geometry rows by how close they already are to a usable
strict-side translation.

This is a controller-facing ranking surface, not a proof surface. It combines
the matrix, overlay, constraint audit, translation targets, strict companion,
translation lanes, and repair comparison surface into one priority queue.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
classification = "canonical"


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Controller ranking surface over the Weyl/Hopf geometry lane. It combines "
    "route class, translation-target buckets, direct open-vs-strict translation "
    "lanes, and repair-comparison pairs to produce the next promotion queue."
)

LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "transport_geometry",
    "geometry_preserving_basis_change",
    "carrier_probe_support",
]

PRIMARY_LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "transport_geometry",
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
    path = RESULT_DIR / name
    if not path.exists():
        raise SystemExit(f"missing required result file: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "pass", "passed", "yes", "sat"}
    return bool(value)


def base_priority(row_id: str) -> float:
    scores = {
        "weyl_hopf_pauli_composed_stack": 0.99,
        "weyl_geometry_carrier_array": 0.94,
        "nested_hopf_tori": 0.92,
        "weyl_pauli_transport": 0.91,
        "hopf_torus_lego": 0.90,
        "weyl_spinor_hopf": 0.89,
        "weyl_geometry_carrier_compare": 0.68,
        "weyl_geometry_graph_proof_alignment": 0.40,
        "weyl_geometry_protocol_dag": 0.39,
        "weyl_geometry_ladder_audit": 0.17,
        "nested_torus_geometry": 0.16,
        "foundation_hopf_torus_geomstats_clifford": 0.15,
        "torch_hopf_connection": 0.14,
        "weyl_nested_shell": 0.13,
        "graph_shell_geometry": 0.12,
        "toponetx_hopf_crosscheck": 0.11,
    }
    return scores.get(row_id, 0.1)


def classify_bucket(row_id: str) -> tuple[str, int, str]:
    if row_id in {
        "nested_hopf_tori",
        "weyl_pauli_transport",
        "hopf_torus_lego",
        "weyl_spinor_hopf",
        "weyl_hopf_pauli_composed_stack",
        "weyl_geometry_carrier_array",
    }:
        return "promote_now", 0, "promote_now"
    if row_id == "weyl_geometry_carrier_compare":
        return "tighten_then_promote", 1, "tighten_then_promote"
    if row_id in {
        "weyl_geometry_protocol_dag",
        "weyl_geometry_graph_proof_alignment",
    }:
        return "bridge_only", 2, "bridge_only"
    return "sidecar_only", 3, "sidecar_only"


def lane_lookup(results: dict[str, Any], key: str, row_id: str | None = None) -> dict[str, Any] | None:
    if row_id is not None and "open_row_id" in results:
        if results.get("open_row_id") == row_id:
            return results
    if row_id is not None and "rows" in results:
        for row in results["rows"]:
            if row.get("open_row_id") == row_id or row.get("row_id") == row_id:
                return row
    return results if key in results else None


def pair_lookup(compare: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["open_row_id"]: row for row in compare.get("rows", [])}


def repair_score_for_row(row_id: str, pair: dict[str, Any] | None, lane: dict[str, Any] | None) -> float:
    score = base_priority(row_id)

    if row_id in {"nested_hopf_tori", "weyl_pauli_transport", "hopf_torus_lego", "weyl_spinor_hopf"}:
        score += 0.02

    if row_id == "weyl_hopf_pauli_composed_stack":
        if lane and truthy(lane.get("all_pass")):
            score += 0.03
        if pair:
            score += 0.02

    if row_id == "weyl_geometry_carrier_array":
        if lane and truthy(lane.get("all_pass")):
            score += 0.02
        if pair:
            score += 0.01

    if row_id == "weyl_geometry_carrier_compare":
        if pair:
            score += 0.02

    if row_id in {"weyl_geometry_protocol_dag", "weyl_geometry_graph_proof_alignment"}:
        score += 0.01

    return round(min(score, 0.99), 6)


def row_note(bucket: str, row_id: str, pair: dict[str, Any] | None, lane: dict[str, Any] | None) -> str:
    if bucket == "promote_now":
        if row_id == "weyl_hopf_pauli_composed_stack":
            return "Best open geometry carrier; already has a direct open-vs-strict translation lane and survives repair comparison cleanly."
        if row_id == "weyl_geometry_carrier_array":
            return "Carrier-array row is broad but bounded; it already has a direct open-vs-strict translation lane."
        if row_id in {"nested_hopf_tori", "weyl_pauli_transport", "hopf_torus_lego", "weyl_spinor_hopf"}:
            return "Reusable geometry foundation row; keep promoted as base infrastructure."
        return "Promote now: stable geometry row with clean current support."

    if bucket == "tighten_then_promote":
        return "Carrier compare is clean but still broader than the strict companion; tighten before further promotion."

    if bucket == "bridge_only":
        if row_id == "weyl_geometry_graph_proof_alignment":
            return "Direct graph/proof bridge with solver-backed ordering and chirality checks."
        return "Protocol DAG bridge row; useful as a legal schedule, not as owner math."

    if row_id == "weyl_geometry_ladder_audit":
        return "Independent witness audit; keep as a sidecar diagnostic."
    return "Legacy geometry sidecar; keep separate from foundation and bridge rows."


def main() -> None:
    matrix = load_json("weyl_geometry_lab_matrix_results.json")
    overlay = load_json("weyl_geometry_alignment_overlay_results.json")
    audit = load_json("weyl_geometry_constraint_audit_results.json")
    targets = load_json("weyl_geometry_translation_targets_results.json")
    companion = load_json("qit_weyl_geometry_companion_results.json")
    translation_lane = load_json("qit_weyl_geometry_translation_lane_results.json")
    carrier_lane = load_json("qit_weyl_geometry_carrier_translation_lane_results.json")
    repair_surface = load_json("qit_weyl_geometry_repair_comparison_surface_results.json")

    repair_pairs = pair_lookup(repair_surface)
    translation_lane_row = translation_lane if truthy(translation_lane.get("all_pass")) else None
    carrier_lane_row = carrier_lane if truthy(carrier_lane.get("all_pass")) else None

    rows = []
    for target_row in targets["rows"]:
        row_id = target_row["row_id"]
        bucket, bucket_rank, action_label = classify_bucket(row_id)

        pair = repair_pairs.get(row_id)
        lane = None
        if row_id == "weyl_hopf_pauli_composed_stack":
            lane = translation_lane_row
        elif row_id == "weyl_geometry_carrier_array":
            lane = carrier_lane_row

        score = repair_score_for_row(row_id, pair, lane)

        source_surfaces = list(target_row.get("source_surfaces", []))
        if row_id == "weyl_hopf_pauli_composed_stack" and "translation_lane" not in source_surfaces:
            source_surfaces.append("translation_lane")
        if row_id == "weyl_geometry_carrier_array" and "translation_lane" not in source_surfaces:
            source_surfaces.append("translation_lane")
        if pair and "repair_comparison_surface" not in source_surfaces:
            source_surfaces.append("repair_comparison_surface")

        row = {
            "row_id": row_id,
            "label": target_row["label"],
            "priority_bucket": bucket,
            "priority_rank": bucket_rank * 100 + int((1.0 - score) * 100),
            "priority_score": score,
            "action_label": action_label,
            "translation_targets_bucket": target_row["bucket"],
            "controller_route": target_row["controller_route"],
            "matrix_role": target_row["matrix_role"],
            "overlay_category": target_row["overlay_category"],
            "audit_route": target_row["audit_route"],
            "source_surfaces": source_surfaces,
            "result_file": target_row["result_file"],
            "all_pass": bool(target_row["all_pass"]),
            "translation_lane_reference": None,
            "repair_pair_id": pair["pair_id"] if pair else None,
            "repair_surviving_features": pair.get("surviving_features", []) if pair else [],
            "repair_surface_action_label": pair.get("action_label") if pair else None,
            "repair_surface_controller_route": pair.get("controller_route") if pair else None,
            "repair_surface_translation_bucket": pair.get("translation_bucket") if pair else None,
            "strict_reference_row": pair.get("strict_row_id") if pair else None,
            "lane_scope_note": target_row.get("note"),
            "note": row_note(bucket, row_id, pair, lane),
        }

        if row_id == "weyl_hopf_pauli_composed_stack" and lane is not None:
            row["translation_lane_reference"] = {
                "file": "qit_weyl_geometry_translation_lane_results.json",
                "stack_error_gap": lane["summary"]["stack_error_gap"],
                "transport_error_gap": lane["summary"]["transport_error_gap"],
                "basis_change_gap": lane["summary"]["basis_change_gap"],
            }
        elif row_id == "weyl_geometry_carrier_array" and lane is not None:
            row["translation_lane_reference"] = {
                "file": "qit_weyl_geometry_carrier_translation_lane_results.json",
                "carrier_count_gap": lane["summary"]["carrier_count_gap"],
                "carrier_readout_gap_abs": lane["summary"]["carrier_readout_gap_abs"],
                "strict_stack_error": lane["summary"]["strict_stack_error"],
            }

        rows.append(row)

    rows.sort(key=lambda row: (row["priority_bucket"], -row["priority_score"], row["row_id"]))

    promote_now_rows = [row for row in rows if row["priority_bucket"] == "promote_now"]
    tighten_rows = [row for row in rows if row["priority_bucket"] == "tighten_then_promote"]
    bridge_rows = [row for row in rows if row["priority_bucket"] == "bridge_only"]
    sidecar_rows = [row for row in rows if row["priority_bucket"] == "sidecar_only"]

    out = {
        "name": "weyl_geometry_repair_priority",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(
                truthy(matrix["summary"]["all_pass"])
                and truthy(overlay["summary"]["all_pass"])
                and truthy(audit["summary"]["all_pass"])
                and truthy(targets["summary"]["all_pass"])
                and truthy(companion["summary"]["all_pass"])
                and truthy(translation_lane["summary"]["all_pass"])
                and truthy(carrier_lane["summary"]["all_pass"])
                and truthy(repair_surface["summary"]["all_pass"])
            ),
            "ranked_rows": len(rows),
            "promote_now_count": len(promote_now_rows),
            "tighten_then_promote_count": len(tighten_rows),
            "bridge_only_count": len(bridge_rows),
            "sidecar_only_count": len(sidecar_rows),
            "top_promote_now_row": promote_now_rows[0]["row_id"] if promote_now_rows else None,
            "top_tighten_then_promote_row": tighten_rows[0]["row_id"] if tighten_rows else None,
            "top_bridge_row": bridge_rows[0]["row_id"] if bridge_rows else None,
            "top_sidecar_row": sidecar_rows[0]["row_id"] if sidecar_rows else None,
            "strict_anchor_row": companion["summary"]["row_count"] and "qit_weyl_geometry_companion" or None,
            "matrix_row_count": matrix["summary"]["row_count"],
            "overlay_row_count": overlay["summary"]["row_count"],
            "audit_row_count": audit["summary"]["row_count"],
            "translation_target_row_count": targets["summary"]["row_count"],
            "strict_companion_sample_count": companion["summary"]["sample_count"],
            "strict_translation_lane_count": 2,
            "repair_comparison_pair_count": repair_surface["summary"]["pair_count"],
            "scope_note": (
                "Priority ranking over Weyl/Hopf geometry rows. Promote-now rows are already strong "
                "or have direct open-vs-strict translation lanes; tighten-then-promote rows still "
                "need one more carrier/readout pass; bridge-only rows stay as schedule/proof surfaces; "
                "sidecars stay diagnostic."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "weyl_geometry_repair_priority_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
