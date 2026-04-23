"""
Direct regression smoke for nested graph layer preserved-overlap observation summary.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.nested_graph_layer_auditor import (
    build_nested_graph_layer_audit,
    render_nested_graph_layer_note,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_workspace(root: Path) -> tuple[str, str]:
    graphs = root / "system_v4" / "a2_state" / "graphs"
    audit_logs = root / "system_v4" / "a2_state" / "audit_logs"

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

    program_path = root / "system_v4" / "a2_state" / "nested_program.json"
    queue_path = root / "system_v4" / "a2_state" / "nested_queue.json"

    _write_json(
        program_path,
        {
            "schema": "NESTED_GRAPH_BUILD_PROGRAM_v1",
            "program_status": "NO_CURRENT_WORK",
            "ready_unit_id": "",
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
            "dispatch_id": "",
            "dispatch_handoff_json": "",
        },
    )

    return (
        str(program_path.relative_to(root)),
        str(queue_path.relative_to(root)),
    )


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="nested_graph_layer_audit_smoke_"))
    try:
        program_path, queue_path = _seed_workspace(temp_root)
        report = build_nested_graph_layer_audit(
            str(temp_root),
            program_path=program_path,
            queue_packet_path=queue_path,
        )
        note = render_nested_graph_layer_note(report)

        summary = report.get("preserved_overlap_observation_summary", {})
        high = summary.get("A2_HIGH_INTAKE", {})
        mid = summary.get("A2_MID_REFINEMENT", {})
        low = summary.get("A2_LOW_CONTROL", {})

        _assert(
            report.get("current_queue_status") == "NO_WORK",
            "expected queue status to remain NO_WORK",
        )
        _assert(
            report.get("next_recommended_unit") is None,
            "expected next_recommended_unit to remain None for NO_WORK",
        )
        _assert(
            report["layer_statuses"]["A2_MID_REFINEMENT"] == "MATERIALIZED",
            "expected A2_MID state to remain MATERIALIZED",
        )
        _assert(
            high.get("observation_state") == "no_preserve_diagnostics_present",
            "expected A2_HIGH treatment summary to report no preserve diagnostics",
        )
        _assert(
            mid.get("observation_state") == "treatment_reported",
            "expected A2_MID treatment summary to report treatment",
        )
        _assert(
            low.get("observation_state") == "treatment_reported",
            "expected A2_LOW treatment summary to report treatment",
        )
        _assert(
            mid.get("preserved_only_edge_count") == 7 and mid.get("preserved_only_overlap_edge_count") == 5,
            "expected A2_MID preserved-only counts to be mirrored",
        )
        _assert(
            low.get("preserved_only_edge_count") == 11 and low.get("preserved_only_overlap_edge_count") == 9,
            "expected A2_LOW preserved-only counts to be mirrored",
        )

        _assert(
            "## PRESERVED_OVERLAP_OBSERVATIONS" in note,
            "expected nested graph layer note to render preserved-overlap observation summary",
        )
        _assert(
            "A2_HIGH_INTAKE: state=no_preserve_diagnostics_present preserved_only_edges=0 preserved_only_overlaps=0" in note,
            "expected note to surface A2_HIGH preserved-overlap observation state",
        )
        _assert(
            "A2_MID_REFINEMENT: state=treatment_reported preserved_only_edges=7 preserved_only_overlaps=5" in note,
            "expected note to surface A2_MID preserved-overlap observation state",
        )
        _assert(
            "A2_LOW_CONTROL: state=treatment_reported preserved_only_edges=11 preserved_only_overlaps=9" in note,
            "expected note to surface A2_LOW preserved-overlap observation state",
        )
        _assert(
            "recommended_future_handling" not in note and "equal_runtime_weight_admissible_now" not in note,
            "expected nested graph layer note to stay observational and omit prescriptive treatment fields",
        )
        print("Nested graph layer preserved-overlap summary smoke")
        print("PASS: nested graph layer audit mirrors preserved-overlap observations without changing queue state")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
