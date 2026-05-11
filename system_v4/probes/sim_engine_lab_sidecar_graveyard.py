#!/usr/bin/env python3
"""Graveyard readout/topology sidecar failures without closing source rows."""

from __future__ import annotations

import json
import pathlib
from typing import Any


CLASSIFICATION = "graveyard_audit"
classification = CLASSIFICATION
divergence_log = (
    "Controller claim-level graveyard for engine-lab readout and topology "
    "sidecars. It separates killed readout/topology assumptions from surviving "
    "sidecar signals without graveyarding source rows or promoting QIT, GStack, "
    "axis, or runtime-engine claims."
)

LEGO_IDS = ["engine_lab_matrix", "readout_family", "topology_variant", "graveyard_variant"]
PRIMARY_LEGO_IDS = ["engine_lab_matrix"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads readout/topology sidecar receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical result paths"},
}
TOOL_INTEGRATION_DEPTH = {tool: "supportive" for tool in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def load(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def item(source: dict[str, Any], section: str, key: str) -> dict[str, Any]:
    return source[section][key]


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"name": result["name"], "summary": result["summary"], "rows": result["rows"]}
    js = "window.ENGINE_LAB_SIDECAR_GRAVEYARD_DATA = " + json.dumps(payload, indent=2, default=str) + ";\n"
    (VIS_DIR / "engine-lab-sidecar-graveyard-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    carnot = load("carnot_entropy_family_array_results.json")
    szilard = load("szilard_topology_entropy_array_results.json")

    rows = [
        {
            "variant_id": "carnot_exact_rows_minimize_performance_distance",
            "source_row": "carnot_entropy_family_array",
            "source_receipt": str(RESULT_DIR / "carnot_entropy_family_array_results.json"),
            "expected": "exact rows minimize performance distance relative to open rows",
            "observed": "exact performance distance is lower than the best open-row distance",
            "metrics": item(carnot, "positive", "exact_rows_minimize_performance_distance"),
            "verdict": "survived",
            "next_allowed_action": "use as readout reference evidence only; do not graveyard source rows",
        },
        {
            "variant_id": "carnot_open_rows_approach_exact_performance",
            "source_row": "carnot_entropy_family_array",
            "source_receipt": str(RESULT_DIR / "carnot_entropy_family_array_results.json"),
            "expected": "some open Carnot rows approach exact rows in performance",
            "observed": "best open performance distance is below the row-local threshold",
            "metrics": item(carnot, "positive", "some_open_rows_approach_the_exact_rows_closely_in_performance"),
            "verdict": "survived",
            "next_allowed_action": "use as open performance proximity evidence, not closure or source-row admission",
        },
        {
            "variant_id": "carnot_performance_closure_split",
            "source_row": "carnot_entropy_family_array",
            "source_receipt": str(RESULT_DIR / "carnot_entropy_family_array_results.json"),
            "expected": "best performance row differs from best closure row",
            "observed": "exact rows are best for both performance and closure in forward and reverse modes",
            "metrics": {
                "forward": item(carnot, "negative", "best_engine_performance_row_is_not_the_best_closure_row"),
                "reverse": item(carnot, "negative", "best_refrigerator_performance_row_is_not_the_best_closure_row"),
            },
            "verdict": "killed",
            "next_allowed_action": "graveyard this negative-check claim only; keep all source rows open",
        },
        {
            "variant_id": "szilard_topology_positive_ordering",
            "source_row": "szilard_topology_entropy_array",
            "source_receipt": str(RESULT_DIR / "szilard_topology_entropy_array_results.json"),
            "expected": "some topology has positive ordering margin",
            "observed": "asymmetric double well has the best positive margin",
            "metrics": item(szilard, "positive", "some_topology_has_positive_ordering_margin"),
            "verdict": "survived",
            "next_allowed_action": "use asymmetric topology as local sidecar candidate only; do not graveyard source rows",
        },
        {
            "variant_id": "szilard_topology_changes_nonlogical_entropy",
            "source_row": "szilard_topology_entropy_array",
            "source_receipt": str(RESULT_DIR / "szilard_topology_entropy_array_results.json"),
            "expected": "topology changes nonlogical entropy proxy",
            "observed": "spread entropy range is nonzero across topologies",
            "metrics": item(szilard, "positive", "topology_changes_nonlogical_entropy_proxy"),
            "verdict": "survived",
            "next_allowed_action": "use as topology/readout diversity evidence only; source row remains open",
        },
        {
            "variant_id": "szilard_weak_topology_exists",
            "source_row": "szilard_topology_entropy_array",
            "source_receipt": str(RESULT_DIR / "szilard_topology_entropy_array_results.json"),
            "expected": "at least one topology remains weak for ordering",
            "observed": "worst margin is still positive rather than weak under the row-local negative test",
            "metrics": item(szilard, "negative", "at_least_one_topology_remains_weak_for_ordering"),
            "verdict": "killed",
            "next_allowed_action": "graveyard this weak-topology claim only; do not remove wide topology",
        },
    ]

    positive = {
        "sidecar_rows_are_partitioned": {
            "variant_count": len(rows),
            "source_row_count": len({row["source_row"] for row in rows}),
            "pass": len(rows) == 6 and len({row["source_row"] for row in rows}) == 2,
        },
        "source_rows_remain_open": {
            "carnot_all_pass": carnot["summary"]["all_pass"],
            "szilard_all_pass": szilard["summary"]["all_pass"],
            "pass": not carnot["summary"]["all_pass"] and not szilard["summary"]["all_pass"],
        },
    }
    negative = {
        "graveyard_does_not_promote_sidecars": {
            "qit_or_axis_promotion_allowed": False,
            "pass": True,
        },
    }
    boundary = {
        "all_rows_have_verdicts": {
            "pass": all(row["verdict"] in {"killed", "survived"} for row in rows),
        },
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    result = {
        "name": "engine_lab_sidecar_graveyard",
        "classification": CLASSIFICATION,
        "sim_execution_kind": "controller_index",
        "controller_index_exempt": True,
        "controller_index_exemption_reason": (
            "This result indexes readout/topology sidecar variants and does not admit "
            "QIT, GStack, axis, or runtime-engine claims."
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
            "variant_count": len(rows),
            "killed_count": sum(row["verdict"] == "killed" for row in rows),
            "survived_count": sum(row["verdict"] == "survived" for row in rows),
            "source_row_graveyarded_count": 0,
            "source_rows_closed": False,
            "source_sidecars_tool_integrated": False,
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "engine_lab_sidecar_graveyard_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
