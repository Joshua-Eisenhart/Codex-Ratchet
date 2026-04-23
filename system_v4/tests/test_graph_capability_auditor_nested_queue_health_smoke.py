"""
Direct regression smoke for graph capability nested queue health summary.
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
    render_graph_capability_note,
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
        {
            "schema": "V4_SYSTEM_GRAPH_v1",
            "nodes": {},
            "edges": [],
        },
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
    _write_json(
        graphs / "a2_high_intake_graph_v1.json",
        {
            "schema": "A2_HIGH_INTAKE_GRAPH_v1",
            "build_status": "MATERIALIZED",
            "materialized": True,
            "nodes": {},
            "edges": [],
        },
    )
    _write_json(
        graphs / "a2_mid_refinement_graph_v1.json",
        {
            "schema": "A2_MID_REFINEMENT_GRAPH_v1",
            "build_status": "MATERIALIZED",
            "materialized": True,
            "preserve_diagnostics": {
                "preserved_only_edge_count": 7,
                "preserved_only_overlaps_hygiene": {
                    "preserved_only_overlap_edge_count": 5,
                },
                "preserved_only_overlaps_treatment": {
                    "current_runtime_effect": "none_observed_in_live_consumers",
                    "equal_runtime_weight_admissible_now": False,
                    "recommended_future_handling": "quarantine_or_downrank_before_equal_runtime_use",
                    "reason_flags": ["mid_reason"],
                },
            },
            "nodes": {},
            "edges": [],
        },
    )
    _write_json(
        graphs / "a2_low_control_graph_v1.json",
        {
            "schema": "A2_LOW_CONTROL_GRAPH_v1",
            "build_status": "MATERIALIZED",
            "materialized": True,
            "preserve_diagnostics": {
                "preserved_only_edge_count": 11,
                "preserved_only_overlaps_hygiene": {
                    "preserved_only_overlap_edge_count": 9,
                },
                "preserved_only_overlaps_treatment": {
                    "current_runtime_effect": "none_observed_in_live_consumers",
                    "equal_runtime_weight_admissible_now": False,
                    "recommended_future_handling": "quarantine_or_downrank_before_equal_runtime_use",
                    "reason_flags": ["low_reason"],
                },
            },
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
    observation_health = {
        "observation_mode": "non_operative",
        "derived_from": "preserved_overlap_observation_summary",
        "layer_count": 3,
        "treatment_reported_layer_count": 2,
        "hygiene_only_layer_count": 0,
        "no_preserve_diagnostics_layer_count": 1,
        "missing_layer_store_count": 0,
        "preserved_only_overlap_layer_count": 2,
        "max_preserved_only_overlap_edge_count": 9,
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
            "next_correction_unit_id": "",
            "ready_unit_id": "",
            "preserved_overlap_observation_summary": observation_summary,
            HEALTH_KEY: observation_health,
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
            HEALTH_KEY: observation_health,
        },
    )


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="graph_capability_nested_queue_health_"))
    try:
        _seed_workspace(temp_root)
        report = build_graph_capability_report(str(temp_root))
        note = render_graph_capability_note(report)

        health = report.get("nested_queue_health_summary", {})

        _assert(
            report.get("next_recommended_unit") is None,
            "expected next_recommended_unit to remain None on NO_WORK paused queue",
        )
        _assert(
            health.get("queue_status") == "NO_WORK",
            "expected nested queue health to mirror queue status",
        )
        _assert(
            health.get("program_status") == "NO_CURRENT_WORK__DIRECT_ENTROPY_EXECUTABLE_PAUSED",
            "expected nested queue health to mirror program status",
        )
        _assert(
            health.get("observation_sync_state") == "in_sync",
            "expected nested queue health to report in-sync observations",
        )
        _assert(
            health.get("observation_source") == "queue_packet",
            "expected nested queue health to prefer queue packet observations when present",
        )
        _assert(
            health.get("stored_health_sync_state") == "in_sync",
            "expected nested queue health to report in-sync stored aggregate health",
        )
        _assert(
            health.get("stored_health_source") == "queue_packet",
            "expected nested queue health to prefer queue packet stored aggregate health when present",
        )
        _assert(
            health.get("stored_health_match_state") == "matches_observations",
            "expected nested queue health to verify stored aggregate health against observations",
        )
        _assert(
            health.get("carryover_heavy_layer_count") == 2,
            "expected nested queue health to count A2_MID and A2_LOW as carryover-heavy",
        )
        _assert(
            health.get("carryover_heavy_layers") == ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"],
            "expected nested queue health to surface the carryover-heavy layers in order",
        )
        _assert(
            "queue_paused_no_work" in health.get("observation_flags", []),
            "expected nested queue health to flag NO_WORK queue posture",
        )
        _assert(
            "observation_sync_in_place" in health.get("observation_flags", []),
            "expected nested queue health to flag observation sync presence",
        )
        _assert(
            "carryover_heavy_a2_layers_observed" in health.get("observation_flags", []),
            "expected nested queue health to flag carryover-heavy A2 observations",
        )
        _assert(
            health.get("preserved_overlap_observation_health", {}).get("treatment_reported_layer_count") == 2,
            "expected nested queue health to expose the stored aggregate health block",
        )
        _assert(
            "## Nested Queue Health" in note,
            "expected capability note to render nested queue health section",
        )
        _assert(
            "- observation_sync_state: in_sync" in note,
            "expected capability note to render observation sync state",
        )
        _assert(
            "- stored_health_match_state: matches_observations" in note,
            "expected capability note to render stored health match state",
        )
        _assert(
            "- preserved_overlap_health_derived_from: preserved_overlap_observation_summary" in note,
            "expected capability note to render the stored aggregate health provenance",
        )
        _assert(
            "- carryover_heavy_layer_count: 2" in note,
            "expected capability note to render carryover-heavy layer count",
        )
        print("Graph capability nested queue health smoke")
        print("PASS: graph capability audit now surfaces nested queue health from synced overlap observations")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
