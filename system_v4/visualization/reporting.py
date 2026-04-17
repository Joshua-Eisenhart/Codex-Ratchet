from __future__ import annotations

from system_v4.visualization.comparison import compare_run_dirs
from system_v4.visualization.inspection import inspect_run_dir


def _join_items(values: list[str]) -> str:
    return ", ".join(values) if values else "(none)"


def _consumer_surface_summary(report: dict) -> str:
    return (
        "Consumer Surfaces: "
        f"eligible={_join_items(report.get('eligible_consumers', []))} | "
        f"blocked={_join_items(report.get('blocked_consumers', []))} | "
        f"promotion_blockers={_join_items(report.get('promotion_blockers', []))}"
    )


def render_run_report(run_dir) -> str:
    report = inspect_run_dir(run_dir)
    evidence = report["evidence_paths"]
    lines = [
        f"Run: {report['run_id']}",
        f"Sim: {report['sim_name']}",
        f"Schema: {report['schema_version']}",
        f"Constraint Set: {report.get('constraint_set')}",
        f"Probe Family: {report.get('probe_family')}",
        f"Carrier: {report.get('carrier')}",
        f"Lane/Layer: {report.get('lane')} / {report.get('layer')}",
        f"Witness Type: {report.get('witness_type')}",
        f"Admission Stage: {report.get('admission_stage')}",
        f"Admission Stage Index: {report.get('admission_stage_index')}",
        f"Promotion Target Stage: {report.get('promotion_target_stage')}",
        "Internal Promotion Restriction: promotion_status=canonical is reserved for bridge-claims",
        f"Claim State: {report.get('claim_state')}",
        f"Promotion Status: {report.get('promotion_status')}",
        f"Claim Ceiling: {report['status_label']}",
        f"Status Label: {report['status_label']}",
        f"Geometry Rendering Status: {report.get('geometry_rendering_status')}",
        f"Witness Trace ID: {report.get('witness_trace_id')}",
        f"Witness Events: {report.get('witness_event_count', 0)}",
        f"Exclusion Events: {report.get('exclusion_event_count', 0)}",
        f"Frames: {report['frame_count']}",
        f"Mesh Patches: {report.get('mesh_patch_count', 0)}",
        f"Transitions: {report.get('transition_meta_count', 0)}",
        f"Lineage Records: {report.get('lineage_meta_count', 0)}",
        f"Topology Changes: {report.get('topology_change_count', 0)}",
        f"Validation Gate: {report['validation_ok']}",
        f"Summary Result: {report['summary_all_pass']}",
        f"Path: {report['path_kind']}",
        f"Projected Path: {report['projected_path_kind']}",
        f"Capabilities: {_join_items(report['capabilities'])}",
        f"Overlays: {_join_items(report['overlays'])}",
        f"Negative Controls: {_join_items(report.get('negative_controls', []))}",
        f"Required Negatives: {_join_items(report.get('required_negatives', []))}",
        f"Negatives Run: {_join_items(report.get('negatives_run', []))}",
        f"Kill Conditions: {_join_items(report.get('kill_conditions', []))}",
        f"Negative Controls Run: {_join_items(report.get('negative_controls_run', []))}",
        f"Exclusion Criteria: {_join_items(report.get('exclusion_criteria', []))}",
        f"Eligible Consumers: {_join_items(report.get('eligible_consumers', []))}",
        f"Blocked Consumers: {_join_items(report.get('blocked_consumers', []))}",
        f"Promotion Blockers: {_join_items(report.get('promotion_blockers', []))}",
        _consumer_surface_summary(report),
        f"Lane Admission: {report.get('lane_admission', {})}",
        "Claim-Evidence Table:",
        f"- claim=candidate {report['run_id']} has status {report['status_label']} under the active witness family | source={evidence['manifest']} | result={evidence['final_frame']} | criteria={','.join(report['criteria_checked'])} | status={report['status_label']} | admission_stage={report.get('admission_stage')} | promotion_target_stage={report.get('promotion_target_stage')}",
    ]
    if report.get("live_splits"):
        lines.append(f"Live Splits: {_join_items(report['live_splits'])}")
    if report["expected_invariants"]:
        lines.append(f"Expected Invariants: {report['expected_invariants']}")
    if report["measured_invariants"]:
        lines.append(f"Measured Invariants: {report['measured_invariants']}")
    if report["validation_warnings"]:
        lines.append(f"Warnings: {_join_items(report['validation_warnings'])}")
    if report["validation_errors"]:
        lines.append(f"Errors: {_join_items(report['validation_errors'])}")
    return "\n".join(lines)


