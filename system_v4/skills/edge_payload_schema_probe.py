"""
edge_payload_schema_probe.py

Instantiate one bounded read-only payload preview over an admitted low-control
relation family using the current edge-payload schema contract.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

LOW_CONTROL_GRAPH = "system_v4/a2_state/graphs/a2_low_control_graph_v1.json"
SCHEMA_AUDIT_JSON = "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_AUDIT__CURRENT__v1.json"
SCHEMA_PACKET_JSON = "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_PACKET__CURRENT__v1.json"
REPORT_JSON = "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_PROBE__CURRENT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_PROBE__CURRENT__v1.md"
PACKET_JSON = "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_PROBE_PACKET__CURRENT__v1.json"

DEFAULT_RELATION = "STRUCTURALLY_RELATED"
SAMPLE_LIMIT = 3


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _normalize_relation(raw: Any) -> str:
    relation = str(raw or DEFAULT_RELATION).strip().upper()
    return relation or DEFAULT_RELATION


def _carrier_snapshot(attrs: dict[str, Any], schema_row: dict[str, Any]) -> dict[str, Any]:
    scalar_keys = [str(item) for item in schema_row.get("optional_scalar_carriers", [])]
    string_keys = [str(item) for item in schema_row.get("optional_string_carriers", [])]
    return {
        "scalar_carriers": {key: attrs.get(key) for key in scalar_keys if key in attrs},
        "string_carriers": {key: attrs.get(key) for key in string_keys if key in attrs},
    }


def _payload_preview(edge: dict[str, Any], schema_row: dict[str, Any], deferred_fields: list[str]) -> dict[str, Any]:
    attrs = edge.get("attributes", {}) if isinstance(edge.get("attributes"), dict) else {}
    return {
        "relation": str(edge.get("relation", "")),
        "source_id": str(edge.get("source_id", "")),
        "target_id": str(edge.get("target_id", "")),
        "carrier_snapshot": _carrier_snapshot(attrs, schema_row),
        "deferred_ga_slots": {field: None for field in deferred_fields},
        "payload_mode": "read_only_sidecar_preview",
        "canonical_graph_write": False,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    preview_lines: list[str] = []
    for item in report.get("payload_previews", []):
        scalar_keys = ", ".join(sorted(item["carrier_snapshot"]["scalar_carriers"].keys())) or "none"
        string_keys = ", ".join(sorted(item["carrier_snapshot"]["string_carriers"].keys())) or "none"
        preview_lines.extend(
            [
                f"- `{item['source_id']}` -> `{item['target_id']}`",
                f"  scalar_carriers: `{scalar_keys}`",
                f"  string_carriers: `{string_keys}`",
            ]
        )
    if not preview_lines:
        preview_lines = ["- none"]
    action_lines = [f"- {item}" for item in report.get("recommended_next_actions", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    return "\n".join(
        [
            "# Edge Payload Schema Probe",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- relation: `{report['relation']}`",
            f"- payload_preview_count: `{report['payload_preview_count']}`",
            f"- recommended_next_step: `{report['recommended_next_step']}`",
            "",
            "## Payload Previews",
            *preview_lines,
            "",
            "## Recommended Next Actions",
            *action_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_edge_payload_schema_probe_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    graph = _load_json(root / LOW_CONTROL_GRAPH)
    schema_audit = _load_json(root / SCHEMA_AUDIT_JSON)
    schema_packet = _load_json(root / SCHEMA_PACKET_JSON)

    relation = _normalize_relation(ctx.get("relation"))
    issues: list[str] = []
    if schema_audit.get("status") != "ok":
        issues.append("edge payload schema audit is missing or not ok")
    if schema_packet.get("status") != "ok":
        issues.append("edge payload schema packet is missing or not ok")

    admitted_relations = [str(item) for item in schema_packet.get("admitted_relations", [])]
    if relation not in admitted_relations:
        issues.append(f"requested relation is not in the admitted schema scope: {relation}")

    schema_rows = {
        str(row.get("relation", "")).upper(): row
        for row in schema_audit.get("schema_rows", [])
        if isinstance(row, dict)
    }
    schema_row = schema_rows.get(relation, {})
    if not schema_row:
        issues.append(f"schema row missing for requested relation: {relation}")

    edges = graph.get("edges", []) if isinstance(graph, dict) else []
    relation_edges = [
        edge
        for edge in edges
        if isinstance(edge, dict) and str(edge.get("relation", "")).upper() == relation
    ]
    if not relation_edges:
        issues.append(f"no low-control edges found for requested relation: {relation}")

    deferred_fields = [str(item) for item in schema_packet.get("deferred_ga_fields", [])]
    payload_previews = [
        _payload_preview(edge, schema_row, deferred_fields)
        for edge in relation_edges[:SAMPLE_LIMIT]
    ] if schema_row and relation_edges else []

    status = "ok" if not issues else "attention_required"
    report = {
        "schema": "EDGE_PAYLOAD_SCHEMA_PROBE_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "relation": relation,
        "low_control_graph": LOW_CONTROL_GRAPH,
        "schema_audit_path": SCHEMA_AUDIT_JSON,
        "schema_packet_path": SCHEMA_PACKET_JSON,
        "payload_preview_count": len(payload_previews),
        "relation_edge_count": len(relation_edges),
        "payload_previews": payload_previews,
        "recommended_next_step": "hold_probe_as_sidecar_only" if not issues else "repair_probe_inputs_first",
        "recommended_next_actions": [
            "Keep these payload previews sidecar-only and do not write them into the canonical graph.",
            "Keep deferred GA slots empty until a later bounded semantic probe earns specific values.",
            "If the graph line continues, use this probe as evidence for a later relation-scoped semantic audit rather than a graph mutation pass.",
        ],
        "issues": issues,
    }
    packet = {
        "schema": "EDGE_PAYLOAD_SCHEMA_PROBE_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": status,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "relation": relation,
        "allow_canonical_graph_write": False,
        "allow_sidecar_payload_preview_only": True,
        "payload_preview_count": len(payload_previews),
        "recommended_next_step": report["recommended_next_step"],
        "deferred_ga_fields": deferred_fields,
    }
    return report, packet


def run_edge_payload_schema_probe(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report, packet = build_edge_payload_schema_probe_report(root, ctx)

    report_path = Path(ctx.get("report_json_path") or (root / REPORT_JSON))
    markdown_path = Path(ctx.get("report_md_path") or (root / REPORT_MD))
    packet_path = Path(ctx.get("packet_path") or (root / PACKET_JSON))

    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report))
    _write_json(packet_path, packet)

    return {
        "status": report["status"],
        "report_json_path": str(report_path),
        "report_md_path": str(markdown_path),
        "packet_path": str(packet_path),
        "recommended_next_step": report["recommended_next_step"],
    }


if __name__ == "__main__":
    result = run_edge_payload_schema_probe({"repo_root": str(REPO_ROOT)})
    print(json.dumps(result, indent=2, sort_keys=True))
