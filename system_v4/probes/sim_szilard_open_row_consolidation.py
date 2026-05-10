#!/usr/bin/env python3
"""Consolidate open Szilard rows into successor and graveyard constraints."""

from __future__ import annotations

import json
import pathlib
from typing import Any


CLASSIFICATION = "canonical"
classification = CLASSIFICATION
divergence_log = (
    "Controller consolidation for four open Szilard rows. It preserves the "
    "source rows as negative/open evidence, accepts only successor or graveyard "
    "constraints with passing receipts, and does not promote QIT, GStack, axis, "
    "bridge, nonclassical, or runtime-engine claims."
)

LEGO_IDS = [
    "szilard_engine",
    "measurement_feedback",
    "record_lifetime",
    "reset_signal",
    "topology_entropy",
    "graveyard_variant",
]
PRIMARY_LEGO_IDS = ["szilard_engine", "measurement_feedback", "topology_entropy"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads exact Szilard source and successor receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical result and visualizer paths"},
}
TOOL_INTEGRATION_DEPTH = {"json": "load_bearing", "pathlib": "load_bearing"}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"

SOURCE_ROWS = {
    "szilard_ordering_sensitivity": {
        "source_script": "sim_szilard_ordering_sensitivity_sweep.py",
        "receipt": "szilard_ordering_sensitivity_sweep_results.json",
        "successor_script": "sim_szilard_ordering_nonmonotone_noise_successor.py",
        "successor": "szilard_ordering_nonmonotone_noise_successor_results.json",
        "survived": "local ordering signal; stronger feedback; high-noise survival as tuning clue",
        "failed": "low-noise monotonicity and clean high-noise failure prior",
        "constraint": "ordering can couple only as nonmonotone noise/feedback evidence, not as strict monotone axis",
    },
    "szilard_substep_refinement_sweep": {
        "source_script": "sim_szilard_substep_refinement_sweep.py",
        "receipt": "szilard_substep_refinement_sweep_results.json",
        "successor_script": "sim_szilard_substep_ordering_reset_successor.py",
        "successor": "szilard_substep_ordering_reset_successor_results.json",
        "survived": "ordering-margin and reset-signal refinement",
        "failed": "measurement mutual-information high-threshold claim",
        "constraint": "substep coupling must carry measurement-information bottleneck explicitly",
    },
    "szilard_record_reset_repair_sweep": {
        "source_script": "sim_szilard_record_reset_repair_sweep.py",
        "receipt": "szilard_record_reset_repair_sweep_results.json",
        "successor_script": "sim_szilard_record_lifetime_repair_successor.py",
        "successor": "szilard_record_lifetime_repair_successor_results.json",
        "survived": "repair score, record lifetime, low-noise ordering, separate reset-axis reroute",
        "failed": "reset swing on this carrier as a direct strict target",
        "constraint": "record/reset coupling must split lifetime survival from reset-axis repair",
    },
    "szilard_topology_entropy_array": {
        "source_script": "sim_szilard_topology_entropy_array.py",
        "receipt": "szilard_topology_entropy_array_results.json",
        "successor_script": "sim_szilard_topology_positive_diversity_successor.py",
        "successor": "szilard_topology_positive_diversity_successor_results.json",
        "survived": "positive ordering margins across tested topology family; asymmetric carrier is best local topology",
        "failed": "weak-topology claim",
        "constraint": "topology can couple as positive diversity evidence, not as GStack or nonclassical admission",
    },
}


