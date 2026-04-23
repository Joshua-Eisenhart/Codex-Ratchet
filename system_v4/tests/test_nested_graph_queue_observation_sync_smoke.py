"""
Direct regression smoke for nested graph queue observation sync.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.nested_graph_queue_observation_sync import (
    HEALTH_KEY,
    OBSERVATION_KEY,
    sync_nested_graph_queue_observations,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_workspace(root: Path) -> tuple[str, str, str]:
    graphs = root / "system_v4" / "a2_state" / "graphs"
    a2_state = root / "system_v4" / "a2_state"
    audit_logs = a2_state / "audit_logs"

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

    for name in (
        "A2_HIGH_INTAKE_GRAPH_AUDIT__2026_03_20__v1.md",
        "A2_MID_REFINEMENT_GRAPH_AUDIT__2026_03_20__v1.md",
        "A2_LOW_CONTROL_GRAPH_AUDIT__2026_03_20__v1.md",
    ):
        (audit_logs / name).parent.mkdir(parents=True, exist_ok=True)
        (audit_logs / name).write_text("# audit\n", encoding="utf-8")

    program_path = a2_state / "nested_program.json"
    queue_path = a2_state / "nested_queue_packet.json"
    note_path = a2_state / "nested_queue_status.md"

    _write_json(
        program_path,
        {
            "schema": "NESTED_GRAPH_BUILD_PROGRAM_v1",
            "program_status": "NO_CURRENT_WORK",
            "ready_unit_id": "",
            "queued_unit_ids": [],
            "next_correction_unit_id": "",
            "next_correction_handoff_json": "",
            "ready_layer_id": "",
            "last_materialized_layer_id": "A1_JARGONED",
            "last_completed_unit_id": "A1_ALIAS_LIFT",
            "last_completed_audit_surface": "system_v4/a2_state/audit_logs/A1_ALIAS_LIFT.md",
            "pause_reason": "paused for bounded follow-on audit",
            "pause_control_surface": "system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md",
            "build_units": [
                {
                    "unit_id": "A2_HIGH_INTAKE",
                    "dispatch_id": "DISPATCH_HIGH",
                    "layer_id": "A2_HIGH_INTAKE",
                    "status": "MATERIALIZED_FROM_EXISTING_FUEL",
                    "depends_on": [],
                    "required_boot": [],
                    "source_artifacts": [],
                    "expected_outputs": [
                        "system_v4/a2_state/graphs/a2_high_intake_graph_v1.json",
                        "system_v4/a2_state/audit_logs/A2_HIGH_INTAKE_GRAPH_AUDIT__2026_03_20__v1.md",
                    ],
                    "owner_surface": "system_v4/a2_state/graphs/a2_high_intake_graph_v1.json",
                    "audit_surface": "system_v4/a2_state/audit_logs/A2_HIGH_INTAKE_GRAPH_AUDIT__2026_03_20__v1.md",
                },
                {
                    "unit_id": "A2_MID_REFINEMENT",
                    "dispatch_id": "DISPATCH_MID",
                    "layer_id": "A2_MID_REFINEMENT",
                    "status": "MATERIALIZED_FROM_EXISTING_FUEL",
                    "depends_on": ["DISPATCH_HIGH"],
                    "required_boot": [],
                    "source_artifacts": [],
                    "expected_outputs": [
                        "system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json",
                        "system_v4/a2_state/audit_logs/A2_MID_REFINEMENT_GRAPH_AUDIT__2026_03_20__v1.md",
                    ],
                    "owner_surface": "system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json",
                    "audit_surface": "system_v4/a2_state/audit_logs/A2_MID_REFINEMENT_GRAPH_AUDIT__2026_03_20__v1.md",
                },
                {
                    "unit_id": "A2_LOW_CONTROL",
                    "dispatch_id": "DISPATCH_LOW",
                    "layer_id": "A2_LOW_CONTROL",
                    "status": "MATERIALIZED_FROM_EXISTING_FUEL",
                    "depends_on": ["DISPATCH_MID"],
                    "required_boot": [],
                    "source_artifacts": [],
                    "expected_outputs": [
                        "system_v4/a2_state/graphs/a2_low_control_graph_v1.json",
                        "system_v4/a2_state/audit_logs/A2_LOW_CONTROL_GRAPH_AUDIT__2026_03_20__v1.md",
                    ],
                    "owner_surface": "system_v4/a2_state/graphs/a2_low_control_graph_v1.json",
                    "audit_surface": "system_v4/a2_state/audit_logs/A2_LOW_CONTROL_GRAPH_AUDIT__2026_03_20__v1.md",
                },
            ],
        },
    )
    _write_json(
        queue_path,
        {
            "schema": "NESTED_GRAPH_BUILD_QUEUE_STATUS_PACKET_v1",
            "queue_status": "NO_WORK",
            "program_id": "NESTED_GRAPH_BUILD_PROGRAM__TEST__v1",
            "dispatch_id": "",
            "required_boot": [],
            "source_artifacts": [],
            "queued_after_dispatch": [],
            "dispatch_handoff_json": "",
            "program_packet_json": "system_v4/a2_state/nested_program.json",
            "source_packet_json": "system_v4/a2_state/nested_program.json",
            "operator_steps": [],
            "prompt_to_send": "",
            "stop_rule": "Stop and keep the route paused.",
            "ready_unit_id": "",
            "ready_layer_id": "",
            "last_materialized_layer_id": "A1_JARGONED",
            "queued_unit_ids": [],
            "next_correction_unit_id": "",
            "next_correction_handoff_json": "",
            "reason": "paused for bounded follow-on audit",
            "pause_control_surface": "system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md",
            "last_completed_dispatch_id": "DISPATCH_ALIAS",
            "last_completed_audit_surface": "system_v4/a2_state/audit_logs/A1_ALIAS_LIFT.md",
        },
    )
    note_path.write_text(
        "\n".join(
            [
                "# NESTED_GRAPH_BUILD_QUEUE_STATUS__CURRENT__TEST__v1",
                "",
                "queue_status: NO_WORK",
                "ready_unit_id:",
                "ready_layer_id:",
                "last_materialized_layer_id: A1_JARGONED",
                "program_status: NO_CURRENT_WORK",
                "dispatch_id:",
                "current_handoff_json:",
                "",
                "## Completed This Round",
                "- existing round summary",
                "",
                "## No Work Reason",
                "- existing no-work reason",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return (
        str(program_path.relative_to(root)),
        str(queue_path.relative_to(root)),
        str(note_path.relative_to(root)),
    )


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="nested_queue_observation_sync_"))
    try:
        program_path, queue_path, note_path = _seed_workspace(temp_root)
        program_before = json.loads((temp_root / program_path).read_text(encoding="utf-8"))
        queue_before = json.loads((temp_root / queue_path).read_text(encoding="utf-8"))

        result = sync_nested_graph_queue_observations(
            str(temp_root),
            program_path=program_path,
            queue_packet_path=queue_path,
            queue_status_note_path=note_path,
        )

        program_after = json.loads((temp_root / program_path).read_text(encoding="utf-8"))
        queue_after = json.loads((temp_root / queue_path).read_text(encoding="utf-8"))
        note_after = (temp_root / note_path).read_text(encoding="utf-8")

        summary_program = program_after.get(OBSERVATION_KEY, {})
        summary_queue = queue_after.get(OBSERVATION_KEY, {})
        health_program = program_after.get(HEALTH_KEY, {})
        health_queue = queue_after.get(HEALTH_KEY, {})

        _assert(
            summary_program == summary_queue,
            "expected program and queue packet to receive the same observation summary",
        )
        _assert(
            health_program == health_queue,
            "expected program and queue packet to receive the same queue health summary",
        )
        _assert(
            summary_program["A2_HIGH_INTAKE"]["observation_state"] == "no_preserve_diagnostics_present",
            "expected A2_HIGH observation to reflect missing preserve diagnostics",
        )
        _assert(
            summary_program["A2_MID_REFINEMENT"]["preserved_only_edge_count"] == 7,
            "expected A2_MID preserved-only edge count to be mirrored",
        )
        _assert(
            summary_program["A2_LOW_CONTROL"]["preserved_only_overlap_edge_count"] == 9,
            "expected A2_LOW preserved-only overlap count to be mirrored",
        )
        _assert(
            health_program.get("observation_mode") == "non_operative",
            "expected queue health summary to stay non-operative",
        )
        _assert(
            health_program.get("derived_from") == OBSERVATION_KEY,
            "expected queue health summary to record its observation provenance",
        )
        _assert(
            health_program.get("treatment_reported_layer_count") == 2,
            "expected queue health summary to count treatment-reported layers",
        )
        _assert(
            health_program.get("no_preserve_diagnostics_layer_count") == 1,
            "expected queue health summary to count layers without preserve diagnostics",
        )
        _assert(
            health_program.get("preserved_only_overlap_layer_count") == 2,
            "expected queue health summary to count layers with preserved-only overlaps",
        )
        _assert(
            health_program.get("max_preserved_only_overlap_edge_count") == 9,
            "expected queue health summary to surface the max overlap count in the seeded temp graph",
        )
        _assert(
            health_program.get("note") == "observational summary only; queue control fields remain unchanged",
            "expected queue health summary to carry an explicit non-operative guard note",
        )
        for field in (
            "program_status",
            "ready_unit_id",
            "queued_unit_ids",
            "next_correction_unit_id",
            "last_materialized_layer_id",
            "pause_reason",
            "pause_control_surface",
        ):
            _assert(
                program_before.get(field) == program_after.get(field),
                f"expected program control field {field} to remain unchanged",
            )
        for field in (
            "queue_status",
            "ready_unit_id",
            "ready_layer_id",
            "last_materialized_layer_id",
            "next_correction_unit_id",
            "reason",
            "stop_rule",
            "pause_control_surface",
            "last_completed_dispatch_id",
            "last_completed_audit_surface",
        ):
            _assert(
                queue_before.get(field) == queue_after.get(field),
                f"expected queue packet control field {field} to remain unchanged",
            )
        _assert(
            "## Completed This Round" in note_after and "existing round summary" in note_after,
            "expected existing queue note content to remain intact",
        )
        _assert(
            "## Preserved Overlap Observations" in note_after,
            "expected queue note to gain preserved overlap observations section",
        )
        _assert(
            "## Preserved Overlap Observation Health" in note_after,
            "expected queue note to gain preserved overlap observation health section",
        )
        _assert(
            "- derived_from: preserved_overlap_observation_summary" in note_after,
            "expected queue note to surface observation provenance for the health aggregate",
        )
        _assert(
            "- treatment_reported_layer_count: 2" in note_after
            and "- no_preserve_diagnostics_layer_count: 1" in note_after,
            "expected queue note to surface aggregate state counts",
        )
        _assert(
            "- max_preserved_only_overlap_edge_count: 9" in note_after,
            "expected queue note to surface the max overlap edge count",
        )
        _assert(
            "- note: observational summary only; queue control fields remain unchanged" in note_after,
            "expected queue note to state that the health block is observational only",
        )
        _assert(
            "A2_MID_REFINEMENT: state=treatment_reported preserved_only_edges=7 preserved_only_overlaps=5" in note_after,
            "expected queue note to surface A2_MID observation summary",
        )
        _assert(
            "recommended_future_handling" not in note_after and "equal_runtime_weight_admissible_now" not in note_after,
            "expected queue note observations to remain non-prescriptive",
        )
        _assert(
            result["program_path"].endswith("nested_program.json")
            and result["queue_packet_path"].endswith("nested_queue_packet.json")
            and result["queue_status_note_path"].endswith("nested_queue_status.md"),
            "expected sync result to report updated surface paths",
        )
        print("Nested graph queue observation sync smoke")
        print("PASS: observation sync updates program, queue packet, and note without changing control state")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
