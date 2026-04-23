"""
control_graph_bridge_gap_auditor.py

Audit the real bridge gaps inside the current control-facing graph families.

This slice reads the authoritative live graph plus the bounded PyG projection
audit, then reports which cross-family links are absent, which are only weak
signals, and which are already materially present.
"""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from system_v4.skills.graph_store import load_graph_json


REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORITATIVE_GRAPH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
PYG_AUDIT_JSON = "system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.json"
REPORT_JSON = "system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_GAP_AUDIT__CURRENT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_GAP_AUDIT__CURRENT__v1.md"
PACKET_JSON = "system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_GAP_PACKET__CURRENT__v1.json"

FOCUS_NODE_TYPES = (
    "SKILL",
    "KERNEL_CONCEPT",
    "EXECUTION_BLOCK",
    "B_OUTCOME",
    "B_SURVIVOR",
    "SIM_EVIDENCED",
)

BRIDGE_FAMILIES = [
    ("SKILL", "KERNEL_CONCEPT"),
    ("SKILL", "EXECUTION_BLOCK"),
    ("SKILL", "B_OUTCOME"),
    ("SKILL", "B_SURVIVOR"),
    ("SKILL", "SIM_EVIDENCED"),
    ("B_OUTCOME", "KERNEL_CONCEPT"),
    ("SIM_EVIDENCED", "KERNEL_CONCEPT"),
    ("SIM_EVIDENCED", "B_SURVIVOR"),
    ("B_SURVIVOR", "KERNEL_CONCEPT"),
    ("B_OUTCOME", "EXECUTION_BLOCK"),
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any]:
    try:
        path.relative_to(REPO_ROOT / "system_v4" / "a2_state" / "graphs")
        return load_graph_json(REPO_ROOT, str(path.relative_to(REPO_ROOT)), default={})
    except ValueError:
        pass
    except FileNotFoundError:
        return {}
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


def _classify_bridge(count: int) -> str:
    if count <= 0:
        return "missing"
    if count <= 3:
        return "weak_signal"
    return "present"


def _collect_bridge_data(root: Path) -> dict[str, Any]:
    data = _load_json(root / AUTHORITATIVE_GRAPH)
    nodes = data.get("nodes", {}) if isinstance(data, dict) else {}
    edges = data.get("edges", []) if isinstance(data, dict) else []

    relation_counts: Counter[tuple[str, str, str]] = Counter()
    examples: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    per_node_type = Counter(
        node.get("node_type", "?")
        for node in nodes.values()
        if isinstance(node, dict) and node.get("node_type") in FOCUS_NODE_TYPES
    )

    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        if source_id not in nodes or target_id not in nodes:
            continue
        source_type = nodes[source_id].get("node_type")
        target_type = nodes[target_id].get("node_type")
        if source_type not in FOCUS_NODE_TYPES or target_type not in FOCUS_NODE_TYPES:
            continue
        relation = str(edge.get("relation", "?"))
        relation_counts[(source_type, relation, target_type)] += 1
        pair = (source_type, target_type)
        if len(examples[pair]) < 3:
            examples[pair].append(
                {
                    "source_id": source_id,
                    "target_id": target_id,
                    "relation": relation,
                    "attributes": edge.get("attributes", {}) or {},
                }
            )

    bridge_rows = []
    for source_type, target_type in BRIDGE_FAMILIES:
        relations = {
            relation: count
            for (s_type, relation, t_type), count in relation_counts.items()
            if s_type == source_type and t_type == target_type
        }
        total_count = sum(relations.values())
        bridge_rows.append(
            {
                "source_type": source_type,
                "target_type": target_type,
                "bridge_status": _classify_bridge(total_count),
                "edge_count": total_count,
                "relations": relations,
                "examples": examples.get((source_type, target_type), []),
            }
        )

    return {
        "focus_node_type_counts": dict(per_node_type),
        "bridge_rows": bridge_rows,
        "relation_counts": {
            f"{source}::{relation}::{target}": count
            for (source, relation, target), count in sorted(relation_counts.items())
        },
    }