def render_comparison_report(left_run, right_run) -> str:
    report = compare_run_dirs(left_run, right_run)
    lines = [
        f"Left: {report['left_run_id']} ({report['left_sim_name']})",
        f"Right: {report['right_run_id']} ({report['right_sim_name']})",
        f"Left Probe/Lane: {report['probe_family']['left']} / {report['lane']['left']}",
        f"Right Probe/Lane: {report['probe_family']['right']} / {report['lane']['right']}",
        f"Left Status Label: {report['status_label']['left']}",
        f"Right Status Label: {report['status_label']['right']}",
        f"Left Claim State: {report['claim_state']['left']}",
        f"Right Claim State: {report['claim_state']['right']}",
        f"Left Admission Stage: {report['admission_stage']['left']}",
        f"Right Admission Stage: {report['admission_stage']['right']}",
        f"Left Promotion Target Stage: {report['promotion_target_stage']['left']}",
        f"Right Promotion Target Stage: {report['promotion_target_stage']['right']}",
        "Internal Promotion Restriction: promotion_status=canonical is reserved for bridge-claims",
        f"Left Promotion Status: {report['promotion_status']['left']}",
        f"Right Promotion Status: {report['promotion_status']['right']}",
        f"Both Validation Gates Green: {report['validation_ok']['left'] and report['validation_ok']['right']}",
        f"Frame Delta: {report['frame_count']['delta']}",
        f"Mesh Patch Delta: {report.get('mesh_patch_count', {}).get('delta', 0)}",
        f"Transition Delta: {report.get('transition_meta_count', {}).get('delta', 0)}",
        f"Lineage Delta: {report.get('lineage_meta_count', {}).get('delta', 0)}",
        f"Topology Change Delta: {report.get('topology_change_count', {}).get('delta', 0)}",
        f"Left-only Capabilities: {_join_items(report['capabilities']['only_left'])}",
        f"Right-only Capabilities: {_join_items(report['capabilities']['only_right'])}",
        f"Left-only Overlays: {_join_items(report['overlays']['only_left'])}",
        f"Right-only Overlays: {_join_items(report['overlays']['only_right'])}",
        f"Path Kinds: left={report['path_kind']['left']} right={report['path_kind']['right']}",
        f"Projected Paths: left={report['projected_path_kind']['left']} right={report['projected_path_kind']['right']}",
    ]

    scalar_diff = report["final_scalars"]
    interesting_scalars = []
    for key, payload in scalar_diff.items():
        if payload.get("delta") not in (None, 0.0) or payload.get("left") is None or payload.get("right") is None:
            interesting_scalars.append(f"{key}: {payload}")
    if interesting_scalars:
        lines.append("Final Scalar Differences:")
        lines.extend(interesting_scalars)

    invariant_diff = report["measured_invariants"]
    interesting_invariants = []
    for key, payload in invariant_diff.items():
        if payload.get("delta") not in (None, 0.0) or payload.get("left") is None or payload.get("right") is None:
            interesting_invariants.append(f"{key}: {payload}")
    if interesting_invariants:
        lines.append("Measured Invariant Differences:")
        lines.extend(interesting_invariants)

    if report["validation_errors"]["left"] or report["validation_errors"]["right"]:
        lines.append(f"Validation Errors Left: {_join_items(report['validation_errors']['left'])}")
        lines.append(f"Validation Errors Right: {_join_items(report['validation_errors']['right'])}")
    if report["validation_warnings"]["left"] or report["validation_warnings"]["right"]:
        lines.append(f"Validation Warnings Left: {_join_items(report['validation_warnings']['left'])}")
        lines.append(f"Validation Warnings Right: {_join_items(report['validation_warnings']['right'])}")

    return "\n".join(lines)
