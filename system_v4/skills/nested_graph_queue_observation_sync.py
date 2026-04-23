"""
nested_graph_queue_observation_sync.py

Synchronize non-operative preserved-overlap observations from the nested graph
layer audit into the current nested build program, queue packet, and queue
status note. This is intentionally fail-closed and observational only: it must
not change queue control fields.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from system_v4.skills.nested_graph_layer_auditor import (
    DEFAULT_PROGRAM,
    DEFAULT_QUEUE_PACKET,
    build_nested_graph_layer_audit,
)


QUEUE_STATUS_NOTE = "system_v4/a2_state/NESTED_GRAPH_BUILD_QUEUE_STATUS__CURRENT__2026_03_20__v1.md"
OBSERVATION_KEY = "preserved_overlap_observation_summary"
HEALTH_KEY = "preserved_overlap_queue_health_summary"
CONTROL_FIELDS = (
    "queue_status",
    "ready_unit_id",
    "ready_layer_id",
    "dispatch_id",
    "next_correction_unit_id",
    "next_correction_handoff_json",
    "reason",
    "stop_rule",
    "pause_control_surface",
    "program_status",
    "last_materialized_layer_id",
    "last_completed_dispatch_id",
    "last_completed_audit_surface",
    "last_completed_unit_id",
    "queued_unit_ids",
)


def _resolve(root: Path, raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (root / path)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _render_observation_section(summary: dict[str, dict[str, Any]]) -> list[str]:
    lines = ["## Preserved Overlap Observations"]
    for layer_id, info in summary.items():
        lines.append(
            f"- {layer_id}: state={info['observation_state']} "
            f"preserved_only_edges={info['preserved_only_edge_count']} "
            f"preserved_only_overlaps={info['preserved_only_overlap_edge_count']}"
        )
        if info.get("current_runtime_effect"):
            lines.append(f"  - current_runtime_effect: {info['current_runtime_effect']}")
        if info.get("reason_flags"):
            lines.append(f"  - reason_flags: {info['reason_flags']}")
    return lines


def _build_queue_health_summary(summary: dict[str, dict[str, Any]]) -> dict[str, Any]:
    treatment_reported_layer_count = 0
    hygiene_only_layer_count = 0
    no_preserve_diagnostics_layer_count = 0
    missing_layer_store_count = 0
    preserved_only_overlap_layer_count = 0
    max_overlap_count = 0

    for layer_id, info in summary.items():
        state = str(info.get("observation_state", ""))
        overlap_count = int(info.get("preserved_only_overlap_edge_count", 0) or 0)
        if state == "treatment_reported":
            treatment_reported_layer_count += 1
        elif state == "hygiene_only":
            hygiene_only_layer_count += 1
        elif state == "no_preserve_diagnostics_present":
            no_preserve_diagnostics_layer_count += 1
        elif state == "missing_layer_store":
            missing_layer_store_count += 1
        if overlap_count > 0:
            preserved_only_overlap_layer_count += 1
        if overlap_count > max_overlap_count:
            max_overlap_count = overlap_count

    return {
        "observation_mode": "non_operative",
        "derived_from": OBSERVATION_KEY,
        "layer_count": len(summary),
        "treatment_reported_layer_count": treatment_reported_layer_count,
        "hygiene_only_layer_count": hygiene_only_layer_count,
        "no_preserve_diagnostics_layer_count": no_preserve_diagnostics_layer_count,
        "missing_layer_store_count": missing_layer_store_count,
        "preserved_only_overlap_layer_count": preserved_only_overlap_layer_count,
        "max_preserved_only_overlap_edge_count": max_overlap_count,
        "note": "observational summary only; queue control fields remain unchanged",
    }


def _render_health_section(health: dict[str, Any]) -> list[str]:
    return [
        "## Preserved Overlap Observation Health",
        f"- derived_from: {health.get('derived_from', '')}",
        f"- observation_mode: {health.get('observation_mode', '')}",
        f"- layer_count: {health.get('layer_count', 0)}",
        f"- treatment_reported_layer_count: {health.get('treatment_reported_layer_count', 0)}",
        f"- hygiene_only_layer_count: {health.get('hygiene_only_layer_count', 0)}",
        f"- no_preserve_diagnostics_layer_count: {health.get('no_preserve_diagnostics_layer_count', 0)}",
        f"- missing_layer_store_count: {health.get('missing_layer_store_count', 0)}",
        f"- preserved_only_overlap_layer_count: {health.get('preserved_only_overlap_layer_count', 0)}",
        f"- max_preserved_only_overlap_edge_count: {health.get('max_preserved_only_overlap_edge_count', 0)}",
        f"- note: {health.get('note', '')}",
    ]


def _upsert_observation_sections(
    existing_text: str,
    health: dict[str, Any],
    summary: dict[str, dict[str, Any]],
) -> str:
    lines = existing_text.splitlines()
    headers = (
        "## Preserved Overlap Observation Health",
        "## Preserved Overlap Queue Health",
        "## Preserved Overlap Observations",
    )
    idx = -1
    for header in headers:
        try:
            idx = lines.index(header)
            break
        except ValueError:
            continue
    if idx >= 0:
        lines = lines[:idx]
        while lines and lines[-1] == "":
            lines.pop()
    if lines and lines[-1] != "":
        lines.append("")
    lines.extend(_render_health_section(health))
    lines.append("")
    lines.extend(_render_observation_section(summary))
    return "\n".join(lines) + "\n"


def sync_nested_graph_queue_observations(
    workspace_root: str,
    program_path: str = DEFAULT_PROGRAM,
    queue_packet_path: str = DEFAULT_QUEUE_PACKET,
    queue_status_note_path: str = QUEUE_STATUS_NOTE,
) -> dict[str, str]:
    root = Path(workspace_root).resolve()
    program_file = _resolve(root, program_path)
    queue_file = _resolve(root, queue_packet_path)
    note_file = _resolve(root, queue_status_note_path)

    program = _load_json(program_file)
    queue_packet = _load_json(queue_file)
    report = build_nested_graph_layer_audit(
        str(root),
        program_path=str(program_file),
        queue_packet_path=str(queue_file),
    )
    summary = report.get(OBSERVATION_KEY, {}) or {}
    health = _build_queue_health_summary(summary)

    before_program = {key: program.get(key) for key in CONTROL_FIELDS}
    before_queue = {key: queue_packet.get(key) for key in CONTROL_FIELDS}

    program[OBSERVATION_KEY] = summary
    queue_packet[OBSERVATION_KEY] = summary
    program[HEALTH_KEY] = health
    queue_packet[HEALTH_KEY] = health

    _write_json(program_file, program)
    _write_json(queue_file, queue_packet)

    existing_note = note_file.read_text(encoding="utf-8") if note_file.exists() else ""
    updated_note = _upsert_observation_sections(existing_note, health, summary)
    note_file.parent.mkdir(parents=True, exist_ok=True)
    note_file.write_text(updated_note, encoding="utf-8")

    after_program = {key: program.get(key) for key in CONTROL_FIELDS}
    after_queue = {key: queue_packet.get(key) for key in CONTROL_FIELDS}
    if before_program != after_program:
        raise RuntimeError("program control fields changed during observation sync")
    if before_queue != after_queue:
        raise RuntimeError("queue packet control fields changed during observation sync")

    return {
        "program_path": str(program_file),
        "queue_packet_path": str(queue_file),
        "queue_status_note_path": str(note_file),
    }


if __name__ == "__main__":
    print(
        json.dumps(
            sync_nested_graph_queue_observations(str(Path(__file__).resolve().parents[2])),
            indent=2,
            sort_keys=True,
        )
    )
