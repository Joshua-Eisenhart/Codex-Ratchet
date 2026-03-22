"""
control_graph_bridge_source_auditor.py

Audit which missing control-graph bridges have honest source surfaces inside the
current repo and which still remain heuristic-only.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORITATIVE_GRAPH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
BRIDGE_GAP_JSON = "system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_GAP_AUDIT__CURRENT__v1.json"
PYG_AUDIT_JSON = "system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.json"
REPORT_JSON = "system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_AUDIT__CURRENT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_AUDIT__CURRENT__v1.md"
PACKET_JSON = "system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_PACKET__CURRENT__v1.json"

FOCUS_TYPES = (
    "SKILL",
    "KERNEL_CONCEPT",
    "EXECUTION_BLOCK",
    "B_OUTCOME",
    "B_SURVIVOR",
    "SIM_EVIDENCED",
)

TRACE_FIELD_KEYS = ("source_concept_id", "kernel_concept_id", "concept_id", "lineage_refs")


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


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _count_direct_edges(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    source_type: str,
    target_type: str,
) -> int:
    count = 0
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        if source_id not in nodes or target_id not in nodes:
            continue
        if nodes[source_id].get("node_type") == source_type and nodes[target_id].get("node_type") == target_type:
            count += 1
    return count


def _skill_row(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    skill_nodes = [node for node in nodes.values() if node.get("node_type") == "SKILL"]
    prop_keys = Counter()
    conceptish_key_hits = 0
    samples: list[dict[str, Any]] = []
    for node_id, node in nodes.items():
        if node.get("node_type") != "SKILL":
            continue
        props = node.get("properties", {}) or {}
        for key in props:
            prop_keys[key] += 1
            if "concept" in key.lower() or "kernel" in key.lower():
                if _nonempty(props.get(key)):
                    conceptish_key_hits += 1
        if len(samples) < 3:
            samples.append(
                {
                    "id": node_id,
                    "name": node.get("name"),
                    "properties": {k: props.get(k) for k in sorted(props.keys())[:8]},
                }
            )
    return {
        "bridge_family": "SKILL -> KERNEL_CONCEPT",
        "derivation_status": "heuristic_only",
        "current_direct_edge_count": _count_direct_edges(nodes, edges, "SKILL", "KERNEL_CONCEPT"),
        "supporting_counts": {
            "skill_count": len(skill_nodes),
            "skill_nodes_with_nonempty_conceptish_fields": conceptish_key_hits,
        },
        "grounding_surface": (
            "skill nodes currently expose operational metadata such as source_path, applicable layers, inputs, outputs, adapters, and related_skills,"
            " but not owner-bound kernel concept identity"
        ),
        "property_keys": sorted(prop_keys.keys()),
        "samples": samples,
        "recommended_interpretation": (
            "do not seed skill-to-kernel edges from current skill metadata alone; any link would still be heuristic or text-derived"
        ),
    }


def _survivor_row(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    survivors = {
        node_id: node
        for node_id, node in nodes.items()
        if node.get("node_type") == "B_SURVIVOR"
    }
    nonempty_source = 0
    resolved_source = 0
    unresolved_examples: list[dict[str, Any]] = []
    resolved_examples: list[dict[str, Any]] = []
    for node_id, node in survivors.items():
        props = node.get("properties", {}) or {}
        source_concept_id = props.get("source_concept_id", "")
        if not _nonempty(source_concept_id):
            continue
        nonempty_source += 1
        if source_concept_id in nodes and nodes[source_concept_id].get("node_type") == "KERNEL_CONCEPT":
            resolved_source += 1
            if len(resolved_examples) < 3:
                resolved_examples.append(
                    {
                        "survivor_id": node_id,
                        "source_concept_id": source_concept_id,
                        "source_concept_name": nodes[source_concept_id].get("name"),
                    }
                )
        elif len(unresolved_examples) < 3:
            unresolved_examples.append(
                {
                    "survivor_id": node_id,
                    "source_concept_id": source_concept_id,
                }
            )
    return {
        "bridge_family": "B_SURVIVOR -> KERNEL_CONCEPT",
        "derivation_status": "partial_property_trace",
        "current_direct_edge_count": _count_direct_edges(nodes, edges, "B_SURVIVOR", "KERNEL_CONCEPT"),
        "supporting_counts": {
            "survivor_count": len(survivors),
            "survivors_with_nonempty_source_concept_id": nonempty_source,
            "survivors_with_resolved_live_kernel_source": resolved_source,
        },
        "grounding_surface": "B_SURVIVOR.properties.source_concept_id is the strongest current owner-bound kernel trace field",
        "samples": {
            "resolved": resolved_examples,
            "unresolved": unresolved_examples,
        },
        "recommended_interpretation": (
            "treat survivor-to-kernel linkage as partially derivable from survivor properties, but only resolved live kernel ids are strong enough for backfill candidates"
        ),
    }


def _sim_row(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    survivors = {
        node_id: node
        for node_id, node in nodes.items()
        if node.get("node_type") == "B_SURVIVOR"
    }
    sim_to_survivor = 0
    sim_to_sourced_survivor = 0
    examples: list[dict[str, Any]] = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        if source_id not in nodes or target_id not in survivors:
            continue
        if nodes[source_id].get("node_type") != "SIM_EVIDENCED" or edge.get("relation") != "SIM_EVIDENCE_FOR":
            continue
        sim_to_survivor += 1
        survivor_props = survivors[target_id].get("properties", {}) or {}
        if _nonempty(survivor_props.get("source_concept_id")):
            sim_to_sourced_survivor += 1
            if len(examples) < 3:
                examples.append(
                    {
                        "sim_id": source_id,
                        "survivor_id": target_id,
                        "survivor_source_concept_id": survivor_props.get("source_concept_id"),
                    }
                )
    return {
        "bridge_family": "SIM_EVIDENCED -> KERNEL_CONCEPT",
        "derivation_status": "chain_partial",
        "current_direct_edge_count": _count_direct_edges(nodes, edges, "SIM_EVIDENCED", "KERNEL_CONCEPT"),
        "supporting_counts": {
            "sim_evidenced_count": sum(1 for node in nodes.values() if node.get("node_type") == "SIM_EVIDENCED"),
            "sim_to_survivor_edge_count": sim_to_survivor,
            "sim_to_sourced_survivor_edge_count": sim_to_sourced_survivor,
        },
        "grounding_surface": "SIM_EVIDENCED reaches kernel-facing trace only through SIM_EVIDENCE_FOR -> B_SURVIVOR -> source_concept_id",
        "samples": examples,
        "recommended_interpretation": (
            "permit only chain-derived kernel trace on the SIM side; do not claim direct sim-to-kernel linkage from current owner surfaces"
        ),
    }


def _generic_trace_row(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    source_type: str,
) -> dict[str, Any]:
    items = {
        node_id: node
        for node_id, node in nodes.items()
        if node.get("node_type") == source_type
    }
    trace_field_hits = Counter()
    samples: list[dict[str, Any]] = []
    for node_id, node in items.items():
        props = node.get("properties", {}) or {}
        for key in TRACE_FIELD_KEYS:
            if _nonempty(props.get(key)):
                trace_field_hits[key] += 1
        if len(samples) < 3:
            subset = {key: props.get(key) for key in TRACE_FIELD_KEYS if key in props}
            samples.append({"id": node_id, "name": node.get("name"), "trace_fields": subset})
    return {
        "bridge_family": f"{source_type} -> KERNEL_CONCEPT",
        "derivation_status": "not_derivable_now",
        "current_direct_edge_count": _count_direct_edges(nodes, edges, source_type, "KERNEL_CONCEPT"),
        "supporting_counts": {
            f"{source_type.lower()}_count": len(items),
            "nonempty_trace_field_total": sum(trace_field_hits.values()),
        },
        "grounding_surface": f"{source_type} currently lacks owner-bound kernel trace fields in the live graph",
        "trace_field_hits": dict(trace_field_hits),
        "samples": samples,
        "recommended_interpretation": (
            f"treat {source_type.lower()} nodes as kernel-untraced control-chain surfaces until explicit concept linkage is emitted"
        ),
    }


def _collect_bridge_source_rows(root: Path) -> dict[str, Any]:
    data = _load_json(root / AUTHORITATIVE_GRAPH)
    nodes = data.get("nodes", {}) if isinstance(data, dict) else {}
    edges = data.get("edges", []) if isinstance(data, dict) else []
    if not isinstance(nodes, dict):
        nodes = {}
    if not isinstance(edges, list):
        edges = []

    focus_counts = Counter(
        node.get("node_type", "?")
        for node in nodes.values()
        if isinstance(node, dict) and node.get("node_type") in FOCUS_TYPES
    )
    rows = [
        _skill_row(nodes, edges),
        _survivor_row(nodes, edges),
        _sim_row(nodes, edges),
        _generic_trace_row(nodes, edges, "B_OUTCOME"),
        _generic_trace_row(nodes, edges, "EXECUTION_BLOCK"),
    ]
    status_counts = Counter(row["derivation_status"] for row in rows)
    return {
        "focus_node_type_counts": dict(focus_counts),
        "bridge_source_rows": rows,
        "bridge_source_summary": dict(status_counts),
    }


def _render_markdown(report: dict[str, Any]) -> str:
    row_lines = []
    for row in report.get("bridge_source_rows", []):
        row_lines.extend(
            [
                f"### {row['bridge_family']}",
                f"- derivation_status: `{row['derivation_status']}`",
                f"- current_direct_edge_count: `{row['current_direct_edge_count']}`",
                f"- grounding_surface: {row['grounding_surface']}",
                f"- recommended_interpretation: {row['recommended_interpretation']}",
                "",
            ]
        )
    next_lines = [f"- {item}" for item in report.get("recommended_next_actions", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    return "\n".join(
        [
            "# Control Graph Bridge Source Audit",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- audit_only: `{report['audit_only']}`",
            f"- do_not_promote: `{report['do_not_promote']}`",
            f"- authoritative_graph: `{report['authoritative_graph']}`",
            "",
            "## Source Rows",
            *row_lines,
            "## Recommended Next Actions",
            *next_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_control_graph_bridge_source_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = ctx or {}
    root = Path(repo_root).resolve()
    graph_path = root / AUTHORITATIVE_GRAPH
    bridge_gap = _load_json(root / BRIDGE_GAP_JSON)
    pyg_audit = _load_json(root / PYG_AUDIT_JSON)

    issues: list[str] = []
    if not graph_path.exists():
        issues.append("missing authoritative live graph store")
    if not bridge_gap:
        issues.append("missing or unreadable bridge-gap audit")
    if not pyg_audit:
        issues.append("missing or unreadable PyG projection audit")

    bridge_source = _collect_bridge_source_rows(root) if graph_path.exists() else {
        "focus_node_type_counts": {},
        "bridge_source_rows": [],
        "bridge_source_summary": {},
    }

    status = "ok" if not issues else "attention_required"
    report = {
        "schema": "CONTROL_GRAPH_BRIDGE_SOURCE_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "authoritative_graph": AUTHORITATIVE_GRAPH,
        "supporting_bridge_gap_audit": BRIDGE_GAP_JSON,
        "supporting_projection_audit": PYG_AUDIT_JSON,
        "focus_node_types": list(FOCUS_TYPES),
        "focus_node_type_counts": bridge_source["focus_node_type_counts"],
        "bridge_source_rows": bridge_source["bridge_source_rows"],
        "bridge_source_summary": bridge_source["bridge_source_summary"],
        "recommended_next_actions": [
            "Do not auto-seed SKILL -> KERNEL_CONCEPT links from current skill metadata; the live owner surfaces still lack owner-bound kernel concept identity on the skill side.",
            "Treat B_SURVIVOR.properties.source_concept_id as the strongest current witness-side bridge source, but only resolved live kernel ids are strong enough for any backfill proposal.",
            "Treat SIM_EVIDENCED kernel trace as chain-derived only through SIM_EVIDENCE_FOR -> B_SURVIVOR, not as direct sim-to-kernel linkage.",
            "Keep B_OUTCOME and EXECUTION_BLOCK kernel-untraced until explicit kernel trace fields or relations are emitted.",
            "Proceed to the first bounded TopoNetX projection with these bridge-source limits explicit instead of pretending the control graph is already fully joined.",
        ],
        "issues": issues,
    }
    packet = {
        "schema": "CONTROL_GRAPH_BRIDGE_SOURCE_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": status,
        "allow_training": False,
        "allow_canonical_graph_replacement": False,
        "allow_bridge_backfill": False,
        "recommended_next_slice_ids": [
            "toponetx-projection-adapter-audit",
            "survivor-kernel-bridge-backfill-audit",
            "skill-kernel-link-seeding-policy-audit",
        ],
        "bridge_source_summary": report["bridge_source_summary"],
        "authoritative_graph": AUTHORITATIVE_GRAPH,
    }
    return report, packet


def run_control_graph_bridge_source_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT
    root = Path(repo_root).resolve()
    report, packet = build_control_graph_bridge_source_report(root, ctx)
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
    result = run_control_graph_bridge_source_audit({"repo_root": str(REPO_ROOT)})
    print(json.dumps(result, indent=2, sort_keys=True))