def load(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def summary_all_pass(receipt: dict[str, Any]) -> bool | None:
    return (receipt.get("summary") or {}).get("all_pass")


def receipt_fresh(script_name: str, receipt_name: str) -> bool:
    script_path = PROBE_DIR / script_name
    receipt_path = RESULT_DIR / receipt_name
    if not script_path.exists() or not receipt_path.exists():
        return False
    return receipt_path.stat().st_mtime >= script_path.stat().st_mtime


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": result["name"],
        "summary": result["summary"],
        "coupling_constraints": result["coupling_constraints"],
        "rows": result["rows"],
    }
    js = "window.SZILARD_OPEN_ROW_CONSOLIDATION_DATA = " + json.dumps(payload, indent=2, default=str) + ";\n"
    (VIS_DIR / "szilard-open-row-consolidation-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    graveyard = load("szilard_open_failure_graveyard_results.json")
    rows: list[dict[str, Any]] = []
    for row_id, spec in SOURCE_ROWS.items():
        source = load(spec["receipt"])
        successor = load(spec["successor"])
        source_open = summary_all_pass(source) is False
        successor_pass = summary_all_pass(successor) is True
        successor_blocks_promotion = (successor.get("summary") or {}).get("qit_or_axis_promotion_allowed") is False
        source_fresh = receipt_fresh(spec["source_script"], spec["receipt"])
        successor_fresh = receipt_fresh(spec["successor_script"], spec["successor"])
        rows.append(
            {
                "row_id": row_id,
                "source_script": str(PROBE_DIR / spec["source_script"]),
                "source_receipt": str(RESULT_DIR / spec["receipt"]),
                "source_all_pass": summary_all_pass(source),
                "source_receipt_fresh": source_fresh,
                "successor_script": str(PROBE_DIR / spec["successor_script"]),
                "successor_receipt": str(RESULT_DIR / spec["successor"]),
                "successor_name": successor.get("name"),
                "successor_all_pass": summary_all_pass(successor),
                "successor_receipt_fresh": successor_fresh,
                "source_preserved_negative": source_open,
                "successor_blocks_promotion": successor_blocks_promotion,
                "survived": spec["survived"],
                "failed_or_killed": spec["failed"],
                "coupling_constraint": spec["constraint"],
                "accepted": source_open
                and successor_pass
                and successor_blocks_promotion
                and source_fresh
                and successor_fresh,
            }
        )

    coupling_constraints = {
        "ordering_to_substep": {
            "allowed": True,
            "constraint": "carry nonmonotone noise/feedback response into substep ordering and reset-signal repair",
        },
        "substep_to_record_reset": {
            "allowed": True,
            "constraint": "do not collapse measurement-information bottleneck into record-survival or reset-swing claims",
        },
        "record_reset_to_topology": {
            "allowed": True,
            "constraint": "topology diversity can host surviving ordering carriers but cannot close reset-axis or admission gaps",
        },
        "topology_to_qit_or_gstack": {
            "allowed": False,
            "constraint": "no QIT, GStack, axis, bridge, nonclassical, or runtime-engine promotion follows from this lane",
        },
    }

    positive = {
        "all_four_source_rows_are_preserved_negative": {
            "source_row_count": len(rows),
            "source_open_count": sum(row["source_preserved_negative"] for row in rows),
            "pass": len(rows) == 4 and all(row["source_preserved_negative"] for row in rows),
        },
        "all_four_rows_have_passing_successor_receipts": {
            "successor_pass_count": sum(row["successor_all_pass"] is True for row in rows),
            "pass": all(row["successor_all_pass"] is True for row in rows),
        },
        "all_four_source_and_successor_receipts_are_fresh": {
            "fresh_source_count": sum(row["source_receipt_fresh"] for row in rows),
            "fresh_successor_count": sum(row["successor_receipt_fresh"] for row in rows),
            "pass": all(row["source_receipt_fresh"] and row["successor_receipt_fresh"] for row in rows),
        },
        "graveyard_receipt_preserves_killed_and_survived_variants": {
            "graveyard_all_pass": summary_all_pass(graveyard),
            "variant_count": (graveyard.get("summary") or {}).get("variant_count"),
            "pass": summary_all_pass(graveyard) is True and (graveyard.get("summary") or {}).get("variant_count", 0) >= 9,
        },
    }
    negative = {
        "consolidation_does_not_close_source_rows": {
            "source_rows_closed": False,
            "pass": True,
        },
        "consolidation_does_not_promote_qit_gstack_axis_bridge_or_nonclassical": {
            "qit_or_axis_promotion_allowed": False,
            "gstack_promotion_allowed": False,
            "bridge_promotion_allowed": False,
            "nonclassical_admission_allowed": False,
            "pass": True,
        },
    }
    boundary = {
        "coupling_constraints_include_blocked_promotion_edge": {
            "blocked_edge": "topology_to_qit_or_gstack",
            "pass": coupling_constraints["topology_to_qit_or_gstack"]["allowed"] is False,
        },
        "every_row_is_accepted_only_as_successor_or_graveyard_constraint": {
            "accepted_count": sum(row["accepted"] for row in rows),
            "pass": all(row["accepted"] for row in rows),
        },
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    result = {
        "name": "szilard_open_row_consolidation",
        "classification": CLASSIFICATION,
        "sim_execution_kind": "controller_index",
        "controller_index_exempt": True,
        "controller_index_exemption_reason": (
            "This result consolidates existing open Szilard rows and successor receipts; "
            "it is not a new runtime admission or QIT/GStack/axis claim."
        ),
        "classification_note": divergence_log,
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
            "source_row_count": len(rows),
            "source_negative_count": sum(row["source_preserved_negative"] for row in rows),
            "passing_successor_count": sum(row["successor_all_pass"] is True for row in rows),
            "fresh_source_count": sum(row["source_receipt_fresh"] for row in rows),
            "fresh_successor_count": sum(row["successor_receipt_fresh"] for row in rows),
            "accepted_constraint_count": sum(row["accepted"] for row in rows),
            "blocked_promotion_edges": [
                key for key, value in coupling_constraints.items() if value["allowed"] is False
            ],
            "source_rows_closed": False,
            "qit_or_axis_promotion_allowed": False,
            "gstack_promotion_allowed": False,
            "bridge_promotion_allowed": False,
            "nonclassical_admission_allowed": False,
            "visual_payload": "visualizer/szilard-open-row-consolidation-data.js",
            "scope_note": divergence_log,
        },
        "coupling_constraints": coupling_constraints,
        "rows": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "szilard_open_row_consolidation_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
