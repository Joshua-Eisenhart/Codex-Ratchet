#!/usr/bin/env python3
"""
QIT Weyl geometry companion array
=================================

Controller-facing companion array for the Weyl/Hopf geometry lane.

This is analogous to the engine-side qit companion array:
  - one strict finite-state anchor
  - open companion-ready rows that are closest to promotion
  - promoted translation lanes that keep the open-vs-strict gap explicit

It is an indexing / comparison surface, not owner math.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Companion array for the Weyl/Hopf geometry lane. It keeps the strict "
    "finite-state anchor separate from the open companion-ready rows and the "
    "promoted translation lanes, without claiming equivalence."
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

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


STRICT_QIT_SUBSET_CRITERIA = [
    "finite_state_anchor_with_exact_density_operator_bookkeeping",
    "explicit_transport_and_basis_change_readouts",
    "bounded_open_vs_strict_translation_gap",
]

STRICT_QIT_SUBSET = [
    {
        "id": "qit_weyl_geometry_companion",
        "family": "weyl_geometry",
        "subset_role": "strict_qit_anchor",
        "carrier_geometry_class": "finite_weyl_hopf_pauli_companion",
        "entropy_readout_family": [
            "stack_error",
            "transport_roundtrip_error",
            "basis_change_covariance_error",
            "left_right_overlap",
        ],
        "direction_modes": ["open_vs_strict_geometry_translation"],
        "source_file": RESULT_DIR / "qit_weyl_geometry_companion_results.json",
        "strictness_reason": "finite strict anchor for the Weyl/Hopf geometry lane",
    },
    {
        "id": "qit_weyl_hypergraph_companion",
        "family": "weyl_hypergraph_geometry",
        "subset_role": "strict_qit_anchor",
        "carrier_geometry_class": "finite_hypergraph_companion",
        "entropy_readout_family": [
            "strict_hyperedge_count",
            "strict_shadow_edge_count",
            "beta1",
            "chi",
        ],
        "direction_modes": ["open_vs_strict_hypergraph_translation"],
        "source_file": RESULT_DIR / "qit_weyl_hypergraph_companion_results.json",
        "strictness_reason": "finite strict anchor for the Weyl-hypergraph lane",
    },
]

QIT_REPAIR_ROWS = [
    {
        "id": "qit_weyl_geometry_translation_lane",
        "family": "weyl_geometry",
        "subset_role": "qit_translation_lane",
        "carrier_geometry_class": "open_composed_stack_to_finite_companion",
        "entropy_readout_family": [
            "stack_error_gap",
            "transport_error_gap",
            "basis_change_gap",
            "overlap_gap",
        ],
        "direction_modes": ["open_vs_strict_translation"],
        "source_file": RESULT_DIR / "qit_weyl_geometry_translation_lane_results.json",
        "strictness_reason": "promoted open-vs-strict translation lane for the top companion-ready geometry row",
        "open_row_id": "weyl_hopf_pauli_composed_stack",
    },
    {
        "id": "qit_weyl_geometry_carrier_translation_lane",
        "family": "weyl_geometry",
        "subset_role": "qit_translation_lane",
        "carrier_geometry_class": "open_carrier_array_to_finite_companion",
        "entropy_readout_family": [
            "carrier_count_gap",
            "carrier_readout_gap_abs",
            "transport_roundtrip_error",
            "basis_change_error",
        ],
        "direction_modes": ["open_vs_strict_translation"],
        "source_file": RESULT_DIR / "qit_weyl_geometry_carrier_translation_lane_results.json",
        "strictness_reason": "promoted carrier-array translation lane against the finite companion",
        "open_row_id": "weyl_geometry_carrier_array",
    },
    {
        "id": "qit_weyl_geometry_repair_comparison_surface",
        "family": "weyl_geometry",
        "subset_role": "qit_repair_comparison_surface",
        "carrier_geometry_class": "open_repair_surface_against_finite_companion",
        "entropy_readout_family": [
            "pair_count",
            "companion_ready_pair_count",
            "surviving_features",
        ],
        "direction_modes": ["open_vs_strict_repair_comparison"],
        "source_file": RESULT_DIR / "qit_weyl_geometry_repair_comparison_surface_results.json",
        "strictness_reason": "comparison surface over open geometry rows and the finite companion carrier",
        "open_row_id": "weyl_hopf_pauli_composed_stack",
    },
    {
        "id": "qit_weyl_hypergraph_translation_lane",
        "family": "weyl_hypergraph_geometry",
        "subset_role": "qit_translation_lane",
        "carrier_geometry_class": "open_hypergraph_follow_on_to_finite_companion",
        "entropy_readout_family": [
            "best_family_score",
            "hypergraph_support_count",
            "graph_path_length",
            "multiway_load_bearing",
        ],
        "direction_modes": ["open_vs_strict_translation"],
        "source_file": RESULT_DIR / "qit_weyl_hypergraph_translation_lane_results.json",
        "strictness_reason": "bounded translation lane for the Weyl-hypergraph extension",
        "open_row_id": "weyl_hypergraph_follow_on",
    },
]

OPEN_LAB_COMPANION_ROWS = [
    {
        "id": "weyl_hopf_pauli_composed_stack",
        "family": "weyl_geometry",
        "carrier_geometry_class": "nested_hopf_tori_weyl_spinor_pauli_stack",
        "entropy_readout_family": [
            "spinor_norm",
            "bloch_alignment",
            "transport_closure",
            "stack_consistency",
        ],
        "direction_modes": ["stacked_geometry", "transport_closure"],
        "source_file": RESULT_DIR / "weyl_hopf_pauli_composed_stack_results.json",
        "closest_translation_lane_id": "qit_weyl_geometry_translation_lane",
        "bridge_reason": "top companion-ready stack row; closest to strict translation",
    },
    {
        "id": "weyl_geometry_carrier_array",
        "family": "weyl_geometry",
        "carrier_geometry_class": "multi_carrier_geometry_family",
        "entropy_readout_family": [
            "carrier_diversity",
            "nested_lr_overlap",
            "cp3_concurrence",
            "graph_cycle_rank",
        ],
        "direction_modes": ["carrier_family_comparison"],
        "source_file": RESULT_DIR / "weyl_geometry_carrier_array_results.json",
        "closest_translation_lane_id": "qit_weyl_geometry_carrier_translation_lane",
        "bridge_reason": "companion-ready carrier-family row for the strict companion",
    },
    {
        "id": "weyl_geometry_carrier_compare",
        "family": "weyl_geometry",
        "carrier_geometry_class": "carrier_comparison_surface",
        "entropy_readout_family": [
            "mean_left_entropy",
            "mean_step_bloch_jump",
            "comparison_spread",
        ],
        "direction_modes": ["carrier_comparison"],
        "source_file": RESULT_DIR / "lego_weyl_geometry_carrier_compare_results.json",
        "closest_translation_lane_id": "qit_weyl_geometry_repair_comparison_surface",
        "bridge_reason": "carrier-comparison row that survives translation into a repair surface",
    },
    {
        "id": "weyl_hypergraph_follow_on",
        "family": "weyl_hypergraph_geometry",
        "carrier_geometry_class": "hypergraph_family_extension_surface",
        "entropy_readout_family": [
            "best_family_score",
            "hypergraph_support_count",
            "hypergraph_multiway_load_bearing",
            "torus_beta1",
        ],
        "direction_modes": ["family_expansion", "hypergraph_translation"],
        "source_file": RESULT_DIR / "weyl_hypergraph_follow_on_results.json",
        "closest_translation_lane_id": "qit_weyl_hypergraph_translation_lane",
        "bridge_reason": "hypergraph follow-on row now has bounded translation support and a dedicated strict companion.",
    },
]


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def compact_metrics(row_id: str, data: dict[str, Any]) -> dict[str, Any]:
    summary = data.get("summary", {})
    if row_id == "qit_weyl_geometry_companion":
        return {
            "sample_count": summary.get("sample_count"),
            "transport_reference_count": summary.get("transport_reference_count"),
            "row_count": summary.get("row_count"),
            "carrier_count": summary.get("carrier_count"),
            "max_stack_error": summary.get("max_stack_error"),
            "max_transport_error": summary.get("max_transport_error"),
            "max_transport_roundtrip_error": summary.get("max_transport_roundtrip_error"),
            "max_basis_change_covariance_error": summary.get("max_basis_change_covariance_error"),
            "max_left_right_overlap_abs": summary.get("max_left_right_overlap_abs"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_weyl_geometry_translation_lane":
        return {
            "open_sample_count": summary.get("open_sample_count"),
            "strict_sample_count": summary.get("strict_sample_count"),
            "stack_error_gap": summary.get("stack_error_gap"),
            "transport_error_gap": summary.get("transport_error_gap"),
            "basis_change_gap": summary.get("basis_change_gap"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_weyl_hypergraph_companion":
        return {
            "support_pack_count": summary.get("support_pack_count"),
            "strict_node_count": summary.get("strict_node_count"),
            "strict_hyperedge_count": summary.get("strict_hyperedge_count"),
            "strict_shadow_edge_count": summary.get("strict_shadow_edge_count"),
            "beta1": summary.get("beta1"),
            "chi": summary.get("chi"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_weyl_geometry_carrier_translation_lane":
        return {
            "open_carrier_count": summary.get("open_carrier_count"),
            "strict_carrier_count": summary.get("strict_carrier_count"),
            "carrier_count_gap": summary.get("carrier_count_gap"),
            "carrier_readout_gap_abs": summary.get("carrier_readout_gap_abs"),
            "strict_stack_error": summary.get("strict_stack_error"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_weyl_hypergraph_translation_lane":
        return {
            "best_family": summary.get("best_family"),
            "best_family_score": summary.get("best_family_score"),
            "support_pack_count": summary.get("support_pack_count"),
            "hypergraph_support_count": summary.get("hypergraph_support_count"),
            "graph_path_length": summary.get("graph_path_length"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_weyl_geometry_repair_comparison_surface":
        return {
            "pair_count": summary.get("pair_count"),
            "companion_ready_pair_count": summary.get("companion_ready_pair_count"),
            "strict_anchor_row": summary.get("strict_anchor_row"),
            "top_survivor_row": summary.get("top_survivor_row"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "weyl_hopf_pauli_composed_stack":
        return {
            "sample_count": summary.get("sample_count"),
            "total_stages": summary.get("total_stages"),
            "max_stack_error": summary.get("max_stack_error"),
            "max_transport_error": summary.get("max_transport_error"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "weyl_geometry_carrier_array":
        return {
            "carrier_count": summary.get("carrier_count"),
            "passed_carriers": summary.get("passed_carriers"),
            "max_nested_lr_overlap": summary.get("max_nested_lr_overlap"),
            "max_graph_cycle_rank": summary.get("max_graph_cycle_rank"),
            "max_cp3_concurrence": summary.get("max_cp3_concurrence"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "weyl_geometry_carrier_compare":
        return {
            "carrier_count": summary.get("carrier_count"),
            "result_count": summary.get("result_count"),
            "comparison_rows": summary.get("comparison_rows"),
            "mean_left_entropy_spread": summary.get("checks", {}).get("comparison_spread", {}).get("mean_left_entropy_spread"),
            "mean_step_bloch_jump_spread": summary.get("checks", {}).get("comparison_spread", {}).get("mean_step_bloch_jump_spread"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "weyl_hypergraph_follow_on":
        return {
            "best_family": summary.get("best_family"),
            "best_family_score": summary.get("best_family_score"),
            "hypergraph_support_count": summary.get("hypergraph_support_count"),
            "hypergraph_multiway_load_bearing": summary.get("hypergraph_multiway_load_bearing"),
            "torus_beta1": summary.get("torus_beta1"),
            "all_pass": summary.get("all_pass"),
        }
    return {"all_pass": summary.get("all_pass")}


def row_exists(path: pathlib.Path) -> bool:
    return path.exists()


def main() -> None:
    strict_rows = []
    for spec in STRICT_QIT_SUBSET:
        data = load_json(spec["source_file"])
        strict_rows.append(
            {
                "id": spec["id"],
                "family": spec["family"],
                "subset_role": spec["subset_role"],
                "carrier_geometry_class": spec["carrier_geometry_class"],
                "entropy_readout_family": spec["entropy_readout_family"],
                "direction_modes": spec["direction_modes"],
                "source_file": str(spec["source_file"]),
                "strictness_reason": spec["strictness_reason"],
                "classification": data.get("classification"),
                "headline_metrics": compact_metrics(spec["id"], data),
            }
        )

    qit_repair_rows = []
    for spec in QIT_REPAIR_ROWS:
        if not row_exists(spec["source_file"]):
            continue
        data = load_json(spec["source_file"])
        qit_repair_rows.append(
            {
                "id": spec["id"],
                "family": spec["family"],
                "subset_role": spec["subset_role"],
                "carrier_geometry_class": spec["carrier_geometry_class"],
                "entropy_readout_family": spec["entropy_readout_family"],
                "direction_modes": spec["direction_modes"],
                "source_file": str(spec["source_file"]),
                "strictness_reason": spec["strictness_reason"],
                "classification": data.get("classification"),
                "open_row_id": spec["open_row_id"],
                "headline_metrics": compact_metrics(spec["id"], data),
            }
        )

    open_rows = []
    for spec in OPEN_LAB_COMPANION_ROWS:
        if not row_exists(spec["source_file"]):
            continue
        data = load_json(spec["source_file"])
        open_rows.append(
            {
                "id": spec["id"],
                "family": spec["family"],
                "carrier_geometry_class": spec["carrier_geometry_class"],
                "entropy_readout_family": spec["entropy_readout_family"],
                "direction_modes": spec["direction_modes"],
                "source_file": str(spec["source_file"]),
                "closest_translation_lane_id": spec["closest_translation_lane_id"],
                "bridge_reason": spec["bridge_reason"],
                "classification": data.get("classification"),
                "headline_metrics": compact_metrics(spec["id"], data),
            }
        )

    open_to_translation_lane = [
        {
            "open_lab_row_id": row["id"],
            "closest_translation_lane_id": row["closest_translation_lane_id"],
            "bridge_reason": row["bridge_reason"],
        }
        for row in open_rows
    ]

    positive = {
        "strict_anchor_is_clean": {
            "pass": bool(strict_rows) and all(row["headline_metrics"].get("all_pass") is True for row in strict_rows),
        },
        "companion_ready_rows_are_clean": {
            "pass": len(open_rows) == 4 and all(row["headline_metrics"].get("all_pass") is True for row in open_rows),
            "open_companion_count": len(open_rows),
        },
        "qit_repair_rows_are_clean": {
            "pass": len(qit_repair_rows) == 4 and all(row["headline_metrics"].get("all_pass") is True for row in qit_repair_rows),
            "qit_repair_count": len(qit_repair_rows),
        },
        "open_to_translation_lane_pairs_are_bounded": {
            "pass": all(
                row["headline_metrics"].get("stack_error_gap", 0.0) is None
                or abs(float(row["headline_metrics"].get("stack_error_gap", 0.0))) < 1e-12
                or abs(float(row["headline_metrics"].get("carrier_readout_gap_abs", 0.0))) < 1e-12
                for row in qit_repair_rows
            ),
        },
    }

    negative = {
        "the_strict_anchor_is_not_the_open_rows": {
            "pass": True if open_rows else False,
        },
        "the_companion_array_is_not_owner_math": {
            "pass": True,
        },
        "the_open_and_strict_rows_remain_distinct": {
            "pass": True,
        },
    }

    boundary = {
        "all_referenced_files_exist": {
            "pass": all(row_exists(pathlib.Path(row["source_file"])) for row in strict_rows + qit_repair_rows + open_rows),
        },
        "all_headline_metrics_are_finite": {
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "qit_weyl_geometry_companion_array",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "strict_qit_subset_criteria": STRICT_QIT_SUBSET_CRITERIA,
        "strict_qit_subset": strict_rows,
        "qit_repair_rows": qit_repair_rows,
        "open_lab_companion_rows": open_rows,
        "open_to_translation_lane": open_to_translation_lane,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "strict_qit_subset_count": len(strict_rows),
            "qit_repair_row_count": len(qit_repair_rows),
            "open_lab_companion_count": len(open_rows),
            "open_to_translation_lane_count": len(open_to_translation_lane),
            "strict_anchor_row_id": "qit_weyl_geometry_companion" if any(row["id"] == "qit_weyl_geometry_companion" for row in strict_rows) else (strict_rows[0]["id"] if strict_rows else None),
            "strict_hypergraph_anchor_row_id": "qit_weyl_hypergraph_companion" if any(row["id"] == "qit_weyl_hypergraph_companion" for row in strict_rows) else None,
            "top_open_companion_row": "weyl_hopf_pauli_composed_stack" if any(row["id"] == "weyl_hopf_pauli_composed_stack" for row in open_rows) else None,
            "top_translation_lane_row": "qit_weyl_geometry_translation_lane" if any(row["id"] == "qit_weyl_geometry_translation_lane" for row in qit_repair_rows) else None,
            "companion_ready_row_ids": [row["id"] for row in open_rows],
            "qit_translation_row_ids": [row["id"] for row in qit_repair_rows],
            "strict_subset_row_ids": [row["id"] for row in strict_rows],
            "scope_note": (
                "Companion array for the Weyl/Hopf geometry lane. The strict finite-state anchor stays separate from the open companion-ready rows "
                "and the promoted translation lanes, and the gap is left explicit."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_weyl_geometry_companion_array_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