def _render_markdown(report: dict[str, Any]) -> str:
    bridge_lines = [
        f"- `{row['source_type']} -> {row['target_type']}`: {row['bridge_status']} ({row['edge_count']} edges)"
        for row in report.get("bridge_rows", [])
    ]
    next_lines = [f"- {item}" for item in report.get("recommended_next_actions", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    return "\n".join(
        [
            "# Control Graph Bridge Gap Audit",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- audit_only: `{report['audit_only']}`",
            f"- do_not_promote: `{report['do_not_promote']}`",
            f"- authoritative_graph: `{report['authoritative_graph']}`",
            "",
            "## Bridge Status",
            *bridge_lines,
            "",
            "## Recommended Next Actions",
            *next_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_control_graph_bridge_gap_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = ctx or {}
    root = Path(repo_root).resolve()
    graph_path = root / AUTHORITATIVE_GRAPH
    pyg_audit = _load_json(root / PYG_AUDIT_JSON)
    issues: list[str] = []
    if not graph_path.exists():
        issues.append("missing authoritative live graph store")
    if not pyg_audit:
        issues.append("missing or unreadable PyG projection audit")

    bridge_data = _collect_bridge_data(root) if graph_path.exists() else {
        "focus_node_type_counts": {},
        "bridge_rows": [],
        "relation_counts": {},
    }

    missing_count = sum(1 for row in bridge_data["bridge_rows"] if row["bridge_status"] == "missing")
    weak_count = sum(1 for row in bridge_data["bridge_rows"] if row["bridge_status"] == "weak_signal")
    present_count = sum(1 for row in bridge_data["bridge_rows"] if row["bridge_status"] == "present")

    status = "ok" if not issues else "attention_required"
    report = {
        "schema": "CONTROL_GRAPH_BRIDGE_GAP_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "authoritative_graph": AUTHORITATIVE_GRAPH,
        "supporting_projection_audit": PYG_AUDIT_JSON,
        "focus_node_types": list(FOCUS_NODE_TYPES),
        "focus_node_type_counts": bridge_data["focus_node_type_counts"],
        "bridge_rows": bridge_data["bridge_rows"],
        "relation_counts": bridge_data["relation_counts"],
        "bridge_summary": {
            "missing_bridge_family_count": missing_count,
            "weak_signal_bridge_family_count": weak_count,
            "present_bridge_family_count": present_count,
        },
        "recommended_next_actions": [
            "Build a bounded skill-to-kernel bridge audit or projection follow-on before claiming the graph connects skills to the control substrate.",
            "Build a bounded witness-to-kernel bridge audit so B/SIM evidence can be traced into kernel/control surfaces more honestly.",
            "Keep the current PyG view read-only until these bridge families are stronger than isolated or absent signals.",
            "Do not widen training claims until bridge families exist beyond SKILL-to-SKILL and kernel-only relation islands.",
        ],
        "issues": issues,
    }
    packet = {
        "schema": "CONTROL_GRAPH_BRIDGE_GAP_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": status,
        "allow_training": False,
        "allow_canonical_graph_replacement": False,
        "recommended_next_slice_ids": [
            "skill-kernel-bridge-audit",
            "witness-kernel-bridge-audit",
        ],
        "bridge_summary": report["bridge_summary"],
        "authoritative_graph": AUTHORITATIVE_GRAPH,
    }
    return report, packet


def run_control_graph_bridge_gap_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT
    root = Path(repo_root).resolve()
    report, packet = build_control_graph_bridge_gap_report(root, ctx)
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
    result = run_control_graph_bridge_gap_audit({"repo_root": str(REPO_ROOT)})
    print(json.dumps(result, indent=2, sort_keys=True))
