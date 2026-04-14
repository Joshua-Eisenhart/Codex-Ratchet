#!/usr/bin/env python3
"""
Weyl Geometry Lab Matrix
=========================
Controller-facing matrix for the Weyl/Hopf geometry lane.

This is not a doctrinal summary. It is a compact lab index that makes the
following surfaces comparable in one place:
  - new reusable base legos
  - composed Weyl/Hopf/Pauli rows
  - graph/proof bridge rows
  - carrier array / carrier compare rows
  - directly relevant legacy geometry anchors already in the repo
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter
from typing import Any
classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"


CLASSIFICATION = "classical_baseline"
CLASSIFICATION_NOTE = (
    "Controller-facing Weyl/Hopf geometry matrix over reusable legos, "
    "composed rows, bridge rows, and directly relevant legacy geometry anchors."
)

LEGO_IDS = [
    "weyl_geometry_lab_matrix",
    "nested_hopf_tori",
    "weyl_pauli_transport",
    "weyl_hopf_pauli_composed_stack",
    "weyl_geometry_protocol_dag",
    "weyl_geometry_graph_proof_alignment",
    "weyl_geometry_carrier_array",
    "weyl_geometry_carrier_compare",
    "weyl_geometry_ladder_audit",
]

PRIMARY_LEGO_IDS = [
    "weyl_geometry_lab_matrix",
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

ROW_SPECS = [
    {
        "id": "nested_hopf_tori",
        "label": "Nested Hopf tori base lego",
        "role": "base_lego",
        "source_kind": "new_lego",
        "level": "nested_torus_geometry",
        "geometry_topology": "layered_hopf_tori",
        "result_file": RESULT_DIR / "lego_nested_hopf_tori_results.json",
        "scope_hint": "base_lego",
    },
    {
        "id": "weyl_pauli_transport",
        "label": "Weyl / Pauli transport lego",
        "role": "base_lego",
        "source_kind": "new_lego",
        "level": "weyl_transport",
        "geometry_topology": "left_right_weyl_spinors_on_nested_tori",
        "result_file": RESULT_DIR / "lego_weyl_pauli_transport_results.json",
        "scope_hint": "base_lego",
    },
    {
        "id": "weyl_hopf_pauli_composed_stack",
        "label": "Composed Weyl / Hopf / Pauli stack",
        "role": "composed_row",
        "source_kind": "new_composed_row",
        "level": "stacked_geometry",
        "geometry_topology": "nested_hopf_tori_plus_pauli_transport",
        "result_file": RESULT_DIR / "weyl_hopf_pauli_composed_stack_results.json",
        "scope_hint": "composed_stack",
    },
    {
        "id": "weyl_geometry_protocol_dag",
        "label": "Weyl geometry protocol DAG",
        "role": "graph_proof_lego",
        "source_kind": "new_bridge_row",
        "level": "graph_proof_alignment",
        "geometry_topology": "nested_hopf_tori_schedule_graph",
        "result_file": RESULT_DIR / "lego_weyl_geometry_protocol_dag_results.json",
        "scope_hint": "graph_proof_bridge",
    },
    {
        "id": "weyl_geometry_graph_proof_alignment",
        "label": "Weyl geometry graph / proof alignment",
        "role": "graph_proof_bridge",
        "source_kind": "new_bridge_row",
        "level": "graph_proof_alignment",
        "geometry_topology": "nested_hopf_tori_transport_graph_alignment",
        "result_file": RESULT_DIR / "weyl_geometry_graph_proof_alignment_results.json",
        "scope_hint": "graph_proof_bridge",
    },
    {
        "id": "weyl_geometry_carrier_array",
        "label": "Weyl geometry carrier array",
        "role": "carrier_array",
        "source_kind": "new_bridge_row",
        "level": "carrier_array",
        "geometry_topology": "multi_carrier_geometry_array",
        "result_file": RESULT_DIR / "weyl_geometry_carrier_array_results.json",
        "scope_hint": "carrier_compare",
    },
    {
        "id": "weyl_geometry_carrier_compare",
        "label": "Weyl geometry carrier compare",
        "role": "carrier_compare",
        "source_kind": "new_bridge_row",
        "level": "carrier_compare",
        "geometry_topology": "compare_across_hopf_sphere_graph_hypergraph",
        "result_file": RESULT_DIR / "lego_weyl_geometry_carrier_compare_results.json",
        "scope_hint": "carrier_compare",
    },
    {
        "id": "weyl_geometry_ladder_audit",
        "label": "Weyl geometry ladder audit",
        "role": "ladder_audit",
        "source_kind": "new_bridge_row",
        "level": "ladder_audit",
        "geometry_topology": "ambient_vs_engine_bridge_ladder",
        "result_file": RESULT_DIR / "weyl_geometry_ladder_audit_results.json",
        "scope_hint": "ladder_audit",
    },
    {
        "id": "hopf_torus_lego",
        "label": "Legacy Hopf torus anchor",
        "role": "legacy_anchor",
        "source_kind": "legacy_geometry",
        "level": "legacy_anchor",
        "geometry_topology": "hopf_torus",
        "result_file": RESULT_DIR / "hopf_torus_lego_results.json",
        "scope_hint": "legacy_geometry",
    },
    {
        "id": "nested_torus_geometry",
        "label": "Legacy nested torus geometry",
        "role": "legacy_anchor",
        "source_kind": "legacy_geometry",
        "level": "legacy_anchor",
        "geometry_topology": "nested_torus",
        "result_file": RESULT_DIR / "nested_torus_geometry_results.json",
        "scope_hint": "legacy_geometry",
    },
    {
        "id": "foundation_hopf_torus_geomstats_clifford",
        "label": "Foundation Hopf torus / geomstats / clifford",
        "role": "legacy_anchor",
        "source_kind": "legacy_geometry",
        "level": "legacy_anchor",
        "geometry_topology": "hopf_torus_with_geomstats_and_clifford",
        "result_file": RESULT_DIR / "foundation_hopf_torus_geomstats_clifford_results.json",
        "scope_hint": "legacy_geometry",
    },
    {
        "id": "torch_hopf_connection",
        "label": "Torch Hopf connection",
        "role": "legacy_anchor",
        "source_kind": "legacy_geometry",
        "level": "legacy_anchor",
        "geometry_topology": "hopf_connection_form",
        "result_file": RESULT_DIR / "torch_hopf_connection_results.json",
        "scope_hint": "legacy_geometry",
    },
    {
        "id": "weyl_nested_shell",
        "label": "Legacy Weyl nested shell",
        "role": "legacy_anchor",
        "source_kind": "legacy_geometry",
        "level": "legacy_anchor",
        "geometry_topology": "weyl_nested_shell",
        "result_file": RESULT_DIR / "weyl_nested_shell_results.json",
        "scope_hint": "legacy_geometry",
    },
    {
        "id": "graph_shell_geometry",
        "label": "Legacy graph shell geometry",
        "role": "legacy_anchor",
        "source_kind": "legacy_geometry",
        "level": "legacy_anchor",
        "geometry_topology": "graph_shell",
        "result_file": RESULT_DIR / "graph_shell_geometry_results.json",
        "scope_hint": "legacy_geometry",
    },
    {
        "id": "toponetx_hopf_crosscheck",
        "label": "Legacy TopoNetX Hopf cross-check",
        "role": "legacy_anchor",
        "source_kind": "legacy_geometry",
        "level": "legacy_anchor",
        "geometry_topology": "hopf_torus_topology_crosscheck",
        "result_file": RESULT_DIR / "toponetx_hopf_crosscheck_results.json",
        "scope_hint": "legacy_geometry",
    },
]

LANE_ORDER = {
    "base_lego": 0,
    "composed_row": 1,
    "graph_proof_lego": 2,
    "graph_proof_bridge": 3,
    "carrier_array": 4,
    "carrier_compare": 5,
    "ladder_audit": 6,
    "legacy_anchor": 7,
}


def load_json(path: pathlib.Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "pass", "passed", "yes", "sat"}
    return False


def infer_all_pass(data: dict[str, Any] | None) -> bool:
    if not data:
        return False

    summary = data.get("summary")
    if isinstance(summary, dict):
        if "all_pass" in summary:
            return truthy(summary["all_pass"])
        if "total_fail" in summary:
            return int(summary["total_fail"]) == 0
        if "failed" in summary:
            return int(summary["failed"]) == 0
        if {"positive_fail", "negative_fail", "boundary_fail"} <= summary.keys():
            return (
                int(summary["positive_fail"]) == 0
                and int(summary["negative_fail"]) == 0
                and int(summary["boundary_fail"]) == 0
            )
        if {"positive_pass", "negative_pass", "boundary_pass"} <= summary.keys():
            return (
                truthy(summary["positive_pass"])
                and truthy(summary["negative_pass"])
                and truthy(summary["boundary_pass"])
            )

    if "all_pass" in data:
        return truthy(data["all_pass"])

    for section_name in ("positive", "negative", "boundary"):
        section = data.get(section_name)
        if not isinstance(section, dict):
            continue
        for entry in section.values():
            if isinstance(entry, dict):
                if "pass" in entry and not truthy(entry["pass"]):
                    return False
                if "status" in entry and isinstance(entry["status"], str):
                    if entry["status"].strip().lower() in {"fail", "false", "killed"}:
                        return False

    return True


def used_tools(data: dict[str, Any] | None) -> list[str]:
    if not data:
        return []
    manifest = data.get("tool_manifest", {})
    if not isinstance(manifest, dict):
        return []
    return sorted([name for name, info in manifest.items() if isinstance(info, dict) and info.get("used")])


def compact_summary_fields(data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    summary = data.get("summary")
    if not isinstance(summary, dict):
        return {}
    keys = [
        "all_pass",
        "passed",
        "failed",
        "total_fail",
        "sample_count",
        "row_count",
        "result_count",
        "carrier_count",
        "total_tests",
        "audited_rows",
        "clean_rows",
        "node_count",
        "edge_count",
        "longest_path_length",
        "graph_path_length",
        "max_point_norm_error",
        "max_left_right_overlap_abs",
        "max_spinor_norm_error",
        "max_transport_error",
        "max_stack_error",
        "mean_left_entropy_spread",
        "mean_step_bloch_jump_spread",
        "ambient_nontrivial_count",
        "engine_nontrivial",
        "overlay_nontrivial",
        "witness_separable",
    ]
    out = {}
    for key in keys:
        if key in summary:
            out[key] = summary[key]
    return out


def extract_headline(row_id: str, data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {"missing": True}

    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    positive = data.get("positive") if isinstance(data.get("positive"), dict) else {}
    negative = data.get("negative") if isinstance(data.get("negative"), dict) else {}
    boundary = data.get("boundary") if isinstance(data.get("boundary"), dict) else {}
    graph_summary = data.get("graph_summary") if isinstance(data.get("graph_summary"), dict) else {}

    headline: dict[str, Any] = {}

    if row_id == "nested_hopf_tori":
        headline = {
            "sample_count": summary.get("sample_count"),
            "torus_levels": summary.get("torus_levels"),
            "max_point_norm_error": summary.get("max_point_norm_error"),
            "max_hopf_norm_error": summary.get("max_hopf_norm_error"),
            "max_transport_error": summary.get("max_transport_error"),
            "max_stack_error": summary.get("max_stack_error"),
        }
    elif row_id == "weyl_pauli_transport":
        samples = positive.get("sample_records", [])
        first = samples[0] if samples else {}
        headline = {
            "sample_count": summary.get("sample_count", len(samples)),
            "transport_count": summary.get("transport_count"),
            "max_left_right_overlap_abs": first.get("left_right_overlap_abs"),
            "max_bloch_antipodal_gap": first.get("bloch_antipodal_gap"),
            "transport_roundtrip_error": first.get("transport_roundtrip_error"),
            "radii_monotone": first.get("radii_monotone"),
        }
    elif row_id == "weyl_hopf_pauli_composed_stack":
        headline = {
            "sample_count": summary.get("sample_count"),
            "torus_levels": summary.get("torus_levels"),
            "max_spinor_norm_error": summary.get("max_spinor_norm_error"),
            "max_bloch_alignment_error": summary.get("max_bloch_alignment_error"),
            "max_transport_error": summary.get("max_transport_error"),
            "max_stack_error": summary.get("max_stack_error"),
        }
    elif row_id == "weyl_geometry_protocol_dag":
        headline = {
            "node_count": graph_summary.get("node_count"),
            "edge_count": graph_summary.get("edge_count"),
            "longest_path_length": graph_summary.get("longest_path_length"),
            "correct_order_sat": positive.get("z3_forces_the_geometry_stack_ordering", {}).get("correct_order_sat"),
            "reverse_order_unsat": positive.get("z3_forces_the_geometry_stack_ordering", {}).get("reverse_order_unsat"),
            "back_edge_unsat": negative.get("back_edge_cycle_control_is_unsat", {}).get("z3_verdict"),
        }
    elif row_id == "weyl_geometry_graph_proof_alignment":
        headline = {
            "node_count": graph_summary.get("node_count"),
            "edge_count": graph_summary.get("edge_count"),
            "graph_path_length": summary.get("graph_path_length", graph_summary.get("longest_path_length")),
            "ordering_unsat": positive.get("z3_forces_the_geometry_stack_ordering", {}).get("reverse_order_unsat"),
            "chirality_unsat": positive.get("z3_separates_left_and_right_chirality_signs", {}).get("verdict"),
            "pauli_products_ok": positive.get("pauli_products_match_the_qubit_algebra", {}).get("pass"),
            "max_left_right_overlap_abs": positive.get("left_and_right_spinors_stay_operationally_distinct_on_each_carrier", {}).get("max_left_right_overlap_abs"),
        }
    elif row_id == "weyl_geometry_carrier_array":
        checks = positive.get("comparison_spread", {})
        headline = {
            "carrier_count": summary.get("carrier_count"),
            "total_tests": summary.get("total_tests"),
            "passed_carriers": summary.get("passed_carriers"),
            "comparison_spread_pass": checks.get("passed"),
            "max_nested_lr_overlap": positive.get("nested_hopf_torus_core", {}).get("lr_orthogonality_on_nested_tori", {}).get("max_|<L|R>|"),
            "max_nested_bloch_gap": positive.get("nested_hopf_torus_core", {}).get("bloch_antipodality_on_nested_tori", {}).get("max_|b_L + b_R|"),
        }
    elif row_id == "weyl_geometry_carrier_compare":
        checks = summary.get("checks", {})
        headline = {
            "carrier_count": summary.get("carrier_count"),
            "result_count": summary.get("result_count"),
            "comparison_rows": summary.get("comparison_rows"),
            "comparison_spread_pass": checks.get("comparison_spread", {}).get("passed"),
            "mean_left_entropy_spread": checks.get("comparison_spread", {}).get("mean_left_entropy_spread"),
            "mean_step_bloch_jump_spread": checks.get("comparison_spread", {}).get("mean_step_bloch_jump_spread"),
        }
    elif row_id == "weyl_geometry_ladder_audit":
        headline = {
            "ambient_nontrivial_count": summary.get("ambient_nontrivial_count"),
            "engine_nontrivial": summary.get("engine_nontrivial"),
            "overlay_nontrivial": summary.get("overlay_nontrivial"),
            "witness_separable": summary.get("witness_separable"),
            "guardrail_pass": summary.get("guardrail_pass"),
        }
    elif row_id == "hopf_torus_lego":
        homology_details = positive.get("gudhi_hopf_torus_homology", {}).get("details", {})
        betti_vector = homology_details.get("betti_numbers_long_lived") or homology_details.get("betti_at_alpha_sq_0.05") or []
        headline = {
            "all_pass": summary.get("all_pass"),
            "n_points_checked": positive.get("hopf_points_on_S3", {}).get("details", {}).get("n_points_checked"),
            "betti_vector": betti_vector,
            "z3_unsat_contractibility": negative.get("z3_unsat_contractibility", {}).get("details", {}).get("z3_result"),
        }
    elif row_id == "nested_torus_geometry":
        headline = {
            "all_pass": summary.get("all_pass"),
            "outer_xy_min": positive.get("nested_tori_have_strict_radial_separation", {}).get("outer_xy_min"),
            "inner_xy_max": positive.get("nested_tori_have_strict_radial_separation", {}).get("inner_xy_max"),
            "single_area": positive.get("torus_surface_area_matches_major_minor_formula", {}).get("single_area"),
        }
    elif row_id == "foundation_hopf_torus_geomstats_clifford":
        headline = {
            "all_pass": summary.get("all_pass"),
            "mean_delta": positive.get("geomstats_torus_frechet_mean_matches_componentwise_circular_mean", {}).get("mean_delta"),
            "metric_g11": positive.get("induced_torus_metric_and_area_match_exact_formulas", {}).get("metric", {}).get("g11"),
            "area": positive.get("induced_torus_metric_and_area_match_exact_formulas", {}).get("metric", {}).get("area"),
            "geodesic_distance": positive.get("s3_geodesic_distance_is_nontrivial_for_distinct_spinors", {}).get("distance"),
        }
    elif row_id == "torch_hopf_connection":
        headline = {
            "all_pass": summary.get("all_pass"),
            "P1_pass": positive.get("P1_s3_on_unit_sphere", {}).get("t=0.000_p=0.000", {}).get("pass"),
            "P2_pass": positive.get("P2_hopf_map_bloch_vector", {}).get("t=0.000_p=0.000", {}).get("pass"),
            "max_bloch_diff": positive.get("P2_hopf_map_bloch_vector", {}).get("t=0.785_p=0.000", {}).get("max_diff"),
            "e3nn_used": data.get("tool_manifest", {}).get("e3nn", {}).get("used"),
        }
    elif row_id == "weyl_nested_shell":
        headline = {
            "all_pass": summary.get("all_pass"),
            "beta0": positive.get("s3_unconstrained", {}).get("beta0"),
            "beta1": positive.get("s3_unconstrained", {}).get("beta1"),
            "z3_chirality_unsat": positive.get("z3_chirality_unsat", {}).get("z3_result"),
            "shell_dag_nodes": positive.get("rustworkx_shell_dag", {}).get("n_nodes"),
        }
    elif row_id == "graph_shell_geometry":
        headline = {
            "all_pass": summary.get("all_pass"),
            "cycle_rank": positive.get("nested_shell_chain_is_connected_and_acyclic", {}).get("cycle_rank"),
            "diameter": positive.get("nested_shell_chain_is_connected_and_acyclic", {}).get("diameter"),
            "zero_modes": positive.get("nested_shell_chain_is_connected_and_acyclic", {}).get("laplacian_zero_modes"),
        }
    elif row_id == "toponetx_hopf_crosscheck":
        headline = {
            "all_pass": summary.get("all_pass"),
            "beta0": summary.get("beta0"),
            "beta1": summary.get("beta1"),
            "chi": summary.get("chi"),
            "z3_unsat": negative.get("z3_unsat_contractible_chi0", {}).get("z3_result"),
        }
    else:
        headline = compact_summary_fields(data)

    return headline


def controller_route(role: str) -> str:
    return {
        "base_lego": "foundation",
        "composed_row": "stack_anchor",
        "graph_proof_lego": "graph_proof_bridge",
        "graph_proof_bridge": "graph_proof_bridge",
        "carrier_array": "carrier_compare",
        "carrier_compare": "carrier_compare",
        "ladder_audit": "ladder_audit",
        "legacy_anchor": "legacy_anchor",
    }.get(role, "unspecified")


def summarize_row(spec: dict[str, Any]) -> dict[str, Any]:
    data = load_json(spec["result_file"])
    row = {
        "id": spec["id"],
        "label": spec["label"],
        "role": spec["role"],
        "source_kind": spec["source_kind"],
        "level": spec["level"],
        "geometry_topology": spec["geometry_topology"],
        "scope_hint": spec["scope_hint"],
        "result_file": spec["result_file"].name,
        "result_exists": data is not None,
        "classification": data.get("classification") if isinstance(data, dict) else None,
        "all_pass": infer_all_pass(data),
        "controller_route": controller_route(spec["role"]),
        "lane_order": LANE_ORDER.get(spec["role"], 99),
        "used_tools": used_tools(data),
        "tool_manifest_used_count": len(used_tools(data)),
        "headline_metrics": extract_headline(spec["id"], data),
    }

    if data and isinstance(data.get("summary"), dict):
        row["result_summary"] = compact_summary_fields(data)
    else:
        row["result_summary"] = {}

    return row


def main() -> None:
    rows = [summarize_row(spec) for spec in ROW_SPECS]
    rows.sort(key=lambda row: (row["lane_order"], row["source_kind"], row["id"]))

    source_kind_counts = Counter(row["source_kind"] for row in rows)
    role_counts = Counter(row["role"] for row in rows)
    controller_route_counts = Counter(row["controller_route"] for row in rows)
    pass_count = sum(1 for row in rows if row["all_pass"])
    used_tool_counts = Counter(tool for row in rows for tool in row["used_tools"])

    summary = {
        "all_pass": pass_count == len(rows),
        "row_count": len(rows),
        "pass_count": pass_count,
        "fail_count": len(rows) - pass_count,
        "source_kind_counts": dict(source_kind_counts),
        "role_counts": dict(role_counts),
        "controller_route_counts": dict(controller_route_counts),
        "used_tool_counts": dict(sorted(used_tool_counts.items())),
        "new_lego_count": source_kind_counts.get("new_lego", 0),
        "new_composed_row_count": source_kind_counts.get("new_composed_row", 0),
        "new_bridge_row_count": source_kind_counts.get("new_bridge_row", 0),
        "legacy_anchor_count": source_kind_counts.get("legacy_geometry", 0),
        "scope_note": (
            "Controller-facing matrix for the Weyl/Hopf lane. New legos and bridge "
            "rows appear first; older directly relevant geometry anchors are kept "
            "at the bottom as reference surfaces."
        ),
    }

    out = {
        "name": "weyl_geometry_lab_matrix",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": summary,
        "rows": rows,
    }

    out_path = RESULT_DIR / "weyl_geometry_lab_matrix_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
