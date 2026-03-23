"""
Direct regression smoke for stored preserved-overlap health mismatch handling.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.graph_capability_auditor import (
    HEALTH_KEY,
    build_graph_capability_report,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_workspace(root: Path) -> None:
    graphs = root / "system_v4" / "a2_state" / "graphs"
    a1_state = root / "system_v4" / "a1_state"
    a2_state = root / "system_v4" / "a2_state"

    _write_json(
        graphs / "system_graph_a2_refinery.json",
        {"schema": "V4_SYSTEM_GRAPH_v1", "nodes": {}, "edges": []},
    )
    _write_json(
        graphs / "nested_graph_v1.json",
        {"schema": "NESTED_GRAPH_v1", "layers": {"A2": {}, "A1": {}}},
    )
    _write_json(
        graphs / "promoted_subgraph.json",
        {"schema": "PROMOTED_SUBGRAPH_v1", "nodes": {}, "edges": []},
    )
    _write_json(
        a1_state / "A1_GRAPH_PROJECTION.json",
        {"schema": "A1_GRAPH_PROJECTION_v1", "nodes": {}, "edges": []},
    )
    _write_json(
        graphs / "identity_registry_v1.json",
        {"schema": "IDENTITY_REGISTRY_v1", "nodes": {}, "edges": []},
    )
    for name in (
        "a2_high_intake_graph_v1.json",
        "a2_mid_refinement_graph_v1.json",
        "a2_low_control_graph_v1.json",
    ):
        _write_json(
            graphs / name,
            {
                "schema": "GRAPH_v1",
                "build_status": "MATERIALIZED",
                "materialized": True,
                "nodes": {},
                "edges": [],
            },
        )
    _write_json(
        a1_state / "a1_jargoned_graph_v1.json",
        {"schema": "A1_JARGONED_GRAPH_v1", "build_status": "MATERIALIZED", "materialized": True, "nodes": {}, "edges": []},
    )
    _write_json(
        a1_state / "a1_stripped_graph_v1.json",
        {"schema": "A1_STRIPPED_GRAPH_v1", "build_status": "FAIL_CLOSED", "materialized": False, "nodes": {}, "edges": []},
    )
    _write_json(
        a1_state / "a1_cartridge_graph_v1.json",
        {"schema": "A1_CARTRIDGE_GRAPH_v1", "build_status": "FAIL_CLOSED", "materialized": False, "nodes": {}, "edges": []},
    )

    observation_summary = {
        "A2_HIGH_INTAKE": {
            "path": str(graphs / "a2_high_intake_graph_v1.json"),
            "exists": True,
            "observation_state": "no_preserve_diagnostics_present",
            "has_preserve_diagnostics": False,
            "has_overlap_hygiene": False,
            "has_overlap_treatment": False,
            "preserved_only_edge_count": 0,
            "preserved_only_overlap_edge_count": 0,
            "current_runtime_effect": "",
            "reason_flags": [],
        },
        "A2_MID_REFINEMENT": {
            "path": str(graphs / "a2_mid_refinement_graph_v1.json"),
            "exists": True,
            "observation_state": "treatment_reported",
            "has_preserve_diagnostics": True,
            "has_overlap_hygiene": True,
            "has_overlap_treatment": True,
            "preserved_only_edge_count": 7,
            "preserved_only_overlap_edge_count": 5,
            "current_runtime_effect": "none_observed_in_live_consumers",
            "reason_flags": ["mid_reason"],
        },
        "A2_LOW_CONTROL": {
            "path": str(graphs / "a2_low_control_graph_v1.json"),
            "exists": True,
            "observation_state": "treatment_reported",
            "has_preserve_diagnostics": True,
            "has_overlap_hygiene": True,
            "has_overlap_treatment": True,
            "preserved_only_edge_count": 11,
            "preserved_only_overlap_edge_count": 9,
            "current_runtime_effect": "none_observed_in_live_consumers",
            "reason_flags": ["low_reason"],
        },
    }
    mismatched_health = {
        "observation_mode": "non_operative",
        "derived_from": "preserved_overlap_observation_summary",
        "layer_count": 3,
        "treatment_reported_layer_count": 1,
        "hygiene_only_layer_count": 1,
        "no_preserve_diagnostics_layer_count": 1,
        "missing_layer_store_count": 0,
        "preserved_only_overlap_layer_count": 1,
        "max_preserved_only_overlap_edge_count": 5,
        "note": "observational summary only; queue control fields remain unchanged",
    }
    _write_json(
        a2_state / "NESTED_GRAPH_BUILD_PROGRAM__2026_03_20__v1.json",
        {
            "schema": "NESTED_GRAPH_BUILD_PROGRAM_v1",
            "program_status": "NO_CURRENT_WORK__DIRECT_ENTROPY_EXECUTABLE_PAUSED",
            "current_queue_packet_json": str(
                a2_state / "NESTED_GRAPH_BUILD_QUEUE_STATUS_PACKET__CURRENT__2026_03_20__v1.json"
            ),
            "next_correction_handoff_json": "",
            "preserved_overlap_observation_summary": observation_summary,
            HEALTH_KEY: mismatched_health,
            "build_units": [],
        },
    )
    _write_json(
        a2_state / "NESTED_GRAPH_BUILD_QUEUE_STATUS_PACKET__CURRENT__2026_03_20__v1.json",
        {
            "schema": "NESTED_GRAPH_BUILD_QUEUE_STATUS_PACKET_v1",
            "queue_status": "NO_WORK",
            "dispatch_id": "",
            "dispatch_handoff_json": "",
            "preserved_overlap_observation_summary": observation_summary,
            HEALTH_KEY: mismatched_health,
        },
    )


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="graph_capability_nested_queue_health_mismatch_"))
    try:
        _seed_workspace(temp_root)
        report = build_graph_capability_report(str(temp_root))
        health = report.get("nested_queue_health_summary", {})
        aggregate = health.get("preserved_overlap_observation_health", {})

        _assert(
            report.get("next_recommended_unit") is None,
            "expected next_recommended_unit to remain None on NO_WORK paused queue",
        )
        _assert(
            health.get("stored_health_source") == "derived_fallback",
            "expected nested queue health to fall back to derived health when stored aggregate is stale",
        )
        _assert(
            health.get("stored_health_sync_state") == "in_sync",
            "expected nested queue health to report in-sync stored aggregate copies",
        )
        _assert(
            health.get("stored_health_match_state") == "mismatch_vs_observations",
            "expected nested queue health to flag stored aggregate mismatch against observations",
        )
        _assert(
            "stored_health_mismatch_vs_observations" in health.get("observation_flags", []),
            "expected nested queue health to surface mismatch as an observation flag",
        )
        _assert(
            aggregate.get("max_preserved_only_overlap_edge_count") == 9,
            "expected nested queue health to expose the derived fallback health instead of stale stored counts",
        )
        print("Graph capability nested queue health mismatch smoke")
        print("PASS: graph capability audit flags stored aggregate mismatch without changing routing")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
