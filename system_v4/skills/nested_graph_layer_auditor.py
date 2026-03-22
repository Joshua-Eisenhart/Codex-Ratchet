"""
nested_graph_layer_auditor.py

Audit the queued nested graph build program against current owner surfaces.
This is intentionally fail-closed and procedural: it reports what exists, what
is blocked, and what is still only queued.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


DEFAULT_PROGRAM = "system_v4/a2_state/NESTED_GRAPH_BUILD_PROGRAM__2026_03_20__v1.json"
DEFAULT_QUEUE_PACKET = "system_v4/a2_state/NESTED_GRAPH_BUILD_QUEUE_STATUS_PACKET__CURRENT__2026_03_20__v1.json"
PRESERVED_OVERLAP_TREATMENT_LAYERS = (
    "A2_HIGH_INTAKE",
    "A2_MID_REFINEMENT",
    "A2_LOW_CONTROL",
)


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve(root: Path, raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (root / path)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_next_required_lane(output_paths: list[Path]) -> str:
    for path in output_paths:
        if not path.exists() or path.suffix.lower() != ".md":
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("next_required_lane: "):
                return line.split(": ", 1)[1].strip()
    return ""


def _inspect_handoff(root: Path, raw_handoff_path: str) -> dict[str, Any]:
    if not raw_handoff_path:
        return {}
    handoff_path = _resolve(root, raw_handoff_path)
    if not handoff_path.exists():
        return {
            "path": str(handoff_path),
            "exists": False,
            "state": "BLOCKED",
            "unit_id": "",
            "dispatch_id": "",
            "layer_id": "",
            "role_type": "",
            "thread_class": "",
            "mode": "",
            "queue_status": "",
            "missing_boot": [],
            "missing_sources": [],
            "existing_outputs": [],
            "expected_output_count": 0,
            "write_scope": [],
            "next_required_lane": "",
        }
    handoff = _load_json(handoff_path)
    required_boot = [_resolve(root, p) for p in handoff.get("required_boot", [])]
    source_artifacts = [_resolve(root, p) for p in handoff.get("source_artifacts", [])]
    expected_outputs = [_resolve(root, p) for p in handoff.get("expected_outputs", [])]
    missing_boot = [str(p) for p in required_boot if not p.exists()]
    missing_sources = [str(p) for p in source_artifacts if not p.exists()]
    existing_outputs = [str(p) for p in expected_outputs if p.exists()]
    if expected_outputs and len(existing_outputs) == len(expected_outputs):
        current_state = "COMPLETED"
    else:
        current_state = "BLOCKED" if (missing_boot or missing_sources) else "QUEUED"
    next_required_lane = _extract_next_required_lane(expected_outputs)
    return {
        "path": str(handoff_path),
        "exists": True,
        "unit_id": str(handoff.get("unit_id", "")),
        "dispatch_id": str(handoff.get("dispatch_id", "")),
        "layer_id": str(handoff.get("layer_id", "")),
        "role_type": str(handoff.get("role_type", "")),
        "thread_class": str(handoff.get("thread_class", "")),
        "mode": str(handoff.get("mode", "")),
        "queue_status": str(handoff.get("queue_status", "")),
        "state": current_state,
        "depends_on": list(handoff.get("depends_on", [])),
        "missing_boot": missing_boot,
        "missing_sources": missing_sources,
        "existing_outputs": existing_outputs,
        "expected_output_count": len(expected_outputs),
        "write_scope": list(handoff.get("write_scope", [])),
        "next_required_lane": next_required_lane,
    }


def _owner_surface_state(path: Path) -> str:
    if not path.exists():
        return "ABSENT"
    if path.suffix.lower() != ".json":
        return "MATERIALIZED"
    data = _load_json(path)
    if data.get("materialized") is False:
        return "BLOCKED"
    build_status = str(data.get("build_status", "")).strip().upper()
    if build_status.startswith("FAIL") or build_status.startswith("BLOCKED"):
        return "BLOCKED"
    return "MATERIALIZED"


def _extract_preserved_overlap_treatment(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    preserve = data.get("preserve_diagnostics", {}) or {}
    overlap_hygiene = preserve.get("preserved_only_overlaps_hygiene", {}) or {}
    overlap_treatment = preserve.get("preserved_only_overlaps_treatment", {}) or {}
    has_preserve_diagnostics = bool(preserve)
    has_overlap_hygiene = bool(overlap_hygiene)
    has_overlap_treatment = bool(overlap_treatment)
    if not path.exists():
        treatment_state = "missing_layer_store"
    elif not has_preserve_diagnostics:
        treatment_state = "no_preserve_diagnostics_present"
    elif has_overlap_treatment:
        treatment_state = "treatment_reported"
    elif has_overlap_hygiene:
        treatment_state = "hygiene_only"
    else:
        treatment_state = "preserve_without_overlap_hygiene"
    return {
        "path": str(path),
        "exists": path.exists(),
        "observation_state": treatment_state,
        "has_preserve_diagnostics": has_preserve_diagnostics,
        "has_overlap_hygiene": has_overlap_hygiene,
        "has_overlap_treatment": has_overlap_treatment,
        "preserved_only_edge_count": int(preserve.get("preserved_only_edge_count", 0) or 0),
        "preserved_only_overlap_edge_count": int(
            overlap_hygiene.get("preserved_only_overlap_edge_count", 0) or 0
        ),
        "current_runtime_effect": overlap_treatment.get("current_runtime_effect", ""),
        "reason_flags": list(overlap_treatment.get("reason_flags", [])),
    }


def build_nested_graph_layer_audit(
    workspace_root: str,
    program_path: str = DEFAULT_PROGRAM,
    queue_packet_path: str = DEFAULT_QUEUE_PACKET,
) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    program = _load_json(_resolve(root, program_path))
    queue_packet = _load_json(_resolve(root, queue_packet_path))

    units = []
    layer_statuses: dict[str, str] = {}
    preserved_overlap_observation_summary: dict[str, dict[str, Any]] = {}
    for unit in program.get("build_units", []):
        required_boot = [_resolve(root, p) for p in unit.get("required_boot", [])]
        source_artifacts = [_resolve(root, p) for p in unit.get("source_artifacts", [])]
        expected_outputs = [_resolve(root, p) for p in unit.get("expected_outputs", [])]
        owner_surface = _resolve(root, unit.get("owner_surface", ""))
        audit_surface = _resolve(root, unit.get("audit_surface", ""))

        missing_boot = [str(p) for p in required_boot if not p.exists()]
        missing_sources = [str(p) for p in source_artifacts if not p.exists()]
        existing_outputs = [str(p) for p in expected_outputs if p.exists()]

        owner_state = _owner_surface_state(owner_surface)
        declared_status = str(unit.get("status", ""))
        if str(unit.get("layer_id", "")) in PRESERVED_OVERLAP_TREATMENT_LAYERS:
            preserved_overlap_observation_summary[str(unit.get("layer_id", ""))] = (
                _extract_preserved_overlap_treatment(owner_surface)
            )

        if owner_state == "MATERIALIZED":
            current_state = "MATERIALIZED"
        elif "BLOCKED" in declared_status:
            current_state = "BLOCKED"
        elif owner_state == "BLOCKED":
            current_state = "BLOCKED"
        elif missing_boot or missing_sources:
            current_state = "BLOCKED"
        else:
            current_state = "QUEUED"

        units.append({
            "unit_id": unit.get("unit_id", unit.get("layer_id", "")),
            "dispatch_id": unit.get("dispatch_id", ""),
            "layer_id": unit.get("layer_id", ""),
            "declared_status": declared_status,
            "current_state": current_state,
            "depends_on": list(unit.get("depends_on", [])),
            "owner_surface": str(owner_surface),
            "audit_surface": str(audit_surface),
            "missing_boot": missing_boot,
            "missing_sources": missing_sources,
            "existing_outputs": existing_outputs,
            "expected_output_count": len(expected_outputs),
            "owner_surface_state": owner_state,
        })
        layer_statuses[str(unit.get("layer_id", ""))] = current_state

    raw_handoff_path = str(
        queue_packet.get("dispatch_handoff_json", "")
        or program.get("next_correction_handoff_json", "")
    )
    if not raw_handoff_path and str(queue_packet.get("queue_status", "")).strip() == "NO_WORK":
        queue_handoff = {
            "path": "",
            "exists": False,
            "state": "NO_WORK",
            "unit_id": "",
            "dispatch_id": "",
            "layer_id": "",
            "role_type": "",
            "thread_class": "",
            "mode": "",
            "queue_status": "NO_WORK",
            "missing_boot": [],
            "missing_sources": [],
            "existing_outputs": [],
            "expected_output_count": 0,
            "write_scope": [],
            "next_required_lane": "",
        }
    else:
        queue_handoff = _inspect_handoff(root, raw_handoff_path)
    next_required_lane = str(queue_handoff.get("next_required_lane", "") or "")
    if queue_handoff and queue_handoff.get("state") == "QUEUED":
        next_recommended_unit = str(
            queue_handoff.get("unit_id", "")
            or program.get("next_correction_unit_id", "")
            or program.get("ready_unit_id", "")
        ) or None
    elif queue_handoff and queue_handoff.get("state") == "NO_WORK":
        next_recommended_unit = None
    else:
        next_recommended_unit = next_required_lane or None

    return {
        "schema": "NESTED_GRAPH_LAYER_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "program_path": str(_resolve(root, program_path)),
        "program_status": str(program.get("program_status", "")),
        "ready_unit_id": str(program.get("ready_unit_id", "")),
        "current_queue_status": str(queue_packet.get("queue_status", "")),
        "current_queue_dispatch_id": str(queue_packet.get("dispatch_id", "")),
        "current_queue_handoff_status": queue_handoff,
        "next_required_lane": next_required_lane or None,
        "next_recommended_unit": next_recommended_unit,
        "live_substrate": "single_authoritative_multigraph_plus_projections",
        "preserved_overlap_observation_summary": preserved_overlap_observation_summary,
        "layer_statuses": layer_statuses,
        "unit_count": len(units),
        "units": units,
    }


def render_nested_graph_layer_note(report: dict[str, Any]) -> str:
    lines = [
        "# NESTED_GRAPH_LAYER_AUDIT__CURRENT__v1",
        "",
        f"generated_utc: {report['generated_utc']}",
        f"program_path: {report['program_path']}",
        f"program_status: {report['program_status']}",
        f"ready_unit_id: {report['ready_unit_id']}",
        f"current_queue_status: {report['current_queue_status']}",
        f"next_required_lane: {report.get('next_required_lane') or ''}",
        f"live_substrate: {report['live_substrate']}",
        "",
    ]
    queue_handoff = report.get("current_queue_handoff_status", {})
    if queue_handoff:
        lines.extend([
            "## CURRENT_QUEUE_HANDOFF",
            f"- path: {queue_handoff.get('path', '')}",
            f"- unit_id: {queue_handoff.get('unit_id', '')}",
            f"- dispatch_id: {queue_handoff.get('dispatch_id', '')}",
            f"- layer_id: {queue_handoff.get('layer_id', '')}",
            f"- role_type: {queue_handoff.get('role_type', '')}",
            f"- thread_class: {queue_handoff.get('thread_class', '')}",
            f"- mode: {queue_handoff.get('mode', '')}",
            f"- queue_status: {queue_handoff.get('queue_status', '')}",
            f"- state: {queue_handoff.get('state', '')}",
            f"- existing_outputs: {len(queue_handoff.get('existing_outputs', []))}/{queue_handoff.get('expected_output_count', 0)}",
        ])
        if queue_handoff.get("next_required_lane"):
            lines.append(f"- next_required_lane: {queue_handoff.get('next_required_lane', '')}")
        if queue_handoff.get("write_scope"):
            lines.append("- write_scope:")
            for item in queue_handoff["write_scope"]:
                lines.append(f"  - {item}")
        if queue_handoff.get("missing_boot"):
            lines.append("- missing_boot:")
            for item in queue_handoff["missing_boot"]:
                lines.append(f"  - {item}")
        if queue_handoff.get("missing_sources"):
            lines.append("- missing_sources:")
            for item in queue_handoff["missing_sources"]:
                lines.append(f"  - {item}")
        lines.append("")
    if report.get("preserved_overlap_observation_summary"):
        lines.extend([
            "## PRESERVED_OVERLAP_OBSERVATIONS",
        ])
        for layer_id, info in report["preserved_overlap_observation_summary"].items():
            lines.append(
                f"- {layer_id}: state={info['observation_state']} "
                f"preserved_only_edges={info['preserved_only_edge_count']} "
                f"preserved_only_overlaps={info['preserved_only_overlap_edge_count']}"
            )
            if info.get("current_runtime_effect"):
                lines.append(f"  - current_runtime_effect: {info['current_runtime_effect']}")
            if info.get("reason_flags"):
                lines.append(f"  - reason_flags: {info['reason_flags']}")
        lines.append("")
    for unit in report["units"]:
        lines.extend([
            f"## {unit['layer_id']}",
            f"- unit_id: {unit['unit_id']}",
            f"- dispatch_id: {unit['dispatch_id']}",
            f"- declared_status: {unit['declared_status']}",
            f"- current_state: {unit['current_state']}",
            f"- owner_surface_state: {unit['owner_surface_state']}",
            f"- owner_surface: {unit['owner_surface']}",
            f"- existing_outputs: {len(unit['existing_outputs'])}/{unit['expected_output_count']}",
        ])
        if unit["missing_boot"]:
            lines.append("- missing_boot:")
            for item in unit["missing_boot"]:
                lines.append(f"  - {item}")
        if unit["missing_sources"]:
            lines.append("- missing_sources:")
            for item in unit["missing_sources"]:
                lines.append(f"  - {item}")
        lines.append("")
    return "\n".join(lines)


def write_nested_graph_layer_audit(workspace_root: str, program_path: str = DEFAULT_PROGRAM) -> dict[str, str]:
    root = Path(workspace_root).resolve()
    report = build_nested_graph_layer_audit(str(root), program_path)
    audit_dir = root / "system_v4" / "a2_state" / "audit_logs"
    audit_dir.mkdir(parents=True, exist_ok=True)
    json_path = audit_dir / "NESTED_GRAPH_LAYER_AUDIT__2026_03_20__v1.json"
    md_path = audit_dir / "NESTED_GRAPH_LAYER_AUDIT__2026_03_20__v1.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_nested_graph_layer_note(report), encoding="utf-8")
    return {"json_path": str(json_path), "md_path": str(md_path)}


if __name__ == "__main__":
    result = write_nested_graph_layer_audit(str(Path(__file__).resolve().parents[2]))
    print(json.dumps(result, indent=2, sort_keys=True))
