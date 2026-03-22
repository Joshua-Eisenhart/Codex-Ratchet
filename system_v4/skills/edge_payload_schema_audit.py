"""
edge_payload_schema_audit.py

Audit the smallest honest sidecar schema for richer edge payloads over admitted
low-control relations.
"""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

LOW_CONTROL_GRAPH = "system_v4/a2_state/graphs/a2_low_control_graph_v1.json"
TOPONETX_AUDIT_JSON = "system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_AUDIT__CURRENT__v1.json"
CLIFFORD_AUDIT_JSON = "system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_AUDIT__CURRENT__v1.json"
REPORT_JSON = "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_AUDIT__CURRENT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_AUDIT__CURRENT__v1.md"
PACKET_JSON = "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_PACKET__CURRENT__v1.json"

ADMITTED_RELATIONS = ("DEPENDS_ON", "EXCLUDES", "STRUCTURALLY_RELATED", "RELATED_TO")
FORBIDDEN_RELATIONS = ("OVERLAPS",)
DEFERRED_GA_FIELDS = [
    "entropy_state",
    "correlation_entropy",
    "orientation_basis",
    "clifford_grade",
    "obstruction_score",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _collect_relation_attr_truth(root: Path) -> dict[str, Any]:
    graph = _load_json(root / LOW_CONTROL_GRAPH)
    edges = graph.get("edges", []) if isinstance(graph, dict) else []
    if not isinstance(edges, list):
        edges = []

    relation_attr_counts: dict[str, Counter[str]] = defaultdict(Counter)
    relation_numeric_attr_counts: dict[str, Counter[str]] = defaultdict(Counter)
    relation_string_attr_counts: dict[str, Counter[str]] = defaultdict(Counter)
    relation_edge_counts: Counter[str] = Counter()

    for edge in edges:
        if not isinstance(edge, dict):
            continue
        relation = str(edge.get("relation", "?"))
        relation_edge_counts[relation] += 1
        attrs = edge.get("attributes", {}) or {}
        for key, value in attrs.items():
            relation_attr_counts[relation][key] += 1
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                relation_numeric_attr_counts[relation][key] += 1
            elif isinstance(value, str):
                relation_string_attr_counts[relation][key] += 1

    return {
        "relation_edge_counts": dict(relation_edge_counts),
        "relation_attr_counts": {rel: dict(counter) for rel, counter in relation_attr_counts.items()},
        "relation_numeric_attr_counts": {rel: dict(counter) for rel, counter in relation_numeric_attr_counts.items()},
        "relation_string_attr_counts": {rel: dict(counter) for rel, counter in relation_string_attr_counts.items()},
    }


def _build_schema_rows(attr_truth: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation in ADMITTED_RELATIONS:
        numeric = attr_truth["relation_numeric_attr_counts"].get(relation, {})
        strings = attr_truth["relation_string_attr_counts"].get(relation, {})
        required_carriers = ["relation", "source_id", "target_id"]
        optional_scalar_carriers = sorted(numeric.keys())
        optional_string_carriers = sorted(k for k in strings.keys() if k not in {"computed_at"})
        rows.append(
            {
                "relation": relation,
                "required_carriers": required_carriers,
                "optional_scalar_carriers": optional_scalar_carriers,
                "optional_string_carriers": optional_string_carriers,
                "deferred_ga_fields": DEFERRED_GA_FIELDS,
                "payload_mode": "read_only_sidecar_only",
            }
        )
    return rows


def _render_markdown(report: dict[str, Any]) -> str:
    row_lines = []
    for row in report.get("schema_rows", []):
        row_lines.extend(
            [
                f"### {row['relation']}",
                f"- required_carriers: `{', '.join(row['required_carriers'])}`",
                f"- optional_scalar_carriers: `{', '.join(row['optional_scalar_carriers']) or 'none'}`",
                f"- optional_string_carriers: `{', '.join(row['optional_string_carriers']) or 'none'}`",
                "",
            ]
        )
    next_lines = [f"- {item}" for item in report.get("recommended_next_actions", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    return "\n".join(
        [
            "# Edge Payload Schema Audit",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- audit_only: `{report['audit_only']}`",
            f"- do_not_promote: `{report['do_not_promote']}`",
            "",
            "## Schema Rows",
            *row_lines,
            "## Recommended Next Actions",
            *next_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_edge_payload_schema_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = ctx or {}
    root = Path(repo_root).resolve()

    issues: list[str] = []
    for rel in (LOW_CONTROL_GRAPH, TOPONETX_AUDIT_JSON, CLIFFORD_AUDIT_JSON):
        if not (root / rel).exists():
            issues.append(f"missing required surface: {rel}")

    attr_truth = _collect_relation_attr_truth(root)
    schema_rows = _build_schema_rows(attr_truth)
    status = "ok" if not issues else "attention_required"
    report = {
        "schema": "EDGE_PAYLOAD_SCHEMA_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "low_control_probe": LOW_CONTROL_GRAPH,
        "supporting_toponetx_audit": TOPONETX_AUDIT_JSON,
        "supporting_clifford_audit": CLIFFORD_AUDIT_JSON,
        "admitted_relations": list(ADMITTED_RELATIONS),
        "forbidden_relations": list(FORBIDDEN_RELATIONS),
        "schema_rows": schema_rows,
        "recommended_next_actions": [
            "Keep the schema sidecar-only and relation-scoped; do not write these payloads into canonical graph edges yet.",
            "Keep OVERLAPS and all skill-edge families outside the admitted schema scope.",
            "If this line continues, the next bounded step would be a read-only payload-schema probe over one admitted relation family, not a runtime mutation pass.",
        ],
        "issues": issues,
    }
    packet = {
        "schema": "EDGE_PAYLOAD_SCHEMA_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": status,
        "allow_training": False,
        "allow_canonical_graph_replacement": False,
        "allow_sidecar_schema_only": True,
        "recommended_next_slice_ids": [
            "edge-payload-schema-probe",
        ],
        "admitted_relations": list(ADMITTED_RELATIONS),
        "forbidden_relations": list(FORBIDDEN_RELATIONS),
        "deferred_ga_fields": DEFERRED_GA_FIELDS,
    }
    return report, packet


def run_edge_payload_schema_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT
    root = Path(repo_root).resolve()
    report, packet = build_edge_payload_schema_report(root, ctx)
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
    }


if __name__ == "__main__":
    result = run_edge_payload_schema_audit({"repo_root": str(REPO_ROOT)})
    print(json.dumps(result, indent=2, sort_keys=True))
