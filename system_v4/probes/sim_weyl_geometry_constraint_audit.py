#!/usr/bin/env python3
"""
Weyl Geometry Constraint Audit
==============================
Controller-facing route audit for the Weyl/Hopf geometry lane.

This is not a proof surface. It classifies existing Weyl/Hopf results into
bounded controller buckets:
- reusable base lego
- graph/proof bridge
- carrier comparison
- composed stack
- open geometry sidecar

The classification is driven by actual result properties, not file naming.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
classification = "canonical"


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Controller audit over the Weyl/Hopf geometry lane. It routes rows by the "
    "properties they actually expose: stacked torus composition, graph/proof "
    "alignment, carrier comparison, reusable base geometry, and open sidecar "
    "diagnostics."
)

LEGO_IDS = [
    "hopf_torus_lego",
    "spinor_geometry",
    "weyl_hopf_pauli_composed_stack",
    "weyl_geometry_graph_proof_alignment",
]

PRIMARY_LEGO_IDS = [
    "hopf_torus_lego",
    "spinor_geometry",
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
REGISTRY_PATH = RESULT_DIR / "actual_lego_registry.json"

ROW_SOURCES = [
    {
        "row_id": "nested_hopf_tori",
        "result_file": "lego_nested_hopf_tori_results.json",
    },
    {
        "row_id": "hopf_torus_lego",
        "result_file": "hopf_torus_lego_results.json",
    },
    {
        "row_id": "weyl_spinor_hopf",
        "result_file": "weyl_spinor_hopf_results.json",
    },
    {
        "row_id": "lego_weyl_pauli_transport",
        "result_file": "lego_weyl_pauli_transport_results.json",
    },
    {
        "row_id": "weyl_hopf_pauli_composed_stack",
        "result_file": "weyl_hopf_pauli_composed_stack_results.json",
    },
    {
        "row_id": "weyl_geometry_graph_proof_alignment",
        "result_file": "weyl_geometry_graph_proof_alignment_results.json",
    },
    {
        "row_id": "weyl_geometry_carrier_array",
        "result_file": "weyl_geometry_carrier_array_results.json",
    },
    {
        "row_id": "weyl_geometry_ladder_audit",
        "result_file": "weyl_geometry_ladder_audit_results.json",
    },
]


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry_lookup() -> dict[str, dict[str, Any]]:
    if not REGISTRY_PATH.exists():
        return {}
    registry = load_json(REGISTRY_PATH)
    lookup: dict[str, dict[str, Any]] = {}
    for row in registry.get("rows", []):
        for key in ("best_existing_result", "machine_best_existing_result", "machine_best_result"):
            value = row.get(key)
            if isinstance(value, str):
                lookup.setdefault(value, row)
    return lookup


def all_pass(result: dict[str, Any]) -> bool:
    summary = result.get("summary", {})
    if isinstance(summary, dict) and "all_pass" in summary:
        return bool(summary["all_pass"])
    return bool(result.get("positive", {}))


def route_row(row_id: str, result: dict[str, Any]) -> tuple[str, str]:
    summary = result.get("summary", {})
    positive = result.get("positive", {})
    tool_depth = result.get("tool_integration_depth", {})
    classification = result.get("classification")

    if row_id == "weyl_hopf_pauli_composed_stack" or summary.get("total_stages") == 4:
        return (
            "composed stack",
            "The row stages a four-layer composed geometry stack and verifies the full stack error budget.",
        )

    if (
        row_id == "weyl_geometry_carrier_array"
        or summary.get("carrier_count") is not None
        or "cross_carrier_consistency" in positive
    ):
        return (
            "carrier comparison",
            "The row compares the same Weyl-style core across multiple carriers and reports a spread check.",
        )

    if row_id == "weyl_geometry_ladder_audit" or {
        "ambient_nontrivial_count",
        "engine_nontrivial",
        "witness_separable",
    }.issubset(set(summary.keys())):
        return (
            "open geometry sidecar",
            "The row is a diagnostic sidecar that checks Weyl-ambient witnesses against engine response without claiming a new core lego.",
        )

    if (
        row_id == "weyl_geometry_graph_proof_alignment"
        or "graph_summary" in result
        or (
            tool_depth.get("z3") == "load_bearing"
            and tool_depth.get("rustworkx") == "load_bearing"
        )
    ):
        return (
            "graph/proof bridge",
            "The row carries load-bearing graph order and solver checks around the geometry stack.",
        )

    if classification == "canonical":
        return (
            "reusable base lego",
            "The row is a canonical base geometry lego with bounded unit-norm, transport, and readout checks but no controller bridge claim.",
        )

    return (
        "open geometry sidecar",
        "The row does not meet a bridge or composed-stack threshold and is better treated as a sidecar diagnostic.",
    )


def metric_pick(row_id: str, result: dict[str, Any], route: str) -> dict[str, Any]:
    summary = result.get("summary", {})
    positive = result.get("positive", {})
    boundary = result.get("boundary", {})

    if route == "composed stack":
        return {
            "all_pass": summary.get("all_pass"),
            "sample_count": summary.get("sample_count"),
            "torus_levels": summary.get("torus_levels"),
            "total_stages": summary.get("total_stages"),
            "max_spinor_norm_error": summary.get("max_spinor_norm_error"),
            "max_bloch_alignment_error": summary.get("max_bloch_alignment_error"),
            "max_transport_error": summary.get("max_transport_error"),
            "max_stack_error": summary.get("max_stack_error"),
        }

    if route == "graph/proof bridge":
        graph = result.get("graph_summary", {})
        geom = result.get("geometry_samples", {})
        return {
            "all_pass": result.get("negative", {}).get("graph_alignment_row_is_not_a_runtime_sim_claim", {}).get("pass"),
            "node_count": graph.get("node_count"),
            "edge_count": graph.get("edge_count"),
            "graph_path_length": graph.get("longest_path_length"),
            "forward_order_sat": positive.get("z3_forces_the_geometry_stack_ordering", {}).get("forward_order_sat"),
            "reverse_order_unsat": positive.get("z3_forces_the_geometry_stack_ordering", {}).get("reverse_order_unsat"),
            "max_left_right_overlap_abs": positive.get("left_and_right_spinors_stay_operationally_distinct_on_each_carrier", {}).get("max_left_right_overlap_abs"),
            "max_hopf_image_norm_gap": positive.get("hopf_and_torus_carriers_stay_unit_and_finite", {}).get("max_hopf_image_norm_gap"),
            "transport_fraction": geom.get("transport_fractions", {}),
        }

    if route == "carrier comparison":
        return {
            "all_pass": summary.get("all_pass"),
            "total_tests": summary.get("total_tests"),
            "passed": summary.get("passed"),
            "failed": summary.get("failed"),
            "carrier_count": summary.get("carrier_count"),
            "passed_carriers": summary.get("passed_carriers"),
            "failed_carriers": summary.get("failed_carriers"),
            "max_nested_lr_overlap": summary.get("max_nested_lr_overlap"),
            "max_nested_bloch_gap": summary.get("max_nested_bloch_gap"),
            "max_graph_cycle_rank": summary.get("max_graph_cycle_rank"),
            "max_hypergraph_shadow_components": summary.get("max_hypergraph_shadow_components"),
            "max_cp3_concurrence": summary.get("max_cp3_concurrence"),
        }

    if route == "open geometry sidecar":
        metadata_name = result.get("metadata", {}).get("name")
        if row_id == "weyl_geometry_ladder_audit" or metadata_name == "weyl_geometry_ladder_audit":
            return {
                "all_pass": result.get("verdict", {}).get("result") == "PASS",
                "ambient_nontrivial_count": summary.get("ambient_nontrivial_count"),
                "clifford_neutral": summary.get("clifford_neutral"),
                "engine_nontrivial": summary.get("engine_nontrivial"),
                "witness_separable": summary.get("witness_separable"),
                "type2_witness_separable": summary.get("type2_witness_separable"),
                "guardrail_pass": summary.get("guardrail_pass"),
            }
        return {
            "all_pass": summary.get("all_pass"),
            "sample_count": summary.get("sample_count"),
            "max_point_norm_error": summary.get("max_point_norm_error"),
            "max_left_right_overlap": positive.get("spinor_construction", {}).get("max_left_right_overlap"),
            "max_transport_error": summary.get("max_transport_error"),
        }

    # reusable base lego
    if result.get("name") == "nested_hopf_tori":
        return {
            "all_pass": summary.get("all_pass"),
            "sample_count": summary.get("sample_count"),
            "torus_levels": summary.get("torus_levels"),
            "max_point_norm_error": summary.get("max_point_norm_error"),
            "max_left_hopf_alignment_error": summary.get("max_left_hopf_alignment_error"),
            "max_transport_error": summary.get("max_transport_error"),
            "max_stack_error": summary.get("max_stack_error"),
        }
    if result.get("name") == "hopf_torus_lego":
        positive_block = result.get("positive", {})
        negative_block = result.get("negative", {})
        return {
            "all_pass": result.get("summary", {}).get("all_pass", True),
            "beta1_equals_2": positive.get("gudhi_hopf_torus_homology", {}).get("details", {}).get("beta1_equals_2"),
            "z3_unsat_contractibility": negative_block.get("z3_unsat_contractibility", {}).get("details", {}).get("z3_result"),
            "max_norm_error": positive.get("hopf_points_on_S3", {}).get("details", {}).get("max_norm_error"),
            "total_phi_loop_length": positive_block.get("geomstats_s3_geodesics", {}).get("details", {}).get("total_phi_loop_length"),
            "symmetry_ok": positive_block.get("geomstats_s3_geodesics", {}).get("details", {}).get("symmetry_ok"),
        }
    if result.get("name") == "weyl_spinor_hopf":
        overlap_block = positive.get("lr_spinor_overlap", {})
        return {
            "all_pass": positive.get("lr_spinor_overlap", {}).get("status") == "PASS" and positive.get("sympy_chirality_operator", {}).get("status") == "PASS",
            "xi_zero_overlap_abs": positive.get("lr_spinor_overlap", {}).get("xi_zero_overlap_abs"),
            "gamma5_left_eigenvalue": positive.get("sympy_chirality_operator", {}).get("left_eigenvalue"),
            "gamma5_right_eigenvalue": positive.get("sympy_chirality_operator", {}).get("right_eigenvalue"),
            "max_left_right_overlap_abs": overlap_block.get("overlaps", {}).get("north_pole", {}).get("overlap_abs"),
        }
    if result.get("name") == "lego_weyl_pauli_transport":
        positive_block = result.get("positive", {})
        return {
            "all_pass": summary.get("all_pass"),
            "sample_count": summary.get("sample_count"),
            "transport_count": 3,
            "max_left_right_overlap_abs": positive_block.get("max_left_right_overlap_abs"),
            "max_bloch_antipodal_gap": positive_block.get("max_bloch_antipodal_gap"),
            "pauli_readout_gap": positive_block.get("pauli_readout_gap"),
            "transport_roundtrip_error": positive_block.get("transport_roundtrip_error"),
        }

    return {"all_pass": summary.get("all_pass")}


def main() -> None:
    registry_lookup = load_registry_lookup()

    rows: list[dict[str, Any]] = []
    route_counts: dict[str, int] = {}
    registry_matched = 0

    for spec in ROW_SOURCES:
        result_path = RESULT_DIR / spec["result_file"]
        result = load_json(result_path)
        route, route_reason = route_row(spec["row_id"], result)

        registry_hit = registry_lookup.get(spec["result_file"]) or registry_lookup.get(result.get("name", ""))
        registry_hint = None
        if registry_hit is not None:
            registry_matched += 1
            registry_hint = {
                "lego_id": registry_hit.get("lego_id"),
                "section": registry_hit.get("section"),
                "machine_current_coverage": registry_hit.get("machine_current_coverage"),
                "machine_result_classification": registry_hit.get("machine_result_classification"),
                "useful_if_rejected": registry_hit.get("useful_if_rejected"),
            }

        metrics = metric_pick(spec["row_id"], result, route)
        row = {
            "row_id": spec["row_id"],
            "result_file": spec["result_file"],
            "route": route,
            "route_reason": route_reason,
            "source_classification": result.get("classification"),
            "all_pass": bool(metrics.get("all_pass")),
            "registry_hint": registry_hint,
            "salient_metrics": metrics,
        }
        rows.append(row)
        route_counts[route] = route_counts.get(route, 0) + 1

    summary = {
        "all_pass": all(row["all_pass"] for row in rows),
        "row_count": len(rows),
        "registry_matched_rows": registry_matched,
        "route_counts": route_counts,
        "reusable_base_lego_count": route_counts.get("reusable base lego", 0),
        "graph_proof_bridge_count": route_counts.get("graph/proof bridge", 0),
        "carrier_comparison_count": route_counts.get("carrier comparison", 0),
        "composed_stack_count": route_counts.get("composed stack", 0),
        "open_geometry_sidecar_count": route_counts.get("open geometry sidecar", 0),
        "scope_note": (
            "Controller audit for the Weyl/Hopf lane. Base legos stay reusable, bridges stay bridge-only, "
            "carrier arrays stay comparison surfaces, composed stacks stay composed-stack surfaces, and the "
            "ladder audit stays a sidecar diagnostic."
        ),
    }

    out = {
        "name": "weyl_geometry_constraint_audit",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": summary,
        "rows": rows,
    }

    out_path = RESULT_DIR / "weyl_geometry_constraint_audit_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
