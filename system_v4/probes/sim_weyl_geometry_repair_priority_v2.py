#!/usr/bin/env python3
"""
Weyl Geometry Repair Priority v2
================================
Updated controller-facing ranking over the Weyl/Hopf geometry lane after the
compare row gained its own open-vs-strict translation lane.

This is a ranking surface, not a proof surface.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
classification = "canonical"


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Updated controller ranking surface over the Weyl/Hopf geometry lane after "
    "direct translation lanes were added for the composed stack, carrier array, "
    "and carrier compare rows."
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
        "weyl_hopf_spinor_bridge": 0.94,
        "weyl_hopf_pauli_composed_stack": 0.99,
        "weyl_hypergraph_follow_on": 0.96,
        "weyl_geometry_carrier_array": 0.95,
        "weyl_geometry_carrier_compare": 0.93,
        "nested_hopf_tori": 0.92,
        "weyl_pauli_transport": 0.91,
        "hopf_torus_lego": 0.90,
        "weyl_spinor_hopf": 0.89,
        "qit_weyl_carnot_bridge": 0.38,
        "qit_weyl_szilard_geometry_bridge": 0.37,
        "weyl_hypergraph_geometry_bridge": 0.36,
        "weyl_geometry_graph_proof_alignment": 0.40,
        "weyl_geometry_protocol_dag": 0.39,
        "weyl_geometry_multifamily_expansion": 0.18,
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
        "weyl_hopf_spinor_bridge",
        "hopf_torus_lego",
        "weyl_spinor_hopf",
        "weyl_hopf_pauli_composed_stack",
        "weyl_hypergraph_follow_on",
        "weyl_geometry_carrier_array",
        "weyl_geometry_carrier_compare",
    }:
        return "promote_now", 0, "promote_now"
    if row_id in {
        "weyl_geometry_protocol_dag",
        "weyl_geometry_graph_proof_alignment",
        "qit_weyl_carnot_bridge",
        "qit_weyl_szilard_geometry_bridge",
        "weyl_hypergraph_geometry_bridge",
    }:
        return "bridge_only", 2, "bridge_only"
    if row_id == "weyl_geometry_multifamily_expansion":
        return "sidecar_only", 3, "sidecar_only"
    return "sidecar_only", 3, "sidecar_only"


def pair_lookup(compare: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["open_row_id"]: row for row in compare.get("rows", [])}


def repair_score_for_row(row_id: str, pair: dict[str, Any] | None, lane: dict[str, Any] | None) -> float:
    score = base_priority(row_id)
    if lane and truthy(lane.get("summary", {}).get("all_pass")):
        score += 0.02
    if pair:
        score += 0.01
    return round(min(score, 0.99), 6)


def row_note(bucket: str, row_id: str) -> str:
    if bucket == "promote_now":
        if row_id == "weyl_hopf_pauli_composed_stack":
            return "Best open geometry carrier; has a direct open-vs-strict translation lane and remains the top survivor."
        if row_id == "weyl_hypergraph_follow_on":
            return "Hypergraph follow-on now has a bounded translation lane and should move with the companion-ready promote-now set."
        if row_id == "weyl_hopf_spinor_bridge":
            return "Reusable spinor bridge base lego; keep it promoted with the other foundation rows."
        if row_id == "weyl_geometry_carrier_array":
            return "Carrier-array row now has a direct open-vs-strict translation lane and should stay in the promote-now set."
        if row_id == "weyl_geometry_carrier_compare":
            return "Compare row now has its own bounded translation lane; it no longer needs to sit in tighten-then-promote."
        return "Reusable geometry foundation row; keep promoted as base infrastructure."
    if bucket == "bridge_only":
        if row_id == "weyl_geometry_graph_proof_alignment":
            return "Direct graph/proof bridge with solver-backed ordering and chirality checks."
        if row_id == "qit_weyl_carnot_bridge":
            return "Bounded geometry-to-Carnot bridge; keep as a bridge-only controller surface."
        if row_id == "qit_weyl_szilard_geometry_bridge":
            return "Bounded geometry-to-Szilard bridge; keep as a bridge-only controller surface."
        if row_id == "weyl_hypergraph_geometry_bridge":
            return "Bounded geometry-to-hypergraph bridge; keep as a bridge-only controller surface."
        return "Protocol DAG bridge row; useful as a legal schedule, not as owner math."
    if row_id == "weyl_geometry_ladder_audit":
        return "Independent witness audit; keep as a sidecar diagnostic."
    if row_id == "weyl_geometry_multifamily_expansion":
        return "Family-expansion routing sidecar; useful for rankings but not a promotion target."
    return "Legacy geometry sidecar; keep separate from foundation and bridge rows."


def main() -> None:
    matrix = load_json("weyl_geometry_lab_matrix_results.json")
    overlay_v2 = load_json("weyl_geometry_alignment_overlay_v2_results.json")
    audit = load_json("weyl_geometry_constraint_audit_results.json")
    targets = load_json("weyl_geometry_translation_targets_results.json")
    companion = load_json("qit_weyl_geometry_companion_results.json")
    translation_lane = load_json("qit_weyl_geometry_translation_lane_results.json")
    carrier_lane = load_json("qit_weyl_geometry_carrier_translation_lane_results.json")
    compare_lane = load_json("qit_weyl_geometry_compare_translation_lane_results.json")
    hypergraph_lane = load_json("qit_weyl_hypergraph_translation_lane_results.json")
    repair_surface = load_json("qit_weyl_geometry_repair_comparison_surface_results.json")

    repair_pairs = pair_lookup(repair_surface)
    lane_map = {
        "weyl_hopf_pauli_composed_stack": translation_lane,
        "weyl_hypergraph_follow_on": hypergraph_lane,
        "weyl_geometry_carrier_array": carrier_lane,
        "weyl_geometry_carrier_compare": compare_lane,
    }

    rows = []
    for target_row in targets["rows"]:
        row_id = target_row["row_id"]
        bucket, bucket_rank, action_label = classify_bucket(row_id)
        pair = repair_pairs.get(row_id)
        lane = lane_map.get(row_id)
        score = repair_score_for_row(row_id, pair, lane)
        rows.append(
            {
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
                "result_file": target_row["result_file"],
                "all_pass": bool(target_row["all_pass"]),
                "translation_lane_reference": lane["name"] if lane else None,
                "repair_pair_id": pair["pair_id"] if pair else None,
                "repair_surviving_features": pair.get("surviving_features", []) if pair else [],
                "strict_reference_row": pair.get("strict_row_id") if pair else None,
                "note": row_note(bucket, row_id),
            }
        )

    rows.sort(key=lambda row: (row["priority_bucket"], -row["priority_score"], row["row_id"]))

    promote_now_rows = [row for row in rows if row["priority_bucket"] == "promote_now"]
    bridge_rows = [row for row in rows if row["priority_bucket"] == "bridge_only"]
    sidecar_rows = [row for row in rows if row["priority_bucket"] == "sidecar_only"]

    out = {
        "name": "weyl_geometry_repair_priority_v2",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(
                truthy(matrix["summary"]["all_pass"])
                and truthy(overlay_v2["summary"]["all_pass"])
                and truthy(audit["summary"]["all_pass"])
                and truthy(targets["summary"]["all_pass"])
                and truthy(companion["summary"]["all_pass"])
                and truthy(translation_lane["summary"]["all_pass"])
                and truthy(carrier_lane["summary"]["all_pass"])
                and truthy(compare_lane["summary"]["all_pass"])
                and truthy(hypergraph_lane["summary"]["all_pass"])
                and truthy(repair_surface["summary"]["all_pass"])
            ),
            "ranked_rows": len(rows),
            "promote_now_count": len(promote_now_rows),
            "tighten_then_promote_count": 0,
            "bridge_only_count": len(bridge_rows),
            "sidecar_only_count": len(sidecar_rows),
            "top_promote_now_row": promote_now_rows[0]["row_id"] if promote_now_rows else None,
            "top_bridge_row": bridge_rows[0]["row_id"] if bridge_rows else None,
            "top_sidecar_row": sidecar_rows[0]["row_id"] if sidecar_rows else None,
            "strict_anchor_row": "qit_weyl_geometry_companion",
            "matrix_row_count": matrix["summary"]["row_count"],
            "overlay_row_count": overlay_v2["summary"]["row_count"],
            "audit_row_count": audit["summary"]["row_count"],
            "translation_target_row_count": targets["summary"]["row_count"],
            "strict_companion_sample_count": companion["summary"]["sample_count"],
            "strict_translation_lane_count": 4,
            "repair_comparison_pair_count": repair_surface["summary"]["pair_count"],
            "scope_note": (
                "Updated priority ranking after the compare row gained its own direct translation lane. "
                "Promote-now rows are foundation or already have bounded translation support; bridge-only "
                "rows stay schedule/proof surfaces; sidecars stay diagnostic."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "weyl_geometry_repair_priority_v2_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
